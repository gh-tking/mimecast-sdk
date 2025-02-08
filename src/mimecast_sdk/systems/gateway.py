"""
Cloud Gateway API implementation
"""
import os
import base64
import mimetypes
import hashlib
import requests
import concurrent.futures
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from io import BytesIO
from .base import BaseAPI

class CloudGatewayAPI(BaseAPI):
    """
    Mimecast Cloud Gateway API

    Endpoints for managing email security, targeted threat protection,
    and gateway configurations.
    """
    
    def _calculate_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Calculate SHA256 hash of a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            SHA256 hash of the file
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files efficiently
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
        
    def _upload_single_file(
        self,
        file_info: Dict[str, Any],
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file using its pre-signed URL
        
        Args:
            file_info: Dict containing file info and upload URL
            content_type: Optional MIME type for the file
            
        Returns:
            Dict containing upload result
        """
        file_path = file_info['path']
        upload_url = file_info['urls'][0]
        
        # Detect content type if not provided
        if not content_type:
            detected_type, _ = mimetypes.guess_type(str(file_path))
            content_type = detected_type or 'application/octet-stream'
            
        # Use FileManager for safe file reading
        from ..file_utils import FileManager
        file_manager = FileManager(str(file_path))
        file_data = file_manager.safe_read(binary=True)
        
        # Upload the file
        response = requests.put(
            upload_url,
            data=file_data,
            headers={
                'Content-Type': 'application/octet-stream',
                'Accept': 'application/json'
            }
        )
        response.raise_for_status()
        
        # Parse response
        upload_response = response.json()
        file_id = upload_response.get('id')
        file_size = os.path.getsize(file_path)
        
        return {
            'url': upload_url,
            'file_id': file_id,
            'success': response.status_code == 200,
            'size': file_size,
            'filename': os.path.basename(str(file_path)),
            'content_type': content_type,
            'path': str(file_path)
        }
        
    def _get_upload_info(
        self,
        file_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get upload URL for a single file
        
        Args:
            file_info: Dict containing file hash and size
            
        Returns:
            Dict containing upload URL and other info
        """
        data = {"data": [{
            "sha256": file_info["sha256"],
            "fileSize": file_info["fileSize"]
        }]}
        
        response = self._post("/api/file/file-upload", json=data)
        if not response or not response[0].get('urls'):
            raise ValueError("Failed to get upload URL from Mimecast")
            
        return {
            'path': file_info['path'],
            'urls': response[0]['urls']
        }
    
    def _prepare_attachment(
        self,
        file_path: Union[str, Path],
        content_id: Optional[str] = None,
        content_disposition: Optional[str] = None,
        extra_headers: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Prepare a file attachment for sending via email
        
        Args:
            file_path: Path to the file to attach
            content_id: Optional Content-ID for inline attachments
            content_disposition: Optional Content-Disposition (inline or attachment)
            extra_headers: Optional list of extra headers as name-value pairs
            
        Returns:
            Dictionary containing the attachment details
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValueError(f"File not found: {file_path}")
            
        # Get file size
        size = file_path.stat().st_size
        
        # Detect content type
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'
            
        # Read and encode file content
        with open(file_path, 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
            
        attachment = {
            'filename': file_path.name,
            'size': size,
            'content': content,
            'contentType': content_type,
            'contentTransferEncoding': 'base64'
        }
        
        # Add optional fields
        if content_id:
            attachment['contentId'] = content_id
        if content_disposition:
            attachment['contentDisposition'] = content_disposition
        if extra_headers:
            attachment['extraHeaders'] = extra_headers
            
        return attachment

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._get("/api/v2/account/get-account")

    def get_ttp_url_logs(
        self,
        from_date: str,
        to_date: str,
        scan_result: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get Targeted Threat Protection URL protection logs

        Args:
            from_date: Start date in ISO format
            to_date: End date in ISO format
            scan_result: Filter by scan result
            **kwargs: Additional query parameters
        """
        data = {
            "meta": {
                "pagination": kwargs.get("pagination", {}),
            },
            "data": [{
                "from": from_date,
                "to": to_date
            }]
        }
        if scan_result:
            data["data"][0]["scanResult"] = scan_result

        return self._post("/api/v2/ttp/url/get-logs", json=data)

    def get_dlp_policies(self) -> Dict[str, Any]:
        """Get DLP policies"""
        return self._get("/api/v2/dlp/get-policies")
        
    def release_held_message(
        self,
        message_id: str,
        action: str,
        reason: str
    ) -> Dict[str, Any]:
        """
        Release or reject a message that is currently on hold
        
        Args:
            message_id: ID of the message to release/reject
            action: Action to take ('release' or 'reject')
            reason: Reason for the action
            
        Returns:
            Dict containing the response status
            
        Raises:
            ValueError: If action is not 'release' or 'reject'
        """
        if action not in ('release', 'reject'):
            raise ValueError("action must be either 'release' or 'reject'")
            
        data = {
            "data": [{
                "id": message_id,
                "action": action,
                "reason": reason
            }]
        }
        
        return self._post("/api/gateway/hold-release", json=data)
        
    def get_hold_messages(
        self,
        admin: bool = False,
        end: Optional[str] = None,
        field_name: Optional[str] = None,
        field_value: Optional[str] = None,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a list of messages currently on hold
        
        Args:
            admin: Whether to return messages held for administrative review
            end: End date for message search in ISO format (e.g., "2024-02-06T14:53:50Z")
            field_name: Field name to search by (e.g., "from", "to", "subject")
            field_value: Value to search for in the specified field
            page_size: Number of results per page (optional)
            page_token: Token for retrieving the next page (optional)
            
        Returns:
            Dict containing the list of held messages and pagination info
            
        Example response:
            {
                "meta": {
                    "status": 200,
                    "pagination": {
                        "pageSize": 25,
                        "pageToken": "next_page_token",
                        "next": "https://api.services.mimecast.com/api/gateway/get-hold-message-list?token=next_page_token"
                    }
                },
                "data": [
                    {
                        "id": "message_id",
                        "subject": "Message Subject",
                        "from": "sender@example.com",
                        "to": ["recipient@example.com"],
                        "received": "2024-02-06T14:53:50Z",
                        "holdType": "admin",
                        ...
                    }
                ]
            }
        """
        data = {
            "data": [{
                "admin": admin
            }]
        }
        
        # Add optional end date
        if end:
            data["data"][0]["end"] = end
            
        # Add optional search criteria
        if field_name and field_value:
            data["data"][0]["searchBy"] = {
                "fieldName": field_name,
                "value": field_value
            }
            
        # Add pagination parameters
        if page_size or page_token:
            data["meta"] = {
                "pagination": {
                    **({"pageSize": page_size} if page_size else {}),
                    **({"pageToken": page_token} if page_token else {})
                }
            }
            
        return self._post("/api/gateway/get-hold-message-list", json=data)
        
    def search_messages(
        self,
        message_id: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        advanced_query: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        search_reason: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        page_size: Optional[int] = None,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for messages using the message-finder API
        
        Args:
            message_id: Message ID to search for (simple search)
            start: Start date in ISO format (e.g., "2024-02-06T00:00:00+0000")
            end: End date in ISO format
            advanced_query: Advanced search query parameters (see API docs for details)
            source: Source of the search (e.g., "cloud_archive")
            search_reason: Reason for performing the search
            search_fields: List of fields to search in
            page_size: Number of results per page
            page_token: Token for pagination
            
        Returns:
            Dict containing search results and pagination info
            
        Example advanced query:
            {
                "and": [
                    {"from": "sender@example.com"},
                    {"subject": {"like": "*important*"}},
                    {"received": {"after": "2024-01-01T00:00:00+0000"}}
                ]
            }
        """
        # Build the request data
        data = {
            "meta": {
                "pagination": {
                    "pageSize": page_size,
                    "pageToken": page_token
                } if page_size or page_token else {}
            },
            "data": [{}]
        }
        
        # Simple message ID search
        if message_id:
            data["data"][0].update({
                "messageId": message_id,
                "start": start,
                "end": end
            })
        # Advanced search
        elif advanced_query:
            data["data"][0]["advancedTrackAndTraceOptions"] = {
                **advanced_query,
                "start": start,
                "end": end,
                "source": source,
                "searchReason": search_reason,
                "searchFields": search_fields
            }
            # Remove None values from advancedTrackAndTraceOptions
            data["data"][0]["advancedTrackAndTraceOptions"] = {
                k: v for k, v in data["data"][0]["advancedTrackAndTraceOptions"].items() 
                if v is not None
            }
        else:
            raise ValueError("Either message_id or advanced_query must be provided")
        
        # Remove None values from top level
        data["data"][0] = {k: v for k, v in data["data"][0].items() if v is not None}
        
        # Remove pagination if not needed
        if not data["meta"]["pagination"]:
            del data["meta"]["pagination"]
            
        return self._post("/api/message-finder/search", json=data)
        
    def get_upload_urls(self, file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
        """
        Get pre-signed URLs for multiple file uploads
        
        Args:
            file_paths: List of paths to the files to upload
            
        Returns:
            Dict containing upload URLs and other details for each file
            
        Raises:
            ValueError: If any file doesn't exist
        """
        # Convert all paths to Path objects and validate
        files = []
        for path in file_paths:
            file_path = Path(path)
            if not file_path.exists():
                raise ValueError(f"File not found: {file_path}")
            
            # Calculate hash and size for each file
            file_hash = self._calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)
            
            files.append({
                "sha256": file_hash,
                "fileSize": file_size,
                "path": file_path  # Store path for reference
            })
        
        # Request upload URLs for all files
        data = {"data": [{
            "sha256": f["sha256"],
            "fileSize": f["fileSize"]
        } for f in files]}
        
        response = self._post("/api/file/file-upload", json=data)
        
        # Map files to their responses
        results = []
        if response:
            for i, file_info in enumerate(files):
                if i < len(response):
                    url_info = response[i]
                    results.append({
                        'path': str(file_info['path']),
                        'urls': url_info.get('urls', []),
                        'file_id': url_info.get('id')
                    })
        
        return results
        
    def get_upload_url(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get a pre-signed URL for a single file upload
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            Dict containing:
            - url: Pre-signed URL for uploading the file
            - id: File ID to reference in other API calls
        """
        response = self.get_upload_urls([file_path])
        return response[0] if response else None
        
    def upload_files(
        self,
        file_paths: List[Union[str, Path]],
        content_types: Optional[Dict[str, str]] = None,
        max_workers: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Upload multiple files to Mimecast using the file-upload endpoint
        
        Args:
            file_paths: List of paths to the files to upload
            content_types: Optional dict mapping filenames to MIME types
            max_workers: Maximum number of concurrent uploads (default: min(32, os.cpu_count() + 4))
            
        Returns:
            List of dicts, each containing:
            - url: Pre-signed URL for uploading the file
            - id: File ID to reference in other API calls
            - size: File size in bytes
            - filename: Name of the file
            - content_type: MIME type of the file
            - success: Whether the upload was successful
            
        Raises:
            ValueError: If any file doesn't exist
            requests.exceptions.RequestException: If any upload fails
        """
        # Convert paths to Path objects and validate
        file_paths = [Path(p) for p in file_paths]
        for path in file_paths:
            if not path.exists():
                raise ValueError(f"File not found: {path}")
            
        # Calculate hash and size for each file
        files = []
        for path in file_paths:
            file_hash = self._calculate_file_hash(path)
            file_size = os.path.getsize(path)
            files.append({
                "sha256": file_hash,
                "fileSize": file_size,
                "path": path
            })
            
        # Get upload URLs for each file concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit tasks to get upload URLs
            upload_info_futures = [
                executor.submit(self._get_upload_info, file_info)
                for file_info in files
            ]
            
            # Wait for all upload URLs
            upload_infos = []
            for future in concurrent.futures.as_completed(upload_info_futures):
                try:
                    upload_infos.append(future.result())
                except Exception as e:
                    # If any URL request fails, cancel remaining tasks
                    for f in upload_info_futures:
                        f.cancel()
                    raise e
                    
            # Submit tasks to upload files
            content_types = content_types or {}
            upload_futures = [
                executor.submit(
                    self._upload_single_file,
                    info,
                    content_types.get(os.path.basename(str(info['path'])))
                )
                for info in upload_infos
            ]
            
            # Wait for all uploads to complete
            results = []
            for future in concurrent.futures.as_completed(upload_futures):
                try:
                    results.append(future.result())
                except Exception as e:
                    # If any upload fails, cancel remaining tasks
                    for f in upload_futures:
                        f.cancel()
                    raise e
            
        # Sort results to match input order
        results.sort(key=lambda r: file_paths.index(Path(r['path'])))
        return results
        
    def upload_file(
        self,
        file_path: Union[str, Path],
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a single file to Mimecast using the file-upload endpoint
        
        Args:
            file_path: Path to the file to upload
            content_type: Optional MIME type. If not provided, it will be detected
            
        Returns:
            Dict containing:
            - url: Pre-signed URL for uploading the file
            - id: File ID to reference in other API calls
            - size: File size in bytes
            - filename: Name of the file
            - content_type: MIME type of the file
            
        Raises:
            ValueError: If the file doesn't exist
            requests.exceptions.RequestException: If the upload fails
        """
        content_types = {os.path.basename(file_path): content_type} if content_type else None
        results = self.upload_files([file_path], content_types)
        return results[0] if results else None

    def send_email(
        self,
        to: List[Union[str, Dict[str, str]]],
        subject: str,
        *,
        html: Optional[Union[str, Dict[str, Any]]] = None,
        text: Optional[str] = None,
        from_email: Optional[Union[str, Dict[str, str]]] = None,
        cc: Optional[List[Union[str, Dict[str, str]]]] = None,
        bcc: Optional[List[Union[str, Dict[str, str]]]] = None,
        reply_to: Optional[Union[str, Dict[str, str]]] = None,
        in_reply_to: Optional[str] = None,
        attachments: Optional[List[Union[str, Dict[str, Any]]]] = None,
        attachment_options: Optional[Dict[str, Dict[str, Any]]] = None,
        file_attachments: Optional[List[Dict[str, Any]]] = None,  # For uploaded files
        headers: Optional[Dict[str, str]] = None,
        importance: Optional[str] = None,
        track_opens: Optional[bool] = None,
        prevent_browser_link_preview: Optional[bool] = None,
        permit_unsubscribe_through_email: Optional[bool] = None,
        html_options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email through Mimecast

        Args:
            to: List of recipient email addresses
            subject: Email subject
            html: HTML content of the email (optional)
            text: Plain text content of the email (optional)
            from_email: Sender email address (optional)
            cc: List of CC recipient email addresses (optional)
            bcc: List of BCC recipient email addresses (optional)
            reply_to: Reply-to email address (optional)
            attachments: List of attachment objects (optional)
                Each attachment should be a dict with:
                - filename: Name of the file
                - content_type: MIME type
                - data: Base64 encoded file content
            headers: Custom email headers (optional)
            importance: Email importance level (optional)
                One of: 'normal', 'low', 'high'
            track_opens: Enable open tracking (optional)
            prevent_browser_link_preview: Prevent link previews in email clients (optional)
            permit_unsubscribe_through_email: Allow unsubscribe via email (optional)

        Returns:
            API response data

        Raises:
            ValueError: If neither html nor text content is provided
        """
        if not (html or text):
            raise ValueError("Either html or text content must be provided")

        # Format email addresses as objects
        def format_email(email):
            if isinstance(email, str):
                return {"emailAddress": email}
            elif isinstance(email, dict):
                # Allow pre-formatted email objects with displayableName
                if "emailAddress" not in email:
                    raise ValueError("Email object must contain 'emailAddress' field")
                return email
            else:
                raise ValueError("Email must be a string or dict")
                
        # Format attachments from uploaded files
        def format_attachment(attachment):
            if isinstance(attachment, str):
                # Local file path - use regular attachment handling
                return attachment
            elif isinstance(attachment, dict):
                # Pre-formatted attachment object
                return attachment
            else:
                raise ValueError("Attachment must be a string path or dict")
                
        formatted_to = [format_email(email) for email in to]
        formatted_cc = [format_email(email) for email in cc] if cc else None
        formatted_bcc = [format_email(email) for email in bcc] if bcc else None
        formatted_from = format_email(from_email) if from_email else None
        formatted_reply_to = format_email(reply_to) if reply_to else None
        
        # Combine regular attachments and file attachments
        all_attachments = []
        if attachments:
            all_attachments.extend(format_attachment(a) for a in attachments)
        if file_attachments:
            all_attachments.extend(file_attachments)

        data = {
            "to": formatted_to,
            "subject": subject
        }

        # Add optional fields if provided
        if html:
            if isinstance(html, str):
                # Simple HTML content
                if html_options:
                    # Format with options
                    data["htmlBody"] = {
                        "content": html,
                        **html_options
                    }
                else:
                    data["html"] = html
            else:
                # Pre-formatted HTML body object
                data["htmlBody"] = html
                
        if text:
            data["text"] = text
            
        if in_reply_to:
            data["inReplyTo"] = in_reply_to
        if formatted_from:
            data["from"] = formatted_from
        if formatted_cc:
            data["cc"] = formatted_cc
        if formatted_bcc:
            data["bcc"] = formatted_bcc
        if formatted_reply_to:
            data["replyTo"] = formatted_reply_to
        # Handle attachments (both local files and uploaded files)
        formatted_attachments = []
        attachment_options = attachment_options or {}
        
        # Handle local file attachments
        if attachments:
            for attachment in attachments:
                if isinstance(attachment, str):
                    # It's a file path, prepare the attachment
                    file_path = attachment
                    options = attachment_options.get(os.path.basename(file_path), {})
                    formatted_attachment = self._prepare_attachment(
                        file_path,
                        content_id=options.get('content_id'),
                        content_disposition=options.get('content_disposition'),
                        extra_headers=options.get('extra_headers')
                    )
                    formatted_attachments.append(formatted_attachment)
                else:
                    # It's already a formatted attachment object
                    formatted_attachments.append(attachment)
        
        # Handle uploaded file attachments
        if file_attachments:
            formatted_attachments.extend(file_attachments)
            
        if formatted_attachments:
            data["attachments"] = formatted_attachments
        if headers:
            data["headers"] = headers
        if importance:
            if importance not in ('normal', 'low', 'high'):
                raise ValueError("importance must be one of: normal, low, high")
            data["importance"] = importance
        if track_opens is not None:
            data["trackOpens"] = track_opens
        if prevent_browser_link_preview is not None:
            data["preventBrowserLinkPreview"] = prevent_browser_link_preview
        if permit_unsubscribe_through_email is not None:
            data["permitUnsubscribeThroughEmail"] = permit_unsubscribe_through_email

        return self._post("/api/email/send-email", json={"data": [data]})

    # Add more Cloud Gateway specific endpoints here:
    # - Email security policies
    # - TTP configurations
    # - Gateway routing
    # - etc.