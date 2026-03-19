"""
Connexion au MinIO partagé (hébergé par Louise).
Les credentials sont dans le .env à la racine du projet.
"""

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

BUCKET = "symp"
