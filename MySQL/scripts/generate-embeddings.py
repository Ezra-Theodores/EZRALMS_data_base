"""
Generate Embeddings for RAG Database
Menggunakan sentence-transformers untuk generate 768-dim vectors
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("⚠️  sentence-transformers tidak terinstall.")
    print("   Install dengan: pip install sentence-transformers")
    print("   atau gunakan mode fallback dengan numpy random vectors")

# Configuration
MODEL_NAME = 'all-mpnet-base-v2'  # 768 dimensions, good quality
VECTOR_DIMENSIONS = 768
BATCH_SIZE = 32


def load_questions(rag_db_path: str) -> Dict[str, dict]:
    """Load all question files from the RAG database"""
    questions_dir = Path(rag_db_path) / 'questions'
    questions = {}

    print(f"🔍 Loading questions from {questions_dir}...")

    # Walk through all topic folders
    for topic_dir in questions_dir.iterdir():
        if not topic_dir.is_dir():
            continue

        # Load each question file
        for question_file in topic_dir.glob('*.json'):
            try:
                with open(question_file, 'r', encoding='utf-8') as f:
                    question = json.load(f)
                    questions[question['id']] = question
            except Exception as e:
                print(f"   ⚠️  Error loading {question_file}: {e}")

    print(f"✅ Loaded {len(questions)} questions")
    return questions


def generate_text_for_embedding(question: dict) -> str:
    """Generate text representation for embedding"""
    parts = []

    # Add Indonesian question
    if question.get('id_q'):
        parts.append(question['id_q'])

    # Add English question
    if question.get('en_q'):
        parts.append(question['en_q'])

    # Add topic
    if question.get('topic'):
        parts.append(f"Topic: {question['topic']}")

    # Add grade
    if question.get('grade'):
        parts.append(f"Grade: {question['grade']}")

    return ' '.join(parts)


def generate_embeddings_batch(
    questions: Dict[str, dict],
    model: Optional[SentenceTransformer] = None
) -> Dict[str, List[float]]:
    """Generate embeddings for all questions using batch processing"""

    vectors = {}
    question_list = list(questions.items())

    print(f"\n🔄 Generating embeddings for {len(question_list)} questions...")

    if model is not None:
        # Use sentence-transformers
        texts = [generate_text_for_embedding(q) for _, q in question_list]

        # Process in batches
        for i in range(0, len(texts), BATCH_SIZE):
            batch_texts = texts[i:i + BATCH_SIZE]
            batch_embeddings = model.encode(batch_texts, show_progress_bar=False)

            for j, embedding in enumerate(batch_embeddings):
                idx = i + j
                if idx < len(question_list):
                    qid, _ = question_list[idx]
                    vectors[qid] = embedding.tolist()

            if (i // BATCH_SIZE + 1) % 10 === 0:
                print(f"   Processed {min(i + BATCH_SIZE, len(texts))}/{len(texts)} questions")
    else:
        # Fallback: Use random vectors for testing
        print("⚠️  Using fallback random vectors (for testing only)")
        for qid, question in question_list:
            # Generate deterministic random vector based on question ID
            seed = int(qid.replace(/[^0-9a-f]/g, '').slice(0, 16), 16) % (2**31)
            np.random.seed(seed)
            vector = np.random.randn(VECTOR_DIMENSIONS).tolist()
            vectors[qid] = vector

    print(f"✅ Generated {len(vectors)} embeddings")
    return vectors


def save_embeddings(vectors: Dict[str, List[float]], output_path: str):
    """Save embeddings to JSON file"""
    print(f"\n💾 Saving embeddings to {output_path}...")

    # Create directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save as JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(vectors, f, indent=2)

    # Calculate file size
    file_size = os.path.getsize(output_path)
    print(f"✅ Saved {len(vectors)} vectors ({file_size / 1024 / 1024:.2f} MB)")


def main():
    """Main entry point"""
    # Paths
    base_dir = Path(__file__).parent.parent
    rag_db_dir = base_dir / 'rag-db'
    output_path = rag_db_dir / 'embeddings' / 'vectors.json'

    print("=" * 60)
    print("🔧 RAG Embeddings Generator")
    print("=" * 60)

    # Check if we have sentence-transformers
    model = None
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        print(f"\n📦 Loading model: {MODEL_NAME}...")
        try:
            model = SentenceTransformer(MODEL_NAME)
            print(f"✅ Model loaded (output dim: {model.get_sentence_embedding_dimension()})")
        except Exception as e:
            print(f"⚠️  Error loading model: {e}")
            print("   Will use fallback random vectors")
    else:
        print("\n⚠️  sentence-transformers not available")
        print("   Install with: pip install sentence-transformers")
        print("   Will use fallback random vectors for testing")

    # Load questions
    questions = load_questions(str(rag_db_dir))

    if not questions:
        print("\n❌ No questions found. Please build the RAG database first:")
        print("   node scripts/build-rag.js")
        return 1

    # Generate embeddings
    vectors = generate_embeddings_batch(questions, model)

    # Save embeddings
    save_embeddings(vectors, str(output_path))

    print("\n" + "=" * 60)
    print("✅ Embeddings generation complete!")
    print("=" * 60)
    print(f"\n📊 Statistics:")
    print(f"   Total vectors: {len(vectors)}")
    print(f"   Dimensions: {VECTOR_DIMENSIONS}")
    print(f"   Output file: {output_path}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
