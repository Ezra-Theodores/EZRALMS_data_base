#!/usr/bin/env python3
"""
EZRA LMS - Firestore to SQLite Sync Script
============================================

Script untuk sinkronisasi data dari Firebase Firestore ke SQLite lokal.
SQLite adalah database file-based (tidak perlu server!)

Cara penggunaan:
    python sync_attendance_sqlite.py
    python sync_attendance_sqlite.py --mode full

"""

import firebase_admin
from firebase_admin import credentials, firestore
import sqlite3
import json
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv
from dateutil import parser as date_parser

# Load environment variables
load_dotenv()

# Constants
DEFAULT_COLLECTION = "attendance"
DEFAULT_SYNC_MODE = "incremental"
LOG_DIR = "logs"
DB_PATH = os.getenv("DB_PATH", "./ezralms.db")


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging with file and console handlers."""
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"sync_{timestamp}.log")

    logger = logging.getLogger("firestore_sync")
    logger.setLevel(getattr(logging, log_level.upper()))
    logger.handlers = []  # Clear existing handlers

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level.upper()))

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


def init_sqlite_db(db_path: str, logger: logging.Logger) -> sqlite3.Connection:
    """Initialize SQLite database with required tables."""
    logger.info(f"Initializing SQLite database: {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Create attendance table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firestore_id TEXT UNIQUE NOT NULL,
            student_id TEXT,
            student_name TEXT,
            class_id TEXT,
            class_name TEXT,
            attendance_date TEXT,
            status TEXT DEFAULT 'present',
            check_in_time TEXT,
            check_out_time TEXT,
            notes TEXT,
            sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
    """)

    # Create indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_firestore_id ON attendance(firestore_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_id ON attendance(student_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_class_id ON attendance(class_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(attendance_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON attendance(status)")

    # Create sync_log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection_name TEXT,
            records_synced INTEGER DEFAULT 0,
            sync_status TEXT DEFAULT 'success',
            error_message TEXT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
        )
    """)

    conn.commit()
    logger.info("SQLite database initialized successfully")
    return conn


def transform_document(doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform Firestore document to SQLite format."""
    result = {
        'firestore_id': doc_id,
        'raw_data': json.dumps(data, default=str)
    }

    # Field mapping
    field_mapping = {
        'student_id': ['student_id', 'studentId', 'id_siswa', 'nis', 'nisn'],
        'student_name': ['student_name', 'studentName', 'nama', 'nama_siswa', 'name'],
        'class_id': ['class_id', 'classId', 'kelas_id', 'id_kelas'],
        'class_name': ['class_name', 'className', 'nama_kelas', 'kelas'],
        'notes': ['notes', 'catatan', 'note', 'keterangan', 'remarks'],
    }

    for target_field, source_fields in field_mapping.items():
        for source in source_fields:
            if source in data and data[source] is not None:
                result[target_field] = str(data[source])
                break

    # Date handling
    date_fields = ['date', 'tanggal', 'attendance_date', 'tgl']
    for field in date_fields:
        if field in data and data[field]:
            try:
                if hasattr(data[field], 'isoformat'):
                    result['attendance_date'] = data[field].strftime('%Y-%m-%d')
                else:
                    dt = date_parser.parse(str(data[field]))
                    result['attendance_date'] = dt.strftime('%Y-%m-%d')
            except:
                pass
            break

    # Status handling
    if 'status' in data and data['status']:
        status = str(data['status']).lower()
        status_map = {
            'hadir': 'present',
            'tidak hadir': 'absent',
            'izin': 'excused',
            'sakit': 'sick',
            'terlambat': 'late'
        }
        result['status'] = status_map.get(status, status)

    # Time handling
    time_fields = [
        ('check_in_time', ['check_in', 'checkin', 'check_in_time', 'waktu_masuk', 'jam_masuk']),
        ('check_out_time', ['check_out', 'checkout', 'check_out_time', 'waktu_keluar', 'jam_keluar'])
    ]

    for target_field, source_fields in time_fields:
        for source in source_fields:
            if source in data and data[source]:
                try:
                    if hasattr(data[source], 'isoformat'):
                        result[target_field] = data[source].strftime('%H:%M:%S')
                    else:
                        result[target_field] = str(data[source])
                except:
                    pass
                break

    return result


