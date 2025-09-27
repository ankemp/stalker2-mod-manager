"""
Test suite for database functionality
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

# Setup logging for testing
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import DatabaseManager, ConfigManager, ModManager, ArchiveManager, DeploymentManager


class DatabaseTests:
    """Test class for database functionality"""
    
    def __init__(self):
        self.test_dir = None
        self.db_manager = None
        self.config_manager = None
        self.mod_manager = None
        self.archive_manager = None
        self.deployment_manager = None
    
    def setup(self):
        """Setup test environment"""
        print("Setting up test environment...")
        
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp(prefix="stalker_mod_test_")
        test_db_path = os.path.join(self.test_dir, "test_database.db")
        
        # Initialize managers
        self.db_manager = DatabaseManager(test_db_path)
        self.config_manager = ConfigManager(self.db_manager)
        self.mod_manager = ModManager(self.db_manager)
        self.archive_manager = ArchiveManager(self.db_manager)
        self.deployment_manager = DeploymentManager(self.db_manager)
        
        print(f"Test database created at: {test_db_path}")
    
    def teardown(self):
        """Clean up test environment"""
        if self.test_dir and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
            print("Test environment cleaned up")
    
    def test_database_creation(self):
        """Test database and table creation"""
        print("\n=== Testing Database Creation ===")
        
        # Test database info
        info = self.db_manager.get_database_info()
        print(f"Database info: {info}")
        
        # Verify all tables exist and are empty
        for table_name in ["config", "mods", "mod_archives", "deployment_selections", "deployed_files"]:
            assert info["table_counts"][table_name] == 0, f"Table {table_name} should be empty"
        
        print("✅ Database creation test passed")
    
    def test_config_manager(self):
        """Test configuration management"""
        print("\n=== Testing Config Manager ===")
        
        # Test basic config operations
        self.config_manager.set_config("test_key", "test_value")
        value = self.config_manager.get_config("test_key")
        assert value == "test_value", f"Expected 'test_value', got '{value}'"
        
        # Test default values
        default_value = self.config_manager.get_config("nonexistent", "default")
        assert default_value == "default", f"Expected 'default', got '{default_value}'"
        
        # Test convenience methods
        self.config_manager.set_api_key("test_api_key_123")
        api_key = self.config_manager.get_api_key()
        assert api_key == "test_api_key_123", f"API key mismatch"
        
        self.config_manager.set_game_path("/path/to/stalker2")
        game_path = self.config_manager.get_game_path()
        assert game_path == "/path/to/stalker2", f"Game path mismatch"
        
        # Test boolean settings
        self.config_manager.set_auto_check_updates(True)
        assert self.config_manager.get_auto_check_updates() == True
        
        self.config_manager.set_auto_check_updates(False)
        assert self.config_manager.get_auto_check_updates() == False
        
        # Test integer settings
        self.config_manager.set_update_interval(48)
        assert self.config_manager.get_update_interval() == 48
        
        # Test get all config
        all_config = self.config_manager.get_all_config()
        assert len(all_config) > 0, "Should have configuration values"
        
        print("✅ Config manager test passed")
    
    def test_mod_manager(self):
        """Test mod management"""
        print("\n=== Testing Mod Manager ===")
        
        # Test adding a mod
        mod_data = {
            "nexus_mod_id": 123,
            "mod_name": "Test Graphics Mod",
            "author": "TestAuthor",
            "summary": "A test mod for graphics enhancement",
            "latest_version": "1.0.0",
            "enabled": False
        }
        
        mod_id = self.mod_manager.add_mod(mod_data)
        assert mod_id > 0, "Mod ID should be positive"
        print(f"Added mod with ID: {mod_id}")
        
        # Test retrieving the mod
        retrieved_mod = self.mod_manager.get_mod(mod_id)
        assert retrieved_mod is not None, "Should retrieve the mod"
        assert retrieved_mod["mod_name"] == "Test Graphics Mod"
        assert retrieved_mod["nexus_mod_id"] == 123
        
        # Test getting mod by Nexus ID
        nexus_mod = self.mod_manager.get_mod_by_nexus_id(123)
        assert nexus_mod is not None, "Should find mod by Nexus ID"
        assert nexus_mod["id"] == mod_id
        
        # Test updating mod
        self.mod_manager.update_mod(mod_id, {"enabled": True, "latest_version": "1.1.0"})
        updated_mod = self.mod_manager.get_mod(mod_id)
        assert updated_mod["enabled"] == 1, "Mod should be enabled"  # SQLite stores as integer
        assert updated_mod["latest_version"] == "1.1.0"
        
        # Test enabling/disabling
        self.mod_manager.set_mod_enabled(mod_id, False)
        disabled_mod = self.mod_manager.get_mod(mod_id)
        assert disabled_mod["enabled"] == 0, "Mod should be disabled"
        
        # Add another mod for testing lists
        mod_data2 = {
            "mod_name": "Test Weapon Mod",
            "author": "AnotherAuthor",
            "enabled": True
        }
        mod_id2 = self.mod_manager.add_mod(mod_data2)
        
        # Test getting all mods
        all_mods = self.mod_manager.get_all_mods()
        assert len(all_mods) == 2, "Should have 2 mods"
        
        # Test enabled/disabled filters
        enabled_mods = self.mod_manager.get_enabled_mods()
        assert len(enabled_mods) == 1, "Should have 1 enabled mod"
        
        disabled_mods = self.mod_manager.get_disabled_mods()
        assert len(disabled_mods) == 1, "Should have 1 disabled mod"
        
        # Test search
        search_results = self.mod_manager.search_mods("Graphics")
        assert len(search_results) == 1, "Should find 1 mod with 'Graphics'"
        
        # Test statistics
        stats = self.mod_manager.get_mod_statistics()
        assert stats["total"] == 2
        assert stats["enabled"] == 1
        assert stats["disabled"] == 1
        assert stats["nexus_mods"] == 1
        assert stats["local_mods"] == 1
        
        print("✅ Mod manager test passed")
        return mod_id, mod_id2
    
    def test_archive_manager(self, mod_id):
        """Test archive management"""
        print("\n=== Testing Archive Manager ===")
        
        # Test adding an archive
        archive_id = self.archive_manager.add_archive(
            mod_id=mod_id,
            version="1.0.0",
            file_name="test_mod_v1.0.0.zip",
            file_size=1024000
        )
        assert archive_id > 0, "Archive ID should be positive"
        print(f"Added archive with ID: {archive_id}")
        
        # Test retrieving the archive
        archive = self.archive_manager.get_archive(archive_id)
        assert archive is not None, "Should retrieve the archive"
        assert archive["file_name"] == "test_mod_v1.0.0.zip"
        assert archive["is_active"] == 1, "Should be active by default"
        
        # Test getting active archive
        active_archive = self.archive_manager.get_active_archive(mod_id)
        assert active_archive is not None, "Should have an active archive"
        assert active_archive["id"] == archive_id
        
        # Add another archive version
        archive_id2 = self.archive_manager.add_archive(
            mod_id=mod_id,
            version="1.1.0",
            file_name="test_mod_v1.1.0.zip",
            file_size=1124000
        )
        
        # The new archive should now be active
        active_archive = self.archive_manager.get_active_archive(mod_id)
        assert active_archive["id"] == archive_id2, "New archive should be active"
        
        # Test getting all archives for mod
        mod_archives = self.archive_manager.get_mod_archives(mod_id)
        assert len(mod_archives) == 2, "Should have 2 archives"
        
        # Test setting active archive
        self.archive_manager.set_active_archive(mod_id, archive_id)
        active_archive = self.archive_manager.get_active_archive(mod_id)
        assert active_archive["id"] == archive_id, "First archive should be active again"
        
        # Test archive by filename
        filename_archive = self.archive_manager.get_archive_by_filename("test_mod_v1.0.0.zip")
        assert filename_archive is not None, "Should find archive by filename"
        assert filename_archive["id"] == archive_id
        
        print("✅ Archive manager test passed")
        return archive_id, archive_id2
    
    def test_deployment_manager(self, mod_id):
        """Test deployment management"""
        print("\n=== Testing Deployment Manager ===")
        
        # Test saving deployment selections
        selected_files = [
            "Data/Scripts/mod_script.lua",
            "Data/Textures/weapon_texture.dds",
            "README.txt"
        ]
        
        self.deployment_manager.save_deployment_selections(mod_id, selected_files)
        
        # Test retrieving selections
        retrieved_selections = self.deployment_manager.get_deployment_selections(mod_id)
        assert len(retrieved_selections) == 3, "Should have 3 selected files"
        assert "Data/Scripts/mod_script.lua" in retrieved_selections
        
        # Test adding individual selection
        self.deployment_manager.add_deployment_selection(mod_id, "Data/Config/settings.cfg")
        updated_selections = self.deployment_manager.get_deployment_selections(mod_id)
        assert len(updated_selections) == 4, "Should have 4 selected files"
        
        # Test removing selection
        removed = self.deployment_manager.remove_deployment_selection(mod_id, "README.txt")
        assert removed == True, "Should successfully remove selection"
        
        final_selections = self.deployment_manager.get_deployment_selections(mod_id)
        assert len(final_selections) == 3, "Should have 3 selected files after removal"
        assert "README.txt" not in final_selections
        
        # Test recording deployed files
        deployed_files = [
            ("C:/Game/Data/Scripts/mod_script.lua", "C:/Backup/mod_script.lua.bak"),
            ("C:/Game/Data/Textures/weapon_texture.dds", None),
            ("C:/Game/Data/Config/settings.cfg", "C:/Backup/settings.cfg.bak")
        ]
        
        for deployed_path, backup_path in deployed_files:
            self.deployment_manager.add_deployed_file(mod_id, deployed_path, backup_path)
        
        # Test retrieving deployed files
        mod_deployed_files = self.deployment_manager.get_deployed_files(mod_id)
        assert len(mod_deployed_files) == 3, "Should have 3 deployed files"
        
        deployed_paths = self.deployment_manager.get_deployed_file_paths(mod_id)
        assert len(deployed_paths) == 3, "Should have 3 deployed file paths"
        
        # Test file conflicts
        conflicts = self.deployment_manager.get_file_conflicts("C:/Game/Data/Scripts/mod_script.lua")
        assert len(conflicts) == 1, "Should have 1 conflict for this file"
        
        # Test deployment statistics
        stats = self.deployment_manager.get_deployment_statistics()
        assert stats["total_deployed_files"] == 3
        assert stats["mods_with_deployments"] == 1
        assert stats["files_with_backups"] == 2
        
        print("✅ Deployment manager test passed")
    
    def test_cascading_deletes(self, mod_id):
        """Test that foreign key constraints work correctly"""
        print("\n=== Testing Cascading Deletes ===")
        
        # Verify we have related data
        archives = self.archive_manager.get_mod_archives(mod_id)
        selections = self.deployment_manager.get_deployment_selections(mod_id)
        deployed = self.deployment_manager.get_deployed_files(mod_id)
        
        assert len(archives) > 0, "Should have archives before deletion"
        assert len(selections) > 0, "Should have selections before deletion"
        assert len(deployed) > 0, "Should have deployed files before deletion"
        
        # Delete the mod
        success = self.mod_manager.remove_mod(mod_id)
        assert success == True, "Should successfully delete mod"
        
        # Verify cascading deletes worked
        archives_after = self.archive_manager.get_mod_archives(mod_id)
        selections_after = self.deployment_manager.get_deployment_selections(mod_id)
        deployed_after = self.deployment_manager.get_deployed_files(mod_id)
        
        assert len(archives_after) == 0, "Archives should be deleted"
        assert len(selections_after) == 0, "Selections should be deleted"
        assert len(deployed_after) == 0, "Deployed files should be deleted"
        
        print("✅ Cascading deletes test passed")
    
    def test_error_handling(self):
        """Test error handling"""
        print("\n=== Testing Error Handling ===")
        
        # Test adding mod with missing required field
        try:
            self.mod_manager.add_mod({"author": "Test"})  # Missing mod_name
            assert False, "Should have raised an error"
        except Exception as e:
            print(f"Correctly caught error: {e}")
        
        # Test getting nonexistent mod
        nonexistent = self.mod_manager.get_mod(99999)
        assert nonexistent is None, "Should return None for nonexistent mod"
        
        # Test duplicate nexus_mod_id
        try:
            self.mod_manager.add_mod({"mod_name": "Test1", "nexus_mod_id": 123})
            self.mod_manager.add_mod({"mod_name": "Test2", "nexus_mod_id": 123})
            assert False, "Should have raised an error for duplicate nexus_mod_id"
        except Exception as e:
            print(f"Correctly caught duplicate error: {e}")
        
        print("✅ Error handling test passed")
    
    def run_all_tests(self):
        """Run all tests"""
        try:
            self.setup()
            
            print("Starting database tests...")
            print("=" * 50)
            
            self.test_database_creation()
            self.test_config_manager()
            mod_id, mod_id2 = self.test_mod_manager()
            archive_id, archive_id2 = self.test_archive_manager(mod_id)
            self.test_deployment_manager(mod_id)
            self.test_cascading_deletes(mod_id)
            self.test_error_handling()
            
            print("\n" + "=" * 50)
            print("🎉 All database tests passed successfully!")
            
            # Show final database info
            info = self.db_manager.get_database_info()
            print(f"\nFinal database info: {info}")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.teardown()
        
        return True


def main():
    """Run database tests"""
    tests = DatabaseTests()
    success = tests.run_all_tests()
    
    if success:
        print("\n✅ Database implementation is working correctly!")
    else:
        print("\n❌ Database tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()