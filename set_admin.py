"""
Modern Educational Complex - School Management System (SMS)
Administrative Credentials & Security Configuration CLI.

Use this script before or after deployment to securely set or reset
the administrator credentials directly from the command line.

Usage:
  python set_admin.py
  python set_admin.py --username myadmin --password "MyStrongPass#2026"
"""

import sys
import getpass
import argparse
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from database.connection import db_manager
from src.repositories.user_repository import UserRepository


def main():
    parser = argparse.ArgumentParser(description="Securely configure Admin credentials for School SMS.")
    parser.add_argument("--username", help="New or existing administrator username")
    parser.add_argument("--password", help="New strong password (min 8 chars, 1 uppercase, 1 digit)")
    parser.add_argument("--name", default="System Administrator", help="Display full name")
    parser.add_argument("--email", default="admin@modernedu.edu.pk", help="Admin email address")
    args = parser.parse_args()

    # Initialize database if needed
    db_manager.init_database()
    repo = UserRepository()

    print("\n" + "=" * 65)
    print("  MODERN EDUCATIONAL COMPLEX - ADMIN SECURITY CONFIGURATION")
    print("=" * 65)

    username = args.username
    if not username:
        default_user = "admin"
        val = input(f"Enter admin username [{default_user}]: ").strip()
        username = val if val else default_user

    password = args.password
    if not password:
        while True:
            p1 = getpass.getpass("Enter new strong password: ")
            p2 = getpass.getpass("Confirm new password:      ")
            if p1 != p2:
                print("[-] Passwords do not match. Please try again.\n")
                continue
            valid, err = repo.validate_password_strength(p1)
            if not valid:
                print(f"[-] Weak password: {err}\n")
                continue
            password = p1
            break
    else:
        valid, err = repo.validate_password_strength(password)
        if not valid:
            print(f"[-] Error: Weak password: {err}")
            sys.exit(1)

    # Check if admin user exists
    existing = db_manager.fetch_one("SELECT id, username FROM users WHERE username = :u", {"u": username})
    if not existing:
        # Fallback to checking the first admin account
        admin_acc = db_manager.fetch_one(
            "SELECT u.id, u.username FROM users u JOIN roles r ON u.role_id = r.id WHERE r.name = 'Admin' ORDER BY u.id ASC"
        )
        if admin_acc:
            user_id = admin_acc["id"]
            repo.update_profile(user_id=user_id, username=username, full_name=args.name, email=args.email)
            existing = {"id": user_id, "username": username}

    if existing:
        user_id = existing["id"]
        success, msg = repo.force_update_password(user_id, password)
        if success:
            repo.update_profile(user_id=user_id, username=username, full_name=args.name, email=args.email)
            print(f"\n[+] SUCCESS: Administrator credentials updated successfully!")
            print(f"    Username: {username}")
            print(f"    Password: [PROTECTED]")
            print(f"    Account ID: {user_id}")
            print("\n[!] The default password warning will no longer appear.")
        else:
            print(f"\n[-] Failed to update password: {msg}")
            sys.exit(1)
    else:
        # Create fresh admin user
        import bcrypt
        admin_role = db_manager.fetch_one("SELECT id FROM roles WHERE name = 'Admin'")
        role_id = admin_role["id"] if admin_role else 1
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        db_manager.execute_query(
            """INSERT INTO users (username, password_hash, full_name, email, role_id)
               VALUES (:u, :p, :fn, :em, :rid)""",
            {
                "u": username,
                "p": hashed,
                "fn": args.name,
                "em": args.email,
                "rid": role_id
            }
        )
        print(f"\n[+] SUCCESS: New administrator account created successfully!")
        print(f"    Username: {username}")

    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
