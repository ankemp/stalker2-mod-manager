"""
Database models and schema for Stalker 2 Mod Manager
"""

import sqlite3
import os
import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import config

# Set up logging
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database-related errors"""
    pass


class DatabaseManager:
    """Manages SQLite database operations"""
    
    # Database schema as defined in the application spec
    SCHEMA = {
        "config": """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """,
        "mods": """
            CREATE TABLE IF NOT EXISTS mods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nexus_mod_id INTEGER UNIQUE,
                mod_name TEXT NOT NULL,
                author TEXT,
                summary TEXT,
                latest_version TEXT,
                enabled BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "mod_archives": """
            CREATE TABLE IF NOT EXISTS mod_archives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_id INTEGER NOT NULL,
                version TEXT NOT NULL,
                file_name TEXT NOT NULL UNIQUE,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                file_size INTEGER,
                download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mod_id) REFERENCES mods (id) ON DELETE CASCADE
            )
        """,
        "deployment_selections": """
            CREATE TABLE IF NOT EXISTS deployment_selections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_id INTEGER NOT NULL,
                archive_path TEXT NOT NULL,
                FOREIGN KEY (mod_id) REFERENCES mods (id) ON DELETE CASCADE,
                UNIQUE(mod_id, archive_path)
            )
        """,
        "deployed_files": """
            CREATE TABLE IF NOT EXISTS deployed_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mod_id INTEGER NOT NULL,
                deployed_path TEXT NOT NULL,
                original_backup_path TEXT,
                deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (mod_id) REFERENCES mods (id) ON DELETE CASCADE,
                UNIQUE(deployed_path)
            )
        """
    }
    
    def __init__(self, db_path: str = None):
        """Initialize database manager with the specified database path"""
        if db_path is None:
            # Import here to avoid circular imports
            import config as app_config
            db_path = app_config.DEFAULT_DATABASE_PATH
        
        self.db_path = Path(db_path).resolve()
        
        # Ensure the directory exists with proper error handling
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create database directory {self.db_path.parent}: {e}")
            # Try to use a fallback location in the current directory
            fallback_path = Path("stalker_mod_manager.db").resolve()
            logger.warning(f"Using fallback database path: {fallback_path}")
            self.db_path = fallback_path
        
        logger.info(f"Initializing database at: {self.db_path}")
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and tables if they don't exist"""
        try:
            with self.get_connection() as conn:
                # Enable foreign key constraints
                conn.execute("PRAGMA foreign_keys = ON")
                
                # Create all tables
                for table_name, schema in self.SCHEMA.items():
                    logger.debug(f"Creating table: {table_name}")
                    conn.execute(schema)
                
                # Create indexes for better performance
                self._create_indexes(conn)
                
                conn.commit()
                logger.info("Database schema created successfully")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to create database schema: {e}")
            raise DatabaseError(f"Failed to create database: {e}")
    
    def _create_indexes(self, conn: sqlite3.Connection):
        """Create database indexes for better performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_mods_nexus_id ON mods(nexus_mod_id)",
            "CREATE INDEX IF NOT EXISTS idx_mods_enabled ON mods(enabled)",
            "CREATE INDEX IF NOT EXISTS idx_archives_mod_id ON mod_archives(mod_id)",
            "CREATE INDEX IF NOT EXISTS idx_archives_active ON mod_archives(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_selections_mod_id ON deployment_selections(mod_id)",
            "CREATE INDEX IF NOT EXISTS idx_deployed_mod_id ON deployed_files(mod_id)",
            "CREATE INDEX IF NOT EXISTS idx_deployed_path ON deployed_files(deployed_path)"
        ]
        
        for index in indexes:
            conn.execute(index)
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with proper context management"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row  # Enable column access by name
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dictionaries"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                # Convert Row objects to dictionaries
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Query execution failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Query failed: {e}")
    
    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE command and return affected rows"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(command, params)
                conn.commit()
                return cursor.rowcount
        except sqlite3.Error as e:
            logger.error(f"Command execution failed: {e}")
            logger.error(f"Command: {command}")
            logger.error(f"Params: {params}")
            raise DatabaseError(f"Command failed: {e}")
    
    def execute_script(self, script: str) -> None:
        """Execute a multi-statement script"""
        try:
            with self.get_connection() as conn:
                conn.executescript(script)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Script execution failed: {e}")
            raise DatabaseError(f"Script failed: {e}")
    
    def get_last_insert_id(self) -> int:
        """Get the last inserted row ID"""
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("SELECT last_insert_rowid()")
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Failed to get last insert ID: {e}")
            raise DatabaseError(f"Failed to get last insert ID: {e}")
    
    def vacuum(self) -> None:
        """Optimize the database"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.commit()
            logger.info("Database vacuumed successfully")
        except sqlite3.Error as e:
            logger.error(f"Database vacuum failed: {e}")
            raise DatabaseError(f"Vacuum failed: {e}")
    
    def backup(self, backup_path: str) -> None:
        """Create a backup of the database"""
        try:
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self.get_connection() as conn:
                with sqlite3.connect(str(backup_path)) as backup_conn:
                    conn.backup(backup_conn)
            
            logger.info(f"Database backed up to: {backup_path}")
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Database backup failed: {e}")
            raise DatabaseError(f"Backup failed: {e}")
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with self.get_connection() as conn:
                # Get table counts
                tables = {}
                for table_name in self.SCHEMA.keys():
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                    tables[table_name] = cursor.fetchone()[0]
                
                # Get database size
                db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                # Get SQLite version
                cursor = conn.execute("SELECT sqlite_version()")
                sqlite_version = cursor.fetchone()[0]
                
                return {
                    "database_path": str(self.db_path),
                    "database_size": db_size,
                    "sqlite_version": sqlite_version,
                    "table_counts": tables
                }
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Failed to get database info: {e}")
            raise DatabaseError(f"Failed to get database info: {e}")


