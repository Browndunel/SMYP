# ============================================================
# SMYP – DAG Health Check
# Vérifie que tous les services sont up toutes les 5 minutes
# ============================================================

from datetime import datetime, timedelta
import requests
import logging
import os

from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

SERVICES = {
    "ocr-service":     os.getenv("OCR_SERVICE_URL",     "http://ocr-service:8001")     + "/health",
    "anomaly-service": os.getenv("ANOMALY_SERVICE_URL", "http://anomaly-service:8000") + "/health",
    "backend":         os.getenv("BACKEND_URL",         "http://backend:5001")         + "/health",
}

default_args = {
    "owner": "brawn_dunel",
    "start_date": datetime(2026, 3, 17),
    "retries": 1,
    "retry_delay": timedelta(seconds=30),
}

dag = DAG(
    dag_id="smyp_health_check",
    default_args=default_args,
    description="Vérifie la santé de tous les services SMYP",
    schedule_interval="*/5 * * * *",   # Toutes les 5 minutes
    catchup=False,
    tags=["smyp", "monitoring"]
)

def check_all_services(**context):
    results = {}
    all_healthy = True

    for name, url in SERVICES.items():
        try:
            r = requests.get(url, timeout=5)
            healthy = r.status_code == 200
            results[name] = {"status": "up" if healthy else "down", "code": r.status_code}
            if not healthy:
                all_healthy = False
                log.error(f"[SMYP HEALTH] {name} DOWN — code {r.status_code}")
            else:
                log.info(f"[SMYP HEALTH] {name} UP")
        except Exception as e:
            results[name] = {"status": "unreachable", "error": str(e)}
            all_healthy = False
            log.error(f"[SMYP HEALTH] {name} UNREACHABLE — {e}")

    log.info(f"[SMYP HEALTH] Résumé : {results}")

    if not all_healthy:
        raise Exception(f"Services en panne : {[k for k,v in results.items() if v['status'] != 'up']}")

    return results

PythonOperator(
    task_id="check_all_services",
    python_callable=check_all_services,
    dag=dag,
    provide_context=True
)