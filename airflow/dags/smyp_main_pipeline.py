# ============================================================
# SMYP – DAG Principal (Option A)
# smyp_main_pipeline.py — Brawn Dunel
#
# Pipeline déclenché par le backend APRÈS upload + OCR + anomaly.
# Rôle : valider les données reçues → confirmer en MongoDB → notifier le frontend
#
# Trigger : POST /api/v1/dags/smyp_main_pipeline/dagRuns
#   conf : { file_id, file_name, doc_type, status, anomaly_score,
#            anomalies, fields, ocr_confidence, user_id }
# ============================================================

from datetime import datetime, timedelta
import os
import requests
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:5001")

default_args = {
    "owner": "brawn_dunel",
    "depends_on_past": False,
    "start_date": datetime(2026, 3, 17),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
    "execution_timeout": timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry": False,
}

dag = DAG(
    dag_id="smyp_main_pipeline",
    default_args=default_args,
    description="Pipeline SMYP : valide → confirme MongoDB → notifie frontend",
    schedule_interval=None,   # Déclenché uniquement via API
    catchup=False,
    tags=["smyp", "pipeline", "production"],
)


# ============================================================
# TÂCHE 1 — Validation des données reçues
# ============================================================
def task_validate(**context):
    """
    Vérifie que le backend a bien envoyé les données requises.
    Pousse les données dans XCom pour les tâches suivantes.
    """
    conf = context["dag_run"].conf or {}

    file_id = conf.get("file_id")
    if not file_id:
        raise ValueError("conf.file_id manquant — le backend n'a pas envoyé l'ID du document")

    file_name     = conf.get("file_name", "inconnu")
    doc_type      = conf.get("doc_type", "INCONNU")
    status        = conf.get("status", "OK")
    anomaly_score = conf.get("anomaly_score", 0)
    anomalies     = conf.get("anomalies", [])
    fields        = conf.get("fields", {})
    ocr_confidence = conf.get("ocr_confidence", 0)

    log.info(f"[SMYP] t1 — Validation OK : file_id={file_id}, doc_type={doc_type}, status={status}")

    ti = context["ti"]
    ti.xcom_push(key="file_id",        value=file_id)
    ti.xcom_push(key="file_name",      value=file_name)
    ti.xcom_push(key="doc_type",       value=doc_type)
    ti.xcom_push(key="status",         value=status)
    ti.xcom_push(key="anomaly_score",  value=anomaly_score)
    ti.xcom_push(key="anomalies",      value=anomalies)
    ti.xcom_push(key="ocr_confidence", value=ocr_confidence)

    return {"ok": True, "file_id": file_id}


# ============================================================
# TÂCHE 2 — Confirmation dans MongoDB
# ============================================================
def task_store_mongodb(**context):
    """
    Appelle POST /api/internal/store sur le backend pour confirmer
    et mettre à jour le document dans MongoDB.
    """
    ti        = context["ti"]
    file_id       = ti.xcom_pull(task_ids="t1_validate", key="file_id")
    status        = ti.xcom_pull(task_ids="t1_validate", key="status")
    anomaly_score = ti.xcom_pull(task_ids="t1_validate", key="anomaly_score")
    anomalies     = ti.xcom_pull(task_ids="t1_validate", key="anomalies")

    log.info(f"[SMYP] t2 — Confirmation MongoDB : file_id={file_id}, status={status}")

    response = requests.post(
        f"{BACKEND_URL}/api/internal/store",
        json={
            "file_id":       file_id,
            "status":        status,
            "anomaly_score": anomaly_score,
            "anomalies":     anomalies,
            "pipeline_version": "2.0",
        },
        timeout=15,
    )
    response.raise_for_status()

    log.info(f"[SMYP] t2 — MongoDB confirmé pour {file_id}")
    return response.json()


# ============================================================
# TÂCHE 3 — Notification frontend
# ============================================================
def task_notify_frontend(**context):
    """
    Envoie le statut final au backend.
    Le frontend poll GET /api/pipeline/status/:file_id.
    """
    ti            = context["ti"]
    file_id       = ti.xcom_pull(task_ids="t1_validate", key="file_id")
    status        = ti.xcom_pull(task_ids="t1_validate", key="status")
    anomaly_score = ti.xcom_pull(task_ids="t1_validate", key="anomaly_score")
    doc_type      = ti.xcom_pull(task_ids="t1_validate", key="doc_type")

    log.info(f"[SMYP] t3 — Notification frontend : file_id={file_id}")

    requests.post(
        f"{BACKEND_URL}/api/pipeline/status",
        json={
            "file_id":       file_id,
            "step":          "complete",
            "status":        "success",
            "progress":      100,
            "document_status": status,
            "anomaly_score": anomaly_score,
            "doc_type":      doc_type,
        },
        timeout=5,
    )

    log.info(f"[SMYP] Pipeline terminé pour {file_id} — status={status}")
    return {"pipeline": "complete", "file_id": file_id, "status": status}


# ============================================================
# Définition et chaînage des tâches
# ============================================================
t1 = PythonOperator(task_id="t1_validate",       python_callable=task_validate,       dag=dag, provide_context=True)
t2 = PythonOperator(task_id="t2_store_mongodb",  python_callable=task_store_mongodb,  dag=dag, provide_context=True)
t3 = PythonOperator(task_id="t3_notify_frontend",python_callable=task_notify_frontend, dag=dag, provide_context=True)

t1 >> t2 >> t3
