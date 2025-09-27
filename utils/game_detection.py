"""
Game path detection utilities for Stalker 2: Heart of Chornobyl
"""

import os
import sys
import logging
import winreg
from pathlib import Path
from typing import Optional, List, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)


class GameDetector:
    """Detects Stalker 2 game installation paths"""
    
    # Game identifiers
    GAME_EXECUTABLE = "Stalker2-Win64-Shipping.exe"
    GAME_DATA_FOLDER = "Stalker2"  # Folder containing game data
    STEAM_APP_ID = "1643320"  # Stalker 2 Steam App ID
    
    # Common installation directories to check
    COMMON_PATHS = [
        # Steam default paths
        r"C:\Program Files (x86)\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"C:\Program Files\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"D:\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"E:\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"F:\Steam\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        
        # Epic Games Store paths
        r"C:\Program Files\Epic Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"D:\Epic Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"E:\Epic Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        
        # GOG paths
        r"C:\Program Files (x86)\GOG Galaxy\Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"C:\GOG Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"D:\GOG Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        
        # Microsoft Store / Xbox Game Pass paths
        r"C:\Program Files\WindowsApps\GSCGameWorld.STALKERHeartofChornobyl_1.0.0.0_x64__h0dg9mbfpz6m4",
        r"C:\XboxGames\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        
        # Alternative common locations
        r"C:\Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"D:\Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"E:\Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
        r"F:\Games\S.T.A.L.K.E.R. 2 Heart of Chornobyl",
    ]
    
    def __init__(self):
        """Initialize the game detector"""
        self.detected_paths = []
        self.detection_methods = []
    
    def detect_all_installations(self) -> List[Dict[str, Any]]:
        """Detect all possible game installations and return detailed information"""
        installations = []
        
        # Method 1: Registry detection
        steam_paths = self._detect_from_steam_registry()
        for path in steam_paths:
            if self._validate_game_path(path):
                installations.append({
                    "path": path,
                    "method": "Steam Registry",
                    "platform": "Steam",
                    "confidence": "High"
                })
        
        # Method 2: Epic Games launcher registry
        epic_paths = self._detect_from_epic_registry()
        for path in epic_paths:
            if self._validate_game_path(path):
                installations.append({
                    "path": path,
                    "method": "Epic Games Registry",
                    "platform": "Epic Games Store",
                    "confidence": "High"
                })
        
        # Method 3: GOG registry
        gog_paths = self._detect_from_gog_registry()
        for path in gog_paths:
            if self._validate_game_path(path):
                installations.append({
                    "path": path,
                    "method": "GOG Registry",
                    "platform": "GOG",
                    "confidence": "High"
                })
        
        # Method 4: Common path scanning
        common_paths = self._scan_common_paths()
        for path in common_paths:
            # Check if we already found this path through registry
            if not any(inst["path"].lower() == path.lower() for inst in installations):
                installations.append({
                    "path": path,
                    "method": "Common Path Scan",
                    "platform": "Unknown",
                    "confidence": "Medium"
                })
        
        # Method 5: Drive scanning (more thorough but slower)
        drive_paths = self._scan_drives()
        for path in drive_paths:
            # Check if we already found this path
            if not any(inst["path"].lower() == path.lower() for inst in installations):
                installations.append({
                    "path": path,
                    "method": "Drive Scan",
                    "platform": "Unknown",
                    "confidence": "Low"
                })
        
        # Sort by confidence (High > Medium > Low)
        confidence_order = {"High": 3, "Medium": 2, "Low": 1}
        installations.sort(key=lambda x: confidence_order.get(x["confidence"], 0), reverse=True)
        
        logger.info(f"Found {len(installations)} game installation(s)")
        for inst in installations:
            logger.info(f"  {inst['path']} ({inst['method']}, {inst['confidence']} confidence)")
        
        return installations
    
    def detect_best_installation(self) -> Optional[str]:
        """Detect the most likely game installation path"""
        installations = self.detect_all_installations()
        
        if installations:
            # Return the highest confidence installation
            best_installation = installations[0]
            logger.info(f"Best installation detected: {best_installation['path']} via {best_installation['method']}")
            return best_installation["path"]
        
        logger.warning("No game installations detected")
        return None
    
    def _detect_from_steam_registry(self) -> List[str]:
        """Detect game path from Steam registry"""
        paths = []
        
        if sys.platform != "win32":
            return paths
        
        try:
            # Try to find Steam installation path
            steam_path = self._get_steam_install_path()
            if not steam_path:
                return paths
            
            # Look for Stalker 2 in Steam's library folders
            library_folders = self._get_steam_library_folders(steam_path)
            
            for library_folder in library_folders:
                # Check for the app in this library
                potential_paths = [
                    os.path.join(library_folder, "steamapps", "common", "S.T.A.L.K.E.R. 2 Heart of Chornobyl"),
                    os.path.join(library_folder, "steamapps", "common", "STALKER 2 Heart of Chornobyl"),
                    os.path.join(library_folder, "steamapps", "common", "Stalker2"),
                ]
                
                for path in potential_paths:
                    if os.path.exists(path):
                        paths.append(path)
                        break
            
            # Also check Steam's appmanifest for the specific app
            for library_folder in library_folders:
                manifest_path = os.path.join(library_folder, "steamapps", f"appmanifest_{self.STEAM_APP_ID}.acf")
                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Parse the installdir from the manifest
                            for line in content.split('\n'):
                                if '"installdir"' in line:
                                    install_dir = line.split('"')[3]
                                    full_path = os.path.join(library_folder, "steamapps", "common", install_dir)
                                    if os.path.exists(full_path) and full_path not in paths:
                                        paths.append(full_path)
                                    break
                    except Exception as e:
                        logger.debug(f"Error reading Steam manifest: {e}")
            
        except Exception as e:
            logger.debug(f"Error detecting from Steam registry: {e}")
        
        return paths
    
    def _get_steam_install_path(self) -> Optional[str]:
        """Get Steam installation path from registry"""
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam") as key:
                steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
                return steam_path
        except:
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam") as key:
                    steam_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    return steam_path
            except:
                pass
        
        return None
    
    def _get_steam_library_folders(self, steam_path: str) -> List[str]:
        """Get all Steam library folders"""
        library_folders = [steam_path]  # Default Steam folder
        
        try:
            # Read libraryfolders.vdf to find additional library locations
            vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
            if os.path.exists(vdf_path):
                with open(vdf_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Simple parsing for library paths
                    lines = content.split('\n')
                    for line in lines:
                        if '"path"' in line:
                            # Extract path from line like: "path"		"D:\\Steam"
                            parts = line.split('"')
                            if len(parts) >= 4:
                                path = parts[3].replace('\\\\', '\\')
                                if os.path.exists(path) and path not in library_folders:
                                    library_folders.append(path)
        except Exception as e:
            logger.debug(f"Error reading Steam library folders: {e}")
        
        return library_folders
    
    def _detect_from_epic_registry(self) -> List[str]:
        """Detect game path from Epic Games Store registry"""
        paths = []
        
        if sys.platform != "win32":
            return paths
        
        try:
            # Epic Games Store registry locations
            epic_keys = [
                r"SOFTWARE\Epic Games\EpicGamesLauncher",
                r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher"
            ]
            
            for key_path in epic_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        app_data_path, _ = winreg.QueryValueEx(key, "AppDataPath")
                        
                        # Look for Stalker 2 installation records
                        manifests_path = os.path.join(app_data_path, "Manifests")
                        if os.path.exists(manifests_path):
                            for manifest_file in os.listdir(manifests_path):
                                if manifest_file.endswith('.item'):
                                    manifest_path = os.path.join(manifests_path, manifest_file)
                                    try:
                                        with open(manifest_path, 'r', encoding='utf-8') as f:
                                            content = f.read()
                                            if 'stalker' in content.lower() and 'chornobyl' in content.lower():
                                                # Try to extract install location
                                                for line in content.split('\n'):
                                                    if '"InstallLocation"' in line:
                                                        install_path = line.split('"')[3]
                                                        if os.path.exists(install_path):
                                                            paths.append(install_path)
                                                        break
                                    except Exception as e:
                                        logger.debug(f"Error reading Epic manifest {manifest_file}: {e}")
                except Exception as e:
                    logger.debug(f"Error accessing Epic registry key {key_path}: {e}")
                    
        except Exception as e:
            logger.debug(f"Error detecting from Epic registry: {e}")
        
        return paths
    
    def _detect_from_gog_registry(self) -> List[str]:
        """Detect game path from GOG registry"""
        paths = []
        
        if sys.platform != "win32":
            return paths
        
        try:
            # GOG registry locations
            gog_keys = [
                r"SOFTWARE\GOG.com\Games",
                r"SOFTWARE\WOW6432Node\GOG.com\Games"
            ]
            
            for key_path in gog_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        # Enumerate all subkeys (game IDs)
                        i = 0
                        while True:
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                subkey_path = f"{key_path}\\{subkey_name}"
                                
                                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey_path) as subkey:
                                    try:
                                        game_name, _ = winreg.QueryValueEx(subkey, "GameName")
                                        if 'stalker' in game_name.lower() and ('chornobyl' in game_name.lower() or 'heart' in game_name.lower()):
                                            path, _ = winreg.QueryValueEx(subkey, "Path")
                                            if os.path.exists(path):
                                                paths.append(path)
                                    except FileNotFoundError:
                                        pass
                                
                                i += 1
                            except OSError:
                                break
                                
                except Exception as e:
                    logger.debug(f"Error accessing GOG registry key {key_path}: {e}")
                            
        except Exception as e:
            logger.debug(f"Error detecting from GOG registry: {e}")
        
        return paths
    
    def _scan_common_paths(self) -> List[str]:
        """Scan common installation paths"""
        paths = []
        
        for common_path in self.COMMON_PATHS:
            if self._validate_game_path(common_path):
                paths.append(common_path)
        
        return paths
    
    def _scan_drives(self, max_drives: int = 8) -> List[str]:
        """Scan available drives for game installations"""
        paths = []
        
        if sys.platform != "win32":
            return paths
        
        # Get available drives
        drives = []
        for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{drive_letter}:\\"
            if os.path.exists(drive_path):
                drives.append(drive_path)
                if len(drives) >= max_drives:  # Limit scanning to avoid excessive time
                    break
        
        # Common folder names to look for
        search_patterns = [
            "Steam\\steamapps\\common\\S.T.A.L.K.E.R. 2*",
            "Epic Games\\S.T.A.L.K.E.R. 2*",
            "GOG Games\\S.T.A.L.K.E.R. 2*",
            "Games\\S.T.A.L.K.E.R. 2*",
            "Program Files\\Steam\\steamapps\\common\\S.T.A.L.K.E.R. 2*",
            "Program Files (x86)\\Steam\\steamapps\\common\\S.T.A.L.K.E.R. 2*",
        ]
        
        for drive in drives:
            for pattern in search_patterns:
                search_path = os.path.join(drive, pattern.replace("*", "Heart of Chornobyl"))
                if self._validate_game_path(search_path):
                    paths.append(search_path)
        
        return paths
    
    def _validate_game_path(self, path: str) -> bool:
        """Validate that a path contains a valid Stalker 2 installation"""
        if not path or not os.path.exists(path):
            return False
        
        path = Path(path)
        
        # Check for game executable
        exe_path = path / self.GAME_EXECUTABLE
        if not exe_path.exists():
            return False
        
        # Check for game data folder
        data_path = path / self.GAME_DATA_FOLDER
        if not data_path.exists():
            return False
        
        # Additional validation - check for some key game files/folders
        key_items = [
            "Engine",  # Unreal Engine folder
            "Stalker2.exe",  # Alternative executable name
        ]
        
        # At least some key items should exist
        found_items = 0
        for item in key_items:
            if (path / item).exists():
                found_items += 1
        
        # We found the main exe and data folder, that's good enough
        logger.debug(f"Validated game path: {path} (found {found_items} additional items)")
        return True
    
    def get_detection_report(self) -> Dict[str, Any]:
        """Get a detailed report of the detection process"""
        installations = self.detect_all_installations()
        
        return {
            "found_installations": len(installations),
            "installations": installations,
            "methods_used": [
                "Steam Registry",
                "Epic Games Registry", 
                "GOG Registry",
                "Common Path Scan",
                "Drive Scan"
            ],
            "best_installation": installations[0]["path"] if installations else None
        }


