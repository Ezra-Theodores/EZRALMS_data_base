from pathlib import Path
from data_house import DataHouse
import hashlib
import re

dh = DataHouse()
conn = dh.connect()
cursor = conn.cursor()

subtopics_path = dh.data_house_path / "Subtopics_By_Class"
print(f"Path: {subtopics_path}, exists: {subtopics_path.exists()}")

md_files = list(subtopics_path.glob("*.md"))
print(f"Files: {len(md_files)}")

class_name = ""
topic_name = ""

for md_file in md_files[:3]:
    print(f"\nProcessing: {md_file}")
    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        topic_name = ""
        if lines and lines[0].startswith('#'):
            topic_name = lines[0].replace('#', '').strip()

        print(f"Topic: {topic_name[:50]}, Lines: {len(lines)}")

        table_started = False
        order_index = 0
        inserted = 0

        for line in lines:
            if line.startswith('|'):
                if 'Judul Materi' in line or 'Title' in line:
                    table_started = True
                    print(f"  Table started at line with: {line[:50]}")
                    continue
                if table_started and '|' in line:
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 3:
                        try:
                            order = int(parts[1]) if parts[1].isdigit() else order_index
                            title = parts[2]
                            subtopic_type = parts[3] if len(parts) > 3 else 'Quiz'

                            subtopic_id = hashlib.md5(f"{md_file.name}{order}{title}".encode()).hexdigest()

                            cursor.execute('''
                                INSERT OR REPLACE INTO subtopics (subtopic_id, topic_name, class_name, order_index, title, subtopic_type, content, source_file)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                subtopic_id,
                                topic_name,
                                'G9',  # class_name
                                order,
                                title,
                                subtopic_type,
                                '',
                                md_file.name
                            ))
                            inserted += 1
                            order_index += 1

                        except Exception as e:
                            print(f"  Error: {e}")

        print(f"  Inserted: {inserted}")

    except Exception as e:
        print(f"File error: {e}")

conn.commit()

cursor.execute('SELECT COUNT(*) FROM subtopics')
print(f"\nTotal subtopics in DB: {cursor.fetchone()[0]}")

cursor.execute('SELECT * FROM subtopics LIMIT 3')
for row in cursor.fetchall():
    print(f"  Row: {row}")
