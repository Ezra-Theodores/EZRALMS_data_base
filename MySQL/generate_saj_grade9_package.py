"""
Generate SAJ Grade 9 Practice Package based on Kisi-Kisi
Matches questions from Quiz Bank Grade 9 to the 30 topics in the kisi-kisi document.
"""

import json
import re
import os

INPUT_MD = "JSON_Exports/Quiz_Grade9_NATIONAL_PLUS.md"
OUTPUT_JSON = "JSON_Exports/SAJ_Grade9_Practice_Package.json"
OUTPUT_MD = "MD_Exports/SAJ_Grade9_Practice_Package.md"

# Kisi-kisi topics mapping to question characteristics
KISI_KISI = [
    {"no": 1, "topic": "Bilangan : Operasi Campuran Pecahan", "keywords": ["pecahan", "fraction", "div", "÷"], "image_required": False},
    {"no": 2, "topic": "Himpunan : Aplikasi Himpunan (Diagram Venn)", "keywords": ["himpunan", "set", "inklusi", "eksklusi", "venn"], "image_required": False},
    {"no": 3, "topic": "Aljabar : Operasi Bentuk Aljabar", "keywords": ["aljabar", "kuadrat", "pangkat", "squared", "algebra"], "image_required": False},
    {"no": 4, "topic": "Persamaan Linear : Aplikasi Persamaan Linear", "keywords": ["usia", "umur", "age", "linear", "persamaan"], "image_required": False},
    {"no": 5, "topic": "Kecepatan, Jarak, Waktu : Kecepatan Rata-rata", "keywords": ["kecepatan", "speed", "jarak", "distance", "waktu", "time"], "image_required": False},
    {"no": 6, "topic": "Perbandingan : Perbandingan Senilai", "keywords": ["perbandingan", "ratio", "rasio", "gaji", "salary"], "image_required": False},
    {"no": 7, "topic": "Geometri (Segitiga) : Konsep Luas Segitiga", "keywords": ["segitiga", "triangle", "luas", "area", "tinggi", "height"], "image_required": True},
    {"no": 8, "topic": "Himpunan : Operasi Himpunan", "keywords": ["himpunan", "set", "irisan", "gabungan", "komplemen", "intersection", "union"], "image_required": False},
    {"no": 9, "topic": "Barisan dan Deret : Deret Aritmatika", "keywords": ["deret", "aritmatika", "arithmetic", "series", "suku"], "image_required": False},
    {"no": 10, "topic": "Persamaan Garis Lurus : Kedudukan Dua Garis", "keywords": ["garis", "tegak lurus", "perpendicular", "gradien", "persamaan"], "image_required": False},
    {"no": 11, "topic": "Aritmatika Sosial / PLSV : Pola Bilangan (Suhu)", "keywords": ["suhu", "temperature", "pola", "kedalaman", "depth"], "image_required": False},
    {"no": 12, "topic": "Persamaan Garis Lurus : Persamaan Garis Sejajar", "keywords": ["sejajar", "parallel", "garis", "persamaan"], "image_required": False},
    {"no": 13, "topic": "Bangun Ruang Sisi Datar : Balok", "keywords": ["balok", "cuboid", "diagonal", "ruang", "space"], "image_required": False},
    {"no": 14, "topic": "Lingkaran : Sudut Pusat dan Sudut Keliling", "keywords": ["lingkaran", "circle", "sudut", "angle", "pusat", "keliling"], "image_required": True},
    {"no": 15, "topic": "Bangun Ruang Sisi Datar : Prisma", "keywords": ["prisma", "prism", "luas", "permukaan", "surface"], "image_required": True},
    {"no": 16, "topic": "Statistika : Rata-rata Gabungan (Mean)", "keywords": ["rata-rata", "mean", "average", "statistika", "gabungan"], "image_required": False},
    {"no": 17, "topic": "Eksponen : Sifat-sifat Eksponen", "keywords": ["eksponen", "pangkat", "exponent", "power", "sederhanakan"], "image_required": False},
    {"no": 18, "topic": "Eksponen dan Bentuk Akar : Operasi Aljabar Eksponen", "keywords": ["akar", "root", "pangkat", "eksponen", "aljabar"], "image_required": False},
    {"no": 19, "topic": "Persamaan Kuadrat : Diskriminan dan Sifat Akar", "keywords": ["kuadrat", "quadratic", "diskriminan", "akar", "real roots"], "image_required": False},
    {"no": 20, "topic": "Persamaan Kuadrat : Menyusun PK Baru", "keywords": ["kuadrat", "quadratic", "akar", "roots", "persamaan", "menyusun"], "image_required": False},
    {"no": 21, "topic": "Fungsi Kuadrat : Titik Puncak dan Koefisien", "keywords": ["fungsi", "kuadrat", "titik puncak", "minimum", "vertex", "koefisien"], "image_required": False},
    {"no": 22, "topic": "Fungsi Kuadrat : Grafik Fungsi Kuadrat", "keywords": ["fungsi", "kuadrat", "grafik", "parabola", "quadratic", "graph"], "image_required": True},
    {"no": 23, "topic": "Kesebangunan : Aplikasi Skala dan Luas", "keywords": ["sebangun", "skala", "scale", "faktor", "luas", "area"], "image_required": False},
    {"no": 24, "topic": "Transformasi Geometri : Refleksi (Pencerminan)", "keywords": ["refleksi", "pencerminan", "reflection", "sumbu", "axis"], "image_required": False},
    {"no": 25, "topic": "Kekongruenan : Syarat Dua Segitiga Kongruen", "keywords": ["kongruen", "congruent", "segitiga", "triangle"], "image_required": True},
    {"no": 26, "topic": "Kesebangunan : Trapesium", "keywords": ["trapesium", "trapezoid", "sebangun", "similar"], "image_required": True},
    {"no": 27, "topic": "Bangun Ruang Sisi Lengkung : Bola dan Kerucut", "keywords": ["bola", "sphere", "kerucut", "cone", "bandul", "pendulum"], "image_required": True},
    {"no": 28, "topic": "Bangun Ruang Sisi Datar : Limas Segiempat", "keywords": ["limas", "pyramid", "segiempat", "square", "permukaan"], "image_required": False},
    {"no": 29, "topic": "Peluang : Frekuensi Harapan", "keywords": ["peluang", "probability", "frekuensi", "harapan", "dadu", "dice"], "image_required": False},
    {"no": 30, "topic": "Peluang : Peluang Kejadian Majemuk", "keywords": ["peluang", "probability", "komplemen", "complement", "kejadian"], "image_required": False},
]

