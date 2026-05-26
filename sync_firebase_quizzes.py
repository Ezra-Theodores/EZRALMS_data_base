"""
Sync quizzes from Firebase Firestore to DATA_HOUSE
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def sync_quizzes(db, cursor, conn):
    """Sync quizzes from Firestore"""
    quizzes_ref = db.collection('quizzes')
    docs = quizzes_ref.stream()

    total = inserted = updated = 0
    questions_synced = 0

    for doc in docs:
        total += 1
        data = doc.to_dict()
        quiz_id = doc.id

        title = data.get('title', '') or quiz_id
        description = data.get('description', '') or ''
        subject = data.get('subject', '') or ''
        grade = str(data.get('grade', '')) or ''
        duration = data.get('duration', 0) or 0
        difficulty = data.get('difficulty', '') or ''
        quiz_type = data.get('type', '') or data.get('mode', '') or ''
        creator_name = data.get('creatorName', '') or ''
        question_count = data.get('questionCount', 0) or 0
        questions_list = data.get('questions', []) or []

        raw_json = json.dumps(data, ensure_ascii=False, default=str)

        cursor.execute('SELECT id FROM quizzes WHERE quiz_id = ?', (quiz_id,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE quizzes SET title=?, description=?, grade=?, subject=?,
                                   difficulty=?, quiz_type=?, creator_name=?,
                                   duration=?, total_questions=?, raw_json=?,
                                   updated_at=CURRENT_TIMESTAMP
                WHERE quiz_id = ?
            ''', (title, description, grade, subject, difficulty, quiz_type,
                  creator_name, duration, question_count, raw_json, quiz_id))
            updated += 1
        else:
            cursor.execute('''
                INSERT INTO quizzes (quiz_id, title, description, grade, subject,
                                    difficulty, quiz_type, creator_name, duration,
                                    total_questions, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, title, description, grade, subject, difficulty, quiz_type,
                  creator_name, duration, question_count, raw_json))
            inserted += 1

        for i, q in enumerate(questions_list):
            if not isinstance(q, dict):
                continue

            question_id = f"{quiz_id}_{q.get('id', i)}"

            topic = q.get('topic', '') or q.get('topic_name', '') or ''
            id_q = q.get('id_q', '') or q.get('question', '') or ''
            en_q = q.get('en_q', '') or q.get('question_en', '') or ''
            image = q.get('image') or ''
            options = q.get('options', []) or []
            ans_val = q.get('ans', 0)
            if isinstance(ans_val, list) and len(ans_val) > 0:
                ans = int(ans_val[0])
            else:
                ans = int(ans_val or 0)
            id_exp = q.get('id_exp', '') or ''
            en_exp = q.get('en_exp', '') or ''

            options_json = json.dumps(options) if isinstance(options, list) else str(options)

            cursor.execute('''
                INSERT OR REPLACE INTO questions (question_id, quiz_id, topic,
                                                  id_q, en_q, image, options, ans,
                                                  id_exp, en_exp, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (question_id, quiz_id, topic, id_q, en_q, image,
                  options_json, ans, id_exp, en_exp, 'firestore'))
            questions_synced += 1

        if total % 50 == 0:
            conn.commit()
            logger.info(f"Progress: {total} quizzes, {questions_synced} questions...")

    conn.commit()
    return total, inserted, updated, questions_synced


def main():
    cred_path = Path(__file__).parent / "DATA_HOUSE_EZRALMS" / "firebase_credentials.json"
    if not cred_path.exists():
        logger.error(f"Credentials not found: {cred_path}")
        return

    cred = credentials.Certificate(str(cred_path))
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from data_house import DataHouse

    dh = DataHouse()
    dh.initialize_database()

    conn = dh.connect()
    cursor = conn.cursor()

    logger.info("Syncing quizzes from Firebase...")
    logger.info("=" * 60)

    total, inserted, updated, questions_synced = sync_quizzes(db, cursor, conn)

    logger.info("=" * 60)
    logger.info("Sync COMPLETE!")
    logger.info(f"  Quizzes processed: {total}")
    logger.info(f"  Inserted: {inserted}")
    logger.info(f"  Updated: {updated}")
    logger.info(f"  Questions synced: {questions_synced}")

    cursor.execute('SELECT COUNT(*) FROM quizzes')
    logger.info(f"  Total quizzes in DB: {cursor.fetchone()[0]}")

    cursor.execute('SELECT COUNT(*) FROM questions')
    logger.info(f"  Total questions in DB: {cursor.fetchone()[0]}")

    dh.close()


if __name__ == '__main__':
    main()
