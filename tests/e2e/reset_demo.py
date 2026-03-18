# ============================================================
# SMYP – Reset état démo
# Vide MongoDB + MinIO avant le jury
# Usage : python tests/e2e/reset_demo.py
# ============================================================

import os
import sys
from dotenv import load_dotenv
from minio import Minio
from pymongo import MongoClient

load_dotenv()

def reset_demo():
    print("\n[SMYP RESET] Nettoyage en cours...\n")

    # ── Vide MongoDB ────────────────────────────────────────
    try:
        client = MongoClient(
            os.getenv("MONGO_URI_EXTERNAL", "mongodb://localhost:27017/smyp"),
            serverSelectionTimeoutMS=5000
        )
        db     = client[os.getenv("MONGO_DB", "smyp")]
        result = db.documents_curated.delete_many({})
        print(f"[SMYP RESET] ✓ MongoDB : {result.deleted_count} documents supprimés")
    except Exception as e:
        print(f"[SMYP RESET] ✗ MongoDB erreur : {e}")
        sys.exit(1)

    # ── Vide MinIO ──────────────────────────────────────────
    try:
        minio = Minio(
            os.getenv("MINIO_ENDPOINT_EXTERNAL", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "smypadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "smypsecret123"),
            secure=False
        )
        for bucket in ["smyp-raw", "smyp-clean", "smyp-curated"]:
            objects = list(minio.list_objects(bucket, recursive=True))
            for obj in objects:
                minio.remove_object(bucket, obj.object_name)
            print(f"[SMYP RESET] ✓ MinIO {bucket} : {len(objects)} fichiers supprimés")
    except Exception as e:
        print(f"[SMYP RESET] ✗ MinIO erreur : {e}")
        sys.exit(1)

    print("\n[SMYP RESET] ✓ Système prêt pour la démo\n")

if __name__ == "__main__":
    reset_demo()