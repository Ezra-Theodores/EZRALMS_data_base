#!/usr/bin/env python3
"""
EZRA LMS - Firestore to MySQL Sync Script
==========================================

Script untuk sinkronisasi data attendance dari Firebase Firestore ke MySQL lokal.

Cara penggunaan:
    python sync_attendance.py
    python sync_attendance.py --collection attendance --mode full
    python sync_attendance.py --help

Fitur:
    - Sinkronisasi full (truncate dan insert ulang)
    - Sinkronisasi incremental (hanya data baru/updated)
    - Auto-create schema jika belum ada
    - Logging ke file dan console
"""

import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
from mysql.connector import errorcode
import json
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Load environment variables
from dotenv import load_dotenv

# Konstanta
DEFAULT_COLLECTION = "attendance"
DEFAULT_SYNC_MODE = "incremental"  # atau "full"
LOG_DIR = "logs"

# Setup logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup logging dengan file handler dan console handler."""
    os.makedirs(LOG_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"sync_{timestamp}.log")

    logger = logging.getLogger("firestore_sync")
    logger.setLevel(getattr(logging, log_level.upper()))

    # File handler
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, log_level.upper()))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


class DatabaseManager:
    """Manager untuk koneksi dan operasi database MySQL."""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.connection = None
        self.cursor = None

    def connect(self, database: Optional[str] = None) -> 'DatabaseManager':
        """Membuat koneksi ke Database (MySQL atau SQLite)."""
        db_type = os.getenv('DB_TYPE', 'mysql').lower()
        
        if db_type == 'sqlite':
            db_path = os.getenv('DB_PATH', './ezralms.db')
            try:
                import sqlite3
                self.connection = sqlite3.connect(db_path)
                self.connection.row_factory = sqlite3.Row
                self.cursor = self.connection.cursor()
                self.logger.info(f"Connected to SQLite (File: {db_path})")
                return self
            except Exception as e:
                self.logger.error(f"SQLite Error: {e}")
                raise
        
        # MySQL logic
        try:
            config = self.config.copy()
            if database:
                config['database'] = database

            self.connection = mysql.connector.connect(**config)
            self.cursor = self.connection.cursor(dictionary=True)
            self.logger.debug(f"Connected to MySQL (DB: {database or 'none'})")
            return self

        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                self.logger.error("Access denied - check username/password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                self.logger.warning(f"Database does not exist: {database}")
            else:
                self.logger.error(f"MySQL Error: {err}")
            raise

    def create_database(self, db_name: str) -> None:
        """Membuat database jika belum ada (Hanya untuk MySQL)."""
        db_type = os.getenv('DB_TYPE', 'mysql').lower()
        if db_type == 'sqlite':
            return # SQLite creates file automatically on connect
            
        try:
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} ")
            self.cursor.execute(f"ALTER DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.logger.info(f"Database '{db_name}' created/verified")
        except Exception as err:
            self.logger.error(f"Failed to create database: {err}")
            raise

    def create_attendance_table(self, table_name: str = "attendance") -> None:
        """Membuat tabel attendance dengan schema yang terstruktur."""
        db_type = os.getenv('DB_TYPE', 'mysql').lower()
        
        if db_type == 'sqlite':
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
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
            """
        else:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                firestore_id VARCHAR(255) UNIQUE NOT NULL,
                student_id VARCHAR(255),
                student_name VARCHAR(255),
                class_id VARCHAR(255),
                class_name VARCHAR(255),
                attendance_date DATE,
                status ENUM('present', 'absent', 'late', 'excused', 'sick') DEFAULT 'present',
                check_in_time TIME,
                check_out_time TIME,
                notes TEXT,
                sync_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                raw_data JSON,
                INDEX idx_firestore_id (firestore_id),
                INDEX idx_student_id (student_id),
                INDEX idx_class_id (class_id),
                INDEX idx_attendance_date (attendance_date),
                INDEX idx_status (status),
                INDEX idx_sync_timestamp (sync_timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            
        try:
            if db_type == 'sqlite':
                # Split statements for sqlite if multiple
                for stmt in create_table_sql.split(';'):
                    if stmt.strip():
                        self.cursor.execute(stmt)
            else:
                self.cursor.execute(create_table_sql)
            self.logger.info(f"Table '{table_name}' created/verified")
        except Exception as err:
            self.logger.error(f"Failed to create table: {err}")
            raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
    def insert_or_update_attendance(
        self,
        table_name: str,
        data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Insert atau update data attendance (upsert)."""
        db_type = os.getenv('DB_TYPE', 'mysql').lower()
        
        try:
            columns = list(data.keys())
            
            if db_type == 'sqlite':
                placeholders = ", ".join(["?"] * len(columns))
                sql = f"REPLACE INTO `{table_name}` ({', '.join(columns)}) VALUES ({placeholders})"
                values = tuple(data[col] for col in columns)
                self.cursor.execute(sql, values)
                return True, "INSERTED/UPDATED"
            else:
                placeholders = ["%s"] * len(columns)
                update_columns = [col for col in columns if col != 'firestore_id']
                update_clause = ", ".join([f"{col}=VALUES({col})" for col in update_columns])

                sql = f"""
                    INSERT INTO `{table_name}` ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                    ON DUPLICATE KEY UPDATE {update_clause}, updated_at = CURRENT_TIMESTAMP
                """
                values = tuple(data[col] for col in columns)
                self.cursor.execute(sql, values)

                affected = self.cursor.rowcount
                if affected == 1:
                    return True, "INSERTED"
                elif affected == 2:
                    return True, "UPDATED"
                else:
                    return True, "UNCHANGED"

        except Exception as err:
            self.logger.error(f"Database error: {err}")
            return False, str(err)

    def get_last_sync_timestamp(self, table_name: str) -> Optional[datetime]:
        """Mendapatkan timestamp sync terakhir."""
        try:
            self.cursor.execute(f"SELECT MAX(sync_timestamp) as last_sync FROM {table_name}")
            result = self.cursor.fetchone()
            if result:
                # Handle both dict (MySQL) and Row/Tuple (SQLite)
                val = result['last_sync'] if isinstance(result, (dict, sqlite3.Row)) else result[0]
                return val if val else None
            return None
        except Exception:
            return None

    def commit(self) -> None:
        """Commit transaksi."""
        if self.connection:
            self.connection.commit()

    def rollback(self) -> None:
        """Rollback transaksi."""
        if self.connection:
            self.connection.rollback()

    def close(self) -> None:
        """Menutup koneksi database."""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            self.logger.debug("Database connection closed")


class FirestoreSync:
    """Main class untuk sinkronisasi Firestore ke MySQL."""

    def __init__(
        self,
        db_manager: DatabaseManager,
        logger: logging.Logger,
        sync_mode: str = "incremental"
    ):
        self.db = db_manager
        self.logger = logger
        self.sync_mode = sync_mode
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'failed': 0,
            'total': 0
        }

    def transform_document(self, doc_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform dokumen Firestore ke format tabel MySQL."""
        result = {
            'firestore_id': doc_id,
            'raw_data': json.dumps(data, default=str)
        }

        # Mapping field umum
        field_mapping = {
            'student_id': ['student_id', 'studentId', 'id_siswa', 'nis', 'nisn'],
            'student_name': ['student_name', 'studentName', 'nama', 'nama_siswa', 'name'],
            'class_id': ['class_id', 'classId', 'kelas_id', 'id_kelas'],
            'class_name': ['class_name', 'className', 'nama_kelas', 'kelas'],
            'notes': ['notes', 'catatan', 'note', 'keterangan', 'remarks'],
        }

        for target_field, source_fields in field_mapping.items():
            for source in source_fields:
                if source in data:
                    result[target_field] = str(data[source]) if data[source] is not None else None
                    break

        # Tangani tanggal
        date_fields = ['date', 'tanggal', 'attendance_date', 'tgl']
        for field in date_fields:
            if field in data and data[field]:
                try:
                    if hasattr(data[field], 'isoformat'):
                        result['attendance_date'] = data[field].strftime('%Y-%m-%d')
                    else:
                        result['attendance_date'] = str(data[field])
                except (ValueError, AttributeError, TypeError):
                    pass
                break

        # Tangani status
        if 'status' in data:
            status = str(data['status']).lower()
            valid_statuses = ['present', 'absent', 'late', 'excused', 'sick', 'hadir', 'tidak hadir', 'izin', 'sakit', 'terlambat']
            if status in valid_statuses:
                status_map = {
                    'hadir': 'present',
                    'tidak hadir': 'absent',
                    'izin': 'excused',
                    'sakit': 'sick',
                    'terlambat': 'late'
                }
                result['status'] = status_map.get(status, status)
            else:
                result['status'] = status

        # Tangani waktu check-in/check-out
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

    def sync_collection(self, collection_name: str) -> None:
        """Sinkronisasi satu koleksi Firestore."""
        self.logger.info(f"Starting sync for collection: {collection_name}")

        try:
            # Ambil timestamp terakhir untuk sync incremental
            last_sync = None
            if self.sync_mode == "incremental":
                last_sync = self.db.get_last_sync_timestamp(collection_name)
                if last_sync:
                    self.logger.info(f"Last sync: {last_sync}")

            # Query Firestore
            query = db_firestore.collection(collection_name)
            if last_sync and self.sync_mode == "incremental":
                # Filter dokumen yang diupdate setelah last_sync
                query = query.where('updatedAt', '>', last_sync)

            docs = query.stream()

            # Reset stats
            self.stats = {'inserted': 0, 'updated': 0, 'failed': 0, 'total': 0}

            # Proses setiap dokumen
            for doc in docs:
                self.stats['total'] += 1
                data = doc.to_dict()

                # Transform data
                transformed = self.transform_document(doc.id, data)

                # Insert atau update
                success, action = self.db.insert_or_update_attendance(
                    collection_name,
                    transformed
                )

                if success:
                    if action == "INSERTED":
                        self.stats['inserted'] += 1
                    elif action == "UPDATED":
                        self.stats['updated'] += 1
                else:
                    self.stats['failed'] += 1
                    self.logger.error(f"Failed to sync document {doc.id}: {action}")

                # Commit setiap 100 records untuk menghindari transaksi terlalu besar
                if self.stats['total'] % 100 == 0:
                    self.db.commit()
                    self.logger.info(f"Progress: {self.stats['total']} records processed")

            # Final commit
            self.db.commit()

            # Log results
            self.logger.info(
                f"Sync completed for {collection_name}. "
                f"Total: {self.stats['total']}, "
                f"Inserted: {self.stats['inserted']}, "
                f"Updated: {self.stats['updated']}, "
                f"Failed: {self.stats['failed']}"
            )

        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Sync failed for collection {collection_name}: {e}")
            raise


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Sync Firestore data to MySQL"
    )
    parser.add_argument(
        "--collection",
        default=os.getenv("SYNC_COLLECTION", "attendance"),
        help="Firestore collection to sync (default: attendance)"
    )
    parser.add_argument(
        "--mode",
        choices=["full", "incremental"],
        default=os.getenv("SYNC_MODE", "incremental"),
        help="Sync mode: full (truncate+insert) or incremental (update only)"
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    return parser.parse_args()


def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_credentials.json")

    if not os.path.exists(cred_path):
        raise FileNotFoundError(f"Firebase credentials file not found: {cred_path}")

    if not firebase_admin._apps:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)

    return firestore.client()


def main():
    """Main entry point."""
    # Load environment variables
    load_dotenv()

    # Parse arguments
    args = parse_arguments()

    # Setup logging
    logger = setup_logging(args.log_level)
    logger.info("=" * 60)
    logger.info("EZRA LMS - Firestore to MySQL Sync")
    logger.info("=" * 60)

    try:
        # Initialize Firebase
        logger.info("Initializing Firebase...")
        global db_firestore
        db_firestore = initialize_firebase()
        logger.info("Firebase initialized successfully")

        # MySQL configuration
        mysql_config = {
            'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'port': int(os.getenv('MYSQL_PORT', 3306))
        }
        db_name = os.getenv('MYSQL_DATABASE', 'ezralms_db')

        # Initialize database
        logger.info("Setting up MySQL database...")
        with DatabaseManager(mysql_config, logger) as db:
            db.connect()
            db.create_database(db_name)
            db.connect(db_name)
            db.create_attendance_table(args.collection)

        # Run sync
        logger.info(f"Starting sync: collection='{args.collection}', mode='{args.mode}'")
        with DatabaseManager(mysql_config, logger) as db:
            db.connect(db_name)
            syncer = FirestoreSync(db, logger, args.mode)
            syncer.sync_collection(args.collection)

        logger.info("Sync completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Sync failed: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main()
