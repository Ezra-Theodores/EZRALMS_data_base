#!/usr/bin/env python3
"""
EZRA LMS - Setup Script
=======================

Script untuk setup awal proyek:
1. Install dependencies
2. Test koneksi
3. Setup database

Usage:
    python setup.py
"""

import os
import sys
import subprocess
import argparse


def run_command(command, description):
    """Menjalankan command dan menampilkan hasil."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print()

    result = subprocess.run(command, shell=True)
    return result.returncode == 0


def install_dependencies():
    """Install Python dependencies."""
    print("Installing dependencies...")

    commands = [
        ("python -m pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing requirements"),
    ]

    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print(f"ERROR: {desc} failed")
            return False

    return True


def test_connections():
    """Test koneksi ke Firebase dan MySQL."""
    print("\nTesting connections...")

    if not run_command("python test_connection.py", "Testing Connections"):
        print("WARNING: Some connections failed")
        return False

    return True


def setup_database():
    """Setup database dan tabel."""
    print("\nSetting up database...")

    # Run sync script to create schema
    if not run_command(
        "python sync_attendance.py --mode full",
        "Creating database schema"
    ):
        print("WARNING: Database setup may have issues")
        return False

    return True


def create_directories():
    """Buat direktori yang diperlukan."""
    print("\nCreating directories...")

    directories = ['logs', 'backups']

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created: {directory}/")

    return True


def main():
    """Main function."""
    print("=" * 60)
    print("EZRA LMS - Setup Script")
    print("=" * 60)

    parser = argparse.ArgumentParser(description="Setup EZRA LMS sync")
    parser.add_argument(
        "--skip-deps",
        action="store_true",
        help="Skip installing dependencies"
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip database setup"
    )
    args = parser.parse_args()

    success = True

    # Step 1: Install dependencies
    if not args.skip_deps:
        success = install_dependencies() and success
    else:
        print("\nSkipping dependency installation")

    # Step 2: Create directories
    success = create_directories() and success

    # Step 3: Test connections
    success = test_connections() and success

    # Step 4: Setup database
    if not args.skip_db:
        success = setup_database() and success
    else:
        print("\nSkipping database setup")

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)

    if success:
        print("✓ Setup completed successfully!")
        print("\nNext steps:")
        print("  1. Review the configuration in .env file")
        print("  2. Run sync: python sync_attendance.py")
        print("  3. Schedule regular sync using Task Scheduler (Windows)")
        return 0
    else:
        print("✗ Setup completed with warnings/errors")
        print("\nPlease review the errors above and fix any issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
