import boto3
from botocore.exceptions import NoCredentialsError

ACCESS_KEY = 'AKIARKZYEVBYLJ3IFBIJ'


def download_data(bot):
    s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                      aws_secret_access_key=bot.token["AWSdownload"])

    try:
        s3.download_file("cahdatastorage", "data.txt", "data.txt")
        print("Download Successful")
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False