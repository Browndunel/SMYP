from minio import Minio
from minio.error import S3Error
from io import BytesIO

client = Minio(
    "localhost:9000",
    access_key="minoadmin",
    secret_key="minioadmin159",
    secure= False
)
bucket_name = "symp"
folders = [
    "raw/", 
    "clean/", 
    "curated/"
]
try:
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        print(f"Bucket '{bucket_name}' created successfully.")
    for folder in folders:
        client.put_object(
            bucket_name,
            folder,
            data=BytesIO(b""),
            length=0
        )
        print(f"Folder '{folder}' created successfully in bucket '{bucket_name}'.")
except S3Error as e:
    print("Error occurred:", e)