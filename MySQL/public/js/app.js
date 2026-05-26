/**
 * RAG Database Web UI - Main Application
 */

// API Base URL
const API_BASE_URL = '/api';

// App State
const state = {
  currentPage: 'dashboard',
  questions: [],
  filteredQuestions: [],
  selectedQuestions: new Set(),
  myQuizzes: [],
  currentQuiz: null,
  pagination: {
    page: 1,
    limit: 20,
    total: 0
  },
  stats: {
    totalQuestions: 0,
    totalQuizzes: 0,
    topics: {},
    grades: {}
  }
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  setupNavigation();
  setupEventListeners();
  await loadStats();
  await loadQuestions();
  renderDashboard();
}

// Navigation
function setupNavigation() {
  const navItems = document.querySelectorAll('.nav-item');

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      const page = item.dataset.page;
      navigateToPage(page);
    });
  });
}

function navigateToPage(page) {
  // Update state
  state.currentPage = page;

  // Update navigation
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.remove('active');
    if (item.dataset.page === page) {
      item.classList.add('active');
    }
  });

  // Update page title
  const pageTitles = {
    dashboard: 'Dashboard',
    search: 'Search & Filter',
    editor: 'Question Editor',
    assembler: 'Quiz Assembler',
    quizzes: 'My Quizzes'
  };
  document.getElementById('pageTitle').textContent = pageTitles[page] || 'Dashboard';

  // Show page
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`${page}-page`).classList.add('active');

  // Page-specific initialization
  if (page === 'search') {
    renderSearchResults();
  } else if (page === 'editor') {
    initEditor();
  } else if (page === 'assembler') {
    initAssembler();
  } else if (page === 'quizzes') {
    renderMyQuizzes();
  }
}

// Event Listeners
function setupEventListeners() {
  // Menu toggle (mobile)
  document.getElementById('menuToggle')?.addEventListener('click', () => {
    document.querySelector('.sidebar').classList.toggle('open');
  });

  // Create quiz button
  document.getElementById('createQuizBtn')?.addEventListener('click', () => {
    navigateToPage('assembler');
  });

  // Search & Filter
  document.getElementById('applyFilters')?.addEventListener('click', applyFilters);
  document.getElementById('clearFilters')?.addEventListener('click', clearFilters);

  // Select all results
  document.getElementById('selectAllResults')?.addEventListener('click', toggleSelectAll);

  // Add to quiz
  document.getElementById('addToQuiz')?.addEventListener('click', addSelectedToQuiz);

  // Editor
  document.getElementById('editor-cancel')?.addEventListener('click', () => {
    showToast('Changes discarded', 'info');
  });

  document.getElementById('editor-save')?.addEventListener('click', saveQuestionChanges);

  // Assembler
  document.getElementById('previewQuizBtn')?.addEventListener('click', previewQuiz);
  document.getElementById('shuffleQuestions')?.addEventListener('click', shuffleQuizQuestions);
  document.getElementById('saveQuizBtn')?.addEventListener('click', () => {
    openModal('saveQuizModal');
  });

  // Save Quiz Modal
  document.getElementById('cancelSaveQuiz')?.addEventListener('click', () => {
    closeModal('saveQuizModal');
  });

  document.getElementById('confirmSaveQuiz')?.addEventListener('click', confirmSaveQuiz);

  // Question Modal
  document.getElementById('closeQuestionModal')?.addEventListener('click', () => {
    closeModal('questionModal');
  });

  document.getElementById('editQuestionBtn')?.addEventListener('click', () => {
    closeModal('questionModal');
    navigateToPage('editor');
  });

  // Close modals on outside click
  document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Close modals on X button
  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('.modal').classList.remove('active');
    });
  });
}

// API Functions
async function fetchData(endpoint, query = {}) {
  try {
    const queryString = new URLSearchParams(query).toString();
    const url = `${API_BASE_URL}${endpoint}${queryString ? '?' + queryString : ''}`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Network response was not ok');
    return await response.ok ? response.json() : null;
  } catch (error) {
    console.error('Fetch error:', error);
    showToast('Error loading data', 'error');
    return null;
  }
}

