"""
Modern Educational Complex - School Management System (SMS)
Online Web Server Launcher.

Usage:
  python run_web.py                 # Starts local & LAN server (0.0.0.0:8000)
  python run_web.py --port 5000     # Runs on custom port
  python run_web.py --public        # Launches instant public internet HTTPS tunnel (via pyngrok)
"""

import sys
import os
import socket
import argparse
import time
from pathlib import Path

# Setup Root Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import db_manager
from database.demo_seeder import seed_demo_environment


def get_lan_ip():
    """Finds the local network IP address of the machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
        return lan_ip
    except Exception:
        return "127.0.0.1"


def print_banner(host: str, port: int, public_url: str = None):
    lan_ip = get_lan_ip()
    print("=" * 70)
    print("  MODERN EDUCATIONAL COMPLEX - SCHOOL MANAGEMENT WEB PORTAL")
    print("=" * 70)
    print(f"  [*] Local Access:    http://localhost:{port}")
    if lan_ip != "127.0.0.1":
        print(f"  [*] Office / Wi-Fi:  http://{lan_ip}:{port}")
    if public_url:
        print(f"  [+] ONLINE INTERNET: {public_url}")
        print("      (School admins can open this link on their mobile or home PC)")
    print("-" * 70)
    try:
        from src.repositories.user_repository import UserRepository
        repo = UserRepository()
        admin_u = repo.get_user_by_username("admin")
        if admin_u and repo.is_default_password(admin_u["id"]):
            print("  [!] SECURITY NOTICE: Default password ('admin123') is currently active.")
            print("      To protect your database before deploying publicly, run:")
            print("         python set_admin.py")
            print("      or click 'Account & Security Settings' inside the Web Portal.")
        else:
            print("  [+] Custom administrator credentials configured and secured.")
    except Exception:
        pass
    print("=" * 70)
    print("  Press CTRL+C to stop the web server.\n")


def run_server(host: str = "0.0.0.0", port: int = 8000, public: bool = False, reload: bool = False):
    """Initializes database and runs the FastAPI web server."""
    # 1. Initialize Relational Database
    print("[*] Initializing Database...")
    db_manager.init_database()

    # 2. Seed Initial Demo Cohort if clean
    seed_demo_environment()

    # 3. Public tunnel if requested
    public_url = None
    if public:
        cf_path = BASE_DIR / "cloudflared.exe"
        if cf_path.exists():
            try:
                import subprocess
                import re
                print("[*] Launching free Cloudflare HTTPS Tunnel (no account required)...")
                cf_proc = subprocess.Popen(
                    [str(cf_path), "tunnel", "--url", f"http://localhost:{port}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                start_time = time.time()
                while time.time() - start_time < 15:
                    line = cf_proc.stdout.readline()
                    if not line:
                        break
                    match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
                    if match:
                        public_url = match.group(0)
                        break
            except Exception as e:
                print(f"[!] Warning: Could not start Cloudflare tunnel: {e}")

        if not public_url:
            try:
                from pyngrok import ngrok
                print("[*] Launching pyngrok tunnel...")
                tunnel = ngrok.connect(port)
                public_url = tunnel.public_url
            except Exception as e:
                print(f"[!] Warning: Could not start public tunnel: {e}")

    print_banner(host, port, public_url)

    # 4. Start Uvicorn Server
    import uvicorn
    uvicorn.run(
        "src.web.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


def main():
    parser = argparse.ArgumentParser(description="Launch Modern Edu Complex SMS Web Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--public", action="store_true", help="Create public internet tunnel via pyngrok")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    args = parser.parse_args()

    run_server(host=args.host, port=args.port, public=args.public, reload=args.reload)


if __name__ == "__main__":
    main()
