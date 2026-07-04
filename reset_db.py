"""
Run this script to completely reset the database and re-run migrations.
USE THIS ONLY IN DEVELOPMENT — it deletes all data.

Usage:
    python reset_db.py
"""
import subprocess
import sys
import os

DB_NAME = "as3_db"
DB_USER = "postgres"

print(f"⚠️  This will DROP and RECREATE the '{DB_NAME}' database.")
confirm = input("Type 'yes' to continue: ").strip()
if confirm != "yes":
    print("Aborted.")
    sys.exit(0)

print(f"\n1. Dropping database '{DB_NAME}'...")
result = subprocess.run(
    ["psql", "-U", DB_USER, "-c", f"DROP DATABASE IF EXISTS {DB_NAME};"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"   Error: {result.stderr}")
    sys.exit(1)
print("   ✅ Dropped")

print(f"\n2. Creating database '{DB_NAME}'...")
result = subprocess.run(
    ["psql", "-U", DB_USER, "-c", f"CREATE DATABASE {DB_NAME};"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"   Error: {result.stderr}")
    sys.exit(1)
print("   ✅ Created")

print("\n3. Running Alembic migrations...")
result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(f"   Error: {result.stderr}")
    sys.exit(1)
print("   ✅ Migrations complete")

print("\n✅ Database reset complete!")
print("   Demo accounts ready:")
print("   Mobile: 9876543210 / 8765432109 / 7654321098")
print("   Password: demo1234")