// UI Functions
function renderDashboard() {
  // Update stats
  document.getElementById('total-questions').textContent = state.stats.totalQuestions.toLocaleString();
  document.getElementById('total-questions-mini').textContent = state.stats.totalQuestions.toLocaleString();
  document.getElementById('total-quizzes').textContent = state.stats.totalQuizzes.toLocaleString();

  // Render topic chart
  renderTopicChart();

  // Render grade chart
  renderGradeChart();

  // Render recent quizzes
  renderRecentQuizzes();
}

function renderTopicChart() {
  const container = document.getElementById('topic-chart');
  const topics = state.stats.topics || {};

  const sortedTopics = Object.entries(topics)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);

  const max = Math.max(...sortedTopics.map(t => t[1]));

  container.innerHTML = `
    <div class="chart-bars">
      ${sortedTopics.map(([topic, count]) => `
        <div class="chart-bar-row">
          <span class="chart-label">${topic}</span>
          <div class="chart-bar-wrapper">
            <div class="chart-bar" style="width: ${(count / max) * 100}%; background: linear-gradient(90deg, var(--primary), var(--primary-light));"></div>
          </div>
          <span class="chart-value">${count.toLocaleString()}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function renderGradeChart() {
  const container = document.getElementById('grade-chart');
  const grades = state.stats.grades || {};

  const max = Math.max(...Object.values(grades), 1);

  container.innerHTML = `
    <div class="chart-pills">
      ${Object.entries(grades).map(([grade, count]) => `
        <div class="grade-pill" onclick="filterByGrade('${grade}')" style="cursor: pointer;" title="Click to view Grade ${grade} questions">
          <span class="grade-name">Grade ${grade}</span>
          <div class="grade-bar-wrapper">
            <div class="grade-bar" style="width: ${(count / max) * 100}%"></div>
          </div>
          <span class="grade-count">${count.toLocaleString()}</span>
        </div>
      `).join('')}
    </div>
  `;
}

async function filterByGrade(grade) {
  // Update UI to search page
  navigateToPage('search');
  
  // Set filter value
  const filterGrade = document.getElementById('filter-grade');
  if (filterGrade) {
    // Clear previous selections
    Array.from(filterGrade.options).forEach(opt => opt.selected = false);
    // Select specific grade
    const option = Array.from(filterGrade.options).find(opt => opt.value === grade);
    if (option) option.selected = true;
  }
  
  // Reset pagination
  state.pagination.page = 1;
  
  // Load questions for this grade
  await loadQuestions({ grade });
  renderSearchResults();
}

async function changeLimit(limit) {
  state.pagination.limit = parseInt(limit);
  state.pagination.page = 1;
  await loadQuestions();
  renderSearchResults();
}

async function changePage(page) {
  state.pagination.page = page;
  await loadQuestions();
  renderSearchResults();
}

function renderRecentQuizzes() {
  const container = document.getElementById('recent-quizzes-list');

  // Mock recent quizzes
  const recentQuizzes = [
    { name: 'Grade 6 Geometry Practice', grade: '6', topic: 'Geometri', count: 20, created: '2026-01-07' },
    { name: 'Algebra Basics', grade: '7', topic: 'Aljabar', count: 15, created: '2026-01-06' },
    { name: 'Statistics Quiz', grade: '5', topic: 'Statistika', count: 25, created: '2026-01-05' }
  ];

  container.innerHTML = recentQuizzes.map(quiz => `
    <div class="quiz-item">
      <div class="quiz-info">
        <h4>${quiz.name}</h4>
        <div class="quiz-meta">
          <span><i class="fas fa-graduation-cap"></i> Grade ${quiz.grade}</span>
          <span><i class="fas fa-tag"></i> ${quiz.topic}</span>
          <span><i class="fas fa-question-circle"></i> ${quiz.count} questions</span>
          <span><i class="fas fa-calendar"></i> ${quiz.created}</span>
        </div>
      </div>
      <div class="quiz-actions">
        <button class="btn-icon" title="Edit"><i class="fas fa-edit"></i></button>
        <button class="btn-icon" title="Export"><i class="fas fa-download"></i></button>
        <button class="btn-icon" title="Delete"><i class="fas fa-trash"></i></button>
      </div>
    </div>
  `).join('');
}

