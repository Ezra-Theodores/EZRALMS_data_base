import os
import json
import glob
import re
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
import time

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

MD_PATH = "MD_Exports/*.md"
DB_PATH = "./chroma_db"

# --- Initialize ChromaDB ---
client = chromadb.PersistentClient(path=DB_PATH)
if api_key:
    google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        api_key=api_key,
        model_name="models/gemini-embedding-001"
    )
else:
    google_ef = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="ezra_quizzes",
    embedding_function=google_ef
)

def extract_json_from_md(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    json_blocks = re.findall(r'```json\n(.*?)\n```', content, re.DOTALL)
    extracted_data = []
    for block in json_blocks:
        try:
            data = json.loads(block)
            extracted_data.append(data)
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON in {file_path}: {e}")
    return extracted_data

def process_quizzes():
    files = glob.glob(MD_PATH)
    if not files:
        print(f"No Markdown files found in {MD_PATH}")
        return

    documents = []
    metadatas = []
    ids = []
    
    seen_ids = set()

    for file in files:
        print(f"Processing {file}...")
        quizzes = extract_json_from_md(file)
        
        for quiz in quizzes:
            title = quiz.get("title", "Untitled")
            subject = quiz.get("subject", "General")
            grade = quiz.get("grade", "Unknown")
            questions = quiz.get("questions") or []
            
            for q in questions:
                text_content = f"Question: {q.get('id_q') or q.get('en_q')}\nExplanation: {q.get('id_exp') or q.get('en_exp')}"
                
                # Create a unique ID
                qid = f"{quiz.get('firestore_id', 'unknown')}_{q.get('id')}"
                
                if qid not in seen_ids:
                    documents.append(text_content)
                    metadatas.append({
                        "title": title,
                        "subject": subject,
                        "grade": grade,
                        "q_id": str(q.get("id")),
                        "source": file
                    })
                    ids.append(qid)
                    seen_ids.add(qid)

    if documents:
        print(f"Adding/Updating {len(documents)} questions in ChromaDB...")
        batch_size = 20
        for i in range(0, len(documents), batch_size):
            print(f"Uploading batch {i//batch_size + 1}...")
            try:
                # Use upsert to avoid DuplicateIDError
                collection.upsert(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
                time.sleep(5) 
            except Exception as e:
                print(f"Error in batch {i}: {e}")
                print("Waiting 60 seconds...")
                time.sleep(60)
                collection.upsert(
                    documents=documents[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size],
                    ids=ids[i:i+batch_size]
                )
        print("Done!")
    else:
        print("No questions extracted.")

if __name__ == "__main__":
    if not api_key:
        print("Error: Please set GOOGLE_API_KEY environment variable.")
    else:
        process_quizzes()
