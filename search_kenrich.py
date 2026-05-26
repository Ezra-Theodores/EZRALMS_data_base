import sqlite3
import json

conn = sqlite3.connect('data_house.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Check all users to see naming patterns
c.execute("SELECT user_id, name, email, role, xp FROM users LIMIT 20")
rows = c.fetchall()
print("=== Sample Users (first 20) ===")
for r in rows:
    print(f"  {dict(r)}")

# Search partial matches
c.execute("SELECT user_id, name, email, role, xp FROM users WHERE name LIKE '%Ken%' OR name LIKE '%ken%' OR name LIKE '%rich%' OR name LIKE '%Rich%'")
rows = c.fetchall()
print(f"\n=== Partial name matches ===")
print(f"Found {len(rows)}")
for r in rows:
    print(f"  {dict(r)}")

# Check if there are any student names in quiz_attempts that contain Ken
c.execute("SELECT DISTINCT student_name, student_id FROM quiz_attempts WHERE student_name LIKE '%Ken%' OR student_name LIKE '%ken%' LIMIT 10")
rows = c.fetchall()
print(f"\n=== Quiz attempts with 'Ken' in name ===")
for r in rows:
    print(f"  {dict(r)}")

# Check attendance for any Ken
c.execute("SELECT DISTINCT student_name, student_id FROM attendance WHERE student_name LIKE '%Ken%' OR student_name LIKE '%ken%' LIMIT 10")
rows = c.fetchall()
print(f"\n=== Attendance with 'Ken' in name ===")
for r in rows:
    print(f"  {dict(r)}")

# Total unique students in quiz_attempts
c.execute("SELECT COUNT(DISTINCT student_id) as cnt FROM quiz_attempts WHERE student_id != '' AND student_id IS NOT NULL")
cnt = c.fetchone()[0]
print(f"\nTotal unique students in quiz_attempts: {cnt}")

# Show some sample quiz_attempts to understand data
c.execute("SELECT student_id, student_name, quiz_id, score, max_score, completed_at FROM quiz_attempts LIMIT 10")
rows = c.fetchall()
print(f"\n=== Sample quiz_attempts ===")
for r in rows:
    print(f"  {dict(r)}")

# Show some sample attendance
c.execute("SELECT student_id, student_name, class_name, status, attendance_date FROM attendance LIMIT 10")
rows = c.fetchall()
print(f"\n=== Sample attendance ===")
for r in rows:
    print(f"  {dict(r)}")

conn.close()
