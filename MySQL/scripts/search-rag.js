/**
 * Semantic Search for RAG Database
 * Pencarian semantik menggunakan embeddings
 */

const fs = require('fs');
const path = require('path');

function cosineSimilarity(vecA, vecB) {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }

  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

function search(queryVector, vectors, metadata, topK = 5) {
  const similarities = [];

  for (const [qid, vec] of Object.entries(vectors)) {
    const sim = cosineSimilarity(queryVector, vec);
    similarities.push({ qid, similarity: sim });
  }

  // Sort by similarity (descending)
  similarities.sort((a, b) => b.similarity - a.similarity);

  // Get top K results
  const topResults = similarities.slice(0, topK);

  // Enrich with metadata
  return topResults.map(result => {
    const meta = metadata.find(m => m.id === result.qid) || {};
    return {
      ...result,
      ...meta
    };
  });
}

function filterSearch(metadata, filters) {
  let results = metadata;

  if (filters.grade) {
    results = results.filter(q => q.grade === filters.grade);
  }

  if (filters.topic) {
    results = results.filter(q => q.topic === filters.topic);
  }

  if (filters.difficulty) {
    results = results.filter(q => q.difficulty === filters.difficulty);
  }

  if (filters.hasImage !== undefined) {
    results = results.filter(q => q.hasImage === filters.hasImage);
  }

  if (filters.skillTag) {
    results = results.filter(q => q.skillTags.includes(filters.skillTag));
  }

  return results;
}

function loadRAGData() {
  const ragDbDir = path.join(__dirname, '..', 'rag-db');

  // Load metadata
  const metadataPath = path.join(ragDbDir, 'metadata', 'index.json');
  const metadata = JSON.parse(fs.readFileSync(metadataPath, 'utf8'));

  // Load vectors if available
  const vectorsPath = path.join(ragDbDir, 'embeddings', 'vectors.json');
  let vectors = {};
  if (fs.existsSync(vectorsPath)) {
    vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));
  }

  return {
    metadata: metadata.questions,
    vectors,
    stats: {
      totalQuestions: metadata.totalQuestions,
      totalQuizzes: metadata.totalQuizzes,
      topics: metadata.topics,
      grades: metadata.grades,
      difficulties: metadata.difficulties,
      hasEmbeddings: Object.keys(vectors).length > 0
    }
  };
}

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];

  console.log('🔍 RAG Database Search\n');

  try {
    const { metadata, vectors, stats } = loadRAGData();

    console.log('📊 Database Stats:');
    console.log(`   Total Questions: ${stats.totalQuestions}`);
    console.log(`   Total Quizzes: ${stats.totalQuizzes}`);
    console.log(`   Embeddings: ${stats.hasEmbeddings ? '✅ Available' : '❌ Not generated'}`);

    if (!command || command === 'stats') {
      console.log('\n📁 By Topic:');
      Object.entries(stats.topics)
        .sort((a, b) => b[1] - a[1])
        .forEach(([topic, count]) => {
          console.log(`   ${topic}: ${count}`);
        });

      console.log('\n📁 By Grade:');
      Object.entries(stats.grades)
        .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
        .forEach(([grade, count]) => {
          console.log(`   Grade ${grade}: ${count}`);
        });

    } else if (command === 'filter') {
      const filters = {};

      // Parse filter arguments
      for (let i = 1; i < args.length; i++) {
        const [key, value] = args[i].split('=');
        if (key && value) {
          if (key === 'hasImage') {
            filters[key] = value === 'true';
          } else {
            filters[key] = value;
          }
        }
      }

      console.log('\n🔍 Filters:', filters);

      const results = filterSearch(metadata, filters);

      console.log(`\n✅ Found ${results.length} matching questions`);

      if (results.length > 0) {
        console.log('\n📋 Sample results (first 5):');
        results.slice(0, 5).forEach((q, i) => {
          console.log(`\n${i + 1}. ${q.quizTitle}`);
          console.log(`   Grade: ${q.grade} | Topic: ${q.topic} | Difficulty: ${q.difficulty}`);
        });
      }

    } else if (command === 'search') {
      console.log('\n⚠️  Semantic search requires embeddings to be generated first.');
      console.log('   Run: python scripts/generate-embeddings.py');
    }

    console.log('\n💡 Available commands:');
    console.log('   node scripts/search-rag.js stats          - Show database statistics');
    console.log('   node scripts/search-rag.js filter grade=6   - Filter by criteria');
    console.log('   node scripts/search-rag.js filter topic=Geometri difficulty=medium');

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error('   Make sure you have built the RAG database first:');
    console.error('   1. node scripts/extract-firebase.js');
    console.error('   2. node scripts/build-rag.js');
    process.exit(1);
  }
}

module.exports = {
  cosineSimilarity,
  search,
  filterSearch,
  loadRAGData
};
