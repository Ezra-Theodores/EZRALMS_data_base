# EZRA LMS - Firestore to MySQL Sync

Proyek untuk sinkronisasi data dari Firebase Firestore (project: `threebody-933be`) ke database MySQL lokal.

## 📁 Struktur File

```
EZRALMS_data_base/
├── .env                          # Konfigurasi environment (kredensial)
├── .env.example                  # Template konfigurasi
├── .gitignore                    # File yang di-exclude dari git
├── firebase_credentials.json     # Kredensial Firebase Service Account
├── mysql_schema.sql              # Schema database MySQL
├── README.md                     # Dokumentasi ini
├── requirements.txt              # Dependency Python
├── sync_attendance.py            # Script sinkronisasi utama (baru)
├── sync_firebase_to_mysql.py     # Script sinkronisasi lama
└── test_connection.py            # Script test koneksi
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Konfigurasi Environment

Copy file `.env.example` ke `.env` dan sesuaikan:

```bash
cp .env.example .env
```

Edit file `.env`:

```env
# MySQL Configuration
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ezralms_db
MYSQL_PORT=3306

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json

# Sync Configuration
SYNC_MODE=incremental
LOG_LEVEL=INFO
```

### 3. Test Koneksi

```bash
python test_connection.py
```

Output yang diharapkan:
```
EZRA LMS - Connection Test
============================================================
Time: 2024-01-01 12:00:00

============================================================
Testing Firebase Connection
============================================================
  Credentials file: firebase_credentials.json
  Connecting to Firestore...
  SUCCESS! Found X collections:
    - attendance
    ...

============================================================
Testing MySQL Connection
============================================================
  Host: 127.0.0.1:3306
  User: root
  Database: ezralms_db

  Connecting to MySQL server...
  SUCCESS! MySQL version: 8.0.x
  ...

Summary
============================================================
  Firebase Firestore: ✓ CONNECTED
  MySQL Database:     ✓ CONNECTED

✓ All connections successful! You're ready to sync.
  Run: python sync_attendance.py
```

### 4. Jalankan Sinkronisasi

#### Mode Incremental (default) - Hanya data baru/berubah:
```bash
python sync_attendance.py
```

#### Mode Full - Hapus semua data dan insert ulang:
```bash
python sync_attendance.py --mode full
```

#### Sinkronisasi collection tertentu:
```bash
python sync_attendance.py --collection students
```

## 📊 Struktur Database MySQL

### Tabel `attendance`

| Field | Type | Description |
|-------|------|-------------|
| `id` | INT (PK) | ID auto-increment |
| `firestore_id` | VARCHAR(255) | ID dokumen Firestore |
| `student_id` | VARCHAR(255) | ID siswa |
| `student_name` | VARCHAR(255) | Nama siswa |
| `class_id` | VARCHAR(255) | ID kelas |
| `class_name` | VARCHAR(255) | Nama kelas |
| `attendance_date` | DATE | Tanggal kehadiran |
| `status` | ENUM | present/absent/late/excused/sick |
| `check_in_time` | TIME | Waktu masuk |
| `check_out_time` | TIME | Waktu keluar |
| `notes` | TEXT | Catatan |
| `raw_data` | JSON | Data lengkap Firestore |
| `created_at` | TIMESTAMP | Waktu dibuat |
| `updated_at` | TIMESTAMP | Waktu diupdate |

## 🔧 Troubleshooting

### Error: `ModuleNotFoundError: No module named 'firebase_admin'`

```bash
pip install -r requirements.txt
```

### Error: `Access denied for user 'root'@'localhost'`

Periksa konfigurasi di file `.env`:
```env
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password
```

### Error: `Firebase credentials file not found`

Pastikan file `firebase_credentials.json` ada di folder yang sama atau sesuaikan path di `.env`:
```env
FIREBASE_CREDENTIALS_PATH=path/to/firebase_credentials.json
```

### MySQL Service Tidak Berjalan (Windows)

Buka Services dan jalankan MySQL:
```powershell
# Jalankan sebagai Administrator
net start MySQL80
```

## 📈 Monitoring

Log sinkronisasi disimpan di folder `logs/` dengan format:
- `sync_YYYYMMDD_HHMMSS.log`

Contoh log:
```
2024-01-01 12:00:00 - INFO - Starting sync for collection: attendance
2024-01-01 12:00:01 - INFO - Successfully synced 150 records to MySQL table `attendance`.
```

## 🔄 Cron Job (Otomatisasi)

### Windows Task Scheduler

1. Buat batch file `run_sync.bat`:
```batch
@echo off
cd /d "C:\Users\Admin\Repo\EZRALMS_data_base"
C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe sync_attendance.py
```

2. Buka Task Scheduler dan buat task baru yang berjalan setiap jam/interval yang diinginkan.

### Linux/Mac (Cron)

```bash
# Edit crontab
crontab -e

# Tambahkan baris berikut untuk sync setiap jam
0 * * * * cd /path/to/EZRALMS_data_base && /usr/bin/python3 sync_attendance.py
```

## 📝 Changelog

### v1.0.0 (Initial Release)
- Sinkronisasi Firestore ke MySQL
- Support mode full dan incremental sync
- Auto-create database schema
- Logging ke file
- Error handling

## 🤝 Support

Jika ada masalah atau pertanyaan, silakan buat issue di repository ini.

---

**Dibuat untuk EZRA LMS** 🎓
