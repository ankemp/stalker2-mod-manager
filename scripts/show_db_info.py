"""
Show database information and statistics
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import DatabaseManager, ConfigManager, ModManager, ArchiveManager, DeploymentManager
import config as app_config

def main():
    """Display database information"""
    print("Stalker 2 Mod Manager - Database Information")
    print("=" * 50)
    
    # Show app configuration first
    app_info = app_config.get_app_info()
    print(f"\n📱 Application Info:")
    print(f"  Name: {app_info['app_name']} v{app_info['app_version']}")
    print(f"  Platform: {'Windows' if app_info['is_windows'] else 'Other'}")
    print(f"  Virtual Environment: {'Yes' if app_info['is_venv'] else 'No'}")
    
    print(f"\n📁 Data Locations:")
    print(f"  App Data (Roaming): {app_info['app_data_dir']}")
    print(f"  Local App Data:     {app_info['local_app_data_dir']}")
    print(f"  Database:           {app_info['database_path']}")
    print(f"  Mods Directory:     {app_info['mods_dir']}")
    print(f"  Cache Directory:    {app_info['cache_dir']}")
    print(f"  Backup Directory:   {app_info['backup_dir']}")
    
    # Ensure directories exist
    app_config.ensure_directories()
    
    # Initialize database components
    db_manager = DatabaseManager(app_config.DEFAULT_DATABASE_PATH)
    config_manager = ConfigManager(db_manager)
    mod_manager = ModManager(db_manager)
    archive_manager = ArchiveManager(db_manager)
    deployment_manager = DeploymentManager(db_manager)
    
    # Show database info
    print("\n📊 Database Information:")
    db_info = db_manager.get_database_info()
    for key, value in db_info.items():
        if key == "table_counts":
            print(f"  {key}:")
            for table, count in value.items():
                print(f"    {table}: {count} records")
        elif key == "database_size":
            print(f"  {key}: {value:,} bytes ({value/1024:.1f} KB)")
        else:
            print(f"  {key}: {value}")
    
    # Show mod statistics
    print("\n🎮 Mod Statistics:")
    mod_stats = mod_manager.get_mod_statistics()
    for key, value in mod_stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Show deployment statistics
    print("\n📁 Deployment Statistics:")
    deploy_stats = deployment_manager.get_deployment_statistics()
    for key, value in deploy_stats.items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    # Show some configuration
    print("\n⚙️  Configuration:")
    game_path = config_manager.get_game_path()
    print(f"  Game Path: {game_path or 'Not set'}")
    
    mods_dir = config_manager.get_mods_directory()
    print(f"  Mods Directory: {mods_dir or 'Not set'}")
    
    api_key = config_manager.get_api_key()
    print(f"  API Key: {'Configured' if api_key else 'Not set'}")
    
    auto_update = config_manager.get_auto_check_updates()
    print(f"  Auto Check Updates: {auto_update}")
    
    update_interval = config_manager.get_update_interval()
    print(f"  Update Interval: {update_interval} hours")
    
    # Show individual mods
    print("\n📦 Installed Mods:")
    all_mods = mod_manager.get_all_mods()
    
    if not all_mods:
        print("  No mods installed yet")
    else:
        for mod in all_mods:
            status = "✅ Enabled" if mod["enabled"] else "❌ Disabled"
            nexus_info = f" (Nexus ID: {mod['nexus_mod_id']})" if mod["nexus_mod_id"] else " (Local)"
            print(f"  {status} {mod['mod_name']} v{mod['latest_version'] or 'Unknown'}{nexus_info}")
            
            # Show archives
            archives = archive_manager.get_mod_archives(mod["id"])
            for archive in archives:
                active = "🔸 Active" if archive["is_active"] else "  "
                size = f" ({archive['file_size']:,} bytes)" if archive["file_size"] else ""
                print(f"    {active} {archive['file_name']} v{archive['version']}{size}")
            
            # Show deployment info
            if mod["enabled"]:
                deployed_files = deployment_manager.get_deployed_file_paths(mod["id"])
                if deployed_files:
                    print(f"    📁 {len(deployed_files)} files deployed")
    
    print("\n" + "=" * 50)
    print("✅ Database is working correctly!")

if __name__ == "__main__":
    main()