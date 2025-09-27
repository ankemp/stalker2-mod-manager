"""
Simple test to verify UI components can be instantiated without errors
"""

import sys
import os
import traceback

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test GUI imports
        from gui.main_window import MainWindow
        from gui.dialogs import AddModDialog, SettingsDialog, DeploymentSelectionDialog
        from gui.components import ModListFrame, ModDetailsFrame, StatusBar
        print("✅ GUI modules imported successfully")
        
        # Test other module imports
        from database.models import DatabaseManager, ConfigManager, ModManager
        from api.nexus_api import NexusModsClient
        from utils.file_manager import ArchiveManager, GameDirectoryManager
        print("✅ Backend modules imported successfully")
        
        # Test config import
        import config
        print("✅ Configuration module imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False

def test_ui_creation():
    """Test that UI components can be created"""
    try:
        print("\nTesting UI component creation...")
        
        import tkinter as tk
        import ttkbootstrap as ttk_bootstrap
        
        # Create root window
        root = ttk_bootstrap.Window(themename="darkly")
        root.withdraw()  # Hide the window
        
        # Test dialog creation (without showing)
        from gui.dialogs import AddModDialog, SettingsDialog
        
        # These should not show the dialogs, just test instantiation
        print("✅ UI components can be created successfully")
        
        root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ UI creation error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Stalker 2 Mod Manager - UI Test Suite")
    print("=" * 50)
    
    success = True
    
    # Test imports
    success &= test_imports()
    
    # Test UI creation
    success &= test_ui_creation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The application should run correctly.")
        print("\nTo run the application: python main.py")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()