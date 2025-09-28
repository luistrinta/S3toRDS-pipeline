import psycopg2
import pandas as pd #import from pandas-layer.zip or AWSSDKPandas-Python312 pre-built layer
import boto3
from botocore.exceptions import ClientError
import os
import logging
import time
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
session = boto3.Session(profile_name="trinta") #local development
S3Client = session.client('s3')
load_dotenv() #local development

def lambda_handler(event, context):
    start = time.time()

    try:
        dbname=os.environ["DB_NAME"]
        user=os.environ["USER_NAME"]
        password=os.environ["PASSWORD"]
        host=os.environ["RDS_URL"]
        logger.info(f"{dbname},{user},{host}")
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
        df = pd.DataFrame()
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

    try:
    
        logger.info("Starting data validation and cleaning...")
        #Data validation/cleaning
        #Drop columns with miss in device_id or model
        df["device_id"]= df["device_id"].replace(to_replace="",value=None)
        df["model"] = df["model"].replace(to_replace="",value=None)
        df.dropna(inplace=True)
            
        #Drop duplicate timestamps partitioned by device_id and model
        df.drop_duplicates(subset=["device_id","model","timestamp"],keep="last",inplace=True)
        logger.info(f"Finished validating/cleaning data in {start-time.time()} ms")
        
        start = time.time()

        logger.info("Starting data transformation...")
        
        #Substitute any negative values with 0
        df.loc[~df["fuel_level_percent"].between(0,100),"fuel_level_percent"] = 0 
        df.loc[df["odometer_km"] < 0,"odometer_km"] = 0 
        df.loc[df["trip_driven_km"] < 0,"trip_driven_km"] = 0 
        df.loc[df["instant_consumption_l_per_100km"] < 0,"instant_consumption_l_per_100km"] = 0

        #Separate the loction array data into different variables
        df['location'] = df['location'].apply(lambda x: x.strip("[]").replace("'", "").replace("(","").replace(")","").split(','))

        # 2. Strip extra whitespace
        df['location'] = df['location'].apply(lambda lst: [item.strip() for item in lst])

        # 3. Create new columns from the list
        df[['city', 'country', 'region']] = pd.DataFrame(df['location'].tolist(), index=df.index)
 
        logger.info(f"Finished data transformation/processing in {time.time() - start} ms")
    
    except RuntimeError as e:
        logger.error(f"Failed to process data from file {key_name}: {e}")
        return

    #Insert data into database
    try:
        data = [(row.timestamp, row.device_id, row.model, row.odometer_km, row.trip_driven_km,\
                 row.instant_consumption_l_per_100km,\
                 row.fuel_level_percent, row.city, row.country, row.region) for row in df.itertuples(index=False)]
        

        with conn.cursor() as cur:
            cur.executemany(
                """INSERT INTO car_data 
                (timestamp, deviceid, model, odometer_km, trip_driven_km,instant_consumption_l_per_100km,fuel_level_pct,city, country_code, timezone) 
                VALUES (%s, %s, %s,%s, %s, %s,%s, %s, %s,%s)""",
                data
            )
            conn.commit()
            logger.info("Data inserted into database")
    except psycopg2.errors.DatabaseError as e:
        logger.error(f"Error inserting data into database: {e}")
        return    




"""

Use this for local testing
if __name__=="__main__":    
    event={
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": <name_of_your_bucket>
        },
        "object": {
          "key": <name_of_your_file>
        }
      }
    }
  ]
}
    
    lambda_handler(event,None)
"""