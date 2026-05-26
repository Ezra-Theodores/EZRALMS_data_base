from student_report_engine import StudentReportEngine

engine = StudentReportEngine()

# Force build session map
engine.get_student_ids("w1kBVxVaMD4Nc3gJ894U")

print("Session map keys containing Kenrich IDs:")
for key, ids in engine._session_map.items():
    if "w1kBVxVaMD4Nc3gJ894U" in ids or "LKK43rlhECv5zZEuxu4G" in ids:
        print(f"  key={key}")
        print(f"  linked_ids={ids}")

# Check what IDs we get
all_ids = engine.get_student_ids("w1kBVxVaMD4Nc3gJ894U")
print(f"\nAll student IDs for Kenrich: {all_ids}")

# Check activities for each ID
for sid in all_ids:
    count = 0
    for doc in engine.db.collection('student_activities').where('studentId', '==', sid).stream():
        count += 1
    print(f"  Activities for {sid}: {count}")
