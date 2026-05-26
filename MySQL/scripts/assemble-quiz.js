/**
 * Assemble Quiz from RAG Database
 * Merakit quiz baru dari database soal berdasarkan kriteria
 */

const fs = require('fs');
const path = require('path');

/**
 * Assemble quiz from RAG database
 * @param {Object} criteria - Selection criteria
 * @param {number} count - Number of questions
 * @returns {Object} Assembled quiz
 */
function assembleQuiz(criteria, count = 20) {
  const { loadRAGData } = require('./search-rag');
  const { metadata } = loadRAGData();

  // Filter questions
  let candidates = metadata;

  if (criteria.grade) {
    candidates = candidates.filter(q => q.grade === criteria.grade);
  }

  if (criteria.topic) {
    candidates = candidates.filter(q => q.topic === criteria.topic);
  }

  if (criteria.difficulty) {
    candidates = candidates.filter(q => q.difficulty === criteria.difficulty);
  }

  if (criteria.hasImage !== undefined) {
    candidates = candidates.filter(q => q.hasImage === criteria.hasImage);
  }

  if (criteria.skillTag) {
    candidates = candidates.filter(q => q.skillTags.includes(criteria.skillTag));
  }

  if (criteria.excludeIds) {
    candidates = candidates.filter(q => !criteria.excludeIds.includes(q.id));
  }

  if (candidates.length === 0) {
    throw new Error('No questions match the given criteria');
  }

  // Shuffle and select
  const shuffled = candidates.sort(() => Math.random() - 0.5);
  const selected = shuffled.slice(0, Math.min(count, shuffled.length));

  // Build quiz object
  const gradeStr = criteria.grade ? `G${criteria.grade}` : 'Mixed';
  const topicStr = criteria.topic || 'Mixed';
  const diffStr = criteria.difficulty ? criteria.difficulty.charAt(0).toUpperCase() + criteria.difficulty.slice(1) : 'Mixed';

  const quiz = {
    name: `${gradeStr} ${topicStr} ${diffStr}`,
    createdAt: new Date().toISOString(),
    grade: criteria.grade || 'mixed',
    topic: criteria.topic || 'mixed',
    difficulty: criteria.difficulty || 'mixed',
    questionCount: selected.length,
    source: 'rag-assembled',
    criteria: criteria,
    questions: selected.map(q => ({
      questionId: q.id,
      quizId: q.quizId,
      quizTitle: q.quizTitle,
      grade: q.grade,
      topic: q.topic,
      difficulty: q.difficulty,
      hasImage: q.hasImage
    }))
  };

  return quiz;
}

/**
 * Get full question details
 * @param {string} questionId
 * @returns {Object|null}
 */
function getQuestionDetails(questionId) {
  const { loadRAGData } = require('./search-rag');
  const { metadata } = loadRAGData();

  const meta = metadata.find(m => m.id === questionId);
  if (!meta) return null;

  // Load full question from file
  const ragDbDir = path.join(__dirname, '..', 'rag-db');
  const topicFolder = getTopicFolderName(meta.topic);
  const questionPath = path.join(ragDbDir, 'questions', topicFolder, `${questionId}.json`);

  if (fs.existsSync(questionPath)) {
    return JSON.parse(fs.readFileSync(questionPath, 'utf8'));
  }

  return meta;
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

// CLI interface
if (require.main === module) {
  const args = process.argv.slice(2);
  const command = args[0];

  console.log('🎯 Quiz Assembler from RAG Database\n');

  try {
    if (!command || command === 'help') {
      console.log('Available commands:');
      console.log('  assemble grade=6 topic=Geometri difficulty=medium count=20');
      console.log('  assemble grade=4 difficulty=easy count=10');
      console.log('  get <questionId>');
      console.log('');
      console.log('Available topics: Bilangan, Aritmatika, Geometri, Pengukuran,');
      console.log('  Statistika, Rasio, Peluang, Aljabar, Logika');
      console.log('');
      console.log('Available difficulties: easy, medium, hard');

    } else if (command === 'assemble') {
      const criteria = {};
      let count = 20;
      let outputPath = null;

      for (let i = 1; i < args.length; i++) {
        const [key, value] = args[i].split('=');
        if (key === 'count') {
          count = parseInt(value);
        } else if (key === 'output') {
          outputPath = value;
        } else {
          criteria[key] = value;
        }
      }

      console.log('🔧 Criteria:', criteria);
      console.log('🔢 Count:', count);
      console.log('');

      const quiz = assembleQuiz(criteria, count);

      console.log('✅ Quiz assembled!\n');
      console.log('📋 Quiz Details:');
      console.log(`   Name: ${quiz.name}`);
      console.log(`   Grade: ${quiz.grade}`);
      console.log(`   Topic: ${quiz.topic}`);
      console.log(`   Difficulty: ${quiz.difficulty}`);
      console.log(`   Questions: ${quiz.questionCount}`);

      // Save to file
      const outputFile = outputPath || path.join(
        __dirname, '..', 'rag-db', 'assembled-quizzes',
        `quiz-${Date.now()}.json`
      );

      // Ensure directory exists
      const dir = path.dirname(outputFile);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      fs.writeFileSync(outputFile, JSON.stringify(quiz, null, 2));
      console.log(`\n💾 Saved to: ${outputFile}`);

    } else if (command === 'get') {
      const questionId = args[1];
      if (!questionId) {
        console.error('❌ Question ID required');
        process.exit(1);
      }

      const question = getQuestionDetails(questionId);

      if (!question) {
        console.error('❌ Question not found:', questionId);
        process.exit(1);
      }

      console.log('📋 Question Details:\n');
      console.log(`ID: ${question.id}`);
      console.log(`Quiz: ${question.quizTitle}`);
      console.log(`Grade: ${question.grade} | Topic: ${question.topic} | Difficulty: ${question.difficulty}`);
      console.log(`\nQuestion (ID): ${question.id_q}`);
      console.log(`Question (EN): ${question.en_q}`);
      console.log(`\nOptions: ${question.options.join(', ')}`);
      console.log(`Answer: ${question.correctAnswerIndex} (${question.options[question.correctAnswerIndex]})`);
      console.log(`\nExplanation (ID): ${question.id_exp?.substring(0, 100)}...`);
      console.log(`\nSkill Tags: ${question.skillTags?.join(', ')}`);

    } else {
      console.error('❌ Unknown command:', command);
      console.log('Run with no arguments for help');
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
    console.error(error.stack);
    process.exit(1);
  }
}

module.exports = {
  assembleQuiz,
  getQuestionDetails,
  filterSearch,
  loadRAGData
};
