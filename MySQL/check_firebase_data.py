import firebase_admin
from firebase_admin import credentials, firestore, db
import json

# Path ke file JSON yang Anda berikan
CERT_PATH = r"C:\Users\Admin\Downloads\threebody-933be-firebase-adminsdk-fbsvc-001e64777a.json"

cred = credentials.Certificate(CERT_PATH)
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://threebody-933be-default-rtdb.firebaseio.com/' # URL default biasanya seperti ini
})

def check_firestore():
    print("Checking Firestore...")
    try:
        client = firestore.client()
        collections = client.collections()
        found = False
        for coll in collections:
            print(f"Found Collection: {coll.id}")
            found = True
        if not found:
            print("No Firestore collections found.")
    except Exception as e:
        print(f"Firestore check failed: {e}")

def check_rtdb():
    print("\nChecking Realtime Database...")
    try:
        ref = db.reference('/')
        data = ref.get()
        if data:
            print(f"Found RTDB data keys: {list(data.keys()) if isinstance(data, dict) else 'Root data is not a dict'}")
        else:
            print("No RTDB data found.")
    except Exception as e:
        print(f"RTDB check failed: {e}")

if __name__ == "__main__":
    check_firestore()
    check_rtdb()
