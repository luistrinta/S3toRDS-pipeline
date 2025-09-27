import psycopg2
import pandas as pd #import from pandas-layer.zip or AWSSDKPandas-Python312 pre-built layer
import boto3
from botocore.exceptions import ClientError
import os
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
S3Client = boto3.client('s3')


def lambda_handler(event, context):
    start = time.time()

    try:
        dbname=os.environ["DB_NAME"]
        user=os.environ["USER_NAME"]
        password=os.environ["PASSWORD"]
        host=os.environ["RDS_URL"]
        #Connect to RDS database
        conn = psycopg2.connect(dbname=dbname ,user=user,password=password,host=host)
    except psycopg2.errors.OperationalError as e:
        logger.error(f"Error connecting to database: {e}")
        return

    #Get the bucket_name and key from the event
    bucket_name= event['Records'][0]['s3']['bucket']['name']
    key_name = event['Records'][0]['s3']['object']['key']
    
    logger.info(bucket_name)
    logger.info(key_name)   

    try:
        #Get object and read data
        logger.info("Fetching from S3...")
        fileObject = S3Client.get_object(Bucket=bucket_name, Key=key_name)
    except ClientError as e:
        logger.error(f"Error fetching from S3: {e}")
        return
    else:
        logger.info("Fetched from S3")
    try:
        #Pass it into a pandas dataframe
        if key_name.endswith('.csv'):
            df = pd.read_csv(fileObject['Body'],header=0)
        elif key_name.endswith('.jsonl'):
            df = pd.read_json(fileObject['Body'],lines=True)
        else:
            logger.warning("File format not yet supported")
    except pd.errors.ParserWarning as e:
        logger.error(f"Error parsing file: {e}")
        return

    #Data validation
    logger.info("Data validation in progress...")
    logger.info(f"Data retrieval and processing took {time.time() - start} ms")
    #Insert data into database
    try:
        data = []# [(row.id, row.name, row.age) for row in df.itertuples(index=False)]

        with conn.cursor() as cur:
            cur.executemany(
                "INSERT INTO test (id, name, age) VALUES (%s, %s, %s)",
                data
            )
            conn.commit()
            logger.info("Data inserted into database")
    except psycopg2.errors.DatabaseError as e:
        logger.error(f"Error inserting data into database: {e}")
        return    