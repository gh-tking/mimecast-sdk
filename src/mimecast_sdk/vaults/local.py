"""
Local secure storage implementations using various backend options
"""
import os
import sys
import json
from typing import Optional
from abc import ABC, abstractmethod
from .base import VaultProvider

class LocalStorageBase(VaultProvider, ABC):
    """Base class for local storage implementations"""
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this storage method is available on the current system"""
        pass

class EnvVarStorage(LocalStorageBase):
    """Store secrets in environment variables"""
    def __init__(self, prefix: str = "MIMECAST_"):
        self.prefix = prefix

    def is_available(self) -> bool:
        return True  # Always available

    def get_secret(self, secret_name: str) -> str:
        env_var = f"{self.prefix}{secret_name.upper()}"
        value = os.getenv(env_var)
        if value is None:
            raise ValueError(f"Secret {secret_name} not found in environment variables")
        return value

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        env_var = f"{self.prefix}{secret_name.upper()}"
        # For Windows
        if sys.platform == 'win32':
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment', 0, winreg.KEY_ALL_ACCESS) as key:
                    winreg.SetValueEx(key, env_var, 0, winreg.REG_SZ, secret_value)
                    # Notify the system of the environment change
                    import ctypes
                    HWND_BROADCAST = 0xFFFF
                    WM_SETTINGCHANGE = 0x1A
                    SMTO_ABORTIFHUNG = 0x0002
                    result = ctypes.c_long()
                    ctypes.windll.user32.SendMessageTimeoutW(
                        HWND_BROADCAST, WM_SETTINGCHANGE, 0,
                        "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
                    )
            except Exception as e:
                raise ValueError(f"Failed to set environment variable: {str(e)}")
        else:
            # For Unix-like systems, write to ~/.profile
            profile_path = os.path.expanduser("~/.profile")
            try:
                with open(profile_path, 'a') as f:
                    f.write(f'\nexport {env_var}="{secret_value}"\n')
            except Exception as e:
                raise ValueError(f"Failed to set environment variable: {str(e)}")

class KeyringStorage(LocalStorageBase):
    """Store secrets using the system keyring"""
    def __init__(self):
        try:
            import keyring
            self.keyring = keyring
        except ImportError:
            raise ImportError("keyring package is required for KeyringStorage")

    def is_available(self) -> bool:
        try:
            # Test if keyring has a viable backend
            self.keyring.get_keyring()
            return True
        except Exception:
            return False

    def get_secret(self, secret_name: str) -> str:
        value = self.keyring.get_password("mimecast", secret_name)
        if value is None:
            raise ValueError(f"Secret {secret_name} not found in keyring")
        return value

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            self.keyring.set_password("mimecast", secret_name, secret_value)
        except Exception as e:
            raise ValueError(f"Failed to store secret in keyring: {str(e)}")

class WindowsCredentialManager(LocalStorageBase):
    """Store secrets using Windows Credential Manager"""
    def __init__(self):
        if sys.platform != 'win32':
            raise RuntimeError("Windows Credential Manager is only available on Windows")

    def is_available(self) -> bool:
        return sys.platform == 'win32'

    def get_secret(self, secret_name: str) -> str:
        try:
            import win32cred
            cred = win32cred.CredRead(
                f"mimecast/{secret_name}",
                win32cred.CRED_TYPE_GENERIC
            )
            return cred['CredentialBlob'].decode('utf-16')
        except ImportError:
            raise ImportError("pywin32 package is required for WindowsCredentialManager")
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret: {str(e)}")

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            import win32cred
            credential = {
                'Type': win32cred.CRED_TYPE_GENERIC,
                'TargetName': f"mimecast/{secret_name}",
                'UserName': 'mimecast',
                'CredentialBlob': secret_value.encode('utf-16'),
                'Persist': win32cred.CRED_PERSIST_LOCAL_MACHINE
            }
            win32cred.CredWrite(credential, 0)
        except ImportError:
            raise ImportError("pywin32 package is required for WindowsCredentialManager")
        except Exception as e:
            raise ValueError(f"Failed to store secret: {str(e)}")

def get_recommended_storage():
    """
    Get the recommended storage method based on the OS
    Returns tuple of (method_name, class, requires_package, package_name)
    """
    if sys.platform == 'win32':
        try:
            import win32cred
            return ("Windows Credential Manager", WindowsCredentialManager, False, None)
        except ImportError:
            return ("Windows Credential Manager", WindowsCredentialManager, True, "pywin32")
    else:  # Linux, macOS, etc.
        try:
            storage = KeyringStorage()
            if storage.is_available():
                return ("System Keyring", KeyringStorage, False, None)
            return ("System Keyring", KeyringStorage, True, "keyring")
        except ImportError:
            return ("System Keyring", KeyringStorage, True, "keyring")

def get_env_var_storage():
    """Get environment variable storage as fallback"""
    return ("Environment Variables", EnvVarStorage, False, None)

class LocalSecureStorage(VaultProvider):
    """
    Main interface for local secure storage that delegates to the selected backend
    """
    def __init__(self, method: str = None):
        """
        Initialize local secure storage
        
        Args:
            method: Storage method to use. If None, will use the first available method
        """
        self.available_methods = get_available_storage_methods()
        if not self.available_methods:
            raise RuntimeError("No local storage methods available")
        
        if method is None:
            # Use first available method
            self.method_name, storage_class = self.available_methods[0]
        else:
            # Find requested method
            for method_name, storage_class in self.available_methods:
                if method_name.lower() == method.lower():
                    self.method_name = method_name
                    break
            else:
                raise ValueError(f"Storage method '{method}' not available")
        
        self.storage = storage_class()

    def get_secret(self, secret_name: str) -> str:
        return self.storage.get_secret(secret_name)

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        self.storage.set_secret(secret_name, secret_value)