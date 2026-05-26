import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Check sessions that link to either ID
print("=== Sessions for w1kBVxVaMD4Nc3gJ894U ===")
for doc in db.collection('sessions').stream():
    data = doc.to_dict()
    if data.get('userId') == 'w1kBVxVaMD4Nc3gJ894U' or data.get('actualUserId') == 'w1kBVxVaMD4Nc3gJ894U' or data.get('uid') == 'w1kBVxVaMD4Nc3gJ894U':
        print(f"  session_id={doc.id}")
        print(f"    userId={data.get('userId')}")
        print(f"    actualUserId={data.get('actualUserId')}")
        print(f"    uid={data.get('uid')}")
        print(f"    displayName={data.get('displayName')}")

print("\n=== Sessions for LKK43rlhECv5zZEuxu4G ===")
for doc in db.collection('sessions').stream():
    data = doc.to_dict()
    if data.get('userId') == 'LKK43rlhECv5zZEuxu4G' or data.get('actualUserId') == 'LKK43rlhECv5zZEuxu4G' or data.get('uid') == 'LKK43rlhECv5zZEuxu4G':
        print(f"  session_id={doc.id}")
        print(f"    userId={data.get('userId')}")
        print(f"    actualUserId={data.get('actualUserId')}")
        print(f"    uid={data.get('uid')}")
        print(f"    displayName={data.get('displayName')}")

# Check user profile for LKK43
print("\n=== User LKK43rlhECv5zZEuxu4G ===")
doc = db.collection('users').document('LKK43rlhECv5zZEuxu4G').get()
if doc.exists:
    data = doc.to_dict()
    print(f"  displayName={data.get('displayName')}")
    print(f"  email={data.get('email')}")
    print(f"  profile={data.get('profile')}")
