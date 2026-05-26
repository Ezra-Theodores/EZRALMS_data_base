"""
Normalize all questions into a single unified table.
Consolidates questions from: Firebase quizzes, JSON_Exports, source_materials

Each question has:
- unique_id: Global unique ID
- source: 'firestore' | 'json_export' | 'source_material'
- source_id: Original ID from source
- grade: Grade level
- subject: Subject (Math, Science, etc)
- topic: Main topic
- subtopic: Subtopic
- id_q: Indonesian question text
- en_q: English question text
- image: Image URL/Base64 SVG
- options: JSON array of options (A, B, C, D)
- ans: Correct answer index (0-3)
- id_exp: Indonesian explanation
- en_exp: English explanation
- difficulty: Easy/Medium/Hard
- curriculum: National, IB, Ezra Curriculum, etc
- class_name: Class/kelas name
- quiz_title: Original quiz title
- raw_json: Original data backup
"""

import sqlite3
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_normalized_table(cursor):
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions_normalized (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unique_id TEXT UNIQUE NOT NULL,
            source TEXT NOT NULL,
            source_id TEXT,
            grade TEXT,
            subject TEXT,
            topic TEXT,
            subtopic TEXT,
            id_q TEXT,
            en_q TEXT,
            image TEXT,
            options TEXT,
            ans INTEGER DEFAULT 0,
            id_exp TEXT,
            en_exp TEXT,
            difficulty TEXT,
            curriculum TEXT,
            class_name TEXT,
            quiz_title TEXT,
            creator_name TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_norm_grade ON questions_normalized(grade)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_norm_topic ON questions_normalized(topic)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_norm_source ON questions_normalized(source)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_norm_unique ON questions_normalized(unique_id)')


def normalize_value(val) -> str:
    if val is None:
        return ''
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False, default=str)
    if isinstance(val, bool):
        return '1' if val else '0'
    return str(val)


def get_options_array(options) -> str:
    if isinstance(options, list):
        return json.dumps(options)
    if isinstance(options, dict):
        opt_list = [options.get('A', ''), options.get('B', ''),
                   options.get('C', ''), options.get('D', '')]
        return json.dumps(opt_list)
    if isinstance(options, str):
        try:
            parsed = json.loads(options)
            if isinstance(parsed, list):
                return options
            return json.dumps([parsed])
        except (json.JSONDecodeError, ValueError):
            return json.dumps([options])
    return json.dumps([])


def extract_answer(ans) -> int:
    if ans is None:
        return 0
    if isinstance(ans, int):
        return max(0, min(3, ans))
    if isinstance(ans, list):
        return int(ans[0]) if ans else 0
    if isinstance(ans, str):
        try:
            return int(ans)
        except (ValueError, TypeError):
            return 0
    return 0


