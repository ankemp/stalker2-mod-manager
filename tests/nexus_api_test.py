"""
Test suite for Nexus Mods API functionality
"""

import os
import sys
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.nexus_api import NexusModsClient, ModDownloader, NexusAPIError, RateLimitError


class TestNexusModsClient(unittest.TestCase):
    """Test cases for NexusModsClient"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.api_key = "test_api_key_123"
        self.client = NexusModsClient(self.api_key)
    
    def tearDown(self):
        """Clean up after tests"""
        self.client.close()
    
    def test_initialization(self):
        """Test client initialization"""
        self.assertEqual(self.client.api_key, self.api_key)
        self.assertEqual(self.client.session.headers["apikey"], self.api_key)
        self.assertIn("Stalker2ModManager/1.0", self.client.session.headers["User-Agent"])
        # Should include system info in User-Agent
        user_agent = self.client.session.headers["User-Agent"]
        self.assertIn("Python/", user_agent)
    
    def test_rate_limit_status(self):
        """Test rate limit status tracking"""
        status = self.client.get_rate_limit_status()
        expected_keys = ["daily_remaining", "hourly_remaining", "daily_reset", "hourly_reset"]
        
        for key in expected_keys:
            self.assertIn(key, status)
    
    @patch('requests.Session.request')
    def test_get_mod_files_with_category(self, mock_request):
        """Test mod files retrieval with category filter"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = {
            "files": [
                {
                    "file_id": 1001,
                    "name": "Main File",
                    "category_name": "MAIN"
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.client.get_mod_files(123, category="main")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["category_name"], "MAIN")
        # Check that category parameter was passed
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"]["category"], "main")
    
    @patch('requests.Session.request')
    def test_get_latest_added_mods(self, mock_request):
        """Test latest added mods retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = [
            {"mod_id": 1, "name": "New Mod 1"},
            {"mod_id": 2, "name": "New Mod 2"}
        ]
        mock_request.return_value = mock_response
        
        result = self.client.get_latest_added_mods()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["mod_id"], 1)
    
    @patch('requests.Session.request')
    def test_get_updated_mods(self, mock_request):
        """Test updated mods retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = [
            {"mod_id": 1, "name": "Updated Mod", "updated_timestamp": 1234567890}
        ]
        mock_request.return_value = mock_response
        
        result = self.client.get_updated_mods("1w")
        
        self.assertEqual(len(result), 1)
        # Check that period parameter was passed
        args, kwargs = mock_request.call_args
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"]["period"], "1w")
    
    def test_get_updated_mods_invalid_period(self):
        """Test updated mods with invalid period"""
        with self.assertRaises(ValueError):
            self.client.get_updated_mods("invalid_period")
    
    @patch('requests.Session.request')
    def test_track_mod(self, mock_request):
        """Test mod tracking"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 201
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = self.client.track_mod(123)
        
        self.assertTrue(result)
        # Check that correct method and parameters were used
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs.get('method') or args[0], "POST")  # method
        self.assertIn("params", kwargs)
        self.assertEqual(kwargs["params"]["domain_name"], "stalker2heartofchornobyl")
    
    @patch('requests.Session.request')
    def test_rate_limit_header_parsing(self, mock_request):
        """Test parsing of rate limit headers"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.headers = {
            'X-RL-Daily-Remaining': '2400',
            'X-RL-Hourly-Remaining': '95',
            'X-RL-Daily-Reset': '2023-01-01T00:00:00+00:00',
            'X-RL-Hourly-Reset': '2023-01-01T12:00:00+00:00'
        }
        mock_response.json.return_value = {"test": "response"}
        mock_request.return_value = mock_response
        
        # Make any request to trigger header parsing
        self.client.validate_api_key()
        
        # Check that rate limit info was parsed
        self.assertEqual(self.client.daily_remaining, 2400)
        self.assertEqual(self.client.hourly_remaining, 95)
        self.assertIsNotNone(self.client.daily_reset)
        self.assertIsNotNone(self.client.hourly_reset)
    
    @patch('requests.Session.request')
    def test_validate_api_key_success(self, mock_request):
        """Test successful API key validation"""
        # Mock successful response
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.headers = {}  # Add empty headers dict
        mock_response.json.return_value = {
            "user_id": 12345,
            "name": "TestUser",
            "email": "test@example.com"
        }
        mock_request.return_value = mock_response
        
        result = self.client.validate_api_key()
        
        self.assertEqual(result["user_id"], 12345)
        self.assertEqual(result["name"], "TestUser")
        mock_request.assert_called_once()
    
    @patch('requests.Session.request')
    def test_validate_api_key_invalid(self, mock_request):
        """Test invalid API key"""
        # Mock error response
        mock_response = Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.headers = {}  # Add empty headers dict
        mock_response.json.return_value = {"message": "Invalid API key"}
        mock_response.text = '{"message": "Invalid API key"}'
        mock_request.return_value = mock_response
        
        with self.assertRaises(NexusAPIError) as context:
            self.client.validate_api_key()
        
        self.assertIn("Invalid API key", str(context.exception))
    
    @patch('requests.Session.request')
    def test_get_mod_info_success(self, mock_request):
        """Test successful mod info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}  # Add empty headers dict
        mock_response.json.return_value = {
            "mod_id": 123,
            "name": "Test Mod",
            "version": "1.0.0",
            "author": "TestAuthor",
            "summary": "A test mod"
        }
        mock_request.return_value = mock_response
        
        result = self.client.get_mod_info(123)
        
        self.assertEqual(result["mod_id"], 123)
        self.assertEqual(result["name"], "Test Mod")
        self.assertEqual(result["version"], "1.0.0")
    
    @patch('requests.Session.request')
    def test_get_file_info_success(self, mock_request):
        """Test successful file info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = {
            "file_id": 1001,
            "name": "Main File",
            "file_name": "mod_v1.0.zip",
            "category_name": "MAIN",
            "version": "1.0.0",
            "size_kb": 1024,
            "uploaded_time": 1234567890
        }
        mock_request.return_value = mock_response
        
        result = self.client.get_file_info(123, 1001)
        
        self.assertEqual(result["file_id"], 1001)
        self.assertEqual(result["name"], "Main File")
        self.assertEqual(result["file_name"], "mod_v1.0.zip")
        self.assertEqual(result["size_kb"], 1024)
    
    @patch('requests.Session.request')
    def test_get_latest_updated_mods(self, mock_request):
        """Test latest updated mods retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = [
            {"mod_id": 1, "name": "Updated Mod 1"},
            {"mod_id": 2, "name": "Updated Mod 2"}
        ]
        mock_request.return_value = mock_response
        
        result = self.client.get_latest_updated_mods()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["mod_id"], 1)
    
    @patch('requests.Session.request')
    def test_search_mods_by_md5(self, mock_request):
        """Test MD5 search functionality"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = [
            {"mod_id": 123, "file_id": 1001, "file_name": "test.zip"}
        ]
        mock_request.return_value = mock_response
        
        test_md5 = "d41d8cd98f00b204e9800998ecf8427e"
        result = self.client.search_mods_by_md5(test_md5)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["mod_id"], 123)
    
    @patch('requests.Session.request')
    def test_endorse_mod(self, mock_request):
        """Test mod endorsement"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        result = self.client.endorse_mod(123, "1.0.0")
        
        self.assertTrue(result)
        # Check that correct method and data were used
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs.get('method') or args[0], "POST")
        self.assertIn("data", kwargs)
        self.assertEqual(kwargs["data"]["version"], "1.0.0")
    
    @patch('requests.Session.request')
    def test_get_all_games(self, mock_request):
        """Test all games retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = [
            {"id": 1, "name": "Skyrim", "domain_name": "skyrim"},
            {"id": 2, "name": "Stalker 2", "domain_name": "stalker2heartofchornobyl"}
        ]
        mock_request.return_value = mock_response
        
        result = self.client.get_all_games()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1]["domain_name"], "stalker2heartofchornobyl")
    
    @patch('requests.Session.request')
    def test_get_game_info(self, mock_request):
        """Test game info retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}
        mock_response.json.return_value = {
            "id": 1,
            "name": "S.T.A.L.K.E.R. 2: Heart of Chornobyl",
            "domain_name": "stalker2heartofchornobyl",
            "downloads": 50000,
            "file_count": 1000
        }
        mock_request.return_value = mock_response
        
        result = self.client.get_game_info()
        
        self.assertEqual(result["domain_name"], "stalker2heartofchornobyl")
        self.assertEqual(result["downloads"], 50000)
    
    @patch('requests.Session.request')
    def test_get_mod_files_success(self, mock_request):
        """Test successful mod files retrieval"""
        mock_response = Mock()
        mock_response.ok = True
        mock_response.headers = {}  # Add empty headers dict
        mock_response.json.return_value = {
            "files": [
                {
                    "file_id": 1001,
                    "name": "Main File",
                    "file_name": "mod_v1.0.zip",
                    "category_name": "MAIN",
                    "version": "1.0.0"
                },
                {
                    "file_id": 1002,
                    "name": "Optional File", 
                    "file_name": "optional_v1.0.zip",
                    "category_name": "OPTIONAL",
                    "version": "1.0.0"
                }
            ]
        }
        mock_request.return_value = mock_response
        
        result = self.client.get_mod_files(123)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["file_id"], 1001)
        self.assertEqual(result[0]["category_name"], "MAIN")
    
    @patch('requests.Session.request')
    def test_rate_limiting(self, mock_request):
        """Test rate limiting handling"""
        # First request: rate limited
        mock_response_429 = Mock()
        mock_response_429.ok = False
        mock_response_429.status_code = 429
        mock_response_429.headers = {"Retry-After": "1"}
        
        # Second request: success
        mock_response_200 = Mock()
        mock_response_200.ok = True
        mock_response_200.headers = {}  # Add empty headers dict
        mock_response_200.json.return_value = {"success": True}
        
        mock_request.side_effect = [mock_response_429, mock_response_200]
        
        # This should succeed after retry
        result = self.client.validate_api_key()
        self.assertEqual(result["success"], True)
        self.assertEqual(mock_request.call_count, 2)
    
    def test_parse_nexus_url_valid(self):
        """Test parsing valid Nexus URLs"""
        test_cases = [
            {
                "url": "https://www.nexusmods.com/stalker2heartofchornobyl/mods/123",
                "expected": {
                    "game_domain": "stalker2heartofchornobyl",
                    "mod_id": 123
                }
            },
            {
                "url": "https://nexusmods.com/stalker2heartofchornobyl/mods/456",
                "expected": {
                    "game_domain": "stalker2heartofchornobyl", 
                    "mod_id": 456
                }
            },
            {
                "url": "www.nexusmods.com/stalker2heartofchornobyl/mods/789",
                "expected": {
                    "game_domain": "stalker2heartofchornobyl",
                    "mod_id": 789
                }
            },
            {
                "url": "https://www.nexusmods.com/stalker2heartofchornobyl/mods/100/files/200",
                "expected": {
                    "game_domain": "stalker2heartofchornobyl",
                    "mod_id": 100,
                    "file_id": 200
                }
            }
        ]
        
        for case in test_cases:
            result = NexusModsClient.parse_nexus_url(case["url"])
            self.assertIsNotNone(result, f"Failed to parse: {case['url']}")
            
            for key, expected_value in case["expected"].items():
                self.assertEqual(result[key], expected_value, 
                               f"Mismatch for {key} in {case['url']}")
    
    def test_parse_nexus_url_invalid(self):
        """Test parsing invalid URLs"""
        invalid_urls = [
            "https://www.google.com",
            "https://www.nexusmods.com/skyrim/mods/123",  # Wrong game
            "https://www.nexusmods.com/stalker2heartofchornobyl/downloads/123",  # Not mods
            "not_a_url",
            "https://www.nexusmods.com/stalker2heartofchornobyl/mods/not_a_number",
            "https://www.nexusmods.com/stalker2heartofchornobyl/mods/",  # Missing mod ID
        ]
        
        for url in invalid_urls:
            result = NexusModsClient.parse_nexus_url(url)
            self.assertIsNone(result, f"Should not parse invalid URL: {url}")
    
    def test_is_valid_nexus_url(self):
        """Test URL validation"""
        valid_urls = [
            "https://www.nexusmods.com/stalker2heartofchornobyl/mods/123",
            "https://nexusmods.com/stalker2heartofchornobyl/mods/456"
        ]
        
        invalid_urls = [
            "https://www.nexusmods.com/skyrim/mods/123",
            "https://www.google.com",
            "not_a_url"
        ]
        
        for url in valid_urls:
            self.assertTrue(NexusModsClient.is_valid_nexus_url(url), 
                          f"Should be valid: {url}")
        
        for url in invalid_urls:
            self.assertFalse(NexusModsClient.is_valid_nexus_url(url), 
                           f"Should be invalid: {url}")


class TestModDownloader(unittest.TestCase):
    """Test cases for ModDownloader"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_client = Mock(spec=NexusModsClient)
        self.downloader = ModDownloader(self.mock_client, self.temp_dir)
    
    def tearDown(self):
        """Clean up after tests"""
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test downloader initialization"""
        self.assertEqual(str(self.downloader.download_directory), self.temp_dir)
        self.assertEqual(self.downloader.nexus_client, self.mock_client)
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_generate_filename(self):
        """Test filename generation"""
        mod_info = {
            "name": "Test: Mod/With\\Special*Characters",
            "version": "1.0.0"
        }
        
        file_info = {
            "file_id": 1001,
            "file_name": "mod_file.zip",
            "version": "1.0.0"
        }
        
        filename = self.downloader.generate_filename(mod_info, file_info)
        
        # Should sanitize special characters
        self.assertNotIn(":", filename)
        self.assertNotIn("/", filename)
        self.assertNotIn("\\", filename)
        self.assertNotIn("*", filename)
        
        # Should contain key components
        self.assertIn("Test", filename)
        self.assertIn("v1.0.0", filename)
        self.assertIn("1001", filename)
        self.assertTrue(filename.endswith(".zip"))
    
    def test_check_for_updates_available(self):
        """Test update checking when update is available"""
        self.mock_client.get_latest_mod_version.return_value = "2.0.0"
        self.mock_client.get_mod_info.return_value = {"name": "Test Mod"}
        
        result = self.downloader.check_for_updates(123, "1.0.0")
        
        self.assertIsNotNone(result)
        self.assertTrue(result["update_available"])
        self.assertEqual(result["current_version"], "1.0.0")
        self.assertEqual(result["latest_version"], "2.0.0")
    
    def test_check_for_updates_none_available(self):
        """Test update checking when no update is available"""
        self.mock_client.get_latest_mod_version.return_value = "1.0.0"
        
        result = self.downloader.check_for_updates(123, "1.0.0")
        
        self.assertIsNotNone(result)
        self.assertFalse(result["update_available"])
        self.assertEqual(result["current_version"], "1.0.0")
        self.assertEqual(result["latest_version"], "1.0.0")


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def test_nexus_api_error_creation(self):
        """Test NexusAPIError creation"""
        error = NexusAPIError("Test error", status_code=404, response_data={"error": "Not found"})
        
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.status_code, 404)
        self.assertEqual(error.response_data["error"], "Not found")
    
    def test_rate_limit_error_creation(self):
        """Test RateLimitError creation"""
        error = RateLimitError("Rate limited", retry_after=60)
        
        self.assertEqual(str(error), "Rate limited")
        self.assertEqual(error.retry_after, 60)


def run_nexus_api_tests():
    """Run all Nexus API tests"""
    print("Nexus Mods API - Test Suite")
    print("=" * 40)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestNexusModsClient))
    suite.addTests(loader.loadTestsFromTestCase(TestModDownloader))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'=' * 40}")
    if result.wasSuccessful():
        print("✅ All Nexus API tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    run_nexus_api_tests()