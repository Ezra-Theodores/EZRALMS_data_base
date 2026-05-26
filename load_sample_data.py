#!/usr/bin/env python3
"""
Load sample data into EZRA LMS database for testing
"""

import sqlite3
import os

DB_PATH = "./ezralms_complete.db"

def init_db():
    """Initialize database with tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'teacher', 'admin', 'parent')),
            grade_level INTEGER,
            class_id TEXT,
            phone TEXT,
            address TEXT,
            profile_image TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT
        )
    """)

    # Grades table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            grade_id TEXT UNIQUE NOT NULL,
            grade_number INTEGER NOT NULL,
            grade_name TEXT NOT NULL,
            description TEXT,
            curriculum_type TEXT DEFAULT 'national_plus',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Classes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_id TEXT UNIQUE NOT NULL,
            grade_id TEXT NOT NULL,
            class_name TEXT NOT NULL,
            class_code TEXT,
            section TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (grade_id) REFERENCES grades(grade_id)
        )
    """)

    # Topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id TEXT UNIQUE NOT NULL,
            class_id TEXT NOT NULL,
            topic_name TEXT NOT NULL,
            description TEXT,
            order_index INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        )
    """)

    # Sub-topics table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sub_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub_topic_id TEXT UNIQUE NOT NULL,
            topic_id TEXT NOT NULL,
            sub_topic_name TEXT NOT NULL,
            description TEXT,
            order_index INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id)
        )
    """)

    # Materials table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id TEXT UNIQUE NOT NULL,
            sub_topic_id TEXT NOT NULL,
            material_title TEXT NOT NULL,
            material_type TEXT NOT NULL,
            description TEXT,
            file_path TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sub_topic_id) REFERENCES sub_topics(sub_topic_id)
        )
    """)

    # Quizzes table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quizzes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quiz_id TEXT UNIQUE NOT NULL,
            sub_topic_id TEXT NOT NULL,
            quiz_title TEXT NOT NULL,
            description TEXT,
            difficulty TEXT,
            passing_score REAL,
            time_limit INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sub_topic_id) REFERENCES sub_topics(sub_topic_id)
        )
    """)

    # Quiz questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE NOT NULL,
            quiz_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT,
            options TEXT,
            correct_answer TEXT,
            explanation TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
        )
    """)

    conn.commit()
    print("[OK] Tables created/verified")

    # Clear existing data
    cursor.execute("DELETE FROM quiz_questions")
    cursor.execute("DELETE FROM quizzes")
    cursor.execute("DELETE FROM materials")
    cursor.execute("DELETE FROM sub_topics")
    cursor.execute("DELETE FROM topics")
    cursor.execute("DELETE FROM classes")
    cursor.execute("DELETE FROM grades")
    cursor.execute("DELETE FROM users")
    conn.commit()
    print("[OK] Cleared existing data")

    # Add sample grades
    grades = [
        ('G1', 1, 'Grade 1', 'First Grade'),
        ('G2', 2, 'Grade 2', 'Second Grade'),
        ('G3', 3, 'Grade 3', 'Third Grade'),
        ('G4', 4, 'Grade 4', 'Fourth Grade'),
        ('G5', 5, 'Grade 5', 'Fifth Grade'),
        ('G6', 6, 'Grade 6', 'Sixth Grade'),
        ('G7', 7, 'Grade 7', 'Seventh Grade'),
        ('G8', 8, 'Grade 8', 'Eighth Grade'),
        ('G9', 9, 'Grade 9', 'Ninth Grade'),
        ('G10', 10, 'Grade 10', 'Tenth Grade'),
        ('G11', 11, 'Grade 11', 'Eleventh Grade'),
        ('G12', 12, 'Grade 12', 'Twelfth Grade'),
    ]
    cursor.executemany(
        "INSERT INTO grades (grade_id, grade_number, grade_name, description) VALUES (?, ?, ?, ?)",
        grades
    )
    print(f"[OK] Added {len(grades)} grades")

    # Add sample classes
    classes = []
    for i in range(1, 13):
        grade_id = f'G{i}'
        for section in ['A', 'B', 'C']:
            class_id = f'C{i}{section}'
            class_name = f'Class {i}{section}'
            classes.append((class_id, grade_id, class_name, f'{i}{section}', section))

    cursor.executemany(
        "INSERT INTO classes (class_id, grade_id, class_name, class_code, section) VALUES (?, ?, ?, ?, ?)",
        classes
    )
    print(f"[OK] Added {len(classes)} classes")

    # Add sample topics
    topics = []
    topic_count = 0
    for class_id in [c[0] for c in classes[:3]]:  # Sample for first 3 classes
        for t in range(1, 6):
            topic_id = f'T{class_id}_{t}'
            topic_name = f'{class_id} Topic {t}'
            topics.append((topic_id, class_id, topic_name, f'Description for {topic_name}', t))
            topic_count += 1

    cursor.executemany(
        "INSERT INTO topics (topic_id, class_id, topic_name, description, order_index) VALUES (?, ?, ?, ?, ?)",
        topics
    )
    print(f"[OK] Added {len(topics)} topics")

    # Add sample sub-topics
    sub_topics = []
    sub_topic_count = 0
    for topic_id in [t[0] for t in topics[:5]]:  # Sample for first 5 topics
        for st in range(1, 4):
            sub_topic_id = f'ST{topic_id}_{st}'
            sub_topic_name = f'{topic_id} Sub-Topic {st}'
            sub_topics.append((sub_topic_id, topic_id, sub_topic_name, f'Description for {sub_topic_name}', st))
            sub_topic_count += 1

    cursor.executemany(
        "INSERT INTO sub_topics (sub_topic_id, topic_id, sub_topic_name, description, order_index) VALUES (?, ?, ?, ?, ?)",
        sub_topics
    )
    print(f"[OK] Added {len(sub_topics)} sub-topics")

    # Add sample materials
    materials = []
    material_types = ['PDF', 'Video', 'Interactive', 'Document']
    for sub_topic_id in [st[0] for st in sub_topics[:8]]:
        for m in range(1, 3):
            material_id = f'M{sub_topic_id}_{m}'
            material_type = material_types[(m-1) % len(material_types)]
            materials.append((
                material_id, sub_topic_id, f'{sub_topic_id} Material {m}',
                material_type, f'Description for material {m}', f'/files/{material_id}'
            ))

    cursor.executemany(
        "INSERT INTO materials (material_id, sub_topic_id, material_title, material_type, description, file_path) VALUES (?, ?, ?, ?, ?, ?)",
        materials
    )
    print(f"[OK] Added {len(materials)} materials")

    # Add sample quizzes
    quizzes = []
    difficulties = ['Easy', 'Medium', 'Hard']
    for sub_topic_id in [st[0] for st in sub_topics[:10]]:
        quiz_id = f'Q{sub_topic_id}'
        difficulty = difficulties[len(quizzes) % len(difficulties)]
        quizzes.append((
            quiz_id, sub_topic_id, f'{sub_topic_id} Quiz',
            f'Quiz for {sub_topic_id}', difficulty, 70, 30
        ))

    cursor.executemany(
        "INSERT INTO quizzes (quiz_id, sub_topic_id, quiz_title, description, difficulty, passing_score, time_limit) VALUES (?, ?, ?, ?, ?, ?, ?)",
        quizzes
    )
    print(f"[OK] Added {len(quizzes)} quizzes")

    # Add sample quiz questions
    questions = []
    question_count = 0
    for quiz_id in [q[0] for q in quizzes]:
        for q in range(1, 11):
            question_id = f'QN{quiz_id}_{q}'
            options = '["Option A", "Option B", "Option C", "Option D"]'
            questions.append((
                question_id, quiz_id, f'Question {q} for {quiz_id}',
                'multiple_choice', options, 'Option A', f'Explanation for question {q}'
            ))
            question_count += 1

    cursor.executemany(
        "INSERT INTO quiz_questions (question_id, quiz_id, question_text, question_type, options, correct_answer, explanation) VALUES (?, ?, ?, ?, ?, ?, ?)",
        questions
    )
    print(f"[OK] Added {len(questions)} quiz questions")

    # Add sample users
    users = [
        ('U1', 'admin@ezra.local', 'Admin User', 'admin', None, None, '555-0001', 'Admin Address'),
        ('U2', 'teacher1@ezra.local', 'Mrs. Smith', 'teacher', None, 'C1A', '555-0002', 'Teacher Address 1'),
        ('U3', 'teacher2@ezra.local', 'Mr. Johnson', 'teacher', None, 'C2B', '555-0003', 'Teacher Address 2'),
    ]

    # Add 30 sample students
    for i in range(1, 31):
        grade = (i % 12) + 1
        class_section = chr(65 + (i % 3))  # A, B, or C
        class_id = f'C{grade}{class_section}'
        users.append((
            f'S{i}', f'student{i}@ezra.local', f'Student {i}', 'student',
            grade, class_id, f'555-{1000+i}', f'Student Address {i}'
        ))

    cursor.executemany(
        "INSERT INTO users (user_id, email, full_name, role, grade_level, class_id, phone, address) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        users
    )
    print(f"[OK] Added {len(users)} users")

    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print("[REPORT] SAMPLE DATA LOADED SUCCESSFULLY!")
    print("="*50)
    print(f"[*] Users: {len(users)}")
    print(f"[*] Grades: {len(grades)}")
    print(f"[*] Classes: {len(classes)}")
    print(f"[*] Topics: {len(topics)}")
    print(f"[*] Sub-Topics: {len(sub_topics)}")
    print(f"[*] Materials: {len(materials)}")
    print(f"[*] Quizzes: {len(quizzes)}")
    print(f"[*] Quiz Questions: {len(questions)}")
    print("="*50)

if __name__ == "__main__":
    init_db()
