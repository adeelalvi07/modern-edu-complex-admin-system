"""
Modern Educational Complex - School Management System (SMS)
Production Application Launcher.
"""
import sys
import logging
from pathlib import Path

# Setup Root Path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import db_manager
from database.demo_seeder import seed_demo_environment

def setup_logging():
    log_file = BASE_DIR / "logs" / "application.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] (%(name)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    logging.getLogger("").addHandler(console)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Modern Educational Complex SMS")
    parser.add_argument("--web", action="store_true", help="Launch online web portal instead of desktop GUI")
    parser.add_argument("--port", type=int, default=8000, help="Web portal port (default: 8000)")
    parser.add_argument("--host", default="0.0.0.0", help="Web portal host bind (default: 0.0.0.0)")
    parser.add_argument("--public", action="store_true", help="Create public internet HTTPS tunnel")
    args, unknown = parser.parse_known_args()

    setup_logging()
    logging.info("Starting Modern Educational Complex SMS...")

    # 1. Initialize Relational Database
    db_manager.init_database()

    # 2. Seed Initial Demo Cohort (PG through Class 10)
    seed_demo_environment()

    if args.web:
        # Launch Web Server
        from run_web import run_server
        run_server(host=args.host, port=args.port, public=args.public)
        return

    # Print tip for web access
    print("\n" + "=" * 65)
    print("  [ONLINE WEB ACCESS READY]")
    print("  To access this system as a website on mobile, laptops, or remote:")
    print("  Run: python run_web.py (or python main.py --web)")
    print("=" * 65 + "\n")

    # 3. Launch CustomTkinter Desktop GUI
    from src.views.app_window import SchoolAppWindow
    app = SchoolAppWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
