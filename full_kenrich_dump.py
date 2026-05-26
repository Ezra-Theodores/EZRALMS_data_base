import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

USER_ID = "w1kBVxVaMD4Nc3gJ894U"
USER_ID2 = "LKK43rlhECv5zZEuxu4G"

# 1. Get raw student activities - show full structure of first few
print("=== Raw Student Activities (first 5) ===")
for doc in db.collection('student_activities').where('studentId', '==', USER_ID).limit(5).stream():
    data = doc.to_dict()
    print(f"\n--- {doc.id} ---")
    print(json.dumps(data, indent=2, default=str))

# Also check for USER_ID2
print("\n=== Raw Student Activities for USER_ID2 (first 5) ===")
for doc in db.collection('student_activities').where('studentId', '==', USER_ID2).limit(5).stream():
    data = doc.to_dict()
    print(f"\n--- {doc.id} ---")
    print(json.dumps(data, indent=2, default=str))

# 2. Get full session log from user profile
print("\n=== Full Session Log ===")
user_doc = db.collection('users').document(USER_ID2).get()
if user_doc.exists:
    user_data = user_doc.to_dict()
    session_log = user_data.get('sessionLog', [])
    for i, log in enumerate(session_log):
        print(f"\n--- Session {i} ---")
        print(json.dumps(log, indent=2, default=str))

# 3. Check if there are other collections that might have Kenrich's data
print("\n=== Checking other collections ===")
# Check classworkSubtopics for any student-specific data
# Check if there's a studentProgress or similar collection
collections_to_check = ['studentProgress', 'progress', 'studentProgress', 'learningProgress', 
                        'studentQuizAttempts', 'studentQuizProgress', 'subtopicProgress',
                        'studentSubtopicProgress', 'recommendations', 'weaknesses']

for coll_name in collections_to_check:
    try:
        docs = list(db.collection(coll_name).limit(1).stream())
        if docs:
            print(f"  Collection '{coll_name}' EXISTS with {len(list(db.collection(coll_name).stream()))} docs")
            # Search for Kenrich
            for doc in db.collection(coll_name).stream():
                data = doc.to_dict()
                json_str = json.dumps(data, default=str).lower()
                if 'kenrich' in json_str or USER_ID in json_str or USER_ID2 in json_str:
                    print(f"    FOUND KENRICH: {doc.id}")
                    print(f"    {json.dumps(data, indent=2, default=str)[:500]}")
    except Exception as e:
        pass

# 4. Check quiz_attempts structure - what do they look like?
print("\n=== Sample quiz_attempts structure (first 3) ===")
for doc in db.collection('quiz_attempts').limit(3).stream():
    data = doc.to_dict()
    print(f"\n--- {doc.id} ---")
    # Truncate large fields
    for k, v in data.items():
        if isinstance(v, str) and len(v) > 200:
            data[k] = v[:200] + '...'
        elif isinstance(v, list) and len(v) > 5:
            data[k] = v[:5] + ['...']
    print(json.dumps(data, indent=2, default=str))

# 5. Check how many quiz_attempts have empty studentId
print("\n=== Quiz attempts analysis ===")
total_qa = 0
empty_sid = 0
non_empty_sid = 0
student_ids = {}
for doc in db.collection('quiz_attempts').stream():
    total_qa += 1
    data = doc.to_dict()
    sid = data.get('studentId', '')
    if not sid or sid == '':
        empty_sid += 1
    else:
        non_empty_sid += 1
        if sid not in student_ids:
            student_ids[sid] = 0
        student_ids[sid] += 1

print(f"Total quiz_attempts: {total_qa}")
print(f"Empty studentId: {empty_sid}")
print(f"Non-empty studentId: {non_empty_sid}")
print(f"Unique studentIds: {len(student_ids)}")
# Show top studentIds
top_sids = sorted(student_ids.items(), key=lambda x: x[1], reverse=True)[:10]
print(f"Top studentIds: {top_sids}")

# 6. Check if any quiz_attempts have answers that might reveal student identity
# Look for quiz_attempts with recent dates that might match Kenrich's activity
print("\n=== Recent quiz_attempts (last 10 by completedAt) ===")
recent_qa = []
for doc in db.collection('quiz_attempts').stream():
    data = doc.to_dict()
    completed = data.get('completedAt', '')
    if completed:
        recent_qa.append({'id': doc.id, **data})

recent_qa.sort(key=lambda x: str(x.get('completedAt', '')), reverse=True)
for qa in recent_qa[:10]:
    print(f"  completedAt={qa.get('completedAt')}, score={qa.get('score')}/{qa.get('maxScore')}, quizId={qa.get('quizId')}")

# Save everything
output = {
    'session_log': user_data.get('sessionLog', []) if user_doc.exists else [],
    'user_profile': user_data if user_doc.exists else {},
    'quiz_attempts_sample': [dict(doc.to_dict()) for doc in db.collection('quiz_attempts').limit(5).stream()],
    'qa_stats': {'total': total_qa, 'empty_sid': empty_sid, 'non_empty_sid': non_empty_sid, 'top_sids': top_sids},
}
with open('kenrich_full_dump.json', 'w') as f:
    json.dump(output, f, indent=2, default=str)
print(f"\nSaved full dump to kenrich_full_dump.json")
