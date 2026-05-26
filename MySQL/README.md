# Workflow SQLite - Firebase EzraLMS

Folder ini berisi script otomatis untuk mensinkronisasi data dari **Google Firebase (Firestore)** ke database **SQLite** lokal (`ezralms.db`).

## Isi Folder
1. `sync_firebase_to_sqlite.py`: Script utama untuk menarik semua koleksi Firestore ke SQLite.
2. `server.js`: Server Node.js untuk melihat data dan RAG (sekarang menggunakan data asli dari SQLite).
3. `firebase_credentials.json`: File kunci (Service Account) untuk akses ke Firebase.

## Persiapan
Pastikan library yang dibutuhkan sudah terinstal:
```bash
pip install firebase-admin python-dotenv
```
Untuk server Node.js:
```bash
npm install sqlite3
```

## Cara Menjalankan Sinkronisasi
1. Masuk ke folder ini melalui terminal:
   ```powershell
   cd "C:\Users\Admin\Repo\EZRALMS_data_base\MySQL"
   ```
2. Jalankan script:
   ```powershell
   python sync_firebase_to_sqlite.py
   ```

## Detail Database SQLite
- **Path:** `../ezralms.db`
- **Tables:** Nama tabel sesuai dengan nama koleksi di Firestore.

Data disimpan dalam format teks agar kompatibel dengan berbagai skema Firestore yang fleksibel.

---
*Diupdate otomatis untuk migrasi SQLite pada 10 Mei 2026.*