def is_valid_stalker2_installation(path: str) -> bool:
    """Check if a path contains a valid Stalker 2 installation"""
    detector = GameDetector()
    return detector._validate_game_path(path)


def get_game_info(path: str) -> Dict[str, Any]:
    """Get information about a Stalker 2 installation"""
    if not is_valid_stalker2_installation(path):
        return {"valid": False}
    
    path = Path(path)
    info = {
        "valid": True,
        "path": str(path),
        "executable": str(path / GameDetector.GAME_EXECUTABLE),
        "data_folder": str(path / GameDetector.GAME_DATA_FOLDER),
        "size": 0,
        "files": 0
    }
    
    try:
        # Calculate installation size and file count
        total_size = 0
        total_files = 0
        
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                    total_files += 1
                except (OSError, PermissionError):
                    pass  # Skip files we can't access
        
        info["size"] = total_size
        info["files"] = total_files
        
    except Exception as e:
        logger.debug(f"Error calculating game info for {path}: {e}")
    
    return info


def detect_game_path() -> Optional[str]:
    """Convenience function to detect the best game installation path"""
    detector = GameDetector()
    return detector.detect_best_installation()


def detect_all_game_paths() -> List[Dict[str, Any]]:
    """Convenience function to detect all game installation paths"""
    detector = GameDetector()
    return detector.detect_all_installations()