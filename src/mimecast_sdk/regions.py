"""
Mimecast region configuration
"""
from typing import Dict, Optional

REGIONS = {
    # Europe (excluding Germany)
    'eu': 'https://eu-api.mimecast.com',
    
    # Germany
    'de': 'https://de-api.mimecast.com',
    
    # United States of America
    'us': 'https://us-api.mimecast.com',
    
    # United States of America (USB)
    'usb': 'https://usb-api.mimecast.com',
    
    # Canada
    'ca': 'https://ca-api.mimecast.com',
    
    # South Africa
    'za': 'https://za-api.mimecast.com',
    
    # Australia
    'au': 'https://au-api.mimecast.com',
    
    # Offshore
    'je': 'https://je-api.mimecast.com'
}

REGION_DESCRIPTIONS = {
    'eu': 'Europe (excluding Germany)',
    'de': 'Germany',
    'us': 'United States of America',
    'usb': 'United States of America (USB)',
    'ca': 'Canada',
    'za': 'South Africa',
    'au': 'Australia',
    'je': 'Offshore'
}

def get_api_url(region: str) -> Optional[str]:
    """
    Get the API URL for a given region code
    
    Args:
        region: Region code (e.g., 'us', 'eu', 'de')
        
    Returns:
        API URL for the region or None if region is invalid
    """
    return REGIONS.get(region.lower())

def get_region_description(region: str) -> Optional[str]:
    """
    Get the human-readable description for a region code
    
    Args:
        region: Region code (e.g., 'us', 'eu', 'de')
        
    Returns:
        Description of the region or None if region is invalid
    """
    return REGION_DESCRIPTIONS.get(region.lower())

def list_regions() -> Dict[str, str]:
    """
    Get a dictionary of all available regions and their descriptions
    
    Returns:
        Dict mapping region codes to descriptions
    """
    return REGION_DESCRIPTIONS.copy()