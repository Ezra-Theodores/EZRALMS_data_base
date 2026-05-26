/**
 * Build RAG Database from extracted quizzes
 * Membangun database soal individual dengan metadata untuk RAG
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Topic classification keywords
const topicKeywords = {
  'Bilangan': ['bilangan', 'number', 'bulat', 'cacah', 'pecahan', 'desimal', 'persen'],
  'Bilangan Lanjut': ['fpb', 'kpk', 'prima', 'faktor', 'kelipatan'],
  'Aritmatika': ['tambah', 'kurang', 'kali', 'bagi', 'operasi', 'hitung', 'arithmetic', 'add', 'subtract', 'multiply', 'divide'],
  'Geometri': ['geometri', 'geometri', 'bangun', 'segitiga', 'lingkaran', 'persegi', 'kubus', 'balok', 'geometry', 'triangle', 'circle', 'square', 'cube'],
  'Pengukuran': ['ukur', 'panjang', 'berat', 'waktu', 'volume', 'luas', 'keliling', 'measurement', 'length', 'weight', 'time', 'area', 'perimeter'],
  'Statistika': ['statistik', 'data', 'grafik', 'tabel', 'mean', 'median', 'modus', 'statistics', 'chart', 'graph', 'average'],
  'Rasio': ['rasio', 'perbandingan', 'skala', 'ratio', 'proportion', 'scale'],
  'Peluang': ['peluang', 'probabilitas', 'probability', 'chance'],
  'Aljabar': ['aljabar', 'algebra', 'variabel', 'variabel', 'persamaan', 'equation', 'x', 'y'],
  'Logika': ['logika', 'logic', 'pola', 'pattern', 'urutan', 'sequence']
};

// Skill tag extraction
const skillKeywords = {
  'calculation': ['hitung', 'calculate', 'tambah', 'kurang', 'kali', 'bagi', 'jumlah', 'hasil'],
  'visual-spatial': ['gambar', 'image', 'diagram', 'visual', 'bentuk', 'shape', 'geometry', 'geometri'],
  'multi-step': ['langkah', 'step', 'kemudian', 'lalu', 'setelah', 'terlebih dahulu'],
  'comparison': ['banding', 'lebih', 'kurang', 'paling', 'terbesar', 'terkecil', 'compare'],
  'formula-application': ['rumus', 'formula', 'gunakan', 'apply'],
  'ordering': ['urut', 'order', 'urutan', 'sort', 'ascending', 'descending'],
  'pattern-recognition': ['pola', 'pattern', 'aturan', 'rule', 'lanjutkan'],
  'reading-graph': ['grafik', 'chart', 'graph', 'baca', 'interpret'],
  'estimation': ['perkiraan', 'estimate', 'approximately', 'sekitar', 'mendekati'],
  'problem-solving': ['masalah', 'problem', 'solve', 'selesaikan', 'cara']
};

function generateUUID() {
  return `q-${crypto.randomUUID()}`;
}

function determineTopic(question) {
  const text = `${question.id_q || ''} ${question.en_q || ''}`.toLowerCase();

  const topicScores = {};
  for (const [topic, keywords] of Object.entries(topicKeywords)) {
    let score = 0;
    for (const keyword of keywords) {
      if (text.includes(keyword.toLowerCase())) {
        score += 1;
      }
    }
    if (score > 0) {
      topicScores[topic] = score;
    }
  }

  // Get topic with highest score
  const sortedTopics = Object.entries(topicScores).sort((a, b) => b[1] - a[1]);
  const bestTopic = sortedTopics[0];

  if (bestTopic && bestTopic[1] >= 1) {
    return {
      topic: bestTopic[0],
      confidence: Math.min(bestTopic[1] / 3, 1.0)  // Normalize confidence
    };
  }

  return { topic: 'Unclassified', confidence: 0 };
}

function extractSkillTags(question, quiz) {
  const tags = [];
  const text = `${question.id_q || ''} ${question.en_q || ''} ${question.id_exp || ''} ${question.en_exp || ''}`.toLowerCase();

  for (const [tag, keywords] of Object.entries(skillKeywords)) {
    for (const keyword of keywords) {
      if (text.includes(keyword.toLowerCase())) {
        tags.push(tag);
        break;
      }
    }
  }

  // Add grade-based tags
  const grade = parseInt(quiz.grade || 1);
  if (grade <= 3) {
    tags.push('grade-lower');
  } else if (grade <= 6) {
    tags.push('grade-middle');
  } else {
    tags.push('grade-upper');
  }

  // Remove duplicates
  return [...new Set(tags)];
}

function buildRAGQuestion(quiz, question, questionIndex) {
  const topicInfo = determineTopic(question);
  const skillTags = extractSkillTags(question, quiz);

  return {
    id: generateUUID(),
    quizId: quiz.id,
    quizTitle: quiz.title,
    questionNumber: questionIndex + 1,
    grade: quiz.grade,
    subject: quiz.subject,
    creator: quiz.creatorName,
    quizType: quiz.type,
    id_q: question.id_q || question.id_q || '',
    en_q: question.en_q || '',
    options: question.options || [],
    correctAnswerIndex: typeof question.ans === 'number' ? question.ans : 0,
    hasImage: !!question.image,
    imageType: question.image ? 'svg' : null,
    id_exp: question.id_exp || '',
    en_exp: question.en_exp || '',
    language: 'bilingual',
    difficulty: (quiz.difficulty || 'medium').toLowerCase(),
    topic: topicInfo.topic,
    topicConfidence: topicInfo.confidence,
    skillTags: skillTags,
    optionCount: (question.options || []).length,
    textLength: ((question.id_q || '') + (question.en_q || '')).length
  };
}

function getTopicFolderName(topic) {
  const mapping = {
    'Bilangan': '01-Bilangan',
    'Bilangan Lanjut': '01-Bilangan-Lanjut',
    'Aritmatika': '02-Aritmatika',
    'Geometri': '03-Geometri',
    'Pengukuran': '04-Pengukuran',
    'Statistika': '05-Statistika',
    'Rasio': '06-Rasio',
    'Peluang': '07-Peluang',
    'Aljabar': '08-Aljabar',
    'Logika': '09-Logika'
  };
  return mapping[topic] || '99-Unclassified';
}

async function buildRAGDatabase() {
  console.log('🏗️  Building RAG Database...\n');

  const dataDir = path.join(__dirname, '..', 'data');
  const ragDbDir = path.join(__dirname, '..', 'rag-db');

  // Check if data exists
  const allQuizzesPath = path.join(dataDir, 'all-quizzes.json');
  if (!fs.existsSync(allQuizzesPath)) {
    console.error('❌ Data tidak ditemukan!');
    console.error('   Jalankan: node scripts/extract-firebase.js');
    process.exit(1);
  }

  // Load quizzes
  console.log('📂 Loading quizzes...');
  const allQuizzes = JSON.parse(fs.readFileSync(allQuizzesPath, 'utf8'));
  console.log(`   ✅ Loaded ${allQuizzes.length} quizzes`);

  // Statistics
  let totalQuestions = 0;
  const topicCounts = {};
  const gradeCounts = {};
  const difficultyCounts = {};
  const metadata = {
    totalQuestions: 0,
    totalQuizzes: allQuizzes.length,
    topics: {},
    grades: {},
    difficulties: {},
    questions: []
  };

  // Process each quiz
  console.log('\n🔄 Processing questions...');

  for (const quiz of allQuizzes) {
    const questions = quiz.questions || [];

    for (let i = 0; i < questions.length; i++) {
      const q = questions[i];

      try {
        // Build RAG question object
        const ragQuestion = buildRAGQuestion(quiz, q, i);

        // Update statistics
        totalQuestions++;
        topicCounts[ragQuestion.topic] = (topicCounts[ragQuestion.topic] || 0) + 1;
        gradeCounts[ragQuestion.grade] = (gradeCounts[ragQuestion.grade] || 0) + 1;
        difficultyCounts[ragQuestion.difficulty] = (difficultyCounts[ragQuestion.difficulty] || 0) + 1;

        // Save to file
        const topicFolder = getTopicFolderName(ragQuestion.topic);
        const outputDir = path.join(ragDbDir, 'questions', topicFolder);

        if (!fs.existsSync(outputDir)) {
          fs.mkdirSync(outputDir, { recursive: true });
        }

        const outputPath = path.join(outputDir, `${ragQuestion.id}.json`);
        fs.writeFileSync(outputPath, JSON.stringify(ragQuestion, null, 2));

        // Add to metadata
        metadata.questions.push({
          id: ragQuestion.id,
          quizId: ragQuestion.quizId,
          quizTitle: ragQuestion.quizTitle,
          grade: ragQuestion.grade,
          topic: ragQuestion.topic,
          topicConfidence: ragQuestion.topicConfidence,
          difficulty: ragQuestion.difficulty,
          language: ragQuestion.language,
          hasImage: ragQuestion.hasImage,
          skillTags: ragQuestion.skillTags
        });

      } catch (error) {
        console.error(`   ❌ Error processing question ${i} in quiz ${quiz.id}:`, error.message);
      }
    }
  }

  // Update metadata statistics
  metadata.totalQuestions = totalQuestions;
  metadata.topics = topicCounts;
  metadata.grades = gradeCounts;
  metadata.difficulties = difficultyCounts;

  // Save metadata
  console.log('\n💾 Saving metadata...');

  const metadataDir = path.join(ragDbDir, 'metadata');
  if (!fs.existsSync(metadataDir)) {
    fs.mkdirSync(metadataDir, { recursive: true });
  }

  fs.writeFileSync(
    path.join(metadataDir, 'index.json'),
    JSON.stringify(metadata, null, 2)
  );

  // Create stats summary
  const stats = {
    generatedAt: new Date().toISOString(),
    totalQuestions,
    totalQuizzes: allQuizzes.length,
    byTopic: topicCounts,
    byGrade: gradeCounts,
    byDifficulty: difficultyCounts
  };

  fs.writeFileSync(
    path.join(metadataDir, 'stats.json'),
    JSON.stringify(stats, null, 2)
  );

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('✅ RAG Database berhasil dibangun!');
  console.log('='.repeat(60));
  console.log(`\n📊 Statistics:`);
  console.log(`   Total Questions: ${totalQuestions}`);
  console.log(`   Total Quizzes: ${allQuizzes.length}`);
  console.log(`\n📁 By Topic:`);
  Object.entries(topicCounts)
    .sort((a, b) => b[1] - a[1])
    .forEach(([topic, count]) => {
      console.log(`   ${topic}: ${count}`);
    });
  console.log(`\n📁 By Grade:`);
  Object.entries(gradeCounts)
    .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
    .forEach(([grade, count]) => {
      console.log(`   Grade ${grade}: ${count}`);
    });
  console.log('');
}

// Run if called directly
if (require.main === module) {
  buildRAGDatabase().catch(err => {
    console.error('❌ Error building RAG database:', err);
    process.exit(1);
  });
}

module.exports = { buildRAGDatabase };
