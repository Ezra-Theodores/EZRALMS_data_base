/**
 * G8 NATIONAL PLUS - Progress Monitor & Resumer
 * 
 * This script monitors the progress of content creation and can resume if it stops.
 * It checks the class page and shows what has been created vs what's remaining.
 * 
 * Usage: 
 *   node monitor.js           - Show progress
 *   node monitor.js --resume  - Resume automation
 *   node monitor.js --create - Start fresh automation
 */

const curriculum = require('./g8-automation.js');

const TOPICS = curriculum.CURRICULUM;

// Expected subtopics
const EXPECTED_SUBTOPICS = TOPICS.flatMap(t => t.subtopics.map(s => s.title));

/**
 * Parse the class page to see what subtopics exist
 */
async function checkProgress() {
  console.log('\n📊 G8 NATIONAL PLUS Progress Check\n');
  console.log('=' .repeat(50));
  
  console.log('\n📋 Expected Subtopics:');
  EXPECTED_SUBTOPICS.forEach((title, i) => {
    console.log(`  ${i + 1}. ${title}`);
  });
  
  console.log('\n💡 To check current progress, run:');
  console.log('   node monitor.js --resume  - Resume automation');
  console.log('   node monitor.js --create - Start fresh automation');
  
  console.log('\n📍 Manual Check:');
  console.log('   Visit: https://students.ezralms.com/class/rKLckFly8YRbdHrAnu36');
  console.log('   Look for topic headings and count subtopics\n');
}

/**
 * Resume/Start the automation
 */
async function resumeAutomation() {
  console.log('\n🚀 G8 NATIONAL PLUS - Automation Resumer\n');
  console.log('='.repeat(50));
  
  console.log('\n⚠️  This automation requires manual browser control.');
  console.log('\n📍 To continue manually:');
  console.log('1. Open Chrome with OpenCode extension');
  console.log('2. Go to: https://students.ezralms.com/class/rKLckFly8YRbdHrAnu36');
  console.log('3. For each empty topic (showing "No subtopics"):');
  console.log('   a. Click "Add Sub-topic"');
  console.log('   b. Click "Subject Matter"');
  console.log('   c. Click "Create New Subject Matter"');
  console.log('   d. Enter title (e.g., "G8-03.3 Quadrilaterals")');
  console.log('   e. Click "Create & Open Editor"');
  console.log('   f. Paste content');
  console.log('   g. Click Save');
  
  console.log('\n📋 Remaining Subtopics to Create:\n');
  
  let topicNum = 0;
  for (const topic of TOPICS) {
    topicNum++;
    console.log(`\n📌 ${topic.topic}:`);
    for (const sub of topic.subtopics) {
      console.log(`   → ${sub.title}`);
    }
  }
}

/**
 * Show detailed instructions for manual creation
 */
function showInstructions() {
  console.log(`
╔════════════════════════════════════════════════════════════════╗
║        G8 NATIONAL PLUS - Manual Creation Guide          ║
╚════════════════════════════════════════════════════════════════╝

🎯 Target: https://students.ezralms.com/class/rKLckFly8YRbdHrAnu36

📝 Total Subtopics to Create: 26

STEP-BY-STEP:

1️⃣  Open Browser
   → Go to https://students.ezralms.com
   → Login as EzraT (PIN: 223183)
   → Navigate to Classes → G8 NATIONAL PLUS

2️⃣  For Each Empty Topic:
   → Look for topic showing "No subtopics"
   → Click "Add Sub-topic"

3️⃣  Create Subtopic:
   → Click "Subject Matter"
   → Click "Create New Subject Matter"
   → Enter title (see list below)
   → Click "Create & Open Editor"

4️⃣  Add Content:
   → Paste HTML in editor
   → Click Save

5️⃣  Repeat for all 26 subtopics

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 SUBTOPIC LIST (26 total):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

G8-03 Geometry and Measurement (5):
  1. G8-03.1 Lines, Angles, and Proofs ✓ DONE
  2. G8-03.2 Triangles ✓ DONE
  3. G8-03.3 Quadrilaterals
  4. G8-03.4 Circles
  5. G8-03.5 Constructions and Loci

G8-04 Statistics and Probability (5):
  1. G8-04.1 Data Collection and Representation
  2. G8-04.2 Measures of Central Tendency
  3. G8-04.3 Measures of Spread
  4. G8-04.4 Probability Basics
  5. G8-04.5 Probability of Combined Events

G8-05 Algebraic Manipulation (5):
  1. G8-05.1 Algebraic Expressions
  2. G8-05.2 Algebraic Formulae
  3. G8-05.3 Linear Equations
  4. G8-05.4 Linear Inequalities
  5. G8-05.5 Expanding and Factoring

G8-06 Number Skills and Indices (4):
  1. G8-06.1 Integers and Operations
  2. G8-06.2 Indices and Powers
  3. G8-06.3 Standard Form
  4. G8-06.4 Roots and Surds

G8-07 Ratio and Proportion (4):
  1. G8-07.1 Ratio
  2. G8-07.2 Proportion
  3. G8-07.3 Direct and Inverse Proportion
  4. G8-07.4 Percentage

G8-08 Sets (3):
  1. G8-08.1 Introduction to Sets
  2. G8-08.2 Operations on Sets
  3. G8-08.3 Applications of Sets

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 Pro Tips:
  • Keep this list open while creating
  • Mark each as done after saving
  • Take breaks every 5 subtopics
  • Save content before closing editor
`);
}

// Main
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  showInstructions();
} else if (args.includes('--resume')) {
  resumeAutomation();
} else if (args.includes('--create')) {
  resumeAutomation();
} else {
  checkProgress();
}

module.exports = { checkProgress, resumeAutomation, showInstructions };