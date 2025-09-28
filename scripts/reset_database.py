"""
Reset the database to a clean state
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config as app_config

def main():
    """Reset the database"""
    print("Stalker 2 Mod Manager - Database Reset")
    print("=" * 40)
    
    db_path = Path(app_config.DEFAULT_DATABASE_PATH)
    
    print(f"📁 Database location: {db_path}")
    
    if db_path.exists():
        print(f"🗑️  Removing existing database...")
        db_path.unlink()
        print("   ✅ Database removed")
    else:
        print("📄 No existing database found")
    
    print("🔄 Database will be recreated on next application run")
    print("💡 Run 'python main.py' to start with a fresh database")
    print("💡 Run 'python show_db_info.py' to view database information")

if __name__ == "__main__":
    main()