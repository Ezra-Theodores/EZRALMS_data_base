/**
 * Extract Firestore data to local JSON
 * Ekstrak semua quiz dari Firestore ke file JSON lokal
 */

const admin = require('firebase-admin');
const fs = require('fs');
const path = require('path');

// Initialize Firebase
const serviceAccountPath = path.join(__dirname, '..', 'firebase_credentials.json');
const serviceAccount = JSON.parse(fs.readFileSync(serviceAccountPath, 'utf8'));

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount)
});

const db = admin.firestore();

async function extractAllQuizzes() {
  console.log('🔍 Memulai ekstrak data dari Firestore...');

  try {
    const quizzesSnapshot = await db.collection('quizzes').get();
    console.log(`📊 Ditemukan ${quizzesSnapshot.size} quiz`);

    const quizzesByGrade = {};
    let totalQuestions = 0;

    // Process each quiz
    for (const quizDoc of quizzesSnapshot.docs) {
      const quizData = quizDoc.data();
      const quizId = quizDoc.id;

      // Get questions subcollection
      const questionsSnapshot = await quizDoc.ref.collection('questions').get();
      const questions = questionsSnapshot.docs.map(q => ({
        id: q.id,
        ...q.data()
      }));

      totalQuestions += questions.length;

      // Construct full quiz object
      const fullQuiz = {
        id: quizId,
        type: quizData.type || 'regular',
        title: quizData.title || 'Untitled',
        subject: quizData.subject || 'Math',
        grade: quizData.grade || '1',
        difficulty: quizData.difficulty || 'Medium',
        duration: quizData.duration || 3600,
        createdBy: quizData.createdBy || '',
        creatorName: quizData.creatorName || 'Unknown',
        createdAt: quizData.createdAt || { _seconds: 0, _nanoseconds: 0 },
        questionCount: questions.length,
        questions: questions
      };

      // Group by grade
      const gradeKey = `kelas-${fullQuiz.grade}-sd`;
      if (!quizzesByGrade[gradeKey]) {
        quizzesByGrade[gradeKey] = [];
      }
      quizzesByGrade[gradeKey].push(fullQuiz);
    }

    // Save to files
    const outputDir = path.join(__dirname, '..', 'data');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }

    // Save all quizzes combined
    const allQuizzes = Object.values(quizzesByGrade).flat();
    fs.writeFileSync(
      path.join(outputDir, 'all-quizzes.json'),
      JSON.stringify(allQuizzes, null, 2)
    );

    // Save by grade
    for (const [grade, quizzes] of Object.entries(quizzesByGrade)) {
      const gradeDir = path.join(outputDir, grade);
      if (!fs.existsSync(gradeDir)) {
        fs.mkdirSync(gradeDir, { recursive: true });
      }

      fs.writeFileSync(
        path.join(gradeDir, `all-quizzes-${grade}.json`),
        JSON.stringify(quizzes, null, 2)
      );

      console.log(`   ✓ ${grade}: ${quizzes.length} quiz`);
    }

    // Summary
    console.log('\n📊 Summary:');
    console.log(`   Total Quiz: ${allQuizzes.length}`);
    console.log(`   Total Questions: ${totalQuestions}`);
    console.log(`   Grades: ${Object.keys(quizzesByGrade).length}`);
    console.log(`\n💾 Output saved to: ${outputDir}`);

    return {
      totalQuizzes: allQuizzes.length,
      totalQuestions,
      byGrade: Object.fromEntries(
        Object.entries(quizzesByGrade).map(([k, v]) => [k, v.length])
      )
    };

  } catch (error) {
    console.error('❌ Error saat ekstrak data:', error);
    throw error;
  } finally {
    admin.app().delete();
  }
}

// Run if called directly
if (require.main === module) {
  extractAllQuizzes()
    .then(result => {
      console.log('\n✅ Ekstrak selesai!');
      process.exit(0);
    })
    .catch(err => {
      console.error('\n❌ Ekstrak gagal:', err);
      process.exit(1);
    });
}

module.exports = { extractAllQuizzes };
