# EZRA LMS - Memory and Progress Report

**Tanggal Dibuat:** 2026-05-10
**Status:** Dokumentasi Lengkap - All-in-One

---

## Daftar Isi

1. [Project Overview](#1-project-overview)
2. [Dokumentasi Firebase-MySQL Sync](#2-dokumentasi-firebase-mysql-sync)
3. [Progress Report: PDF/Web to JSON Converter](#3-progress-report-pdfweb-to-json-converter)
4. [Project Memory](#4-project-memory)
5. [Implementation Summary: Image Extraction & SVG](#5-implementation-summary-image-extraction--svg)
6. [JSON Format Standard](#6-json-format-standard)
7. [Next Steps](#7-next-steps)

---

## 1. Project Overview

Proyek ini bertujuan untuk:
- **Sinkronisasi data** dari Firebase Firestore ke MySQL lokal
- **Konversi konten edukasi** (PDF, web URL) ke format JSON terstruktur
- **Manajemen database** soal untuk EZRA LMS

### Struktur Folder Utama

```
EZRALMS_data_base/
├── .env                          # Konfigurasi environment
├── .env.example                  # Template konfigurasi
├── firebase_credentials.json     # Kredensial Firebase
├── mysql_schema.sql              # Schema database MySQL
├── requirements.txt              # Dependency Python
├── README.md                     # Dokumentasi sync
├── sync_attendance.py            # Script sinkronisasi utama
├── sync_firebase_to_mysql.py     # Script sinkronisasi lama
├── test_connection.py            # Test koneksi
├── data_house.db                 # SQLite data house
├── ezralms.db                    # SQLite ezralms
├── rag_db_manager.py            # RAG database manager
├── dashboard_app.py             # Dashboard Flask app
└── DATA_HOUSE_EZRALMS/           # Konversi PDF/Web ke JSON
    ├── server.py                # Flask API server
    ├── pdf_to_json.py           # Ekstraksi PDF
    ├── auto_scraper.py          # Web scraping
    ├── image_extractor.py       # Ekstrak gambar
    ├── svg_converter.py         # Konversi ke SVG
    ├── convert.py               # CLI unified tool
    ├── STANDAR_FORMAT_JSON.md   # Format JSON standar
    ├── web_ui/                  # Frontend UI
    ├── output/                  # JSON hasil
    ├── chroma_db/               # Chroma vector DB
    └── Subtopics_By_Class/      # Subtopik per kelas
```

---

## 2. Dokumentasi Firebase-MySQL Sync

### 2.1 Struktur Database MySQL

#### Tabel `attendance`

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

### 2.2 Cara Menjalankan

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Konfigurasi Environment
Copy `.env.example` ke `.env` dan sesuaikan:
```env
MYSQL_HOST=127.0.0.1
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=ezralms_db
MYSQL_PORT=3306
FIREBASE_CREDENTIALS_PATH=firebase_credentials.json
SYNC_MODE=incremental
LOG_LEVEL=INFO
```

#### Test Koneksi
```bash
python test_connection.py
```

#### Jalankan Sinkronisasi
```bash
# Mode Incremental (default)
python sync_attendance.py

# Mode Full (hapus semua & insert ulang)
python sync_attendance.py --mode full

# Collection tertentu
python sync_attendance.py --collection students
```

### 2.3 Troubleshooting

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'firebase_admin'` | `pip install -r requirements.txt` |
| `Access denied for user 'root'@'localhost'` | Periksa password di `.env` |
| `Firebase credentials file not found` | Sesuaikan path di `.env` |
| MySQL service tidak berjalan | `net start MySQL80` (Windows) |

### 2.4 Monitoring

Log sinkronisasi: `logs/sync_YYYYMMDD_HHMMSS.log`

---

## 3. Progress Report: PDF/Web to JSON Converter

**Tanggal:** 2026-05-04
**Status:** ✅ Core functionality completed, Gemini API integration ready

### 3.1 Completed Work

#### PDF Extraction & Conversion
- **File:** `pdf_to_json.py`
- Extracts text from PDF using `pdfplumber`
- Parses questions from Singapore Math Challenge format
- Handles Section A (Q1-40) and Section B (Q41-45)
- Cleans page headers, footers, and artifacts
- Outputs JSON following `STANDAR_FORMAT_JSON.md`

**Result:** Successfully converted `Singapore_Math_Challenge_Grade3_2023.pdf` → 45 questions

#### Web Scraping & Conversion
- **File:** `auto_scraper.py`
- Fetches content from educational websites (defantri.com, zenius.net, etc.)
- Extracts main content using BeautifulSoup
- Saves raw text to `output/raw_{n}_{domain}.md`
- Uses **Gemini API** to extract questions and generate JSON

#### Web UI (Flask Backend + HTML Frontend)
- **Files:** `server.py`, `web_ui/index.html`
- Drag & drop PDF upload
- URL input for web scraping
- Real-time progress tracking
- JSON preview with tabs (Preview / Questions List)
- Download JSON file
- Copy to clipboard
- Gemini API status indicator

#### API Endpoints
- `GET /` - Serve web UI
- `POST /api/convert` - Convert PDF or URL
- `GET /api/health` - Check Gemini API availability

### 3.2 Dependencies

```
flask==3.0.0
flask-cors==4.0.0
pdfplumber==0.11.9
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
google-generativeai==0.3.2
```

### 3.3 Known Limitations

1. **Web Scraping without Gemini API:** Limited accuracy - Solution: Set `GEMINI_API_KEY`
2. **PDF Text Extraction:** Requires text-based PDF (not scanned images)
3. **SVG Generation:** Currently placeholder SVGs - Future: AI-generated educational illustrations

---

## 4. Project Memory

**Last Updated:** 2026-05-08

### 4.1 Tujuan Project

Project ini bertujuan untuk **mengumpulkan dan mengkonversi soal-soal matematika dari berbagai sumber (website, PDF) ke dalam format JSON yang terstruktur dan standar**.

### 4.2 Struktur Folder

1. **raw_material_links.md** - Link sumber soal yang SUDAH diproses
2. **output/** - File JSON hasil parsing dari website
3. **output_jason_std/** - JSON yang sudah dikelompokkan per topik
4. **raw_PDF/** - PDF asli
5. **.agents/** - Konfigurasi sistem agent
6. **web_ui/** - Web interface untuk upload dan konversi
7. **chroma_db/** - Chroma vector database untuk RAG

### 4.3 Alur Kerja (Workflow)

```
Step 1: Ekstraksi Materi (Raw Material → Text + Image Flags)
    ↓
Step 2: Konversi ke Markdown (Format JSON)
    ↓
Step 3: Konfirmasi Gambar (User Interaction)
    ↓
Step 4: Standarisasi Logika Matematika (Hitung ulang jawaban)
    ↓
Step 5: Standarisasi Struktur JSON
    ↓
Step 6: Simpan JSON ke output_jason_std/
```

### 4.4 Unified CLI Tool: `convert.py`

**Installation:**
```bash
pip install google-genai PyPDF2
```

**Commands:**

| Command | Description |
|---------|-------------|
| `convert --input <file> --output <dir> [--mode mc] [--no-image]` | Convert input to JSON |
| `validate --dir <directory> [--verbose]` | Validate JSON format |
| `expand --file <file.json> --min 20` | Generate additional questions |
| `add-images --file <file.json> --mapping <images.csv>` | Add images from CSV |

### 4.5 Current Context

- Web UI sudah dimodifikasi untuk mendukung semua PDF
- Bridging protocol aktif untuk task baru
- Server Flask berjalan dengan static files
- RAG database manager sudah tersedia (`rag_db_manager.py`)

---

## 5. Implementation Summary: Image Extraction & SVG

**Status:** ✅ All core modules complete and ready for testing

### 5.1 Core Modules Created

| Module | Lines | Description |
|--------|-------|-------------|
| `image_extractor.py` | 1,100 | Extract images from PDF (PyMuPDF) & web (BeautifulSoup) |
| `svg_converter.py` | 600 | Convert raster to SVG (Potrace, edge detection, Pillow) |
| `image_question_matcher.py` | 520 | Match images to questions (position, Gemini Vision, sequential) |
| `pdf_to_json_with_images.py` | 300 | Complete pipeline with images |

### 5.2 Architecture

```
PDF/Web Source
    ↓
[Image Extractor] → Extract images with metadata
    ↓
[SVG Converter] → Convert images to SVG
    ↓
[Question Matcher] → Match images to questions
    ↓
[JSON Output] → Questions with embedded SVG
```

### 5.3 Usage Examples

```python
# Process PDF with Images
from pdf_to_json_with_images import process_pdf_with_images
result = process_pdf_with_images(
    pdf_path='path/to/file.pdf',
    output_dir='output/',
    gemini_api_key='your-api-key'
)

# Extract Images Only
from image_extractor import extract_and_save_images
saved_paths = extract_and_save_images(source='file.pdf', output_dir='output/images/')

# Convert Image to SVG
from svg_converter import convert_image_to_svg
svg_content = convert_image_to_svg(image_path='img.png', method='auto')

# Match Images to Questions
from image_question_matcher import ImageQuestionMatcher
matcher = ImageQuestionMatcher(gemini_api_key='your-key')
matches = matcher.match_images_to_questions(questions, images, strategy='auto')
```

### 5.4 Dependencies Added

```
PyMuPDF==1.25.3
Pillow==10.2.0
numpy==1.26.0
svglib==1.5.1
reportlab==4.0.9
pypotrace==0.3
```

---

## 6. JSON Format Standard

### 6.1 Struktur Setiap Question

```json
{
  "id": 1,
  "id_q": "Pertanyaan dalam Bahasa Indonesia",
  "en_q": "Question in English",
  "image": "<svg>...</svg>",
  "options": ["A", "B", "C", "D"],
  "id_options": ["Pilihan A", "Pilihan B", "Pilihan C", "Pilihan D"],
  "en_options": ["Option A", "Option B", "Option C", "Option D"],
  "ans": 0,
  "id_exp": "Penjelasan dalam Bahasa Indonesia",
  "en_exp": "Explanation in English"
}
```

### 6.2 Field Details

| Field | Type | Keterangan |
|-------|------|-------------|
| `id` | Integer | Nomor urut soal (1, 2, 3, ...) |
| `id_q` | String | Pertanyaan dalam Bahasa Indonesia |
| `en_q` | String | Pertanyaan dalam Bahasa Inggris |
| `image` | String | SVG inline atau `""` untuk soal tanpa gambar |
| `options` | Array | Label: `["A", "B", "C", "D"]` |
| `id_options` | Array | Pilihan jawaban dalam ID |
| `en_options` | Array | Pilihan jawaban dalam EN |
| `ans` | Integer/null | Indeks jawaban benar (0=A, 1=B, 2=C, 3=D), null untuk open-ended |
| `id_exp` | String | Penjelasan dalam Bahasa Indonesia |
| `en_exp` | String | Penjelasan dalam Bahasa Inggris |

### 6.3 LaTeX Notation

| Format | Syntax | Contoh |
|--------|--------|--------|
| Pecahan | `$\frac{a}{b}$` | `$\frac{1}{2}$` |
| Pangkat | `$x^2$` | `$2^{-3}$` |
| Akar | `$\sqrt{x}$` | `$\sqrt[3]{8}$` |
| Derajat | `$90^\circ$ |  |

### 6.4 Translation Guide

| English | Bahasa Indonesia |
|---------|------------------|
| Fraction | Pecahan |
| Decimal | Desimal |
| Percentage | Persen |
| Area | Luas |
| Perimeter | Keliling |
| Volume | Volume |
| Mean/Average | Rata-rata/Mean |
| Rectangle | Persegi Panjang |
| Square | Persegi |
| Cube | Kubus |
| Triangle | Segitiga |
| Circle | Lingkaran |

### 6.5 Validasi

Pastikan:
1. Semua field wajib ada
2. `id` unik dan berurutan
3. Jumlah `id_options` = 4 untuk pilihan ganda
4. `ans` dalam range 0-3 atau `null` untuk open-ended
5. SVG valid jika ada
6. LaTeX properly escaped

---

## 7. Next Steps

### 7.1 Priority Items

1. **Testing RAG Database**
   - Test `rag_db_manager.py` dengan data yang ada
   - Verify ChromaDB integration

2. **SVG Generation Enhancement**
   - Integrate AI untuk automatic SVG creation
   - Build library of reusable educational graphics

3. **Translation Automation**
   - Auto-translate ID ↔ EN menggunakan API
   - Improve mathematical terminology consistency

4. **Web UI Dashboard**
   - Verify `dashboard_app.py` fully functional
   - Check `templates/dashboard.html`

### 7.2 User Preferences Observed

1. **Standardization is critical** - All JSON must follow exact format
2. **Question extraction must be accurate** - Only questions, no theory content
3. **Bilingual output** - Every field in both ID and EN
4. **SVG illustrations** - Important for visual questions
5. **Workflow consistency** - Follow `auto_scraper.py` pattern

### 7.3 Files to Reference

1. `auto_scraper.py` - Proven web scraping workflow
2. `JSON_SOAL_GENERATOR_PROMPT.md` - System prompt for Gemini
3. `STANDAR_FORMAT_JSON.md` - Complete format documentation
4. `convert.py` - Unified CLI tool

---

## 📝 Catatan

- **Dokumen ini digabungkan dari 5 file:**
  1. SESSION_PROGRESS_2026-05-04.md
  2. PROJECT_MEMORY.md
  3. IMPLEMENTATION_SUMMARY.md
  4. README.md (root)
  5. STANDAR_FORMAT_JSON.md

- **Last Update:** 2026-05-10

---

**End of Memory and Progress Report**