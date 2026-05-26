#!/usr/bin/env python3
"""
EZRA LMS - Student Report & Recommendation Web Application
===========================================================
Search for students, view objective performance reports,
and get personalized skill development recommendations.

Usage:
    python student_report_app.py

Then open browser to: http://localhost:5005
"""

import os
import json
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

from student_report_engine import StudentReportEngine

app = Flask(__name__)
CORS(app)

# Initialize engine (lazy)
_engine = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = StudentReportEngine()
    return _engine


@app.route('/')
def index():
    """Render student report page."""
    return render_template('student_report.html')


@app.route('/api/search')
def api_search():
    """Search for students by name/email."""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'success': False, 'error': 'Query must be at least 2 characters'})

    try:
        engine = get_engine()
        results = engine.search_users(query)
        return jsonify({'success': True, 'count': len(results), 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/report/<user_id>')
def api_report(user_id):
    """Generate full student report."""
    try:
        engine = get_engine()
        report = engine.generate_report(user_id)
        return jsonify({'success': True, 'data': report})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/skill-gaps/<user_id>')
def api_skill_gaps(user_id):
    """Get only skill gap analysis."""
    try:
        engine = get_engine()
        activities = engine.get_student_activities(user_id)
        quiz_analysis = engine.analyze_quiz_performance(activities)
        skill_summary = engine.analyze_skill_gaps(quiz_analysis['quiz_scores'])
        weak_topics = engine.identify_weak_topics(skill_summary)

        return jsonify({
            'success': True,
            'data': {
                'skill_summary': {k: {kk: vv for kk, vv in v.items() if kk != 'quizzes'} for k, v in skill_summary.items()},
                'weak_topics': weak_topics,
                'quiz_count': quiz_analysis['total_quizzes'],
                'average_score': quiz_analysis['average_score'],
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/recommendations/<user_id>')
def api_recommendations(user_id):
    """Get recommendations for a student."""
    try:
        engine = get_engine()
        report = engine.generate_report(user_id)
        return jsonify({
            'success': True,
            'data': {
                'student': report['student'],
                'recommendations': report['recommendations'],
                'summary': report['summary'],
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/quiz-history/<user_id>')
def api_quiz_history(user_id):
    """Get quiz history for a student."""
    try:
        engine = get_engine()
        activities = engine.get_student_activities(user_id)
        quiz_analysis = engine.analyze_quiz_performance(activities)
        return jsonify({
            'success': True,
            'data': {
                'quiz_scores': quiz_analysis['quiz_scores'],
                'total': quiz_analysis['total_quizzes'],
                'passed': quiz_analysis['passed'],
                'failed': quiz_analysis['failed'],
                'pass_rate': quiz_analysis['pass_rate'],
                'average_score': quiz_analysis['average_score'],
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/trend/<user_id>')
def api_trend(user_id):
    """Get performance trend."""
    try:
        engine = get_engine()
        activities = engine.get_student_activities(user_id)
        quiz_analysis = engine.analyze_quiz_performance(activities)
        trend = engine.get_monthly_trend(quiz_analysis['quiz_scores'])
        return jsonify({'success': True, 'data': trend})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("EZRA LMS - Student Report & Recommendation System")
    print("=" * 60)
    print("\nFeatures:")
    print("  - Search students by name/email")
    print("  - View objective performance reports")
    print("  - Skill gap analysis")
    print("  - Personalized development recommendations")
    print("  - Quiz history & performance trends")
    print("\nURL: http://localhost:5005")
    print("=" * 60)
    print("Press CTRL+C to stop\n")

    app.run(host='0.0.0.0', port=5005, debug=True)
