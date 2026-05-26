from student_report_engine import StudentReportEngine

engine = StudentReportEngine()

# Check activities for LKK43 user
count = 0
quiz_count = 0
subtopic_count = 0
for doc in engine.db.collection('student_activities').where('studentId', '==', 'LKK43rlhECv5zZEuxu4G').stream():
    count += 1
    data = doc.to_dict()
    if data.get('type') == 'quiz_completed':
        quiz_count += 1
    elif data.get('type') == 'subtopic_completed':
        subtopic_count += 1

print(f"LKK43rlhECv5zZEuxu4G activities: {count} (quiz={quiz_count}, subtopic={subtopic_count})")

# Check for w1kBVxVaMD4Nc3gJ894U
count2 = 0
quiz_count2 = 0
subtopic_count2 = 0
for doc in engine.db.collection('student_activities').where('studentId', '==', 'w1kBVxVaMD4Nc3gJ894U').stream():
    count2 += 1
    data = doc.to_dict()
    if data.get('type') == 'quiz_completed':
        quiz_count2 += 1
    elif data.get('type') == 'subtopic_completed':
        subtopic_count2 += 1

print(f"w1kBVxVaMD4Nc3gJ894U activities: {count2} (quiz={quiz_count2}, subtopic={subtopic_count2})")

# Total combined
print(f"\nCombined: {count + count2} (quiz={quiz_count + quiz_count2}, subtopic={subtopic_count + subtopic_count2})")
