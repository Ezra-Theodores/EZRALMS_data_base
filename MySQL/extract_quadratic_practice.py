"""
Extract all Quadratic Equation practice questions from Grade 9 Quiz Bank
Save as JSON embedded in Markdown format
"""

import json
import re

INPUT_MD = "JSON_Exports/Quiz_Grade9_NATIONAL_PLUS.md"
OUTPUT_MD = "MD_Exports/Grade9_Quadratic_Equations_Practice.md"

# Keywords for quadratic equation topics
QUADRATIC_KEYWORDS = [
    "kuadrat", "quadratic", 
    "diskriminan", "discriminant",
    "akar real", "real roots",
    "menyusun persamaan", "form equation",
    "titik puncak", "vertex",
    "grafik parabola", "parabola graph",
    "fungsi kuadrat", "quadratic function",
    "persamaan kuadrat", "quadratic equation"
]

def extract_quizzes_from_md(md_path):
    """Extract all quiz JSON data from the markdown file"""
    print("Reading markdown file...")
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all JSON blocks
    json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
    print(f"Found {len(json_blocks)} JSON blocks")
    
    quizzes = []
    for i, block in enumerate(json_blocks):
        try:
            quiz_data = json.loads(block)
            if isinstance(quiz_data, dict) and 'questions' in quiz_data and 'subject' in quiz_data:
                quizzes.append(quiz_data)
        except json.JSONDecodeError as e:
            if i < 3:
                print(f"Warning: Could not parse JSON block {i}: {str(e)[:100]}...")
    
    print(f"Successfully parsed {len(quizzes)} valid quizzes")
    return quizzes

def is_quadratic_question(question):
    """Check if a question is related to quadratic equations"""
    id_q = question.get('id_q', '').lower()
    en_q = question.get('en_q', '').lower()
    id_exp = question.get('id_exp', '').lower()
    en_exp = question.get('en_exp', '').lower()
    
    combined_text = f"{id_q} {en_q} {id_exp} {en_exp}"
    
    # Check for any quadratic keyword
    for keyword in QUADRATIC_KEYWORDS:
        if keyword.lower() in combined_text:
            return True
    
    return False

def extract_quadratic_questions(quizzes):
    """Extract all quadratic equation questions"""
    quadratic_questions = []
    
    for quiz in quizzes:
        quiz_title = quiz.get('title', 'Unknown')
        questions = quiz.get('questions', [])
        
        if not isinstance(questions, list):
            continue
        
        for question in questions:
            if not isinstance(question, dict):
                continue
            
            if is_quadratic_question(question):
                # Add source info
                question_with_source = dict(question)
                question_with_source['source_quiz'] = quiz_title
                question_with_source['grade'] = quiz.get('grade', 9)
                question_with_source['subject'] = quiz.get('subject', 'Math')
                question_with_source['difficulty'] = quiz.get('difficulty', 'N/A')
                
                quadratic_questions.append(question_with_source)
    
    return quadratic_questions

def categorize_questions(questions):
    """Categorize quadratic questions by topic"""
    categories = {
        "Diskriminan dan Sifat Akar": [],
        "Menyusun Persamaan Kuadrat Baru": [],
        "Fungsi Kuadrat - Titik Puncak": [],
        "Fungsi Kuadrat - Grafik": [],
        "Aplikasi Persamaan Kuadrat": []
    }
    
    for q in questions:
        id_q = q.get('id_q', '').lower()
        en_q = q.get('en_q', '').lower()
        
        # Categorize based on keywords
        if 'diskriminan' in id_q or 'discriminant' in en_q or 'akar real' in id_q or 'real roots' in en_q:
            categories["Diskriminan dan Sifat Akar"].append(q)
        elif 'menyusun' in id_q or 'form equation' in en_q or 'akar α' in id_q or 'roots α' in en_q:
            categories["Menyusun Persamaan Kuadrat Baru"].append(q)
        elif 'titik puncak' in id_q or 'vertex' in en_q or 'minimum' in id_q or 'minimum' in en_q:
            categories["Fungsi Kuadrat - Titik Puncak"].append(q)
        elif 'grafik' in id_q or 'graph' in en_q or 'parabola' in id_q or 'parabola' in en_q:
            categories["Fungsi Kuadrat - Grafik"].append(q)
        else:
            categories["Aplikasi Persamaan Kuadrat"].append(q)
    
    return categories