function renderSearchResults() {
  const container = document.getElementById('search-results');
  const countEl = document.getElementById('results-count');

  const questions = state.filteredQuestions.length > 0
    ? state.filteredQuestions
    : state.questions;

  countEl.textContent = `(${questions.length})`;

  if (questions.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-search"></i>
        <p>No questions found. Try adjusting your filters.</p>
      </div>
    `;
    return;
  }

  // Data is already paginated from server
  const paginated = questions;

  if (paginated.length === 0) {
    console.log('No questions to display');
  }

  container.innerHTML = paginated.map((q, idx) => {
    const isSelected = state.selectedQuestions.has(q.id);
    return `
    <div class="question-item ${isSelected ? 'selected' : ''}" 
         data-id="${q.id}" 
         onclick="toggleQuestionSelection('${q.id}')">
      <div class="question-checkbox-wrapper">
        <input type="checkbox" class="question-checkbox"
               data-id="${q.id}"
               ${isSelected ? 'checked' : ''}
               onclick="event.stopPropagation(); toggleQuestionSelection('${q.id}')">
      </div>
      <div class="question-content">
        <div class="question-text">${q.id_q || q.en_q}</div>
        <div class="question-meta">
          <span class="badge badge-grade"><i class="fas fa-graduation-cap"></i> Grade ${q.grade}</span>
          <span class="badge badge-topic"><i class="fas fa-tag"></i> ${q.topic}</span>
          <span class="badge badge-difficulty-${q.difficulty}"><i class="fas fa-signal"></i> ${q.difficulty}</span>
          ${q.hasImage ? '<span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #a78bfa;"><i class="fas fa-image"></i> Image</span>' : ''}
        </div>
      </div>
      <div class="question-actions">
        <button class="btn-icon" title="View" onclick="event.stopPropagation(); viewQuestion('${q.id}')">
          <i class="fas fa-eye"></i>
        </button>
        <button class="btn-icon" title="Edit" onclick="event.stopPropagation(); editQuestion('${q.id}')">
          <i class="fas fa-edit"></i>
        </button>
      </div>
    </div>
  `;}).join('');

  renderPagination(state.pagination.total);
}

function renderPagination(total) {
  const container = document.getElementById('pagination');
  const { page, limit } = state.pagination;
  const totalPages = state.pagination.totalPages || Math.ceil(total / limit);

  if (totalPages <= 1) {
    container.innerHTML = '';
    return;
  }

  let html = `
    <button ${page === 1 ? 'disabled' : ''} onclick="changePage(${page - 1})">
      <i class="fas fa-chevron-left"></i>
    </button>
  `;

  for (let i = 1; i <= totalPages; i++) {
    if (i === 1 || i === totalPages || (i >= page - 1 && i <= page + 1)) {
      html += `<button class="${i === page ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    } else if (i === page - 2 || i === page + 2) {
      html += `<span>...</span>`;
    }
  }

  html += `
    <button ${page === totalPages ? 'disabled' : ''} onclick="changePage(${page + 1})">
      <i class="fas fa-chevron-right"></i>
    </button>
  `;

  container.innerHTML = html;
}

// Data Loading
async function loadStats() {
  const data = await fetchData('/stats');
  if (data) {
    state.stats = {
      totalQuestions: data.totalQuestions || 0,
      totalQuizzes: data.totalQuizzes || 0,
      grades: data.grades || {},
      topics: data.topics || {}
    };
  }
}

