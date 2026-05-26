import firebase_admin
from firebase_admin import credentials, firestore
import sqlite3
import json
import os
from datetime import datetime

# Konfigurasi
CERT_PATH = "firebase_credentials.json"
DB_PATH = "../ezralms.db" # Menggunakan SQLite database yang sudah ada di root

# Inisialisasi Firebase
if not firebase_admin._apps:
    if os.path.exists(CERT_PATH):
        cred = credentials.Certificate(CERT_PATH)
        firebase_admin.initialize_app(cred)
    else:
        print(f"Error: {CERT_PATH} not found.")
        exit(1)

db_firestore = firestore.client()

def sync_collection(collection_name):
    print(f"Syncing collection: {collection_name}...")
    
    # Ambil data dari Firestore
    try:
        docs = db_firestore.collection(collection_name).stream()
        data_list = []
        all_keys = set()
        
        for doc in docs:
            d = doc.to_dict()
            d['firestore_id'] = doc.id
            data_list.append(d)
            all_keys.update(d.keys())

        if not data_list:
            print(f"No data found in {collection_name}")
            return

        # Koneksi ke SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Buat tabel secara dinamis
        # Kita gunakan TEXT untuk semua kolom agar fleksibel, serupa dengan LONGTEXT di MySQL
        columns = []
        for key in all_keys:
            if key == 'firestore_id':
                columns.append(f"`{key}` TEXT PRIMARY KEY")
            else:
                columns.append(f"`{key}` TEXT")
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS `{collection_name}` ({', '.join(columns)})"
        cursor.execute(create_table_sql)
        
        # Masukkan data (Upsert logic menggunakan REPLACE INTO)
        placeholders = ", ".join(["?"] * len(all_keys))
        columns_sql = ", ".join([f"`{key}`" for key in all_keys])
        insert_sql = f"REPLACE INTO `{collection_name}` ({columns_sql}) VALUES ({placeholders})"
        
        count = 0
        for item in data_list:
            values = []
            for key in all_keys:
                val = item.get(key)
                if hasattr(val, "isoformat"): 
                    values.append(val.isoformat())
                elif isinstance(val, (dict, list)):
                    try:
                        values.append(json.dumps(val, default=str))
                    except (TypeError, ValueError):
                        values.append(str(val))
                else:
                    values.append(str(val) if val is not None else None)
            
            cursor.execute(insert_sql, tuple(values))
            count += 1
            
        conn.commit()
        conn.close()
        print(f"Successfully synced {count} records to SQLite table `{collection_name}`.")
        
    except Exception as e:
        print(f"Error syncing {collection_name}: {e}")

if __name__ == "__main__":
    # Mendapatkan semua koleksi secara otomatis
    try:
        collections = db_firestore.collections()
        for coll in collections:
            sync_collection(coll.id)
    except Exception as e:
        print(f"Failed to fetch collections: {e}")
