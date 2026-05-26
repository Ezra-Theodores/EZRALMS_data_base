from data_house import DataHouse
dh = DataHouse()
conn = dh.connect()
c = conn.cursor()

c.execute('SELECT name FROM sqlite_master WHERE type="table"')
print('Tables:', [r[0] for r in c.fetchall()])

c.execute('SELECT COUNT(*) FROM subtopics')
print('Subtopics count:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM source_materials')
print('Source materials count:', c.fetchone()[0])

c.execute('SELECT COUNT(*) FROM questions')
print('Questions count:', c.fetchone()[0])

c.execute('SELECT * FROM subtopics LIMIT 2')
rows = c.fetchall()
print('Subtopics sample:', rows)

c.execute('SELECT * FROM source_materials LIMIT 2')
rows = c.fetchall()
print('Source sample:', rows)
