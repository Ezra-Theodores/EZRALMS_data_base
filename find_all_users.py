import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Get ALL users and find ones with actual names
print("=== All users with non-empty names ===")
users_with_names = []
for doc in db.collection('users').stream():
    data = doc.to_dict()
    name = data.get('name', '') or ''
    email = data.get('email', '') or ''
    if name.strip():
        users_with_names.append({'id': doc.id, 'name': name, 'email': email, 'role': data.get('role',''), 'xp': data.get('xp', 0)})
        print(f"  {doc.id}: name='{name}', email={email}, role={data.get('role','')}")

print(f"\nTotal users with names: {len(users_with_names)}")

# Also check if there's a 'students' or 'profiles' collection
collections = ['students', 'profiles', 'studentProfiles', 'members', 'pupils']
for coll in collections:
    try:
        docs = list(db.collection(coll).limit(1).stream())
        if docs:
            print(f"\n=== Collection '{coll}' exists ===")
            for doc in db.collection(coll).stream():
                data = doc.to_dict()
                name = str(data.get('name', '') or data.get('studentName', '') or data.get('fullName', '') or '').lower()
                if 'kenrich' in name:
                    print(f"  FOUND KENRICH: {doc.id} -> {data}")
    except Exception as e:
        pass

# Search ALL collections for "kenrich"
print("\n=== Searching ALL collections for 'kenrich' ===")
all_collections = db.collections()
for coll in all_collections:
    coll_name = coll.id
    try:
        for doc in coll.stream():
            data = doc.to_dict()
            json_str = json.dumps(data, default=str).lower()
            if 'kenrich' in json_str:
                print(f"  FOUND in '{coll_name}'/{doc.id}")
                print(f"    {json.dumps(data, indent=2, default=str)[:500]}")
                break  # Just show first match per collection
    except Exception as e:
        pass

# Save users with names
with open('users_with_names.json', 'w') as f:
    json.dump(users_with_names, f, indent=2, default=str)
print(f"\nSaved {len(users_with_names)} users to users_with_names.json")
