"""
Mimecast SDK - Python client library for Mimecast API 2.0
"""

from .client import MimecastClient
from .auth import MimecastAuth

__version__ = "0.1.0"
__all__ = ['MimecastClient', 'MimecastAuth']