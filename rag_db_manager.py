"""
EZRA LMS - RAG Database Management System
BM25-based semantic search (no GPU/model inference needed)
"""

import sqlite3
import json
import os
import hashlib
import logging
import re
import math
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from collections import Counter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class Document:
    id: str
    content: str
    metadata: Dict[str, Any]
    tokens: List[str] = field(default_factory=list)
    source_table: str = "attendance"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class SearchResult:
    document: Document
    score: float


class BM25:
    """BM25 ranking function implementation"""

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


class VectorStore:
    """Document store with BM25 indexing"""

    def __init__(self):
        self.documents: List[Document] = []
        self.bm25 = BM25()
        self._indexed = False

    def add(self, document: Document):
        self.documents.append(document)
        self._indexed = False

    def index(self):
        if not self.documents:
            return
        corpus = [doc.tokens for doc in self.documents]
        self.bm25.fit(corpus)
        self._indexed = True

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        if not self._indexed:
            self.index()

        query_tokens = self._tokenize(query)
        scores = []

        for i in range(len(self.documents)):
            score = self.bm25.score(query_tokens, i)
            if score > 0:
                scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scores[:k]:
            results.append(SearchResult(
                document=self.documents[idx],
                score=score
            ))

        return results

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def save(self, filepath: str):
        save_data = {
            'documents': [
                {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.metadata,
                    'tokens': doc.tokens,
                    'source_table': doc.source_table,
                    'created_at': doc.created_at
                }
                for doc in self.documents
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        logger.info(f"Vector store saved: {filepath}")

    def load(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                save_data = json.load(f)

            self.documents = [
                Document(
                    id=doc['id'],
                    content=doc['content'],
                    metadata=doc['metadata'],
                    tokens=doc.get('tokens', []),
                    source_table=doc.get('source_table', 'attendance'),
                    created_at=doc.get('created_at', datetime.now().isoformat())
                )
                for doc in save_data['documents']
            ]

            if self.documents:
                self.index()

            logger.info(f"Vector store loaded: {filepath} ({len(self.documents)} documents)")
            return True
        except Exception as e:
            logger.error(f"Failed to load vector store: {e}")
            return False


class RAGDatabaseManager:
    """
    RAG System for managing EzraLMS SQLite database.
    Provides BM25-based search and SQL queries.
    """

    def __init__(self, db_path: str = 'ezralms.db'):
        self.db_path = db_path
        self.vector_store_path = 'ezralms_vectors.json'
        self.vector_store = VectorStore()
        self._initialized = False

        self._load_vector_store()

    def _load_vector_store(self):
        if self.vector_store.load(self.vector_store_path):
            logger.info("Vector store loaded from disk")
        else:
            logger.info("No existing vector store found. Run rebuild_index() to create one.")

    def initialize(self):
        self._initialized = True
        logger.info("RAG Database Manager initialized")

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def rebuild_index(self, force: bool = False):
        if not force and self.vector_store.documents:
            logger.warning("Vector store already exists. Use force=True to rebuild.")
            return

        logger.info("Rebuilding index from database...")

        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM attendance')
        rows = cursor.fetchall()
        conn.close()

        self.vector_store = VectorStore()

        for row in rows:
            doc = self._row_to_document(dict(row))
            self.vector_store.add(doc)

        self.vector_store.index()
        self.vector_store.save(self.vector_store_path)
        logger.info(f"Index rebuilt: {len(self.vector_store.documents)} documents")

    def _row_to_document(self, row: Dict) -> Document:
        raw_data = {}
        if row.get('raw_data'):
            try:
                raw_data = json.loads(row['raw_data'])
            except json.JSONDecodeError:
                pass
                pass

        content_parts = [
            f"Student: {row.get('student_name') or raw_data.get('studentId', 'Unknown')}",
            f"Status: {row.get('status', 'unknown')}",
            f"Date: {row.get('attendance_date', 'N/A')}",
        ]

        if row.get('class_name'):
            content_parts.append(f"Class: {row['class_name']}")
        if row.get('check_in_time'):
            content_parts.append(f"Check-in: {row['check_in_time']}")
        if row.get('check_out_time'):
            content_parts.append(f"Check-out: {row['check_out_time']}")
        if row.get('notes'):
            content_parts.append(f"Notes: {row['notes']}")

        content = " | ".join(filter(None, content_parts))
        tokens = self._tokenize(content)

        doc_id = hashlib.md5(
            f"{row.get('firestore_id', '')}{row.get('id', '')}".encode()
        ).hexdigest()

        metadata = {
            'id': row.get('id'),
            'firestore_id': row.get('firestore_id'),
            'student_id': row.get('student_id'),
            'student_name': row.get('student_name'),
            'class_id': row.get('class_id'),
            'class_name': row.get('class_name'),
            'status': row.get('status'),
            'attendance_date': row.get('attendance_date'),
            'check_in_time': row.get('check_in_time'),
            'check_out_time': row.get('check_out_time'),
        }

        return Document(
            id=doc_id,
            content=content,
            metadata=metadata,
            tokens=tokens,
            source_table='attendance'
        )

    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'\b\w+\b', text)
        return tokens

    def search(self, query: str, k: int = 5) -> List[SearchResult]:
        results = self.vector_store.search(query, k=k)
        logger.info(f"Search '{query}' returned {len(results)} results")
        return results

    def query(self, sql: str, params: Tuple = ()) -> List[Dict]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]

    def get_statistics(self) -> Dict:
        conn = self.connect()
        cursor = conn.cursor()
        stats = {}

        cursor.execute('SELECT COUNT(*) as total FROM attendance')
        stats['total_attendance'] = cursor.fetchone()['total']

        cursor.execute('SELECT status, COUNT(*) as count FROM attendance GROUP BY status')
        stats['by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}

        cursor.execute('SELECT COUNT(DISTINCT student_id) as count FROM attendance')
        stats['unique_students'] = cursor.fetchone()['count']

        conn.close()

        stats['vector_index_size'] = len(self.vector_store.documents)
        stats['search_engine'] = 'BM25'

        return stats

    def add_attendance(self, data: Dict) -> int:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO attendance (firestore_id, student_id, student_name, class_id, class_name,
                                   attendance_date, status, check_in_time, check_out_time, notes, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('firestore_id'),
            data.get('student_id'),
            data.get('student_name'),
            data.get('class_id'),
            data.get('class_name'),
            data.get('attendance_date'),
            data.get('status', 'pending'),
            data.get('check_in_time'),
            data.get('check_out_time'),
            data.get('notes'),
            json.dumps(data.get('raw_data', {}))
        ))

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        doc = self._row_to_document({'id': new_id, **data})
        self.vector_store.add(doc)
        self.vector_store.index()
        self.vector_store.save(self.vector_store_path)

        return new_id

    def update_attendance(self, firestore_id: str, data: Dict) -> bool:
        conn = self.connect()
        cursor = conn.cursor()

        update_fields = []
        update_values = []

        for key in ['student_name', 'class_id', 'class_name', 'attendance_date',
                   'status', 'check_in_time', 'check_out_time', 'notes']:
            if key in data:
                update_fields.append(f"{key} = ?")
                update_values.append(data[key])

        if update_fields:
            update_fields.append('updated_at = ?')
            update_values.append(datetime.now().isoformat())
            update_values.append(firestore_id)

            cursor.execute(
                f"UPDATE attendance SET {', '.join(update_fields)} WHERE firestore_id = ?",
                update_values
            )

            conn.commit()
            affected = cursor.rowcount
            conn.close()

            if affected > 0:
                self.rebuild_index(force=True)

            return affected > 0

        return False

    def delete_attendance(self, firestore_id: str) -> bool:
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM attendance WHERE firestore_id = ?', (firestore_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        if affected > 0:
            self.rebuild_index(force=True)

        return affected > 0

    def sync_from_firestore(self):
        logger.info("Syncing from Firestore...")
        os.system('python sync_attendance_sqlite.py')
        self.rebuild_index(force=True)

    def generate_context(self, query: str, max_results: int = 3) -> str:
        results = self.search(query, k=max_results)

        if not results:
            return "No relevant data found."

        context_parts = ["Context from EzraLMS Attendance Database:", ""]

        for i, result in enumerate(results, 1):
            doc = result.document
            context_parts.append(
                f"[{i}] {doc.content} (score: {result.score:.2f})"
            )

        return "\n".join(context_parts)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='EZRA LMS RAG Database Manager')
    parser.add_argument('command', choices=['search', 'stats', 'sync', 'rebuild', 'query', 'context'],
                       help='Command to execute')
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--k', type=int, default=5, help='Number of results')
    parser.add_argument('--sql', type=str, help='SQL query to execute')

    args = parser.parse_args()

    manager = RAGDatabaseManager()

    if args.command == 'search':
        if not args.query:
            print("Error: --query required for search command")
            return

        results = manager.search(args.query, k=args.k)
        print(f"\nSearch results for: '{args.query}'\n")
        for i, result in enumerate(results, 1):
            print(f"[{i}] Score: {result.score:.3f}")
            print(f"    {result.document.content}")
            print()

    elif args.command == 'stats':
        stats = manager.get_statistics()
        print("\nDatabase Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            print(f"  {key}: {value}")

    elif args.command == 'sync':
        manager.sync_from_firestore()

    elif args.command == 'rebuild':
        manager.rebuild_index(force=True)

    elif args.command == 'query':
        if not args.sql:
            print("Error: --sql required for query command")
            return

        results = manager.query(args.sql)
        for row in results:
            print(row)

    elif args.command == 'context':
        if not args.query:
            print("Error: --query required for context command")
            return

        context = manager.generate_context(args.query, max_results=args.k)
        print(context)


if __name__ == '__main__':
    main()
