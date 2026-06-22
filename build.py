"""
Build script to package the WoW Font Replacer application into a standalone .exe
using PyInstaller.
"""

import os
import sys
import subprocess
import shutil

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Download pre-packaged fonts
    print("--- 1. Checking pre-packaged fonts ---")
    download_script = os.path.join(base_dir, "download_fonts.py")
    try:
        subprocess.check_call([sys.executable, download_script])
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to run download_fonts.py: {e}")
        sys.exit(1)
        
    # 2. Check for PyInstaller
    print("\n--- 2. Checking PyInstaller installation ---")
    try:
        import PyInstaller
        print("[OK] PyInstaller is already installed.")
    except ImportError:
        print("PyInstaller not found. Installing via pip...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller>=6.0.0"])
            print("[OK] PyInstaller installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to install PyInstaller: {e}")
            sys.exit(1)

    # 3. Clean previous build artifacts
    print("\n--- 3. Cleaning previous build artifacts ---")
    for folder in ["build", "dist"]:
        path = os.path.join(base_dir, folder)
        if os.path.exists(path):
            print(f"Removing {folder}...")
            shutil.rmtree(path)
            
    spec_file = os.path.join(base_dir, "WoWFontReplacer.spec")
    if os.path.exists(spec_file):
        os.remove(spec_file)
        
    # 4. Run PyInstaller
    print("\n--- 4. Compiling application ---")
    
    # We specify os.pathsep (';' on Windows, ':' on Unix)
    # The --add-data argument format is "source_dir;dest_dir" on Windows
    add_data_arg = f"fonts{os.pathsep}fonts"
    
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--add-data", add_data_arg,
        "--name", "WoWFontReplacer",
        "main.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\n[OK] Package build succeeded!")
        
        exe_path = os.path.join(base_dir, "dist", "WoWFontReplacer.exe")
        if os.path.exists(exe_path):
            print(f"[OK] Standalone executable is available at:\n{exe_path}")
        else:
            print("[WARNING] Build reported success, but WoWFontReplacer.exe was not found in dist/.")
            
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] PyInstaller compilation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
