const fs = require('fs');

const html = fs.readFileSync('C:/Users/Admin/Repo/EzraLms_automation/G8-01.1.html', 'utf-8');

// Extract srcdoc attribute from iframe
const match = html.match(/<iframe[^>]*srcdoc="([^"]+)"/);
if (!match) {
  console.log('No iframe srcdoc found');
  process.exit(1);
}

const srcdoc = decodeURIComponent(match[1]);
fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/G8-01.1-content.html', srcdoc);
console.log('Extracted srcdoc content');

// Strip HTML tags and get text
const textOnly = srcdoc.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
fs.writeFileSync('C:/Users/Admin/Repo/EzraLms_automation/G8-01.1-content.txt', textOnly);
console.log('Text content saved');
console.log('\n=== CONTENT TEXT ===\n');
console.log(textOnly);