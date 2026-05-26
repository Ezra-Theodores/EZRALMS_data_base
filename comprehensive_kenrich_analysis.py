import firebase_admin
from firebase_admin import credentials, firestore
import json
from collections import defaultdict

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

USER_ID = "w1kBVxVaMD4Nc3gJ894U"  # Kenrich
USER_ID2 = "LKK43rlhECv5zZEuxu4G"  # Kenrick Harvey Wijaya

# 1. Get ALL activities for both IDs
all_activities = []
for uid in [USER_ID, USER_ID2]:
    for doc in db.collection('student_activities').where('studentId', '==', uid).stream():
        data = doc.to_dict()
        data['_doc_id'] = doc.id
        data['_userId'] = uid
        all_activities.append(data)

print(f"Total activities: {len(all_activities)}")

# Separate quizzes and subtopics
quiz_activities = [a for a in all_activities if a.get('type') == 'quiz_completed']
subtopic_activities = [a for a in all_activities if a.get('type') == 'subtopic_completed']

print(f"Quiz completions: {len(quiz_activities)}")
print(f"Subtopic completions: {len(subtopic_activities)}")

# 2. Analyze quiz performance
print("\n=== QUIZ PERFORMANCE ANALYSIS ===")
quiz_scores = []
for qa in quiz_activities:
    quiz_scores.append({
        'quiz_id': qa.get('referenceId'),
        'title': qa.get('referenceTitle'),
        'score': qa.get('score', 0),
        'max_score': qa.get('maxScore', 100),
        'passed': qa.get('passed', False),
        'time_taken': qa.get('timeTaken'),
        'timestamp': str(qa.get('timestamp', '')),
        'classId': qa.get('classId'),
        'attemptId': qa.get('attemptId'),
    })

# Sort by timestamp
quiz_scores.sort(key=lambda x: x['timestamp'])

# Print all quiz scores
for qs in quiz_scores:
    pct = qs['score'] / qs['max_score'] * 100 if qs['max_score'] > 0 else 0
    status = "PASS" if qs['passed'] else "FAIL"
    print(f"  [{qs['timestamp'][:10]}] {qs['title']}: {qs['score']}/{qs['max_score']} = {pct:.0f}% [{status}] time={qs['time_taken']}s")

# Calculate stats
total_quizzes = len(quiz_scores)
passed = sum(1 for q in quiz_scores if q['passed'])
failed = total_quizzes - passed
avg_score = sum(q['score']/q['max_score']*100 for q in quiz_scores if q['max_score'] > 0) / total_quizzes if total_quizzes > 0 else 0

print(f"\nTotal quizzes: {total_quizzes}")
print(f"Passed: {passed} ({passed/total_quizzes*100:.0f}%)")
print(f"Failed: {failed} ({failed/total_quizzes*100:.0f}%)")
print(f"Average score: {avg_score:.1f}%")

# Group by quiz title to find repeated attempts
quiz_by_title = defaultdict(list)
for qs in quiz_scores:
    quiz_by_title[qs['title']].append(qs)

print(f"\n=== QUIZZES BY TITLE (with multiple attempts) ===")
for title, attempts in sorted(quiz_by_title.items(), key=lambda x: len(x[1]), reverse=True):
    if len(attempts) > 1:
        scores_str = ', '.join(f"{a['score']}/{a['max_score']}" for a in attempts)
        best = max(a['score']/a['max_score']*100 for a in attempts)
        print(f"  {title}: {len(attempts)} attempts [{scores_str}] best={best:.0f}%")

# 3. Analyze subtopics completed
print(f"\n=== SUBTOPICS COMPLETED ({len(subtopic_activities)}) ===")
subtopic_by_title = defaultdict(list)
for sa in subtopic_activities:
    subtopic_by_title[sa.get('referenceTitle', 'Unknown')].append(sa)

