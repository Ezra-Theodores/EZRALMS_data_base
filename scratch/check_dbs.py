import sqlite3

dbs = ['ezralms.db', 'data_house.db']

for db_file in dbs:
    print(f"\nChecking {db_file}...")
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        print(f"Tables: {tables}")
        
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} rows")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
