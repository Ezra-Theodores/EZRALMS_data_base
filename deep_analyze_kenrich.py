import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

USER_ID = "w1kBVxVaMD4Nc3gJ894U"
USER_ID2 = "LKK43rlhECv5zZEuxu4G"

# 1. Get ALL student activities for Kenrich with full details
print("=== ALL Student Activities (Kenrich) ===")
activities = []
for doc in db.collection('student_activities').where('studentId', '==', USER_ID).stream():
    data = doc.to_dict()
    activities.append({'id': doc.id, **data})

for doc in db.collection('student_activities').where('studentId', '==', USER_ID2).stream():
    data = doc.to_dict()
    if doc.id not in [a['id'] for a in activities]:
        activities.append({'id': doc.id, **data})

print(f"Total activities: {len(activities)}")

# Group by type
from collections import Counter
type_counts = Counter(a.get('type', 'unknown') for a in activities)
print(f"Activity types: {dict(type_counts)}")

# Show recent activities sorted by createdAt
activities_sorted = sorted(activities, key=lambda x: str(x.get('createdAt', '')), reverse=True)
print("\n=== Recent 20 Activities ===")
for a in activities_sorted[:20]:
    print(f"  type={a.get('type')}, title={a.get('title')}, xp={a.get('xpEarned')}, created={a.get('createdAt')}")
    # Show subtopicId or quizId if present
    for key in ['subtopicId', 'quizId', 'topicId', 'subtopicName', 'quizName', 'topicName']:
        if key in a and a[key]:
            print(f"    {key}: {a[key]}")

# 2. Find unique studentIds in quiz_attempts to find Kenrich's quiz studentId
print("\n=== Finding Kenrich's quiz_attempts studentId ===")
# Check if any quiz_attempts have studentId matching our users
all_qa_student_ids = set()
for doc in db.collection('quiz_attempts').limit(50).stream():
    data = doc.to_dict()
    all_qa_student_ids.add(data.get('studentId', ''))

print(f"Sample studentIds in quiz_attempts: {list(all_qa_student_ids)[:10]}")

# Search quiz_attempts by studentName "Kenrick" or "Kenrich"
print("\n=== Quiz attempts by name search ===")
for name in ['Kenrich', 'Kenrick', 'Kenrick Harvey Wijaya']:
    qa_docs = list(db.collection('quiz_attempts').where('studentName', '==', name).stream())
    print(f"  studentName='{name}': {len(qa_docs)} attempts")
    for doc in qa_docs[:5]:
        data = doc.to_dict()
        print(f"    quizId={data.get('quizId')}, score={data.get('score')}/{data.get('maxScore')}, studentId={data.get('studentId')}")

# 3. Get all subtopic IDs from his activities to understand what he's studied
print("\n=== Subtopics Kenrich has completed ===")
subtopic_ids = set()
quiz_ids_from_activities = set()
for a in activities:
    if a.get('subtopicId'):
        subtopic_ids.add(a['subtopicId'])
    if a.get('quizId'):
        quiz_ids_from_activities.add(a['quizId'])

print(f"Unique subtopics: {len(subtopic_ids)}")
print(f"Unique quizzes from activities: {len(quiz_ids_from_activities)}")

# Fetch subtopic details
print("\n=== Subtopic Details ===")
for sid in list(subtopic_ids)[:15]:
    sdoc = db.collection('classworkSubtopics').document(sid).get()
    if sdoc.exists:
        sdata = sdoc.to_dict()
        print(f"  {sid}: name={sdata.get('name')}, topicId={sdata.get('topicId')}, type={sdata.get('type')}")
    else:
        print(f"  {sid}: NOT FOUND")

# Fetch quiz details from activities
print("\n=== Quiz Details (from activities) ===")
for qid in list(quiz_ids_from_activities)[:15]:
    qdoc = db.collection('quizzes').document(qid).get()
    if qdoc.exists:
        qdata = qdoc.to_dict()
        print(f"  {qid}: title={qdata.get('title')}, subject={qdata.get('subject')}, topic={qdata.get('topic')}")
    else:
        print(f"  {qid}: NOT FOUND")

# 4. Get ALL quiz_attempts and find which ones might be Kenrich's
print("\n=== Scanning ALL quiz_attempts for Kenrich's studentId ===")
# First get all unique studentIds from quiz_attempts
student_id_map = {}
for doc in db.collection('quiz_attempts').stream():
    data = doc.to_dict()
    sid = data.get('studentId', '')
    if sid and sid not in student_id_map:
        student_id_map[sid] = []
    if sid:
        student_id_map[sid].append({'id': doc.id, **data})

# Check which studentIds have activities matching
for sid, attempts in student_id_map.items():
    # Check if this studentId appears in Kenrich's activities
    for a in activities:
        if a.get('subtopicId') or a.get('quizId'):
            # This might be the same student
            pass
    
    if len(attempts) > 0 and len(attempts) < 200:
        # Show studentIds with reasonable attempt counts
        scores = [a.get('score', 0) for a in attempts]
        max_scores = [a.get('maxScore', 100) for a in attempts]
        avg_pct = sum(s/m*100 for s, m in zip(scores, max_scores) if m > 0) / len(attempts) if attempts else 0
        print(f"  studentId={sid}: {len(attempts)} attempts, avg={avg_pct:.1f}%")

# Save detailed data
result = {
    'activities': activities,
    'subtopic_ids': list(subtopic_ids),
    'quiz_ids_from_activities': list(quiz_ids_from_activities),
    'student_id_map_sample': {k: len(v) for k, v in list(student_id_map.items())[:20]},
}
with open('kenrich_detailed.json', 'w') as f:
    json.dump(result, f, indent=2, default=str)
print(f"\nSaved detailed data to kenrich_detailed.json")
