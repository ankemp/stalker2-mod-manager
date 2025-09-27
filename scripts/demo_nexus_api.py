"""
Demo script for Nexus Mods API functionality
NOTE: This requires a valid Nexus Mods API key to run
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.nexus_api import NexusModsClient, ModDownloader, NexusAPIError, RateLimitError
import config as app_config


def demo_url_parsing():
    """Demonstrate URL parsing functionality"""
    print("\n📋 URL Parsing Demo")
    print("-" * 30)
    
    test_urls = [
        "https://www.nexusmods.com/stalker2heartofchornobyl/mods/123",
        "https://nexusmods.com/stalker2heartofchornobyl/mods/456/files/789",
        "www.nexusmods.com/stalker2heartofchornobyl/mods/100",
        "https://www.nexusmods.com/skyrim/mods/123",  # Wrong game
        "not_a_valid_url",
        "https://www.google.com"
    ]
    
    for url in test_urls:
        parsed = NexusModsClient.parse_nexus_url(url)
        is_valid = NexusModsClient.is_valid_nexus_url(url)
        
        status = "✅ Valid" if is_valid else "❌ Invalid"
        print(f"{status} {url}")
        
        if parsed:
            print(f"    Mod ID: {parsed.get('mod_id')}")
            if 'file_id' in parsed:
                print(f"    File ID: {parsed.get('file_id')}")


def demo_api_with_mock_data():
    """Demonstrate API functionality with mock data (no real API calls)"""
    print("\n🔧 Mock API Demo (No Real Calls)")
    print("-" * 40)
    
    # This shows how you would use the API client
    try:
        # Initialize client (with dummy key for demo)
        client = NexusModsClient("dummy_api_key_for_demo")
        
        print("✅ Client initialized successfully")
        print(f"   Base URL: {client.BASE_URL}")
        print(f"   Game Domain: {client.GAME_DOMAIN}")
        print(f"   Headers: {list(client.session.headers.keys())}")
        
        # Initialize downloader
        app_config.ensure_directories()
        downloader = ModDownloader(client, app_config.DEFAULT_MODS_DIR)
        
        print(f"✅ Downloader initialized")
        print(f"   Download Directory: {downloader.get_download_directory()}")
        
        # Test filename generation
        mock_mod_info = {
            "name": "Enhanced Graphics Pack: Special Edition",
            "version": "2.1.0"
        }
        
        mock_file_info = {
            "file_id": 1001,
            "file_name": "graphics_mod_v2.1.0.zip",
            "version": "2.1.0"
        }
        
        filename = downloader.generate_filename(mock_mod_info, mock_file_info)
        print(f"✅ Generated filename: {filename}")
        
        # Test rate limit status
        rate_status = client.get_rate_limit_status()
        print(f"✅ Rate limit status initialized: {list(rate_status.keys())}")
        
        client.close()
        
    except Exception as e:
        print(f"❌ Demo error: {e}")


def demo_with_real_api():
    """Demonstrate with real API calls (requires valid API key)"""
    print("\n🌐 Real API Demo")
    print("-" * 20)
    
    # Try to get API key from environment or config
    api_key = os.environ.get('NEXUS_API_KEY')
    
    if not api_key:
        # Try to get from database config
        try:
            from database.models import DatabaseManager, ConfigManager
            db_manager = DatabaseManager()
            config_manager = ConfigManager(db_manager)
            api_key = config_manager.get_api_key()
        except Exception:
            pass
    
    if not api_key:
        print("⚠️  No API key found. To test with real API:")
        print("   1. Set NEXUS_API_KEY environment variable, or")
        print("   2. Configure API key in the application settings")
        print("   3. Get your API key from: https://www.nexusmods.com/users/myaccount?tab=api")
        return
    
    try:
        print(f"🔑 Using API key: {api_key[:8]}...")
        
        # Initialize client
        client = NexusModsClient(api_key)
        
        # Test API key validation
        print("📡 Validating API key...")
        user_info = client.validate_api_key()
        print(f"✅ API key valid for user: {user_info.get('name', 'Unknown')}")
        print(f"   User ID: {user_info.get('user_id')}")
        print(f"   Premium: {user_info.get('is_premium', False)}")
        
        # Show rate limit status
        rate_status = client.get_rate_limit_status()
        if rate_status['daily_remaining'] is not None:
            print(f"   Daily requests remaining: {rate_status['daily_remaining']}")
        if rate_status['hourly_remaining'] is not None:
            print(f"   Hourly requests remaining: {rate_status['hourly_remaining']}")
        
        # Test discovery endpoints
        print(f"\n🔍 Testing discovery endpoints...")
        try:
            latest_mods = client.get_latest_added_mods()
            print(f"✅ Found {len(latest_mods)} latest added mods")
            
            trending_mods = client.get_trending_mods()
            print(f"✅ Found {len(trending_mods)} trending mods")
            
            updated_mods = client.get_updated_mods("1w")
            print(f"✅ Found {len(updated_mods)} mods updated in the last week")
            
        except NexusAPIError as e:
            if e.status_code == 404:
                print(f"⚠️  Discovery endpoints may not be available for Stalker 2 yet")
            else:
                print(f"❌ Discovery error: {e}")
        
        # Test with a popular mod (if it exists)
        test_mod_id = 1  # Usually the first mod uploaded
        
        print(f"\n📦 Testing with mod ID {test_mod_id}...")
        
        try:
            # Get mod info
            mod_info = client.get_mod_info(test_mod_id)
            print(f"✅ Mod found: {mod_info.get('name', 'Unknown')}")
            print(f"   Author: {mod_info.get('author', 'Unknown')}")
            print(f"   Version: {mod_info.get('version', 'Unknown')}")
            print(f"   Downloads: {mod_info.get('unique_downloads', 0):,}")
            
            # Get mod files
            files = client.get_mod_files(test_mod_id)
            print(f"✅ Found {len(files)} files for this mod")
            
            if files:
                main_file = files[0]
                print(f"   Main file: {main_file.get('name', 'Unknown')}")
                print(f"   File size: {main_file.get('size_kb', 0):,} KB")
                
                # Note: We won't actually download to avoid using bandwidth
                print("   (Skipping actual download to save bandwidth)")
                
        except NexusAPIError as e:
            if e.status_code == 404:
                print(f"⚠️  Mod {test_mod_id} not found (this is normal)")
            else:
                print(f"❌ API error: {e}")
        
        client.close()
        
    except RateLimitError as e:
        print(f"⏰ Rate limited. Retry after {e.retry_after} seconds")
    except NexusAPIError as e:
        print(f"❌ API error: {e}")
        if e.status_code == 401:
            print("   Check that your API key is valid and has not expired")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demo_progress_callback():
    """Demonstrate progress callback functionality"""
    print("\n📊 Progress Callback Demo")
    print("-" * 30)
    
    def sample_progress_callback(downloaded: int, total: int):
        """Sample progress callback"""
        if total > 0:
            percent = (downloaded / total) * 100
            bar_length = 30
            filled_length = int(bar_length * downloaded // total)
            bar = '█' * filled_length + '-' * (bar_length - filled_length)
            print(f'\r|{bar}| {percent:.1f}% ({downloaded:,}/{total:,} bytes)', end='')
        else:
            print(f'\rDownloaded: {downloaded:,} bytes', end='')
    
    # Simulate progress
    total_size = 1024 * 1024  # 1MB
    chunk_size = 8192
    
    print("Simulating download progress:")
    for downloaded in range(0, total_size + 1, chunk_size):
        sample_progress_callback(min(downloaded, total_size), total_size)
        import time
        time.sleep(0.01)  # Simulate download time
    
    print("\n✅ Download simulation complete!")


def main():
    """Main demo function"""
    print("Stalker 2 Mod Manager - Nexus API Demo")
    print("=" * 50)
    
    try:
        # Run demos
        demo_url_parsing()
        demo_api_with_mock_data()
        demo_progress_callback()
        demo_with_real_api()
        
        print(f"\n{'=' * 50}")
        print("✅ Demo completed successfully!")
        print("\n💡 Usage Tips:")
        print("   • Always validate API keys before making requests")
        print("   • Handle rate limiting gracefully")
        print("   • Use progress callbacks for large downloads")
        print("   • Parse URLs before extracting mod IDs")
        print("   • Check for updates periodically, not too frequently")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()