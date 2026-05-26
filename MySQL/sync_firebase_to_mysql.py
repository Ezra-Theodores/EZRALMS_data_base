import firebase_admin
from firebase_admin import credentials, firestore
import mysql.connector
from mysql.connector import errorcode
import json

# Konfigurasi
CERT_PATH = "firebase_credentials.json"
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
}
DB_NAME = 'firebase_sync'

# Inisialisasi Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(CERT_PATH)
    firebase_admin.initialize_app(cred)

db_firestore = firestore.client()

def sync_collection(collection_name):
    print(f"Syncing collection: {collection_name}...")
    
    # Ambil data dari Firestore
    docs = db_firestore.collection(collection_name).stream()
    data_list = []
    all_keys = set()
    
    for doc in docs:
        d = doc.to_dict()
        d['firestore_id'] = doc.id # Tambahkan ID dokumen sebagai kolom
        data_list.append(d)
        all_keys.update(d.keys())

    if not data_list:
        print(f"No data found in {collection_name}")
        return

    # Koneksi ke MySQL
    try:
        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = cnx.cursor()
        
        # Buat database jika belum ada
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")
        
        # Buat tabel secara dinamis (semua kolom dianggap TEXT/JSON untuk kemudahan awal)
        columns = []
        for key in all_keys:
            columns.append(f"`{key}` LONGTEXT")
        
        create_table_sql = f"CREATE TABLE IF NOT EXISTS `{collection_name}` ({', '.join(columns)})"
        cursor.execute(create_table_sql)
        
        # Kosongkan tabel sebelum sync (opsional, tergantung kebutuhan)
        cursor.execute(f"TRUNCATE TABLE `{collection_name}`")
        
        # Masukkan data
        placeholders = ", ".join(["%s"] * len(all_keys))
        columns_sql = ", ".join([f"`{key}`" for key in all_keys])
        insert_sql = f"INSERT INTO `{collection_name}` ({columns_sql}) VALUES ({placeholders})"
        
        for item in data_list:
            values = []
            for key in all_keys:
                val = item.get(key)
                if hasattr(val, "isoformat"): # Menangani Datetime/Timestamp
                    values.append(val.isoformat())
                elif isinstance(val, (dict, list)):
                    try:
                        values.append(json.dumps(val, default=str))
                    except:
                        values.append(str(val))
                else:
                    values.append(str(val) if val is not None else None)
            cursor.execute(insert_sql, tuple(values))
            
        cnx.commit()
        print(f"Successfully synced {len(data_list)} records to MySQL table `{collection_name}`.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    # Mendapatkan semua koleksi secara otomatis
    collections = db_firestore.collections()
    for coll in collections:
        try:
            sync_collection(coll.id)
        except Exception as e:
            print(f"Failed to sync {coll.id}: {e}")