async function loadQuestions(extraFilters = {}) {
  const { page, limit } = state.pagination;
  
  // Get filter values from UI
  const filters = {
    page,
    limit,
    ...extraFilters
  };
  
  // Always include UI filters unless explicitly overridden
  const gradeSelect = document.getElementById('filter-grade');
  const topicSelect = document.getElementById('filter-topic');
  const difficultySelect = document.getElementById('filter-difficulty');
  const hasImageSelect = document.getElementById('filter-hasImage');

  if (gradeSelect && !filters.grade) {
    const val = Array.from(gradeSelect.selectedOptions).map(opt => opt.value);
    if (val.length > 0) filters.grade = val[0];
  }
  
  if (topicSelect && !filters.topic) {
    const val = Array.from(topicSelect.selectedOptions).map(opt => opt.value);
    if (val.length > 0) filters.topic = val[0];
  }

  if (difficultySelect && difficultySelect.value && !filters.difficulty) {
    filters.difficulty = difficultySelect.value;
  }

  if (hasImageSelect && hasImageSelect.value && !filters.hasImage) {
    filters.hasImage = hasImageSelect.value;
  }

  const data = await fetchData('/questions', filters);
  if (data && data.questions) {
    state.questions = data.questions;
    state.filteredQuestions = data.questions;
    state.pagination.total = data.pagination.total;
    state.pagination.totalPages = data.pagination.totalPages;
  }
}

// Filter Functions
async function applyFilters() {
  state.pagination.page = 1;
  await loadQuestions();
  renderSearchResults();
  showToast(`Filters applied`, 'success');
}

function clearFilters() {
  document.getElementById('filter-grade').value = '';
  document.getElementById('filter-topic').value = '';
  document.getElementById('filter-difficulty').value = '';
  document.getElementById('filter-hasImage').value = '';

  state.filteredQuestions = [...state.questions];
  state.pagination.page = 1;
  renderSearchResults();
}

// Question Selection
function toggleQuestionSelection(id) {
  if (state.selectedQuestions.has(id)) {
    state.selectedQuestions.delete(id);
  } else {
    state.selectedQuestions.add(id);
  }
  updateBulkEditVisibility();
  renderSearchResults();
  
  // Update checkbox state immediately without re-rendering
  const checkbox = document.querySelector(`.question-item[data-id="${id}"] .question-checkbox`);
  if (checkbox) {
    checkbox.checked = state.selectedQuestions.has(id);
  }
}

// Debug: Verify functions are exposed
console.log('Functions loaded:', { 
  viewQuestion: typeof viewQuestion, 
  editQuestion: typeof editQuestion,
  toggleQuestionSelection: typeof toggleQuestionSelection
});

function toggleSelectAll() {
  const allIds = state.questions.map(q => q.id);
  const allOnPageSelected = allIds.every(id => state.selectedQuestions.has(id));

  if (allOnPageSelected) {
    allIds.forEach(id => state.selectedQuestions.delete(id));
  } else {
    allIds.forEach(id => state.selectedQuestions.add(id));
  }

  updateBulkEditVisibility();
  renderSearchResults();
  showToast(allOnPageSelected ? 'Selection cleared' : `${state.selectedQuestions.size} questions selected`, 'info');
}

function clearSelection() {
  state.selectedQuestions.clear();
  updateBulkEditVisibility();
  renderSearchResults();
  showToast('Selection cleared', 'info');
}

function updateBulkEditVisibility() {
  const count = state.selectedQuestions.size;
  const bulkUi = document.getElementById('bulk-edit-ui');
  const clearBtn = document.getElementById('clearSelection');
  const selectBtn = document.getElementById('selectAllResults');
  
  if (bulkUi) bulkUi.style.display = count > 0 ? 'flex' : 'none';
  if (clearBtn) clearBtn.style.display = count > 0 ? 'inline-flex' : 'none';
  
  if (selectBtn) {
    const allIds = state.questions.map(q => q.id);
    const allOnPageSelected = allIds.length > 0 && allIds.every(id => state.selectedQuestions.has(id));
    selectBtn.innerHTML = allOnPageSelected 
      ? '<i class="fas fa-minus-square"></i> Deselect Page' 
      : '<i class="fas fa-check-square"></i> Select Page';
  }
}

