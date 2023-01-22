from minio import Minio
from minio.error import S3Error
client = Minio(
    "10.1.112.87:9000",
    access_key="NV36RD72QN276TTX9B4H",
    secret_key="pQGs5lEEAkvF91hjCgZBdMKwCzsBLNFHobZbFbYB",
    secure= False
)

# Make 'asiatrip' bucket if not exist.
found = client.bucket_exists("datalake")
if not found:
    client.make_bucket("datalake")
else:
    print("Bucket 'datalake' already exists")


list(client.list_objects("datalake"))