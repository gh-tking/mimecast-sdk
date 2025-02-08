"""
Base interface for vault implementations
"""
from abc import ABC, abstractmethod
from typing import Optional

class VaultProvider(ABC):
    @abstractmethod
    def get_secret(self, secret_name: str) -> str:
        """Retrieve a secret from the vault"""
        pass
    
    @abstractmethod
    def set_secret(self, secret_name: str, secret_value: str) -> None:
        """Store a secret in the vault"""
        pass