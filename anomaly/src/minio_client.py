"""Client MinIO configuré depuis le .env"""

import os
from pathlib import Path
from dotenv import load_dotenv
from minio import Minio

load_dotenv(Path(__file__).parent.parent / ".env")

client = Minio(
    os.getenv("MINIO_ENDPOINT"),
    access_key=os.getenv("MINIO_ACCESS_KEY"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE", "true").lower() == "true",
)

BUCKET_RAW = "smyp-raw"
BUCKET_CLEAN = "smyp-clean"
BUCKET_CURATED = "smyp-curated"

# Créer les buckets s'ils n'existent pas
for bucket in [BUCKET_RAW, BUCKET_CLEAN, BUCKET_CURATED]:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        print(f"[MinIO] Bucket '{bucket}' créé")
    else:
        print(f"[MinIO] Bucket '{bucket}' OK")
