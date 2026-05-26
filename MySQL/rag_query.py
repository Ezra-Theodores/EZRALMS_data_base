import os
import google.generativeai as genai
import chromadb
from chromadb.utils import embedding_functions
import sys

# --- Configuration ---
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("Error: GOOGLE_API_KEY environment variable not set.")
    sys.exit(1)

genai.configure(api_key=api_key)
# Using gemini-flash-latest for reliability
model = genai.GenerativeModel('gemini-flash-latest')

DB_PATH = "./chroma_db"

# --- Initialize ChromaDB ---
client = chromadb.PersistentClient(path=DB_PATH)
google_ef = embedding_functions.GoogleGenerativeAiEmbeddingFunction(
    api_key=api_key,
    model_name="models/gemini-embedding-001"
)

collection = client.get_collection(
    name="ezra_quizzes",
    embedding_function=google_ef
)

def rag_query(query_text):
    # 1. Retrieve relevant questions
    print(f"Searching for context for: '{query_text}'...")
    results = collection.query(
        query_texts=[query_text],
        n_results=3
    )
    
    contexts = []
    if results['documents']:
        for doc, meta in zip(results['documents'][0], results['metadatas'][0]):
            source_info = f"[Source: {meta['title']} ({meta['subject']} Grade {meta['grade']})]"
            contexts.append(f"{source_info}\n{doc}")
    
    context_str = "\n\n---\n\n".join(contexts) if contexts else "Tidak ada konteks kuis yang ditemukan."
    
    # 2. Build Prompt
    prompt = f"""
Anda adalah AI Tutor untuk EzraLMS. Jawablah pertanyaan user berdasarkan konteks data kuis di bawah ini. 
Jika informasi tidak ada dalam konteks, jawablah berdasarkan pengetahuan umum Anda tetapi tetap hubungkan dengan materi yang relevan.

KONTEKS KUIS:
{context_str}

PERTANYAAN USER:
{query_text}

JAWABAN (Gunakan Bahasa Indonesia):
"""

    # 3. Generate Answer
    print("Generating answer...")
    response = model.generate_content(prompt)
    return response.text

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        user_query = input("Masukkan pertanyaan Anda: ")
    
    try:
        answer = rag_query(user_query)
        print("\n" + "="*30)
        print("JAWABAN AI TUTOR:")
        print("="*30)
        print(answer)
    except Exception as e:
        print(f"Error during query: {e}")
