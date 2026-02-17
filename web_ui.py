"""
Autonomous Coding Agent — Production Web UI
Premium dark-mode interface with real-time code streaming.
"""
from config import CODER_MODEL, REVIEWER_MODEL


def get_html():
    """Return the production HTML with config values injected."""
    return HTML_PAGE.replace("__CODER_MODEL__", CODER_MODEL).replace("__REVIEWER_MODEL__", REVIEWER_MODEL)


HTML_PAGE = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Autonomous Coding Agent</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --bg-0: #08090d;
  --bg-1: #0c0e14;
  --bg-2: #12151e;
  --bg-3: #181c28;
  --bg-4: #1e2333;
  --bg-hover: #252a3a;
  --border-1: #1e2333;
  --border-2: #2a3040;
  --border-active: #4c7bf5;
  --text-0: #f0f2f5;
  --text-1: #c8cdd8;
  --text-2: #8b92a8;
  --text-3: #5a6178;
  --accent: #4c7bf5;
  --accent-dim: rgba(76,123,245,0.12);
  --green: #2dd4a0;
  --green-dim: rgba(45,212,160,0.1);
  --red: #f5564c;
  --red-dim: rgba(245,86,76,0.1);
  --yellow: #f5c842;
  --yellow-dim: rgba(245,200,66,0.1);
  --purple: #a78bfa;
  --cyan: #22d3ee;
  --orange: #fb923c;
  --mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  --sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --radius: 10px;
  --radius-sm: 6px;
  --shadow: 0 4px 24px rgba(0,0,0,0.4);
}

* { margin:0; padding:0; box-sizing:border-box; }
html, body { height: 100%; overflow: hidden; }

body {
  font-family: var(--sans);
  background: var(--bg-0);
  color: var(--text-1);
}

/* ═══════ LAYOUT ═══════ */
.app {
  display: grid;
  grid-template-rows: 52px 1fr 32px;
  grid-template-columns: 280px 1fr 340px;
  grid-template-areas:
    "header header header"
    "sidebar main panel"
    "footer footer footer";
  height: 100vh;
}

/* ═══════ HEADER ═══════ */
.header {
  grid-area: header;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: var(--bg-1);
  border-bottom: 1px solid var(--border-1);
  z-index: 100;
}

.header-left { display: flex; align-items: center; gap: 14px; }

.logo {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-0);
  letter-spacing: -0.3px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon {
  width: 26px; height: 26px;
  background: linear-gradient(135deg, var(--accent), var(--purple));
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px;
}

.status-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 3px 10px 3px 8px;
  border-radius: 100px;
  font-size: 11px;
  font-weight: 600;
  font-family: var(--mono);
  letter-spacing: 0.3px;
  text-transform: uppercase;
}

.status-pill.idle { background: var(--bg-3); color: var(--text-3); }
.status-pill.running { background: var(--accent-dim); color: var(--accent); }
.status-pill.done { background: var(--green-dim); color: var(--green); }
.status-pill.error { background: var(--red-dim); color: var(--red); }

.status-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.status-pill.running .status-dot { animation: blink 1s ease infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

.header-center {
  display: flex; align-items: center; gap: 16px;
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-3);
}

.header-center .sep { color: var(--border-2); }

.header-right { display: flex; align-items: center; gap: 10px; }

.model-tag {
  font-size: 10px;
  font-family: var(--mono);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  background: var(--bg-3);
  color: var(--text-2);
  border: 1px solid var(--border-1);
}

