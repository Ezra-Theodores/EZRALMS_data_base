# EzraLMS Subtopic Creation - FULL QUALITY STANDARD

## Overview
All subtopics in EzraLMS must follow the FULL interactive lesson format - not simple HTML. This is a complete web app with:

## Required Components

### 1. HTML Structure
- Full HTML5 document with proper head/body
- Embedded CSS styles
- Embedded JavaScript
- EzraLMS logo image
- Language toggle (EN/ID)

### 2. Visual Design
- Clean, modern UI matching existing lessons
- Gradient hero section
- Card-based content
- Score/progress bar
- Tab navigation

### 3. Content Tabs (minimum 2-4)
- **Concepts/Concept** - Main theory
- **Laws/Rules** - Key formulas/rules
- **Practice/Examples** - Worked examples
- **Exercises/Latihan** - Interactive quizzes

### 4. Bilingual Support
- Full English content
- Full Indonesian translation
- JavaScript function `setLang(lang)` to switch

### 5. Interactive Features
- Score tracking
- Multiple choice questions
- Feedback on answers (correct/wrong)
- Progress bar
- Language switcher

## Template Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>SUBTOPIC TITLE</title>
    <style>
        /* Full CSS from existing lessons */
    </style>
</head>
<body>
    <div class="wrap">
        <!-- Top Bar with Language Toggle -->
        <div class="topbar">
            <div class="lang-btn">
                <button class="active" onclick="setLang('en')">English</button>
                <button onclick="setLang('id')">Indonesia</button>
            </div>
            <img src="https://i.imgur.com/3lLW585.png" class="logo">
        </div>

        <!-- Hero Section -->
        <div class="hero">
            <h1 id="h-title">TITLE</h1>
            <p id="h-sub">Cambridge Grade 8 Mathematics — TOPIC</p>
        </div>

        <!-- Score Bar -->
        <div class="score-bar">
            <span class="score-badge">Score: 0 / 0</span>
            <div class="progress-wrap"><div class="progress-fill" style="width:0%"></div></div>
            <span>0%</span>
        </div>

        <!-- Tabs -->
        <div class="tabs">
            <button class="tab-btn active">Concepts</button>
            <button class="tab-btn">Laws</button>
            <button class="tab-btn">Practice</button>
        </div>

        <!-- Content Sections -->
        <div class="section active">
            <!-- Cards with content -->
        </div>
        <div class="section">
            <!-- Laws/Rules -->
        </div>
        <div class="section">
            <!-- Quiz Questions -->
        </div>
    </div>

    <script>
        // Language translations object
        const TX = {
            en: { /* English */ },
            id: { /* Indonesian */ }
        };
        
        // Functions: setLang(), showTab(), mcq(), updateScore()
    </script>
</body>
</html>
```

## Creation Steps

1. **Go to Class Page**
   - Navigate to: https://students.ezralms.com/class/CLASS_ID

2. **Click Add Sub-topic**
   - Find empty topic section
   - Click "Add Sub-topic" button

3. **Select Subject Matter**
   - Click "Subject Matter"
   - Click "Create New Subject Matter"

4. **Fill Title**
   - Enter subtopic title (e.g., "G8-03.3 Quadrilaterals")
   - Click "Create & Open Editor"

5. **Paste Full HTML**
   - Must use COMPLETE HTML template (not simple HTML)
   - Include all CSS, JS, bilingual content

6. **Save**
   - Click Save button
   - Verify saved

## Important Notes

- NEVER use simple HTML only - MUST have interactive features
- ALWAYS include bilingual (EN + ID) content
- ALWAYS include score tracking and quizzes
- Logo URL: https://i.imgur.com/3lLW585.png
- Follow exact CSS from existing lessons
- JavaScript required for language toggle and quiz logic

## Files Reference
- Existing full lesson: `C:\Users\Admin\Repo\EzraLms_automation\G8-01.1.html`
- Template: `C:\Users\Admin\Repo\EzraLms_automation\KURIKULUM EZRA\KURIKULUM UMUM\G8 NATIONAL PLUS\templates.js`