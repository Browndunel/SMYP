from minio import Minio
from pymongo import MongoClient
import json
import time

# connexion MinIO
minio_client = Minio(
    "josue-unreceiving-toshiko.ngrok-free.dev",
    access_key="minoadmin",
    secret_key="minioadmin159",
    secure=True
)

bucket_name = "symp"
prefix_curated = "curated/"

# connexion MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["SYMP"]
collection = db["SYMP_CURATED_DATA"]

processed_files = set()

# Boucle infinie pour surveiller MinIO
print("Démarrage du watcher sur curated/ ...")
while True:
    try:
        objects = minio_client.list_objects(bucket_name, prefix=prefix_curated, recursive=True)
        for obj in objects:
            if obj.size == 0:
                continue  # ignorer dossiers/fichiers vides

            if obj.object_name in processed_files:
                continue  # déjà traité

            # Récupérer le fichier
            response = minio_client.get_object(bucket_name, obj.object_name)
            data = response.read()

            if not data:
                print(f"Fichier vide ignoré : {obj.object_name}")
                continue

            try:
                json_data = json.loads(data)
            except json.JSONDecodeError:
                print(f"Fichier non JSON ignoré : {obj.object_name}")
                continue

            # Ajouter un champ _id basé sur le nom de fichier pour éviter duplicata
            json_data["_id"] = obj.object_name
            collection.insert_one(json_data)
            processed_files.add(obj.object_name)
            print(f"✅ Document inséré : {obj.object_name}")

    except Exception as e:
        print("⚠️ Erreur :", e)

    time.sleep(10)  # vérifier toutes les 10 secondes
    