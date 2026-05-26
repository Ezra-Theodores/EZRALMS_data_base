import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Initialize Firebase
cred_path = os.path.join("DATA_HOUSE_EZRALMS", "firebase_credentials.json")
if not os.path.exists(cred_path):
    cred_path = "firebase_credentials.json"

print(f"Using credentials: {cred_path}")
cred = credentials.Certificate(cred_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Search for Kenrich in users collection
print("\n=== Searching users collection ===")
users_ref = db.collection('users')
docs = users_ref.stream()
kenrich_users = []
for doc in docs:
    data = doc.to_dict()
    name = data.get('name', '') or ''
    email = data.get('email', '') or ''
    if 'kenrich' in name.lower() or 'kenrich' in email.lower() or 'ken' in name.lower():
        kenrich_users.append({'id': doc.id, **data})
        print(f"  Found: {doc.id} -> name={name}, email={email}")

if not kenrich_users:
    print("  No users found with 'Kenrich' in name/email")
    # Show some sample users
    print("\n  Sample users (first 10):")
    users_ref2 = db.collection('users')
    for doc in users_ref2.limit(10).stream():
        data = doc.to_dict()
        print(f"    {doc.id}: name={data.get('name','')}, email={data.get('email','')}, role={data.get('role','')}")

# Search in attendance
print("\n=== Searching attendance collection ===")
att_ref = db.collection('attendance')
found_att = 0
for doc in att_ref.stream():
    data = doc.to_dict()
    name = str(data.get('studentName', '') or data.get('student_name', '') or data.get('name', '') or '').lower()
    sid = str(data.get('studentId', '') or data.get('student_id', '') or '').lower()
    if 'kenrich' in name or 'kenrich' in sid:
        found_att += 1
        print(f"  Found: {doc.id} -> {data}")
        if found_att >= 5:
            break

if found_att == 0:
    print("  No attendance records found for Kenrich")

# Search in quiz_attempts
print("\n=== Searching quiz_attempts collection ===")
qa_ref = db.collection('quiz_attempts')
found_qa = 0
for doc in qa_ref.stream():
    data = doc.to_dict()
    name = str(data.get('studentName', '') or data.get('student_name', '') or '').lower()
    sid = str(data.get('studentId', '') or data.get('student_id', '') or '').lower()
    if 'kenrich' in name or 'kenrich' in sid:
        found_qa += 1
        if found_qa <= 10:
            print(f"  Found: {doc.id} -> quizId={data.get('quizId','')}, score={data.get('score','')}, maxScore={data.get('maxScore','')}, completedAt={data.get('completedAt','')}")

if found_qa == 0:
    print("  No quiz attempts found for Kenrich")

# Search in student_activities
print("\n=== Searching student_activities collection ===")
sa_ref = db.collection('student_activities')
found_sa = 0
for doc in sa_ref.stream():
    data = doc.to_dict()
    sid = str(data.get('studentId', '') or data.get('student_id', '') or '').lower()
    if 'kenrich' in sid:
        found_sa += 1
        if found_sa <= 5:
            print(f"  Found: {doc.id} -> {data}")

if found_sa == 0:
    print("  No student activities found for Kenrich")

print(f"\n=== Summary ===")
print(f"Users matching Kenrich: {len(kenrich_users)}")
print(f"Attendance records: {found_att}")
print(f"Quiz attempts: {found_qa}")
print(f"Student activities: {found_sa}")

# Save Kenrich data
if kenrich_users:
    with open('kenrich_firebase.json', 'w') as f:
        json.dump(kenrich_users, f, indent=2, default=str)
    print("\nSaved Kenrich user data to kenrich_firebase.json")