def generate_unique_id(source: str, source_id: str, id_q: str) -> str:
    combined = f"{source}:{source_id}:{id_q[:50] if id_q else ''}"
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def normalize_firestore_questions(conn, cursor):
    """Normalize questions from Firestore quizzes"""
    cursor.execute('SELECT quiz_id, title, grade, subject, difficulty, creator_name, raw_json FROM quizzes')
    quizzes = cursor.fetchall()

    total = 0
    skipped = 0

    for quiz in quizzes:
        quiz_id = quiz[0]
        quiz_title = quiz[1] or ''
        grade = str(quiz[2]) if quiz[2] else ''
        subject = quiz[3] or ''
        difficulty = quiz[4] or ''
        creator_name = quiz[5] or ''

        cursor.execute('SELECT quiz_id, topic, id_q, en_q, image, options, ans, id_exp, en_exp FROM questions WHERE quiz_id = ?', (quiz_id,))
        questions = cursor.fetchall()

        for q in questions:
            topic = q[1] or ''
            id_q = q[2] or ''
            en_q = q[3] or ''
            image = q[4] or ''
            options = q[5] or '[]'
            ans = q[6]
            id_exp = q[7] or ''
            en_exp = q[8] or ''

            if not id_q and not en_q:
                skipped += 1
                continue

            unique_id = generate_unique_id('firestore', q[0], id_q)
            options_json = get_options_array(options)
            ans_int = extract_answer(ans)

            raw_json = json.dumps({
                'quiz_id': quiz_id,
                'quiz_title': quiz_title,
                'topic': topic,
                'id_q': id_q,
                'en_q': en_q,
                'image': image,
                'options': options,
                'ans': ans,
                'id_exp': id_exp,
                'en_exp': en_exp
            }, ensure_ascii=False, default=str)

            cursor.execute('''
                INSERT OR REPLACE INTO questions_normalized
                (unique_id, source, source_id, grade, subject, topic, subtopic,
                 id_q, en_q, image, options, ans, id_exp, en_exp,
                 difficulty, curriculum, class_name, quiz_title, creator_name, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                unique_id, 'firestore', q[0], grade, subject, topic, '',
                id_q, en_q, image, options_json, ans_int, id_exp, en_exp,
                difficulty, '', '', quiz_title, creator_name, raw_json
            ))

    conn.commit()
    return total, skipped


def normalize_json_exports(conn, cursor, base_path):
    """Normalize questions from JSON_Exports folder"""
    json_path = base_path / "DATA_HOUSE_EZRALMS" / "JSON_Exports"
    if not json_path.exists():
        logger.warning(f"JSON_Exports not found: {json_path}")
        return 0, 0

    total = 0
    skipped = 0

    for json_file in json_path.glob("*.json"):
        if 'Grade' not in json_file.stem and 'SAJ' not in json_file.stem:
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = data if isinstance(data, list) else data.get('questions', [])
            if not questions:
                continue

            grade = ''
            grade_match = json_file.stem
            for g in range(1, 13):
                if f'Grade{g}' in grade_match or f'Grade {g}' in grade_match:
                    grade = str(g)
                    break
                if f'Kelas{g}' in grade_match:
                    grade = str(g)
                    break

            for q in questions:
                if not isinstance(q, dict):
                    continue

                id_q = q.get('id_q', '') or q.get('question', '') or q.get('text', '')
                en_q = q.get('en_q', '') or ''
                topic = q.get('topic', '') or ''

                if not id_q:
                    skipped += 1
                    continue

                unique_id = generate_unique_id('json_export', f"{json_file.stem}_{q.get('id', 0)}", id_q)

                options = q.get('options', []) or []
                id_options = q.get('id_options', []) or options
                if id_options == options and isinstance(options, dict):
                    id_options = [options.get('A', ''), options.get('B', ''),
                                  options.get('C', ''), options.get('D', '')]

                options_json = json.dumps(id_options) if isinstance(id_options, list) else str(id_options)
                ans_int = extract_answer(q.get('ans', 0))

                cursor.execute('''
                    INSERT OR IGNORE INTO questions_normalized
                    (unique_id, source, source_id, grade, subject, topic, subtopic,
                     id_q, en_q, image, options, ans, id_exp, en_exp, difficulty, quiz_title, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    unique_id, 'json_export', f"{json_file.stem}_{q.get('id', 0)}",
                    grade, 'Math', topic, '',
                    id_q, en_q, '',
                    options_json, ans_int,
                    q.get('id_exp', '') or q.get('explanation', ''),
                    q.get('en_exp', ''),
                    '', json_file.stem,
                    json.dumps(q, ensure_ascii=False)
                ))
                total += 1

        except Exception as e:
            logger.error(f"Failed to process {json_file.name}: {e}")
            skipped += 1

    conn.commit()
    return total, skipped


