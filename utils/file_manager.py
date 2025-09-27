"""
File management utilities for Stalker 2 Mod Manager
"""

import os
import shutil
import zipfile
import tempfile
import hashlib
import logging
import json
import re
import sys
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import stat
import config


class ArchiveManager:
    """Manages mod archive files"""
    
    def __init__(self, archives_directory: str):
        """Initialize with the directory for storing mod archives"""
        self.archives_directory = Path(archives_directory)
        self.archives_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def extract_archive_contents(self, archive_path: str) -> List[Dict[str, Any]]:
        """Extract and list contents of a mod archive"""
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        if not self.is_valid_archive(str(archive_path)):
            raise ValueError(f"Invalid archive format: {archive_path}")
        
        contents = []
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for info in zip_ref.infolist():
                    # Skip directories and focus on files
                    if not info.is_dir():
                        # Normalize path separators for Windows
                        normalized_path = info.filename.replace('/', os.sep)
                        
                        # Get file info
                        file_info = {
                            'path': normalized_path,
                            'filename': os.path.basename(info.filename),
                            'size': info.file_size,
                            'compressed_size': info.compress_size,
                            'date_time': datetime(*info.date_time),
                            'crc': info.CRC,
                            'is_directory': info.is_dir(),
                            'directory': os.path.dirname(normalized_path),
                            'extension': Path(info.filename).suffix.lower(),
                            'relative_path': info.filename
                        }
                        
                        contents.append(file_info)
            
            # Sort by path for consistent ordering
            contents.sort(key=lambda x: x['path'])
            self.logger.info(f"Extracted {len(contents)} files from {archive_path.name}")
            
            return contents
            
        except zipfile.BadZipFile:
            raise ValueError(f"Corrupted or invalid zip file: {archive_path}")
        except Exception as e:
            self.logger.error(f"Error extracting archive {archive_path}: {e}")
            raise
    
    def get_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename for storing the archive"""
        original_path = Path(original_filename)
        base_name = original_path.stem
        extension = original_path.suffix
        
        # Start with the original filename
        counter = 0
        unique_name = original_filename
        
        while (self.archives_directory / unique_name).exists():
            counter += 1
            unique_name = f"{base_name}_{counter}{extension}"
        
        return unique_name
    
    def copy_archive(self, source_path: str, mod_name: str) -> str:
        """Copy an archive to the managed directory"""
        source_path = Path(source_path)
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source archive not found: {source_path}")
        
        if not self.is_valid_archive(str(source_path)):
            raise ValueError(f"Invalid archive format: {source_path}")
        
        # Generate a filename based on mod name and original filename
        original_name = source_path.name
        sanitized_mod_name = self._sanitize_filename(mod_name)
        
        # Create a meaningful filename: ModName_OriginalName
        if sanitized_mod_name and sanitized_mod_name.lower() not in original_name.lower():
            new_name = f"{sanitized_mod_name}_{original_name}"
        else:
            new_name = original_name
        
        # Ensure uniqueness
        unique_filename = self.get_unique_filename(new_name)
        destination_path = self.archives_directory / unique_filename
        
        try:
            # Copy the file
            shutil.copy2(source_path, destination_path)
            self.logger.info(f"Copied archive {source_path.name} to {unique_filename}")
            
            # Verify the copy
            if not self._verify_copy(source_path, destination_path):
                destination_path.unlink()  # Remove corrupted copy
                raise RuntimeError("Archive copy verification failed")
            
            return unique_filename
            
        except Exception as e:
            self.logger.error(f"Error copying archive {source_path}: {e}")
            # Clean up partial copy if it exists
            if destination_path.exists():
                try:
                    destination_path.unlink()
                except:
                    pass
            raise
    
    def remove_archive(self, archive_filename: str) -> None:
        """Remove an archive file"""
        archive_path = self.archives_directory / archive_filename
        
        if not archive_path.exists():
            self.logger.warning(f"Archive file not found for removal: {archive_filename}")
            return
        
        try:
            archive_path.unlink()
            self.logger.info(f"Removed archive: {archive_filename}")
        except Exception as e:
            self.logger.error(f"Error removing archive {archive_filename}: {e}")
            raise
    
    def get_archive_info(self, archive_filename: str) -> Dict[str, Any]:
        """Get information about an archive file"""
        archive_path = self.archives_directory / archive_filename
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_filename}")
        
        stat_info = archive_path.stat()
        
        return {
            'filename': archive_filename,
            'path': str(archive_path),
            'size': stat_info.st_size,
            'created': datetime.fromtimestamp(stat_info.st_ctime),
            'modified': datetime.fromtimestamp(stat_info.st_mtime),
            'is_valid': self.is_valid_archive(str(archive_path))
        }
    
    def is_valid_archive(self, file_path: str) -> bool:
        """Check if a file is a valid mod archive"""
        file_path = Path(file_path)
        
        # Check file extension using config
        if file_path.suffix.lower() not in config.SUPPORTED_ARCHIVE_EXTENSIONS:
            return False
        
        # For now, only handle ZIP files (most common for mods)
        if file_path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Try to read the file list - this will fail if corrupted
                    zip_ref.namelist()
                    return True
            except:
                return False
        
        # For other formats, just check if file exists and has content
        return file_path.exists() and file_path.stat().st_size > 0
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename for safe file system usage"""
        if not filename:
            return ""
        
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace spaces with underscores
        filename = filename.replace(' ', '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        
        # Remove leading/trailing underscores
        filename = filename.strip('_')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename
    
    def _verify_copy(self, source_path: Path, destination_path: Path) -> bool:
        """Verify that a file was copied correctly by comparing sizes and checksums"""
        try:
            # Check file sizes
            if source_path.stat().st_size != destination_path.stat().st_size:
                return False
            
            # For small files, compare checksums
            if source_path.stat().st_size < 50 * 1024 * 1024:  # 50MB
                source_hash = self._calculate_file_hash(source_path)
                dest_hash = self._calculate_file_hash(destination_path)
                return source_hash == dest_hash
            
            return True
        except:
            return False
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except:
            return ""


class GameDirectoryManager:
    """Manages deployment of files to the game directory"""
    
    def __init__(self, game_directory: str):
        """Initialize with the game installation directory"""
        self.game_directory = Path(game_directory)
        self.backup_directory = self.game_directory / "_mod_manager_backups"
        self.backup_directory.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
    
    def deploy_files(self, mod_id: int, archive_path: str, 
                    selected_files: List[str]) -> List[str]:
        """Deploy selected files from a mod archive to the game directory"""
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        if not self.validate_game_directory():
            raise RuntimeError("Invalid game directory")
        
        deployed_files = []
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for file_path in selected_files:
                    try:
                        # Normalize the path
                        normalized_path = file_path.replace('/', os.sep)
                        target_path = self.game_directory / normalized_path
                        
                        # Create directory structure if needed
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Backup original file if it exists
                        backup_path = None
                        if target_path.exists():
                            backup_path = self._backup_file(target_path, mod_id)
                        
                        # Extract and copy the file
                        with zip_ref.open(file_path) as source:
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                        
                        # Record the deployment
                        deployment_info = {
                            'deployed_path': str(target_path),
                            'original_archive_path': file_path,
                            'backup_path': backup_path,
                            'deployed_at': datetime.now().isoformat()
                        }
                        
                        deployed_files.append(deployment_info)
                        self.logger.debug(f"Deployed {file_path} to {target_path}")
                        
                    except Exception as e:
                        self.logger.error(f"Error deploying file {file_path}: {e}")
                        # Continue with other files, but log the error
                        continue
            
            self.logger.info(f"Deployed {len(deployed_files)} files for mod {mod_id}")
            return deployed_files
            
        except Exception as e:
            self.logger.error(f"Error deploying files from {archive_path}: {e}")
            # Cleanup any partially deployed files
            self._cleanup_partial_deployment(deployed_files)
            raise
    
    def remove_deployed_files(self, deployed_files: List[str]) -> None:
        """Remove previously deployed files from the game directory"""
        removed_count = 0
        
        for file_info in deployed_files:
            if isinstance(file_info, str):
                # Handle legacy format (just file paths)
                file_path = Path(file_info)
            else:
                # Handle new format (deployment info dict)
                file_path = Path(file_info.get('deployed_path', file_info))
            
            try:
                if file_path.exists():
                    # Check if this is really a mod file and not a game file
                    if self._is_safe_to_remove(file_path):
                        file_path.unlink()
                        removed_count += 1
                        self.logger.debug(f"Removed deployed file: {file_path}")
                    else:
                        self.logger.warning(f"Skipped removal of potentially important file: {file_path}")
                
            except Exception as e:
                self.logger.error(f"Error removing file {file_path}: {e}")
                continue
        
        self.logger.info(f"Removed {removed_count} deployed files")
    
    def backup_original_files(self, files_to_replace: List[str]) -> Dict[str, str]:
        """Create backups of original game files before replacement"""
        backup_mapping = {}
        
        for file_path_str in files_to_replace:
            file_path = Path(file_path_str)
            
            if not file_path.exists():
                continue
            
            try:
                backup_path = self._backup_file(file_path, backup_id="manual")
                if backup_path:
                    backup_mapping[file_path_str] = backup_path
                    self.logger.debug(f"Backed up {file_path} to {backup_path}")
                    
            except Exception as e:
                self.logger.error(f"Error backing up file {file_path}: {e}")
                continue
        
        self.logger.info(f"Created {len(backup_mapping)} file backups")
        return backup_mapping
    
    def restore_original_files(self, backup_mapping: Dict[str, str]) -> None:
        """Restore original game files from backups"""
        restored_count = 0
        
        for original_path, backup_path in backup_mapping.items():
            try:
                original_file = Path(original_path)
                backup_file = Path(backup_path)
                
                if backup_file.exists():
                    # Create directory if needed
                    original_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore the file
                    shutil.copy2(backup_file, original_file)
                    restored_count += 1
                    self.logger.debug(f"Restored {original_path} from backup")
                else:
                    self.logger.warning(f"Backup file not found: {backup_path}")
                    
            except Exception as e:
                self.logger.error(f"Error restoring file {original_path}: {e}")
                continue
        
        self.logger.info(f"Restored {restored_count} files from backups")
    
    def validate_game_directory(self) -> bool:
        """Validate that the directory is a valid Stalker 2 installation"""
        if not self.game_directory.exists():
            return False
        
        # Check for key Stalker 2 files/folders
        # These are common files/folders that should exist in a Stalker 2 installation
        required_items = [
            "Stalker2.exe",  # Main executable
            "Engine",        # Unreal Engine folder
            "Stalker2",      # Game content folder
        ]
        
        # Optional items that indicate a valid installation
        optional_items = [
            "Content",
            "Binaries",
            "Config",
            "Engine.ini"
        ]
        
        required_found = 0
        for item in required_items:
            if (self.game_directory / item).exists():
                required_found += 1
        
        optional_found = 0
        for item in optional_items:
            if (self.game_directory / item).exists():
                optional_found += 1
        
        # Require at least some required items and some optional items
        is_valid = required_found >= 1 and (required_found + optional_found) >= 2
        
        if not is_valid:
            self.logger.warning(f"Game directory validation failed: {self.game_directory}")
            self.logger.debug(f"Required items found: {required_found}/{len(required_items)}")
            self.logger.debug(f"Optional items found: {optional_found}/{len(optional_items)}")
        
        return is_valid
    
    def _backup_file(self, file_path: Path, backup_id: Any) -> Optional[str]:
        """Create a backup of a file"""
        if not file_path.exists():
            return None
        
        try:
            # Create a unique backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.backup_{backup_id}_{timestamp}"
            backup_path = self.backup_directory / backup_name
            
            # Copy the file
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
            
        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {e}")
            return None
    
    def _is_safe_to_remove(self, file_path: Path) -> bool:
        """Check if a file is safe to remove (i.e., it's a mod file, not a game file)"""
        # This is a safety check to prevent removing important game files
        
        # Files in backup directory are never safe to remove via this method
        if self.backup_directory in file_path.parents:
            return False
        
        # For now, be conservative and only remove files in common mod directories
        safe_directories = [
            "Mods",
            "Content/Paks/Mods",
            "Plugins",
            "Data"
        ]
        
        file_str = str(file_path).lower()
        for safe_dir in safe_directories:
            if safe_dir.lower() in file_str:
                return True
        
        # If we can't determine it's safe, don't remove
        return False
    
    def _cleanup_partial_deployment(self, deployed_files: List[Dict[str, Any]]) -> None:
        """Clean up files from a failed deployment"""
        for file_info in deployed_files:
            try:
                deployed_path = Path(file_info['deployed_path'])
                if deployed_path.exists():
                    deployed_path.unlink()
                
                # Restore backup if one was created
                backup_path = file_info.get('backup_path')
                if backup_path:
                    backup_file = Path(backup_path)
                    if backup_file.exists():
                        shutil.copy2(backup_file, deployed_path)
                        
            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")
                continue


class FileConflictResolver:
    """Handles file conflicts during mod deployment"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_conflicts(self, new_files: List[str], 
                        existing_deployments: Dict[int, List[str]]) -> List[Dict[str, Any]]:
        """Detect file conflicts between mods"""
        conflicts = []
        
        # Normalize new file paths for comparison
        new_files_normalized = {self._normalize_path(f): f for f in new_files}
        
        for mod_id, deployed_files in existing_deployments.items():
            for deployed_file in deployed_files:
                # Handle both old format (strings) and new format (dicts)
                if isinstance(deployed_file, dict):
                    deployed_path = deployed_file.get('deployed_path', '')
                else:
                    deployed_path = str(deployed_file)
                
                deployed_normalized = self._normalize_path(deployed_path)
                
                # Check if any new file conflicts with this deployed file
                if deployed_normalized in new_files_normalized:
                    conflict = {
                        'conflicted_file': deployed_path,
                        'new_file': new_files_normalized[deployed_normalized],
                        'existing_mod_id': mod_id,
                        'conflict_type': 'file_overwrite',
                        'severity': self._assess_conflict_severity(deployed_path)
                    }
                    conflicts.append(conflict)
        
        self.logger.info(f"Detected {len(conflicts)} file conflicts")
        return conflicts
    
    def resolve_conflicts(self, conflicts: List[Dict[str, Any]], 
                         resolution_strategy: str) -> Dict[str, Any]:
        """Resolve file conflicts based on strategy"""
        resolution_results = {
            'resolved': [],
            'skipped': [],
            'errors': [],
            'actions_taken': []
        }
        
        for conflict in conflicts:
            try:
                conflicted_file = conflict['conflicted_file']
                new_file = conflict['new_file']
                
                if resolution_strategy == "overwrite":
                    # Allow overwrite - no action needed, deployment will proceed
                    resolution_results['resolved'].append(conflict)
                    resolution_results['actions_taken'].append(f"Will overwrite {conflicted_file}")
                
                elif resolution_strategy == "skip":
                    # Skip the conflicting file
                    resolution_results['skipped'].append(conflict)
                    resolution_results['actions_taken'].append(f"Skipped {new_file}")
                
                elif resolution_strategy == "rename":
                    # Rename the new file to avoid conflict
                    renamed_file = self._generate_renamed_path(new_file)
                    conflict['renamed_to'] = renamed_file
                    resolution_results['resolved'].append(conflict)
                    resolution_results['actions_taken'].append(f"Will rename {new_file} to {renamed_file}")
                
                elif resolution_strategy == "backup_and_overwrite":
                    # Create backup of existing file before overwriting
                    backup_path = self._generate_backup_path(conflicted_file)
                    conflict['backup_path'] = backup_path
                    resolution_results['resolved'].append(conflict)
                    resolution_results['actions_taken'].append(f"Will backup {conflicted_file} and overwrite")
                
                else:
                    # Unknown strategy
                    resolution_results['errors'].append({
                        'conflict': conflict,
                        'error': f"Unknown resolution strategy: {resolution_strategy}"
                    })
                    
            except Exception as e:
                resolution_results['errors'].append({
                    'conflict': conflict,
                    'error': str(e)
                })
        
        self.logger.info(f"Resolved {len(resolution_results['resolved'])} conflicts using strategy: {resolution_strategy}")
        return resolution_results
    
    def _normalize_path(self, file_path: str) -> str:
        """Normalize a file path for comparison"""
        return str(Path(file_path)).lower().replace('\\', '/')
    
    def _assess_conflict_severity(self, file_path: str) -> str:
        """Assess the severity of a file conflict"""
        file_path_lower = file_path.lower()
        
        # Critical files that should never be overwritten carelessly
        critical_patterns = [
            'stalker2.exe',
            'engine.ini',
            'gameusersettings.ini',
            'input.ini'
        ]
        
        for pattern in critical_patterns:
            if pattern in file_path_lower:
                return 'critical'
        
        # Important game files
        important_patterns = [
            '.exe',
            '.dll',
            'config/',
            'engine/',
            'binaries/'
        ]
        
        for pattern in important_patterns:
            if pattern in file_path_lower:
                return 'high'
        
        # Content files (textures, models, etc.)
        content_patterns = [
            'content/',
            'data/',
            '.pak',
            '.uasset',
            '.umap'
        ]
        
        for pattern in content_patterns:
            if pattern in file_path_lower:
                return 'medium'
        
        # Everything else
        return 'low'
    
    def _generate_renamed_path(self, original_path: str) -> str:
        """Generate a renamed path to avoid conflicts"""
        path = Path(original_path)
        base_name = path.stem
        extension = path.suffix
        directory = path.parent
        
        counter = 1
        while True:
            new_name = f"{base_name}_conflict_{counter}{extension}"
            new_path = directory / new_name
            if not new_path.exists():
                return str(new_path)
            counter += 1
    
    def _generate_backup_path(self, original_path: str) -> str:
        """Generate a backup path for an existing file"""
        path = Path(original_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{path.name}.backup_{timestamp}"
        return str(path.parent / backup_name)


class ModFileValidator:
    """Validates mod files and archives"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @staticmethod
    def is_valid_archive(file_path: str) -> bool:
        """Check if a file is a valid mod archive"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return False
        
        # Check file extension using config
        if file_path.suffix.lower() not in config.SUPPORTED_ARCHIVE_EXTENSIONS:
            return False
        
        # Check file size (should be > 0)
        if file_path.stat().st_size == 0:
            return False
        
        # For ZIP files, try to open and validate
        if file_path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # Test the zip file integrity
                    zip_ref.testzip()
                    # Ensure it has some files
                    return len(zip_ref.namelist()) > 0
            except:
                return False
        
        # For other formats, basic checks passed
        return True
    
    def scan_for_malicious_content(self, archive_path: str) -> List[str]:
        """Scan archive for potentially malicious files"""
        warnings = []
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            return ["Archive file not found"]
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    filename = file_info.filename
                    warnings.extend(self._check_file_security(filename, file_info))
                    
        except Exception as e:
            warnings.append(f"Error scanning archive: {e}")
        
        if warnings:
            self.logger.warning(f"Security scan found {len(warnings)} potential issues in {archive_path.name}")
        
        return warnings
    
    def validate_file_paths(self, file_paths: List[str]) -> List[str]:
        """Validate that file paths are safe for deployment"""
        issues = []
        
        for file_path in file_paths:
            issues.extend(self._validate_single_path(file_path))
        
        if issues:
            self.logger.warning(f"Path validation found {len(issues)} issues")
        
        return issues
    
    def _check_file_security(self, filename: str, file_info) -> List[str]:
        """Check a single file for security issues"""
        warnings = []
        filename_lower = filename.lower()
        
        # Check for executable files
        executable_extensions = {'.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.msi'}
        if any(filename_lower.endswith(ext) for ext in executable_extensions):
            warnings.append(f"Executable file detected: {filename}")
        
        # Check for script files
        script_extensions = {'.ps1', '.vbs', '.js', '.jar'}
        if any(filename_lower.endswith(ext) for ext in script_extensions):
            warnings.append(f"Script file detected: {filename}")
        
        # Check for directory traversal attempts
        if '..' in filename or filename.startswith('/') or ':' in filename:
            warnings.append(f"Suspicious path detected: {filename}")
        
        # Check for system directories
        system_dirs = ['windows', 'system32', 'program files']
        if any(sys_dir in filename_lower for sys_dir in system_dirs):
            warnings.append(f"File targets system directory: {filename}")
        
        # Check for hidden files (Windows)
        if filename.startswith('.') and not filename.startswith('./'):
            warnings.append(f"Hidden file detected: {filename}")
        
        # Check file size (files that are too large might be suspicious)
        if hasattr(file_info, 'file_size') and file_info.file_size > 100 * 1024 * 1024:  # 100MB
            warnings.append(f"Large file detected: {filename} ({file_info.file_size} bytes)")
        
        return warnings
    
    def _validate_single_path(self, file_path: str) -> List[str]:
        """Validate a single file path"""
        issues = []
        
        # Check for empty or None paths
        if not file_path or not file_path.strip():
            issues.append("Empty file path")
            return issues
        
        # Check path length
        if len(file_path) > 260:  # Windows MAX_PATH limitation
            issues.append(f"Path too long (>{260} characters): {file_path}")
        
        # Check for invalid characters
        invalid_chars = '<>"|?*'
        for char in invalid_chars:
            if char in file_path:
                issues.append(f"Invalid character '{char}' in path: {file_path}")
        
        # Check for reserved names (Windows)
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        
        path_parts = Path(file_path).parts
        for part in path_parts:
            if part.upper() in reserved_names:
                issues.append(f"Reserved name in path: {part}")
        
        # Check for directory traversal
        if '..' in file_path:
            issues.append(f"Directory traversal detected: {file_path}")
        
        # Check for absolute paths (should be relative)
        if os.path.isabs(file_path):
            issues.append(f"Absolute path detected: {file_path}")
        
        return issues


class TempFileManager:
    """Manages temporary files and cleanup"""
    
    def __init__(self):
        self.temp_dirs = []
        self.temp_files = []
        self.logger = logging.getLogger(__name__)
    
    def create_temp_dir(self, prefix: str = "stalker_mod_") -> str:
        """Create a temporary directory"""
        try:
            temp_dir = tempfile.mkdtemp(prefix=prefix)
            self.temp_dirs.append(temp_dir)
            self.logger.debug(f"Created temporary directory: {temp_dir}")
            return temp_dir
        except Exception as e:
            self.logger.error(f"Error creating temporary directory: {e}")
            raise
    
    def create_temp_file(self, suffix: str = "", prefix: str = "stalker_mod_") -> str:
        """Create a temporary file"""
        try:
            fd, temp_file = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(fd)  # Close the file descriptor
            self.temp_files.append(temp_file)
            self.logger.debug(f"Created temporary file: {temp_file}")
            return temp_file
        except Exception as e:
            self.logger.error(f"Error creating temporary file: {e}")
            raise
    
    def extract_to_temp_dir(self, archive_path: str, selected_files: Optional[List[str]] = None) -> str:
        """Extract archive contents to a temporary directory"""
        temp_dir = self.create_temp_dir()
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                if selected_files:
                    # Extract only selected files
                    for file_path in selected_files:
                        try:
                            zip_ref.extract(file_path, temp_dir)
                        except KeyError:
                            self.logger.warning(f"File not found in archive: {file_path}")
                        except Exception as e:
                            self.logger.error(f"Error extracting {file_path}: {e}")
                else:
                    # Extract all files
                    zip_ref.extractall(temp_dir)
            
            self.logger.info(f"Extracted archive to temporary directory: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            self.logger.error(f"Error extracting archive {archive_path}: {e}")
            # Clean up the temp directory if extraction failed
            self._cleanup_directory(temp_dir)
            raise
    
    def cleanup(self) -> None:
        """Clean up all temporary files and directories"""
        # Clean up temporary files
        for temp_file in self.temp_files[:]:  # Copy list to avoid modification during iteration
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    self.logger.debug(f"Cleaned up temporary file: {temp_file}")
                self.temp_files.remove(temp_file)
            except Exception as e:
                self.logger.warning(f"Error cleaning up temporary file {temp_file}: {e}")
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs[:]:  # Copy list to avoid modification during iteration
            try:
                self._cleanup_directory(temp_dir)
                self.temp_dirs.remove(temp_dir)
            except Exception as e:
                self.logger.warning(f"Error cleaning up temporary directory {temp_dir}: {e}")
        
        if self.temp_files or self.temp_dirs:
            self.logger.info("Completed cleanup of temporary files and directories")
    
    def _cleanup_directory(self, directory: str) -> None:
        """Clean up a specific directory"""
        directory_path = Path(directory)
        
        if not directory_path.exists():
            return
        
        try:
            # On Windows, we might need to handle read-only files
            def handle_remove_readonly(func, path, exc):
                """Handle removal of read-only files on Windows"""
                if os.path.exists(path):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
            
            shutil.rmtree(directory, onerror=handle_remove_readonly)
            self.logger.debug(f"Cleaned up temporary directory: {directory}")
            
        except Exception as e:
            self.logger.error(f"Error removing directory {directory}: {e}")
            raise
    
    def get_temp_stats(self) -> Dict[str, Any]:
        """Get statistics about temporary files and directories"""
        return {
            'temp_files': len(self.temp_files),
            'temp_dirs': len(self.temp_dirs),
            'active_temp_files': [f for f in self.temp_files if os.path.exists(f)],
            'active_temp_dirs': [d for d in self.temp_dirs if os.path.exists(d)]
        }
    
    def __del__(self):
        """Ensure cleanup on destruction"""
        try:
            self.cleanup()
        except:
            # Don't raise exceptions in __del__
            pass


class ModFileManager:
    """
    High-level file management facade that coordinates all file operations
    """
    
    def __init__(self, archives_directory: str, game_directory: str):
        """Initialize the mod file manager"""
        self.archive_manager = ArchiveManager(archives_directory)
        self.game_directory_manager = GameDirectoryManager(game_directory)
        self.conflict_resolver = FileConflictResolver()
        self.validator = ModFileValidator()
        self.temp_manager = TempFileManager()
        self.logger = logging.getLogger(__name__)
    
    def install_mod_from_archive(self, archive_path: str, mod_name: str, 
                                selected_files: List[str], mod_id: int,
                                existing_deployments: Optional[Dict[int, List[str]]] = None,
                                conflict_resolution: str = "ask_user") -> Dict[str, Any]:
        """
        Complete mod installation process from archive
        
        Returns:
            Dict containing installation results and any conflicts
        """
        installation_result = {
            'success': False,
            'archive_filename': None,
            'deployed_files': [],
            'conflicts': [],
            'warnings': [],
            'errors': []
        }
        
        try:
            # 1. Validate the archive
            if not self.validator.is_valid_archive(archive_path):
                raise ValueError(f"Invalid archive: {archive_path}")
            
            # 2. Security scan
            security_warnings = self.validator.scan_for_malicious_content(archive_path)
            if security_warnings:
                installation_result['warnings'].extend(security_warnings)
                self.logger.warning(f"Security scan found {len(security_warnings)} issues")
            
            # 3. Validate file paths
            path_issues = self.validator.validate_file_paths(selected_files)
            if path_issues:
                installation_result['warnings'].extend(path_issues)
                self.logger.warning(f"Path validation found {len(path_issues)} issues")
            
            # 4. Copy archive to managed location
            archive_filename = self.archive_manager.copy_archive(archive_path, mod_name)
            installation_result['archive_filename'] = archive_filename
            
            archive_in_storage = self.archive_manager.archives_directory / archive_filename
            
            # 5. Detect conflicts if existing deployments provided
            if existing_deployments:
                conflicts = self.conflict_resolver.detect_conflicts(selected_files, existing_deployments)
                installation_result['conflicts'] = conflicts
                
                if conflicts and conflict_resolution == "ask_user":
                    # Return early with conflicts for user resolution
                    installation_result['requires_user_input'] = True
                    return installation_result
                elif conflicts:
                    # Resolve conflicts automatically
                    resolution_result = self.conflict_resolver.resolve_conflicts(conflicts, conflict_resolution)
                    installation_result['conflict_resolution'] = resolution_result
            
            # 6. Deploy files to game directory
            deployed_files = self.game_directory_manager.deploy_files(
                mod_id, str(archive_in_storage), selected_files
            )
            installation_result['deployed_files'] = deployed_files
            
            installation_result['success'] = True
            self.logger.info(f"Successfully installed mod {mod_name} (ID: {mod_id})")
            
        except Exception as e:
            installation_result['errors'].append(str(e))
            self.logger.error(f"Error installing mod {mod_name}: {e}")
            
            # Cleanup on failure
            if installation_result.get('archive_filename'):
                try:
                    self.archive_manager.remove_archive(installation_result['archive_filename'])
                except:
                    pass
        
        return installation_result
    
    def uninstall_mod(self, mod_id: int, archive_filename: str, 
                     deployed_files: List[str]) -> Dict[str, Any]:
        """
        Complete mod uninstallation process
        """
        uninstall_result = {
            'success': False,
            'files_removed': 0,
            'errors': []
        }
        
        try:
            # Remove deployed files from game directory
            self.game_directory_manager.remove_deployed_files(deployed_files)
            
            # Remove archive file
            if archive_filename:
                self.archive_manager.remove_archive(archive_filename)
            
            uninstall_result['success'] = True
            uninstall_result['files_removed'] = len(deployed_files)
            self.logger.info(f"Successfully uninstalled mod {mod_id}")
            
        except Exception as e:
            uninstall_result['errors'].append(str(e))
            self.logger.error(f"Error uninstalling mod {mod_id}: {e}")
        
        return uninstall_result
    
    def get_archive_contents(self, archive_path: str) -> List[Dict[str, Any]]:
        """Get the contents of an archive file"""
        return self.archive_manager.extract_archive_contents(archive_path)
    
    def validate_game_directory(self) -> bool:
        """Validate that the game directory is correct"""
        return self.game_directory_manager.validate_game_directory()
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files"""
        self.temp_manager.cleanup()
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for debugging"""
        return {
            'archives_directory': str(self.archive_manager.archives_directory),
            'game_directory': str(self.game_directory_manager.game_directory),
            'game_directory_valid': self.validate_game_directory(),
            'temp_file_stats': self.temp_manager.get_temp_stats(),
            'python_version': sys.version,
            'platform': os.name
        }


# Utility functions
def get_file_size_formatted(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def is_mod_file(file_path: str) -> bool:
    """Check if a file appears to be a mod file based on its path and extension"""
    file_path_lower = file_path.lower()
    
    # Common mod file extensions (specific to game files)
    mod_extensions = {'.pak', '.uasset', '.umap', '.dll'}
    
    # Config/text files are only mod files if in mod directories
    config_extensions = {'.ini', '.cfg', '.txt'}
    
    # Common mod directories
    mod_directories = ['mods', 'content', 'data', 'plugins']
    
    # Check extension
    file_ext = Path(file_path).suffix.lower()
    
    # Direct mod file extensions
    if file_ext in mod_extensions:
        return True
    
    # Config files only if in mod directories
    if file_ext in config_extensions:
        for mod_dir in mod_directories:
            if mod_dir in file_path_lower:
                return True
    
    # Check if in mod directories (regardless of extension)
    for mod_dir in mod_directories:
        if mod_dir in file_path_lower:
            return True
    
    return False


def normalize_mod_filename(filename: str) -> str:
    """Normalize a mod filename for consistent storage"""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    
    return filename


class FileManager:
    """
    Simplified file manager wrapper for UI integration
    """
    
    def __init__(self, game_path: str, mods_path: str, backup_path: str):
        """Initialize the file manager"""
        self.game_path = Path(game_path) if game_path else None
        self.mods_path = Path(mods_path)
        self.backup_path = Path(backup_path)
        
        # Create directories if they don't exist (only for paths we control)
        self.mods_path.mkdir(parents=True, exist_ok=True)
        self.backup_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize sub-managers only if game_path is valid
        if self.game_path and self.game_path.exists():
            self.mod_file_manager = ModFileManager(str(self.mods_path), str(self.game_path))
        else:
            self.mod_file_manager = None
        
        self.temp_manager = TempFileManager()
        self.logger = logging.getLogger(__name__)
    
    def validate_archive(self, archive_path: str) -> bool:
        """Validate that an archive is valid and readable"""
        try:
            # Use the validator directly
            validator = ModFileValidator()
            return validator.is_valid_archive(archive_path)
        except Exception as e:
            self.logger.error(f"Error validating archive {archive_path}: {e}")
            return False
    
    def scan_archive_security(self, archive_path: str) -> Dict[str, Any]:
        """Scan archive for security issues"""
        try:
            # Use the validator directly
            validator = ModFileValidator()
            warnings = validator.scan_for_malicious_content(archive_path)
            return {
                'safe': len(warnings) == 0,
                'warnings': warnings
            }
        except Exception as e:
            self.logger.error(f"Error scanning archive {archive_path}: {e}")
            return {
                'safe': False,
                'warnings': [f"Error during security scan: {e}"]
            }
    
    def get_archive_contents(self, archive_path: str) -> List[Dict[str, Any]]:
        """Get the contents of an archive file"""
        try:
            # Use the archive manager directly
            archive_manager = ArchiveManager(str(self.mods_path))
            return archive_manager.extract_archive_contents(archive_path)
        except Exception as e:
            self.logger.error(f"Error getting archive contents {archive_path}: {e}")
            return []
    
    def deploy_mod_files(self, archive_path: str, selected_files: List[str], 
                        target_directory: str = None) -> Dict[str, Any]:
        """Deploy selected files from an archive to the target directory"""
        if not target_directory and self.game_path:
            target_directory = str(self.game_path)
        elif not target_directory:
            raise ValueError("No target directory specified and no game path configured")
        
        try:
            # Extract selected files to temp directory
            temp_dir = self.temp_manager.extract_to_temp_dir(archive_path, selected_files)
            
            deployed_files = {}
            warnings = []
            
            # Copy files from temp directory to target
            for file_path in selected_files:
                source_path = Path(temp_dir) / file_path
                target_path = Path(target_directory) / file_path
                
                if not source_path.exists():
                    warnings.append(f"File not found in archive: {file_path}")
                    continue
                
                # Create target directory if needed
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Backup original file if it exists
                if target_path.exists():
                    backup_file = self.backup_path / f"{target_path.name}.backup"
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(target_path), str(backup_file))
                
                # Copy the file
                shutil.copy2(str(source_path), str(target_path))
                deployed_files[file_path] = str(target_path)
            
            return {
                'deployed_files': deployed_files,
                'warnings': warnings
            }
            
        except Exception as e:
            self.logger.error(f"Error deploying mod files: {e}")
            raise
        finally:
            # Cleanup temp files
            self.temp_manager.cleanup()
    
    def remove_deployed_file(self, file_path: str) -> bool:
        """Remove a deployed file and restore backup if available"""
        try:
            target_path = Path(file_path)
            
            if not target_path.exists():
                return True  # File already removed
            
            # Check for backup
            backup_file = self.backup_path / f"{target_path.name}.backup"
            
            if backup_file.exists():
                # Restore from backup
                shutil.copy2(str(backup_file), str(target_path))
                os.remove(str(backup_file))
            else:
                # Just remove the file
                os.remove(str(target_path))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing deployed file {file_path}: {e}")
            return False
    
    def validate_game_directory(self) -> bool:
        """Validate that the game directory is correct"""
        if not self.game_path or not self.game_path.exists():
            return False
        
        if not self.mod_file_manager:
            return False
            
        return self.mod_file_manager.validate_game_directory()
    
    def cleanup_temp_files(self) -> None:
        """Clean up all temporary files"""
        self.temp_manager.cleanup()