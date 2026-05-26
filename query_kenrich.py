import sqlite3
import json

def query_kenrich():
    results = {}
    
    # Check ezralms.db
    conn1 = sqlite3.connect('ezralms.db')
    conn1.row_factory = sqlite3.Row
    c1 = conn1.cursor()
    
    c1.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables1 = [row[0] for row in c1.fetchall()]
    results['ezralms_tables'] = tables1
    
    if 'attendance' in tables1:
        c1.execute("SELECT * FROM attendance WHERE student_name LIKE '%Kenrich%' OR student_id LIKE '%Kenrich%'")
        rows = c1.fetchall()
        results['ezralms_attendance'] = [dict(r) for r in rows]
        print(f"ezralms.db attendance: {len(rows)} records")
        for r in rows[:5]:
            print(f"  {dict(r)}")
    
    conn1.close()
    
    # Check data_house.db
    conn2 = sqlite3.connect('data_house.db')
    conn2.row_factory = sqlite3.Row
    c2 = conn2.cursor()
    
    c2.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables2 = [row[0] for row in c2.fetchall()]
    results['data_house_tables'] = tables2
    
    if 'users' in tables2:
        c2.execute("SELECT * FROM users WHERE name LIKE '%Kenrich%' OR user_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_users'] = [dict(r) for r in rows]
        print(f"\ndata_house.db users: {len(rows)} records")
        for r in rows:
            print(f"  {dict(r)}")
    
    if 'attendance' in tables2:
        c2.execute("SELECT * FROM attendance WHERE student_name LIKE '%Kenrich%' OR student_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_attendance'] = [dict(r) for r in rows]
        print(f"\ndata_house.db attendance: {len(rows)} records")
        for r in rows[:5]:
            print(f"  {dict(r)}")
    
    if 'quiz_attempts' in tables2:
        c2.execute("SELECT * FROM quiz_attempts WHERE student_name LIKE '%Kenrich%' OR student_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_quiz_attempts'] = [dict(r) for r in rows]
        print(f"\ndata_house.db quiz_attempts: {len(rows)} records")
        for r in rows[:15]:
            d = dict(r)
            # Truncate raw_json for display
            if 'raw_json' in d:
                d['raw_json'] = d['raw_json'][:200] + '...' if len(d.get('raw_json','')) > 200 else d['raw_json']
            print(f"  {d}")
    
    if 'student_activities' in tables2:
        c2.execute("SELECT * FROM student_activities WHERE student_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_activities'] = [dict(r) for r in rows]
        print(f"\ndata_house.db student_activities: {len(rows)} records")
        for r in rows[:5]:
            print(f"  {dict(r)}")
    
    if 'weekly_achievements' in tables2:
        c2.execute("SELECT * FROM weekly_achievements WHERE student_name LIKE '%Kenrich%' OR student_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_achievements'] = [dict(r) for r in rows]
        print(f"\ndata_house.db weekly_achievements: {len(rows)} records")
        for r in rows:
            print(f"  {dict(r)}")
    
    if 'xp_transactions' in tables2:
        c2.execute("SELECT * FROM xp_transactions WHERE user_id LIKE '%Kenrich%'")
        rows = c2.fetchall()
        results['data_house_xp'] = [dict(r) for r in rows]
        print(f"\ndata_house.db xp_transactions: {len(rows)} records")
        for r in rows[:10]:
            print(f"  {dict(r)}")
    
    if 'quizzes' in tables2:
        c2.execute("SELECT COUNT(*) as cnt FROM quizzes")
        cnt = c2.fetchone()[0]
        results['quizzes_count'] = cnt
        print(f"\ndata_house.db quizzes: {cnt} total")
    
    if 'questions' in tables2:
        c2.execute("SELECT COUNT(*) as cnt FROM questions")
        cnt = c2.fetchone()[0]
        results['questions_count'] = cnt
        print(f"data_house.db questions: {cnt} total")
        
    if 'classwork_topics' in tables2:
        c2.execute("SELECT COUNT(*) as cnt FROM classwork_topics")
        cnt = c2.fetchone()[0]
        results['topics_count'] = cnt
        print(f"data_house.db classwork_topics: {cnt} total")
        
    if 'classwork_subtopics' in tables2:
        c2.execute("SELECT COUNT(*) as cnt FROM classwork_subtopics")
        cnt = c2.fetchone()[0]
        results['subtopics_count'] = cnt
        print(f"data_house.db classwork_subtopics: {cnt} total")
    
    conn2.close()
    
    # Save results
    with open('kenrich_data.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved to kenrich_data.json")

query_kenrich()