for title, completions in sorted(subtopic_by_title.items()):
    timestamps = [str(c.get('timestamp', ''))[:10] for c in completions]
    print(f"  {title}: {len(completions)}x completed [{', '.join(timestamps)}]")

# 4. Get quiz details from Firestore to understand topics
print(f"\n=== FETCHING QUIZ DETAILS FROM FIRESTORE ===")
unique_quiz_ids = list(set(qs['quiz_id'] for qs in quiz_scores))
print(f"Unique quiz IDs: {len(unique_quiz_ids)}")

quiz_topic_map = {}
for qid in unique_quiz_ids:
    qdoc = db.collection('quizzes').document(qid).get()
    if qdoc.exists:
        qdata = qdoc.to_dict()
        quiz_topic_map[qid] = {
            'title': qdata.get('title', ''),
            'subject': qdata.get('subject', ''),
            'grade': str(qdata.get('grade', '')),
            'difficulty': qdata.get('difficulty', ''),
            'topic': qdata.get('topic', ''),
            'questions': qdata.get('questions', []),
        }
        # Extract topics from questions
        question_topics = set()
        for q in qdata.get('questions', []):
            if isinstance(q, dict) and q.get('topic'):
                question_topics.add(q['topic'])
        quiz_topic_map[qid]['question_topics'] = list(question_topics)

# 5. Group quiz performance by topic
print(f"\n=== PERFORMANCE BY QUIZ TOPIC ===")
topic_scores = defaultdict(list)
for qs in quiz_scores:
    qid = qs['quiz_id']
    if qid in quiz_topic_map:
        qt = quiz_topic_map[qid]
        topic = qt['topic'] or qt['subject'] or qt['grade'] or 'unknown'
        pct = qs['score'] / qs['max_score'] * 100 if qs['max_score'] > 0 else 0
        topic_scores[topic].append({
            'title': qs['title'],
            'score': qs['score'],
            'max_score': qs['max_score'],
            'percentage': pct,
            'passed': qs['passed'],
            'timestamp': qs['timestamp'],
        })

for topic, scores in sorted(topic_scores.items(), key=lambda x: sum(s['percentage'] for s in x[1])/len(x[1])):
    avg = sum(s['percentage'] for s in scores) / len(scores)
    pass_rate = sum(1 for s in scores if s['passed']) / len(scores) * 100
    print(f"\n  TOPIC: {topic}")
    print(f"    Attempts: {len(scores)}, Avg: {avg:.1f}%, Pass rate: {pass_rate:.0f}%")
    for s in scores:
        status = "PASS" if s['passed'] else "FAIL"
        print(f"      [{s['timestamp'][:10]}] {s['title']}: {s['score']}/{s['max_score']} = {s['percentage']:.0f}% [{status}]")

# 6. Identify weak topics
print(f"\n=== WEAK TOPICS (avg < 70%) ===")
weak_topics = {}
for topic, scores in topic_scores.items():
    avg = sum(s['percentage'] for s in scores) / len(scores)
    if avg < 70:
        weak_topics[topic] = {
            'average_score': round(avg, 1),
            'attempts': len(scores),
            'pass_rate': round(sum(1 for s in scores if s['passed']) / len(scores) * 100, 0),
            'quizzes': [s['title'] for s in scores],
        }
        print(f"  {topic}: avg={avg:.1f}%, attempts={len(scores)}, pass_rate={weak_topics[topic]['pass_rate']}%")

# 7. Get subtopic details
print(f"\n=== SUBTOPIC DETAILS ===")
unique_subtopic_ids = list(set(sa.get('referenceId') for sa in subtopic_activities if sa.get('referenceId')))
subtopic_topic_map = {}
for sid in unique_subtopic_ids[:30]:
    sdoc = db.collection('classworkSubtopics').document(sid).get()
    if sdoc.exists:
        sdata = sdoc.to_dict()
        subtopic_topic_map[sid] = {
            'name': sdata.get('name', ''),
            'topicId': sdata.get('topicId', ''),
            'type': sdata.get('type', ''),
            'classId': sdata.get('classId', ''),
        }

