# RAG Database - Dokumentasi

Sistem RAG (Retrieval-Augmented Generation) Database untuk soal matematika dengan semantic search.

## Status

| Komponen | Status |
|----------|--------|
| Firebase Connection | Connected (project `threebody-933be`) |
| Data Extraction | 277 quizzes, 5,431 questions |
| RAG Database | Built with metadata |
| Quiz Assembler | Ready |
| Search/Filter | Ready |

## Struktur Folder

```
rag-db/
├── questions/              # Soal per topik
│   ├── 01-Bilangan/
│   ├── 02-Aritmatika/
│   ├── 03-Geometri/
│   ├── 04-Pengukuran/
│   ├── 05-Statistika/
│   ├── 06-Rasio/
│   ├── 07-Peluang/
│   ├── 08-Aljabar/
│   ├── 09-Logika/
│   └── 99-Unclassified/
├── embeddings/             # Vector embeddings (768-dim)
├── metadata/
│   ├── index.json        # Complete question index
│   └── stats.json        # Database statistics
└── assembled-quizzes/    # Generated quizzes
```

## Quick Start

### 1. Ekstrak Data dari Firebase
```bash
node scripts/extract-firebase.js
```
Output: `data/all-quizzes.json`

### 2. Build RAG Database
```bash
node scripts/build-rag.js
```
Output: `rag-db/questions/*`, `rag-db/metadata/*`

### 3. Search/Filter Soal
```bash
# Lihat statistik
node scripts/search-rag.js stats

# Filter soal
node scripts/search-rag.js filter topic=Geometri grade=6
node scripts/search-rag.js filter difficulty=medium hasImage=true
node scripts/search-rag.js filter skillTag=visual-spatial
```

### 4. Assemble Quiz
```bash
# Buat quiz baru
node scripts/assemble-quiz.js assemble grade=6 topic=Geometri difficulty=medium count=20

# Dengan output file
node scripts/assemble-quiz.js assemble grade=4 difficulty=easy count=10 output=./my-quiz.json

# Lihat detail soal
node scripts/assemble-quiz.js get q-xxxxx-xxxx-xxxx
```

## Generate Embeddings (Opsional)

Untuk semantic search dengan vector similarity:

```bash
# Install dependencies
pip install sentence-transformers torch numpy

# Generate embeddings
python scripts/generate-embeddings.py
```

## Filter & Search Options

### Filter Parameters
| Parameter | Type | Example |
|-----------|------|---------|
| `grade` | string | `grade=6` |
| `topic` | string | `topic=Geometri` |
| `difficulty` | string | `difficulty=medium` |
| `hasImage` | boolean | `hasImage=true` |
| `skillTag` | string | `skillTag=visual-spatial` |

### Available Topics
- Bilangan, Bilangan Lanjut
- Aritmatika
- Geometri
- Pengukuran
- Statistika
- Rasio
- Peluang
- Aljabar
- Logika

### Available Skill Tags
- calculation, visual-spatial, multi-step
- grade-lower, grade-middle, grade-upper
- comparison, formula-application
- ordering, pattern-recognition, reading-graph
- estimation, problem-solving

## API Integration Example

```javascript
const { assembleQuiz, getQuestionDetails } = require('./scripts/assemble-quiz');
const { filterSearch } = require('./scripts/search-rag');

// Assemble custom quiz
const quiz = assembleQuiz({
  grade: '6',
  topic: 'Geometri',
  difficulty: 'medium'
}, 20);

// Filter questions
const geometryQuestions = filterSearch(metadata, {
  topic: 'Geometri',
  grade: '6',
  difficulty: 'medium'
});
```

## Maintenance

### Update Database
```bash
# Re-extract from Firebase
node scripts/extract-firebase.js

# Rebuild RAG database
node scripts/build-rag.js

# Regenerate embeddings (if needed)
python scripts/generate-embeddings.py
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Cannot find module 'firebase-admin'` | Run `npm install firebase-admin` |
| `Service account file not found` | Check `firebase_credentials.json` exists |
| `No questions match criteria` | Check filter parameters or run `stats` |
| Embeddings too slow | Use GPU or reduce batch size |

## Next Steps

1. ✅ Firebase Connection - DONE
2. ✅ Data Extraction - DONE
3. ✅ RAG Database - DONE
4. ✅ Quiz Assembler - DONE
5. ⏭️ Optional: Generate Embeddings
6. ⏭️ Optional: MySQL Integration
7. ⏭️ Optional: API Endpoints

---

**Generated:** 2026-05-07  
**Version:** 1.0.0
