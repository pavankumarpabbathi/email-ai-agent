import boto3

class S3Downloader:
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name="us-east-2")

    def download_object(self, bucket_name, object_name, file_path):
        try:
            self.s3_client.download_file(bucket_name, object_name, file_path)
            print(f"Downloaded {object_name} from {bucket_name} to {file_path}")
        except Exception as e:
            print(f"Error downloading object: {e}")
