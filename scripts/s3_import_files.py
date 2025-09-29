import  os
import uuid
import boto3
from botocore.exceptions import ClientError
import argparse
# AK: AKIASISLBULHKW7MSINE 
# Pass: rgrySuzQswquN2pFq5ba6Bqh+nG7EOQhV/kDekv2

def create_bucket(s3_resource):
    print("Creating bucket...")
    #Name the bucket with a unique name
    bucket_name = f"learn-aws-{str(uuid.uuid4())}"
    #Create the bucket object locally
    bucket = s3_resource.Bucket(bucket_name)
    try:
        #create the bucket in AWS
        bucket.create(
            CreateBucketConfiguration={
                "LocationConstraint": s3_resource.meta.client.meta.region_name
            }
        )
        print(f"Bucket {bucket_name} created.")
    except ClientError as e:
        print(f"Error creating bucket {bucket_name}: {e}")
        return None
    
    return bucket_name

def import_file(s3_client,bucket_name,file_name):
    try:
        #Check if file exists
        if not os.path.exists(file_name):
            print("File was not found, exiting program")
            return None
        #Create the name of the object, lets base it on the basename of each file
        object_name = os.path.basename(file_name)
        # Try and upload the file into the object
        try:
            s3_client.upload_file(file_name, bucket_name, object_name)
        
        except ClientError as s3_e:
            print(f"Failed to upload file {file_name} into object: {s3_e}")
        print("File uploaded successfully")
        return file_name
    except ClientError as e:
        print(f"Failed to upload file {file_name}: {e}")


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("--s3-bucket",type=str,default=None,help="Name of the S3 bucket")
    args.add_argument("--single",type=bool,default=False,help="Upload a single file")
    #Connect to the s3 client
    session = boto3.Session(profile_name="trinta") 
    s3_client = session.client("s3")
    args = args.parse_args()

    if not args.s3_bucket:
        print("Invalid bucket name, please provide a bucket name: python3 --bucket-name=<bucket-name>")
        exit(0)

    BUCKET_NAME = args.s3_bucket
    FILE_FOLDER = f"{os.path.dirname(__file__)}/files"
    print(FILE_FOLDER)
    #import each file individually
    file_list = os.listdir(FILE_FOLDER)
    if len(file_list) > 0:
        if args.single:
            file_list = file_list[0]
    print(file_list)
    for file_name in file_list:
        import_file(s3_client,BUCKET_NAME,f"{FILE_FOLDER}/{file_name}")
    