def upsert_attendance(conn: sqlite3.Connection, data: Dict[str, Any], logger: logging.Logger) -> Tuple[bool, str]:
    """Insert or update attendance record."""
    try:
        cursor = conn.cursor()

        # Check if record exists
        cursor.execute("SELECT id FROM attendance WHERE firestore_id = ?", (data['firestore_id'],))
        existing = cursor.fetchone()

        if existing:
            # Update
            set_clause = ", ".join([f"{k} = ?" for k in data.keys() if k != 'firestore_id'])
            values = [v for k, v in data.items() if k != 'firestore_id']
            values.append(data['firestore_id'])

            cursor.execute(f"""
                UPDATE attendance
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE firestore_id = ?
            """, values)
            return True, "UPDATED"
        else:
            # Insert
            columns = list(data.keys())
            placeholders = ", ".join(["?"] * len(columns))
            values = [data.get(col) for col in columns]

            cursor.execute(f"""
                INSERT INTO attendance ({', '.join(columns)})
                VALUES ({placeholders})
            """, values)
            return True, "INSERTED"

    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return False, str(e)


def sync_collection(
    db_firestore,
    conn: sqlite3.Connection,
    collection_name: str,
    sync_mode: str,
    logger: logging.Logger
) -> Dict[str, int]:
    """Sync Firestore collection to SQLite."""
    logger.info(f"Starting sync for collection: {collection_name}")

    stats = {'total': 0, 'inserted': 0, 'updated': 0, 'failed': 0}

    try:
        # Get last sync timestamp for incremental sync
        last_sync = None
        if sync_mode == "incremental":
            cursor = conn.cursor()
            cursor.execute("""
                SELECT MAX(sync_timestamp) as last_sync
                FROM attendance
            """)
            row = cursor.fetchone()
            if row and row[0]:
                last_sync = row[0]
                logger.info(f"Last sync: {last_sync}")

        # Query Firestore
        query = db_firestore.collection(collection_name)
        docs = query.stream()

        # Process documents
        for doc in docs:
            stats['total'] += 1
            data = doc.to_dict()

            # Transform data
            transformed = transform_document(doc.id, data)

            # Insert or update
            success, action = upsert_attendance(conn, transformed, logger)

            if success:
                if action == "INSERTED":
                    stats['inserted'] += 1
                elif action == "UPDATED":
                    stats['updated'] += 1
            else:
                stats['failed'] += 1
                logger.error(f"Failed to sync document {doc.id}: {action}")

            # Commit every 100 records
            if stats['total'] % 100 == 0:
                conn.commit()
                logger.info(f"Progress: {stats['total']} records processed")

        # Final commit
        conn.commit()

        # Log results
        logger.info(
            f"Sync completed. Total: {stats['total']}, "
            f"Inserted: {stats['inserted']}, "
            f"Updated: {stats['updated']}, "
            f"Failed: {stats['failed']}"
        )

    except Exception as e:
        conn.rollback()
        logger.error(f"Sync failed: {e}")
        raise

    return stats


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Sync Firestore data to SQLite")
    parser.add_argument("--collection", default="attendance", help="Collection to sync")
    parser.add_argument("--mode", choices=["full", "incremental"], default="incremental")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_level)
    logger.info("=" * 60)
    logger.info("EZRA LMS - Firestore to SQLite Sync")
    logger.info("=" * 60)

    try:
        # Initialize Firebase
        logger.info("Initializing Firebase...")
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        db_firestore = firestore.client()
        logger.info("Firebase initialized successfully")

        # Initialize SQLite database
        logger.info(f"Initializing SQLite database: {DB_PATH}")
        conn = init_sqlite_db(DB_PATH, logger)

        # Run sync
        logger.info(f"Starting sync: collection='{args.collection}', mode='{args.mode}'")
        stats = sync_collection(db_firestore, conn, args.collection, args.mode, logger)

        # Close connection
        conn.close()

        logger.info("=" * 60)
        logger.info("Sync completed successfully!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    sys.exit(main())
