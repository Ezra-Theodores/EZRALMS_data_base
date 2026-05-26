import mysql.connector
import json
import random
import os

MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'firebase_sync'
}

OUTPUT_PATH = r"C:\Users\Admin\Repo\EzraLms_automation\KURIKULUM EZRA\KURIKULUM UMUM\SAJ_G6_30_Modifikasi.md"

def generate_modified_saj():
    try:
        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        # Ambil kuis-kuis SAJ Kelas 6
        query = "SELECT questions FROM quizzes WHERE grade = '6' AND (title LIKE '%SAJ%' OR title LIKE '%US%' OR title LIKE '%G6%')"
        cursor.execute(query)
        rows = cursor.fetchall()

        all_questions = []
        for row in rows:
            if row['questions']:
                try:
                    q_list = json.loads(row['questions'])
                    if isinstance(q_list, list):
                        all_questions.extend(q_list)
                except (json.JSONDecodeError, TypeError, ValueError):
                    continue

        if len(all_questions) < 30:
            print(f"Hanya ditemukan {len(all_questions)} soal, mengambil semuanya.")
            selected_questions = all_questions
        else:
            # Mengacak dan mengambil 30 soal
            selected_questions = random.sample(all_questions, 30)

        # Modifikasi ringan (misalnya membersihkan metadata tertentu agar bersih sebagai kuis baru)
        for i, q in enumerate(selected_questions):
            q['id'] = f"saj_g6_mod_{i+1}"
            # Menghapus field yang tidak diperlukan jika ada
            q.pop('quizId', None)
            
        # Membuat struktur kuis final
        new_quiz = {
            "title": "SAJ Matematika Kelas 6 - 30 Soal Modifikasi",
            "grade": "6",
            "subject": "Math",
            "type": "SAJ",
            "questionCount": len(selected_questions),
            "questions": selected_questions
        }

        # Simpan ke Markdown
        os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
        
        md_content = "# Kuis SAJ Kelas 6 - 30 Soal Modifikasi\n\n"
        md_content += "Kuis ini disusun secara otomatis dari bank soal SAJ G6 yang ada di database.\n\n"
        md_content += "```json\n"
        md_content += json.dumps(new_quiz, indent=2)
        md_content += "\n```\n"

        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        print(f"Berhasil membuat kuis modifikasi di: {OUTPUT_PATH}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    generate_modified_saj()
