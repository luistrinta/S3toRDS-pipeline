import  os, uuid
import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import S3UploadFailedError

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
    """ 
    # Create an S3 resource
    s3_resource = boto3.resource("s3")
    bucket_name = create_bucket(s3_resource=s3_resource)

    if bucket_name:
        print(f"Bucket {bucket_name} is ready for use.")
    """ 
    #Connect to the s3 client
    s3_client = boto3.client("s3")
    BUCKET_NAME = "learn-aws-ab8e1d2f-5afa-4fa5-bf7f-e0121838c350"
    
    #import each file individually
    for file_name in os.listdir("./files"):
        import_file(s3_client,BUCKET_NAME,f"./files/{file_name}")

    