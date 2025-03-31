import boto3
from botocore.exceptions import NoCredentialsError


class S3Utility:
    """
    A utility class for S3 operations that can be used by multiple tools.
    """

    def __init__(
        self, bucket_name: str, aws_access_key_id: str, aws_secret_access_key: str
    ):
        self.bucket_name = bucket_name
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def upload_file(
        self, file_data: bytes, file_name: str, acl: str = "public-read"
    ) -> str:
        """
        Uploads a file to the S3 bucket and returns the public URL.
        """
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        try:
            s3.put_object(
                Bucket=self.bucket_name, Key=file_name, Body=file_data, ACL=acl
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
        except NoCredentialsError:
            raise Exception("AWS credentials not available")

    def download_file(self, file_name: str) -> bytes:
        """
        Downloads a file from the S3 bucket and returns its content.
        """
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        try:
            response = s3.get_object(Bucket=self.bucket_name, Key=file_name)
            return response["Body"].read()
        except NoCredentialsError:
            raise Exception("AWS credentials not available")
        except s3.exceptions.NoSuchKey:
            raise Exception(f"File {file_name} not found in the bucket")

    def list_files(self, prefix: str = "") -> list[str]:
        """
        Lists files in the S3 bucket, optionally filtered by a prefix.
        """
        s3 = boto3.client(
            "s3",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        try:
            response = s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except NoCredentialsError:
            raise Exception("AWS credentials not available")