def normalize_source_materials(conn, cursor, base_path):
    """Normalize questions from raw_to_JSON output folder"""
    output_path = base_path / "DATA_HOUSE_EZRALMS" / "output"
    if not output_path.exists():
        logger.warning(f"output not found: {output_path}")
        return 0, 0

    total = 0
    skipped = 0

    for json_file in output_path.glob("*.json"):
        if 'raw_' in json_file.name:
            continue

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            questions = data if isinstance(data, list) else data.get('questions', [])
            if not questions:
                continue

            for q in questions:
                if not isinstance(q, dict):
                    continue

                id_q = q.get('id_q', '') or q.get('question', '') or q.get('text', '')
                if not id_q:
                    skipped += 1
                    continue

                unique_id = generate_unique_id('source_material', f"{json_file.stem}_{q.get('id', 0)}", id_q)

                options = q.get('options', []) or []
                id_options = q.get('id_options', []) or options

                options_json = json.dumps(id_options) if isinstance(id_options, list) else str(id_options)
                ans_int = extract_answer(q.get('ans', 0))

                cursor.execute('''
                    INSERT OR IGNORE INTO questions_normalized
                    (unique_id, source, source_id, grade, subject, topic, subtopic,
                     id_q, en_q, image, options, ans, id_exp, en_exp, difficulty, quiz_title, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    unique_id, 'source_material', f"{json_file.stem}_{q.get('id', 0)}",
                    '', '', q.get('topic', ''), '',
                    id_q, q.get('en_q', ''),
                    q.get('image', ''),
                    options_json, ans_int,
                    q.get('id_exp', ''),
                    q.get('en_exp', ''),
                    '', json_file.stem,
                    json.dumps(q, ensure_ascii=False)
                ))
                total += 1

        except Exception as e:
            logger.error(f"Failed to process {json_file.name}: {e}")
            skipped += 1

    conn.commit()
    return total, skipped


def infer_grades_from_topics(conn, cursor):
    """Infer grade from topic/classwork_topics"""
    cursor.execute('SELECT topic_id, name, class_name, grade FROM classwork_topics')
    topic_map = {}
    for row in cursor.fetchall():
        topic_map[row[0]] = {
            'name': row[1],
            'class_name': row[2],
            'grade': row[3]
        }

    cursor.execute('SELECT unique_id, topic FROM questions_normalized WHERE grade = "" OR grade IS NULL')
    rows = cursor.fetchall()

    for row in rows:
        unique_id = row[0]
        topic = row[1] or ''

        matched_grade = ''
        matched_class = ''

        for topic_id, info in topic_map.items():
            if topic and topic_id and (topic_id in topic or topic in topic_id):
                matched_grade = info['grade']
                matched_class = info['class_name']
                break

        if matched_grade:
            cursor.execute('''
                UPDATE questions_normalized SET grade = ?, class_name = ? WHERE unique_id = ?
            ''', (matched_grade, matched_class, unique_id))

    conn.commit()


def main():
    db_path = Path(__file__).parent / "data_house.db"
    base_path = Path(__file__).parent

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("Creating normalized questions table...")
    create_normalized_table(cursor)
    conn.commit()

    logger.info("\n" + "=" * 60)
    logger.info("NORMALIZING QUESTIONS FROM ALL SOURCES")
    logger.info("=" * 60)

    logger.info("\n[1/3] Normalizing Firestore quizzes...")
    total, skipped = normalize_firestore_questions(conn, cursor)
    logger.info(f"  Done: {total} questions normalized, {skipped} skipped")

    logger.info("\n[2/3] Normalizing JSON_Exports...")
    total, skipped = normalize_json_exports(conn, cursor, base_path)
    logger.info(f"  Done: {total} questions normalized, {skipped} skipped")

    logger.info("\n[3/3] Normalizing source_materials...")
    total, skipped = normalize_source_materials(conn, cursor, base_path)
    logger.info(f"  Done: {total} questions normalized, {skipped} skipped")

    logger.info("\n[+] Inferring grades from topics...")
    infer_grades_from_topics(conn, cursor)

    cursor.execute('SELECT COUNT(*) FROM questions_normalized')
    total_count = cursor.fetchone()[0]

    cursor.execute('SELECT source, COUNT(*) as c FROM questions_normalized GROUP BY source')
    by_source = cursor.fetchall()

    cursor.execute('SELECT grade, COUNT(*) as c FROM questions_normalized WHERE grade != "" GROUP BY grade ORDER BY CAST(grade AS INTEGER)')
    by_grade = cursor.fetchall()

    logger.info("\n" + "=" * 60)
    logger.info("NORMALIZATION COMPLETE!")
    logger.info("=" * 60)
    logger.info(f"  Total questions: {total_count:,}")

    logger.info("\n  By source:")
    for row in by_source:
        logger.info(f"    {row['source']}: {row['c']:,}")

    logger.info("\n  By grade:")
    for row in by_grade:
        if row['grade']:
            logger.info(f"    Grade {row['grade']}: {row['c']:,}")

    cursor.execute('SELECT DISTINCT topic FROM questions_normalized WHERE topic != "" ORDER BY topic')
    topics = [r[0] for r in cursor.fetchall()]
    logger.info(f"\n  Unique topics: {len(topics)}")

    conn.close()


if __name__ == '__main__':
    main()
