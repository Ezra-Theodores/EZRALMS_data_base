"""
Sync ALL collections from Firebase Firestore to DATA_HOUSE
Collections: quizzes, topics, subtopics, classes, users, sessions, packages,
student_packages, package_sessions, quiz_attempts, student_activities, tasks,
task_assignments, xp_transactions, league_cohorts, games, notifications, etc.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import logging
import sqlite3
from pathlib import Path
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_tables(cursor):
    """Create all tables for Firebase collections"""

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
            duration INTEGER DEFAULT 0,
            total_questions INTEGER DEFAULT 0,
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
            ans INTEGER DEFAULT 0,
            id_exp TEXT,
            en_exp TEXT,
            source TEXT DEFAULT 'firestore',
            FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id TEXT UNIQUE,
            name TEXT,
            class_id TEXT,
            class_name TEXT,
            grade TEXT,
            subject TEXT,
            order_index INTEGER DEFAULT 0,
            topic_type TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classwork_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id TEXT UNIQUE,
            name TEXT,
            class_id TEXT,
            class_name TEXT,
            grade TEXT,
            subject TEXT,
            order_index INTEGER DEFAULT 0,
            topic_type TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classwork_subtopics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subtopic_id TEXT UNIQUE,
            topic_id TEXT,
            name TEXT,
            class_id TEXT,
            class_name TEXT,
            title TEXT,
            order_index INTEGER DEFAULT 0,
            subtopic_type TEXT,
            content TEXT,
            raw_json TEXT,
            source_file TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id TEXT UNIQUE,
            name TEXT,
            grade TEXT,
            subject TEXT,
            curriculum TEXT,
            teacher_name TEXT,
            schedule TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            role TEXT,
            phone TEXT,
            avatar_url TEXT,
            xp INTEGER DEFAULT 0,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            user_id TEXT,
            class_id TEXT,
            name TEXT,
            subject TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_id TEXT UNIQUE,
            name TEXT,
            description TEXT,
            grade TEXT,
            subject TEXT,
            price INTEGER DEFAULT 0,
            session_count INTEGER DEFAULT 0,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_package_id TEXT UNIQUE,
            student_id TEXT,
            package_id TEXT,
            start_date TEXT,
            end_date TEXT,
            sessions_remaining INTEGER DEFAULT 0,
            status TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS package_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package_session_id TEXT UNIQUE,
            student_package_id TEXT,
            session_id TEXT,
            status TEXT,
            completed_at TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            attempt_id TEXT UNIQUE,
            quiz_id TEXT,
            student_id TEXT,
            student_name TEXT,
            score INTEGER DEFAULT 0,
            max_score INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            answers TEXT,
            started_at TEXT,
            completed_at TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id TEXT UNIQUE,
            student_id TEXT,
            activity_type TEXT,
            title TEXT,
            xp_earned INTEGER DEFAULT 0,
            description TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE,
            title TEXT,
            description TEXT,
            due_date TEXT,
            assigned_to TEXT,
            status TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id TEXT UNIQUE,
            task_id TEXT,
            student_id TEXT,
            status TEXT,
            submitted_at TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS xp_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE,
            user_id TEXT,
            amount INTEGER DEFAULT 0,
            transaction_type TEXT,
            description TEXT,
            source TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS league_cohorts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cohort_id TEXT UNIQUE,
            name TEXT,
            start_date TEXT,
            end_date TEXT,
            status TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT UNIQUE,
            name TEXT,
            game_type TEXT,
            description TEXT,
            rules TEXT,
            raw_json TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS weekly_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id TEXT UNIQUE,
            student_id TEXT,
            student_name TEXT,
            week TEXT,
            xp_earned INTEGER DEFAULT 0,
            achievements TEXT,
            raw_json TEXT,
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
            raw_json TEXT,
            sync_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            collection TEXT,
            operation TEXT,
            records_processed INTEGER DEFAULT 0,
            records_inserted INTEGER DEFAULT 0,
            records_updated INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    ''')

    for table in ['quizzes', 'questions', 'topics', 'classwork_topics', 'classwork_subtopics',
                 'classes', 'users', 'sessions', 'packages', 'student_packages',
                 'package_sessions', 'quiz_attempts', 'student_activities', 'tasks',
                 'task_assignments', 'xp_transactions', 'league_cohorts', 'games',
                 'weekly_achievements', 'attendance']:
        try:
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{table}_id ON {table}(id)')
        except sqlite3.OperationalError:
            pass


def safe_value(val):
    """Convert value to safe SQLite type"""
    if val is None:
        return ''
    if isinstance(val, (datetime,)):
        return val.isoformat() if hasattr(val, 'isoformat') else str(val)
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False, default=str)
    if isinstance(val, bool):
        return '1' if val else '0'
    if isinstance(val, (int, float)):
        return val
    return str(val) if val else ''


def sync_collection(db, cursor, conn, collection_name, table_name, field_mapping, batch_size=100):
    """Generic sync for a collection"""
    total = inserted = updated = errors = 0
    docs_ref = db.collection(collection_name)
    docs = docs_ref.stream()

    for doc in docs:
        total += 1
        data = doc.to_dict()
        doc_id = doc.id

        fields = {}
        raw_data = {}

        for fb_field, db_field in field_mapping.items():
            val = safe_value(data.get(fb_field, ''))
            fields[db_field] = val
            raw_data[db_field] = val

        try:
            raw_json = json.dumps(data, ensure_ascii=False, default=str)

            cursor.execute(f'PRAGMA table_info({table_name})')
            columns = [row[1] for row in cursor.fetchall()]

            available_fields = {k: v for k, v in fields.items() if k in columns}
            if 'raw_json' in columns:
                available_fields['raw_json'] = raw_json

            placeholders = ', '.join(['?'] * len(available_fields))
            columns_list = ', '.join(available_fields.keys())
            values = list(available_fields.values())

            cursor.execute(f'''
                INSERT OR REPLACE INTO {table_name} ({columns_list})
                VALUES ({placeholders})
            ''', values)
            inserted += 1

        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.error(f"Error syncing {doc_id}: {e}")

        if total % batch_size == 0:
            conn.commit()
            logger.info(f"  {collection_name}: {total} docs...")

    conn.commit()
    return total, inserted, updated, errors


def sync_quizzes_questions(db, cursor, conn):
    """Special sync for quizzes with nested questions"""
    total = inserted = updated = errors = questions_synced = 0
    quizzes_ref = db.collection('quizzes')
    docs = quizzes_ref.stream()

    for doc in docs:
        total += 1
        data = doc.to_dict()
        quiz_id = doc.id

        title = data.get('title', '') or quiz_id
        description = data.get('description', '') or ''
        subject = data.get('subject', '') or ''
        grade = str(data.get('grade', '')) or ''
        difficulty = data.get('difficulty', '') or ''
        quiz_type = data.get('type', '') or data.get('mode', '') or ''
        creator_name = data.get('creatorName', '') or ''
        duration = data.get('duration', 0) or 0
        question_count = data.get('questionCount', 0) or 0
        questions_list = data.get('questions', []) or []
        raw_json = json.dumps(data, ensure_ascii=False, default=str)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO quizzes (quiz_id, title, description, grade, subject,
                                              difficulty, quiz_type, creator_name, duration,
                                              total_questions, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_id, title, description, grade, subject, difficulty, quiz_type,
                  creator_name, duration, question_count, raw_json))
            inserted += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.error(f"Quiz error: {e}")

        for i, q in enumerate(questions_list):
            if not isinstance(q, dict):
                continue

            question_id = f"{quiz_id}_{q.get('id', i)}"
            topic = q.get('topic', '') or ''
            id_q = q.get('id_q', '') or ''
            en_q = q.get('en_q', '') or ''
            image = q.get('image') or ''
            options = q.get('options', []) or []
            ans_val = q.get('ans', 0)
            if isinstance(ans_val, list):
                ans = int(ans_val[0]) if ans_val else 0
            else:
                ans = int(ans_val or 0)
            id_exp = q.get('id_exp', '') or ''
            en_exp = q.get('en_exp', '') or ''
            options_json = json.dumps(options) if isinstance(options, list) else str(options)

            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO questions (question_id, quiz_id, topic,
                                                      id_q, en_q, image, options, ans,
                                                      id_exp, en_exp, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (question_id, quiz_id, topic, id_q, en_q, image,
                      options_json, ans, id_exp, en_exp, 'firestore'))
                questions_synced += 1
            except Exception as e:
                pass

        if total % 50 == 0:
            conn.commit()
            logger.info(f"  quizzes: {total} quizzes, {questions_synced} questions...")

    conn.commit()
    return total, inserted, updated, errors, questions_synced


def sync_topics_subtopics(db, cursor, conn):
    """Sync topics and subtopics"""
    topics_total = topics_inserted = topics_errors = 0
    subtopics_total = subtopics_inserted = subtopics_errors = 0

    topics_ref = db.collection('topics')
    for doc in topics_ref.stream():
        topics_total += 1
        data = doc.to_dict()
        doc_id = doc.id
        raw_json = json.dumps(data, ensure_ascii=False, default=str)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO topics (topic_id, name, grade, subject, raw_json)
                VALUES (?, ?, ?, ?, ?)
            ''', (doc_id, data.get('name', '') or data.get('title', ''),
                  data.get('grade', ''), data.get('subject', ''), raw_json))
            topics_inserted += 1
        except Exception as e:
            topics_errors += 1

    topics_ref2 = db.collection('classworkTopics')
    for doc in topics_ref2.stream():
        topics_total += 1
        data = doc.to_dict()
        doc_id = doc.id
        raw_json = json.dumps(data, ensure_ascii=False, default=str)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO classwork_topics (topic_id, name, class_id, class_name,
                                                        grade, subject, order_index, topic_type, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_id,
                  safe_value(data.get('name', '')) or safe_value(data.get('title', '')),
                  safe_value(data.get('classId', '')),
                  safe_value(data.get('className', '')),
                  safe_value(data.get('grade', '')),
                  safe_value(data.get('subject', '')),
                  int(safe_value(data.get('order', 0))),
                  safe_value(data.get('type', '')) or safe_value(data.get('topicType', '')),
                  raw_json))
            topics_inserted += 1
        except Exception as e:
            topics_errors += 1

    conn.commit()

    subtopics_ref = db.collection('classworkSubtopics')
    for doc in subtopics_ref.stream():
        subtopics_total += 1
        data = doc.to_dict()
        doc_id = doc.id
        raw_json = json.dumps(data, ensure_ascii=False, default=str)

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO classwork_subtopics (subtopic_id, topic_id, name, class_id,
                                                          class_name, title, order_index, subtopic_type,
                                                          content, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (doc_id,
                  safe_value(data.get('topicId', '')),
                  safe_value(data.get('name', '')) or safe_value(data.get('topicName', '')),
                  safe_value(data.get('classId', '')),
                  safe_value(data.get('className', '')),
                  safe_value(data.get('title', '')),
                  int(safe_value(data.get('order', 0))),
                  safe_value(data.get('type', '')) or safe_value(data.get('subtopicType', '')),
                  safe_value(data.get('content', '')) or safe_value(data.get('text', '')),
                  raw_json))
            subtopics_inserted += 1
        except Exception as e:
            subtopics_errors += 1

    conn.commit()
    return topics_total, topics_inserted, topics_errors, subtopics_total, subtopics_inserted, subtopics_errors


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

    create_tables(cursor)
    conn.commit()
    conn.commit()

    logger.info("=" * 70)
    logger.info("SYNCING ALL COLLECTIONS FROM FIREBASE")
    logger.info("=" * 70)

    grand_total = 0
    grand_inserted = 0
    grand_updated = 0
    grand_errors = 0

    logger.info("\n[1/15] Syncing quizzes + questions...")
    total, inserted, updated, errors, questions = sync_quizzes_questions(db, cursor, conn)
    logger.info(f"  Done: {total} quizzes, {questions} questions")
    grand_total += total
    grand_inserted += inserted

    logger.info("\n[2/15] Syncing topics + subtopics...")
    t_total, t_ins, t_err, s_total, s_ins, s_err = sync_topics_subtopics(db, cursor, conn)
    logger.info(f"  Done: {t_total} topics, {s_total} subtopics")
    grand_total += t_total + s_total
    grand_inserted += t_ins + s_ins

    logger.info("\n[3/15] Syncing classes...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'classes', 'classes', {
        'name': 'name', 'grade': 'grade', 'subject': 'subject',
        'curriculum': 'curriculum', 'teacherName': 'teacher_name'
    })
    logger.info(f"  Done: {total} classes")
    grand_total += total

    logger.info("\n[4/15] Syncing users...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'users', 'users', {
        'name': 'name', 'email': 'email', 'role': 'role',
        'phone': 'phone', 'avatarUrl': 'avatar_url', 'xp': 'xp'
    })
    logger.info(f"  Done: {total} users")
    grand_total += total

    logger.info("\n[5/15] Syncing sessions...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'sessions', 'sessions', {
        'userId': 'user_id', 'classId': 'class_id', 'name': 'name',
        'subject': 'subject', 'startTime': 'start_time', 'endTime': 'end_time',
        'status': 'status'
    })
    logger.info(f"  Done: {total} sessions")
    grand_total += total

    logger.info("\n[6/15] Syncing packages...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'packages', 'packages', {
        'name': 'name', 'description': 'description', 'grade': 'grade',
        'subject': 'subject', 'price': 'price', 'sessionCount': 'session_count'
    })
    logger.info(f"  Done: {total} packages")
    grand_total += total

    logger.info("\n[7/15] Syncing student_packages...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'student_packages', 'student_packages', {
        'studentId': 'student_id', 'packageId': 'package_id',
        'startDate': 'start_date', 'endDate': 'end_date',
        'sessionsRemaining': 'sessions_remaining', 'status': 'status'
    })
    logger.info(f"  Done: {total} student_packages")
    grand_total += total

    logger.info("\n[8/15] Syncing package_sessions...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'package_sessions', 'package_sessions', {
        'studentPackageId': 'student_package_id', 'sessionId': 'session_id',
        'status': 'status', 'completedAt': 'completed_at'
    })
    logger.info(f"  Done: {total} package_sessions")
    grand_total += total

    logger.info("\n[9/15] Syncing quiz_attempts...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'quiz_attempts', 'quiz_attempts', {
        'quizId': 'quiz_id', 'studentId': 'student_id', 'studentName': 'student_name',
        'score': 'score', 'maxScore': 'max_score', 'duration': 'duration',
        'answers': 'answers', 'startedAt': 'started_at', 'completedAt': 'completed_at'
    })
    logger.info(f"  Done: {total} quiz_attempts")
    grand_total += total

    logger.info("\n[10/15] Syncing student_activities...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'student_activities', 'student_activities', {
        'studentId': 'student_id', 'type': 'activity_type', 'title': 'title',
        'xpEarned': 'xp_earned', 'description': 'description'
    })
    logger.info(f"  Done: {total} activities")
    grand_total += total

    logger.info("\n[11/15] Syncing tasks...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'tasks', 'tasks', {
        'title': 'title', 'description': 'description', 'dueDate': 'due_date',
        'assignedTo': 'assigned_to', 'status': 'status'
    })
    logger.info(f"  Done: {total} tasks")
    grand_total += total

    logger.info("\n[12/15] Syncing task_assignments...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'task_assignments', 'task_assignments', {
        'taskId': 'task_id', 'studentId': 'student_id', 'status': 'status',
        'submittedAt': 'submitted_at'
    })
    logger.info(f"  Done: {total} assignments")
    grand_total += total

    logger.info("\n[13/15] Syncing xp_transactions...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'xp_transactions', 'xp_transactions', {
        'userId': 'user_id', 'amount': 'amount', 'type': 'transaction_type',
        'description': 'description', 'source': 'source'
    })
    logger.info(f"  Done: {total} transactions")
    grand_total += total

    logger.info("\n[14/15] Syncing games + league_cohorts...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'games', 'games', {
        'name': 'name', 'type': 'game_type', 'description': 'description', 'rules': 'rules'
    })
    logger.info(f"  Done: {total} games")
    grand_total += total

    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'league_cohorts', 'league_cohorts', {
        'name': 'name', 'startDate': 'start_date', 'endDate': 'end_date', 'status': 'status'
    })
    logger.info(f"  Done: {total} cohorts")

    logger.info("\n[15/15] Syncing weekly_achievements...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'weekly_achievements', 'weekly_achievements', {
        'studentId': 'student_id', 'studentName': 'student_name', 'week': 'week',
        'xpEarned': 'xp_earned', 'achievements': 'achievements'
    })
    logger.info(f"  Done: {total} achievements")
    grand_total += total

    logger.info("\n[+] Syncing attendance...")
    total, inserted, updated, errors = sync_collection(db, cursor, conn, 'attendance', 'attendance', {
        'studentId': 'student_id', 'studentName': 'student_name', 'classId': 'class_id',
        'className': 'class_name', 'date': 'attendance_date', 'status': 'status',
        'checkInTime': 'check_in_time', 'checkOutTime': 'check_out_time', 'notes': 'notes'
    })
    logger.info(f"  Done: {total} attendance records")
    grand_total += total

    logger.info("\n" + "=" * 70)
    logger.info("SYNC COMPLETE!")
    logger.info("=" * 70)

    cursor.execute('SELECT COUNT(*) FROM quizzes')
    quizzes_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM questions')
    questions_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM topics')
    topics_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM classwork_topics')
    cw_topics_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM classwork_subtopics')
    cw_subtopics_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM classes')
    classes_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM sessions')
    sessions_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM packages')
    packages_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM student_packages')
    student_packages_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM package_sessions')
    package_sessions_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM quiz_attempts')
    quiz_attempts_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM student_activities')
    activities_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM tasks')
    tasks_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM task_assignments')
    assignments_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM xp_transactions')
    xp_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM games')
    games_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM league_cohorts')
    cohorts_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM weekly_achievements')
    achievements_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM attendance')
    attendance_count = cursor.fetchone()[0]

    logger.info(f"  quizzes:          {quizzes_count}")
    logger.info(f"  questions:         {questions_count}")
    logger.info(f"  topics:            {topics_count}")
    logger.info(f"  classwork_topics: {cw_topics_count}")
    logger.info(f"  classwork_sub:    {cw_subtopics_count}")
    logger.info(f"  classes:           {classes_count}")
    logger.info(f"  users:             {users_count}")
    logger.info(f"  sessions:          {sessions_count}")
    logger.info(f"  packages:          {packages_count}")
    logger.info(f"  student_packages: {student_packages_count}")
    logger.info(f"  package_sessions: {package_sessions_count}")
    logger.info(f"  quiz_attempts:     {quiz_attempts_count}")
    logger.info(f"  activities:       {activities_count}")
    logger.info(f"  tasks:             {tasks_count}")
    logger.info(f"  assignments:      {assignments_count}")
    logger.info(f"  xp_transactions:   {xp_count}")
    logger.info(f"  games:             {games_count}")
    logger.info(f"  cohorts:           {cohorts_count}")
    logger.info(f"  achievements:     {achievements_count}")
    logger.info(f"  attendance:       {attendance_count}")

    dh.close()


if __name__ == '__main__':
    main()
