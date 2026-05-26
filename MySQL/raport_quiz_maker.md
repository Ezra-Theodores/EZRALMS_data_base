# Workflow: Pembuatan Raport Kuis EzraLMS

Workflow ini digunakan untuk mengumpulkan seluruh nilai kuis seorang siswa dari Firebase dan mengekspornya ke dalam file Excel yang rapi.

## Persiapan
1. Pastikan file `firebase_credentials.json` berada di direktori utama.
2. Pastikan library `pandas`, `openpyxl`, dan `firebase-admin` sudah terinstal.
   ```bash
   pip install pandas openpyxl firebase-admin
   ```

## Langkah-langkah Penggunaan

### 1. Menjalankan Script Otomatis
Anda dapat menggunakan script `make_report.py` untuk memproses raport secara otomatis.

**Cara Penggunaan:**
Buka terminal di direktori proyek dan jalankan perintah berikut:

```bash
python make_report.py "Nama_Siswa"
```
*Ganti `"Nama_Siswa"` dengan username atau nama lengkap siswa yang terdaftar di database.*

### 2. Output
Script akan melakukan hal berikut:
1. Mencari UID siswa berdasarkan nama yang dimasukkan.
2. Mengambil semua data dari koleksi `quiz_attempts` milik siswa tersebut.
3. Memilih **skor terbaru** jika siswa mengerjakan kuis yang sama lebih dari satu kali.
4. Menghitung persentase nilai secara otomatis.
5. Menghasilkan file Excel dengan nama: `Raport_Quiz_[Nama_Siswa].xlsx`.

## Struktur Data dalam Raport
File Excel yang dihasilkan akan memiliki kolom sebagai berikut:
- **Date**: Waktu penyelesaian kuis (WIB/UTC).
- **Quiz Title**: Judul materi kuis.
- **Score**: Nilai yang diperoleh.
- **Max Score**: Nilai maksimal kuis.
- **Percentage**: Persentase keberhasilan (%).
- **Correct**: Jumlah jawaban benar.
- **Total Q**: Total soal dalam kuis.

---

## Troubleshooting
- **User tidak ditemukan**: Pastikan nama yang dimasukkan sesuai dengan kolom `username` atau `name` di Firestore.
- **Data kosong**: Jika user ditemukan tetapi tidak ada file Excel, berarti user tersebut belum pernah mengerjakan kuis di aplikasi.
- **Timezone Error**: Jika muncul error terkait timezone di Excel, pastikan script menggunakan `.dt.tz_localize(None)` sebelum export (sudah ditangani di `make_report.py`).

---
*Dibuat otomatis oleh Antigravity untuk EzraLMS.*
