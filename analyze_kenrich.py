import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Kenrich's user IDs
USER_ID = "w1kBVxVaMD4Nc3gJ894U"  # Kenrich (sessions)
USER_ID2 = "LKK43rlhECv5zZEuxu4G"  # Kenrick Harvey Wijaya (users)

kenrich_profile = {}

# 1. Get session data for Kenrich
print("=== Session Data (Kenrich) ===")
session_docs = list(db.collection('sessions').where('userId', '==', USER_ID).stream())
for doc in session_docs:
    data = doc.to_dict()
    print(f"  Session: {doc.id}")
    print(f"    displayName: {data.get('displayName')}")
    print(f"    role: {data.get('role')}")
    print(f"    lastLogin: {data.get('lastLogin')}")
    print(f"    createdAt: {data.get('createdAt')}")
    kenrich_profile['session'] = data

# 2. Get user profile for Kenrick
print("\n=== User Profile (Kenrick Harvey Wijaya) ===")
user_doc = db.collection('users').document(USER_ID2).get()
if user_doc.exists:
    user_data = user_doc.to_dict()
    print(f"  displayName: {user_data.get('displayName')}")
    print(f"  profile: {user_data.get('profile')}")
    print(f"  role: {user_data.get('role')}")
    print(f"  metadata: {user_data.get('metadata')}")
    if 'sessionLog' in user_data:
        print(f"  sessionLog entries: {len(user_data['sessionLog'])}")
        for i, log in enumerate(user_data['sessionLog'][:10]):
            print(f"    [{i}] topic={log.get('topic')}, date={log.get('date')}, tutor={log.get('tutorName')}")
            notes = log.get('notes', '')
            if notes:
                print(f"        notes: {notes[:200]}")
    kenrich_profile['user'] = user_data

# 3. Get quiz attempts for Kenrich
print("\n=== Quiz Attempts (Kenrich) ===")
quiz_attempts = []
for uid in [USER_ID, USER_ID2]:
    qa_docs = list(db.collection('quiz_attempts').where('studentId', '==', uid).stream())
    for doc in qa_docs:
        data = doc.to_dict()
        quiz_attempts.append({'id': doc.id, **data})
        print(f"  quizId={data.get('quizId')}, score={data.get('score')}/{data.get('maxScore')}, completed={data.get('completedAt')}")

# Also search by studentName
for uid in [USER_ID, USER_ID2]:
    qa_docs2 = list(db.collection('quiz_attempts').where('studentName', '==', 'Kenrich').stream())
    for doc in qa_docs2:
        data = doc.to_dict()
        if doc.id not in [qa['id'] for qa in quiz_attempts]:
            quiz_attempts.append({'id': doc.id, **data})
            print(f"  (by name) quizId={data.get('quizId')}, score={data.get('score')}/{data.get('maxScore')}")

kenrich_profile['quiz_attempts'] = quiz_attempts
print(f"  Total quiz attempts: {len(quiz_attempts)}")

# 4. Get attendance for Kenrich
print("\n=== Attendance (Kenrich) ===")
attendance = []
for uid in [USER_ID, USER_ID2]:
    att_docs = list(db.collection('attendance').where('studentId', '==', uid).stream())
    for doc in att_docs:
        data = doc.to_dict()
        attendance.append({'id': doc.id, **data})
        if len(attendance) <= 5:
            print(f"  date={data.get('date')}, status={data.get('status')}, class={data.get('className')}")

kenrich_profile['attendance'] = attendance
print(f"  Total attendance records: {len(attendance)}")

# 5. Get student activities for Kenrich
print("\n=== Student Activities (Kenrich) ===")
activities = []
for uid in [USER_ID, USER_ID2]:
    sa_docs = list(db.collection('student_activities').where('studentId', '==', uid).stream())
    for doc in sa_docs:
        data = doc.to_dict()
        activities.append({'id': doc.id, **data})
        if len(activities) <= 5:
            print(f"  type={data.get('type')}, title={data.get('title')}, xp={data.get('xpEarned')}")

kenrich_profile['activities'] = activities
print(f"  Total activities: {len(activities)}")

# 6. Get XP transactions for Kenrich
print("\n=== XP Transactions (Kenrich) ===")
xp_trans = []
for uid in [USER_ID, USER_ID2]:
    xp_docs = list(db.collection('xp_transactions').where('userId', '==', uid).stream())
    for doc in xp_docs:
        data = doc.to_dict()
        xp_trans.append({'id': doc.id, **data})
        if len(xp_trans) <= 5:
            print(f"  amount={data.get('amount')}, type={data.get('type')}, desc={data.get('description')}")

