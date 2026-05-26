import mysql.connector
import json

MYSQL_CONFIG = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'firebase_sync'
}

def generate_report():
    try:
        cnx = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = cnx.cursor(dictionary=True)

        # 1. Ambil semua kuis
        cursor.execute("SELECT title, grade, subject, firestore_id FROM quizzes")
        quizzes = cursor.fetchall()

        # 2. Ambil semua kelas untuk pemetaan
        cursor.execute("SELECT name, grade, subject, studentIds FROM classes")
        classes = cursor.fetchall()

        print(f"{'No':<4} | {'Judul Kuis':<30} | {'Grade':<10} | {'Kelas Terkait':<25} | {'Siswa':<6}")
        print("-" * 85)

        for i, quiz in enumerate(quizzes, 1):
            quiz_grade = str(quiz['grade'])
            quiz_subject = str(quiz['subject'])
            
            # Cari kelas yang cocok berdasarkan grade dan subject
            related_classes = []
            total_students = 0
            
            for cls in classes:
                # Logika pencocokan: Grade dan Subject harus sama
                if str(cls['grade']) == quiz_grade and str(cls['subject']) == quiz_subject:
                    related_classes.append(cls['name'])
                    
                    # Hitung jumlah siswa dari string/JSON list studentIds
                    try:
                        ids = json.loads(cls['studentIds'])
                        if isinstance(ids, list):
                            total_students += len(ids)
                    except (json.JSONDecodeError, TypeError, ValueError):
                        # Jika bukan JSON, mungkin string kosong atau format lain
                        if cls['studentIds'] and cls['studentIds'] != 'None':
                            total_students += 1 # Asumsi minimal 1 jika ada isinya tapi bukan list

            class_names = ", ".join(related_classes) if related_classes else "Tidak ada kelas cocok"
            
            print(f"{i:<4} | {quiz['title'][:30]:<30} | {quiz_grade:<10} | {class_names[:25]:<25} | {total_students:<6}")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()

if __name__ == "__main__":
    generate_report()