def extract_quizzes_from_md(md_path):
    """Extract all quiz JSON data from the markdown file"""
    print("Reading markdown file...")
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all JSON blocks - use a more robust pattern
    json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
    print(f"Found {len(json_blocks)} JSON blocks")
    
    quizzes = []
    for i, block in enumerate(json_blocks):
        try:
            quiz_data = json.loads(block)
            if isinstance(quiz_data, dict) and 'questions' in quiz_data and 'subject' in quiz_data:
                quizzes.append(quiz_data)
        except json.JSONDecodeError as e:
            # Skip truncated JSON blocks (common in large files)
            if i < 5:  # Only show first few errors
                print(f"Warning: Could not parse JSON block {i}: {str(e)[:100]}...")
    
    print(f"Successfully parsed {len(quizzes)} valid quizzes")
    return quizzes

def find_matching_question(question, kisi_topic):
    """Check if a question matches a kisi-kisi topic based on keywords"""
    id_q = question.get('id_q', '').lower()
    en_q = question.get('en_q', '').lower()
    id_exp = question.get('id_exp', '').lower()
    en_exp = question.get('en_exp', '').lower()
    
    combined_text = f"{id_q} {en_q} {id_exp} {en_exp}"
    
    # Check if any keyword matches
    for keyword in kisi_topic['keywords']:
        if keyword.lower() in combined_text:
            return True
    
    return False

def select_questions_for_kisi(quizzes, kisi_topic, used_question_ids):
    """Select the best matching question for a kisi-kisi topic"""
    candidates = []
    
    for quiz in quizzes:
        questions = quiz.get('questions', [])
        if not isinstance(questions, list):
            continue
            
        for question in questions:
            if not isinstance(question, dict):
                continue
                
            q_id = f"{quiz['title']}_{question.get('id', '')}"
            
            # Skip if already used
            if q_id in used_question_ids:
                continue
            
            # Check if question matches the topic
            if find_matching_question(question, kisi_topic):
                # Calculate match score
                score = 0
                id_q = question.get('id_q', '').lower()
                en_q = question.get('en_q', '').lower()
                
                for keyword in kisi_topic['keywords']:
                    if keyword.lower() in id_q or keyword.lower() in en_q:
                        score += 1
                
                # Prefer questions with images if required
                if kisi_topic['image_required'] and question.get('image'):
                    score += 2
                
                candidates.append((score, question, quiz['title']))
    
    if candidates:
        # Sort by score (descending) and pick the best
        candidates.sort(key=lambda x: x[0], reverse=True)
        best_match = candidates[0]
        return best_match[1], best_match[2]  # question, quiz_title
    
    return None, None

