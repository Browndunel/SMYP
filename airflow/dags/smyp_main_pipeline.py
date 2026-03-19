# ============================================================
# SMYP – DAG Principal
# smyp_main_pipeline.py — Brawn Dunel
#
# Pipeline : ingestion → ocr → ner → anomaly → storage → notify
# Déclenché par : POST /api/trigger depuis le backend (Eloic)
# ============================================================

from datetime import datetime, timedelta
import json
import os
import requests
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable

# ── Logger ─────────────────────────────────────────────────
log = logging.getLogger(__name__)

# ── Config depuis variables d'environnement ─────────────────
OCR_SERVICE_URL      = os.getenv("OCR_SERVICE_URL",      "http://ocr-service:8001")
ANOMALY_SERVICE_URL  = os.getenv("ANOMALY_SERVICE_URL",  "http://anomaly-service:8002")
BACKEND_URL          = os.getenv("BACKEND_URL",          "http://backend:5000")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "josue-unreceiving-toshiko.ngrok-free.dev")
MINIO_SECURE   = os.getenv("MINIO_SECURE", "true").lower() == "true"

# ── Paramètres DAG ──────────────────────────────────────────
default_args = {
    "owner": "brawn_dunel",
    "depends_on_past": False,
    "start_date": datetime(2026, 3, 17),
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
    "execution_timeout": timedelta(minutes=10),
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="smyp_main_pipeline",
    default_args=default_args,
    description="Pipeline principal SMYP : OCR → NER → Anomaly → Storage → Notify",
    schedule_interval=None,   # Déclenché manuellement via API uniquement
    catchup=False,
    tags=["smyp", "pipeline", "production"],
    params={
        "file_id": "",          # UUID du fichier uploadé
        "file_name": "",        # Nom original du fichier
        "file_path": "",        # Chemin dans MinIO RAW
        "file_type": "",        # pdf | png | jpg
    }
)

# ============================================================
# TÂCHE 1 — Validation ingestion
# Vérifie que le fichier est bien présent dans MinIO RAW
# ============================================================
def task_validate_ingestion(**context):
    """
    Vérifie que le fichier uploadé est accessible dans MinIO RAW.
    Input  : params.file_id, params.file_path
    Output : pousse file_id dans XCom pour les tâches suivantes
    """
    params    = context["params"]
    file_id   = params["file_id"]
    file_name = params["file_name"]
    file_path = params["file_path"]

    log.info(f"[SMYP] Validation ingestion — file_id={file_id}, file={file_name}")

    if not file_id or not file_path:
        raise ValueError(f"Paramètres manquants : file_id={file_id}, file_path={file_path}")

    # Notifie le backend que le pipeline a démarré
    try:
        requests.post(
            f"{BACKEND_URL}/api/pipeline/status",
            json={
                "file_id": file_id,
                "step": "ingestion",
                "status": "running",
                "progress": 10
            },
            timeout=5
        )
    except Exception as e:
        log.warning(f"[SMYP] Impossible de notifier backend (non bloquant) : {e}")

    # Pousse les infos dans XCom pour les tâches suivantes
    context["ti"].xcom_push(key="file_id",   value=file_id)
    context["ti"].xcom_push(key="file_name", value=file_name)
    context["ti"].xcom_push(key="file_path", value=file_path)
    context["ti"].xcom_push(key="file_type", value=params.get("file_type", "pdf"))

    log.info(f"[SMYP] Ingestion validée pour {file_name}")
    return {"status": "ok", "file_id": file_id}


# ============================================================
# TÂCHE 2 — OCR
# Appelle ocr-service:8001/process (Ludo)
# ============================================================
def task_ocr(**context):
    """
    Appelle le service OCR de Ludo.
    Input  : file_path depuis XCom
    Output : texte OCR + confidence → pousse dans XCom
    """
    ti        = context["ti"]
    file_id   = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_id")
    file_name = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_name")
    file_path = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_path")

    log.info(f"[SMYP] OCR démarré — {file_name}")

    # Notifie le backend
    _notify_backend(file_id, "ocr", "running", 25)

    # Appel au service OCR (Ludo)
    response = requests.post(
        f"{OCR_SERVICE_URL}/process",
        json={
            "file_id":   file_id,
            "file_path": file_path,
            "bucket":    MINIO_BUCKET_RAW
        },
        timeout=120   # OCR peut être lent sur images dégradées
    )

    if response.status_code != 200:
        raise Exception(f"OCR service error {response.status_code}: {response.text}")

    ocr_result = response.json()
    log.info(f"[SMYP] OCR terminé — confidence={ocr_result.get('confidence', 0):.2f}")

    # Pousse les résultats dans XCom
    ti.xcom_push(key="ocr_text",       value=ocr_result.get("text", ""))
    ti.xcom_push(key="ocr_confidence", value=ocr_result.get("confidence", 0))
    ti.xcom_push(key="clean_path",     value=ocr_result.get("clean_path", ""))

    _notify_backend(file_id, "ocr", "success", 40)
    return ocr_result


