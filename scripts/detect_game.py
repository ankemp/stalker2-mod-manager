#!/usr/bin/env python3
"""
Stalker 2 Game Detection Utility

This script can be run independently to detect Stalker 2 installations
and provide detailed information about detected game paths.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.game_detection import GameDetector, detect_game_path, detect_all_game_paths, get_game_info


def format_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def main():
    """Main detection utility"""
    print("🎮 Stalker 2: Heart of Chornobyl - Game Detection Utility")
    print("=" * 60)
    
    # Detect all installations
    print("\n🔍 Scanning for game installations...")
    installations = detect_all_game_paths()
    
    if not installations:
        print("❌ No Stalker 2 installations detected.")
        print("\nPossible reasons:")
        print("• Game is not installed")
        print("• Game is installed in a non-standard location")
        print("• Registry entries are missing or corrupted")
        print("\nTry:")
        print("• Installing the game through Steam, Epic Games, or GOG")
        print("• Manually browsing for the game path in the application settings")
        return
    
    print(f"✅ Found {len(installations)} installation(s):")
    print()
    
    # Display detailed information for each installation
    for i, installation in enumerate(installations, 1):
        print(f"📂 Installation #{i}")
        print(f"   Path: {installation['path']}")
        print(f"   Platform: {installation['platform']}")
        print(f"   Detection Method: {installation['method']}")
        print(f"   Confidence: {installation['confidence']}")
        
        # Get detailed game information
        try:
            game_info = get_game_info(installation['path'])
            if game_info['valid']:
                print(f"   Installation Size: {format_size(game_info['size'])}")
                print(f"   Total Files: {game_info['files']:,}")
                print(f"   Executable: {os.path.basename(game_info['executable'])}")
            else:
                print("   ⚠️ Warning: Path validation failed")
        except Exception as e:
            print(f"   ⚠️ Error getting detailed info: {e}")
        
        print()
    
    # Show recommended installation
    best_installation = installations[0]  # Already sorted by confidence
    print("🎯 Recommended Installation:")
    print(f"   {best_installation['path']}")
    print(f"   ({best_installation['platform']} - {best_installation['confidence']} confidence)")
    
    # Show detection report
    detector = GameDetector()
    report = detector.get_detection_report()
    
    print(f"\n📊 Detection Summary:")
    print(f"   Methods Used: {', '.join(report['methods_used'])}")
    print(f"   Total Installations: {report['found_installations']}")

    print("\n" + "=" * 60)
    print("Detection complete! Use the recommended path in your mod manager settings.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDetection cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during detection: {e}")
        print("Please report this issue if it persists.")
        sys.exit(1)