/* ═══════ SIDEBAR ═══════ */
.sidebar {
  grid-area: sidebar;
  background: var(--bg-1);
  border-right: 1px solid var(--border-1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-section {
  padding: 14px 16px 8px;
  flex-shrink: 0;
}

.sidebar-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.2px;
  color: var(--text-3);
  margin-bottom: 10px;
}

.goal-input-wrap {
  position: relative;
}

.goal-input {
  width: 100%;
  min-height: 80px;
  max-height: 140px;
  background: var(--bg-0);
  border: 1px solid var(--border-2);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  color: var(--text-0);
  font-family: var(--mono);
  font-size: 12px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  transition: border-color .2s;
}

.goal-input:focus { border-color: var(--accent); }
.goal-input::placeholder { color: var(--text-3); }

.btn-row { display: flex; gap: 6px; margin-top: 8px; }

.btn {
  flex: 1;
  padding: 8px 0;
  border-radius: var(--radius-sm);
  font-family: var(--sans);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all .15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.btn-run {
  background: var(--accent);
  color: #fff;
}
.btn-run:hover { background: #5d88f7; }
.btn-run:disabled { opacity: .4; cursor: not-allowed; }

.btn-stop {
  background: var(--red-dim);
  color: var(--red);
  border: 1px solid rgba(245,86,76,.2);
  display: none;
}
.btn-stop:hover { background: rgba(245,86,76,.2); }

.divider {
  height: 1px;
  background: var(--border-1);
  margin: 4px 0;
}

/* File tree */
.file-tree {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.file-tree::-webkit-scrollbar { width: 4px; }
.file-tree::-webkit-scrollbar-thumb {
  background: var(--border-2);
  border-radius: 2px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  font-family: var(--mono);
  color: var(--text-2);
  cursor: pointer;
  transition: background .12s;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-item:hover { background: var(--bg-hover); color: var(--text-1); }
.file-item.active { background: var(--accent-dim); color: var(--accent); }
.file-icon { font-size: 13px; flex-shrink: 0; }

/* Activity feed */
.activity-section {
  flex-shrink: 0;
  max-height: 220px;
  overflow-y: auto;
  padding: 0 8px 12px;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 5px 8px;
  font-size: 11px;
  color: var(--text-2);
  border-radius: var(--radius-sm);
}

.activity-icon {
  flex-shrink: 0;
  width: 18px; height: 18px;
  border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px;
  margin-top: 1px;
}

.activity-icon.create { background: var(--green-dim); color: var(--green); }
.activity-icon.edit { background: var(--accent-dim); color: var(--accent); }
.activity-icon.cmd { background: var(--yellow-dim); color: var(--yellow); }
.activity-icon.err { background: var(--red-dim); color: var(--red); }
.activity-icon.git { background: rgba(167,139,250,.1); color: var(--purple); }
.activity-icon.done { background: var(--green-dim); color: var(--green); }

.activity-text { line-height: 1.45; word-break: break-word; }
.activity-time { color: var(--text-3); font-family: var(--mono); font-size: 10px; margin-left: auto; flex-shrink:0; }

/* ═══════ MAIN PANEL ═══════ */
.main-panel {
  grid-area: main;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg-0);
}

/* Tabs */
.tabs {
  display: flex;
  align-items: center;
  padding: 0 12px;
  background: var(--bg-1);
  border-bottom: 1px solid var(--border-1);
  flex-shrink: 0;
  height: 36px;
  gap: 0;
}

.tab {
  padding: 0 14px;
  height: 36px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-family: var(--mono);
  color: var(--text-3);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all .15s;
  white-space: nowrap;
}

.tab:hover { color: var(--text-2); }
.tab.active {
  color: var(--text-0);
  border-bottom-color: var(--accent);
}

.tab-icon { font-size: 12px; }

/* Code area */
.code-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  font-family: var(--mono);
  font-size: 12.5px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
  scroll-behavior: smooth;
}

.code-area::-webkit-scrollbar { width: 6px; }
.code-area::-webkit-scrollbar-track { background: transparent; }
.code-area::-webkit-scrollbar-thumb {
  background: var(--border-2);
  border-radius: 3px;
}

/* Streaming tokens */
.token { color: var(--text-1); }
.token-thinking { color: var(--cyan); opacity: .85; }
.token-plan { color: var(--purple); }
.token-action { color: var(--green); font-weight: 500; }
.token-code { color: var(--yellow); }
.token-error { color: var(--red); }

.cursor-blink {
  display: inline-block;
  width: 7px; height: 15px;
  background: var(--accent);
  animation: cursorBlink .8s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 1px;
  border-radius: 1px;
}

@keyframes cursorBlink { 0%,100%{opacity:1} 50%{opacity:0} }

.iteration-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  margin: 12px 0;
  color: var(--text-3);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.iteration-banner::before,
.iteration-banner::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border-1);
}

.section-marker {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  margin: 8px 0 4px;
}

.section-marker.thinking { background: rgba(34,211,238,.08); color: var(--cyan); }
.section-marker.plan { background: rgba(167,139,250,.08); color: var(--purple); }
.section-marker.action { background: rgba(45,212,160,.08); color: var(--green); }
.section-marker.result { background: rgba(245,200,66,.08); color: var(--yellow); }
.section-marker.error { background: var(--red-dim); color: var(--red); }
.section-marker.done { background: var(--green-dim); color: var(--green); }

/* ═══════ RIGHT PANEL ═══════ */
.right-panel {
  grid-area: panel;
  background: var(--bg-1);
  border-left: 1px solid var(--border-1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-1);
  flex-shrink: 0;
}

.panel-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-3);
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 12px 16px;
  flex-shrink: 0;
}