kenrich_profile['xp_transactions'] = xp_trans
print(f"  Total XP transactions: {len(xp_trans)}")

# 7. Get student packages for Kenrich
print("\n=== Student Packages (Kenrich) ===")
packages = []
for uid in [USER_ID, USER_ID2]:
    sp_docs = list(db.collection('student_packages').where('studentId', '==', uid).stream())
    for doc in sp_docs:
        data = doc.to_dict()
        packages.append({'id': doc.id, **data})
        print(f"  packageId={data.get('packageId')}, status={data.get('status')}, remaining={data.get('sessionsRemaining')}")

kenrich_profile['packages'] = packages

# 8. Get tasks for Kenrich
print("\n=== Tasks (Kenrich) ===")
tasks = []
for uid in [USER_ID, USER_ID2]:
    ta_docs = list(db.collection('task_assignments').where('studentId', '==', uid).stream())
    for doc in ta_docs:
        data = doc.to_dict()
        tasks.append({'id': doc.id, **data})
        print(f"  taskId={data.get('taskId')}, status={data.get('status')}")

kenrich_profile['tasks'] = tasks

# 9. Get weekly achievements
print("\n=== Weekly Achievements (Kenrich) ===")
achievements = []
for uid in [USER_ID, USER_ID2]:
    wa_docs = list(db.collection('weekly_achievements').where('studentId', '==', uid).stream())
    for doc in wa_docs:
        data = doc.to_dict()
        achievements.append({'id': doc.id, **data})
        print(f"  week={data.get('week')}, xp={data.get('xpEarned')}, achievements={data.get('achievements')}")

kenrich_profile['achievements'] = achievements

# Analyze quiz performance by topic
print("\n=== QUIZ PERFORMANCE ANALYSIS ===")
if quiz_attempts:
    # Get quiz details for each attempt
    quiz_ids = list(set(qa.get('quizId') for qa in quiz_attempts if qa.get('quizId')))
    print(f"  Unique quizzes attempted: {len(quiz_ids)}")
    
    # Fetch quiz details
    quiz_details = {}
    for qid in quiz_ids[:20]:  # Limit to avoid too many requests
        qdoc = db.collection('quizzes').document(qid).get()
        if qdoc.exists:
            qdata = qdoc.to_dict()
            quiz_details[qid] = {
                'title': qdata.get('title', ''),
                'subject': qdata.get('subject', ''),
                'grade': qdata.get('grade', ''),
                'difficulty': qdata.get('difficulty', ''),
                'topic': qdata.get('topic', ''),
            }
    
    # Calculate scores
    scores = []
    for qa in quiz_attempts:
        score = qa.get('score', 0)
        max_score = qa.get('maxScore', 100)
        pct = (score / max_score * 100) if max_score > 0 else 0
        qid = qa.get('quizId', '')
        quiz_info = quiz_details.get(qid, {})
        scores.append({
            'quiz_id': qid,
            'score': score,
            'max_score': max_score,
            'percentage': round(pct, 1),
            'topic': quiz_info.get('topic', 'unknown'),
            'subject': quiz_info.get('subject', 'unknown'),
            'title': quiz_info.get('title', qid),
            'completed_at': str(qa.get('completedAt', '')),
        })
        print(f"  {quiz_info.get('title', qid)[:50]}: {score}/{max_score} = {pct:.1f}% | topic={quiz_info.get('topic', 'N/A')}")
    
    # Average score
    avg_score = sum(s['percentage'] for s in scores) / len(scores) if scores else 0
    print(f"\n  Average score: {avg_score:.1f}%")
    
    # Weak topics (< 70%)
    weak_topics = {}
    for s in scores:
        topic = s['topic']
        if s['percentage'] < 70:
            if topic not in weak_topics:
                weak_topics[topic] = []
            weak_topics[topic].append(s['percentage'])
    
    print(f"\n  WEAK TOPICS (< 70%):")
    for topic, scores_list in sorted(weak_topics.items(), key=lambda x: sum(x[1])/len(x[1])):
        avg = sum(scores_list) / len(scores_list)
        print(f"    {topic}: avg {avg:.1f}% ({len(scores_list)} attempts)")
    
    kenrich_profile['analysis'] = {
        'average_score': round(avg_score, 1),
        'total_attempts': len(scores),
        'weak_topics': {k: round(sum(v)/len(v), 1) for k, v in weak_topics.items()},
        'scores': scores,
    }

# Save comprehensive profile
with open('kenrich_profile.json', 'w') as f:
    json.dump(kenrich_profile, f, indent=2, default=str)
print(f"\nSaved comprehensive profile to kenrich_profile.json")
