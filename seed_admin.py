"""
One-time script to create the single admin user.

There is no public registration endpoint by design — this is the only way
a User row gets created. Run it once against whichever database DATABASE_URL
points at (local SQLite by default, or set DATABASE_URL to hit Railway's
Postgres directly for prod).

Usage:
    ADMIN_USERNAME=aleksei ADMIN_PASSWORD='choose-a-real-one' python seed_admin.py

Safe to re-run: if the username already exists, it updates the password
instead of creating a duplicate.
"""
import os
import sys

from auth import hash_password
from database import Base, SessionLocal, engine
import models


def main() -> None:
    username = os.getenv("ADMIN_USERNAME")
    password = os.getenv("ADMIN_PASSWORD")

    if not username or not password:
        print(
            "Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables before running.\n"
            "Example: ADMIN_USERNAME=aleksei ADMIN_PASSWORD='choose-a-real-one' python seed_admin.py",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(password) < 8:
        print("ADMIN_PASSWORD must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(models.User).filter(models.User.username == username).first()
        if existing:
            existing.hashed_password = hash_password(password)
            db.commit()
            print(f"Updated password for existing user '{username}'.")
        else:
            user = models.User(username=username, hashed_password=hash_password(password))
            db.add(user)
            db.commit()
            print(f"Created admin user '{username}'.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