.stat-card {
  background: var(--bg-2);
  border: 1px solid var(--border-1);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
}

.stat-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-3);
  margin-bottom: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 800;
  font-family: var(--mono);
  color: var(--text-0);
}

.stat-card.highlight .stat-value { color: var(--accent); }
.stat-card.success .stat-value { color: var(--green); }
.stat-card.warn .stat-value { color: var(--yellow); }
.stat-card.danger .stat-value { color: var(--red); }

/* Current action */
.current-action {
  padding: 12px 16px;
  flex-shrink: 0;
}

.action-card {
  background: var(--bg-2);
  border: 1px solid var(--border-1);
  border-radius: var(--radius);
  padding: 14px;
  min-height: 60px;
}

.action-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-3);
  margin-bottom: 8px;
}

.action-name {
  font-size: 13px;
  font-family: var(--mono);
  font-weight: 600;
  color: var(--green);
  margin-bottom: 4px;
}

.action-detail {
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-2);
  word-break: break-all;
}

/* Code preview */
.code-preview-section {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  padding: 0 16px 12px;
}

.code-preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.code-preview {
  flex: 1;
  overflow-y: auto;
  background: var(--bg-0);
  border: 1px solid var(--border-1);
  border-radius: var(--radius-sm);
  padding: 12px;
  font-family: var(--mono);
  font-size: 11px;
  line-height: 1.65;
  color: var(--text-2);
  white-space: pre-wrap;
  word-break: break-word;
}

.code-preview::-webkit-scrollbar { width: 4px; }
.code-preview::-webkit-scrollbar-thumb {
  background: var(--border-2);
  border-radius: 2px;
}

/* Progress bar */
.progress-bar {
  height: 2px;
  background: var(--bg-3);
  position: relative;
  flex-shrink: 0;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent), var(--purple));
  width: 0%;
  transition: width .3s;
  border-radius: 1px;
}

.progress-bar.active .progress-fill {
  animation: progressPulse 2s ease-in-out infinite;
}

@keyframes progressPulse {
  0% { opacity: .6; }
  50% { opacity: 1; }
  100% { opacity: .6; }
}

/* ═══════ FOOTER ═══════ */
.footer {
  grid-area: footer;
  background: var(--bg-1);
  border-top: 1px solid var(--border-1);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  font-size: 11px;
  font-family: var(--mono);
  color: var(--text-3);
}

.footer-left, .footer-right { display: flex; align-items: center; gap: 16px; }
.footer-item { display: flex; align-items: center; gap: 4px; }
.footer-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--green);
}

/* ═══════ RESPONSIVE ═══════ */
@media (max-width: 1100px) {
  .app {
    grid-template-columns: 1fr;
    grid-template-areas:
      "header"
      "main"
      "footer";
  }
  .sidebar, .right-panel { display: none; }
}