def generate_practice_package():
    """Main function to generate the practice package"""
    print("Loading Quiz Bank...")
    quizzes = extract_quizzes_from_md(INPUT_MD)
    print(f"Loaded {len(quizzes)} quizzes")
    
    # Count total questions
    total_questions = sum(len(q.get('questions', [])) for q in quizzes)
    print(f"Total questions available: {total_questions}")
    
    # Select questions for each kisi-kisi topic
    selected_questions = []
    used_question_ids = set()
    
    print("\nMatching questions to kisi-kisi topics...")
    for kisi in KISI_KISI:
        question, quiz_title = select_questions_for_kisi(quizzes, kisi, used_question_ids)
        
        if question:
            q_id = f"{quiz_title}_{question['id']}"
            used_question_ids.add(q_id)
            
            # Format the question
            formatted_question = {
                "id": kisi['no'],
                "topic": kisi['topic'],
                "id_q": question.get('id_q', ''),
                "en_q": question.get('en_q', ''),
                "image": question.get('image', ''),
                "options": question.get('options', []),
                "ans": question.get('ans', 0),
                "id_exp": question.get('id_exp', ''),
                "en_exp": question.get('en_exp', ''),
                "source": quiz_title
            }
            selected_questions.append(formatted_question)
            print(f"✓ Topic {kisi['no']}: Matched from {quiz_title}")
        else:
            print(f"✗ Topic {kisi['no']}: No matching question found")
            # Create placeholder
            selected_questions.append({
                "id": kisi['no'],
                "topic": kisi['topic'],
                "id_q": f"[PERLU DIBUAT] Soal untuk topik: {kisi['topic']}",
                "en_q": f"[TO BE CREATED] Question for topic: {kisi['topic']}",
                "image": "",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "ans": 0,
                "id_exp": "Penjelasan akan ditambahkan",
                "en_exp": "Explanation to be added",
                "source": "PLACEHOLDER"
            })
    
    # Save JSON output
    output_data = {
        "title": "SAJ Grade 9 Practice Package",
        "description": "Practice questions based on Kisi-Kisi SAJ Kelas 9",
        "total_questions": len(selected_questions),
        "questions": selected_questions
    }
    
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ JSON saved to: {OUTPUT_JSON}")
    
    # Generate Markdown report
    md_content = "# 📚 SAJ Grade 9 Practice Package\n\n"
    md_content += "**Based on Kisi-Kisi Bank Soal SAJ Kelas 9**\n\n"
    md_content += f"**Total Questions:** {len(selected_questions)}\n\n"
    md_content += "---\n\n"
    
    # Group by topic category
    categories = {}
    for q in selected_questions:
        topic_parts = q['topic'].split(' : ')
        category = topic_parts[0] if len(topic_parts) > 0 else "Other"
        
        if category not in categories:
            categories[category] = []
        categories[category].append(q)
    
    for category in sorted(categories.keys()):
        md_content += f"## 📖 {category}\n\n"
        
        for q in categories[category]:
            subtopic = q['topic'].split(' : ')[1] if len(q['topic'].split(' : ')) > 1 else q['topic']
            md_content += f"### Question {q['id']}: {subtopic}\n\n"
            md_content += f"**Source:** {q['source']}\n\n"
            md_content += f"**Indonesian:** {q['id_q']}\n\n"
            md_content += f"**English:** {q['en_q']}\n\n"
            
            if q['image']:
                md_content += f"![Image]({q['image']})\n\n"
            
            md_content += "**Options:**\n"
            for i, opt in enumerate(q['options']):
                md_content += f"- {chr(65+i)}. {opt}\n"
            md_content += "\n"
            
            md_content += f"**Answer:** {chr(65+q['ans']) if isinstance(q['ans'], int) else q['ans']}\n\n"
            md_content += f"**Explanation (ID):** {q['id_exp']}\n\n"
            md_content += f"**Explanation (EN):** {q['en_exp']}\n\n"
            md_content += "---\n\n"
    
    # Save Markdown output
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Markdown saved to: {OUTPUT_MD}")
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   Total topics: {len(KISI_KISI)}")
    print(f"   Matched questions: {len([q for q in selected_questions if q['source'] != 'PLACEHOLDER'])}")
    print(f"   Placeholders: {len([q for q in selected_questions if q['source'] == 'PLACEHOLDER'])}")

if __name__ == "__main__":
    generate_practice_package()
