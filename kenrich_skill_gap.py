import firebase_admin
from firebase_admin import credentials, firestore
import json
from collections import defaultdict

cred = credentials.Certificate("DATA_HOUSE_EZRALMS/firebase_credentials.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

USER_ID = "w1kBVxVaMD4Nc3gJ894U"

# Get all quiz activities
quiz_activities = []
for doc in db.collection('student_activities').where('studentId', '==', USER_ID).stream():
    data = doc.to_dict()
    if data.get('type') == 'quiz_completed':
        quiz_activities.append(data)

# Find his WORST quizzes (score < 50%)
worst_quizzes = [q for q in quiz_activities if q.get('score', 0) / q.get('maxScore', 100) < 0.5]
worst_quizzes.sort(key=lambda x: x.get('score', 0) / x.get('maxScore', 100))

print("=== KENRICH'S WORST QUIZZES (< 50%) ===")
for q in worst_quizzes:
    pct = q['score'] / q['maxScore'] * 100
    print(f"  {q['referenceTitle']}: {q['score']}/{q['maxScore']} = {pct:.0f}% | quizId={q['referenceId']} | attemptId={q.get('attemptId')}")

# Get question-level analysis for worst quizzes
print("\n=== QUESTION-LEVEL ANALYSIS ===")
for q in worst_quizzes[:8]:
    quiz_id = q['referenceId']
    attempt_id = q.get('attemptId')
    
    # Get the quiz details
    qdoc = db.collection('quizzes').document(quiz_id).get()
    if not qdoc.exists:
        print(f"\n  Quiz {quiz_id}: NOT FOUND")
        continue
    
    qdata = qdoc.to_dict()
    questions = qdata.get('questions', [])
    
    # Get the attempt details
    adoc = db.collection('quiz_attempts').document(attempt_id).get()
    if not adoc.exists:
        print(f"\n  Attempt {attempt_id}: NOT FOUND for quiz {q['referenceTitle']}")
        continue
    
    adata = adoc.to_dict()
    answers = adata.get('answers', {})
    correct_count = adata.get('correctCount', 0)
    
    print(f"\n  --- {q['referenceTitle']} (score: {q['score']}/{q['maxScore']}) ---")
    print(f"  Correct: {correct_count}/{len(questions)}")
    
    # Analyze each question
    wrong_questions = []
    for i, question in enumerate(questions):
        if not isinstance(question, dict):
            continue
        user_answer = answers.get(str(i))
        correct_answer = question.get('ans')
        
        # Handle ans being a list
        if isinstance(correct_answer, list):
            correct_answer = correct_answer[0] if correct_answer else None
        
        if user_answer is not None and correct_answer is not None and user_answer != correct_answer:
            wrong_questions.append({
                'q_num': i,
                'question': question.get('id_q', '')[:80],
                'topic': question.get('topic', ''),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'options': question.get('id_options', question.get('options', [])),
            })
    
    if wrong_questions:
        print(f"  WRONG ANSWERS ({len(wrong_questions)}):")
        for wq in wrong_questions:
            print(f"    Q{wq['q_num']+1}: [{wq['topic']}] {wq['question']}")
            print(f"      Your answer: {wq['user_answer']}, Correct: {wq['correct_answer']}")
    
    # Group wrong answers by topic
    topic_errors = defaultdict(int)
    for wq in wrong_questions:
        topic_errors[wq['topic']] += 1
    
    if topic_errors:
        print(f"  ERROR TOPICS:")
        for topic, count in sorted(topic_errors.items(), key=lambda x: x[1], reverse=True):
            print(f"    {topic}: {count} errors")

# Analyze performance trends over time
print("\n=== PERFORMANCE TREND (by month) ===")
from datetime import datetime
monthly_scores = defaultdict(list)
for q in quiz_activities:
    ts = q.get('timestamp', '')
    if ts:
        try:
            if hasattr(ts, 'strftime'):
                month = ts.strftime('%Y-%m')
            else:
                month = str(ts)[:7]
            pct = q['score'] / q['maxScore'] * 100
            monthly_scores[month].append(pct)
        except:
            pass

for month in sorted(monthly_scores.keys()):
    scores = monthly_scores[month]
    avg = sum(scores) / len(scores)
    print(f"  {month}: {len(scores)} quizzes, avg={avg:.1f}%")

# Identify specific skill gaps
print("\n=== SKILL GAP ANALYSIS ===")
# Group by quiz title pattern
skill_categories = {
    'Bangun Datar (Geometry)': ['BANGUN DATAR', 'Bangun datar'],
    'Algebra': ['Algebra', 'ALGEBRA'],
    'Multiplication': ['Multiplication', 'Multiplication Intro'],
    'Division': ['Division', 'Pembagian', 'PEMBAGIAN'],
    'Number Sense': ['menghitung', 'Sorting', 'Explore', 'Number Bound'],
    'Addition/Subtraction': ['Addition', 'subtraction', 'Add Subt', 'POKE ADD'],
    'Competition Math': ['OSN', 'IOB', 'JISMO', 'HXC', 'IKMC'],
    'Intervals/Sequences': ['INTERVAL', 'PROGRESSION'],
    'Word Problems': ['Tambah Tanggal'],
}

skill_scores = defaultdict(list)
for q in quiz_activities:
    title = q.get('referenceTitle', '')
    pct = q['score'] / q['maxScore'] * 100
    for category, keywords in skill_categories.items():
        if any(kw.lower() in title.lower() for kw in keywords):
            skill_scores[category].append(pct)
            break

print(f"\n{'Category':<35} {'Attempts':>10} {'Avg %':>10} {'Status':>15}")
print("-" * 70)
for category in sorted(skill_scores.keys(), key=lambda x: sum(skill_scores[x])/len(skill_scores[x])):
    scores = skill_scores[category]
    avg = sum(scores) / len(scores)
    status = "STRONG" if avg >= 80 else "OK" if avg >= 60 else "WEAK" if avg >= 40 else "CRITICAL"
    print(f"  {category:<33} {len(scores):>10} {avg:>9.1f}% {status:>15}")

# Save detailed analysis
detailed = {
    'worst_quizzes': [{
        'title': q['referenceTitle'],
        'score': q['score'],
        'max_score': q['maxScore'],
        'percentage': round(q['score']/q['maxScore']*100, 1),
        'quiz_id': q['referenceId'],
        'attempt_id': q.get('attemptId'),
    } for q in worst_quizzes],
    'skill_gaps': {
        k: {
            'attempts': len(v),
            'average': round(sum(v)/len(v), 1),
            'status': "STRONG" if sum(v)/len(v) >= 80 else "OK" if sum(v)/len(v) >= 60 else "WEAK" if sum(v)/len(v) >= 40 else "CRITICAL",
        } for k, v in skill_scores.items()
    },
    'monthly_trend': {k: {'count': len(v), 'avg': round(sum(v)/len(v), 1)} for k, v in monthly_scores.items()},
}

with open('kenrich_detailed_analysis.json', 'w') as f:
    json.dump(detailed, f, indent=2, default=str)
print(f"\nSaved detailed analysis to kenrich_detailed_analysis.json")
