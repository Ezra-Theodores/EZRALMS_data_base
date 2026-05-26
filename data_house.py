"""
DATA_HOUSE_EZRALMS - Unified Data Management System
================================================
Centralized data hub untuk semua kurikulum, soal, topic, dan user data.
- Baca dari folder data lokal (JSON_Exports, Firebase_Topics, Subtopics_By_Class, output)
- Sinkronisasi dari Firebase/Firestore
- RAG search untuk semantic query
- SQL query interface
"""

import sqlite3
import json
import re
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BM25:
    """BM25 ranking function"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.avgdl = 0
        self.doc_len = []
        self.doc_freqs = {}
        self.idf = {}
        self.N = 0
        self.corpus = []

    def fit(self, corpus: List[List[str]]):
        self.N = len(corpus)
        self.corpus = corpus
        self.doc_len = []
        self.doc_freqs = {}

        for doc in corpus:
            self.doc_len.append(len(doc))
            freq = Counter(doc)
            for word in freq:
                self.doc_freqs[word] = self.doc_freqs.get(word, 0) + 1

        self.avgdl = sum(self.doc_len) / self.N if self.N > 0 else 0

        for word, df in self.doc_freqs.items():
            self.idf[word] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def score(self, query: List[str], doc_idx: int) -> float:
        if doc_idx >= len(self.corpus):
            return 0

        doc = self.corpus[doc_idx]
        doc_len = self.doc_len[doc_idx]
        doc_freqs = Counter(doc)

        score = 0.0
        for term in query:
            if term not in self.idf:
                continue

            tf = doc_freqs.get(term, 0)
            idf = self.idf[term]

            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avgdl)

            score += idf * (numerator / denominator) if denominator > 0 else 0

        return score


import math


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    tokens: List[str] = field(default_factory=list)
    source_type: str = ""
    source_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SearchResult:
    document: Document
    score: float


class DataHouse:
    """
    DATA_HOUSE_EZRALMS - Centralized Data Management
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            self.base_path = Path(__file__).parent
        else:
            self.base_path = Path(base_path)

        self.data_house_path = self.base_path / "DATA_HOUSE_EZRALMS"
        self.db_path = self.base_path / "data_house.db"
        self.vector_index_path = self.base_path / "data_house_vectors.json"

        self._conn = None
        self._init_vector_store()

        logger.info(f"DATA_HOUSE initialized at: {self.base_path}")

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def initialize_database(self):
        """Create all tables"""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id TEXT UNIQUE,
                title TEXT,
                description TEXT,
                grade TEXT,
                subject TEXT,
                difficulty TEXT,
                quiz_type TEXT,
                creator_name TEXT,
                class_id TEXT,
                class_name TEXT,
                duration INTEGER DEFAULT 0,
                total_questions INTEGER DEFAULT 0,
                source TEXT,
                raw_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT UNIQUE,
                quiz_id TEXT,
                topic TEXT,
                id_q TEXT,
                en_q TEXT,
                image TEXT,
                options TEXT,
                ans INTEGER,
                id_exp TEXT,
                en_exp TEXT,
                source TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_id TEXT UNIQUE,
                topic_name TEXT,
                class_name TEXT,
                grade TEXT,
                curriculum TEXT,
                order_index INTEGER,
                topic_type TEXT,
                path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtopics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subtopic_id TEXT UNIQUE,
                topic_id TEXT,
                topic_name TEXT,
                class_name TEXT,
                order_index INTEGER,
                title TEXT,
                subtopic_type TEXT,
                content TEXT,
                source_file TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                material_id TEXT UNIQUE,
                source_name TEXT,
                topic TEXT,
                id_q TEXT,
                en_q TEXT,
                image TEXT,
                options TEXT,
                ans INTEGER,
                id_exp TEXT,
                en_exp TEXT,
                content_type TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                firestore_id TEXT UNIQUE,
                student_id TEXT,
                student_name TEXT,
                class_id TEXT,
                class_name TEXT,
                attendance_date TEXT,
                status TEXT,
                check_in_time TEXT,
                check_out_time TEXT,
                notes TEXT,
                raw_data TEXT,
                sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                operation TEXT,
                records_affected INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')

        for table in ['quizzes', 'questions', 'topics', 'subtopics', 'source_materials', 'attendance']:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_id ON {table}(id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_created ON {table}(created_at)')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_topic ON questions(topic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_questions_quiz ON questions(quiz_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_subtopics_topic ON subtopics(topic_id)')

        conn.commit()
        logger.info("Database tables initialized")

    def _init_vector_store(self):
        self.vector_store: List[Document] = []
        self.bm25 = BM25()
        self._indexed = False
        self._load_vectors()

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def _load_vectors(self):
        if self.vector_index_path.exists():
            try:
                with open(self.vector_index_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.vector_store = [
                    Document(
                        id=doc['id'],
                        content=doc['content'],
                        metadata=doc.get('metadata', {}),
                        tokens=doc.get('tokens', []),
                        source_type=doc.get('source_type', ''),
                        source_path=doc.get('source_path', ''),
                        created_at=doc.get('created_at', '')
                    )
                    for doc in data.get('documents', [])
                ]
                if self.vector_store:
                    self._reindex()
                logger.info(f"Vector store loaded: {len(self.vector_store)} documents")
            except Exception as e:
                logger.error(f"Failed to load vectors: {e}")

    def _reindex(self):
        if not self.vector_store:
            return
        corpus = [doc.tokens for doc in self.vector_store]
        self.bm25.fit(corpus)
        self._indexed = True

    def _save_vectors(self):
        save_data = {
            'documents': [
                {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'tokens': doc.tokens,
                    'source_type': doc.source_type,
                    'source_path': doc.source_path,
                    'created_at': doc.created_at
                }
                for doc in self.vector_store
            ]
        }
        with open(self.vector_index_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

    def _add_document(self, content: str, metadata: Dict, source_type: str, source_path: str = ""):
        doc_id = hashlib.md5(f"{content[:100]}{source_path}".encode()).hexdigest()

        existing = [d for d in self.vector_store if d.id == doc_id]
        if existing:
            return

        tokens = self._tokenize(content)
        doc = Document(
            id=doc_id,
            content=content,
            metadata=metadata,
            tokens=tokens,
            source_type=source_type,
            source_path=source_path
        )
        self.vector_store.append(doc)
        self._indexed = False

    def rebuild_index(self, force: bool = False):
        """Rebuild vector index from database"""
        if not force and self._indexed:
            logger.warning("Index already exists. Use force=True to rebuild.")
            return

        logger.info("Rebuilding vector index...")

        conn = self.connect()
        cursor = conn.cursor()

        self.vector_store = []

        cursor.execute('SELECT quiz_id, title, description, grade, subject, class_name FROM quizzes')
        for row in cursor.fetchall():
            content = f"Quiz: {row['title']} | Grade: {row['grade']} | Subject: {row['subject']} | Class: {row['class_name']} | {row['description']}"
            self._add_document(content, {
                'quiz_id': row['quiz_id'],
                'title': row['title'],
                'grade': row['grade'],
                'subject': row['subject'],
                'type': 'quiz'
            }, 'quiz', f"quizzes/{row['quiz_id']}")

        cursor.execute('SELECT unique_id, grade, subject, topic, id_q, en_q, difficulty, quiz_title FROM questions_normalized LIMIT 5000')
        for row in cursor.fetchall():
            content = f"Grade: {row['grade']} | Subject: {row['subject']} | Topic: {row['topic']} | {row['id_q'][:150] if row['id_q'] else ''}"
            self._add_document(content, {
                'unique_id': row['unique_id'],
                'grade': row['grade'],
                'subject': row['subject'],
                'topic': row['topic'],
                'type': 'normalized_question'
            }, 'normalized_question', f"questions_normalized/{row['unique_id']}")

        cursor.execute('SELECT topic_id, name, class_name, grade, subject FROM classwork_topics')
        for row in cursor.fetchall():
            content = f"Topic: {row['name']} | Class: {row['class_name']} | Grade: {row['grade']} | Subject: {row['subject']}"
            self._add_document(content, {
                'topic_id': row['topic_id'],
                'topic_name': row['name'],
                'type': 'classwork_topic'
            }, 'classwork_topic', f"classwork_topics/{row['topic_id']}")

        cursor.execute('SELECT subtopic_id, title, topic_id, class_name, subtopic_type FROM classwork_subtopics LIMIT 3000')
        for row in cursor.fetchall():
            content = f"Subtopic: {row['title']} | Type: {row['subtopic_type']} | Class: {row['class_name']}"
            self._add_document(content, {
                'subtopic_id': row['subtopic_id'],
                'title': row['title'],
                'type': 'classwork_subtopic'
            }, 'classwork_subtopic', f"classwork_subtopics/{row['subtopic_id']}")

        cursor.execute('SELECT class_id, name, grade, subject, curriculum, teacher_name FROM classes LIMIT 500')
        for row in cursor.fetchall():
            content = f"Class: {row['name']} | Grade: {row['grade']} | Subject: {row['subject']} | Curriculum: {row['curriculum']} | Teacher: {row['teacher_name']}"
            self._add_document(content, {
                'class_id': row['class_id'],
                'name': row['name'],
                'type': 'class'
            }, 'class', f"classes/{row['class_id']}")

        cursor.execute('SELECT user_id, name, email, role, xp FROM users LIMIT 500')
        for row in cursor.fetchall():
            content = f"User: {row['name']} | Email: {row['email']} | Role: {row['role']} | XP: {row['xp']}"
            self._add_document(content, {
                'user_id': row['user_id'],
                'name': row['name'],
                'type': 'user'
            }, 'user', f"users/{row['user_id']}")

        self._reindex()
        self._save_vectors()
        logger.info(f"Index rebuilt: {len(self.vector_store)} documents")

    def index_data_house(self):
        """Index all data from DATA_HOUSE folder"""
        logger.info("Indexing DATA_HOUSE...")

        self._index_json_exports()
        self._index_subtopics()
        self._index_source_materials()

        self._reindex()
        self._save_vectors()
        logger.info(f"Indexing complete: {len(self.vector_store)} documents")

    def _index_json_exports(self):
        """Index JSON_Exports folder"""
        json_path = self.data_house_path / "JSON_Exports"
        if not json_path.exists():
            logger.warning(f"JSON_Exports not found: {json_path}")
            return

        conn = self.connect()
        cursor = conn.cursor()

        for json_file in json_path.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if isinstance(data, dict) and 'questions' in data:
                    quiz_data = data
                elif isinstance(data, list):
                    quiz_data = {'questions': data, 'title': json_file.stem}
                else:
                    continue

                quiz_id = hashlib.md5(json_file.name.encode()).hexdigest()
                title = quiz_data.get('title', json_file.stem)
                description = quiz_data.get('description', '')

                grade = self._extract_grade(title)
                class_name = self._extract_class_name(title)

                cursor.execute('''
                    INSERT OR REPLACE INTO quizzes (quiz_id, title, description, grade, class_name, total_questions, source, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    quiz_id,
                    title,
                    description,
                    grade,
                    class_name,
                    len(quiz_data.get('questions', [])),
                    json_file.name,
                    json.dumps(quiz_data)
                ))

                for q in quiz_data.get('questions', []):
                    question_id = f"{quiz_id}_{q.get('id', 0)}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO questions (question_id, quiz_id, topic, id_q, en_q, image, options, ans, id_exp, en_exp, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        question_id,
                        quiz_id,
                        q.get('topic', ''),
                        q.get('id_q', ''),
                        q.get('en_q', ''),
                        q.get('image', ''),
                        json.dumps(q.get('options', [])),
                        q.get('ans', 0),
                        q.get('id_exp', ''),
                        q.get('en_exp', ''),
                        q.get('source', json_file.stem)
                    ))

                    content = f"Topic: {q.get('topic', '')} | Question: {q.get('id_q', '')[:300]}"
                    self._add_document(content, {
                        'question_id': question_id,
                        'topic': q.get('topic', ''),
                        'type': 'question'
                    }, 'question', str(json_file))

                conn.commit()
                logger.info(f"Indexed: {json_file.name} ({len(quiz_data.get('questions', []))} questions)")

            except Exception as e:
                logger.error(f"Failed to index {json_file.name}: {e}")

    def _index_subtopics(self):
        """Index Subtopics_By_Class folder"""
        subtopics_path = self.data_house_path / "Subtopics_By_Class"
        if not subtopics_path.exists():
            logger.warning(f"Subtopics_By_Class not found: {subtopics_path}")
            return

        conn = self.connect()
        cursor = conn.cursor()

        class_name = ""
        topic_name = ""

        for md_file in subtopics_path.glob("*.md"):
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                class_name = self._parse_class_name_from_file(md_file.name)

                lines = content.split('\n')
                topic_name = ""
                if lines and lines[0].startswith('#'):
                    topic_name = lines[0].replace('#', '').strip()

                table_started = False
                order_index = 0

                for line in lines:
                    if line.startswith('|'):
                        if 'Judul Materi' in line or 'Title' in line:
                            table_started = True
                            continue
                        if table_started and '|' in line:
                            parts = [p.strip() for p in line.split('|')]
                            if len(parts) >= 3:
                                try:
                                    order = int(parts[1]) if parts[1].isdigit() else order_index
                                    title = parts[2]
                                    subtopic_type = parts[3] if len(parts) > 3 else 'Quiz'

                                    subtopic_id = hashlib.md5(f"{md_file.name}{order}{title}".encode()).hexdigest()

                                    cursor.execute('''
                                        INSERT OR REPLACE INTO subtopics (subtopic_id, topic_name, class_name, order_index, title, subtopic_type, content, source_file)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    ''', (
                                        subtopic_id,
                                        topic_name,
                                        class_name,
                                        order,
                                        title,
                                        subtopic_type,
                                        '',
                                        md_file.name
                                    ))

                                    content_text = f"Subtopic: {title} | Type: {subtopic_type} | Topic: {topic_name}"
                                    self._add_document(content_text, {
                                        'subtopic_id': subtopic_id,
                                        'title': title,
                                        'class_name': class_name,
                                        'type': 'subtopic'
                                    }, 'subtopic', str(md_file))

                                    order_index += 1
                                except (ValueError, IndexError, KeyError):
                                    pass

                logger.info(f"Indexed subtopics from: {md_file.name}")

            except Exception as e:
                logger.error(f"Failed to index {md_file.name}: {e}")

        conn.commit()

    def _index_source_materials(self):
        """Index raw_to_JSON output folder"""
        output_path = self.data_house_path / "output"
        if not output_path.exists():
            logger.warning(f"output not found: {output_path}")
            return

        conn = self.connect()
        cursor = conn.cursor()

        for json_file in output_path.glob("*.json"):
            if 'raw_' in json_file.name:
                continue

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                questions = data if isinstance(data, list) else data.get('questions', [])

                for q in questions:
                    material_id = f"{json_file.stem}_{q.get('id', 0)}"
                    cursor.execute('''
                        INSERT OR REPLACE INTO source_materials (material_id, source_name, topic, id_q, en_q, image, options, ans, id_exp, en_exp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        material_id,
                        json_file.stem,
                        q.get('topic', ''),
                        q.get('id_q', ''),
                        q.get('en_q', ''),
                        q.get('image', ''),
                        json.dumps(q.get('options', [])),
                        q.get('ans', 0),
                        q.get('id_exp', ''),
                        q.get('en_exp', '')
                    ))

                logger.info(f"Indexed source materials from: {json_file.name} ({len(questions)} questions)")

            except Exception as e:
                logger.error(f"Failed to index {json_file.name}: {e}")

        conn.commit()
        logger.info("Source materials indexing complete")

    def _extract_grade(self, title: str) -> str:
        match = re.search(r'Grade\s*(\d+)', title, re.IGNORECASE)
        if match:
            return f"Grade {match.group(1)}"
        match = re.search(r'Kelas\s*(\d+)', title, re.IGNORECASE)
        if match:
            return f"Kelas {match.group(1)}"
        return "Unknown"

    def _extract_class_name(self, title: str) -> str:
        patterns = [
            r'G(\d+)',
            r'Grade\s*(\d+)',
            r'Kelas\s*(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return f"G{match.group(1)}"
        return "Unknown"

    def _parse_class_name_from_file(self, filename: str) -> str:
        name = filename.replace('.md', '').replace('Grade_', 'G').replace('Kelas_', 'G')
        return name

    def sync_attendance_from_firestore(self):
        """Sync attendance data from Firestore to local SQLite"""
        logger.info("Syncing attendance from Firestore...")

        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError:
            logger.error("firebase-admin not installed. Run: pip install firebase-admin")
            return False

        try:
            cred = credentials.Certificate(str(self.data_house_path / "firebase_credentials.json"))
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)

            db = firestore.client()
            attendance_ref = db.collection('attendance')
            docs = attendance_ref.stream()

            conn = self.connect()
            cursor = conn.cursor()
            inserted = updated = 0

            for doc in docs:
                data = doc.to_dict()
                firestore_id = doc.id

                raw_data = json.dumps(data)

                cursor.execute('''
                    INSERT OR REPLACE INTO attendance (firestore_id, student_id, student_name, class_id, class_name,
                                                       attendance_date, status, check_in_time, check_out_time, notes, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    firestore_id,
                    data.get('studentId'),
                    data.get('student_name'),
                    data.get('classId'),
                    data.get('class_name'),
                    data.get('attendance_date'),
                    data.get('status'),
                    data.get('check_in_time'),
                    data.get('check_out_time'),
                    data.get('notes'),
                    raw_data
                ))

                if cursor.rowcount == 1:
                    inserted += 1
                else:
                    updated += 1

            conn.commit()

            cursor.execute('''
                INSERT INTO sync_log (table_name, operation, records_affected, details)
                VALUES ('attendance', 'sync', ?, ?)
            ''', (inserted + updated, f"Inserted: {inserted}, Updated: {updated}"))
            conn.commit()

            logger.info(f"Sync complete: Inserted={inserted}, Updated={updated}")
            return True

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return False

    def search(self, query: str, k: int = 10, source_type: str = None) -> List[SearchResult]:
        """BM25 search across all indexed documents"""
        if not self._indexed:
            self._reindex()

        query_tokens = self._tokenize(query)
        scores = []

        for i, doc in enumerate(self.vector_store):
            if source_type and doc.source_type != source_type:
                continue

            score = self.bm25.score(query_tokens, i)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:k]:
            results.append(SearchResult(
                document=self.vector_store[idx],
                score=score
            ))

        return results

    def query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        """Execute SQL query"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        stats = {}

        tables = [
            'quizzes', 'questions', 'questions_normalized', 'classwork_topics', 'classwork_subtopics',
            'classes', 'users', 'sessions', 'packages', 'student_packages',
            'package_sessions', 'quiz_attempts', 'student_activities', 'tasks',
            'task_assignments', 'xp_transactions', 'games', 'league_cohorts',
            'weekly_achievements', 'attendance'
        ]
        for table in tables:
            try:
                result = self.query(f'SELECT COUNT(*) as count FROM {table}')
                stats[f'{table}_count'] = result[0]['count'] if result else 0
            except sqlite3.OperationalError:
                stats[f'{table}_count'] = 0

        if 'questions_normalized_count' in stats:
            stats['total_normalized_questions'] = stats.pop('questions_normalized_count')

        stats['vector_index_size'] = len(self.vector_store)
        stats['search_engine'] = 'BM25'

        return stats

    def generate_context(self, query: str, k: int = 5) -> str:
        """Generate context string for RAG queries"""
        results = self.search(query, k=k)

        if not results:
            return "No relevant data found."

        context_parts = ["[DATA_HOUSE Context]", ""]

        for i, result in enumerate(results, 1):
            doc = result.document
            meta = doc.metadata
            context_parts.append(
                f"[{i}] ({doc.source_type.upper()}) {doc.content[:200]} "
                f"(score: {result.score:.2f})"
            )

        return "\n".join(context_parts)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='DATA_HOUSE_EZRALMS - Unified Data Management')
    parser.add_argument('command', choices=['init', 'index', 'sync', 'search', 'stats', 'query', 'context', 'rebuild'],
                        help='Command to execute')
    parser.add_argument('--query', '-q', type=str, help='Search/query string')
    parser.add_argument('--k', type=int, default=10, help='Number of results')
    parser.add_argument('--type', '-t', type=str, help='Source type filter (quiz/question/topic/subtopic)')
    parser.add_argument('--sql', type=str, help='SQL query')
    parser.add_argument('--force', '-f', action='store_true', help='Force rebuild')

    args = parser.parse_args()

    dh = DataHouse()

    if args.command == 'init':
        dh.initialize_database()
        print("Database initialized!")

    elif args.command == 'index':
        dh.initialize_database()
        dh.index_data_house()
        print("Indexing complete!")

    elif args.command == 'sync':
        dh.initialize_database()
        dh.sync_attendance_from_firestore()
        print("Sync complete!")

    elif args.command == 'search':
        results = dh.search(args.query or "", k=args.k, source_type=args.type)
        print(f"\nSearch: '{args.query}' ({len(results)} results)\n")
        for i, r in enumerate(results, 1):
            print(f"[{i}] Score: {r.score:.2f} [{r.document.source_type}]")
            print(f"    {r.document.content[:150]}")
            print()

    elif args.command == 'stats':
        stats = dh.get_statistics()
        print("\nDATA_HOUSE Statistics:")
        print("=" * 50)
        for k, v in stats.items():
            print(f"  {k}: {v}")

    elif args.command == 'query':
        results = dh.query(args.sql or "SELECT * FROM quizzes LIMIT 3")
        for row in results:
            print(row)

    elif args.command == 'context':
        context = dh.generate_context(args.query or "", k=args.k)
        print(context)

    elif args.command == 'rebuild':
        dh.rebuild_index(force=args.force)


if __name__ == '__main__':
    main()
