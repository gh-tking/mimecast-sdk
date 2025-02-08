"""
Version management for Mimecast SDK and dependencies
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import pkg_resources
import logging

logger = logging.getLogger(__name__)

@dataclass
class DependencySpec:
    """Specification for a dependency"""
    name: str
    min_version: str
    max_version: Optional[str] = None
    recommended_version: Optional[str] = None
    python_version: str = ">=3.7"

# Core dependencies required for basic SDK functionality
CORE_DEPENDENCIES = {
    'requests': DependencySpec(
        name='requests',
        min_version='2.25.0',
        recommended_version='2.31.0',
        max_version='3.0.0'
    )
}

# Vault integration dependencies
VAULT_DEPENDENCIES = {
    'aws': {
        'boto3': DependencySpec(
            name='boto3',
            min_version='1.26.0',
            recommended_version='1.34.0'
        ),
        'botocore': DependencySpec(
            name='botocore',
            min_version='1.29.0',
            recommended_version='1.34.0'
        )
    },
    'azure': {
        'azure-keyvault-secrets': DependencySpec(
            name='azure-keyvault-secrets',
            min_version='4.0.0',
            recommended_version='4.7.0'
        ),
        'azure-identity': DependencySpec(
            name='azure-identity',
            min_version='1.5.0',
            recommended_version='1.15.0'
        ),
        'azure-core': DependencySpec(
            name='azure-core',
            min_version='1.24.0',
            recommended_version='1.29.5'
        )
    },
    'kubernetes': {
        'kubernetes': DependencySpec(
            name='kubernetes',
            min_version='28.1.0',
            recommended_version='29.0.0'
        )
    },
    'hashicorp': {
        'hvac': DependencySpec(
            name='hvac',
            min_version='1.2.0',
            recommended_version='2.1.0'
        )
    },
    'gcp': {
        'google-cloud-secret-manager': DependencySpec(
            name='google-cloud-secret-manager',
            min_version='2.16.0',
            recommended_version='2.17.0'
        ),
        'google-auth': DependencySpec(
            name='google-auth',
            min_version='2.22.0',
            recommended_version='2.25.2'
        )
    },
    'local': {
        'keyring': DependencySpec(
            name='keyring',
            min_version='24.0.0',
            recommended_version='24.3.0'
        )
    }
}

# Automation framework dependencies
AUTOMATION_DEPENDENCIES = {
    'ansible': {
        'ansible-runner': DependencySpec(
            name='ansible-runner',
            min_version='2.3.1',
            recommended_version='2.3.4'
        ),
        'ansible-core': DependencySpec(
            name='ansible-core',
            min_version='2.15.0',
            recommended_version='2.15.8'
        )
    }
    # Future framework dependencies
    # 'puppet': {...},
    # 'chef': {...},
    # 'salt': {...}
}

def get_installed_version(package_name: str) -> Optional[str]:
    """
    Get installed version of a package

    Args:
        package_name: Name of the package

    Returns:
        str: Version string if installed, None otherwise
    """
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return None

def check_dependency(spec: DependencySpec) -> Dict[str, str]:
    """
    Check a dependency against its specification

    Args:
        spec: Dependency specification

    Returns:
        Dict with status information
    """
    current_version = get_installed_version(spec.name)
    if not current_version:
        return {
            'name': spec.name,
            'status': 'missing',
            'current': None,
            'required': spec.min_version,
            'recommended': spec.recommended_version
        }

    try:
        current = pkg_resources.parse_version(current_version)
        minimum = pkg_resources.parse_version(spec.min_version)
        maximum = (pkg_resources.parse_version(spec.max_version) 
                  if spec.max_version else None)
        recommended = (pkg_resources.parse_version(spec.recommended_version)
                      if spec.recommended_version else None)

        if maximum and current >= maximum:
            status = 'incompatible'
        elif current < minimum:
            status = 'outdated'
        elif recommended and current < recommended:
            status = 'upgradable'
        else:
            status = 'ok'

        return {
            'name': spec.name,
            'status': status,
            'current': current_version,
            'required': spec.min_version,
            'recommended': spec.recommended_version
        }
    except ValueError as e:
        logger.warning(f"Error checking {spec.name} version: {e}")
        return {
            'name': spec.name,
            'status': 'error',
            'current': current_version,
            'required': spec.min_version,
            'recommended': spec.recommended_version
        }

def check_dependencies(
    include_core: bool = True,
    vault_type: Optional[str] = None,
    automation_type: Optional[str] = None
) -> Dict[str, List[Dict[str, str]]]:
    """
    Check all relevant dependencies

    Args:
        include_core: Whether to check core dependencies
        vault_type: Type of vault to check dependencies for
        automation_type: Type of automation framework to check dependencies for

    Returns:
        Dict with dependency status by category
    """
    results = {}

    if include_core:
        results['core'] = [
            check_dependency(spec)
            for spec in CORE_DEPENDENCIES.values()
        ]

    if vault_type and vault_type in VAULT_DEPENDENCIES:
        results['vault'] = [
            check_dependency(spec)
            for spec in VAULT_DEPENDENCIES[vault_type].values()
        ]

    if automation_type and automation_type in AUTOMATION_DEPENDENCIES:
        results['automation'] = [
            check_dependency(spec)
            for spec in AUTOMATION_DEPENDENCIES[automation_type].values()
        ]

    return results

def get_install_requires() -> List[str]:
    """Get core dependencies in pip install_requires format"""
    return [
        f"{spec.name}>={spec.min_version}"
        + (f",<{spec.max_version}" if spec.max_version else "")
        for spec in CORE_DEPENDENCIES.values()
    ]

def get_extras_require() -> Dict[str, List[str]]:
    """Get all optional dependencies in pip extras_require format"""
    extras = {
        'vault': {}
    }

    # Add vault dependencies
    for vault_type, specs in VAULT_DEPENDENCIES.items():
        extras['vault'][vault_type] = [
            f"{spec.name}>={spec.min_version}"
            + (f",<{spec.max_version}" if spec.max_version else "")
            for spec in specs.values()
        ]

    # Add automation dependencies
    extras['automation'] = {
        framework: [
            f"{spec.name}>={spec.min_version}"
            + (f",<{spec.max_version}" if spec.max_version else "")
            for spec in specs.values()
        ]
        for framework, specs in AUTOMATION_DEPENDENCIES.items()
    }

    return extras