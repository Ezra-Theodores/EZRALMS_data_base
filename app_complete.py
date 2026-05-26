#!/usr/bin/env python3
"""
EZRA LMS - Complete Web UI for Users & Curriculum Management
===============================================================

Comprehensive Flask application for managing:
- Users (Students, Teachers, Admins)
- Curriculum Structure:
  - Grades (1-12)
  - Classes
  - Topics
  - Sub-topics
  - Materials
  - Quizzes

Usage:
    python app_complete.py

Then open browser to: http://localhost:5005
"""

import os
import sqlite3
import json
import logging
try:
    import mysql.connector
except ImportError:
    mysql = None
from flask import Flask, render_template, request, jsonify, g, send_from_directory
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Database configuration
DB_PATH = os.getenv("DB_PATH", "./ezralms_complete.db")
DATA_HOUSE = "./DATA_HOUSE_EZRALMS"

# Ensure DATA_HOUSE directory exists
os.makedirs(DATA_HOUSE, exist_ok=True)


def get_db():
    """Get database connection."""
    if 'db' not in g:
        absolute_db_path = os.path.abspath(DB_PATH)
        g.db = sqlite3.connect(absolute_db_path)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with all tables."""
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
            class_name TEXT NOT NULL,
            grade_id TEXT NOT NULL,
            teacher_id TEXT,
            room_number TEXT,
            schedule TEXT,
            max_students INTEGER DEFAULT 30,
            academic_year TEXT,
            is_active BOOLEAN DEFAULT 1,
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
            topic_name TEXT NOT NULL,
            class_id TEXT NOT NULL,
            description TEXT,
            learning_objectives TEXT,
            estimated_hours INTEGER,
            sequence_order INTEGER,
            prerequisites TEXT,
            is_active BOOLEAN DEFAULT 1,
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
            sub_topic_name TEXT NOT NULL,
            topic_id TEXT NOT NULL,
            description TEXT,
            content_summary TEXT,
            estimated_minutes INTEGER,
            sequence_order INTEGER,
            resources_needed TEXT,
            is_active BOOLEAN DEFAULT 1,
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
            material_title TEXT NOT NULL,
            sub_topic_id TEXT NOT NULL,
            material_type TEXT NOT NULL CHECK(material_type IN ('video', 'document', 'presentation', 'pdf', 'image', 'audio', 'link', 'interactive')),
            content_url TEXT,
            file_path TEXT,
            description TEXT,
            duration_seconds INTEGER,
            file_size_mb REAL,
            download_allowed BOOLEAN DEFAULT 1,
            sequence_order INTEGER,
            is_active BOOLEAN DEFAULT 1,
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
            quiz_title TEXT NOT NULL,
            sub_topic_id TEXT,
            topic_id TEXT,
            class_id TEXT,
            quiz_type TEXT DEFAULT 'multiple_choice' CHECK(quiz_type IN ('multiple_choice', 'true_false', 'fill_blank', 'essay', 'mixed')),
            description TEXT,
            instructions TEXT,
            time_limit_minutes INTEGER,
            passing_score INTEGER DEFAULT 70,
            max_attempts INTEGER DEFAULT 1,
            shuffle_questions BOOLEAN DEFAULT 1,
            show_correct_answers BOOLEAN DEFAULT 1,
            is_published BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sub_topic_id) REFERENCES sub_topics(sub_topic_id),
            FOREIGN KEY (topic_id) REFERENCES topics(topic_id),
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        )
    """)

    # Quiz Questions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id TEXT UNIQUE NOT NULL,
            quiz_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            question_type TEXT DEFAULT 'multiple_choice' CHECK(question_type IN ('multiple_choice', 'true_false', 'fill_blank', 'essay', 'matching')),
            options TEXT, -- JSON array of options
            correct_answer TEXT,
            explanation TEXT,
            points INTEGER DEFAULT 1,
            difficulty_level TEXT DEFAULT 'medium' CHECK(difficulty_level IN ('easy', 'medium', 'hard')),
            sequence_order INTEGER,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (quiz_id) REFERENCES quizzes(quiz_id)
        )
    """)

    # Create indexes for better performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_classes_grade ON classes(grade_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_topics_class ON topics(class_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_topics_topic ON sub_topics(topic_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_sub_topic ON materials(sub_topic_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quizzes_sub_topic ON quizzes(sub_topic_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_quiz_questions_quiz ON quiz_questions(quiz_id)")

    conn.commit()
    conn.close()
    print("[OK] Database initialized successfully!")


# Routes
@app.route('/')
def index():
    """Render main page — redirect to unified SPA running on port 5000."""
    from flask import redirect
    return redirect('http://localhost:5000/', code=302)


@app.route('/test')
def test():
    """Serve test page."""
    try:
        with open('test_dashboard_api.html', 'r') as f:
            return f.read()
    except:
        return "Test page not found", 404


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    try:
        db = get_db()
        cursor = db.cursor()

        stats = {}

        # Users by role
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            GROUP BY role
        """)
        stats['users_by_role'] = {row['role']: row['count'] for row in cursor.fetchall()}

        # Grades count
        cursor.execute("SELECT COUNT(*) as count FROM grades")
        stats['grades_count'] = cursor.fetchone()['count']

        # Classes count
        cursor.execute("SELECT COUNT(*) as count FROM classes")
        stats['classes_count'] = cursor.fetchone()['count']

        # Topics count
        cursor.execute("SELECT COUNT(*) as count FROM topics")
        stats['topics_count'] = cursor.fetchone()['count']

        # Sub-topics count
        cursor.execute("SELECT COUNT(*) as count FROM sub_topics")
        stats['sub_topics_count'] = cursor.fetchone()['count']

        # Materials count by type
        cursor.execute("""
            SELECT material_type, COUNT(*) as count
            FROM materials
            GROUP BY material_type
        """)
        stats['materials_by_type'] = {row['material_type']: row['count'] for row in cursor.fetchall()}

        # Quizzes count
        cursor.execute("SELECT COUNT(*) as count FROM quizzes")
        stats['quizzes_count'] = cursor.fetchone()['count']

        # Quiz questions count
        cursor.execute("SELECT COUNT(*) as count FROM quiz_questions")
        stats['questions_count'] = cursor.fetchone()['count']

        return jsonify({'success': True, 'data': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tree/<entity_type>')
def get_tree(entity_type):
    """Get hierarchical tree structure."""
    try:
        db = get_db()
        cursor = db.cursor()

        if entity_type == 'curriculum':
            # Get full curriculum tree
            tree = []

            # Get all grades
            cursor.execute("""
                SELECT grade_id, grade_number, grade_name, description
                FROM grades
                ORDER BY grade_number
            """)
            grades = cursor.fetchall()

            for grade in grades:
                grade_node = {
                    'id': grade['grade_id'],
                    'type': 'grade',
                    'number': grade['grade_number'],
                    'name': grade['grade_name'],
                    'description': grade['description'],
                    'children': []
                }

                # Get classes for this grade
                cursor.execute("""
                    SELECT class_id, class_name, teacher_id, room_number,
                           schedule, max_students, academic_year
                    FROM classes
                    WHERE grade_id = ? AND is_active = 1
                    ORDER BY class_name
                """, (grade['grade_id'],))
                classes = cursor.fetchall()

                for class_ in classes:
                    class_node = {
                        'id': class_['class_id'],
                        'type': 'class',
                        'name': class_['class_name'],
                        'teacher': class_['teacher_id'],
                        'room': class_['room_number'],
                        'schedule': class_['schedule'],
                        'max_students': class_['max_students'],
                        'academic_year': class_['academic_year'],
                        'children': []
                    }

                    # Get topics for this class
                    cursor.execute("""
                        SELECT topic_id, topic_name, description,
                               learning_objectives, estimated_hours
                        FROM topics
                        WHERE class_id = ? AND is_active = 1
                        ORDER BY sequence_order, topic_name
                    """, (class_['class_id'],))
                    topics = cursor.fetchall()

                    for topic in topics:
                        topic_node = {
                            'id': topic['topic_id'],
                            'type': 'topic',
                            'name': topic['topic_name'],
                            'description': topic['description'],
                            'learning_objectives': topic['learning_objectives'],
                            'estimated_hours': topic['estimated_hours'],
                            'children': []
                        }

                        # Get sub-topics for this topic
                        cursor.execute("""
                            SELECT sub_topic_id, sub_topic_name, description,
                                   content_summary, estimated_minutes
                            FROM sub_topics
                            WHERE topic_id = ? AND is_active = 1
                            ORDER BY sequence_order, sub_topic_name
                        """, (topic['topic_id'],))
                        sub_topics = cursor.fetchall()

                        for sub_topic in sub_topics:
                            sub_topic_node = {
                                'id': sub_topic['sub_topic_id'],
                                'type': 'sub_topic',
                                'name': sub_topic['sub_topic_name'],
                                'description': sub_topic['description'],
                                'content_summary': sub_topic['content_summary'],
                                'estimated_minutes': sub_topic['estimated_minutes'],
                                'children': []
                            }

                            # Get materials for this sub-topic
                            cursor.execute("""
                                SELECT material_id, material_title, material_type,
                                       content_url, description, duration_seconds
                                FROM materials
                                WHERE sub_topic_id = ? AND is_active = 1
                                ORDER BY sequence_order, material_title
                            """, (sub_topic['sub_topic_id'],))
                            materials = cursor.fetchall()

                            for material in materials:
                                sub_topic_node['children'].append({
                                    'id': material['material_id'],
                                    'type': 'material',
                                    'title': material['material_title'],
                                    'material_type': material['material_type'],
                                    'content_url': material['content_url'],
                                    'description': material['description'],
                                    'duration_seconds': material['duration_seconds']
                                })

                            # Get quizzes for this sub-topic
                            cursor.execute("""
                                SELECT quiz_id, quiz_title, quiz_type,
                                       description, time_limit_minutes, passing_score
                                FROM quizzes
                                WHERE sub_topic_id = ? AND is_published = 1 AND is_active = 1
                                ORDER BY created_at
                            """, (sub_topic['sub_topic_id'],))
                            quizzes = cursor.fetchall()

                            for quiz in quizzes:
                                sub_topic_node['children'].append({
                                    'id': quiz['quiz_id'],
                                    'type': 'quiz',
                                    'title': quiz['quiz_title'],
                                    'quiz_type': quiz['quiz_type'],
                                    'description': quiz['description'],
                                    'time_limit_minutes': quiz['time_limit_minutes'],
                                    'passing_score': quiz['passing_score']
                                })

                            topic_node['children'].append(sub_topic_node)

                        class_node['children'].append(topic_node)

                    grade_node['children'].append(class_node)

                tree.append(grade_node)

            return jsonify({'success': True, 'data': tree})

        elif entity_type == 'users':
            # Get all users with optional filtering
            role = request.args.get('role')
            grade = request.args.get('grade')
            search = request.args.get('search')

            query = "SELECT * FROM users WHERE 1=1"
            params = []

            if role:
                query += " AND role = ?"
                params.append(role)
            if grade:
                query += " AND grade_level = ?"
                params.append(grade)
            if search:
                query += " AND (full_name LIKE ? OR email LIKE ? OR user_id LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            query += " ORDER BY full_name"

            cursor.execute(query, params)
            users = cursor.fetchall()

            return jsonify({
                'success': True,
                'count': len(users),
                'data': [dict(user) for user in users]
            })

        else:
            return jsonify({'success': False, 'error': 'Invalid entity type'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# CRUD Operations

@app.route('/api/<entity_type>', methods=['POST'])
def create_entity(entity_type):
    """Create new entity."""
    try:
        data = request.json
        db = get_db()
        cursor = db.cursor()

        if entity_type == 'user':
            cursor.execute("""
                INSERT INTO users (user_id, email, full_name, role, grade_level, class_id, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('user_id'), data.get('email'), data.get('full_name'),
                data.get('role'), data.get('grade_level'), data.get('class_id'),
                data.get('phone'), data.get('address')
            ))

        elif entity_type == 'grade':
            cursor.execute("""
                INSERT INTO grades (grade_id, grade_number, grade_name, description, curriculum_type)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data.get('grade_id'), data.get('grade_number'), data.get('grade_name'),
                data.get('description'), data.get('curriculum_type', 'national_plus')
            ))

        elif entity_type == 'class':
            cursor.execute("""
                INSERT INTO classes (class_id, class_name, grade_id, teacher_id, room_number, schedule, max_students, academic_year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('class_id'), data.get('class_name'), data.get('grade_id'),
                data.get('teacher_id'), data.get('room_number'), data.get('schedule'),
                data.get('max_students', 30), data.get('academic_year')
            ))

        elif entity_type == 'topic':
            cursor.execute("""
                INSERT INTO topics (topic_id, topic_name, class_id, description, learning_objectives, estimated_hours, sequence_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('topic_id'), data.get('topic_name'), data.get('class_id'),
                data.get('description'), data.get('learning_objectives'),
                data.get('estimated_hours'), data.get('sequence_order', 0)
            ))

        elif entity_type == 'sub_topic':
            cursor.execute("""
                INSERT INTO sub_topics (sub_topic_id, sub_topic_name, topic_id, description, content_summary, estimated_minutes, sequence_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('sub_topic_id'), data.get('sub_topic_name'), data.get('topic_id'),
                data.get('description'), data.get('content_summary'),
                data.get('estimated_minutes'), data.get('sequence_order', 0)
            ))

        elif entity_type == 'material':
            cursor.execute("""
                INSERT INTO materials (material_id, material_title, sub_topic_id, material_type, content_url, file_path, description, duration_seconds, sequence_order)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('material_id'), data.get('material_title'), data.get('sub_topic_id'),
                data.get('material_type'), data.get('content_url'), data.get('file_path'),
                data.get('description'), data.get('duration_seconds'), data.get('sequence_order', 0)
            ))

        elif entity_type == 'quiz':
            cursor.execute("""
                INSERT INTO quizzes (quiz_id, quiz_title, sub_topic_id, topic_id, class_id, quiz_type, description, instructions, time_limit_minutes, passing_score, max_attempts, shuffle_questions, show_correct_answers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('quiz_id'), data.get('quiz_title'), data.get('sub_topic_id'),
                data.get('topic_id'), data.get('class_id'), data.get('quiz_type', 'multiple_choice'),
                data.get('description'), data.get('instructions'), data.get('time_limit_minutes'),
                data.get('passing_score', 70), data.get('max_attempts', 1),
                data.get('shuffle_questions', 1), data.get('show_correct_answers', 1)
            ))

        db.commit()
        return jsonify({'success': True, 'message': f'{entity_type} created successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/<entity_type>/<id>', methods=['PUT', 'DELETE'])
def update_or_delete_entity(entity_type, id):
    """Update or delete entity."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Map entity types to table names
        table_map = {
            'user': 'users', 'grade': 'grades', 'class': 'classes',
            'topic': 'topics', 'sub_topic': 'sub_topics',
            'material': 'materials', 'quiz': 'quizzes'
        }
        table = table_map.get(entity_type, entity_type + 's')
        id_column = f"{entity_type}_id"

        if request.method == 'DELETE':
            cursor.execute(f"DELETE FROM {table} WHERE {id_column} = ?", (id,))
            db.commit()
            return jsonify({'success': True, 'message': f'{entity_type} deleted successfully'})

        elif request.method == 'PUT':
            data = request.json
            # Build update query dynamically
            update_fields = []
            values = []

            for key, value in data.items():
                if key not in ['id', 'created_at']:
                    update_fields.append(f"{key} = ?")
                    values.append(value)

            values.append(id)  # For WHERE clause

            query = f"UPDATE {table} SET {', '.join(update_fields)} WHERE {id_column} = ?"
            cursor.execute(query, values)
            db.commit()
            return jsonify({'success': True, 'message': f'{entity_type} updated successfully'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/export/<entity_type>')
def export_data(entity_type):
    """Export data to JSON."""
    try:
        db = get_db()
        cursor = db.cursor()

        if entity_type == 'curriculum':
            # Export full curriculum tree
            tree_response = get_tree('curriculum')
            data = tree_response.get_json()

            # Save to DATA_HOUSE
            export_file = os.path.join(DATA_HOUSE, 'curriculum_export.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return jsonify({
                'success': True,
                'message': 'Curriculum exported successfully',
                'file_path': export_file,
                'download_url': f'/download/curriculum_export.json'
            })

        elif entity_type == 'users':
            cursor.execute("SELECT * FROM users ORDER BY full_name")
            users = cursor.fetchall()
            data = {
                'count': len(users),
                'users': [dict(user) for user in users]
            }

            export_file = os.path.join(DATA_HOUSE, 'users_export.json')
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return jsonify({
                'success': True,
                'message': 'Users exported successfully',
                'file_path': export_file,
                'download_url': f'/download/users_export.json'
            })

        else:
            return jsonify({'success': False, 'error': 'Invalid export type'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download exported file."""
    return send_from_directory(DATA_HOUSE, filename, as_attachment=True)


@app.route('/api/import/<entity_type>', methods=['POST'])
def import_data(entity_type):
    """Import data from JSON."""
    try:
        data = request.json
        db = get_db()
        cursor = db.cursor()

        imported_count = 0

        if entity_type == 'users':
            users = data.get('users', [])
            for user in users:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO users
                        (user_id, email, full_name, role, grade_level, class_id, phone, address)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        user.get('user_id'), user.get('email'), user.get('full_name'),
                        user.get('role'), user.get('grade_level'), user.get('class_id'),
                        user.get('phone'), user.get('address')
                    ))
                    if cursor.rowcount > 0:
                        imported_count += 1
                except (mysql.connector.Error, sqlite3.Error) as e:
                    print(f"Skipping user import error: {e}")
                    continue

        elif entity_type == 'curriculum':
            # Import curriculum tree
            grades = data.get('data', []) if 'data' in data else data

            for grade in grades:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO grades (grade_id, grade_number, grade_name, description)
                        VALUES (?, ?, ?, ?)
                    """, (grade.get('id'), grade.get('number'), grade.get('name'), grade.get('description')))
                    if cursor.rowcount > 0:
                        imported_count += 1

                    # Import classes
                    for class_ in grade.get('children', []):
                        cursor.execute("""
                            INSERT OR IGNORE INTO classes
                            (class_id, class_name, grade_id, teacher_id, room_number, schedule, max_students, academic_year)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            class_.get('id'), class_.get('name'), grade.get('id'),
                            class_.get('teacher'), class_.get('room'), class_.get('schedule'),
                            class_.get('max_students'), class_.get('academic_year')
                        ))
                        if cursor.rowcount > 0:
                            imported_count += 1

                        # Continue with topics, sub-topics, etc.
                        # (Similar pattern for remaining levels)

                except Exception as e:
                    print(f"Error importing grade: {e}")
                    continue

        db.commit()

        return jsonify({
            'success': True,
            'message': f'{imported_count} records imported successfully'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/sync', methods=['POST'])
def sync_firebase():
    """Sync data from Firebase to local SQLite"""
    try:
        # Initialize Firebase if not already initialized
        if not firebase_admin._apps:
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', 'firebase_credentials.json')
            if not os.path.exists(cred_path):
                return jsonify({'success': False, 'error': f'Firebase credentials not found at {cred_path}'}), 500
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            
        firestore_db = firestore.client()
        local_db = get_db()
        cursor = local_db.cursor()
        
        # 1. Sync Users
        users_ref = firestore_db.collection('users').stream()
        users_synced = 0
        for doc in users_ref:
            data = doc.to_dict()
            user_id = data.get('id', doc.id)
            
            raw_role = str(data.get('role', 'student')).lower()
            valid_roles = ['student', 'teacher', 'admin', 'parent']
            final_role = raw_role if raw_role in valid_roles else 'student'
            
            cursor.execute("""
                INSERT OR REPLACE INTO users (user_id, full_name, email, role, grade_level, class_id, phone, address, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                user_id,
                data.get('full_name', ''),
                data.get('email', f"{user_id}@ezralms.local"),
                final_role,
                data.get('grade_level', ''),
                data.get('class_id', ''),
                data.get('phone', ''),
                data.get('address', '')
            ))
            users_synced += 1
            
        # 2. Sync Attendance
        attendance_ref = firestore_db.collection('attendance').stream()
        attendance_synced = 0
        
        def custom_serializer(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        for doc in attendance_ref:
            data = doc.to_dict()
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO attendance (firestore_id, student_id, student_name, class_name, attendance_date, status, raw_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.id,
                    data.get('student_id', ''),
                    data.get('student_name', ''),
                    data.get('class_name', ''),
                    data.get('date', ''),
                    data.get('status', ''),
                    json.dumps(data, default=custom_serializer)
                ))
                attendance_synced += 1
            except sqlite3.OperationalError:
                pass

        local_db.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Synced {users_synced} users and {attendance_synced} attendance records from Firebase.'
        })
        
    except Exception as e:
        app.logger.error(f"Error syncing with Firebase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/student/<user_id>/weaknesses-and-recommendations', methods=['GET'])
def get_weaknesses_and_recommendations(user_id):
    """
    Identify student's weak topics (<70% mastery) and recommend quizzes.
    """
    try:
        db = get_db()
        cursor = db.cursor()

        # Step 1: Calculate Topic Mastery based on Latest Attempts
        mastery_query = """
        WITH LatestAttempts AS (
            SELECT 
                userId, 
                quizId, 
                score, 
                maxScore,
                (CAST(score AS REAL) / CAST(maxScore AS REAL)) * 100 AS percentage,
                ROW_NUMBER() OVER (PARTITION BY userId, quizId ORDER BY completedAt DESC) as rn
            FROM quiz_attempts
            WHERE userId = ?
        )
        SELECT 
            t.topic_id,
            t.topic_name,
            AVG(la.percentage) as average_topic_score,
            COUNT(la.quizId) as quizzes_attempted
        FROM LatestAttempts la
        JOIN quizzes q ON la.quizId = q.quiz_id
        JOIN topics t ON q.topic_id = t.topic_id
        WHERE la.rn = 1
        GROUP BY t.topic_id
        HAVING average_topic_score < 70.0
        ORDER BY average_topic_score ASC;
        """
        
        cursor.execute(mastery_query, (user_id,))
        weak_topics = cursor.fetchall()
        
        weaknesses_list = []
        recommendations_list = []
        
        # Recommendations query
        rec_query = """
        SELECT q.quiz_id, q.quiz_title, q.topic_id, q.sub_topic_id
        FROM quizzes q
        WHERE q.topic_id = ?
          AND q.is_published = 1
          AND q.quiz_id NOT IN (
              SELECT quizId 
              FROM quiz_attempts 
              WHERE userId = ? AND (CAST(score AS REAL) / CAST(maxScore AS REAL)) >= 0.7
          )
        LIMIT ?;
        """
        
        for row in weak_topics:
            topic_id = row['topic_id']
            topic_name = row['topic_name']
            avg_score = round(row['average_topic_score'], 2)
            
            weaknesses_list.append({
                "topic_id": topic_id,
                "topic_name": topic_name,
                "average_score": avg_score
            })
            
            rem_limit = 3 - len(recommendations_list)
            if rem_limit > 0:
                cursor.execute(rec_query, (topic_id, user_id, rem_limit))
                recs = cursor.fetchall()
                for rec in recs:
                    recommendations_list.append({
                        "quiz_id": rec['quiz_id'],
                        "quiz_title": rec['quiz_title'],
                        "topic_id": rec['topic_id'],
                        "sub_topic_id": rec['sub_topic_id']
                    })

        payload = {
            "success": True,
            "student_id": user_id,
            "weaknesses": weaknesses_list,
            "recommendations": recommendations_list
        }
        
        return jsonify(payload)

    except Exception as e:
        app.logger.error(f"Error fetching weaknesses for user {user_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Automation Global State
automation_process = None
autopilot_process = None
import subprocess
import os

@app.route('/api/automation/status', methods=['GET'])
def automation_status():
    global automation_process, autopilot_process
    
    browser_running = False
    if automation_process is not None:
        if automation_process.poll() is None:
            browser_running = True
            
    autopilot_running = False
    if autopilot_process is not None:
        if autopilot_process.poll() is None:
            autopilot_running = True
            
    return jsonify({
        'success': True,
        'browser_running': browser_running,
        'autopilot_running': autopilot_running
    })

@app.route('/api/automation/start', methods=['POST'])
def automation_start():
    global automation_process
    try:
        if automation_process is not None and automation_process.poll() is None:
            return jsonify({'success': False, 'error': 'Browser is already running'})
            
        automation_dir = os.path.join(os.getcwd(), 'EzraLms_automation')
        script_path = os.path.join(automation_dir, 'persistent_browser.js')
        
        # Start persistent browser
        automation_process = subprocess.Popen(
            ['node', script_path],
            cwd=automation_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return jsonify({'success': True, 'message': 'Browser started'})
    except Exception as e:
        app.logger.error(f"Error starting automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/automation/stop', methods=['POST'])
def automation_stop():
    global automation_process, autopilot_process
    try:
        if automation_process is not None and automation_process.poll() is None:
            automation_process.terminate()
            automation_process = None
            
        if autopilot_process is not None and autopilot_process.poll() is None:
            autopilot_process.terminate()
            autopilot_process = None
            
        return jsonify({'success': True, 'message': 'Automation stopped'})
    except Exception as e:
        app.logger.error(f"Error stopping automation: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/automation/autopilot', methods=['POST'])
def automation_autopilot():
    global autopilot_process, automation_process
    try:
        if automation_process is None or automation_process.poll() is not None:
            return jsonify({'success': False, 'error': 'Start the persistent browser first'})
            
        if autopilot_process is not None and autopilot_process.poll() is None:
            return jsonify({'success': False, 'error': 'Autopilot is already running'})
            
        automation_dir = os.path.join(os.getcwd(), 'EzraLms_automation')
        script_path = os.path.join(automation_dir, 'autopilot_g8.js')
        
        # Start autopilot script
        autopilot_process = subprocess.Popen(
            ['node', script_path],
            cwd=automation_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return jsonify({'success': True, 'message': 'Autopilot G8 started'})
    except Exception as e:
        app.logger.error(f"Error starting autopilot: {e}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print("EZRA LMS - Complete Web UI")
    print("Users & Curriculum Management")
    print("=" * 60)

    # Initialize database
    init_db()

    print(f"\nDatabase: {DB_PATH}")
    print(f"Data House: {DATA_HOUSE}")
    
    print(f"\nOpen browser to: http://localhost:5007")
    print("=" * 60)
    print("Press CTRL+C to stop\n")

    # Run the application
    app.run(host='0.0.0.0', port=5007, debug=True)
