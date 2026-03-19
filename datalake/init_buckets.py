# ============================================================
# SMYP – Initialisation MinIO
# Connexion au serveur MinIO de Louise (ngrok)
# Usage : python datalake/init_buckets.py
# ============================================================

import os
import sys
from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

load_dotenv()

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "josue-unreceiving-toshiko.ngrok-free.dev")
ACCESS_KEY     = os.getenv("MINIO_ACCESS_KEY", "minoadmin")
SECRET_KEY     = os.getenv("MINIO_SECRET_KEY", "minioadmin159")
SECURE         = os.getenv("MINIO_SECURE", "true").lower() == "true"
BUCKETS        = ["smyp-raw", "smyp-clean", "smyp-curated"]

def init_buckets():
    print(f"\n[SMYP] Connexion MinIO : {MINIO_ENDPOINT} (secure={SECURE})")

    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=SECURE
        )
    except Exception as e:
        print(f"[SMYP] ✗ Erreur connexion : {e}")
        sys.exit(1)

    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                print(f"[SMYP] ✓ Bucket créé    : {bucket}")
            else:
                print(f"[SMYP] → Bucket existant : {bucket}")
        except S3Error as e:
            print(f"[SMYP] ✗ Erreur bucket {bucket} : {e}")
            sys.exit(1)

    print("\n[SMYP] ✓ Initialisation terminée")
    print(f"[SMYP] Endpoint : {MINIO_ENDPOINT}\n")

if __name__ == "__main__":
    init_buckets()