def generate_output(questions, categories):
    """Generate markdown output with embedded JSON"""
    
    # Create markdown content
    md_content = "# 📐 Grade 9 Quadratic Equations Practice\n\n"
    md_content += "**Kumpulan soal Persamaan Kuadrat untuk Kelas 9**\n\n"
    md_content += "---\n\n"
    
    md_content += f"## 📊 Summary\n\n"
    md_content += f"- **Total Questions:** {len(questions)}\n"
    md_content += f"- **Grade Level:** 9\n"
    md_content += f"- **Subject:** Mathematics\n\n"
    
    md_content += "### Topics Covered:\n"
    for category, qs in categories.items():
        md_content += f"- {category}: {len(qs)} questions\n"
    md_content += "\n---\n\n"
    
    md_content += "## 📝 Questions by Category\n\n"
    
    for category, qs in categories.items():
        if qs:
            md_content += f"### {category}\n\n"
            
            for i, q in enumerate(qs, 1):
                md_content += f"**Question {i}:**\n\n"
                md_content += f"**Indonesian:** {q.get('id_q', 'N/A')}\n\n"
                md_content += f"**English:** {q.get('en_q', 'N/A')}\n\n"
                
                if q.get('image'):
                    if q['image'].startswith('http'):
                        md_content += f"![Diagram]({q['image']})\n\n"
                
                md_content += "**Options:**\n"
                for j, opt in enumerate(q.get('options', [])):
                    md_content += f"- {chr(65+j)}. {opt}\n"
                md_content += "\n"
                
                ans = q.get('ans', 0)
                ans_label = chr(65+ans) if isinstance(ans, int) else ans
                md_content += f"**Answer:** {ans_label}\n\n"
                md_content += f"**Explanation (ID):** {q.get('id_exp', 'N/A')}\n\n"
                md_content += f"**Explanation (EN):** {q.get('en_exp', 'N/A')}\n\n"
                md_content += f"*Source: {q.get('source_quiz', 'Unknown')}*\n\n"
                md_content += "---\n\n"
    
    # Add JSON section
    md_content += "## 📄 Full JSON Data\n\n"
    md_content += "```json\n"
    
    json_output = {
        "title": "Grade 9 Quadratic Equations Practice",
        "description": "Collection of quadratic equation questions for Grade 9",
        "total_questions": len(questions),
        "categories": {cat: len(qs) for cat, qs in categories.items()},
        "questions": questions
    }
    
    md_content += json.dumps(json_output, indent=2, ensure_ascii=False)
    md_content += "\n```\n"
    
    return md_content

def main():
    print("Loading Quiz Bank...")
    quizzes = extract_quizzes_from_md(INPUT_MD)
    
    print("\nExtracting quadratic equation questions...")
    quadratic_questions = extract_quadratic_questions(quizzes)
    
    print(f"Found {len(quadratic_questions)} quadratic equation questions")
    
    if not quadratic_questions:
        print("No quadratic equation questions found. Trying broader search...")
        # Fallback: search for any question with x² or similar patterns
        for quiz in quizzes:
            quiz_title = quiz.get('title', 'Unknown')
            questions = quiz.get('questions', [])
            
            if not isinstance(questions, list):
                continue
            
            for question in questions:
                if not isinstance(question, dict):
                    continue
                
                id_q = question.get('id_q', '')
                en_q = question.get('en_q', '')
                
                # Look for x^2 or x² patterns
                if 'x²' in id_q or 'x^2' in id_q or 'x²' in en_q or 'x^2' in en_q:
                    question_with_source = dict(question)
                    question_with_source['source_quiz'] = quiz_title
                    question_with_source['grade'] = quiz.get('grade', 9)
                    question_with_source['subject'] = quiz.get('subject', 'Math')
                    question_with_source['difficulty'] = quiz.get('difficulty', 'N/A')
                    quadratic_questions.append(question_with_source)
        
        print(f"Found {len(quadratic_questions)} questions with x² pattern")
    
    # Categorize questions
    categories = categorize_questions(quadratic_questions)
    
    # Generate output
    md_content = generate_output(quadratic_questions, categories)
    
    # Save to file
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"\n✅ Saved to: {OUTPUT_MD}")
    
    # Print summary
    print(f"\n📊 Summary by Category:")
    for category, qs in categories.items():
        print(f"   {category}: {len(qs)} questions")

if __name__ == "__main__":
    main()
