"""
Directory API client for Mimecast
"""
from typing import Dict, Any, List, Optional, Union, Literal
from .base import BaseAPI

class DirectoryAPI(BaseAPI):
    """Directory API client"""
    
    def find_groups(
        self,
        query: Optional[str] = None,
        source: Optional[Literal['ldap', 'cloud']] = None,
        search_both: bool = True
    ) -> Dict[str, Any]:
        """
        Find groups in LDAP and/or cloud directory
        
        Args:
            query: Search query string (optional)
            source: Source to search ('ldap' or 'cloud')
            search_both: Whether to search both LDAP and cloud when source is None
            
        Returns:
            Dict containing the search results
            
        Example response:
            {
                "meta": {
                    "status": 200
                },
                "data": [
                    {
                        "folders": [
                            {
                                "id": "group_id",
                                "description": "Group description",
                                "emailAddress": "group@example.com",
                                "name": "Group Name",
                                "parentId": "parent_group_id",
                                "source": "ldap",
                                "type": "group_type"
                            }
                        ]
                    }
                ]
            }
        """
        # Build request data
        if source:
            # Search specific source
            data = [{
                **({"query": query} if query else {}),
                "source": source
            }]
        elif search_both:
            # Search both sources and combine results
            ldap_data = self._post("/api/directory/find-groups", json={
                "data": [{
                    **({"query": query} if query else {}),
                    "source": "ldap"
                }]
            })
            
            cloud_data = self._post("/api/directory/find-groups", json={
                "data": [{
                    **({"query": query} if query else {}),
                    "source": "cloud"
                }]
            })
            
            # Combine results
            combined_folders = []
            if isinstance(ldap_data, list) and ldap_data:
                combined_folders.extend(ldap_data[0].get('folders', []))
            if isinstance(cloud_data, list) and cloud_data:
                combined_folders.extend(cloud_data[0].get('folders', []))
                
            return [{
                'folders': combined_folders
            }]
        else:
            # Default to empty query
            data = [{
                **({"query": query} if query else {})
            }]
            
        return self._post("/api/directory/find-groups", json={"data": data})
        
    def add_group_member(
        self,
        group_id: str,
        email: Optional[str] = None,
        domain: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add a member to a group
        
        Args:
            group_id: ID of the group to add the member to
            email: Email address of the member to add (mutually exclusive with domain)
            domain: Domain of the member (mutually exclusive with email)
            notes: Additional notes about the member (optional)
            
        Returns:
            Dict containing the response status
            
        Example response:
            {
                "meta": {
                    "status": 200
                },
                "data": [
                    {
                        "emailAddress": "user@example.com",
                        "domain": "example.com",
                        "id": "group_id",
                        "status": "updated"
                    }
                ]
            }
            
        Raises:
            ValueError: If neither email nor domain is provided, or if both are provided
        """
        if not (email or domain):
            raise ValueError("Either email or domain must be provided")
        if email and domain:
            raise ValueError("Only one of email or domain can be provided")
            
        data = {
            "data": [{
                "id": group_id,
                **({"emailAddress": email} if email else {"domain": domain}),
                **({"notes": notes} if notes else {})
            }]
        }
        
        return self._post("/api/directory/add-group-member", json=data)
        
    def create_group(
        self,
        description: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new group/folder
        
        Args:
            description: Description/name of the group
            parent_id: ID of the parent group (optional, for creating subgroups)
            
        Returns:
            Dict containing the created group information
            
        Example response:
            {
                "meta": {
                    "status": 200
                },
                "data": [
                    {
                        "id": "new_group_id",
                        "description": "New Group",
                        "parentId": "parent_group_id",
                        "source": "cloud",
                        "userCount": 0,
                        "folderCount": 0
                    }
                ]
            }
        """
        data = {
            "data": [{
                "description": description,
                **({"parentId": parent_id} if parent_id else {})
            }]
        }
        
        return self._post("/api/directory/create-group", json=data)
        
    def get_group_members(
        self,
        group_id: str
    ) -> Dict[str, Any]:
        """
        Get members of a specific group using the cloud gateway endpoint
        
        Args:
            group_id: ID of the group to get members from
            
        Returns:
            Dict containing the group members
            
        Example response:
            {
                "meta": {
                    "status": 200,
                    "pagination": {
                        "pageSize": 25,
                        "pageToken": "next_page_token",
                        "next": "..."
                    }
                },
                "data": [
                    {
                        "id": "member_id",
                        "emailAddress": "user@example.com",
                        "internal": true,
                        "type": "user",
                        "status": "active"
                    }
                ]
            }
        """
        endpoint = f"/directory/cloud-gateway/v1/groups/{group_id}/members"
        return self._get(endpoint)