"""
Comprehensive test runner for all Stalker 2 Mod Manager tests
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test_file(test_file: str) -> bool:
    """Run a single test file and return success status"""
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    print(f"\n🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        # Run the test file as a subprocess
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=False,
            text=True,
            cwd=test_path.parent.parent  # Run from project root
        )
        
        success = result.returncode == 0
        if success:
            print(f"✅ {test_file} completed successfully")
        else:
            print(f"❌ {test_file} failed with exit code {result.returncode}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def run_validation_script() -> bool:
    """Run the API compliance validation script"""
    script_path = Path(__file__).parent.parent / "scripts" / "validate_api_compliance.py"
    
    if not script_path.exists():
        print("❌ Validation script not found")
        return False
    
    print(f"\n🔍 Running API Compliance Validation...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            cwd=script_path.parent.parent  # Run from project root
        )
        
        success = result.returncode == 0
        if success:
            print("✅ API compliance validation completed successfully")
        else:
            print(f"❌ API compliance validation failed with exit code {result.returncode}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running validation: {e}")
        return False

def main():
    """Run all tests and validations"""
    print("Stalker 2 Mod Manager - Comprehensive Test Suite")
    print("=" * 60)
    
    # Discover all test files matching 'test_*.py' in the tests directory
    test_files = sorted([
        f.name for f in Path(__file__).parent.glob("test_*.py")
        if f.name != "run_all_tests.py"
    ])
    
    # Track results
    results = {}
    all_passed = True
    
    # Run each test file
    for test_file in test_files:
        success = run_test_file(test_file)
        results[test_file] = success
        if not success:
            all_passed = False
    
    # Run validation script
    validation_success = run_validation_script()
    results["API Compliance Validation"] = validation_success
    if not validation_success:
        all_passed = False
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n{'=' * 60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED! The application is ready for use.")
        print("\n💡 Next steps:")
        print("   • Run the application: python main.py")
        print("   • Try the API demo: python scripts/demo_nexus_api.py")
        print("   • Check database info: python scripts/show_db_info.py")
    else:
        failed_count = sum(1 for success in results.values() if not success)
        print(f"⚠️  {failed_count} test(s) failed. Please review the output above.")
        print("\n🔧 Troubleshooting:")
        print("   • Check that all dependencies are installed: pip install -r requirements.txt")
        print("   • Ensure the virtual environment is activated")
        print("   • Review error messages for specific issues")
    
    print(f"{'=' * 60}")
    
    # Return appropriate exit code
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)