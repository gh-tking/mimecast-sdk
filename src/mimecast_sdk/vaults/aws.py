"""
AWS Secrets Manager implementation
"""
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from .base import VaultProvider

class AWSSecretsManager(VaultProvider):
    def __init__(
        self,
        region_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        profile_name: Optional[str] = None
    ):
        session = boto3.Session(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            profile_name=profile_name,
            region_name=region_name
        )
        self.client = session.client('secretsmanager')

    def get_secret(self, secret_name: str) -> str:
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response['SecretString']
        except ClientError as e:
            raise ValueError(f"Failed to retrieve secret: {str(e)}")

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            self.client.create_secret(
                Name=secret_name,
                SecretString=secret_value
            )
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceExistsException':
                self.client.put_secret_value(
                    SecretId=secret_name,
                    SecretString=secret_value
                )
            else:
                raise ValueError(f"Failed to store secret: {str(e)}")