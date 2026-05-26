/**
 * G8 NATIONAL PLUS - Automation Runner
 * 
 * This script runs the automation to create all subtopics in the G8 NATIONAL PLUS class.
 * It uses Chrome DevTools to interact with the browser.
 * 
 * Usage: node run-automation.js [--dry-run]
 * 
 * The script will:
 * 1. Login to EzraLMS
 * 2. Navigate to G8 NATIONAL PLUS class
 * 3. Create each topic if it doesn't exist
 * 4. Add each subtopic with subject matter content
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

// Import curriculum data
const curriculum = require('./g8-automation.js');

// Configuration
const CONFIG = {
  baseUrl: 'https://students.ezralms.com',
  username: curriculum.USERNAME,
  pin: curriculum.PIN,
  classUrl: curriculum.CLASS_URL
};

let browser = null;
let page = null;

/**
 * Initialize browser
 */
async function initBrowser() {
  console.log('🚀 Starting browser...');
  
  // Connect to existing Chrome with debug port
  browser = await chromium.connectOverCDP('http://localhost:9222');
  const context = browser.contexts()[0];
  page = context.pages()[0];
  
  console.log('✅ Browser connected');
  return page;
}

/**
 * Login to EzraLMS
 */
async function login() {
  console.log('🔐 Checking login status...');
  
  await page.goto(CONFIG.baseUrl);
  await page.waitForTimeout(2000);
  
  const url = page.url();
  
  // Check if already logged in
  if (url.includes('/dashboard') || url.includes('/tutor-dashboard') || url.includes('/classes')) {
    console.log('✅ Already logged in');
    return true;
  }
  
  // Need to login
  console.log('📝 Logging in...');
  
  // Fill username
  await page.fill('#identifier', CONFIG.username);
  await page.click('button:has-text("Continue")');
  
  // Wait for PIN modal
  await page.waitForTimeout(2000);
  await page.waitForSelector('#pin', { timeout: 5000 }).catch(() => null);
  
  // Fill PIN
  await page.fill('#pin', CONFIG.pin);
  await page.click('button:has-text("Sign In")');
  
  // Wait for dashboard
  await page.waitForTimeout(3000);
  
  console.log('✅ Logged in successfully');
  return true;
}

/**
 * Navigate to class
 */
async function navigateToClass() {
  console.log('📂 Navigating to G8 NATIONAL PLUS class...');
  
  await page.goto(CONFIG.classUrl);
  await page.waitForTimeout(3000);
  
  // Check if we're on the class page
  const content = await page.content();
  if (content.includes('G8 NATIONAL PLUS')) {
    console.log('✅ On class page');
    return true;
  }
  
  console.log('⚠️ Could not verify class page');
  return false;
}

/**
 * Create a topic if it doesn't exist
 */
async function createTopic(topicName) {
  console.log(`📋 Checking topic: ${topicName}...`);
  
  // Check if topic exists
  const topicExists = await page.$(`text=${topicName}`);
  
  if (topicExists) {
    console.log(`  ✅ Topic exists`);
    return true;
  }
  
  // Click Add Topic button
  console.log(`  ➕ Creating topic: ${topicName}`);
  await page.click('button:has-text("Add Topic")');
  await page.waitForTimeout(1000);
  
  // Fill topic name
  await page.fill('input[name="topicName"]', topicName);
  await page.click('button:has-text("Add")');
  
  await page.waitForTimeout(2000);
  console.log(`  ✅ Topic created`);
  
  return true;
}

/**
 * Add a subtopic to a topic
 */
async function addSubtopic(topicName, subtopic) {
  console.log(`  📖 Adding: ${subtopic.title}`);
  
  // Expand the topic
  await page.click(`text=${topicName}`);
  await page.waitForTimeout(1000);
  
  // Click Add Sub-topic
  await page.click(`text=Add Sub-topic >> nth=0`);
  await page.waitForTimeout(1000);
  
  // Select Subject Matter
  if (await page.$('text=Subject Matter')) {
    await page.click('text=Subject Matter');
  }
  await page.waitForTimeout(500);
  
  // Click Create New (or create button)
  await page.click('text=Create New >> nth=0');
  await page.waitForTimeout(1000);
  
  // Fill title
  const titleInput = await page.$('input[name="title"]');
  if (titleInput) {
    await titleInput.fill(subtopic.title);
  } else {
    await page.fill('input[type="text"]', subtopic.title);
  }
  
  // Click Create & Open Editor
  await page.click('text=Create & Open Editor');
  await page.waitForTimeout(3000);
  
  // Now we're in the editor - paste content
  // Use the workaround: type, delete, paste, cut, paste
  const textarea = await page.$('textarea[name="html_content"]');
  
  if (textarea) {
    // Type one character to activate
    await textarea.type('a');
    await textarea.press('Backspace');
    
    // Paste content
    await page.evaluate((content) => {
      navigator.clipboard.writeText(content);
    }, subtopic.content);
    
    await textarea.press('Control+a');
    await textarea.press('Control+v');
  }
  
  // Save
  await page.click('text=Save');
  await page.waitForTimeout(2000);
  
  console.log(`  ✅ Created: ${subtopic.title}`);
  
  // Go back to class page
  await page.goto(CONFIG.classUrl);
  await page.waitForTimeout(2000);
  
  return true;
}

/**
 * Main automation runner
 */
async function runAutomation() {
  try {
    // Initialize browser
    await initBrowser();
    
    // Login
    await login();
    
    // Navigate to class
    await navigateToClass();
    
    // Process each topic
    for (const topicData of curriculum.CURRICULUM) {
      const topicName = topicData.topic;
      
      // Create topic if needed
      await createTopic(topicName);
      
      // Add each subtopic
      for (const subtopic of topicData.subtopics) {
        await addSubtopic(topicName, subtopic);
      }
    }
    
    console.log('🎉 All content created successfully!');
    
  } catch (error) {
    console.error('❌ Error:', error.message);
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

// Run if called directly
if (require.main === module) {
  const isDryRun = process.argv.includes('--dry-run');
  
  if (isDryRun) {
    console.log('� dry-run mode - showing curriculum only');
    console.log(JSON.stringify(curriculum.CURRICULUM, null, 2));
  } else {
    runAutomation().catch(console.error);
  }
}

module.exports = { runAutomation };