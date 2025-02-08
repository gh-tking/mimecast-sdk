"""
Mimecast systems module containing implementations for different Mimecast platforms
"""

from .gateway import CloudGatewayAPI
from .integrated import CloudIntegratedAPI
from .partner import PartnerAPI
from .directory import DirectoryAPI
from .user import UserAPI
from .ttp import TtpAPI
from .domain import DomainAPI

__all__ = [
    'CloudGatewayAPI',
    'CloudIntegratedAPI',
    'PartnerAPI',
    'DirectoryAPI',
    'UserAPI',
    'TtpAPI',
    'DomainAPI'
]