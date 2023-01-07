from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession


spark = SparkSession.builder \
        .config("spark.hadoop.fs.s3a.endpoint", "http://10.1.112.80:9000") \
        .config("spark.hadoop.fs.s3a.access.key", "COQX70GCQXBBWGCSISEO") \
        .config("spark.hadoop.fs.s3a.secret.key", "Y01yFxxj9RYX4nBCGfk3xSr0RsL3T5lanjpVTz1F") \
        .config("spark.hadoop.fs.s3a.path.style.access", True) \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled","false") \
        .config("spark.hadoop.com.amazonaws.services.s3.enableV2","true") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider","org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")\
        .getOrCreate()

customer = spark.read.csv("s3a://datalake/olist_customers_dataset.csv")
customer.show()
print(customer.columns)

male_users = userdata.select("customer_id", "customer_unique_id")

#male_users.write.mode("overwrite").parquet("s3a://datalake/maleuserdata/")