async function bulkUpdateTopic() {
  const topic = document.getElementById('bulk-topic').value;
  if (!topic) {
    showToast('Please select a topic', 'warning');
    return;
  }
  
  const ids = Array.from(state.selectedQuestions);
  if (ids.length === 0) return;
  
  if (!confirm(`Update topic to "${topic}" for ${ids.length} selected questions?`)) return;
  
  try {
    const response = await fetch(`${API_BASE_URL}/questions/update-topic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids, topic })
    });
    
    const result = await response.json();
    if (result.success) {
      showToast(result.message, 'success');
      state.selectedQuestions.clear();
      document.getElementById('bulk-edit-ui').style.display = 'none';
      await loadQuestions();
      renderSearchResults();
    } else {
      showToast(result.error || 'Failed to update topics', 'error');
    }
  } catch (error) {
    showToast('Network error', 'error');
  }
}

function addSelectedToQuiz() {
  if (state.selectedQuestions.size === 0) {
    showToast('Please select at least one question', 'warning');
    return;
  }

  navigateToPage('assembler');
  showToast(`${state.selectedQuestions.size} questions added to quiz`, 'success');
}

// Question Actions
function viewQuestion(id) {
  console.log('=== VIEW QUESTION DEBUG ===');
  console.log('Input id:', id, 'type:', typeof id);
  console.log('State questions count:', state.questions.length);
  console.log('First 5 IDs:', state.questions.slice(0, 5).map(q => ({id: q.id, type: typeof q.id})));
  
  const question = state.questions.find(q => String(q.id) === String(id));
  if (!question) {
    showToast('Question not found', 'error');
    return;
  }

  const modalBody = document.getElementById('questionModalBody');
  if (!modalBody) {
    console.error('Modal body not found');
    showToast('View modal not available', 'error');
    return;
  }
  modalBody.innerHTML = `
    <div class="question-detail">
      <h4>Question (Indonesian)</h4>
      <div class="question-text-box">
        <p>${question.id_q}</p>
      </div>

      <h4>Question (English)</h4>
      <div class="question-text-box">
        <p>${question.en_q}</p>
      </div>

      <h4>Options</h4>
      <div class="options-list">
        ${question.options.map((opt, idx) => `
          <div class="option-item ${idx === question.correctAnswerIndex ? 'correct' : ''}">
            <span class="option-label">${String.fromCharCode(65 + idx)}</span>
            <span>${opt}</span>
            ${idx === question.correctAnswerIndex ? '<i class="fas fa-check" style="color: var(--secondary); margin-left: auto;"></i>' : ''}
          </div>
        `).join('')}
      </div>

      <h4>Explanation (Indonesian)</h4>
      <div class="question-text-box">
        <p>${question.id_exp}</p>
      </div>

      <h4>Explanation (English)</h4>
      <div class="question-text-box">
        <p>${question.en_exp}</p>
      </div>

      <h4>Metadata</h4>
      <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem; font-size: 0.875rem;">
        <div><strong>Grade:</strong> ${question.grade}</div>
        <div><strong>Topic:</strong> ${question.topic}</div>
        <div><strong>Difficulty:</strong> ${question.difficulty}</div>
        <div><strong>Has Image:</strong> ${question.hasImage ? 'Yes' : 'No'}</div>
        <div><strong>Quiz:</strong> ${question.quizTitle}</div>
        <div><strong>Creator:</strong> ${question.creator}</div>
      </div>
    </div>
  `;

  openModal('questionModal');
}

function editQuestion(id) {
  console.log('=== EDIT QUESTION DEBUG ===');
  console.log('Input id:', id, 'type:', typeof id);
  console.log('State questions count:', state.questions.length);
  
  const question = state.questions.find(q => String(q.id) === String(id));
  if (!question) {
    showToast('Question not found', 'error');
    return;
  }

  const editorPage = document.getElementById('editor-page');
  if (!editorPage) {
    console.error('Editor page not found');
    showToast('Editor page not available', 'error');
    return;
  }

  // Populate form
  document.getElementById('edit-id').value = question.id;
  document.getElementById('edit-quizTitle').value = question.quizTitle;
  document.getElementById('edit-grade').value = question.grade;
  document.getElementById('edit-topic').value = question.topic;
  document.getElementById('edit-difficulty').value = question.difficulty;
  document.getElementById('edit-id_q').value = question.id_q;
  document.getElementById('edit-en_q').value = question.en_q;
  document.getElementById('edit-options').value = question.options.join('\n');
  document.getElementById('edit-correctAnswerIndex').value = question.correctAnswerIndex;
  document.getElementById('edit-hasImage').checked = question.hasImage;
  document.getElementById('edit-id_exp').value = question.id_exp;
  document.getElementById('edit-en_exp').value = question.en_exp;

  navigateToPage('editor');
}

async function saveQuestionChanges() {
  const id = document.getElementById('edit-id').value;
  const topic = document.getElementById('edit-topic').value;

  if (!id || !topic) {
    showToast('Missing required fields', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/questions/update-topic`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [id], topic })
    });
    
    const result = await response.json();
    if (result.success) {
      showToast('Question updated successfully', 'success');
      await loadQuestions();
      renderSearchResults();
    } else {
      showToast(result.error || 'Failed to update question', 'error');
    }
  } catch (error) {
    showToast('Network error', 'error');
  }
}

