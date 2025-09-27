# File Manager Implementation Guide

## Overview

The Stalker 2 Mod Manager file management system provides comprehensive functionality for handling mod archives, deploying files to the game directory, managing conflicts, and ensuring security. The system is built with multiple specialized classes that work together to provide a robust and safe mod installation experience.

## Architecture

### Core Components

```
ModFileManager (Facade)
├── ArchiveManager          # Archive handling and validation
├── GameDirectoryManager    # Game file deployment and management
├── FileConflictResolver    # Conflict detection and resolution
├── ModFileValidator        # Security and validation checks
└── TempFileManager         # Temporary file operations
```

## Class Documentation

### ArchiveManager

Manages mod archive files with comprehensive validation and storage.

**Key Features:**
- Archive validation (ZIP, 7z, RAR support)
- Content extraction and listing
- Secure file copying with verification
- Unique filename generation
- Archive metadata retrieval

**Usage Example:**
```python
from utils.file_manager import ArchiveManager

archive_manager = ArchiveManager("C:/ModArchives")

# Validate an archive
if archive_manager.is_valid_archive("mod.zip"):
    # Extract contents for preview
    contents = archive_manager.extract_archive_contents("mod.zip")
    for file_info in contents:
        print(f"File: {file_info['path']} ({file_info['size']} bytes)")
    
    # Copy to managed storage
    filename = archive_manager.copy_archive("mod.zip", "My Awesome Mod")
    print(f"Archive stored as: {filename}")
```

### GameDirectoryManager

Handles deployment of mod files to the game directory with backup and restore capabilities.

**Key Features:**
- Game directory validation
- Safe file deployment with backups
- Deployed file tracking
- Automatic backup creation
- File restoration capabilities
- Windows read-only file handling

**Usage Example:**
```python
from utils.file_manager import GameDirectoryManager

game_manager = GameDirectoryManager("C:/Games/Stalker2")

# Validate game directory
if game_manager.validate_game_directory():
    # Deploy mod files
    deployed_files = game_manager.deploy_files(
        mod_id=1,
        archive_path="mod.zip",
        selected_files=["Mods/MyMod/data.pak", "Config/settings.ini"]
    )
    
    # Later, remove deployed files
    game_manager.remove_deployed_files(deployed_files)
```

### FileConflictResolver

Detects and resolves conflicts between mod files.

**Key Features:**
- Intelligent conflict detection
- Multiple resolution strategies
- Conflict severity assessment
- Automatic resolution options

**Resolution Strategies:**
- `overwrite` - Replace existing files
- `skip` - Skip conflicting files
- `rename` - Rename new files to avoid conflicts
- `backup_and_overwrite` - Backup existing, then overwrite

**Usage Example:**
```python
from utils.file_manager import FileConflictResolver

resolver = FileConflictResolver()

# Detect conflicts
conflicts = resolver.detect_conflicts(
    new_files=["Config/game.ini", "Data/textures.pak"],
    existing_deployments={
        1: ["Config/game.ini"],  # Mod 1 already deployed this file
        2: ["Data/other.pak"]
    }
)

# Resolve conflicts
resolution = resolver.resolve_conflicts(conflicts, "backup_and_overwrite")
print(f"Resolved {len(resolution['resolved'])} conflicts")
```

### ModFileValidator

Provides security validation and file safety checks.

**Key Features:**
- Archive integrity validation
- Malicious content detection
- Path traversal prevention
- File path validation
- Windows compatibility checks

**Security Checks:**
- Executable file detection
- Script file scanning
- Directory traversal attempts
- System directory targeting
- Hidden file detection
- Oversized file warnings

**Usage Example:**
```python
from utils.file_manager import ModFileValidator

validator = ModFileValidator()

# Validate archive
if validator.is_valid_archive("mod.zip"):
    # Security scan
    warnings = validator.scan_for_malicious_content("mod.zip")
    if warnings:
        print("Security warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    # Validate file paths
    file_paths = ["Mods/MyMod/data.pak", "Config/../../../system32/evil.exe"]
    issues = validator.validate_file_paths(file_paths)
    if issues:
        print("Path validation issues:")
        for issue in issues:
            print(f"  - {issue}")
```

### TempFileManager

Manages temporary files and directories with automatic cleanup.

**Key Features:**
- Temporary directory creation
- Temporary file management
- Archive extraction to temp locations
- Automatic cleanup on destruction
- Windows read-only file handling

**Usage Example:**
```python
from utils.file_manager import TempFileManager

temp_manager = TempFileManager()

# Create temporary directory
temp_dir = temp_manager.create_temp_dir()

# Extract archive to temp location
extracted_dir = temp_manager.extract_to_temp_dir(
    "mod.zip", 
    selected_files=["Mods/MyMod/data.pak"]
)

# Automatic cleanup when done
temp_manager.cleanup()
```

### ModFileManager (Facade)

High-level interface that coordinates all file operations.

**Key Features:**
- Complete mod installation workflow
- Conflict detection and resolution
- Security validation integration
- Automatic cleanup on failure
- Comprehensive error reporting

**Usage Example:**
```python
from utils.file_manager import ModFileManager

# Initialize with storage locations
mod_manager = ModFileManager(
    archives_directory="C:/ModManager/Archives",
    game_directory="C:/Games/Stalker2"
)

# Install a mod with full workflow
result = mod_manager.install_mod_from_archive(
    archive_path="downloaded_mod.zip",
    mod_name="Awesome Graphics Mod",
    selected_files=["Mods/Graphics/textures.pak", "Config/graphics.ini"],
    mod_id=1,
    existing_deployments={},  # No conflicts for first mod
    conflict_resolution="ask_user"
)

if result['success']:
    print(f"Mod installed successfully!")
    print(f"Archive: {result['archive_filename']}")
    print(f"Files deployed: {len(result['deployed_files'])}")
else:
    print(f"Installation failed: {result['errors']}")

# Later, uninstall the mod
uninstall_result = mod_manager.uninstall_mod(
    mod_id=1,
    archive_filename=result['archive_filename'],
    deployed_files=result['deployed_files']
)
```

