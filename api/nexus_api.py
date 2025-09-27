"""
Nexus Mods API client for Stalker 2 Mod Manager
"""

import requests
import os
import time
import hashlib
import logging
from typing import Optional, Dict, Any, List, Callable
import re
from urllib.parse import urlparse, urljoin
from pathlib import Path
import config

# Set up logging
logger = logging.getLogger(__name__)


class NexusAPIError(Exception):
    """Exception raised for Nexus API errors"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(NexusAPIError):
    """Exception raised when rate limits are exceeded"""
    
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message)
        self.retry_after = retry_after


class NexusModsClient:
    """Client for interacting with the Nexus Mods API"""
    
    BASE_URL = config.NEXUS_API_BASE
    GAME_DOMAIN = config.NEXUS_GAME_DOMAIN
    
    # Rate limiting constants
    RATE_LIMIT_DELAY = 1.0  # Minimum delay between requests
    MAX_RETRIES = 3
    TIMEOUT = 30
    
    def __init__(self, api_key: str):
        """Initialize the Nexus Mods API client"""
        self.api_key = api_key
        self.session = requests.Session()
        
        # Create a proper User-Agent string with system info
        import platform
        system_info = f"{platform.system()}_{platform.release()}"
        architecture = platform.machine()
        python_version = f"Python/{platform.python_version()}"
        
        user_agent = f"Stalker2ModManager/1.0 ({system_info}; {architecture}) {python_version}"
        
        self.session.headers.update({
            "apikey": api_key,
            "User-Agent": user_agent,
            "Content-Type": "application/json"
        })
        self.last_request_time = 0
        
        # Rate limiting tracking
        self.daily_remaining = None
        self.hourly_remaining = None
        self.daily_reset = None
        self.hourly_reset = None
        
        logger.info(f"Initialized Nexus Mods API client with User-Agent: {user_agent}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make a rate-limited request to the Nexus API"""
        # Rate limiting
        time_since_last = time.time() - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        
        url = urljoin(self.BASE_URL.rstrip('/') + '/', endpoint.lstrip('/'))

        for attempt in range(self.MAX_RETRIES):
            try:
                logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.TIMEOUT,
                    **kwargs
                )
                
                self.last_request_time = time.time()
                
                # Parse rate limiting headers
                self._parse_rate_limit_headers(response)
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited. Retry after {retry_after} seconds")
                    
                    if attempt < self.MAX_RETRIES - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        raise RateLimitError(
                            f"Rate limit exceeded. Retry after {retry_after} seconds",
                            retry_after=retry_after
                        )
                
                # Handle other HTTP errors
                if not response.ok:
                    error_msg = f"API request failed with status {response.status_code}"
                    try:
                        error_data = response.json()
                        if "message" in error_data:
                            error_msg = error_data["message"]
                    except:
                        error_msg = response.text[:200] if response.text else error_msg
                    
                    raise NexusAPIError(error_msg, response.status_code, response.json() if response.text else None)
                
                return response
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise NexusAPIError(f"Network error after {self.MAX_RETRIES} attempts: {e}")
        
        raise NexusAPIError("Max retries exceeded")
    
    def _parse_rate_limit_headers(self, response: requests.Response):
        """Parse rate limiting headers from the response"""
        headers = response.headers
        
        # Parse rate limit headers
        self.daily_remaining = headers.get('X-RL-Daily-Remaining')
        self.hourly_remaining = headers.get('X-RL-Hourly-Remaining')
        self.daily_reset = headers.get('X-RL-Daily-Reset')
        self.hourly_reset = headers.get('X-RL-Hourly-Reset')
        
        if self.daily_remaining is not None:
            try:
                self.daily_remaining = int(self.daily_remaining)
            except (ValueError, TypeError):
                self.daily_remaining = None
        
        if self.hourly_remaining is not None:
            try:
                self.hourly_remaining = int(self.hourly_remaining)
            except (ValueError, TypeError):
                self.hourly_remaining = None
        
        # Log rate limit status if we're getting low
        if self.daily_remaining is not None and self.daily_remaining < 100:
            logger.warning(f"Daily API requests remaining: {self.daily_remaining}")
        
        if self.hourly_remaining is not None and self.hourly_remaining < 10:
            logger.warning(f"Hourly API requests remaining: {self.hourly_remaining}")
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return {
            "daily_remaining": self.daily_remaining,
            "hourly_remaining": self.hourly_remaining,
            "daily_reset": self.daily_reset,
            "hourly_reset": self.hourly_reset
        }
    
    def validate_api_key(self) -> Dict[str, Any]:
        """Validate the API key and return user information"""
        try:
            response = self._make_request("GET", "/users/validate.json")
            user_data = response.json()
            
            logger.info(f"API key validated for user: {user_data.get('name', 'Unknown')}")
            return user_data
            
        except NexusAPIError as e:
            logger.error(f"API key validation failed: {e}")
            raise
    
    def get_mod_info(self, mod_id: int) -> Dict[str, Any]:
        """Get mod information from Nexus Mods"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}.json"
            response = self._make_request("GET", endpoint)
            mod_data = response.json()
            
            logger.info(f"Retrieved mod info for ID {mod_id}: {mod_data.get('name', 'Unknown')}")
            return mod_data
            
        except NexusAPIError as e:
            logger.error(f"Failed to get mod info for ID {mod_id}: {e}")
            raise
    
    def get_mod_files(self, mod_id: int, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get list of files for a mod with optional category filtering"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/files.json"
            
            # Add category filter if specified
            params = {}
            if category:
                params["category"] = category
            
            response = self._make_request("GET", endpoint, params=params)
            files_data = response.json()
            
            # Extract files array from response
            files = files_data.get("files", []) if isinstance(files_data, dict) else files_data
            
            logger.info(f"Retrieved {len(files)} files for mod ID {mod_id}" + 
                       (f" (category: {category})" if category else ""))
            return files
            
        except NexusAPIError as e:
            logger.error(f"Failed to get mod files for ID {mod_id}: {e}")
            raise
    
    def get_file_info(self, mod_id: int, file_id: int) -> Dict[str, Any]:
        """Get information about a specific file for a mod"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/files/{file_id}.json"
            response = self._make_request("GET", endpoint)
            file_data = response.json()
            
            logger.info(f"Retrieved file info for mod {mod_id}, file {file_id}: {file_data.get('name', 'Unknown')}")
            return file_data
            
        except NexusAPIError as e:
            logger.error(f"Failed to get file info for mod {mod_id}, file {file_id}: {e}")
            raise
    
    def get_download_link(self, mod_id: int, file_id: int, key: Optional[str] = None, 
                         expires: Optional[int] = None) -> Dict[str, Any]:
        """Get download link for a specific mod file
        
        Args:
            mod_id: The mod ID
            file_id: The file ID
            key: Key from .nxm link (required for non-premium users)
            expires: Expiry time from .nxm link (required for non-premium users)
        """
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/files/{file_id}/download_link.json"
            
            # Add non-premium parameters if provided
            params = {}
            if key:
                params["key"] = key
            if expires:
                params["expires"] = expires
            
            response = self._make_request("GET", endpoint, params=params)
            download_data = response.json()
            
            logger.info(f"Retrieved download link for mod {mod_id}, file {file_id}")
            return download_data
            
        except NexusAPIError as e:
            logger.error(f"Failed to get download link for mod {mod_id}, file {file_id}: {e}")
            raise
    
    def download_file(self, download_url: str, file_path: str, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """Download a file from the given URL with progress tracking"""
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Starting download to {file_path}")
            
            # Use a separate session for downloads to avoid interfering with API requests
            with requests.Session() as download_session:
                download_session.headers.update({
                    "User-Agent": "Stalker2ModManager/1.0"
                })
                
                response = download_session.get(download_url, stream=True, timeout=self.TIMEOUT)
                response.raise_for_status()
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback and total_size > 0:
                                progress_callback(downloaded, total_size)
                
                logger.info(f"Download completed: {file_path} ({downloaded:,} bytes)")
                
        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Clean up partial download
            if file_path.exists():
                file_path.unlink()
            raise NexusAPIError(f"Download failed: {e}")
    
    def get_latest_mod_version(self, mod_id: int) -> Optional[str]:
        """Get the latest version string for a mod"""
        try:
            mod_info = self.get_mod_info(mod_id)
            return mod_info.get("version")
        except NexusAPIError:
            return None
    
    def get_main_file_id(self, mod_id: int) -> Optional[int]:
        """Get the main file ID for a mod"""
        try:
            files = self.get_mod_files(mod_id)
            
            # Look for main files first
            main_files = [f for f in files if f.get("category_name") == "MAIN"]
            if main_files:
                # Sort by upload time and get the latest
                main_files.sort(key=lambda x: x.get("uploaded_time", 0), reverse=True)
                return main_files[0].get("file_id")
            
            # Fallback to any file
            if files:
                files.sort(key=lambda x: x.get("uploaded_time", 0), reverse=True)
                return files[0].get("file_id")
            
            return None
            
        except NexusAPIError:
            return None
    
    @staticmethod
    def parse_nexus_url(url: str) -> Optional[Dict[str, Any]]:
        """Parse a Nexus Mods URL and extract mod information"""
        try:
            # Normalize URL
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            
            parsed = urlparse(url)
            
            # Check if it's a Nexus Mods URL
            if not parsed.netloc.endswith("nexusmods.com"):
                return None
            
            # Extract path components
            path_parts = [part for part in parsed.path.split("/") if part]
            
            if len(path_parts) < 3:
                return None
            
            game_domain = path_parts[0]
            if path_parts[1] != "mods":
                return None
            
            # Validate game domain
            if game_domain != NexusModsClient.GAME_DOMAIN:
                return None
            
            try:
                mod_id = int(path_parts[2])
            except ValueError:
                return None
            
            result = {
                "game_domain": game_domain,
                "mod_id": mod_id,
                "url": url
            }
            
            # Extract file ID if present
            if len(path_parts) >= 5 and path_parts[3] == "files":
                try:
                    file_id = int(path_parts[4])
                    result["file_id"] = file_id
                except ValueError:
                    pass
            
            logger.debug(f"Parsed Nexus URL: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse URL '{url}': {e}")
            return None
    
    @staticmethod
    def is_valid_nexus_url(url: str) -> bool:
        """Check if a URL is a valid Nexus Mods URL for Stalker 2"""
        parsed = NexusModsClient.parse_nexus_url(url)
        return parsed is not None and parsed.get("game_domain") == NexusModsClient.GAME_DOMAIN
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current user information (alias for validate_api_key)"""
        return self.validate_api_key()
    
    def get_latest_added_mods(self) -> List[Dict[str, Any]]:
        """Get the 10 latest added mods for Stalker 2"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/latest_added.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get latest added mods: {e}")
            raise
    
    def get_latest_updated_mods(self) -> List[Dict[str, Any]]:
        """Get the 10 latest updated mods for Stalker 2"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/latest_updated.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get latest updated mods: {e}")
            raise
    
    def get_trending_mods(self) -> List[Dict[str, Any]]:
        """Get the 10 trending mods for Stalker 2"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/trending.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get trending mods: {e}")
            raise
    
    def get_updated_mods(self, period: str = "1w") -> List[Dict[str, Any]]:
        """Get mods updated in the given period
        
        Args:
            period: Time period - "1d", "1w", or "1m" (1 day, 1 week, 1 month)
        """
        try:
            if period not in ["1d", "1w", "1m"]:
                raise ValueError("Period must be '1d', '1w', or '1m'")
            
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/updated.json"
            response = self._make_request("GET", endpoint, params={"period": period})
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get updated mods: {e}")
            raise
    
    def get_mod_changelogs(self, mod_id: int) -> List[Dict[str, Any]]:
        """Get all changelogs for a mod"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/changelogs.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get changelogs for mod {mod_id}: {e}")
            raise
    
    def get_tracked_mods(self) -> List[Dict[str, Any]]:
        """Get all mods tracked by the current user"""
        try:
            endpoint = "/user/tracked_mods.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get tracked mods: {e}")
            raise
    
    def track_mod(self, mod_id: int) -> bool:
        """Track a mod for the current user"""
        try:
            endpoint = "/user/tracked_mods.json"
            data = {"mod_id": mod_id}
            params = {"domain_name": self.GAME_DOMAIN}
            
            response = self._make_request("POST", endpoint, params=params, data=data)
            
            # Returns 201 for newly tracked, 200 if already tracking
            success = response.status_code in [200, 201]
            if success:
                logger.info(f"Successfully tracking mod {mod_id}")
            return success
            
        except NexusAPIError as e:
            logger.error(f"Failed to track mod {mod_id}: {e}")
            raise
    
    def untrack_mod(self, mod_id: int) -> bool:
        """Stop tracking a mod for the current user"""
        try:
            endpoint = "/user/tracked_mods.json"
            data = {"mod_id": mod_id}
            params = {"domain_name": self.GAME_DOMAIN}
            
            response = self._make_request("DELETE", endpoint, params=params, data=data)
            success = response.status_code == 200
            
            if success:
                logger.info(f"Stopped tracking mod {mod_id}")
            return success
            
        except NexusAPIError as e:
            logger.error(f"Failed to untrack mod {mod_id}: {e}")
            raise
    
    def get_user_endorsements(self) -> List[Dict[str, Any]]:
        """Get all endorsements for the current user"""
        try:
            endpoint = "/user/endorsements.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get user endorsements: {e}")
            raise
    
    def search_mods_by_md5(self, md5_hash: str) -> Dict[str, Any]:
        """Search for a mod file by MD5 hash"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/md5_search/{md5_hash}.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to search mods by MD5 {md5_hash}: {e}")
            raise
    
    def endorse_mod(self, mod_id: int, version: Optional[str] = None) -> bool:
        """Endorse a mod"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/endorse.json"
            data = {}
            if version:
                data["version"] = version
            
            response = self._make_request("POST", endpoint, data=data)
            success = response.status_code in [200, 201]
            
            if success:
                logger.info(f"Successfully endorsed mod {mod_id}")
            return success
            
        except NexusAPIError as e:
            logger.error(f"Failed to endorse mod {mod_id}: {e}")
            raise
    
    def abstain_from_endorsing_mod(self, mod_id: int, version: Optional[str] = None) -> bool:
        """Abstain from endorsing a mod"""
        try:
            endpoint = f"/games/{self.GAME_DOMAIN}/mods/{mod_id}/abstain.json"
            data = {}
            if version:
                data["version"] = version
            
            response = self._make_request("POST", endpoint, data=data)
            success = response.status_code in [200, 201]
            
            if success:
                logger.info(f"Successfully abstained from endorsing mod {mod_id}")
            return success
            
        except NexusAPIError as e:
            logger.error(f"Failed to abstain from endorsing mod {mod_id}: {e}")
            raise
    
    def get_all_games(self, include_unapproved: bool = False) -> List[Dict[str, Any]]:
        """Get all games supported by Nexus Mods"""
        try:
            endpoint = "/games.json"
            params = {}
            if include_unapproved:
                params["include_unapproved"] = True
            
            response = self._make_request("GET", endpoint, params=params)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get all games: {e}")
            raise
    
    def get_game_info(self, game_domain_name: Optional[str] = None) -> Dict[str, Any]:
        """Get information about a specific game"""
        try:
            domain = game_domain_name or self.GAME_DOMAIN
            endpoint = f"/games/{domain}.json"
            response = self._make_request("GET", endpoint)
            game_data = response.json()
            
            logger.info(f"Retrieved game info for {domain}: {game_data.get('name', 'Unknown')}")
            return game_data
            
        except NexusAPIError as e:
            logger.error(f"Failed to get game info for {game_domain_name or self.GAME_DOMAIN}: {e}")
            raise
    
    def get_colour_schemes(self) -> List[Dict[str, Any]]:
        """Get all colour schemes"""
        try:
            endpoint = "/colourschemes.json"
            response = self._make_request("GET", endpoint)
            return response.json()
        except NexusAPIError as e:
            logger.error(f"Failed to get colour schemes: {e}")
            raise
    
    def close(self):
        """Close the session"""
        self.session.close()
        logger.info("Nexus Mods API client closed")


class ModDownloader:
    """Helper class for downloading and managing mod files"""
    
    def __init__(self, nexus_client: NexusModsClient, download_directory: str):
        self.nexus_client = nexus_client
        self.download_directory = Path(download_directory)
        self.download_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized ModDownloader with directory: {self.download_directory}")
    
    def generate_filename(self, mod_info: Dict[str, Any], file_info: Dict[str, Any]) -> str:
        """Generate a safe filename for the downloaded mod"""
        mod_name = mod_info.get("name", "unknown_mod")
        version = file_info.get("version", mod_info.get("version", "unknown"))
        file_name = file_info.get("file_name", "mod_file")
        
        # Sanitize filename components
        safe_mod_name = re.sub(r'[<>:"/\\|?*]', '_', mod_name)
        safe_version = re.sub(r'[<>:"/\\|?*]', '_', version)
        
        # Keep original extension if possible
        _, ext = os.path.splitext(file_name)
        if not ext:
            ext = ".zip"  # Default extension
        
        # Create filename: ModName_v1.0.0_filename.zip
        filename = f"{safe_mod_name}_v{safe_version}_{file_info.get('file_id', 'unknown')}{ext}"
        
        return filename
    
    def download_mod(self, mod_id: int, file_id: Optional[int] = None, 
                    progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
        """Download a mod and return the file path"""
        try:
            # Get mod information
            mod_info = self.nexus_client.get_mod_info(mod_id)
            
            # Get file ID if not provided
            if file_id is None:
                file_id = self.nexus_client.get_main_file_id(mod_id)
                if file_id is None:
                    raise NexusAPIError(f"No downloadable files found for mod {mod_id}")
            
            # Get file information
            files = self.nexus_client.get_mod_files(mod_id)
            file_info = None
            for f in files:
                if f.get("file_id") == file_id:
                    file_info = f
                    break
            
            if not file_info:
                raise NexusAPIError(f"File {file_id} not found for mod {mod_id}")
            
            # Generate filename
            filename = self.generate_filename(mod_info, file_info)
            file_path = self.download_directory / filename
            
            # Check if file already exists
            if file_path.exists():
                logger.info(f"File already exists: {file_path}")
                return str(file_path)
            
            # Get download link
            download_data = self.nexus_client.get_download_link(mod_id, file_id)
            
            # Extract download URL
            download_url = None
            if isinstance(download_data, list) and download_data:
                download_url = download_data[0].get("URI")
            elif isinstance(download_data, dict):
                download_url = download_data.get("URI")
            
            if not download_url:
                raise NexusAPIError("No download URL returned from API")
            
            # Download the file
            self.nexus_client.download_file(download_url, str(file_path), progress_callback)
            
            logger.info(f"Successfully downloaded mod {mod_id} to {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Failed to download mod {mod_id}: {e}")
            raise
    
    def check_for_updates(self, mod_id: int, current_version: str) -> Optional[Dict[str, Any]]:
        """Check if a newer version of the mod is available"""
        try:
            latest_version = self.nexus_client.get_latest_mod_version(mod_id)
            
            if not latest_version:
                logger.warning(f"Could not determine latest version for mod {mod_id}")
                return None
            
            # Simple version comparison (this could be improved with proper semver)
            if latest_version != current_version:
                mod_info = self.nexus_client.get_mod_info(mod_id)
                return {
                    "mod_id": mod_id,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "mod_name": mod_info.get("name"),
                    "update_available": True
                }
            
            return {
                "mod_id": mod_id,
                "current_version": current_version,
                "latest_version": latest_version,
                "update_available": False
            }
            
        except NexusAPIError as e:
            logger.error(f"Failed to check updates for mod {mod_id}: {e}")
            return None
    
    def get_download_directory(self) -> str:
        """Get the download directory path"""
        return str(self.download_directory)
    
    def cleanup_old_downloads(self, keep_latest: int = 3) -> List[str]:
        """Clean up old download files, keeping only the most recent"""
        removed_files = []
        
        try:
            # Group files by mod name
            mod_files = {}
            for file_path in self.download_directory.glob("*.zip"):
                # Extract mod name from filename (before first underscore)
                parts = file_path.stem.split("_", 1)
                if len(parts) >= 1:
                    mod_name = parts[0]
                    if mod_name not in mod_files:
                        mod_files[mod_name] = []
                    mod_files[mod_name].append(file_path)
            
            # Remove old files for each mod
            for mod_name, files in mod_files.items():
                if len(files) > keep_latest:
                    # Sort by modification time, newest first
                    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # Remove older files
                    for old_file in files[keep_latest:]:
                        logger.info(f"Removing old download: {old_file}")
                        old_file.unlink()
                        removed_files.append(str(old_file))
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
        
        return removed_files