/* ═══════ SCROLLBAR GLOBAL ═══════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-2); border-radius: 3px; }
</style>
</head>
<body>

<div class="app">
  <!-- HEADER -->
  <div class="header">
    <div class="header-left">
      <div class="logo">
        <div class="logo-icon">⚡</div>
        Coding Agent
      </div>
      <div class="status-pill idle" id="statusPill">
        <div class="status-dot"></div>
        <span id="statusLabel">IDLE</span>
      </div>
    </div>
    <div class="header-center">
      <span>Iteration <strong id="hdrIter" style="color:var(--text-1)">0</strong></span>
      <span class="sep">│</span>
      <span id="hdrTimer">00:00</span>
      <span class="sep">│</span>
      <span>Tokens: <strong id="hdrTokens" style="color:var(--text-1)">0</strong></span>
    </div>
    <div class="header-right">
      <div class="model-tag" title="Coder Model">🧠 __CODER_MODEL__</div>
      <div class="model-tag" title="Reviewer Model">🔍 __REVIEWER_MODEL__</div>
    </div>
  </div>

  <!-- SIDEBAR -->
  <div class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">📋 Goal</div>
      <div class="goal-input-wrap">
        <textarea class="goal-input" id="goalInput"
          placeholder="Describe your coding task..."></textarea>
      </div>
      <div class="btn-row">
        <button class="btn btn-run" id="btnRun" onclick="startAgent()">▶ Run</button>
        <button class="btn btn-stop" id="btnStop" onclick="stopAgent()">⏹ Stop</button>
      </div>
    </div>
    <div class="divider"></div>

    <div class="sidebar-section">
      <div class="sidebar-label">📁 Workspace Files</div>
    </div>
    <div class="file-tree" id="fileTree">
      <div style="padding:8px;color:var(--text-3);font-size:11px;font-style:italic;">No files yet</div>
    </div>
    <div class="divider"></div>

    <div class="sidebar-section">
      <div class="sidebar-label">📌 Activity</div>
    </div>
    <div class="activity-section" id="activityFeed"></div>
  </div>

  <!-- MAIN -->
  <div class="main-panel">
    <div class="tabs">
      <div class="tab active" data-tab="stream" onclick="switchTab('stream')">
        <span class="tab-icon">⚡</span> Live Stream
      </div>
      <div class="tab" data-tab="code" onclick="switchTab('code')">
        <span class="tab-icon">📄</span> Generated Code
      </div>
      <div class="tab" data-tab="terminal" onclick="switchTab('terminal')">
        <span class="tab-icon">🖥</span> Terminal
      </div>
    </div>
    <div class="progress-bar" id="progressBar">
      <div class="progress-fill" id="progressFill"></div>
    </div>
    <div class="code-area" id="codeArea">
      <span style="color:var(--text-3)">Waiting for goal...</span>
    </div>
  </div>

  <!-- RIGHT PANEL -->
  <div class="right-panel">
    <div class="panel-header">
      <div class="panel-title">📊 Dashboard</div>
    </div>
    <div class="stats-grid">
      <div class="stat-card highlight">
        <div class="stat-label">Iterations</div>
        <div class="stat-value" id="statIter">0</div>
      </div>
      <div class="stat-card success">
        <div class="stat-label">Files</div>
        <div class="stat-value" id="statFiles">0</div>
      </div>
      <div class="stat-card warn">
        <div class="stat-label">Commands</div>
        <div class="stat-value" id="statCmds">0</div>
      </div>
      <div class="stat-card danger">
        <div class="stat-label">Errors</div>
        <div class="stat-value" id="statErrors">0</div>
      </div>
    </div>

    <div class="current-action">
      <div class="action-card">
        <div class="action-label">🔥 Current Action</div>
        <div class="action-name" id="curAction">—</div>
        <div class="action-detail" id="curDetail"></div>
      </div>
    </div>

    <div class="code-preview-section">
      <div class="code-preview-header">
        <div class="sidebar-label" style="margin:0">💻 Last Code Output</div>
      </div>
      <div class="code-preview" id="codePreview">No code generated yet.</div>
    </div>
  </div>

  <!-- FOOTER -->
  <div class="footer">
    <div class="footer-left">
      <div class="footer-item">
        <div class="footer-dot" id="footerDot"></div>
        <span id="footerStatus">Ready</span>
      </div>
      <div class="footer-item">workspace/</div>
    </div>
    <div class="footer-right">
      <div class="footer-item" id="footerModel">__CODER_MODEL__</div>
    </div>
  </div>
</div>

<script>
const $ = id => document.getElementById(id);

let running = false;
let startTime = null;
let timerInt = null;
let tokenCount = 0;
let stats = { iter: 0, files: 0, cmds: 0, errors: 0 };
let currentTab = 'stream';
let lastCodeContent = '';

// ─── PERFORMANCE: Token batching to prevent crash ───
let tokenBuffer = [];
let renderScheduled = false;
const MAX_STREAM_NODES = 600;  // Max DOM nodes in stream
let streamNodeCount = 0;

function scheduleRender() {
  if (renderScheduled) return;
  renderScheduled = true;
  requestAnimationFrame(flushTokens);
}

function flushTokens() {
  renderScheduled = false;
  if (tokenBuffer.length === 0) return;

  const area = $('codeArea');
  const frag = document.createDocumentFragment();

  for (const item of tokenBuffer) {
    if (item.type === 'html') {
      const div = document.createElement('div');
      div.innerHTML = item.content;
      while (div.firstChild) {
        frag.appendChild(div.firstChild);
        streamNodeCount++;
      }
    } else {
      const span = document.createElement('span');
      span.className = item.cls || '';
      span.textContent = item.content;
      frag.appendChild(span);
      streamNodeCount++;
    }
  }
  tokenBuffer = [];

  // Remove old nodes to keep DOM small
  while (streamNodeCount > MAX_STREAM_NODES && area.firstChild) {
    area.removeChild(area.firstChild);
    streamNodeCount--;
  }

  // Remove old cursor
  const oldCursor = area.querySelector('.cursor-blink');
  if (oldCursor) oldCursor.remove();

  area.appendChild(frag);

  // Add cursor
  if (running) {
    const cursor = document.createElement('span');
    cursor.className = 'cursor-blink';
    area.appendChild(cursor);
  }

  // Auto-scroll
  area.scrollTop = area.scrollHeight;
}

// ─── Tab switching ──────────────────────────────
function switchTab(name) {
  currentTab = name;
  document.querySelectorAll('.tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === name);
  });
  if (name === 'stream') {
    // Already live DOM
  } else if (name === 'code') {
    $('codeArea').innerHTML = codeTabHTML || '<span style="color:var(--text-3)">No code yet</span>';
  } else if (name === 'terminal') {
    $('codeArea').innerHTML = terminalHTML || '<span style="color:var(--text-3)">No terminal output yet</span>';
  }
}

let codeTabHTML = '';
let terminalHTML = '';

// ─── Status ─────────────────────────────────────
function setStatus(label, type) {
  const pill = $('statusPill');
  pill.className = 'status-pill ' + type;
  $('statusLabel').textContent = label;
  $('footerStatus').textContent = label;
  $('footerDot').style.background =
    type === 'running' ? 'var(--accent)' :
    type === 'done' ? 'var(--green)' :
    type === 'error' ? 'var(--red)' : 'var(--text-3)';
}

function updateTimer() {
  if (!startTime) return;
  const s = Math.floor((Date.now() - startTime) / 1000);
  const m = Math.floor(s / 60);
  const ss = s % 60;
  $('hdrTimer').textContent = m.toString().padStart(2,'0') + ':' + ss.toString().padStart(2,'0');
}

function updateStats() {
  $('statIter').textContent = stats.iter;
  $('statFiles').textContent = stats.files;
  $('statCmds').textContent = stats.cmds;
  $('statErrors').textContent = stats.errors;
  $('hdrIter').textContent = stats.iter;
}

// ─── Activity feed ──────────────────────────────
function addActivity(icon, cls, text) {
  const feed = $('activityFeed');
  const now = new Date().toLocaleTimeString('en',{hour:'2-digit',minute:'2-digit',hour12:false});
  const item = document.createElement('div');
  item.className = 'activity-item';
  item.innerHTML = `
    <div class="activity-icon ${cls}">${icon}</div>
    <div class="activity-text">${esc(text)}</div>
    <div class="activity-time">${now}</div>`;
  feed.prepend(item);
  // Limit feed size
  while (feed.children.length > 30) feed.lastChild.remove();
}

// ─── Stream append (batched) ────────────────────
function appendStream(html) {
  if (currentTab !== 'stream') return;
  tokenBuffer.push({ type: 'html', content: html });
  scheduleRender();
}

function appendToken(text, cls) {
  if (currentTab !== 'stream') return;
  tokenBuffer.push({ type: 'text', content: text, cls: cls });
  scheduleRender();
}

function esc(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ─── File tree ──────────────────────────────────
function refreshFiles(files) {
  const tree = $('fileTree');
  if (!files || files.length === 0) {
    tree.innerHTML = '<div style="padding:8px;color:var(--text-3);font-size:11px;font-style:italic;">No files yet</div>';
    return;
  }
  tree.innerHTML = files.map(f => {
    const icon = f.endsWith('/') ? '📁' :
                 f.endsWith('.py') ? '🐍' :
                 f.endsWith('.js') || f.endsWith('.ts') ? '📜' :
                 f.endsWith('.html') ? '🌐' :
                 f.endsWith('.css') ? '🎨' :
                 f.endsWith('.json') ? '📋' :
                 f.endsWith('.md') ? '📝' : '📄';
    return `<div class="file-item" onclick="requestFile('${esc(f)}')" title="${esc(f)}">
      <span class="file-icon">${icon}</span>${esc(f)}
    </div>`;
  }).join('');
}

function requestFile(path) {
  fetch('/api/file?path=' + encodeURIComponent(path))
    .then(r => r.json())
    .then(data => {
      if (data.content !== undefined) {
        codeTabHTML = '<div style="color:var(--text-3);margin-bottom:8px;font-size:11px;">📄 ' + esc(path) + '</div>'
          + '<div style="color:var(--text-1)">' + esc(data.content) + '</div>';
        switchTab('code');
      }
    }).catch(() => {});
}

// ─── Agent control ──────────────────────────────
async function startAgent() {
  const goal = $('goalInput').value.trim();
  if (!goal) { $('goalInput').focus(); return; }

  running = true;
  stats = { iter: 0, files: 0, cmds: 0, errors: 0 };
  tokenCount = 0;
  tokenBuffer = [];
  streamNodeCount = 0;
  codeTabHTML = '';
  terminalHTML = '';
  startTime = Date.now();
  timerInt = setInterval(updateTimer, 1000);

  $('btnRun').style.display = 'none';
  $('btnStop').style.display = 'flex';
  $('goalInput').disabled = true;
  $('progressBar').classList.add('active');
  $('progressFill').style.width = '100%';
  $('codeArea').innerHTML = '';

  setStatus('RUNNING', 'running');
  updateStats();

  appendStream('<div class="iteration-banner">Agent Starting</div>');
  appendStream('<span style="color:var(--text-2)">Goal: ' + esc(goal) + '</span>\n');
  addActivity('🚀', 'create', 'Agent started: ' + goal.slice(0, 60));

  try {
    const resp = await fetch('/api/start', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ goal })
    });

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';

    while (true) {
      const { value, done: streamDone } = await reader.read();
      if (streamDone) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          handleEvent(JSON.parse(line.slice(6)));
        } catch(e) {}
      }
    }
  } catch(e) {
    appendStream('<div class="section-marker error">❌ CONNECTION ERROR</div>\n' + esc(e.message) + '\n');
    setStatus('ERROR', 'error');
  }
  finish();
}

function handleEvent(ev) {
  switch (ev.type) {

    case 'iteration':
      stats.iter = ev.iteration;
      updateStats();
      appendStream('\n<div class="iteration-banner">Iteration ' + ev.iteration + '</div>\n');
      break;

    case 'token':
      tokenCount++;
      if (tokenCount % 20 === 0) $('hdrTokens').textContent = tokenCount;
      const cls = ev.section === 'thinking' ? 'token-thinking' :
                  ev.section === 'action' ? 'token-action' :
                  ev.section === 'plan' ? 'token-plan' : 'token';
      appendToken(ev.text, cls);
      break;

    case 'section':
      const sectionType = ev.name.toLowerCase();
      appendStream('\n<div class="section-marker ' + sectionType + '">' + esc(ev.label) + '</div>\n');
      break;

    case 'action':
      $('curAction').textContent = ev.tool;
      $('curDetail').textContent = ev.detail || '';
      addActivity(
        ev.tool === 'create_file' ? '📄' :
        ev.tool === 'edit_file' ? '✏️' :
        ev.tool === 'run_command' ? '⚡' :
        ev.tool === 'git' ? '📦' : '🔧',
        ev.tool === 'run_command' ? 'cmd' :
        ev.tool === 'create_file' ? 'create' :
        ev.tool === 'edit_file' ? 'edit' :
        ev.tool === 'git' ? 'git' : 'create',
        ev.tool + ': ' + (ev.detail || '').slice(0, 80)
      );
      if (ev.tool === 'create_file' || ev.tool === 'edit_file') stats.files++;
      if (ev.tool === 'run_command') stats.cmds++;
      updateStats();
      break;

    case 'result':
      const rIcon = ev.success ? '✅' : '❌';
      const rCls = ev.success ? 'token' : 'token-error';
      // Truncate long output for DOM safety
      const output = (ev.output || '').slice(0, 1500);
      appendStream('\n<div class="section-marker ' + (ev.success ? 'result' : 'error') + '">'
        + rIcon + ' Result</div>\n<span class="' + rCls + '">'
        + esc(output) + '</span>\n');

      if (ev.success && ev.code) {
        $('codePreview').textContent = ev.code.slice(0, 3000);
        lastCodeContent = ev.code;
      }

      if (!ev.success) {
        stats.errors++;
        updateStats();
        addActivity('❌', 'err', (ev.output || 'Error').slice(0, 80));
      }

      if (ev.output && ev.output.startsWith('$')) {
        terminalHTML += '<span style="color:var(--green)">' + esc(output) + '</span>\n';
      }
      break;

    case 'files':
      refreshFiles(ev.list || []);
      break;

    case 'done':
      appendStream('\n<div class="section-marker done">✅ TASK COMPLETED</div>\n'
        + '<span class="token">' + esc(ev.summary || '') + '</span>\n');
      $('curAction').textContent = '✅ Done';
      $('curDetail').textContent = '';
      addActivity('✅', 'done', 'Task completed');
      setStatus('DONE', 'done');
      break;

    case 'error':
      appendStream('\n<div class="section-marker error">❌ ERROR</div>\n'
        + '<span class="token-error">' + esc(ev.message || '') + '</span>\n');
      stats.errors++;
      updateStats();
      addActivity('❌', 'err', ev.message || 'Error');
      setStatus('ERROR', 'error');
      break;

    case 'log':
      appendStream('<span style="color:var(--text-3)">' + esc(ev.text || '') + '</span>\n');
      break;
  }
}

function stopAgent() {
  fetch('/api/stop', { method: 'POST' }).catch(() => {});
  finish();
  setStatus('STOPPED', 'error');
  addActivity('⏹', 'err', 'Agent stopped by user');
}

function finish() {
  running = false;
  clearInterval(timerInt);
  $('btnRun').style.display = 'flex';
  $('btnStop').style.display = 'none';
  $('goalInput').disabled = false;
  $('progressBar').classList.remove('active');
  $('progressFill').style.width = '0%';
  // Final flush
  flushTokens();
  // Remove cursor
  const cursor = $('codeArea').querySelector('.cursor-blink');
  if (cursor) cursor.remove();
}

// ─── Keyboard shortcut ─────────────────────────
document.addEventListener('keydown', e => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
    e.preventDefault();
    if (!running) startAgent();
  }
});
</script>
</body>
</html>'''
