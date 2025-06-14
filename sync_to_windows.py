#!/usr/bin/env python3
"""
Dynamic sync tool for CalorieTracker WSL ↔ Windows development
Supports one-time sync, watching for changes, and selective sync
"""
import os
import shutil
import subprocess
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
WSL_PROJECT_DIR = "/home/niko/projects/CalorieTracker"
WINDOWS_PROJECT_DIR = "/mnt/k/CalorieTracker"

# Files to always watch/sync
WATCH_FILES = [
    "CalorieApp.py",
    "db_handler_orm.py", 
    "db_orm.py",
    "models.py",
    "requirements.txt",
    "templates/*.html",
    "static/css/*.css",
    "static/js/*.js"
]

# Files to exclude
EXCLUDE_PATTERNS = [
    '__pycache__',
    '*.pyc',
    '.git',
    'venv',
    '*.db',
    '.env',
    'node_modules',
    '*.log',
    '.pytest_cache'
]

def ensure_windows_dir():
    """Create Windows directory if it doesn't exist"""
    windows_path = Path(WINDOWS_PROJECT_DIR)
    if not windows_path.exists():
        print(f"📁 Creating Windows directory: {WINDOWS_PROJECT_DIR}")
        windows_path.mkdir(parents=True, exist_ok=True)
    return windows_path

def get_modified_files(since_minutes=None):
    """Get list of recently modified files"""
    modified_files = []
    wsl_path = Path(WSL_PROJECT_DIR)
    
    for pattern in WATCH_FILES:
        if '*' in pattern:
            # Handle glob patterns
            parent_dir = wsl_path / pattern.split('/')[0] if '/' in pattern else wsl_path
            if parent_dir.exists():
                glob_pattern = pattern.split('/')[-1]
                for file_path in parent_dir.glob(glob_pattern):
                    if file_path.is_file():
                        if since_minutes is None:
                            modified_files.append(file_path.relative_to(wsl_path))
                        else:
                            # Check if file was modified recently
                            mtime = file_path.stat().st_mtime
                            now = time.time()
                            if (now - mtime) < (since_minutes * 60):
                                modified_files.append(file_path.relative_to(wsl_path))
        else:
            # Handle specific files
            file_path = wsl_path / pattern
            if file_path.exists():
                if since_minutes is None:
                    modified_files.append(Path(pattern))
                else:
                    mtime = file_path.stat().st_mtime
                    now = time.time()
                    if (now - mtime) < (since_minutes * 60):
                        modified_files.append(Path(pattern))
    
    return modified_files

def sync_files(files_list=None, verbose=True):
    """Sync files from WSL to Windows"""
    if verbose:
        print(f"🔄 Syncing files from WSL to Windows... ({datetime.now().strftime('%H:%M:%S')})")
    
    if files_list is None:
        files_list = get_modified_files()
    
    if not files_list:
        if verbose:
            print("📂 No files to sync")
        return True, []
    
    # Try rsync first for efficiency
    exclude_args = []
    for pattern in EXCLUDE_PATTERNS:
        exclude_args.extend(['--exclude', pattern])
    
    rsync_cmd = [
        'rsync', '-av', '--delete',
        *exclude_args,
        f"{WSL_PROJECT_DIR}/",
        f"{WINDOWS_PROJECT_DIR}/"
    ]
    
    try:
        result = subprocess.run(rsync_cmd, check=True, capture_output=True, text=True)
        # Parse rsync output to get actually synced files
        synced_files = []
        for line in result.stdout.split('\n'):
            # rsync outputs files it's transferring
            if line and not line.endswith('/') and not line.startswith('sending') and not line.startswith('total'):
                clean_line = line.strip()
                if clean_line and '/' in clean_line:
                    synced_files.append(clean_line)
        
        if verbose:
            print(f"✅ Files synced successfully! ({len(synced_files)} files)")
        return True, synced_files
    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"❌ Rsync failed: {e}")
        return basic_copy(files_list, verbose)
    except FileNotFoundError:
        if verbose:
            print("⚠️  rsync not found, using file copy...")
        return basic_copy(files_list, verbose)

def basic_copy(files_list=None, verbose=True):
    """Fallback file copy method"""
    try:
        windows_dir = ensure_windows_dir()
        
        if files_list is None:
            files_list = get_modified_files()
        
        actually_copied = []
        for file_path in files_list:
            src = Path(WSL_PROJECT_DIR) / file_path
            dst = windows_dir / file_path
            
            if src.exists():
                # Check if file actually needs copying (different or doesn't exist)
                needs_copy = True
                if dst.exists():
                    src_mtime = src.stat().st_mtime
                    dst_mtime = dst.stat().st_mtime
                    src_size = src.stat().st_size
                    dst_size = dst.stat().st_size
                    
                    # Only copy if source is newer or size is different
                    needs_copy = src_mtime > dst_mtime or src_size != dst_size
                
                if needs_copy:
                    # Create parent directory if needed
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    actually_copied.append(str(file_path))
                    if verbose:
                        print(f"  ✓ {file_path}")
        
        # Also copy directories that might be new
        for dir_name in ["static", "templates"]:
            src_dir = Path(WSL_PROJECT_DIR) / dir_name
            dst_dir = windows_dir / dir_name
            if src_dir.exists() and not dst_dir.exists():
                shutil.copytree(src_dir, dst_dir)
                actually_copied.append(f"{dir_name}/")
                if verbose:
                    print(f"  ✓ {dir_name}/")
        
        if verbose:
            print(f"✅ Files copied successfully! ({len(actually_copied)} items)")
        return True, actually_copied
        
    except Exception as e:
        if verbose:
            print(f"❌ Copy failed: {e}")
        return False, []