# ============================================================
# TÂCHE 3 — NER + Classification
# Appelle ocr-service:8001/extract_entities (Ludo)
# ============================================================
def task_ner_extraction(**context):
    """
    Extrait les entités (SIRET, montants, dates...) depuis le texte OCR.
    Input  : ocr_text depuis XCom
    Output : JSON structuré avec tous les champs extraits
    """
    ti             = context["ti"]
    file_id        = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_id")
    file_name      = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_name")
    ocr_text       = ti.xcom_pull(task_ids="t2_ocr",                key="ocr_text")
    ocr_confidence = ti.xcom_pull(task_ids="t2_ocr",                key="ocr_confidence")

    log.info(f"[SMYP] NER démarré — {file_name}")
    _notify_backend(file_id, "ner_extraction", "running", 55)

    # Appel classification
    classif_response = requests.post(
        f"{OCR_SERVICE_URL}/classify",
        json={"text": ocr_text},
        timeout=30
    )
    classif_response.raise_for_status()
    classif = classif_response.json()
    doc_type   = classif.get("doc_type",    "INCONNU")
    confidence = classif.get("confidence",  0.0)

    log.info(f"[SMYP] Classification : {doc_type} (confidence={confidence:.2f})")

    # Appel NER extraction
    ner_response = requests.post(
        f"{OCR_SERVICE_URL}/extract_entities",
        json={
            "file_id":        file_id,
            "doc_type":       doc_type,
            "text":           ocr_text,
            "ocr_confidence": ocr_confidence
        },
        timeout=60
    )
    ner_response.raise_for_status()
    ner_result = ner_response.json()

    # Construit le JSON structuré complet (contrat Ludo → Loan)
    structured = {
        "file_id":                    file_id,
        "file_name":                  file_name,
        "doc_type":                   doc_type,
        "ocr_confidence":             ocr_confidence,
        "classification_confidence":  confidence,
        "fields":                     ner_result.get("fields", {})
    }

    ti.xcom_push(key="structured_data", value=json.dumps(structured))
    ti.xcom_push(key="doc_type",        value=doc_type)

    _notify_backend(file_id, "ner_extraction", "success", 65)
    log.info(f"[SMYP] NER terminé — {len(structured['fields'])} champs extraits")
    return structured


# ============================================================
# TÂCHE 4 — Détection anomalies
# Appelle anomaly-service:8002/validate (Loan)
# ============================================================
def task_anomaly_detection(**context):
    """
    Valide les règles métier et détecte les anomalies.
    Input  : structured_data depuis XCom
    Output : status (OK/suspect/frauduleux) + anomalies[]
    """
    ti              = context["ti"]
    file_id         = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_id")
    structured_json = ti.xcom_pull(task_ids="t3_ner_extraction",     key="structured_data")
    structured      = json.loads(structured_json)

    log.info(f"[SMYP] Détection anomalies — {file_id}")
    _notify_backend(file_id, "anomaly_detection", "running", 75)

    # Appel au service Loan
    response = requests.post(
        f"{ANOMALY_SERVICE_URL}/validate",
        json=structured,
        timeout=60
    )
    response.raise_for_status()
    anomaly_result = response.json()

    status = anomaly_result.get("status", "suspect")
    score  = anomaly_result.get("anomaly_score", 0)
    nb_anomalies = len(anomaly_result.get("anomalies", []))

    log.info(f"[SMYP] Anomalies : status={status}, score={score:.2f}, anomalies={nb_anomalies}")

    ti.xcom_push(key="anomaly_result",    value=json.dumps(anomaly_result))
    ti.xcom_push(key="document_status",   value=status)
    ti.xcom_push(key="anomaly_score",     value=score)

    _notify_backend(file_id, "anomaly_detection", "success", 85)
    return anomaly_result


