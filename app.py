#!/usr/bin/env python3
"""
EZRA LMS - Web UI for Attendance Data
======================================

Flask web application for searching and displaying
attendance data from SQLite database.

Usage:
    python app.py

Then open browser to: http://localhost:5006
"""

import os
import sqlite3
import json

from flask import Flask, render_template, request, jsonify, g
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# Database configuration
DB_PATH = os.getenv("DB_PATH", "./ezralms.db")


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
    """Render main page."""
    return render_template('index.html')


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) as total FROM attendance")
        total = cursor.fetchone()['total']

        # Records by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM attendance
            GROUP BY status
        """)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}

        # Date range
        cursor.execute("""
            SELECT MIN(attendance_date) as min_date,
                   MAX(attendance_date) as max_date
            FROM attendance
        """)
        date_range = cursor.fetchone()

        return jsonify({
            'success': True,
            'data': {
                'total_records': total,
                'by_status': by_status,
                'date_range': {
                    'min': date_range['min_date'],
                    'max': date_range['max_date']
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search')
def search():
    """Search attendance records."""
    try:
        db = get_db()
        cursor = db.cursor()

        # Get search parameters
        student_name = request.args.get('student_name', '').strip()
        student_id = request.args.get('student_id', '').strip()
        class_name = request.args.get('class_name', '').strip()
        status = request.args.get('status', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()

        # Build query
        conditions = []
        params = []

        if student_name:
            conditions.append("student_name LIKE ?")
            params.append(f"%{student_name}%")

        if student_id:
            conditions.append("student_id LIKE ?")
            params.append(f"%{student_id}%")

        if class_name:
            conditions.append("class_name LIKE ?")
            params.append(f"%{class_name}%")

        if status:
            conditions.append("status = ?")
            params.append(status)

        if date_from:
            conditions.append("attendance_date >= ?")
            params.append(date_from)

        if date_to:
            conditions.append("attendance_date <= ?")
            params.append(date_to)

        # Build final query
        query = "SELECT * FROM attendance"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY attendance_date DESC, student_name ASC"

        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()

        # Convert to list of dicts
        records = []
        for row in rows:
            record = dict(row)
            # Parse raw_data JSON if exists
            if record.get('raw_data'):
                try:
                    record['raw_data_parsed'] = json.loads(record['raw_data'])
                except (json.JSONDecodeError, ValueError):
                    pass
            records.append(record)

        return jsonify({
            'success': True,
            'count': len(records),
            'data': records
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/record/<firestore_id>')
def get_record(firestore_id):
    """Get single record by Firestore ID."""
    try:
        db = get_db()
        cursor = db.cursor()

        cursor.execute(
            "SELECT * FROM attendance WHERE firestore_id = ?",
            (firestore_id,)
        )
        row = cursor.fetchone()

        if row:
            record = dict(row)
            if record.get('raw_data'):
                try:
                    record['raw_data_parsed'] = json.loads(record['raw_data'])
                except (json.JSONDecodeError, ValueError):
                    pass
            return jsonify({'success': True, 'data': record})
        else:
            return jsonify({'success': False, 'error': 'Record not found'}), 404

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("EZRA LMS - Web UI for Attendance Data")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Open browser to: http://localhost:5002")
    print("=" * 60)
    print("Press CTRL+C to stop")
    print()

    app.run(host='0.0.0.0', port=5006, debug=True)