# 8. Get class info
print(f"\n=== CLASS INFO ===")
class_ids = set(a.get('classId') for a in all_activities if a.get('classId'))
for cid in class_ids:
    cdoc = db.collection('classes').document(cid).get()
    if cdoc.exists:
        cdata = cdoc.to_dict()
        print(f"  {cid}: name={cdata.get('name')}, grade={cdata.get('grade')}, subject={cdata.get('subject')}")

# 9. Build recommendation
print(f"\n{'='*60}")
print(f"RECOMMENDATIONS FOR KENRICH")
print(f"{'='*60}")

recommendations = []

# Weak topic recommendations
for topic, data in sorted(weak_topics.items(), key=lambda x: x[1]['average_score']):
    recommendations.append({
        'type': 'weak_topic_practice',
        'topic': topic,
        'priority': 'HIGH',
        'reason': f"Average score {data['average_score']}% across {data['attempts']} attempts",
        'action': f"Assign additional practice quizzes on '{topic}'",
    })

# Session note-based recommendation
recommendations.append({
    'type': 'tutor_note_followup',
    'priority': 'HIGH',
    'reason': "Tutor noted: 'Kenrich masih kesulitan untuk soal sifat-sifat bangun datar melalui kalimat'",
    'action': "Create targeted exercises on properties of flat shapes (bangun datar) presented as word problems",
})

# Repeated quiz with low scores
for title, attempts in quiz_by_title.items():
    best = max(a['score']/a['max_score']*100 for a in attempts)
    if best < 60 and len(attempts) >= 1:
        recommendations.append({
            'type': 'retry_failed_quiz',
            'quiz': title,
            'priority': 'MEDIUM',
            'reason': f"Best score {best:.0f}% on '{title}' across {len(attempts)} attempts",
            'action': f"Review concepts and retry '{title}' with tutor guidance",
        })

# Subtopic gaps - find subtopics in his classes he hasn't completed
recommendations.append({
    'type': 'progress_review',
    'priority': 'MEDIUM',
    'reason': f"Completed {len(subtopic_activities)} subtopics and {len(quiz_activities)} quizzes",
    'action': "Review curriculum coverage and identify missing subtopics in his class track",
})

for i, rec in enumerate(recommendations, 1):
    print(f"\n{i}. [{rec['priority']}] {rec['type']}")
    print(f"   Reason: {rec['reason']}")
    print(f"   Action: {rec['action']}")

# Save comprehensive analysis
analysis = {
    'student': {
        'userId': USER_ID,
        'displayName': 'Kenrich',
        'fullName': 'Kenrick Harvey Wijaya',
        'role': 'student',
        'lastLogin': '2026-05-21',
    },
    'summary': {
        'total_quizzes': total_quizzes,
        'passed': passed,
        'failed': failed,
        'pass_rate': round(passed/total_quizzes*100, 1) if total_quizzes > 0 else 0,
        'average_score': round(avg_score, 1),
        'total_subtopics': len(subtopic_activities),
        'unique_subtopics': len(subtopic_by_title),
    },
    'weak_topics': weak_topics,
    'quiz_scores': quiz_scores,
    'quiz_topic_map': {k: {kk: vv for kk, vv in v.items() if kk != 'questions'} for k, v in quiz_topic_map.items()},
    'subtopics_completed': list(subtopic_by_title.keys()),
    'session_notes': [
        "Kenrich masih kesulitan untuk soal sifat-sifat bangun datar melalui kalimat"
    ],
    'recommendations': recommendations,
}

with open('kenrich_analysis.json', 'w') as f:
    json.dump(analysis, f, indent=2, default=str)
print(f"\n\nSaved analysis to kenrich_analysis.json")