def watch_and_sync(interval=2):
    """Watch for file changes and sync automatically"""
    print(f"👀 Watching for changes... (checking every {interval}s)")
    print("Press Ctrl+C to stop")
    print()
    
    last_check = time.time()
    
    try:
        while True:
            time.sleep(interval)
            
            # Look for files modified in the last interval + 1 second buffer
            check_minutes = (interval + 1) / 60
            modified_files = get_modified_files(since_minutes=check_minutes)
            
            if modified_files:
                print(f"\n📝 Changes detected in {len(modified_files)} files:")
                for file_path in modified_files[:5]:  # Show first 5
                    print(f"   • {file_path}")
                if len(modified_files) > 5:
                    print(f"   ... and {len(modified_files) - 5} more")
                
                success, synced_files = sync_files(modified_files, verbose=False)
                if success:
                    if synced_files:
                        print(f"🔄 Synced {len(synced_files)} files at {datetime.now().strftime('%H:%M:%S')}")
                        # Show first few synced files
                        for file_path in synced_files[:3]:
                            print(f"   • {file_path}")
                        if len(synced_files) > 3:
                            print(f"   ... and {len(synced_files) - 3} more")
                    else:
                        print(f"✅ All files up to date at {datetime.now().strftime('%H:%M:%S')}")
                else:
                    print("❌ Sync failed!")
            
            last_check = time.time()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping file watcher")

def show_status():
    """Show sync status and recent changes"""
    print("📊 CalorieTracker Sync Status")
    print(f"WSL:     {WSL_PROJECT_DIR}")
    print(f"Windows: {WINDOWS_PROJECT_DIR}")
    print()
    
    # Check if Windows directory exists
    if not Path(WINDOWS_PROJECT_DIR).exists():
        print("❌ Windows directory not found!")
        return
    
    # Show recently modified files
    recent_files = get_modified_files(since_minutes=60)  # Last hour
    if recent_files:
        print(f"📝 Recently modified files (last hour): {len(recent_files)}")
        for file_path in recent_files[:10]:
            src_path = Path(WSL_PROJECT_DIR) / file_path
            mtime = datetime.fromtimestamp(src_path.stat().st_mtime)
            print(f"   • {file_path} ({mtime.strftime('%H:%M:%S')})")
        if len(recent_files) > 10:
            print(f"   ... and {len(recent_files) - 10} more")
    else:
        print("📂 No recent changes detected")
    print()

def show_synced_files(synced_files):
    """Show what files were actually synced"""
    if not synced_files:
        print("📂 No files were synced (all up to date)")
        return
    
    print(f"📋 Files synced ({len(synced_files)} total):")
    
    # Group files by type for better readability
    file_groups = {
        'Python Files': [],
        'Templates': [],
        'Stylesheets': [],
        'JavaScript': [],
        'Other': []
    }
    
    for file_path in synced_files:
        if file_path.endswith('.py'):
            file_groups['Python Files'].append(file_path)
        elif file_path.startswith('templates/') or file_path.endswith('.html'):
            file_groups['Templates'].append(file_path)
        elif file_path.startswith('static/css/') or file_path.endswith('.css'):
            file_groups['Stylesheets'].append(file_path)
        elif file_path.startswith('static/js/') or file_path.endswith('.js'):
            file_groups['JavaScript'].append(file_path)
        else:
            file_groups['Other'].append(file_path)
    
    # Display grouped files
    for group_name, files in file_groups.items():
        if files:
            print(f"  {group_name}:")
            for file_path in files[:5]:  # Show max 5 per group
                print(f"    • {file_path}")
            if len(files) > 5:
                print(f"    ... and {len(files) - 5} more {group_name.lower()}")
            print()

def main():
    parser = argparse.ArgumentParser(description='CalorieTracker WSL ↔ Windows Sync Tool')
    parser.add_argument('command', nargs='?', default='sync', 
                       choices=['sync', 'watch', 'status'],
                       help='Command to run (default: sync)')
    parser.add_argument('--interval', '-i', type=int, default=2,
                       help='Watch interval in seconds (default: 2)')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Minimal output')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔄 CalorieTracker WSL ↔ Windows Sync Tool")
        print(f"WSL:     {WSL_PROJECT_DIR}")
        print(f"Windows: {WINDOWS_PROJECT_DIR}")
        print()
    
    # Ensure Windows directory exists
    ensure_windows_dir()
    
    if args.command == 'sync':
        # One-time sync
        success, synced_files = sync_files(verbose=not args.quiet)
        if success:
            if not args.quiet:
                print()
                show_synced_files(synced_files)
                print("🎉 Sync completed successfully!")
                print()
                print("📋 Next steps:")
                print("1. cd K:\\CalorieTracker")
                print("2. python Start.py")
                print("3. Use 192.168.86.25:5000 from mobile!")
                print()
                print("💡 Tip: Use 'python3 sync_to_windows.py watch' for auto-sync")
        else:
            print("❌ Sync failed")
    
    elif args.command == 'watch':
        # Watch for changes and auto-sync
        if not args.quiet:
            print("🚀 Starting automatic sync mode...")
            print("   Make changes in WSL, they'll auto-sync to Windows!")
            print()
        watch_and_sync(args.interval)
    
    elif args.command == 'status':
        # Show status
        show_status()

if __name__ == "__main__":
    main()