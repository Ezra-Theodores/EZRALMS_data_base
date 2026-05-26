/**
 * RAG Database Web Server
 * Serves static files and provides API endpoints using SQLite
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const sqlite3 = require('sqlite3').verbose();

const PORT = process.env.PORT || 3000;
const PUBLIC_DIR = path.join(__dirname, 'public');
const DB_PATH = path.join(__dirname, '..', 'data_house.db');

// Connect to SQLite
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('Error opening database:', err.message);
  } else {
    console.log('Connected to the SQLite database:', DB_PATH);
  }
});

// MIME types
const MIME_TYPES = {
  '.html': 'text/html',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.eot': 'application/vnd.ms-fontobject'
};

// Request handler
const server = http.createServer((req, res) => {
  const parsedUrl = url.parse(req.url, true);
  const pathname = parsedUrl.pathname;

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API routes
  if (pathname.startsWith('/api/')) {
    handleApiRequest(req, res, pathname, parsedUrl.query);
    return;
  }

  // Static files
  let filePath = pathname === '/' ? '/index.html' : pathname;
  filePath = path.join(PUBLIC_DIR, filePath);

  const ext = path.extname(filePath).toLowerCase();
  const contentType = MIME_TYPES[ext] || 'application/octet-stream';

  fs.readFile(filePath, (err, content) => {
    if (err) {
      if (err.code === 'ENOENT') {
        res.writeHead(404, { 'Content-Type': 'text/html' });
        res.end(`<h1>404 - Page Not Found</h1><a href="/">Go Home</a>`);
      } else {
        res.writeHead(500);
        res.end(`Server Error: ${err.code}`);
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content, 'utf-8');
    }
  });
});

// API request handler
function handleApiRequest(req, res, pathname, query) {
  res.setHeader('Content-Type', 'application/json');

  const route = pathname.replace('/api', '');

  switch (route) {
    case '/stats':
      // Get counts by grade
      db.all("SELECT grade, COUNT(*) as count FROM questions_normalized GROUP BY grade", (err, gradeRows) => {
        if (err) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: err.message }));
          return;
        }

        // Get total questions
        db.get("SELECT COUNT(*) as total FROM questions_normalized", (err, totalRow) => {
          if (err) {
            res.writeHead(500);
            res.end(JSON.stringify({ error: err.message }));
            return;
          }

          const grades = {};
          gradeRows.forEach(row => {
            if (row.grade) grades[row.grade] = row.count;
          });

          res.writeHead(200);
          res.end(JSON.stringify({
            totalQuestions: totalRow.total,
            grades: grades,
            timestamp: new Date().toISOString()
          }));
        });
      });
      break;

    case '/questions':
      const limit = parseInt(query.limit) || 20;
      const page = parseInt(query.page) || 1;
      const offset = (page - 1) * limit;
      const grade = query.grade;
      
      let sql = "SELECT * FROM questions_normalized";
      let countSql = "SELECT COUNT(*) as total FROM questions_normalized";
      const params = [];
      
      if (grade) {
        sql += " WHERE grade = ?";
        countSql += " WHERE grade = ?";
        params.push(grade);
      }
      
      sql += ` LIMIT ? OFFSET ?`;
      const queryParams = [...params, limit, offset];

      db.get(countSql, params, (err, countRow) => {
        if (err) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: err.message }));
          return;
        }

        db.all(sql, queryParams, (err, rows) => {
          if (err) {
            res.writeHead(500);
            res.end(JSON.stringify({ error: err.message }));
            return;
          }
          
          res.writeHead(200);
          res.end(JSON.stringify({
            questions: rows.map(r => {
              let opts = [];
              try { opts = JSON.parse(r.options || '[]'); } catch(e) {}
              
              return {
                ...r,
                options: opts,
                correctAnswerIndex: r.ans,
                hasImage: r.image && r.image !== 'null' && r.image !== ''
              };
            }),
            pagination: { 
              limit, 
              page, 
              total: countRow.total,
              totalPages: Math.ceil(countRow.total / limit)
            }
          }));
        });
      });
      break;

    case '/tables':
      db.all("SELECT name FROM sqlite_master WHERE type='table'", (err, rows) => {
        if (err) {
          res.writeHead(500);
          res.end(JSON.stringify({ error: err.message }));
          return;
        }
        res.writeHead(200);
        res.end(JSON.stringify({ tables: rows.map(r => r.name) }));
      });
      break;

    case '/questions/update-topic':
      if (req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk.toString(); });
        req.on('end', () => {
          try {
            const { ids, topic } = JSON.parse(body);
            if (!ids || !Array.isArray(ids) || !topic) {
              res.writeHead(400);
              res.end(JSON.stringify({ error: 'Missing ids or topic' }));
              return;
            }

            const placeholders = ids.map(() => '?').join(',');
            const sql = `UPDATE questions_normalized SET topic = ? WHERE id IN (${placeholders})`;
            
            db.run(sql, [topic, ...ids], function(err) {
              if (err) {
                res.writeHead(500);
                res.end(JSON.stringify({ error: err.message }));
                return;
              }
              res.writeHead(200);
              res.end(JSON.stringify({ 
                success: true, 
                message: `Updated ${this.changes} questions`,
                changes: this.changes 
              }));
            });
          } catch (e) {
            res.writeHead(400);
            res.end(JSON.stringify({ error: 'Invalid JSON' }));
          }
        });
      } else {
        res.writeHead(405);
        res.end(JSON.stringify({ error: 'Method not allowed' }));
      }
      break;

    case '/sync':
      const { exec } = require('child_process');
      const syncScript = path.join(__dirname, 'sync_firebase_to_sqlite.py');
      
      res.writeHead(200);
      res.write(JSON.stringify({ status: 'started', message: 'Synchronization started in background' }));
      res.end();

      console.log('Starting synchronization script...');
      exec(`python "${syncScript}"`, (error, stdout, stderr) => {
        if (error) {
          console.error(`Sync error: ${error.message}`);
          return;
        }
        if (stderr) {
          console.error(`Sync stderr: ${stderr}`);
          return;
        }
        console.log(`Sync success: ${stdout}`);
      });
      break;

    default:
      res.writeHead(404);
      res.end(JSON.stringify({ error: 'API endpoint not found' }));
  }
}

// Start server
server.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     EZRA LMS RAG Server (SQLite) - Running               ║
║                                                          ║
║        http://localhost:${PORT}                            ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
  `);
});