async function activateSQL() {
  showToast('Checking SQL Connection...', 'info');
  const data = await fetchData('/stats');
  if (data && data.totalQuestions !== undefined) {
    showToast(`SQL Active. Total questions: ${data.totalQuestions}`, 'success');
    renderDashboard();
  } else {
    showToast('Failed to connect to SQL', 'error');
  }
}

async function syncWithFirebase() {
  if (!confirm('Start synchronization with Firebase? This may take a few minutes.')) return;
  
  showToast('Starting synchronization...', 'info');
  const data = await fetchData('/sync');
  
  if (data && data.status === 'started') {
    showToast('Sync in progress in background. Refresh in a few minutes.', 'success');
  } else {
    showToast('Failed to start synchronization', 'error');
  }
}

// Editor Functions
function initEditor() {
  // Populate question list
  const listContainer = document.getElementById('editor-question-list');

  listContainer.innerHTML = state.questions.slice(0, 20).map(q => `
    <div class="editor-list-item" data-id="${q.id}" onclick="loadQuestionToEditor('${q.id}')">
      <div class="q-preview">${q.id_q || q.en_q}</div>
      <div class="q-meta">
        <span>Grade ${q.grade}</span>
        <span>${q.topic}</span>
      </div>
    </div>
  `).join('');

  // Load first question
  if (state.questions.length > 0) {
    loadQuestionToEditor(state.questions[0].id);
  }
}

function loadQuestionToEditor(id) {
  // Update active state in list
  document.querySelectorAll('.editor-list-item').forEach(item => {
    item.classList.toggle('active', item.dataset.id === id);
  });

  editQuestion(id);
}

// Assembler Functions
function initAssembler() {
  // Set default name
  const nameInput = document.getElementById('asm-name');
  if (!nameInput.value) {
    nameInput.value = generateQuizName();
  }

  // If questions are selected, show them in preview
  if (state.selectedQuestions.size > 0) {
    const selected = state.questions.filter(q => state.selectedQuestions.has(q.id));
    renderAssemblerPreview(selected);
  }
}

