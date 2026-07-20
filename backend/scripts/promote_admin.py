#!/usr/bin/env python3
"""
Promote a user to admin role.

Uses a lightweight MongoDB connection (no embedding/LLM imports).

Usage:
    # List all users
    python scripts/promote_admin.py --list

    # Promote by email
    python scripts/promote_admin.py --email user@example.com

    # Promote the first non-admin user
    python scripts/promote_admin.py --first
"""

import argparse
import asyncio
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from pymongo import AsyncMongoClient  # noqa: E402

# Load .env manually to avoid the heavy config import chain.
_ENV_PATH = _BACKEND_ROOT / ".env"
_ENV: dict[str, str] = {}
if _ENV_PATH.exists():
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            _ENV[key.strip()] = value.strip()

MONGODB_URI = _ENV.get("MONGODB_URI", "")
DATABASE_NAME = _ENV.get("DATABASE_NAME", "customer_support_ai")
USERS_COLLECTION = _ENV.get("USERS_COLLECTION", "users")


async def list_users():
    """List all users with their roles."""
    client = AsyncMongoClient(MONGODB_URI)
    try:
        db = client[DATABASE_NAME]
        users = db[USERS_COLLECTION]
        cursor = users.find({}, {"name": 1, "email": 1, "role": 1, "is_active": 1})
        all_users = await cursor.to_list(length=None)

        if not all_users:
            print("No users found. Register an account first.")
            return

        print(f"\n{'Email':<35} {'Name':<20} {'Role':<10} {'Active'}")
        print("-" * 80)
        for u in all_users:
            role_marker = " <- ADMIN" if u["role"] == "admin" else ""
            print(
                f"{u['email']:<35} {u['name']:<20} "
                f"{u['role']:<10} {u['is_active']}{role_marker}"
            )
        print()
    finally:
        await client.close()


async def promote_user(email: str | None = None, first: bool = False):
    """Promote a user to admin."""
    client = AsyncMongoClient(MONGODB_URI)
    try:
        db = client[DATABASE_NAME]
        users = db[USERS_COLLECTION]

        if email:
            user = await users.find_one({"email": email})
            if not user:
                print(f"No user found with email: {email}")
                return False
        elif first:
            user = await users.find_one({"role": {"$ne": "admin"}})
            if not user:
                print("All users are already admins.")
                return False
            email = user["email"]
        else:
            print("Provide --email or --first")
            return False

        if user["role"] == "admin":
            print(f"User '{email}' is already an admin.")
            return True

        result = await users.update_one(
            {"_id": user["_id"]},
            {"$set": {"role": "admin"}},
        )

        if result.modified_count:
            print(f"User '{email}' promoted to admin.")
            print("Log out and log back in for the change to take effect.")
            return True
        else:
            print(f"Failed to promote user '{email}'.")
            return False
    finally:
        await client.close()


async def main():
    parser = argparse.ArgumentParser(description="Manage admin users.")
    parser.add_argument("--list", action="store_true", help="List all users.")
    parser.add_argument("--email", help="Email of user to promote.")
    parser.add_argument(
        "--first", action="store_true", help="Promote the first non-admin user."
    )
    args = parser.parse_args()

    if not args.list and not args.email and not args.first:
        parser.print_help()
        return

    if args.list:
        await list_users()
    else:
        await promote_user(email=args.email, first=args.first)


if __name__ == "__main__":
    asyncio.run(main())
