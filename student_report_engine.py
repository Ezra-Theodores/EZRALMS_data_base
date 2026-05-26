"""
EZRA LMS - Student Report & Recommendation Engine
==================================================
Analyzes student performance from Firebase Firestore, identifies skill gaps,
and generates personalized development recommendations.
"""

import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from collections import defaultdict
from datetime import datetime


class StudentReportEngine:
    """Analyzes student data and generates reports with recommendations."""

    SKILL_CATEGORIES = {
        'Algebra': ['Algebra', 'ALGEBRA', 'algebra', 'equation', 'variable'],
        'Multiplication': ['Multiplication', 'multiplication', 'kali', 'perkalian'],
        'Division': ['Division', 'division', 'Pembagian', 'PEMBAGIAN', 'bagi'],
        'Geometry': ['Bangun Datar', 'bangun datar', 'Geometry', 'geometry', 'segitiga', 'lingkaran', 'persegi'],
        'Number Sense': ['menghitung', 'Sorting', 'Explore', 'Number Bound', 'number', 'counting'],
        'Addition/Subtraction': ['Addition', 'Subtraction', 'addition', 'subtraction', 'tambah', 'kurang', 'Add Subt', 'POKE ADD'],
        'Competition Math': ['OSN', 'IOB', 'JISMO', 'HXC', 'IKMC', 'competition', 'Competition'],
        'Intervals/Sequences': ['INTERVAL', 'interval', 'PROGRESSION', 'progression', 'pola'],
        'Word Problems': ['Tambah Tanggal', 'word problem', 'cerita', 'soal cerita'],
        'Fractions/Decimals': ['Pecahan', 'pecahan', 'Desimal', 'desimal', 'Fraction', 'fraction'],
        'Measurement': ['Pengukuran', 'pengukuran', 'Measurement', 'measurement', 'satuan', 'unit'],
    }

    PASS_THRESHOLD = 60.0
    WEAK_THRESHOLD = 70.0

    def __init__(self, cred_path=None):
        if cred_path is None:
            cred_path = os.path.join(os.path.dirname(__file__), 'DATA_HOUSE_EZRALMS', 'firebase_credentials.json')
            if not os.path.exists(cred_path):
                cred_path = os.path.join(os.path.dirname(__file__), 'firebase_credentials.json')

        if not os.path.exists(cred_path):
            raise FileNotFoundError(f"Firebase credentials not found: {cred_path}")

        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

        self.db = firestore.client()
        self._user_cache = {}
        self._quiz_cache = {}

    def search_users(self, query, limit=20):
        """Search for users by name, email, or displayName."""
        query_lower = query.lower()
        results = []
        seen = set()

        for doc in self.db.collection('users').stream():
            if len(results) >= limit:
                break
            data = doc.to_dict()
            name = (data.get('name', '') or '').lower()
            email = (data.get('email', '') or '').lower()
            display_name = (data.get('displayName', '') or '').lower()
            profile = data.get('profile', {})
            if isinstance(profile, dict):
                first_name = (profile.get('firstName', '') or '').lower()
                last_name = (profile.get('lastName', '') or '').lower()
            else:
                first_name = ''
                last_name = ''

            searchable = f"{name} {email} {display_name} {first_name} {last_name}"
            if query_lower in searchable and doc.id not in seen:
                seen.add(doc.id)
                results.append({
                    'user_id': doc.id,
                    'name': data.get('displayName') or data.get('name') or first_name or 'Unknown',
                    'email': data.get('email', ''),
                    'role': data.get('role', ''),
                    'first_name': profile.get('firstName', '') if isinstance(profile, dict) else '',
                    'last_name': profile.get('lastName', '') if isinstance(profile, dict) else '',
                    'source': 'users',
                })

        # Also search sessions collection for displayNames
        for doc in self.db.collection('sessions').stream():
            if len(results) >= limit:
                break
            data = doc.to_dict()
            display_name = (data.get('displayName', '') or '').lower()
            username = (data.get('username', '') or '').lower()
            uid = data.get('uid', '')
            actual_uid = data.get('actualUserId', '') or data.get('userId', '')

            searchable = f"{display_name} {username} {uid} {actual_uid}"
            if query_lower in searchable and actual_uid not in seen:
                seen.add(actual_uid)
                results.append({
                    'user_id': actual_uid,
                    'name': data.get('displayName') or data.get('username') or 'Unknown',
                    'email': '',
                    'role': data.get('role', 'student'),
                    'first_name': '',
                    'last_name': '',
                    'source': 'sessions',
                    'session_id': doc.id,
                })

        return results

    def get_student_ids(self, user_id):
        """Get all possible student IDs for a user (user_id, actualUserId, etc)."""
        ids = {user_id}

        # Check sessions for this user - only scan once and cache
        if not hasattr(self, '_session_map'):
            self._session_map = {}
            for doc in self.db.collection('sessions').stream():
                data = doc.to_dict()
                uid = data.get('uid', '')
                actual = data.get('actualUserId', '')
                userId = data.get('userId', '')
                key = uid or actual or userId
                if key:
                    if key not in self._session_map:
                        self._session_map[key] = set()
                    self._session_map[key].add(uid)
                    self._session_map[key].add(actual)
                    self._session_map[key].add(userId)

        # Find all linked IDs
        for key, linked_ids in self._session_map.items():
            if user_id in linked_ids:
                ids.update(linked_ids)

        return {i for i in ids if i}

    def get_student_profile(self, user_id):
        """Get comprehensive student profile."""
        student_ids = self.get_student_ids(user_id)

        profile = {
            'user_id': user_id,
            'name': '',
            'email': '',
            'role': 'student',
            'classes': [],
            'session_log': [],
            'created_at': '',
            'last_login': '',
        }

        # Get user document
        user_doc = self.db.collection('users').document(user_id).get()
        if user_doc.exists:
            data = user_doc.to_dict()
            profile['name'] = data.get('displayName') or data.get('name') or ''
            profile['email'] = data.get('email', '')
            profile['role'] = data.get('role', 'student')
            meta = data.get('metadata', {})
            if isinstance(meta, dict):
                created = meta.get('createdAt', '')
                profile['created_at'] = str(created) if created else ''
            session_log = data.get('sessionLog', [])
            if isinstance(session_log, list):
                profile['session_log'] = session_log

        # Get session data from cache
        if hasattr(self, '_session_map'):
            for key, linked_ids in self._session_map.items():
                if user_id in linked_ids or any(sid in linked_ids for sid in student_ids):
                    # Find the session doc
                    for doc in self.db.collection('sessions').stream():
                        data = doc.to_dict()
                        if data.get('userId') in student_ids or data.get('actualUserId') in student_ids or data.get('uid') in student_ids:
                            if not profile['name']:
                                profile['name'] = data.get('displayName', '')
                            profile['last_login'] = str(data.get('lastLogin', ''))
                            profile['role'] = data.get('role', 'student')
                            break
                    break

        return profile

    def get_student_activities(self, user_id):
        """Get all student activities from ALL linked user IDs."""
        student_ids = self.get_student_ids(user_id)
        activities = []
        seen = set()

        for sid in student_ids:
            for doc in self.db.collection('student_activities').where('studentId', '==', sid).stream():
                if doc.id not in seen:
                    seen.add(doc.id)
                    data = doc.to_dict()
                    data['_doc_id'] = doc.id
                    activities.append(data)

        return activities

    def get_quiz_details(self, quiz_id):
        """Get quiz details with caching."""
        if quiz_id in self._quiz_cache:
            return self._quiz_cache[quiz_id]

        doc = self.db.collection('quizzes').document(quiz_id).get()
        if doc.exists:
            data = doc.to_dict()
            self._quiz_cache[quiz_id] = data
            return data
        return None

    def analyze_quiz_performance(self, activities):
        """Analyze quiz performance from activities."""
        quiz_activities = [a for a in activities if a.get('type') == 'quiz_completed']

        quiz_scores = []
        for qa in quiz_activities:
            score = qa.get('score', 0)
            max_score = qa.get('maxScore', 100)
            pct = (score / max_score * 100) if max_score > 0 else 0
            quiz_scores.append({
                'quiz_id': qa.get('referenceId'),
                'title': qa.get('referenceTitle'),
                'score': score,
                'max_score': max_score,
                'percentage': round(pct, 1),
                'passed': qa.get('passed', False),
                'time_taken': qa.get('timeTaken'),
                'timestamp': str(qa.get('timestamp', '')),
                'class_id': qa.get('classId'),
                'attempt_id': qa.get('attemptId'),
            })

        quiz_scores.sort(key=lambda x: x['timestamp'])

        total = len(quiz_scores)
        passed = sum(1 for q in quiz_scores if q['passed'])
        avg_score = sum(q['percentage'] for q in quiz_scores) / total if total > 0 else 0

        return {
            'quiz_scores': quiz_scores,
            'total_quizzes': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': round(passed / total * 100, 1) if total > 0 else 0,
            'average_score': round(avg_score, 1),
        }

    def analyze_skill_gaps(self, quiz_scores):
        """Categorize quiz performance by skill area."""
        skill_scores = defaultdict(list)

        for qs in quiz_scores:
            title = qs.get('title', '')
            pct = qs['percentage']
            matched = False
            for category, keywords in self.SKILL_CATEGORIES.items():
                if any(kw.lower() in title.lower() for kw in keywords):
                    skill_scores[category].append({
                        'title': title,
                        'score': qs['score'],
                        'max_score': qs['max_score'],
                        'percentage': pct,
                        'passed': qs['passed'],
                        'timestamp': qs['timestamp'],
                    })
                    matched = True
                    break
            if not matched:
                skill_scores['Other'].append({
                    'title': title,
                    'score': qs['score'],
                    'max_score': qs['max_score'],
                    'percentage': pct,
                    'passed': qs['passed'],
                    'timestamp': qs['timestamp'],
                })

        skill_summary = {}
        for category, scores in skill_scores.items():
            avg = sum(s['percentage'] for s in scores) / len(scores)
            skill_summary[category] = {
                'attempts': len(scores),
                'average_score': round(avg, 1),
                'status': self._get_status_label(avg),
                'quizzes': scores,
            }

        return skill_summary

    def _get_status_label(self, avg_score):
        if avg_score >= 80:
            return 'STRONG'
        elif avg_score >= 60:
            return 'OK'
        elif avg_score >= 40:
            return 'WEAK'
        else:
            return 'CRITICAL'

    def identify_weak_topics(self, skill_summary):
        """Identify topics where student needs improvement."""
        weak = []
        for category, data in skill_summary.items():
            if data['average_score'] < self.WEAK_THRESHOLD:
                weak.append({
                    'topic': category,
                    'average_score': data['average_score'],
                    'attempts': data['attempts'],
                    'status': data['status'],
                    'quizzes': data['quizzes'],
                })

        weak.sort(key=lambda x: x['average_score'])
        return weak

    def get_failed_quizzes(self, quiz_scores):
        """Get quizzes that student failed or scored poorly on."""
        failed = []
        quiz_best_scores = defaultdict(lambda: {'best': 0, 'attempts': []})

        for qs in quiz_scores:
            title = qs['title']
            quiz_best_scores[title]['attempts'].append(qs)
            if qs['percentage'] > quiz_best_scores[title]['best']:
                quiz_best_scores[title]['best'] = qs['percentage']

        for title, data in quiz_best_scores.items():
            if data['best'] < self.PASS_THRESHOLD:
                failed.append({
                    'title': title,
                    'best_score': round(data['best'], 1),
                    'attempts': len(data['attempts']),
                    'latest_score': data['attempts'][-1]['percentage'] if data['attempts'] else 0,
                })

        failed.sort(key=lambda x: x['best_score'])
        return failed

    def get_monthly_trend(self, quiz_scores):
        """Get performance trend by month."""
        monthly = defaultdict(list)
        for qs in quiz_scores:
            ts = qs.get('timestamp', '')
            if ts:
                month = ts[:7] if isinstance(ts, str) else ''
                if month:
                    monthly[month].append(qs['percentage'])

        trend = {}
        for month in sorted(monthly.keys()):
            scores = monthly[month]
            trend[month] = {
                'count': len(scores),
                'average': round(sum(scores) / len(scores), 1),
            }
        return trend

    def get_tutor_notes(self, session_log):
        """Extract tutor notes from session log."""
        notes = []
        for log in session_log:
            if isinstance(log, dict):
                note = log.get('notes', '')
                if note:
                    notes.append({
                        'topic': log.get('topic', ''),
                        'date': str(log.get('date', '')),
                        'tutor': log.get('tutorName', ''),
                        'notes': note,
                    })
        return notes

    def generate_recommendations(self, profile, quiz_analysis, skill_summary, weak_topics, failed_quizzes, tutor_notes):
        """Generate personalized recommendations."""
        recommendations = []
        priority_counter = 0

        # 1. Critical skill gaps (avg < 40%)
        for topic in weak_topics:
            if topic['status'] == 'CRITICAL':
                priority_counter += 1
                recommendations.append({
                    'id': priority_counter,
                    'priority': 'CRITICAL',
                    'type': 'skill_gap',
                    'title': f"Critical Gap: {topic['topic']}",
                    'reason': f"Average score {topic['average_score']}% across {topic['attempts']} attempts",
                    'action': f"Create foundational exercises for {topic['topic']}. Start with visual/concrete examples before abstract problems.",
                    'suggested_quiz_type': f"{topic['topic']} Basics - Visual & Concrete",
                })

        # 2. Weak skill gaps (40% <= avg < 70%)
        for topic in weak_topics:
            if topic['status'] in ('WEAK', 'OK'):
                priority_counter += 1
                recommendations.append({
                    'id': priority_counter,
                    'priority': 'HIGH',
                    'type': 'skill_gap',
                    'title': f"Weak Area: {topic['topic']}",
                    'reason': f"Average score {topic['average_score']}% across {topic['attempts']} attempts",
                    'action': f"Assign targeted practice quizzes on {topic['topic']} with scaffolded difficulty.",
                    'suggested_quiz_type': f"{topic['topic']} Practice - Scaffolded",
                })

        # 3. Failed quizzes that need retry
        for fq in failed_quizzes[:5]:
            priority_counter += 1
            recommendations.append({
                'id': priority_counter,
                'priority': 'HIGH' if fq['best_score'] < 40 else 'MEDIUM',
                'type': 'retry_quiz',
                'title': f"Retry: {fq['title']}",
                'reason': f"Best score {fq['best_score']}% across {fq['attempts']} attempt(s)",
                'action': f"Review concepts, then retry '{fq['title']}' with tutor guidance.",
                'suggested_quiz_type': fq['title'],
            })

        # 4. Tutor note follow-ups
        for note in tutor_notes:
            priority_counter += 1
            recommendations.append({
                'id': priority_counter,
                'priority': 'HIGH',
                'type': 'tutor_followup',
                'title': f"Tutor Note: {note['topic'] or 'General'}",
                'reason': f"Tutor {note['tutor']} noted: '{note['notes']}'",
                'action': f"Create targeted exercises addressing: {note['notes']}",
                'suggested_quiz_type': f"{note['topic']} - Word Problems" if note['topic'] else "Word Problems",
            })

        # 5. Declining trend
        trend = self.get_monthly_trend(quiz_analysis['quiz_scores'])
        months = list(trend.keys())
        if len(months) >= 2:
            last_avg = trend[months[-1]]['average']
            prev_avg = trend[months[-2]]['average']
            if last_avg < prev_avg - 15:
                priority_counter += 1
                recommendations.append({
                    'id': priority_counter,
                    'priority': 'HIGH',
                    'type': 'trend_alert',
                    'title': 'Performance Declining',
                    'reason': f"Score dropped from {prev_avg}% ({months[-2]}) to {last_avg}% ({months[-1]})",
                    'action': "Schedule review session. Check if new topics are too advanced or if student needs concept reinforcement.",
                    'suggested_quiz_type': 'Review & Reinforcement',
                })

        # 6. Progress review
        priority_counter += 1
        recommendations.append({
            'id': priority_counter,
            'priority': 'LOW',
            'type': 'progress_review',
            'title': 'Overall Progress Review',
            'reason': f"{quiz_analysis['total_quizzes']} quizzes completed, {quiz_analysis['pass_rate']}% pass rate",
            'action': "Review curriculum coverage and identify any missing subtopics in the student's class track.",
            'suggested_quiz_type': 'Curriculum Gap Assessment',
        })

        return recommendations

    def generate_report(self, user_id):
        """Generate complete student report."""
        # Get profile
        profile = self.get_student_profile(user_id)

        # Get activities
        activities = self.get_student_activities(user_id)

        # Analyze quiz performance
        quiz_analysis = self.analyze_quiz_performance(activities)

        # Analyze skill gaps
        skill_summary = self.analyze_skill_gaps(quiz_analysis['quiz_scores'])

        # Identify weak topics
        weak_topics = self.identify_weak_topics(skill_summary)

        # Get failed quizzes
        failed_quizzes = self.get_failed_quizzes(quiz_analysis['quiz_scores'])

        # Get monthly trend
        monthly_trend = self.get_monthly_trend(quiz_analysis['quiz_scores'])

        # Get tutor notes
        tutor_notes = self.get_tutor_notes(profile.get('session_log', []))

        # Generate recommendations
        recommendations = self.generate_recommendations(
            profile, quiz_analysis, skill_summary, weak_topics, failed_quizzes, tutor_notes
        )

        # Build report
        report = {
            'student': {
                'user_id': user_id,
                'name': profile['name'],
                'email': profile['email'],
                'role': profile['role'],
                'created_at': profile['created_at'],
                'last_login': profile['last_login'],
            },
            'summary': {
                'total_quizzes': quiz_analysis['total_quizzes'],
                'passed': quiz_analysis['passed'],
                'failed': quiz_analysis['failed'],
                'pass_rate': quiz_analysis['pass_rate'],
                'average_score': quiz_analysis['average_score'],
                'total_subtopics': len([a for a in activities if a.get('type') == 'subtopic_completed']),
                'total_activities': len(activities),
            },
            'skill_gaps': {k: {kk: vv for kk, vv in v.items() if kk != 'quizzes'} for k, v in skill_summary.items()},
            'weak_topics': [{k: v for k, v in t.items() if k != 'quizzes'} for t in weak_topics],
            'failed_quizzes': failed_quizzes,
            'monthly_trend': monthly_trend,
            'tutor_notes': tutor_notes,
            'quiz_history': quiz_analysis['quiz_scores'][-20:],  # Last 20
            'recommendations': recommendations,
            'generated_at': datetime.now().isoformat(),
        }

        return report
