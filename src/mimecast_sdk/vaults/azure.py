"""
Azure Key Vault implementation
"""
from typing import Optional
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from .base import VaultProvider

class AzureKeyVault(VaultProvider):
    def __init__(self, vault_url: str):
        credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=credential)

    def get_secret(self, secret_name: str) -> str:
        try:
            secret = self.client.get_secret(secret_name)
            return secret.value
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret: {str(e)}")

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            self.client.set_secret(secret_name, secret_value)
        except Exception as e:
            raise ValueError(f"Failed to store secret: {str(e)}")