# Mimecast SDK

Core Python SDK for interacting with the Mimecast API 2.0, featuring optional cloud vault integrations for secure credential management.

## Features

- 🔒 Secure authentication with automatic token refresh
- 🌍 Regional API endpoint support:
  - Europe (excluding Germany) [eu]
  - Germany [de]
  - United States of America [us]
  - United States of America (USB) [usb]
  - Canada [ca]
  - South Africa [za]
  - Australia [au]
  - Offshore [je]
- 🔄 Built-in rate limiting and retry logic
- 🗄️ Optional vault integrations:
  - AWS Secrets Manager
  - Azure Key Vault
  - Kubernetes Secrets
  - HashiCorp Vault
  - Google Cloud Secret Manager
  - Local secure storage

## Development Setup

1. Install development dependencies:
```bash
pip install -e ".[dev,test]"
```

2. Run tests:
```bash
pytest tests/
```

## Local Development with Vault Providers

To develop with vault integrations, install the required extras:

```bash
# For AWS Secrets Manager
pip install -e ".[aws,dev]"

# For Azure Key Vault
pip install -e ".[azure,dev]"

# For Kubernetes Secrets
pip install -e ".[kubernetes,dev]"

# For HashiCorp Vault
pip install -e ".[hashicorp,dev]"

# For Google Cloud Secret Manager
pip install -e ".[gcp,dev]"

# For local secure storage
pip install -e ".[local,dev]"

# For all providers
pip install -e ".[all,dev]"
```

## Credential Management

The SDK supports several methods for managing credentials securely:

1. Environment Variables:
```bash
# Set environment variables
export MIMECAST_CLIENT_ID=your_client_id
export MIMECAST_CLIENT_SECRET=your_client_secret
export MIMECAST_REGION=us  # Optional: eu, de, us, usb, ca, za, au, je
```

2. System Keyring:
```bash
# First, use the CLI to store credentials securely
pip install mimecast-cli
mimecast init
```

3. Vault Providers:
```python
# AWS Secrets Manager
from mimecast_sdk.vaults.aws import AWSSecretsManager
vault = AWSSecretsManager()
client = MimecastClient.from_vault(vault, "mimecast/credentials")

# Azure Key Vault
from mimecast_sdk.vaults.azure import AzureKeyVault
vault = AzureKeyVault(vault_url="https://your-vault.vault.azure.net/")
client = MimecastClient.from_vault(vault, "mimecast-credentials")

# Kubernetes Secrets
from mimecast_sdk.vaults.kubernetes import KubernetesSecrets
vault = KubernetesSecrets(namespace="your-namespace")
client = MimecastClient.from_vault(vault, "mimecast-credentials")
```

## Usage

### Gateway API

```python
from mimecast_sdk.systems import CloudGatewayAPI

# Method 1: Using environment variables
gateway = CloudGatewayAPI()  # Reads from MIMECAST_* environment variables

# Method 2: Using system keyring
gateway = CloudGatewayAPI.from_keyring()  # Uses credentials stored by 'mimecast init'

# Method 3: Using a vault provider
gateway = CloudGatewayAPI.from_vault(vault, "mimecast/credentials")

# Send an email
response = gateway.send_email(
    to=["recipient@example.com"],
    subject="Test Email",
    text="Hello from Mimecast!",
    track_opens=True,  # Optional tracking
    importance="high"  # Optional importance
)

# Search messages by ID
messages = gateway.search_messages(
    message_id="<message-id>",
    start="2024-02-06T14:53:50Z",
    end="2024-02-06T14:54:50Z"
)

# Advanced message search
messages = gateway.search_messages(
    advanced_query={
        "and": [
            {"subject": {"like": "*important*"}},
            {"from": "sender@example.com"},
            {"received": {"after": "2024-02-01T00:00:00Z"}}
        ]
    },
    source="cloud_archive",
    search_reason="Audit"
)
```

### Directory API

```python
from mimecast_sdk.systems import DirectoryAPI

# Initialize the Directory API client (uses same credential methods)
directory = DirectoryAPI()  # From environment variables
# or
directory = DirectoryAPI.from_keyring()  # From system keyring
# or
directory = DirectoryAPI.from_vault(vault, "mimecast/credentials")

# Find groups
groups = directory.find_groups(
    query="admin",      # Optional search query
    source="cloud",     # "cloud" or "ldap"
    search_both=True    # Search both sources
)

# Create a group
new_group = directory.create_group(
    description="My New Group",
    parent_id="optional_parent_id"  # For creating subgroups
)

# Add member to group by email
result = directory.add_group_member(
    group_id="group_id",
    email="user@example.com",
    notes="Added by SDK"
)

# Add member to group by domain
result = directory.add_group_member(
    group_id="group_id",
    domain="example.com",
    notes="Added entire domain"
)
```

### Low-Level Client

```python
from mimecast_sdk import MimecastClient

# Method 1: Using environment variables
client = MimecastClient()  # Reads from MIMECAST_* environment variables

# Method 2: Using system keyring
client = MimecastClient.from_keyring()  # Uses credentials stored by 'mimecast init'

# Method 3: Using a vault provider
client = MimecastClient.from_vault(vault, "mimecast/credentials")

# Optional: Override region
client = MimecastClient(base_url="https://eu-api.mimecast.com")

# Make API requests
response = client.get("/api/v2/discovery")
data = response.json()

# Post with JSON payload
response = client.post(
    "/api/v2/email/send",
    json={
        "to": ["recipient@example.com"],
        "subject": "Test Email"
    }
)
```

## Using with Vault Providers

### AWS Secrets Manager

```python
from mimecast_sdk.vaults.aws import AWSSecretsManager

vault = AWSSecretsManager(
    region_name="us-east-1",
    # Optional: provide AWS credentials if not using environment variables or IAM roles
    aws_access_key_id="your_access_key_id",
    aws_secret_access_key="your_secret_access_key"
)

# Retrieve secrets
secret = vault.get_secret("mimecast/credentials")
```

### Azure Key Vault

```python
from mimecast_sdk.vaults.azure import AzureKeyVault

vault = AzureKeyVault(
    vault_url="https://your-vault.vault.azure.net/"
)

# Retrieve secrets
secret = vault.get_secret("mimecast-credentials")
```

### Kubernetes Secrets

```python
from mimecast_sdk.vaults.kubernetes import KubernetesSecrets

vault = KubernetesSecrets(
    namespace="your-namespace",
    # Optional: provide path to kubeconfig file
    kubeconfig_path="/path/to/kubeconfig"
)

# Retrieve secrets
secret = vault.get_secret("mimecast-credentials")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.