function generateQuizName() {
  const grade = document.getElementById('asm-grade')?.value || '6';
  const topic = document.getElementById('asm-topic')?.value || 'Mixed';
  return `Grade ${grade} ${topic} Quiz`;
}

async function previewQuiz() {
  const grade = document.getElementById('asm-grade').value;
  const topic = document.getElementById('asm-topic').value;
  const difficulty = document.getElementById('asm-difficulty').value;
  const count = parseInt(document.getElementById('asm-count').value);

  // Filter questions
  let filtered = state.questions.filter(q => {
    if (grade && q.grade !== grade) return false;
    if (topic && !topic.includes(q.topic)) return false;
    if (difficulty && q.difficulty !== difficulty) return false;
    return true;
  });

  // Shuffle and select
  filtered = filtered.sort(() => Math.random() - 0.5).slice(0, count);

  state.currentQuiz = {
    name: document.getElementById('asm-name').value || generateQuizName(),
    questions: filtered
  };

  renderAssemblerPreview(filtered);
  document.getElementById('assembler-actions').style.display = 'flex';

  showToast(`Found ${filtered.length} matching questions`, 'success');
}

function renderAssemblerPreview(questions) {
  const container = document.getElementById('assembler-preview-list');
  const countEl = document.getElementById('preview-count');

  countEl.textContent = `(${questions.length} questions)`;

  if (questions.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <i class="fas fa-clipboard-list"></i>
        <p>Click "Preview Questions" to see matching questions</p>
      </div>
    `;
    return;
  }

  container.innerHTML = questions.map((q, idx) => `
    <div class="preview-item" data-id="${q.id}">
      <span class="preview-number">${idx + 1}</span>
      <span class="preview-text">${q.id_q || q.en_q}</span>
      <button class="preview-remove" onclick="removeFromQuiz('${q.id}')">
        <i class="fas fa-times"></i>
      </button>
    </div>
  `).join('');
}

function shuffleQuizQuestions() {
  if (!state.currentQuiz) return;

  state.currentQuiz.questions = state.currentQuiz.questions.sort(() => Math.random() - 0.5);
  renderAssemblerPreview(state.currentQuiz.questions);
  showToast('Questions shuffled', 'info');
}

function removeFromQuiz(id) {
  if (!state.currentQuiz) return;

  state.currentQuiz.questions = state.currentQuiz.questions.filter(q => q.id !== id);
  renderAssemblerPreview(state.currentQuiz.questions);
}

function confirmSaveQuiz() {
  const name = document.getElementById('final-quiz-name').value;
  const description = document.getElementById('final-quiz-description').value;

  if (!name) {
    showToast('Please enter a quiz name', 'error');
    return;
  }

  if (!state.currentQuiz || state.currentQuiz.questions.length === 0) {
    showToast('No questions to save', 'error');
    return;
  }

  const quiz = {
    id: `quiz-${Date.now()}`,
    name,
    description,
    createdAt: new Date().toISOString(),
    questionCount: state.currentQuiz.questions.length,
    questions: state.currentQuiz.questions.map(q => ({
      questionId: q.id,
      quizId: q.quizId,
      quizTitle: q.quizTitle,
      grade: q.grade,
      topic: q.topic,
      difficulty: q.difficulty,
      hasImage: q.hasImage
    }))
  };

  state.myQuizzes.push(quiz);

  closeModal('saveQuizModal');
  showToast('Quiz saved successfully!', 'success');

  // Clear current quiz
  state.currentQuiz = null;
  document.getElementById('assembler-actions').style.display = 'none';
  document.getElementById('assembler-preview-list').innerHTML = `
    <div class="empty-state">
      <i class="fas fa-clipboard-list"></i>
      <p>Click "Preview Questions" to see matching questions</p>
    </div>
  `;
}

function renderMyQuizzes() {
  const container = document.getElementById('quizzes-grid');

  if (state.myQuizzes.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1/-1;">
        <i class="fas fa-clipboard-list"></i>
        <p>No quizzes yet. Create your first quiz using the Quiz Assembler!</p>
        <button class="btn btn-primary" onclick="navigateToPage('assembler')">
          <i class="fas fa-plus"></i> Create Quiz
        </button>
      </div>
    `;
    return;
  }

  container.innerHTML = state.myQuizzes.map(quiz => `
    <div class="quiz-card">
      <div class="quiz-card-header">
        <h4>${quiz.name}</h4>
        <span class="quiz-date">${new Date(quiz.createdAt).toLocaleDateString()}</span>
      </div>
      <div class="quiz-card-body">
        <p class="quiz-description">${quiz.description || 'No description'}</p>
        <div class="quiz-stats">
          <span><i class="fas fa-question-circle"></i> ${quiz.questionCount} questions</span>
        </div>
      </div>
      <div class="quiz-card-footer">
        <button class="btn btn-sm btn-primary" onclick="editQuiz('${quiz.id}')">
          <i class="fas fa-edit"></i> Edit
        </button>
        <button class="btn btn-sm btn-secondary" onclick="exportQuiz('${quiz.id}')">
          <i class="fas fa-download"></i> Export
        </button>
        <button class="btn btn-sm btn-danger" onclick="deleteQuiz('${quiz.id}')">
          <i class="fas fa-trash"></i>
        </button>
      </div>
    </div>
  `).join('');
}

