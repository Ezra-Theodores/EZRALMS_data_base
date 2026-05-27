/* EZRA LMS Unified SPA — single-page front-end for the unified backend.
 *
 * Each panel is a small module-style object with init/load. Routing is
 * hash-based (window.location.hash = "#users").
 */

(() => {
  // ── utility ───────────────────────────────────────────────────────────
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const escape = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  const toast = (msg, kind = "") => {
    const t = $("#toast");
    t.textContent = msg;
    t.className = `toast show ${kind}`;
    setTimeout(() => t.classList.remove("show"), 2400);
  };

  async function api(path, opts = {}) {
    try {
      const r = await fetch(path, opts);
      const json = await r.json();
      return json;
    } catch (e) {
      console.error(path, e);
      return { success: false, error: e.message };
    }
  }

  // ── routing ───────────────────────────────────────────────────────────
  const VIEWS = ["dashboard", "users", "curriculum", "attendance", "student",
                 "rag", "quizzes", "pipeline", "sync", "automation", "finance"];

  const VIEW_TITLES = {
    student: "Student Progress Tracking",
  };

  function switchView(view) {
    if (!VIEWS.includes(view)) view = "dashboard";
    $$(".view").forEach(v => v.style.display = "none");
    $(`#view-${view}`).style.display = "block";
    $$("#sidebar-menu li").forEach(li => li.classList.toggle("active", li.dataset.view === view));
    $("#pageTitle").textContent = VIEW_TITLES[view] || (view.charAt(0).toUpperCase() + view.slice(1));
    if (MODULES[view] && MODULES[view].onShow) MODULES[view].onShow();
  }

  function handleHashChange() {
    const view = (location.hash || "#dashboard").slice(1);
    switchView(view);
  }

  // ── DASHBOARD ─────────────────────────────────────────────────────────
  const dashboard = {
    async onShow() {
      await Promise.all([
        this.loadStats(),
        this.loadBlueprintHealth(),
      ]);
    },
    async loadStats() {
      const [curr, qz, att] = await Promise.all([
        api("/api/curriculum/stats"),
        api("/api/quizzes/stats"),
        api("/api/attendance/stats"),
      ]);

      if (curr.success) {
        const d = curr.data;
        const totalUsers = Object.values(d.users_by_role || {}).reduce((a, b) => a + b, 0);
        $("#stat-users").textContent = totalUsers;
        $("#stat-grades").textContent = d.grades_count;
        $("#stat-classes").textContent = d.classes_count;
        $("#stat-topics").textContent = d.topics_count;

        const labelMap = d.users_by_role || {};
        const max = Math.max(1, ...Object.values(labelMap));
        $("#chart-roles").innerHTML = Object.entries(labelMap).map(([k, v]) => `
          <div class="row"><div class="label">${escape(k)}</div>
            <div class="bar" style="width:${(v / max) * 100}%"></div>
            <div class="value">${v}</div></div>
        `).join("") || '<p class="empty">No data</p>';
      }

      if (qz.success) {
        const d = qz.data;
        $("#stat-quizzes").textContent = d.total_quizzes;
        $("#stat-questions").textContent = d.total_questions;

        const grades = d.by_grade || {};
        const entries = Object.entries(grades).sort((a, b) => {
          const an = parseInt(a[0]); const bn = parseInt(b[0]);
          return (isNaN(an) ? 99 : an) - (isNaN(bn) ? 99 : bn);
        });
        const max = Math.max(1, ...entries.map(e => e[1]));
        $("#chart-grades").innerHTML = entries.map(([k, v]) => `
          <div class="row"><div class="label">Grade ${escape(k)}</div>
            <div class="bar" style="width:${(v / max) * 100}%"></div>
            <div class="value">${v}</div></div>
        `).join("") || '<p class="empty">No data</p>';
      }

      if (att.success) {
        $("#stat-attendance").textContent = att.data.total_records;
      }

      // quiz attempts indirect: derive from quizzes endpoint? Use placeholder for now.
      $("#stat-attempts").textContent = "—";
      // Pull from leaderboard endpoint as a proxy (count of attempts in top 20).
      // Real count would need a new endpoint; deferred.
    },
async loadBlueprintHealth() {
      const blueprints = [
        ["attendance",   "/api/attendance/ping"],
        ["curriculum",   "/api/curriculum/ping"],
        ["students",     "/api/students/ping"],
        ["automation",   "/api/automation/ping"],
        ["firebase_sync", "/api/sync/ping"],
        ["pipeline",     "/api/pipeline/ping"],
        ["rag",          "/api/rag/ping"],
        ["quiz_manager", "/api/quizzes/ping"],
        ["finance",      "/finance/health"],
      ];
      const results = await Promise.all(blueprints.map(([n, p]) => api(p)));
      $("#blueprint-health").innerHTML = blueprints.map(([name], i) => {
        const ok = results[i].success;
        return `<div class="health-cell"><span>${name}</span>
                <span class="status-badge ${ok ? 'ok' : 'err'}">${ok ? 'UP' : 'DOWN'}</span></div>`;
      }).join("");
    },
  };

  // ── USERS ─────────────────────────────────────────────────────────────
  const users = {
    init() {
      $("#usersLoadBtn").addEventListener("click", () => this.load());
      $("#usersSearch").addEventListener("keyup", (e) => { if (e.key === "Enter") this.load(); });
    },
    onShow() { this.load(); },
    async load() {
      const search = $("#usersSearch").value.trim();
      const role = $("#usersRole").value;
      const qs = new URLSearchParams();
      if (search) qs.set("search", search);
      if (role)   qs.set("role", role);
      const tbody = $("#usersTableBody");
      tbody.innerHTML = `<tr><td colspan="6" class="empty">Loading…</td></tr>`;

      const r = await api(`/api/curriculum/tree/users?${qs}`);
      if (!r.success) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">Error: ${escape(r.error)}</td></tr>`;
        return;
      }
      if (!r.data.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">No users found.</td></tr>`;
        return;
      }
      tbody.innerHTML = r.data.map(u => `
        <tr>
          <td><code>${escape(u.user_id || "—")}</code></td>
          <td>${escape(u.name || "—")}</td>
          <td>${escape(u.email || "—")}</td>
          <td><span class="status-badge">${escape(u.role || "—")}</span></td>
          <td>${escape(u.phone || "—")}</td>
          <td>${escape(u.xp ?? "—")}</td>
        </tr>
      `).join("");
    },
  };

  // ── CURRICULUM TREE ───────────────────────────────────────────────────
  const curriculum = {
    init() {
      $("#treeExpandAll").addEventListener("click", () => $$(".tree-node-children").forEach(e => e.style.display = "block"));
      $("#treeCollapseAll").addEventListener("click", () => $$(".tree-node-children").forEach(e => e.style.display = "none"));
    },
    async onShow() {
      const root = $("#curriculumTree");
      root.textContent = "Loading…";
      const r = await api("/api/curriculum/tree/curriculum");
      if (!r.success) { root.textContent = "Error: " + r.error; return; }
      root.innerHTML = "<ul>" + r.data.map(node => this.renderNode(node)).join("") + "</ul>";
      root.addEventListener("click", (e) => {
        const node = e.target.closest(".tree-node");
        if (!node) return;
        if (e.target.classList.contains("toggle")) {
          const children = node.nextElementSibling;
          if (children && children.classList.contains("tree-node-children")) {
            const hidden = children.style.display === "none";
            children.style.display = hidden ? "block" : "none";
            e.target.textContent = hidden ? "▾" : "▸";
          }
          return;
        }
        $$(".tree-node").forEach(n => n.classList.remove("selected"));
        node.classList.add("selected");
        this.showDetails(JSON.parse(node.dataset.payload));
      });
    },
    renderNode(node) {
      const hasKids = node.children && node.children.length;
      const toggle = hasKids ? '<span class="toggle">▾</span>' : '<span class="toggle">•</span>';
      const icon = { grade: "🎓", class: "🏫", topic: "📚", sub_topic: "📖", material: "📎", quiz: "📝" }[node.type] || "·";
      const label = escape(node.name || node.title || node.id);
      const payload = escape(JSON.stringify(node));
      return `<li>
        <div class="tree-node" data-payload='${payload}'>
          ${toggle} ${icon} <span>${label}</span>
        </div>
        ${hasKids ? `<ul class="tree-node-children">${node.children.map(c => this.renderNode(c)).join("")}</ul>` : ""}
      </li>`;
    },
    showDetails(node) {
      $("#treeSelectedTitle").textContent = `${node.type}: ${node.name || node.title || node.id}`;
      $("#treeNodeDetails").innerHTML = `<pre class="output-block">${escape(JSON.stringify(node, null, 2))}</pre>`;
    },
  };

  // ── ATTENDANCE ────────────────────────────────────────────────────────
  const attendance = {
    init() {
      $("#attendanceForm").addEventListener("submit", (e) => { e.preventDefault(); this.search(); });
    },
    async search() {
      const fd = new FormData($("#attendanceForm"));
      const qs = new URLSearchParams();
      for (const [k, v] of fd.entries()) if (v) qs.set(k, v);
      const tbody = $("#attendanceTableBody");
      tbody.innerHTML = `<tr><td colspan="5" class="empty">Searching…</td></tr>`;
      const r = await api(`/api/attendance/search?${qs}`);
      if (!r.success) { tbody.innerHTML = `<tr><td colspan="5" class="empty">Error: ${escape(r.error)}</td></tr>`; return; }
      $("#attendanceCount").textContent = `${r.count} record(s)`;
      if (!r.data.length) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty">No matching records.</td></tr>`;
        return;
      }
      tbody.innerHTML = r.data.map(a => `
        <tr>
          <td>${escape(a.attendance_date || "—")}</td>
          <td>${escape(a.student_name || "—")}</td>
          <td><code>${escape(a.student_id || "—")}</code></td>
          <td>${escape(a.class_name || "—")}</td>
          <td><span class="status-badge">${escape(a.status || "—")}</span></td>
        </tr>
      `).join("");
    },
  };

  // ── STUDENT TRACKING ─────────────────────────────────────────────────────
  const student = {
    init() {
      $("#studentSearchBtn").addEventListener("click", () => this.search());
      $("#studentLeaderboardBtn").addEventListener("click", () => this.leaderboard());
      $("#studentSearchInput").addEventListener("keyup", (e) => { if (e.key === "Enter") this.search(); });
    },
    async search() {
      const q = $("#studentSearchInput").value.trim();
      const resultsDiv = $("#studentSearchResults");
      const profileDiv = $("#studentProfile");
      profileDiv.style.display = "none";

      if (!q) { toast("Enter a student name", "err"); return; }
      resultsDiv.style.display = "block";
      const tbody = $("#studentListBody");
      tbody.innerHTML = `<tr><td colspan="5" class="empty">Searching…</td></tr>`;

      const r = await api(`/api/students/search?q=${encodeURIComponent(q)}`);
      if (!r.success) { tbody.innerHTML = `<tr><td colspan="5" class="empty">Error: ${escape(r.error)}</td></tr>`; return; }
      if (!r.data.length) { tbody.innerHTML = `<tr><td colspan="5" class="empty">No students found.</td></tr>`; return; }
      tbody.innerHTML = r.data.map(s => `
        <tr>
          <td>${escape(s.name || "—")}</td>
          <td>${escape(s.email || "—")}</td>
          <td><span class="status-badge">${escape(s.role || "—")}</span></td>
          <td>${escape(s.xp ?? "—")}</td>
          <td><button class="btn btn-sm" onclick="STUDENT_MODULE.loadProfile('${escape(s.user_id)}')">View Profile</button></td>
        </tr>
      `).join("");
    },
    async loadProfile(studentId) {
      const profileDiv = $("#studentProfile");
      profileDiv.style.display = "block";
      profileDiv.innerHTML = `<p class="empty">Loading profile…</p>`;

      const r = await api(`/api/students/profile/${encodeURIComponent(studentId)}`);
      if (!r.success) { profileDiv.innerHTML = `<div class="status-block">${escape(r.error)}</div>`; return; }

      const p = r;
      const s = p.student;
      const qs = p.quiz_summary;
      const att = p.attendance;
      const cats = p.categories;
      const topics = p.topic_mastery;
      const quizzes = p.quizzes;
      const tasks = p.tasks;

      // Category color map
      const catColor = {
        "Bilangan": "#4CAF50", "Aljabar": "#2196F3", "Data": "#FF9800",
        "Geometri": "#9C27B0", "Kombinatorik": "#00BCD4", "Logika": "#F44336",
        "Lainnya": "#607D8B",
      };
      const catBadge = (name) => {
        const color = catColor[name] || "#607D8B";
        return `<span style="background:${color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px">${escape(name)}</span>`;
      };
      const scoreColor = (pct) => pct >= 75 ? "#4CAF50" : pct >= 60 ? "#FF9800" : "#F44336";

      // Build HTML
      profileDiv.innerHTML = `
        <div class="profile-header">
          <h2>📊 ${escape(s.name || "—")}</h2>
          <div class="profile-meta">
            <span class="status-badge">${escape(s.role || "student")}</span>
            <span>📧 ${escape(s.email || "—")}</span>
            <span>⭐ XP: ${s.total_xp || 0}</span>
          </div>
        </div>

        <!-- Summary cards -->
        <div class="stats-grid" style="margin-bottom:24px">
          <div class="stat-card"><i class="fas fa-edit"></i><div class="stat-info"><h3>${qs.total}</h3><p>Quizzes Done</p></div></div>
          <div class="stat-card"><i class="fas fa-percent"></i><div class="stat-info"><h3>${qs.average}%</h3><p>Avg Score</p></div></div>
          <div class="stat-card"><i class="fas fa-book-open"></i><div class="stat-info"><h3>${p.materials_opened}</h3><p>Materials Opened</p></div></div>
          <div class="stat-card"><i class="fas fa-calendar-check"></i><div class="stat-info"><h3>${att.summary.attendance_rate}%</h3><p>Attendance (30d)</p></div></div>
        </div>

        <div class="profile-row">
          <!-- Left: Quiz details -->
          <div class="card flex-1">
            <div class="card-header"><h3>📝 Quiz History</h3></div>
            <div class="card-body" style="max-height:400px;overflow-y:auto">
              ${quizzes.length ? `
                <table class="data-table">
                  <thead><tr><th>Quiz</th><th>Grade</th><th>Category</th><th>Score</th><th>Status</th></tr></thead>
                  <tbody>
                    ${quizzes.map(q => `
                      <tr>
                        <td>${escape(q.quiz_title || "—")}</td>
                        <td>G${escape(q.grade || "—")}</td>
                        <td>${catBadge(q.category)}</td>
                        <td style="color:${scoreColor(q.percentage)};font-weight:bold">${q.percentage}%</td>
                        <td>${q.passed ? "<span style='color:#4CAF50'>✓ Pass</span>" : "<span style='color:#F44336'>✗</span>"}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>` : '<p class="empty">No quiz data yet.</p>'}
            </div>
          </div>

          <!-- Right: Attendance -->
          <div class="card flex-1">
            <div class="card-header"><h3>📅 Attendance (30d)</h3></div>
            <div class="card-body">
              <div style="display:flex;gap:16px;margin-bottom:16px">
                <div style="text-align:center"><div style="font-size:24px;color:#4CAF50;font-weight:bold">${att.summary.present}</div><div>Present</div></div>
                <div style="text-align:center"><div style="font-size:24px;color:#F44336;font-weight:bold">${att.summary.absent}</div><div>Absent</div></div>
                <div style="text-align:center"><div style="font-size:24px;color:#FF9800;font-weight:bold">${att.summary.late}</div><div>Late</div></div>
              </div>
              <p style="color:#888;font-size:13px">${att.summary.total_days} total days tracked · ${att.summary.attendance_rate}% attendance rate</p>
              ${att.records.length ? `
                <table class="data-table" style="margin-top:8px">
                  <thead><tr><th>Date</th><th>Status</th><th>Check-in</th></tr></thead>
                  <tbody>
                    ${att.records.slice(0, 15).map(a => `
                      <tr>
                        <td>${escape(a.attendance_date || "—")}</td>
                        <td><span class="status-badge">${escape(a.status || "—")}</span></td>
                        <td>${escape(a.check_in_time || "—")}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>` : ""}
            </div>
          </div>
        </div>

        <!-- Task Assignments -->
        ${tasks.length ? `
        <div class="card" style="margin-top:16px">
          <div class="card-header"><h3>📋 Assigned Tasks</h3></div>
          <div class="card-body">
            <table class="data-table">
              <thead><tr><th>Task</th><th>Quiz</th><th>Due Date</th><th>Status</th></tr></thead>
              <tbody>
                ${tasks.map(t => `
                  <tr>
                    <td>${escape(t.title || "—")}</td>
                    <td>${escape(t.quiz_title || "—")}</td>
                    <td>${escape(t.due_date ? t.due_date.slice(0, 10) : "—")}</td>
                    <td><span class="status-badge ${t.status === "completed" ? "ok" : ""}">${escape(t.status)}</span></td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>` : ""}

        <!-- Topic Mastery by Category -->
        <div class="card" style="margin-top:16px">
          <div class="card-header"><h3>🏆 Mastery by Topic Category</h3></div>
          <div class="card-body">
            ${cats.length ? `
              <table class="data-table">
                <thead><tr><th>Category</th><th>Attempts</th><th>Average Score</th><th>Level</th></tr></thead>
                <tbody>
                  ${cats.map(c => {
                    const color = catColor[c.name] || "#607D8B";
                    const level = c.average >= 80 ? "🟢 Advanced" : c.average >= 70 ? "🟡 Proficient" : c.average >= 60 ? "🟠 Developing" : "🔴 Beginning";
                    return `<tr>
                      <td><span style="background:${color};color:#fff;padding:2px 10px;border-radius:12px;font-size:12px">${escape(c.name)}</span></td>
                      <td>${c.attempts}</td>
                      <td style="font-weight:bold;color:${scoreColor(c.average)}">${c.average}%</td>
                      <td>${level}</td>
                    </tr>`;
                  }).join("")}
                </tbody>
              </table>` : '<p class="empty">No category data yet.</p>'}
          </div>
        </div>

        <!-- Topic-level details (all topics) -->
        ${topics.length ? `
        <div class="card" style="margin-top:16px">
          <div class="card-header"><h3>📖 Topic-Level Mastery</h3></div>
          <div class="card-body" style="max-height:300px;overflow-y:auto">
            <table class="data-table">
              <thead><tr><th>Topic</th><th>Attempts</th><th>Average</th><th>Latest</th><th>Trend</th></tr></thead>
              <tbody>
                ${topics.map(t => `
                  <tr>
                    <td>${escape(t.topic || "—")}</td>
                    <td>${t.attempts}</td>
                    <td style="color:${scoreColor(t.average)};font-weight:bold">${t.average}%</td>
                    <td>${t.latest}%</td>
                    <td>${t.trend === "up" ? "📈" : "📉"}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        </div>` : ""}
      `;
    },
    async leaderboard() {
      const profileDiv = $("#studentProfile");
      const resultsDiv = $("#studentSearchResults");
      resultsDiv.style.display = "none";
      profileDiv.style.display = "block";
      profileDiv.innerHTML = `<p class="empty">Loading…</p>`;

      const r = await api("/api/students/leaderboard");
      if (!r.success) { profileDiv.innerHTML = `<div class="status-block">${escape(r.error)}</div>`; return; }
      profileDiv.innerHTML = `<div class="table-container">
        <table class="data-table">
          <thead><tr><th>#</th><th>Name</th><th>User ID</th><th>XP</th><th>Quizzes</th></tr></thead>
          <tbody>${r.data.map((u, i) => `
            <tr><td>${i + 1}</td>
                <td>${escape(u.name || "—")}</td>
                <td><code>${escape(u.user_id || "—")}</code></td>
                <td>⭐ ${u.total_xp ?? 0}</td>
                <td>${u.quiz_count ?? 0}</td>
                <td><button class="btn btn-sm" onclick="STUDENT_MODULE.loadProfile('${escape(u.user_id)}')">View</button></td>
            </tr>`).join("")}</tbody>
        </table></div>`;
    },
  };
  window.STUDENT_MODULE = student;

  // ── RAG ───────────────────────────────────────────────────────────────
  const rag = {
    init() {
      $("#ragSearchBtn").addEventListener("click", () => this.search());
      $("#ragRebuildBtn").addEventListener("click", () => this.rebuild());
      $("#ragQuery").addEventListener("keyup", (e) => { if (e.key === "Enter") this.search(); });
      // Tab switching
      $("#ragTabBm25").addEventListener("click", () => this.showTab("bm25"));
      $("#ragTabSql").addEventListener("click", () => this.showTab("sql"));
      // SQL
      $("#ragSqlBtn").addEventListener("click", () => this.runSql());
      $("#ragSqlInput").addEventListener("keyup", (e) => { if (e.key === "Enter") this.runSql(); });
    },
    showTab(tab) {
      $(".rag-tab").forEach(t => t.classList.toggle("active", t.dataset.tab === tab));
      $("#ragBm25Panel").style.display = tab === "bm25" ? "block" : "none";
      $("#ragSqlPanel").style.display = tab === "sql" ? "block" : "none";
    },
    async search() {
      const q = $("#ragQuery").value.trim();
      const type = $("#ragType").value;
      if (!q) { toast("Enter a query", "err"); return; }
      const qs = new URLSearchParams({ q });
      if (type) qs.set("type", type);
      const out = $("#ragResults");
      out.innerHTML = '<p class="empty">Searching…</p>';
      const r = await api(`/api/rag/search?${qs}`);
      if (!r.success) { out.innerHTML = `<div class="status-block">${escape(r.error)}</div>`; return; }
      if (!r.results.length) { out.innerHTML = '<p class="empty">No results.</p>'; return; }
      out.innerHTML = r.results.map(res => `
        <div class="rag-card">
          <div class="meta"><span class="type">${escape(res.source_type)}</span>
               <span class="score">${res.score.toFixed(2)}</span>
               <span>${escape(res.source_path || "")}</span></div>
          <div class="content">${escape(res.content)}</div>
        </div>
      `).join("");
    },
    async rebuild() {
      if (!confirm("Rebuild the BM25 vector index? May take ~30s.")) return;
      toast("Rebuilding…");
      const r = await api("/api/rag/rebuild", { method: "POST" });
      toast(r.success ? "Index rebuilt" : `Error: ${r.error}`, r.success ? "ok" : "err");
    },
    async runSql() {
      const sql = $("#ragSqlInput").value.trim();
      if (!sql) { toast("Enter a SELECT query", "err"); return; }
      const out = $("#ragSqlResults");
      out.innerHTML = `<p class="empty">Loading…</p>`;

      const r = await api(`/api/rag/sql?${new URLSearchParams({ sql, limit: 50 })}`);
      if (!r.success) { out.innerHTML = `<div class="status-block">Error: ${escape(r.error)}</div>`; return; }
      if (!r.rows.length) { out.innerHTML = `<p class="empty">No results (${r.count} rows returned).</p>`; return; }

      out.innerHTML = `<div style="margin-bottom:8px;font-size:0.8rem;color:var(--text-muted)">
          ${r.count} row(s)${r.has_more ? " (truncated)" : ""} · ${r.columns.length} column(s)
        </div>
        <div class="table-container">
          <table class="data-table">
            <thead><tr>${r.columns.map(c => `<th>${escape(c)}</th>`).join("")}</tr></thead>
            <tbody>${r.rows.map(row => `<tr>${r.columns.map(c => `<td>${escape(String(row[c] ?? "—"))}</td>`).join("")}</tr>`).join("")}</tbody>
          </table>
        </div>`;
    },
  };

  // ── QUIZ MANAGER ──────────────────────────────────────────────────────
  const quizManager = {
    init() {
      $("#qmSearchBtn").addEventListener("click", () => this.searchQuestions());
      $("#qmListQuizzesBtn").addEventListener("click", () => this.listQuizzes());
      $("#qmQuery").addEventListener("keyup", (e) => { if (e.key === "Enter") this.searchQuestions(); });
    },
    async searchQuestions() {
      const qs = new URLSearchParams({ limit: 20 });
      const q = $("#qmQuery").value.trim();
      const grade = $("#qmGrade").value;
      const hi = $("#qmHasImage").value;
      if (q) qs.set("q", q);
      if (grade) qs.set("grade", grade);
      if (hi) qs.set("hasImage", hi);

      const out = $("#qmResults");
      out.innerHTML = '<p class="empty">Loading…</p>';
      const r = await api(`/api/quizzes/questions?${qs}`);
      if (!r.success) { out.innerHTML = `<div class="status-block">${escape(r.error)}</div>`; return; }
      $("#qmCount").textContent = `${r.total} question(s) total — showing page ${r.page}`;
      if (!r.data.length) { out.innerHTML = '<p class="empty">No questions.</p>'; return; }
      out.innerHTML = r.data.map(q => `
        <div class="qm-card">
          <div class="qm-meta">${escape(q.topic || "—")} · ${escape(q.quiz_title || "?")} · Grade ${escape(q.grade || "?")}</div>
          <div>${escape((q.id_q || q.en_q || "").slice(0, 240))}</div>
          ${Array.isArray(q.options) && q.options.length ? `
            <ul class="qm-options">${q.options.map((o, i) =>
              `<li>${String.fromCharCode(65 + i)}. ${escape(String(o).slice(0, 120))}${q.ans === i ? ' ✅' : ''}</li>`
            ).join("")}</ul>` : ""}
        </div>
      `).join("");
    },
    async listQuizzes() {
      const out = $("#qmResults");
      out.innerHTML = '<p class="empty">Loading…</p>';
      const r = await api("/api/quizzes/quizzes?limit=30");
      if (!r.success) { out.innerHTML = `<div class="status-block">${escape(r.error)}</div>`; return; }
      $("#qmCount").textContent = `${r.total} quizzes total — showing ${r.data.length}`;
      out.innerHTML = `<div class="table-container"><table class="data-table">
        <thead><tr><th>Title</th><th>Grade</th><th>Subject</th><th># Questions</th><th>Quiz ID</th></tr></thead>
        <tbody>${r.data.map(q => `<tr>
          <td>${escape(q.title || "—")}</td>
          <td>${escape(q.grade || "—")}</td>
          <td>${escape(q.subject || "—")}</td>
          <td>${q.total_questions ?? "—"}</td>
          <td><code>${escape(q.quiz_id)}</code></td>
        </tr>`).join("")}</tbody></table></div>`;
    },
  };

  // ── PIPELINE ──────────────────────────────────────────────────────────
  const pipeline = {
    init() {
      $("#pipelinePingBtn").addEventListener("click", () => this.probeUser());
    },
    async onShow() { this.probe(); },
    async probe() {
      const out = $("#pipelineStatus");
      out.textContent = "Checking…";
      const ping = await api("/api/pipeline/ping");
      const status = await api("/api/pipeline/status");
      const lines = [
        `Backend env var: ${ping.backend || "(not set)"}`,
        status.configured
          ? (status.success ? `Upstream OK (HTTP ${status.upstream_status})` : `Upstream error: ${status.error}`)
          : `Hint: ${status.hint || "not configured"}`,
      ];
      out.textContent = lines.join("\n");
    },
    async probeUser() {
      const url = $("#pipelineUrl").value.trim();
      if (!url) { toast("Enter a URL", "err"); return; }
      toast("Note: env var PIPELINE_BACKEND not changed (read-only)");
      // Best we can do for now: try a direct fetch to confirm reachability.
      try {
        const r = await fetch(url, { mode: "no-cors" });
        toast("Sent a no-cors probe — see browser network tab", "ok");
      } catch (e) {
        toast(`Unreachable: ${e.message}`, "err");
      }
    },
  };

  // ── SYNC ──────────────────────────────────────────────────────────────
  const sync = {
    init() {
      $("#syncRunBtn").addEventListener("click", () => this.run());
      $("#syncProbeBtn").addEventListener("click", () => this.probe());
    },
    onShow() { this.probe(); },
    async probe() {
      $("#syncStatus").textContent = "Checking…";
      const r = await api("/api/sync/status");
      $("#syncStatus").textContent = r.success
        ? "Firebase reachable ✓"
        : `Error: ${r.error}`;
    },
    async run() {
      if (!confirm("Run Firestore sync now? This pulls users + attendance.")) return;
      $("#syncOutput").textContent = "Syncing…";
      $("#syncRunBtn").disabled = true;
      const r = await api("/api/sync/all", { method: "POST" });
      $("#syncRunBtn").disabled = false;
      $("#syncOutput").textContent = JSON.stringify(r, null, 2);
      toast(r.success ? "Sync done" : "Sync failed", r.success ? "ok" : "err");
    },
  };

  // ── AUTOMATION ────────────────────────────────────────────────────────
  const automation = {
    init() {
      $("#autoStartBtn").addEventListener("click", async () => {
        const r = await api("/api/automation/start", { method: "POST" });
        toast(r.message || r.error, r.success ? "ok" : "err");
        this.refresh();
      });
      $("#autoStopBtn").addEventListener("click", async () => {
        if (!confirm("Stop all automation processes?")) return;
        const r = await api("/api/automation/stop", { method: "POST" });
        toast(r.message || r.error, r.success ? "ok" : "err");
        this.refresh();
      });
      $("#autoAutopilotBtn").addEventListener("click", async () => {
        const r = await api("/api/automation/autopilot", { method: "POST" });
        toast(r.message || r.error, r.success ? "ok" : "err");
        this.refresh();
      });
    },
    onShow() { this.refresh(); },
    async refresh() {
      const r = await api("/api/automation/status");
      if (!r.success) return;
      $("#autoBrowserBadge").textContent = r.browser_running ? "running" : "stopped";
      $("#autoBrowserBadge").className = "status-badge " + (r.browser_running ? "ok" : "inactive");
      $("#autoAutopilotBadge").textContent = r.autopilot_running ? "running" : "idle";
      $("#autoAutopilotBadge").className = "status-badge " + (r.autopilot_running ? "ok" : "inactive");
    },
  };

  // ── FINANCE ───────────────────────────────────────────────────────────
  const finance = {
    _authKey: "finance_auth",
    _authHeader() {
      return "Basic " + btoa(sessionStorage.getItem("finance_user") + ":" + sessionStorage.getItem("finance_pass"));
    },
    _clearAuth() {
      sessionStorage.removeItem("finance_user");
      sessionStorage.removeItem("finance_pass");
    },
    _isAuthed() {
      return !!(sessionStorage.getItem("finance_user") && sessionStorage.getItem("finance_pass"));
    },
    init() {
      $("#finance-connect-btn").addEventListener("click", () => this.connect());
      $("#finance-user").addEventListener("keyup", (e) => { if (e.key === "Enter") this.connect(); });
      $("#finance-pass").addEventListener("keyup", (e) => { if (e.key === "Enter") this.connect(); });
      $("#fin-search-btn").addEventListener("click", () => this.loadReport());
      $("#fin-logout-btn").addEventListener("click", () => this.logout());
    },
    onShow() {
      if (this._isAuthed()) {
        this._showDashboard();
        this.loadSummary();
      } else {
        this._showAuth();
      }
    },
    _showAuth() {
      $("#finance-auth").style.display = "block";
      $("#finance-dashboard").style.display = "none";
      $("#finance-auth-error").style.display = "none";
    },
    _showDashboard() {
      $("#finance-auth").style.display = "none";
      $("#finance-dashboard").style.display = "block";
    },
    connect() {
      const user = $("#finance-user").value.trim();
      const pass = $("#finance-pass").value;
      if (!user || !pass) {
        $("#finance-auth-error").textContent = "Please enter username and password.";
        $("#finance-auth-error").style.display = "block";
        return;
      }
      sessionStorage.setItem("finance_user", user);
      sessionStorage.setItem("finance_pass", pass);
      this._showDashboard();
      this.loadSummary();
    },
    logout() {
      this._clearAuth();
      this._showAuth();
      $("#finance-user").value = "";
      $("#finance-pass").value = "";
    },
    async _api(path, opts = {}) {
      const key = sessionStorage.getItem("finance_auth_key");
      try {
        const r = await fetch(path, {
          ...opts,
          headers: {
            ...(opts.headers || {}),
            "Authorization": this._authHeader(),
          },
        });
        if (r.status === 401) {
          this._clearAuth();
          this._showAuth();
          toast("Finance auth failed — please re-enter credentials", "err");
          return { success: false, error: "Unauthorized" };
        }
        const json = await r.json();
        return json;
      } catch (e) {
        return { success: false, error: e.message };
      }
    },
    async loadSummary() {
      const r = await this._api("/finance/summary");
      if (!r.success) return;
      const d = r.data || r;
      $("#fin-income").textContent = this._fmt(d.total_income);
      $("#fin-expense").textContent = this._fmt(d.total_expense);
      const income = parseFloat(d.total_income) || 0;
      const expense = parseFloat(d.total_expense) || 0;
      $("#fin-balance").textContent = this._fmt(income - expense);
      $("#fin-count").textContent = d.transaction_count ?? "–";
    },
    async loadReport() {
      const start = $("#fin-start").value;
      const end = $("#fin-end").value;
      const qs = new URLSearchParams();
      if (start) qs.set("start_date", start);
      if (end) qs.set("end_date", end);
      const tbody = $("#fin-table-body");
      tbody.innerHTML = `<tr><td colspan="6" class="empty">Loading…</td></tr>`;
      const r = await this._api(`/finance/report?${qs}`);
      if (!r.success) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">Error: ${escape(r.error)}</td></tr>`;
        return;
      }
      const data = r.data || r.report || [];
      if (!data.length) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">No transactions found.</td></tr>`;
        return;
      }
      tbody.innerHTML = data.map(tx => `
        <tr>
          <td>${escape(tx.date || tx.transaction_date || "—")}</td>
          <td>${escape(tx.category || "—")}</td>
          <td><span class="status-badge ${(tx.type || "").toLowerCase() === "income" ? "ok" : ""}">${escape(tx.type || "—")}</span></td>
          <td style="color:${(tx.type || "").toLowerCase() === "income" ? "#4CAF50" : "#F44336"};font-weight:bold">${this._fmt(tx.amount)}</td>
          <td>${escape(tx.description || "—")}</td>
          <td><code>${escape(tx.reference || "—")}</code></td>
        </tr>
      `).join("");
    },
    _fmt(v) {
      const n = parseFloat(v);
      if (isNaN(n)) return "–";
      return new Intl.NumberFormat("en-MY", { style: "currency", currency: "MYR" }).format(n);
    },
  };

  // ── REGISTRY + BOOT ───────────────────────────────────────────────────
  const MODULES = {
    dashboard, users, curriculum, attendance, student, rag,
    quizzes: quizManager, pipeline, sync, automation, finance,
  };

  function bindSidebar() {
    $$("#sidebar-menu li").forEach(li => {
      li.addEventListener("click", (e) => {
        e.preventDefault();
        location.hash = "#" + li.dataset.view;
      });
    });
  }

  async function checkApiStatus() {
    const r = await api("/api/ping");
    const badge = $("#apiStatus");
    if (r.success) {
      badge.textContent = `${r.blueprints.length} blueprints up`;
      badge.classList.add("ok");
    } else {
      badge.textContent = "API offline";
      badge.classList.add("err");
    }
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindSidebar();
    Object.values(MODULES).forEach(m => m.init && m.init());
    window.addEventListener("hashchange", handleHashChange);
    $("#refreshBtn").addEventListener("click", async () => {
      const btn = $("#refreshBtn");
      const orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Updating…`;
      try {
        const r = await api("/api/sync/all", { method: "POST" });
        if (r.success) {
          toast(r.message || "Update complete", "ok");
          // Refresh current view
          const view = (location.hash || "#dashboard").slice(1);
          if (MODULES[view] && MODULES[view].onShow) MODULES[view].onShow();
        } else {
          toast("Update failed: " + (r.error || "?"), "err");
        }
      } catch(e) {
        toast("Update error: " + e.message, "err");
      } finally {
        btn.disabled = false;
        btn.innerHTML = orig;
      }
    });
    checkApiStatus();
    handleHashChange(); // initial view
  });
})();
