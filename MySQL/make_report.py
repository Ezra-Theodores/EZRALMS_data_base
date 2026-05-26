import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import os
import sys

# Konfigurasi Path
CERT_PATH = "firebase_credentials.json"

def initialize_firebase():
    if not firebase_admin._apps:
        cred = credentials.Certificate(CERT_PATH)
        firebase_admin.initialize_app(cred)
    return firestore.client()

def find_user_by_username(db, username):
    """Mencari UID user berdasarkan username atau name."""
    users_ref = db.collection('users')
    docs = users_ref.stream()
    for doc in docs:
        d = doc.to_dict()
        sd = d.get('studentDetails', {})
        # Cek username, name, atau studentDetails['username'] (case-insensitive)
        if username.lower() == str(d.get('username', '')).lower() or \
           username.lower() == str(d.get('name', '')).lower() or \
           username.lower() == str(sd.get('username', '')).lower():
            return doc.id, d.get('username') or sd.get('username') or d.get('name')
    return None, None

def make_report(username):
    db = initialize_firebase()
    uid, actual_name = find_user_by_username(db, username)
    
    if not uid:
        print(f"Error: User '{username}' tidak ditemukan di database.")
        return

    print(f"Mengumpulkan data untuk: {actual_name} (ID: {uid})...")
    
    attempts_ref = db.collection('quiz_attempts').where('userId', '==', uid)
    docs = attempts_ref.stream()
    
    data = []
    for doc in docs:
        d = doc.to_dict()
        data.append({
            'Quiz Title': d.get('quizTitle'),
            'Score': d.get('score'),
            'Max Score': d.get('maxScore', 100),
            'Correct': d.get('correctCount'),
            'Total Q': d.get('totalQuestions'),
            'Date': d.get('completedAt')
        })
    
    if not data:
        print(f"Tidak ada data kuis ditemukan untuk {actual_name}.")
        return

    df = pd.DataFrame(data)
    
    # Bersihkan Timezone untuk Excel
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None)
    
    # Sortir berdasarkan tanggal terbaru
    df = df.sort_values(by='Date', ascending=False)
    
    # Ambil attempt terbaru untuk setiap kuis unik
    report_df = df.groupby('Quiz Title').first().reset_index()
    
    # Hitung Persentase
    report_df['Percentage'] = (report_df['Score'] / report_df['Max Score'] * 100).round(2)
    
    # Pilih dan urutkan kolom
    final_report = report_df[['Date', 'Quiz Title', 'Score', 'Max Score', 'Percentage', 'Correct', 'Total Q']]
    
    output_file = f"Raport_Quiz_{actual_name.replace(' ', '_')}.xlsx"
    final_report.to_excel(output_file, index=False)
    
    print(f"Berhasil! Raport disimpan di: {output_file}")
    return output_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        name = input("Masukkan nama/username siswa: ")
    else:
        name = sys.argv[1]
    
    make_report(name)
