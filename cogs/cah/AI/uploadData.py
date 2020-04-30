import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'AKIARKZYEVBYPIGGW6UF'

def upload_to_aws(bot, local_file, bucket, s3_file):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=bot.token["AWSUpload"])

    try:
        s3.upload_file(local_file, bucket, s3_file)
        print("Upload Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False
