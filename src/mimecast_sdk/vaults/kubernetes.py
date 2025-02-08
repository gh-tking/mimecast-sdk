"""
Kubernetes Secrets implementation
"""
import base64
from typing import Optional
from kubernetes import client, config
from .base import VaultProvider

class KubernetesSecrets(VaultProvider):
    def __init__(
        self,
        namespace: str = "default",
        kubeconfig_path: Optional[str] = None
    ):
        if kubeconfig_path:
            config.load_kube_config(kubeconfig_path)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
        
        self.namespace = namespace
        self.v1 = client.CoreV1Api()

    def get_secret(self, secret_name: str) -> str:
        try:
            secret = self.v1.read_namespaced_secret(secret_name, self.namespace)
            # Kubernetes stores secrets as base64-encoded strings
            return base64.b64decode(secret.data[secret_name]).decode()
        except Exception as e:
            raise ValueError(f"Failed to retrieve secret: {str(e)}")

    def set_secret(self, secret_name: str, secret_value: str) -> None:
        try:
            # Encode the secret value in base64
            encoded_value = base64.b64encode(secret_value.encode()).decode()
            
            # Create the secret object
            secret = client.V1Secret(
                metadata=client.V1ObjectMeta(name=secret_name),
                data={secret_name: encoded_value}
            )
            
            try:
                self.v1.create_namespaced_secret(self.namespace, secret)
            except client.rest.ApiException as e:
                if e.status == 409:  # Conflict, secret already exists
                    self.v1.replace_namespaced_secret(
                        secret_name, self.namespace, secret
                    )
                else:
                    raise
        except Exception as e:
            raise ValueError(f"Failed to store secret: {str(e)}")