## Utility Functions

### File Size Formatting
```python
from utils.file_manager import get_file_size_formatted

print(get_file_size_formatted(1024))        # "1.0 KB"
print(get_file_size_formatted(1024*1024))   # "1.0 MB"
```

### Mod File Detection
```python
from utils.file_manager import is_mod_file

print(is_mod_file("Mods/MyMod/data.pak"))     # True
print(is_mod_file("Content/textures.uasset")) # True
print(is_mod_file("random_file.txt"))         # False
```

### Filename Normalization
```python
from utils.file_manager import normalize_mod_filename

normalized = normalize_mod_filename("My Mod: Special Edition!")
print(normalized)  # "My_Mod_Special_Edition"
```

## Security Features

### Malicious Content Detection

The system automatically scans for potentially dangerous content:

- **Executable Files**: `.exe`, `.bat`, `.cmd`, `.scr`, etc.
- **Script Files**: `.ps1`, `.vbs`, `.js`, `.jar`
- **Directory Traversal**: Paths containing `../` or absolute paths
- **System Targeting**: Files targeting Windows system directories
- **Hidden Files**: Files starting with `.` (Unix-style hidden files)
- **Oversized Files**: Files larger than 100MB (potential space bombs)

### Path Validation

All file paths are validated for:

- **Length Limits**: Windows MAX_PATH (260 characters)
- **Invalid Characters**: `<>"|?*` and other problematic characters
- **Reserved Names**: Windows reserved names like `CON`, `PRN`, `AUX`, etc.
- **Directory Traversal**: Prevention of `../` attacks
- **Absolute Paths**: Rejection of absolute paths in archives

### Safe Deployment

File deployment includes multiple safety measures:

- **Backup Creation**: Original files backed up before replacement
- **Verification**: File copies verified with checksums
- **Rollback**: Failed deployments automatically rolled back
- **Safe Removal**: Only mod files removed, never game files
- **Permission Handling**: Windows read-only files handled properly

## Error Handling

The file manager provides comprehensive error handling:

```python
try:
    result = mod_manager.install_mod_from_archive(...)
    if not result['success']:
        for error in result['errors']:
            print(f"Error: {error}")
        for warning in result['warnings']:
            print(f"Warning: {warning}")
except Exception as e:
    print(f"Critical error: {e}")
```

### Common Error Scenarios

- **Archive Not Found**: Source archive file missing
- **Invalid Archive**: Corrupted or unsupported archive format
- **Security Issues**: Malicious content detected
- **Path Issues**: Invalid or dangerous file paths
- **Permission Errors**: Insufficient permissions for deployment
- **Disk Space**: Insufficient space for deployment
- **Game Directory**: Invalid or corrupted game installation

## Performance Considerations

### Memory Efficiency

- **Streaming**: Large files processed in chunks
- **Lazy Loading**: Archive contents loaded on demand
- **Cleanup**: Automatic temporary file cleanup
- **Resource Management**: Proper file handle management

### I/O Optimization

- **Batch Operations**: Multiple files processed efficiently
- **Copy Verification**: Smart verification based on file size
- **Path Caching**: Repeated path operations optimized
- **Compression**: ZIP archives processed without full extraction

## Integration with Application

### Database Integration

The file manager integrates with the database layer:

```python
# Example integration with database
from database.models import ArchiveManager as DBArchiveManager

# After successful installation
db_archive_manager = DBArchiveManager()
db_archive_manager.add_archive(
    mod_id=mod_id,
    filename=result['archive_filename'],
    file_size=archive_size,
    md5_hash=calculate_hash(archive_path)
)
```

### UI Integration

The file manager provides progress callbacks and status information for UI integration:

```python
def progress_callback(current, total, operation):
    progress = (current / total) * 100
    print(f"{operation}: {progress:.1f}%")

# File operations can report progress
mod_manager.install_mod_from_archive(
    ...,
    progress_callback=progress_callback
)
```

## Testing

The file manager includes comprehensive tests covering:

- **Archive Operations**: Creation, validation, extraction
- **Deployment**: File deployment and removal
- **Conflict Resolution**: All resolution strategies
- **Security Validation**: Malicious content detection
- **Error Scenarios**: All error conditions
- **Integration**: High-level workflow testing

Run tests with:
```bash
python tests/test_file_manager.py
```

## Best Practices

### For Developers

1. **Always Validate**: Use validation before any operations
2. **Handle Errors**: Comprehensive error handling required
3. **Cleanup Resources**: Use try/finally or context managers
4. **Security First**: Never skip security validation
5. **User Feedback**: Provide progress and status information

### For Users

1. **Backup First**: The system creates backups automatically
2. **Verify Sources**: Only install mods from trusted sources
3. **Monitor Space**: Ensure sufficient disk space
4. **Review Conflicts**: Understand conflict resolutions
5. **Regular Cleanup**: Remove unused mod archives periodically

## Future Enhancements

Planned improvements include:

- **7-Zip Support**: Full 7z and RAR archive support
- **Differential Updates**: Smart updating of existing mods
- **Compression**: Archive compression for storage efficiency
- **Integrity Monitoring**: Ongoing file integrity verification
- **Advanced Conflicts**: More sophisticated conflict resolution
- **Performance Metrics**: Detailed operation performance tracking

---

The file manager system provides a robust, secure, and user-friendly foundation for mod management in the Stalker 2 Mod Manager application.