import sqlite3
import sys

db_path = sys.argv[1]
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
for row in cursor.fetchall():
    print(f"Table: {row[0]}")
    print(f"Schema:\n{row[1]}\n")
conn.close()