class ConfigManager:
    """Manages application configuration in the database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def get_config(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a configuration value"""
        try:
            results = self.db.execute_query(
                "SELECT value FROM config WHERE key = ?",
                (key,)
            )
            if results:
                return results[0]["value"]
            return default
        except DatabaseError as e:
            logger.error(f"Failed to get config '{key}': {e}")
            return default
    
    def set_config(self, key: str, value: str) -> None:
        """Set a configuration value"""
        try:
            # Use INSERT OR REPLACE to update existing or create new
            self.db.execute_command(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)",
                (key, value)
            )
            logger.debug(f"Set config '{key}' = '{value}'")
        except DatabaseError as e:
            logger.error(f"Failed to set config '{key}': {e}")
            raise
    
    def get_all_config(self) -> Dict[str, str]:
        """Get all configuration values"""
        try:
            results = self.db.execute_query("SELECT key, value FROM config")
            return {row["key"]: row["value"] for row in results}
        except DatabaseError as e:
            logger.error(f"Failed to get all config: {e}")
            return {}
    
    def delete_config(self, key: str) -> bool:
        """Delete a configuration value"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM config WHERE key = ?",
                (key,)
            )
            return affected > 0
        except DatabaseError as e:
            logger.error(f"Failed to delete config '{key}': {e}")
            return False
    
    # Convenience methods for common configuration values
    
    def get_api_key(self) -> Optional[str]:
        """Get the Nexus Mods API key"""
        return self.get_config("nexus_api_key")
    
    def set_api_key(self, api_key: str) -> None:
        """Set the Nexus Mods API key"""
        self.set_config("nexus_api_key", api_key)
    
    def get_game_path(self) -> Optional[str]:
        """Get the game installation path"""
        return self.get_config("game_path")
    
    def set_game_path(self, path: str) -> None:
        """Set the game installation path"""
        self.set_config("game_path", path)
    
    def get_mods_directory(self) -> Optional[str]:
        """Get the mod storage directory"""
        return self.get_config("mods_directory")
    
    def set_mods_directory(self, path: str) -> None:
        """Set the mod storage directory"""
        self.set_config("mods_directory", path)
    
    def get_auto_check_updates(self) -> bool:
        """Get auto update checking setting"""
        return self.get_config("auto_check_updates", "true").lower() == "true"
    
    def set_auto_check_updates(self, enabled: bool) -> None:
        """Set auto update checking setting"""
        self.set_config("auto_check_updates", "true" if enabled else "false")
    
    def get_update_interval(self) -> int:
        """Get update check interval in hours"""
        try:
            return int(self.get_config("update_interval_hours", str(config.DEFAULT_UPDATE_INTERVAL_HOURS)))
        except (ValueError, TypeError):
            return config.DEFAULT_UPDATE_INTERVAL_HOURS
    
    def set_update_interval(self, hours: int) -> None:
        """Set update check interval in hours"""
        self.set_config("update_interval_hours", str(hours))
    
    def get_confirm_actions(self) -> bool:
        """Get confirmation dialog setting"""
        return self.get_config("confirm_actions", "true").lower() == "true"
    
    def set_confirm_actions(self, enabled: bool) -> None:
        """Set confirmation dialog setting"""
        self.set_config("confirm_actions", "true" if enabled else "false")
    
    def get_show_notifications(self) -> bool:
        """Get system notifications setting"""
        return self.get_config("show_notifications", "true").lower() == "true"
    
    def set_show_notifications(self, enabled: bool) -> None:
        """Set system notifications setting"""
        self.set_config("show_notifications", "true" if enabled else "false")


class ModManager:
    """Manages mod records in the database"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_mod(self, mod_data: Dict[str, Any]) -> int:
        """Add a new mod and return its ID"""
        try:
            # Extract required and optional fields
            nexus_mod_id = mod_data.get("nexus_mod_id")
            mod_name = mod_data.get("mod_name") or mod_data.get("name")
            author = mod_data.get("author")
            summary = mod_data.get("summary")
            latest_version = mod_data.get("latest_version") or mod_data.get("version")
            enabled = mod_data.get("enabled", False)
            
            if not mod_name:
                raise ValueError("mod_name is required")
            
            # Insert the mod
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO mods (nexus_mod_id, mod_name, author, summary, latest_version, enabled)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nexus_mod_id, mod_name, author, summary, latest_version, enabled))
                
                mod_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added mod '{mod_name}' with ID {mod_id}")
                return mod_id
                
        except (sqlite3.Error, ValueError) as e:
            logger.error(f"Failed to add mod: {e}")
            logger.error(f"Mod data: {mod_data}")
            raise DatabaseError(f"Failed to add mod: {e}")
    
    def get_mod(self, mod_id: int) -> Optional[Dict[str, Any]]:
        """Get mod by ID"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM mods WHERE id = ?",
                (mod_id,)
            )
            return results[0] if results else None
        except DatabaseError as e:
            logger.error(f"Failed to get mod {mod_id}: {e}")
            return None
    
    def get_mod_by_nexus_id(self, nexus_mod_id: int) -> Optional[Dict[str, Any]]:
        """Get mod by Nexus Mods ID"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM mods WHERE nexus_mod_id = ?",
                (nexus_mod_id,)
            )
            return results[0] if results else None
        except DatabaseError as e:
            logger.error(f"Failed to get mod by Nexus ID {nexus_mod_id}: {e}")
            return None
    
    def get_all_mods(self) -> List[Dict[str, Any]]:
        """Get all mods"""
        try:
            return self.db.execute_query(
                "SELECT * FROM mods ORDER BY mod_name"
            )
        except DatabaseError as e:
            logger.error(f"Failed to get all mods: {e}")
            return []
    
    def get_enabled_mods(self) -> List[Dict[str, Any]]:
        """Get all enabled mods"""
        try:
            return self.db.execute_query(
                "SELECT * FROM mods WHERE enabled = 1 ORDER BY mod_name"
            )
        except DatabaseError as e:
            logger.error(f"Failed to get enabled mods: {e}")
            return []
    
    def get_disabled_mods(self) -> List[Dict[str, Any]]:
        """Get all disabled mods"""
        try:
            return self.db.execute_query(
                "SELECT * FROM mods WHERE enabled = 0 ORDER BY mod_name"
            )
        except DatabaseError as e:
            logger.error(f"Failed to get disabled mods: {e}")
            return []
    
    def get_outdated_mods(self) -> List[Dict[str, Any]]:
        """Get mods that have updates available"""
        try:
            # Get mods where there's a newer version available
            # This requires comparing current version with latest_version
            results = self.db.execute_query("""
                SELECT m.*, ma.version as current_version
                FROM mods m
                JOIN mod_archives ma ON m.id = ma.mod_id AND ma.is_active = 1
                WHERE m.latest_version IS NOT NULL 
                AND m.latest_version != ma.version
                ORDER BY m.mod_name
            """)
            return results
        except DatabaseError as e:
            logger.error(f"Failed to get outdated mods: {e}")
            return []
    
    def update_mod(self, mod_id: int, mod_data: Dict[str, Any]) -> None:
        """Update mod data"""
        try:
            # Build update query dynamically based on provided data
            update_fields = []
            params = []
            
            for field in ["nexus_mod_id", "mod_name", "author", "summary", "latest_version", "enabled"]:
                if field in mod_data:
                    update_fields.append(f"{field} = ?")
                    params.append(mod_data[field])
            
            if not update_fields:
                logger.warning(f"No fields to update for mod {mod_id}")
                return
            
            # Add updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            params.append(mod_id)
            
            query = f"UPDATE mods SET {', '.join(update_fields)} WHERE id = ?"
            affected = self.db.execute_command(query, tuple(params))
            
            if affected > 0:
                logger.info(f"Updated mod {mod_id}")
            else:
                logger.warning(f"No mod found with ID {mod_id}")
                
        except DatabaseError as e:
            logger.error(f"Failed to update mod {mod_id}: {e}")
            raise
    
    def remove_mod(self, mod_id: int) -> bool:
        """Remove mod and all related data (cascading delete)"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM mods WHERE id = ?",
                (mod_id,)
            )
            
            if affected > 0:
                logger.info(f"Removed mod {mod_id}")
                return True
            else:
                logger.warning(f"No mod found with ID {mod_id}")
                return False
                
        except DatabaseError as e:
            logger.error(f"Failed to remove mod {mod_id}: {e}")
            raise
    
    def set_mod_enabled(self, mod_id: int, enabled: bool) -> None:
        """Set mod enabled/disabled status"""
        try:
            affected = self.db.execute_command(
                "UPDATE mods SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (enabled, mod_id)
            )
            
            if affected > 0:
                status = "enabled" if enabled else "disabled"
                logger.info(f"Mod {mod_id} {status}")
            else:
                logger.warning(f"No mod found with ID {mod_id}")
                
        except DatabaseError as e:
            logger.error(f"Failed to set mod {mod_id} enabled status: {e}")
            raise
    
    def search_mods(self, search_term: str) -> List[Dict[str, Any]]:
        """Search mods by name or author"""
        try:
            search_pattern = f"%{search_term}%"
            return self.db.execute_query("""
                SELECT * FROM mods 
                WHERE mod_name LIKE ? OR author LIKE ?
                ORDER BY mod_name
            """, (search_pattern, search_pattern))
        except DatabaseError as e:
            logger.error(f"Failed to search mods: {e}")
            return []
    
    def get_mod_statistics(self) -> Dict[str, int]:
        """Get statistics about mods"""
        try:
            stats = {}
            
            # Total mods
            result = self.db.execute_query("SELECT COUNT(*) as count FROM mods")
            stats["total"] = result[0]["count"] if result else 0
            
            # Enabled mods
            result = self.db.execute_query("SELECT COUNT(*) as count FROM mods WHERE enabled = 1")
            stats["enabled"] = result[0]["count"] if result else 0
            
            # Disabled mods
            result = self.db.execute_query("SELECT COUNT(*) as count FROM mods WHERE enabled = 0")
            stats["disabled"] = result[0]["count"] if result else 0
            
            # Nexus mods
            result = self.db.execute_query("SELECT COUNT(*) as count FROM mods WHERE nexus_mod_id IS NOT NULL")
            stats["nexus_mods"] = result[0]["count"] if result else 0
            
            # Local mods
            result = self.db.execute_query("SELECT COUNT(*) as count FROM mods WHERE nexus_mod_id IS NULL")
            stats["local_mods"] = result[0]["count"] if result else 0
            
            return stats
            
        except DatabaseError as e:
            logger.error(f"Failed to get mod statistics: {e}")
            return {}


class ArchiveManager:
    """Manages mod archive records"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def add_archive(self, mod_id: int, version: str, file_name: str, 
                   file_size: Optional[int] = None, set_active: bool = True) -> int:
        """Add a new mod archive"""
        try:
            # If this should be the active archive, deactivate others first
            if set_active:
                self.db.execute_command(
                    "UPDATE mod_archives SET is_active = 0 WHERE mod_id = ?",
                    (mod_id,)
                )
            
            # Insert the new archive
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO mod_archives (mod_id, version, file_name, is_active, file_size)
                    VALUES (?, ?, ?, ?, ?)
                """, (mod_id, version, file_name, set_active, file_size))
                
                archive_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Added archive '{file_name}' for mod {mod_id}")
                return archive_id
                
        except sqlite3.Error as e:
            logger.error(f"Failed to add archive: {e}")
            raise DatabaseError(f"Failed to add archive: {e}")
    
    def get_archive(self, archive_id: int) -> Optional[Dict[str, Any]]:
        """Get archive by ID"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM mod_archives WHERE id = ?",
                (archive_id,)
            )
            return results[0] if results else None
        except DatabaseError as e:
            logger.error(f"Failed to get archive {archive_id}: {e}")
            return None
    
    def get_active_archive(self, mod_id: int) -> Optional[Dict[str, Any]]:
        """Get the active archive for a mod"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM mod_archives WHERE mod_id = ? AND is_active = 1",
                (mod_id,)
            )
            return results[0] if results else None
        except DatabaseError as e:
            logger.error(f"Failed to get active archive for mod {mod_id}: {e}")
            return None
    
    def get_mod_archives(self, mod_id: int) -> List[Dict[str, Any]]:
        """Get all archives for a mod"""
        try:
            return self.db.execute_query(
                "SELECT * FROM mod_archives WHERE mod_id = ? ORDER BY download_date DESC",
                (mod_id,)
            )
        except DatabaseError as e:
            logger.error(f"Failed to get archives for mod {mod_id}: {e}")
            return []
    
    def set_active_archive(self, mod_id: int, archive_id: int) -> None:
        """Set which archive is active for a mod"""
        try:
            with self.db.get_connection() as conn:
                # Deactivate all archives for this mod
                conn.execute(
                    "UPDATE mod_archives SET is_active = 0 WHERE mod_id = ?",
                    (mod_id,)
                )
                
                # Activate the specified archive
                cursor = conn.execute(
                    "UPDATE mod_archives SET is_active = 1 WHERE id = ? AND mod_id = ?",
                    (archive_id, mod_id)
                )
                
                if cursor.rowcount == 0:
                    raise DatabaseError(f"Archive {archive_id} not found for mod {mod_id}")
                
                conn.commit()
                logger.info(f"Set archive {archive_id} active for mod {mod_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to set active archive: {e}")
            raise DatabaseError(f"Failed to set active archive: {e}")
    
    def remove_archive(self, archive_id: int) -> bool:
        """Remove an archive record"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM mod_archives WHERE id = ?",
                (archive_id,)
            )
            
            if affected > 0:
                logger.info(f"Removed archive {archive_id}")
                return True
            else:
                logger.warning(f"No archive found with ID {archive_id}")
                return False
                
        except DatabaseError as e:
            logger.error(f"Failed to remove archive {archive_id}: {e}")
            raise
    
    def remove_mod_archives(self, mod_id: int) -> int:
        """Remove all archives for a mod"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM mod_archives WHERE mod_id = ?",
                (mod_id,)
            )
            
            logger.info(f"Removed {affected} archives for mod {mod_id}")
            return affected
            
        except DatabaseError as e:
            logger.error(f"Failed to remove archives for mod {mod_id}: {e}")
            raise
    
    def update_archive(self, archive_id: int, update_data: Dict[str, Any]) -> None:
        """Update archive data"""
        try:
            # Build update query dynamically
            update_fields = []
            params = []
            
            for field in ["version", "file_name", "is_active", "file_size"]:
                if field in update_data:
                    update_fields.append(f"{field} = ?")
                    params.append(update_data[field])
            
            if not update_fields:
                logger.warning(f"No fields to update for archive {archive_id}")
                return
            
            params.append(archive_id)
            query = f"UPDATE mod_archives SET {', '.join(update_fields)} WHERE id = ?"
            
            affected = self.db.execute_command(query, tuple(params))
            
            if affected > 0:
                logger.info(f"Updated archive {archive_id}")
            else:
                logger.warning(f"No archive found with ID {archive_id}")
                
        except DatabaseError as e:
            logger.error(f"Failed to update archive {archive_id}: {e}")
            raise
    
    def get_archive_by_filename(self, file_name: str) -> Optional[Dict[str, Any]]:
        """Get archive by filename"""
        try:
            results = self.db.execute_query(
                "SELECT * FROM mod_archives WHERE file_name = ?",
                (file_name,)
            )
            return results[0] if results else None
        except DatabaseError as e:
            logger.error(f"Failed to get archive by filename '{file_name}': {e}")
            return None
    
    def get_all_archives(self) -> List[Dict[str, Any]]:
        """Get all archives"""
        try:
            return self.db.execute_query(
                "SELECT * FROM mod_archives ORDER BY download_date DESC"
            )
        except DatabaseError as e:
            logger.error(f"Failed to get all archives: {e}")
            return []


class DeploymentManager:
    """Manages file deployment selections and tracking"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def save_deployment_selections(self, mod_id: int, selected_files: List[str]) -> None:
        """Save which files are selected for deployment"""
        try:
            with self.db.get_connection() as conn:
                # Remove existing selections for this mod
                conn.execute(
                    "DELETE FROM deployment_selections WHERE mod_id = ?",
                    (mod_id,)
                )
                
                # Insert new selections
                for file_path in selected_files:
                    conn.execute(
                        "INSERT INTO deployment_selections (mod_id, archive_path) VALUES (?, ?)",
                        (mod_id, file_path)
                    )
                
                conn.commit()
                logger.info(f"Saved {len(selected_files)} deployment selections for mod {mod_id}")
                
        except sqlite3.Error as e:
            logger.error(f"Failed to save deployment selections: {e}")
            raise DatabaseError(f"Failed to save deployment selections: {e}")
    
    def get_deployment_selections(self, mod_id: int) -> List[str]:
        """Get the selected files for deployment"""
        try:
            results = self.db.execute_query(
                "SELECT archive_path FROM deployment_selections WHERE mod_id = ? ORDER BY archive_path",
                (mod_id,)
            )
            return [row["archive_path"] for row in results]
        except DatabaseError as e:
            logger.error(f"Failed to get deployment selections for mod {mod_id}: {e}")
            return []
    
    def add_deployment_selection(self, mod_id: int, archive_path: str) -> None:
        """Add a single deployment selection"""
        try:
            self.db.execute_command(
                "INSERT OR IGNORE INTO deployment_selections (mod_id, archive_path) VALUES (?, ?)",
                (mod_id, archive_path)
            )
            logger.debug(f"Added deployment selection '{archive_path}' for mod {mod_id}")
        except DatabaseError as e:
            logger.error(f"Failed to add deployment selection: {e}")
            raise
    
    def remove_deployment_selection(self, mod_id: int, archive_path: str) -> bool:
        """Remove a deployment selection"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM deployment_selections WHERE mod_id = ? AND archive_path = ?",
                (mod_id, archive_path)
            )
            return affected > 0
        except DatabaseError as e:
            logger.error(f"Failed to remove deployment selection: {e}")
            raise
    
    def clear_deployment_selections(self, mod_id: int) -> int:
        """Clear all deployment selections for a mod"""
        try:
            affected = self.db.execute_command(
                "DELETE FROM deployment_selections WHERE mod_id = ?",
                (mod_id,)
            )
            logger.info(f"Cleared {affected} deployment selections for mod {mod_id}")
            return affected
        except DatabaseError as e:
            logger.error(f"Failed to clear deployment selections for mod {mod_id}: {e}")
            raise
    
    def add_deployed_file(self, mod_id: int, deployed_path: str, 
                         original_backup_path: Optional[str] = None) -> None:
        """Record a deployed file"""
        try:
            self.db.execute_command(
                "INSERT OR REPLACE INTO deployed_files (mod_id, deployed_path, original_backup_path) VALUES (?, ?, ?)",
                (mod_id, deployed_path, original_backup_path)
            )
            logger.debug(f"Recorded deployed file '{deployed_path}' for mod {mod_id}")
        except DatabaseError as e:
            logger.error(f"Failed to record deployed file: {e}")
            raise
    
    def get_deployed_files(self, mod_id: int) -> List[Dict[str, Any]]:
        """Get all deployed files for a mod"""
        try:
            return self.db.execute_query(
                "SELECT * FROM deployed_files WHERE mod_id = ? ORDER BY deployed_path",
                (mod_id,)
            )
        except DatabaseError as e:
            logger.error(f"Failed to get deployed files for mod {mod_id}: {e}")
            return []
    
    def get_deployed_file_paths(self, mod_id: int) -> List[str]:
        """Get just the deployed file paths for a mod"""
        try:
            results = self.db.execute_query(
                "SELECT deployed_path FROM deployed_files WHERE mod_id = ? ORDER BY deployed_path",
                (mod_id,)
            )
            return [row["deployed_path"] for row in results]
        except DatabaseError as e:
            logger.error(f"Failed to get deployed file paths for mod {mod_id}: {e}")
            return []
    
    def remove_deployed_file(self, deployed_path: str) -> Optional[Dict[str, Any]]:
        """Remove a deployed file record and return its info"""
        try:
            # Get the file info first
            results = self.db.execute_query(
                "SELECT * FROM deployed_files WHERE deployed_path = ?",
                (deployed_path,)
            )
            
            if not results:
                return None
            
            file_info = results[0]
            
            # Remove the record
            self.db.execute_command(
                "DELETE FROM deployed_files WHERE deployed_path = ?",
                (deployed_path,)
            )
            
            logger.debug(f"Removed deployed file record: {deployed_path}")
            return file_info
            
        except DatabaseError as e:
            logger.error(f"Failed to remove deployed file '{deployed_path}': {e}")
            raise
    
    def remove_deployed_files(self, mod_id: int) -> List[Dict[str, Any]]:
        """Remove all deployed file records for a mod and return their info"""
        try:
            # Get the file info first
            deployed_files = self.get_deployed_files(mod_id)
            
            # Remove all records
            affected = self.db.execute_command(
                "DELETE FROM deployed_files WHERE mod_id = ?",
                (mod_id,)
            )
            
            logger.info(f"Removed {affected} deployed file records for mod {mod_id}")
            return deployed_files
            
        except DatabaseError as e:
            logger.error(f"Failed to remove deployed files for mod {mod_id}: {e}")
            raise
    
    def get_file_conflicts(self, deployed_path: str) -> List[Dict[str, Any]]:
        """Get all mods that have deployed the same file path"""
        try:
            return self.db.execute_query(
                "SELECT * FROM deployed_files WHERE deployed_path = ?",
                (deployed_path,)
            )
        except DatabaseError as e:
            logger.error(f"Failed to get file conflicts for '{deployed_path}': {e}")
            return []
    
    def get_all_deployed_files(self) -> List[Dict[str, Any]]:
        """Get all deployed files across all mods"""
        try:
            return self.db.execute_query("""
                SELECT df.*, m.mod_name 
                FROM deployed_files df
                JOIN mods m ON df.mod_id = m.id
                ORDER BY df.deployed_path
            """)
        except DatabaseError as e:
            logger.error(f"Failed to get all deployed files: {e}")
            return []
    
    def get_deployment_statistics(self) -> Dict[str, int]:
        """Get statistics about deployments"""
        try:
            stats = {}
            
            # Total deployed files
            result = self.db.execute_query("SELECT COUNT(*) as count FROM deployed_files")
            stats["total_deployed_files"] = result[0]["count"] if result else 0
            
            # Mods with deployments
            result = self.db.execute_query("SELECT COUNT(DISTINCT mod_id) as count FROM deployed_files")
            stats["mods_with_deployments"] = result[0]["count"] if result else 0
            
            # Files with backups
            result = self.db.execute_query("SELECT COUNT(*) as count FROM deployed_files WHERE original_backup_path IS NOT NULL")
            stats["files_with_backups"] = result[0]["count"] if result else 0
            
            # Potential conflicts (same file deployed by multiple mods)
            result = self.db.execute_query("""
                SELECT COUNT(*) as count FROM (
                    SELECT deployed_path FROM deployed_files 
                    GROUP BY deployed_path 
                    HAVING COUNT(*) > 1
                )
            """)
            stats["potential_conflicts"] = result[0]["count"] if result else 0
            
            return stats
            
        except DatabaseError as e:
            logger.error(f"Failed to get deployment statistics: {e}")
            return {}