# ============================================================
# TÂCHE 5 — Stockage final
# Écrit dans MinIO CURATED + MongoDB (Louise)
# ============================================================
def task_storage(**context):
    """
    Construit le document final et l'envoie au backend pour
    stockage dans MinIO CURATED et MongoDB.
    Input  : tout depuis XCom
    Output : document complet stocké
    """
    ti              = context["ti"]
    file_id         = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_id")
    file_name       = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_name")
    file_path       = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_path")
    clean_path      = ti.xcom_pull(task_ids="t2_ocr",                key="clean_path")
    ocr_confidence  = ti.xcom_pull(task_ids="t2_ocr",                key="ocr_confidence")
    doc_type        = ti.xcom_pull(task_ids="t3_ner_extraction",      key="doc_type")
    structured_json = ti.xcom_pull(task_ids="t3_ner_extraction",      key="structured_data")
    anomaly_json    = ti.xcom_pull(task_ids="t4_anomaly_detection",   key="anomaly_result")

    structured     = json.loads(structured_json)
    anomaly_result = json.loads(anomaly_json)

    log.info(f"[SMYP] Stockage — {file_id}")
    _notify_backend(file_id, "storage", "running", 90)

    # Document final complet (contrat Loan → Louise)
    curated_path = f"{MINIO_BUCKET_CURATED}/{file_id}_curated.json"
    final_doc = {
        "file_id":                   file_id,
        "file_name":                 file_name,
        "doc_type":                  doc_type,
        "status":                    anomaly_result.get("status", "suspect"),
        "anomaly_score":             anomaly_result.get("anomaly_score", 0),
        "confidence_score":          anomaly_result.get("confidence_score", 0),
        "anomalies":                 anomaly_result.get("anomalies", []),
        "fields":                    structured.get("fields", {}),
        "minio_paths": {
            "raw":     file_path,
            "clean":   clean_path,
            "curated": curated_path
        },
        "ocr_confidence":            ocr_confidence,
        "classification_confidence": structured.get("classification_confidence", 0),
        "pipeline_version":          "1.0",
        "created_at":                datetime.utcnow().isoformat() + "Z"
    }

    # Envoie au backend qui écrit dans MongoDB + MinIO CURATED
    response = requests.post(
        f"{BACKEND_URL}/api/internal/store",
        json=final_doc,
        timeout=30
    )
    response.raise_for_status()

    log.info(f"[SMYP] Stockage terminé — status={final_doc['status']}")
    ti.xcom_push(key="final_doc", value=json.dumps(final_doc))
    return final_doc


# ============================================================
# TÂCHE 6 — Notification frontend
# Prévient le backend que le pipeline est terminé (Eloic)
# ============================================================
def task_notify_frontend(**context):
    """
    Envoie la notification finale au backend.
    Le frontend React poll /api/pipeline/status/:job_id
    et se rafraîchit automatiquement quand status=success.
    """
    ti       = context["ti"]
    file_id  = ti.xcom_pull(task_ids="t1_validate_ingestion", key="file_id")
    status   = ti.xcom_pull(task_ids="t4_anomaly_detection",  key="document_status")
    score    = ti.xcom_pull(task_ids="t4_anomaly_detection",  key="anomaly_score")

    log.info(f"[SMYP] Notification frontend — file_id={file_id}, status={status}")

    _notify_backend(
        file_id=file_id,
        step="complete",
        status="success",
        progress=100,
        extra={
            "document_status": status,
            "anomaly_score":   score
        }
    )

    log.info(f"[SMYP] Pipeline terminé avec succès pour {file_id}")
    return {"pipeline": "complete", "file_id": file_id, "status": status}


# ============================================================
# Helper — notifie le backend à chaque étape
# ============================================================
def _notify_backend(file_id: str, step: str, status: str,
                    progress: int, extra: dict = None):
    """
    Envoie le statut au backend Express (Eloic).
    Non bloquant — une erreur ici ne tue pas le pipeline.
    """
    payload = {
        "file_id":  file_id,
        "step":     step,
        "status":   status,
        "progress": progress
    }
    if extra:
        payload.update(extra)
    try:
        requests.post(
            f"{BACKEND_URL}/api/pipeline/status",
            json=payload,
            timeout=5
        )
    except Exception as e:
        log.warning(f"[SMYP] Notification backend échouée (non bloquant) : {e}")


# ============================================================
# DÉFINITION DES TÂCHES ET DÉPENDANCES
# ============================================================

t1 = PythonOperator(
    task_id="t1_validate_ingestion",
    python_callable=task_validate_ingestion,
    dag=dag,
    provide_context=True
)

t2 = PythonOperator(
    task_id="t2_ocr",
    python_callable=task_ocr,
    dag=dag,
    provide_context=True
)

t3 = PythonOperator(
    task_id="t3_ner_extraction",
    python_callable=task_ner_extraction,
    dag=dag,
    provide_context=True
)

t4 = PythonOperator(
    task_id="t4_anomaly_detection",
    python_callable=task_anomaly_detection,
    dag=dag,
    provide_context=True
)

t5 = PythonOperator(
    task_id="t5_storage",
    python_callable=task_storage,
    dag=dag,
    provide_context=True
)

t6 = PythonOperator(
    task_id="t6_notify_frontend",
    python_callable=task_notify_frontend,
    dag=dag,
    provide_context=True
)

# Pipeline séquentiel : t1 → t2 → t3 → t4 → t5 → t6
t1 >> t2 >> t3 >> t4 >> t5 >> t6