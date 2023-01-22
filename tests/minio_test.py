from minio import Minio
from minio.error import S3Error
client = Minio(
    "10.1.112.79:9000",
    access_key="COQX70GCQXBBWGCSISEO",
    secret_key="Y01yFxxj9RYX4nBCGfk3xSr0RsL3T5lanjpVTz1F",
    secure= False
)

# Make 'asiatrip' bucket if not exist.
found = client.bucket_exists("datalake")
if not found:
    client.make_bucket("datalake")
else:
    print("Bucket 'datalake' already exists")


list(client.list_objects("datalake"))