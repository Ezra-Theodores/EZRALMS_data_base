#!/usr/bin/env python3
"""
EZRA LMS - Dashboard Application
=================================

Dashboard for monitoring and managing:
- Users (Students, Teachers, Admins)
- Curriculum Hierarchy:
  - Grades 1-12
  - Classes
  - Topics
  - Sub-topics
  - Materials
  - Quizzes

Usage:
    python dashboard_app.py

Then open browser to: http://localhost:5004
"""

import os
import sys
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g

app = Flask(__name__)

# Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), 'ezralms_complete.db')
DATA_HOUSE = os.path.join(os.path.dirname(__file__), 'DATA_HOUSE_EZRALMS')

# Ensure DATA_HOUSE exists
os.makedirs(DATA_HOUSE, exist_ok=True)


def get_db():
    """Get database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


@app.route('/')
def index():
    """Render main dashboard."""
    return render_template('dashboard.html')


@app.route('/api/stats')
def get_stats():
    """Get dashboard statistics."""
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

        # Total users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        stats['total_users'] = cursor.fetchone()['count']

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

        # Materials count
        cursor.execute("SELECT COUNT(*) as count FROM materials")
        stats['materials_count'] = cursor.fetchone()['count']

        # Quizzes count
        cursor.execute("SELECT COUNT(*) as count FROM quizzes")
        stats['quizzes_count'] = cursor.fetchone()['count']

        return jsonify({'success': True, 'data': stats})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/users')
def get_users():
    """Get all users with optional filtering."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Get query parameters
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

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tree/curriculum')
def get_curriculum_tree():
    """Get full curriculum tree structure."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Build tree structure
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

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("EZRA LMS - Dashboard Application")
    print("=" * 60)
    print("\nFeatures:")
    print("  - Users Management")
    print("  - Curriculum Hierarchy (Grades 1-12)")
    print("  - Tree View Navigation")
    print("  - Statistics & Analytics")
    print("\nURL: http://localhost:5004")
    print("=" * 60)
    print("Press CTRL+C to stop\n")

    app.run(host='0.0.0.0', port=5004, debug=True)
