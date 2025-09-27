# Nexus Mods API Implementation

## Overview

This document describes the complete Nexus Mods API implementation for the Stalker 2 Mod Manager, fully compliant with the official Nexus Mods API Swagger specification.

## Swagger Compliance ✅

**Validation Status**: FULLY COMPLIANT  
**Specification Source**: `docs/nexus-swagger.json`  
**Validation Tool**: `validate_api_compliance.py`

Our implementation has been validated against the official Nexus Mods API Swagger specification and is 100% compliant with all requirements including:
- ✅ Correct endpoint URLs and parameters
- ✅ Proper authentication headers (`apikey`)  
- ✅ Rate limiting compliance (429 handling)
- ✅ System-aware User-Agent strings
- ✅ Response format handling
- ✅ Error code management

## Implementation Details

### NexusModsClient Class

**Core Functionality:**
- API key authentication and validation
- Rate limiting with automatic retry logic
- Comprehensive error handling with custom exceptions
- Request management with timeout and retry mechanisms

**API Endpoints Implemented:**
- `GET /v1/users/validate.json` - API key validation
- `GET /v1/games/{game_domain}/mods/{id}.json` - Mod information
- `GET /v1/games/{game_domain}/mods/{mod_id}/files.json` - Mod files listing
- `GET /v1/games/{game_domain}/mods/{mod_id}/files/{id}/download_link.json` - Download links

**Features:**
- ✅ Automatic rate limiting (1 second between requests)
- ✅ Exponential backoff retry logic
- ✅ Request timeout handling (30 seconds)
- ✅ HTTP error code handling
- ✅ JSON response parsing
- ✅ User-Agent header compliance
- ✅ Session management for connection reuse

### URL Parsing & Validation

**Supported URL Formats:**
```
https://www.nexusmods.com/stalker2heartofchornobyl/mods/{mod_id}
https://www.nexusmods.com/stalker2heartofchornobyl/mods/{mod_id}/files/{file_id}
https://nexusmods.com/stalker2heartofchornobyl/mods/{mod_id}
www.nexusmods.com/stalker2heartofchornobyl/mods/{mod_id}
```

**Validation Rules:**
- Must be a Nexus Mods domain (nexusmods.com)
- Game domain must be "stalker2heartofchornobyl"
- Mod ID must be a positive integer
- File ID is optional but must be integer if present

### ModDownloader Class

**Functionality:**
- Mod file downloading with progress tracking
- Automatic filename generation with sanitization
- Update checking and version comparison
- Download directory management
- File cleanup utilities

**Features:**
- ✅ Progress callback support for UI integration
- ✅ Safe filename generation (removes invalid characters)
- ✅ Automatic directory creation
- ✅ File existence checking to avoid re-downloads
- ✅ Cleanup of old download files
- ✅ Main file detection for mods

### Error Handling

**Custom Exception Classes:**
- `NexusAPIError` - General API errors with status codes
- `RateLimitError` - Rate limiting specific errors with retry timing

**Error Scenarios Handled:**
- Network connectivity issues
- Invalid API keys (401 Unauthorized)
- Rate limiting (429 Too Many Requests)
- Mod not found (404 Not Found)
- Server errors (5xx status codes)
- Malformed responses
- Timeout errors

### Rate Limiting

**Implementation:**
- Minimum 1 second delay between requests
- Automatic retry on 429 status codes
- Exponential backoff for network errors
- Respect Retry-After headers from server
- Maximum 3 retry attempts per request

**Benefits:**
- Prevents API key suspension
- Maintains good standing with Nexus Mods
- Handles temporary server issues gracefully

## Testing

### Test Coverage

**Unit Tests (15 test cases):**
- Client initialization and configuration
- API key validation (success and failure)
- Mod information retrieval
- File listing functionality
- Rate limiting behavior
- URL parsing (valid and invalid cases)
- URL validation
- Error handling scenarios
- Downloader initialization
- Filename generation with special characters
- Update checking functionality

**Test Results:**
```
Ran 15 tests in 1.012s
OK
✅ All Nexus API tests passed!
```

### Demo Script

**Features Demonstrated:**
- URL parsing with various formats
- Client initialization and configuration
- Progress callback simulation
- Mock data usage for development
- Real API integration (when API key available)

## Usage Examples

### Basic Client Usage

```python
from api.nexus_api import NexusModsClient, NexusAPIError

# Initialize client
client = NexusModsClient("your_api_key")

try:
    # Validate API key
    user = client.validate_api_key()
    print(f"Welcome, {user['name']}!")
    
    # Get mod information
    mod_info = client.get_mod_info(123)
    print(f"Mod: {mod_info['name']} v{mod_info['version']}")
    
    # Get mod files
    files = client.get_mod_files(123)
    print(f"Found {len(files)} files")
    
except NexusAPIError as e:
    print(f"API Error: {e}")
finally:
    client.close()
```

### Download with Progress

```python
from api.nexus_api import ModDownloader

def progress_callback(downloaded, total):
    if total > 0:
        percent = (downloaded / total) * 100
        print(f"Progress: {percent:.1f}% ({downloaded:,}/{total:,} bytes)")

# Initialize downloader
downloader = ModDownloader(client, "./downloads")

# Download mod with progress tracking
file_path = downloader.download_mod(
    mod_id=123, 
    progress_callback=progress_callback
)

print(f"Downloaded to: {file_path}")
```

### URL Parsing

```python
from api.nexus_api import NexusModsClient

# Parse URL
url = "https://www.nexusmods.com/stalker2heartofchornobyl/mods/123"
parsed = NexusModsClient.parse_nexus_url(url)

if parsed:
    print(f"Mod ID: {parsed['mod_id']}")
    print(f"Game: {parsed['game_domain']}")
    
    if 'file_id' in parsed:
        print(f"File ID: {parsed['file_id']}")
```

## Integration Points

### Database Integration

The API client integrates with the database system for:
- Storing API keys in configuration
- Saving mod metadata from API responses
- Tracking downloaded file information
- Managing mod update status

### UI Integration

The API provides hooks for UI integration:
- Progress callbacks for download progress bars
- Error handling for user feedback
- URL validation for user input
- Async-friendly design for non-blocking operations

## Security Considerations

**API Key Protection:**
- API keys are stored securely in the database
- Keys are never logged or exposed in error messages
- Session headers are properly configured
- HTTPS is enforced for all requests

**File Safety:**
- Downloaded files are validated
- Filenames are sanitized to prevent directory traversal
- Temporary files are cleaned up properly
- Download directories are created safely

## Performance Optimizations

**Network Efficiency:**
- Session reuse for connection pooling
- Streaming downloads for large files
- Chunked reading to manage memory usage
- Request timeouts to prevent hanging

**Rate Limiting:**
- Intelligent request spacing
- Automatic retry with backoff
- Respect for server rate limits
- Efficient batch operations

## Future Enhancements

**Potential Improvements:**
- Parallel download support for multiple files
- Resume incomplete downloads
- Checksum verification for downloaded files
- Mod dependency resolution
- Advanced version comparison (semantic versioning)
- Download scheduling and queuing

## Compliance

**Nexus Mods API Guidelines:**
- ✅ Proper User-Agent identification
- ✅ Rate limiting compliance
- ✅ Error handling best practices
- ✅ API key security
- ✅ Respectful request patterns

The implementation follows all Nexus Mods API guidelines and terms of service.