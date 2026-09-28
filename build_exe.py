"""
Automated PyInstaller Build Script.
Compiles the School Management System into a standalone Windows .exe with CustomTkinter assets.
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def build():
    print("=" * 60)
    print("Building School Management System Standalone Executable (.exe)")
    print("=" * 60)

    # Check if pyinstaller is installed
    if not shutil.which("pyinstaller"):
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Locate customtkinter package path for bundling assets
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent

    dist_dir = BASE_DIR / "dist"
    build_dir = BASE_DIR / "build"

    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "ModernEduComplex_SMS",
        # Include customtkinter theme files
        f"--add-data={ctk_path};customtkinter",
        # Include database schema
        f"--add-data={BASE_DIR / 'database' / 'schema.sql'};database",
        # Include assets (logos, icons, watermarks)
        f"--add-data={BASE_DIR / 'assets'};assets",
        # Application icon (.ico)
        f"--icon={BASE_DIR / 'assets' / 'logo.ico'}",
        # Hidden imports
        "--hidden-import=reportlab",
        "--hidden-import=openpyxl",
        "--hidden-import=bcrypt",
        "--hidden-import=psycopg2",
        "--hidden-import=pymysql",
        "--hidden-import=scipy",
        "--hidden-import=scipy.stats",
        "--hidden-import=numpy",
        "--hidden-import=schedule",
        # Entry point
        str(BASE_DIR / "main.py")
    ]

    print("Executing PyInstaller command:")
    print(" ".join(cmd))
    subprocess.check_call(cmd, cwd=str(BASE_DIR))

    print("\n" + "=" * 60)
    print("BUILD SUCCESSFUL!")
    print(f"Standalone application bundle created at: {dist_dir / 'ModernEduComplex_SMS'}")
    print("=" * 60)

if __name__ == "__main__":
    build()