// Utility Functions
function openModal(modalId) {
  document.getElementById(modalId).classList.add('active');
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icons = {
    success: 'check-circle',
    error: 'exclamation-circle',
    warning: 'exclamation-triangle',
    info: 'info-circle'
  };

  toast.innerHTML = `
    <i class="fas fa-${icons[type]}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function changePage(page) {
  state.pagination.page = page;
  renderSearchResults();
}

// Quiz Actions
function editQuiz(id) {
  const quiz = state.myQuizzes.find(q => q.id === id);
  if (!quiz) return;

  state.currentQuiz = {
    name: quiz.name,
    questions: quiz.questions.map(q => state.questions.find(qs => qs.id === q.questionId)).filter(Boolean)
  };

  // Populate assembler
  document.getElementById('asm-name').value = quiz.name;
  renderAssemblerPreview(state.currentQuiz.questions);
  document.getElementById('assembler-actions').style.display = 'flex';

  navigateToPage('assembler');
}

function exportQuiz(id) {
  const quiz = state.myQuizzes.find(q => q.id === id);
  if (!quiz) return;

  const dataStr = JSON.stringify(quiz, null, 2);
  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);

  const exportFileDefaultName = `${quiz.name.replace(/\s+/g, '_')}.json`;

  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', dataUri);
  linkElement.setAttribute('download', exportFileDefaultName);
  linkElement.click();

  showToast('Quiz exported successfully', 'success');
}

function deleteQuiz(id) {
  if (!confirm('Are you sure you want to delete this quiz?')) return;

  state.myQuizzes = state.myQuizzes.filter(q => q.id !== id);
  renderMyQuizzes();
  showToast('Quiz deleted', 'success');
}

// Make functions globally accessible
window.navigateToPage = navigateToPage;
window.viewQuestion = viewQuestion;
window.editQuestion = editQuestion;
window.toggleQuestionSelection = toggleQuestionSelection;
window.changePage = changePage;
window.removeFromQuiz = removeFromQuiz;
window.editQuiz = editQuiz;
window.exportQuiz = exportQuiz;
window.deleteQuiz = deleteQuiz;
window.loadQuestionToEditor = loadQuestionToEditor;
window.bulkUpdateTopic = bulkUpdateTopic;
window.applyFilters = applyFilters;
window.clearFilters = clearFilters;
window.toggleSelectAll = toggleSelectAll;
window.addSelectedToQuiz = addSelectedToQuiz;
window.changeLimit = changeLimit;
window.filterByGrade = filterByGrade;
window.clearSelection = clearSelection;
