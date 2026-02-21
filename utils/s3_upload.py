import boto3
import os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("AWS_REGION")
)

BUCKET = os.getenv("AWS_BUCKET")

def upload_to_s3(file_path, file_name):
    try:
        # Upload the file to S3
        s3.upload_file(file_path, BUCKET, file_name)

        # Generate file URL
        url = f"https://{BUCKET}.s3.{os.getenv('AWS_REGION')}.amazonaws.com/{file_name}"

        return url

    except Exception as e:
        print("S3 Upload Error:", e)
        return None