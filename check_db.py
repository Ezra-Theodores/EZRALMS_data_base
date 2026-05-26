import sqlite3

conn = sqlite3.connect('ezralms.db')
c = conn.cursor()

c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print("Tables:", [row[0] for row in c.fetchall()])

c.execute('PRAGMA table_info(attendance)')
print("\nSchema attendance:")
for row in c.fetchall():
    print(row)

c.execute('SELECT * FROM attendance LIMIT 5')
print("\nSample data:")
for row in c.fetchall():
    print(row)

conn.close()
