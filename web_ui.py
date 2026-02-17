"""
Autonomous Coding Agent — Web UI
A sleek terminal-in-browser interface for the agent.
"""
import os
import json
import threading
import subprocess
import sys
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from config import OLLAMA_BASE_URL, CODER_MODEL, REVIEWER_MODEL, WORKSPACE_DIR


WEB_PORT = int(os.getenv("WEB_PORT", "8080"))


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🤖 Autonomous Coding Agent</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');

  :root {
    --bg-primary: #0a0e17;
    --bg-secondary: #111827;
    --bg-card: #1a1f2e;
    --bg-input: #0d1117;
    --border: #2d3748;
    --border-active: #4f8ff7;
    --text-primary: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-dim: #64748b;
    --accent-blue: #4f8ff7;
    --accent-green: #22c55e;
    --accent-red: #ef4444;
    --accent-yellow: #eab308;
    --accent-purple: #a78bfa;
    --accent-cyan: #06b6d4;
    --gradient-hero: linear-gradient(135deg, #4f8ff7 0%, #a78bfa 50%, #06b6d4 100%);
    --shadow-glow: 0 0 30px rgba(79, 143, 247, 0.15);
  }

  * { margin:0; padding:0; box-sizing:border-box; }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* ─── Header ─── */
  .header {
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    backdrop-filter: blur(10px);
    position: sticky;
    top: 0;
    z-index: 100;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .logo {
    font-size: 24px;
    font-weight: 700;
    background: var(--gradient-hero);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
  }

  .status-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    background: rgba(34, 197, 94, 0.1);
    color: var(--accent-green);
    border: 1px solid rgba(34, 197, 94, 0.2);
  }

  .status-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent-green);
    animation: pulse 2s infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
  }

  .header-info {
    display: flex; gap: 24px;
    font-size: 12px;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
  }

  .info-item { display: flex; align-items: center; gap: 6px; }
  .info-label { color: var(--text-dim); }
  .info-value { color: var(--text-secondary); }

  /* ─── Main Layout ─── */
  .main {
    display: grid;
    grid-template-columns: 1fr;
    max-width: 1200px;
    margin: 0 auto;
    padding: 24px;
    gap: 24px;
  }

  /* ─── Goal Input ─── */
  .goal-section {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px;
    box-shadow: var(--shadow-glow);
  }

  .section-title {
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--accent-blue);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .goal-input {
    width: 100%;
    min-height: 100px;
    background: var(--bg-input);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px;
    color: var(--text-primary);
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    line-height: 1.6;
    resize: vertical;
    outline: none;
    transition: border-color 0.3s, box-shadow 0.3s;
  }

  .goal-input:focus {
    border-color: var(--border-active);
    box-shadow: 0 0 0 3px rgba(79, 143, 247, 0.1);
  }

  .goal-input::placeholder {
    color: var(--text-dim);
  }

  .goal-actions {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 16px;
  }

  .btn {
    padding: 10px 24px;
    border-radius: 10px;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.3s;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .btn-primary {
    background: var(--gradient-hero);
    color: white;
    box-shadow: 0 4px 15px rgba(79, 143, 247, 0.3);
  }

  .btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(79, 143, 247, 0.4);
  }

  .btn-primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  .btn-secondary {
    background: var(--bg-input);
    color: var(--text-secondary);
    border: 1px solid var(--border);
  }

  .btn-secondary:hover {
    border-color: var(--accent-blue);
    color: var(--text-primary);
  }

  .btn-danger {
    background: rgba(239, 68, 68, 0.1);
    color: var(--accent-red);
    border: 1px solid rgba(239, 68, 68, 0.2);
  }

  .btn-danger:hover {
    background: rgba(239, 68, 68, 0.2);
  }

  /* ─── Output Terminal ─── */
  .terminal-section {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
  }

  .terminal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
  }

  .terminal-dots {
    display: flex; gap: 6px;
  }

  .terminal-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
  }

  .dot-red { background: #ef4444; }
  .dot-yellow { background: #eab308; }
  .dot-green { background: #22c55e; }

  .terminal-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-dim);
  }

  .terminal-body {
    height: 500px;
    overflow-y: auto;
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    line-height: 1.7;
    background: var(--bg-input);
    scroll-behavior: smooth;
  }

  .terminal-body::-webkit-scrollbar { width: 6px; }
  .terminal-body::-webkit-scrollbar-track { background: transparent; }
  .terminal-body::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 3px;
  }

  .log-line { margin-bottom: 2px; white-space: pre-wrap; word-break: break-all; }
  .log-thinking { color: var(--accent-cyan); }
  .log-action { color: var(--accent-green); font-weight: 500; }
  .log-error { color: var(--accent-red); }
  .log-info { color: var(--text-dim); }
  .log-success { color: var(--accent-green); }
  .log-tool { color: var(--accent-yellow); }
  .log-step {
    color: var(--accent-purple);
    font-weight: 700;
    padding: 8px 0;
    border-top: 1px solid var(--border);
    margin-top: 8px;
  }

  /* ─── Stats Bar ─── */
  .stats-bar {
    display: flex;
    gap: 16px;
    padding: 12px 20px;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border);
  }

  .stat {
    display: flex; align-items: center; gap: 6px;
    font-size: 12px;
    color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace;
  }

  .stat-value {
    color: var(--text-primary);
    font-weight: 600;
  }

  /* ─── Responsive ─── */
  @media (max-width: 768px) {
    .main { padding: 12px; }
    .header { padding: 12px 16px; }
    .header-info { display: none; }
    .terminal-body { height: 400px; }
  }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="logo">🤖 Coding Agent</div>
    <div class="status-badge" id="statusBadge">
      <div class="status-dot"></div>
      <span id="statusText">Ready</span>
    </div>
  </div>
  <div class="header-info">
    <div class="info-item">
      <span class="info-label">Coder:</span>
      <span class="info-value" id="coderModel">CODER_MODEL</span>
    </div>
    <div class="info-item">
      <span class="info-label">Reviewer:</span>
      <span class="info-value" id="reviewerModel">REVIEWER_MODEL</span>
    </div>
  </div>
</div>

<div class="main">
  <div class="goal-section">
    <div class="section-title">📋 Goal</div>
    <textarea
      class="goal-input"
      id="goalInput"
      placeholder="Enter your coding goal...&#10;&#10;Examples:&#10;• Create a FastAPI backend with JWT auth and SQLite&#10;• Fix the bug in src/auth.py — login returns 500&#10;• Add unit tests for the utils module"
    ></textarea>
    <div class="goal-actions">
      <div style="display:flex; gap:8px;">
        <button class="btn btn-primary" id="startBtn" onclick="startAgent()">
          ▶ Start Agent
        </button>
        <button class="btn btn-danger" id="stopBtn" onclick="stopAgent()" style="display:none;">
          ⏹ Stop
        </button>
      </div>
      <button class="btn btn-secondary" onclick="clearTerminal()">
        🗑 Clear
      </button>
    </div>
  </div>

  <div class="terminal-section">
    <div class="terminal-header">
      <div class="terminal-dots">
        <div class="terminal-dot dot-red"></div>
        <div class="terminal-dot dot-yellow"></div>
        <div class="terminal-dot dot-green"></div>
      </div>
      <div class="terminal-title">agent output</div>
      <div style="font-size:12px;color:var(--text-dim);font-family:'JetBrains Mono',monospace;">
        <span id="iterCount">0</span> iterations
      </div>
    </div>
    <div class="terminal-body" id="terminal"></div>
    <div class="stats-bar">
      <div class="stat">Steps: <span class="stat-value" id="statSteps">0</span></div>
      <div class="stat">Files: <span class="stat-value" id="statFiles">0</span></div>
      <div class="stat">Commands: <span class="stat-value" id="statCmds">0</span></div>
      <div class="stat">Errors: <span class="stat-value" id="statErrors">0</span></div>
      <div class="stat">Time: <span class="stat-value" id="statTime">0:00</span></div>
    </div>
  </div>
</div>

<script>
  let ws = null;
  let running = false;
  let startTime = null;
  let timerInterval = null;
  let stats = { steps: 0, files: 0, cmds: 0, errors: 0 };

  function log(text, cls = '') {
    const terminal = document.getElementById('terminal');
    const line = document.createElement('div');
    line.className = 'log-line ' + cls;
    line.textContent = text;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
  }

  function updateStats() {
    document.getElementById('statSteps').textContent = stats.steps;
    document.getElementById('statFiles').textContent = stats.files;
    document.getElementById('statCmds').textContent = stats.cmds;
    document.getElementById('statErrors').textContent = stats.errors;
  }

  function updateTimer() {
    if (!startTime) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const min = Math.floor(elapsed / 60);
    const sec = elapsed % 60;
    document.getElementById('statTime').textContent =
      min + ':' + (sec < 10 ? '0' : '') + sec;
  }

  function setStatus(text, type) {
    const badge = document.getElementById('statusBadge');
    const dot = badge.querySelector('.status-dot');
    const span = document.getElementById('statusText');
    span.textContent = text;

    badge.style.background = type === 'running'
      ? 'rgba(79, 143, 247, 0.1)' : type === 'done'
      ? 'rgba(34, 197, 94, 0.1)' : type === 'error'
      ? 'rgba(239, 68, 68, 0.1)' : 'rgba(34, 197, 94, 0.1)';

    badge.style.color = dot.style.background = type === 'running'
      ? '#4f8ff7' : type === 'done'
      ? '#22c55e' : type === 'error'
      ? '#ef4444' : '#22c55e';

    badge.style.borderColor = type === 'running'
      ? 'rgba(79, 143, 247, 0.2)' : type === 'done'
      ? 'rgba(34, 197, 94, 0.2)' : type === 'error'
      ? 'rgba(239, 68, 68, 0.2)' : 'rgba(34, 197, 94, 0.2)';
  }

  async function startAgent() {
    const goal = document.getElementById('goalInput').value.trim();
    if (!goal) { alert('Please enter a goal.'); return; }

    running = true;
    stats = { steps: 0, files: 0, cmds: 0, errors: 0 };
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 1000);

    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('stopBtn').style.display = 'flex';
    document.getElementById('goalInput').disabled = true;
    setStatus('Running...', 'running');

    log('═══════════════════════════════════════════', 'log-step');
    log('🤖 Agent Started', 'log-step');
    log('Goal: ' + goal, 'log-info');
    log('═══════════════════════════════════════════', 'log-step');

    try {
      const response = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            handleEvent(data);
          } catch(e) {}
        }
      }
    } catch(e) {
      log('❌ Connection error: ' + e.message, 'log-error');
      setStatus('Error', 'error');
    }

    stopAgent();
  }

  function handleEvent(data) {
    switch(data.type) {
      case 'iteration':
        stats.steps++;
        document.getElementById('iterCount').textContent = stats.steps;
        log('', '');
        log('══════ ITERATION ' + data.iteration + ' ══════', 'log-step');
        break;
      case 'thinking':
        log('💭 ' + data.text, 'log-thinking');
        break;
      case 'action':
        log('⚡ ACTION: ' + data.tool, 'log-action');
        if (data.tool === 'run_command') stats.cmds++;
        if (data.tool === 'create_file' || data.tool === 'edit_file') stats.files++;
        break;
      case 'result':
        if (data.success) {
          log('✅ ' + data.output, 'log-success');
        } else {
          log('❌ ' + data.output, 'log-error');
          stats.errors++;
        }
        break;
      case 'done':
        log('', '');
        log('══════════════════════════════════════', 'log-step');
        log('✅ TASK COMPLETED', 'log-success');
        log(data.summary || '', 'log-info');
        setStatus('Done', 'done');
        break;
      case 'error':
        log('❌ ERROR: ' + data.message, 'log-error');
        stats.errors++;
        setStatus('Error', 'error');
        break;
      case 'log':
        log(data.text, 'log-info');
        break;
    }
    updateStats();
  }

  function stopAgent() {
    running = false;
    clearInterval(timerInterval);
    document.getElementById('startBtn').style.display = 'flex';
    document.getElementById('stopBtn').style.display = 'none';
    document.getElementById('goalInput').disabled = false;
    if (document.getElementById('statusText').textContent === 'Running...') {
      setStatus('Stopped', 'error');
    }
    fetch('/api/stop', { method: 'POST' }).catch(() => {});
  }

  function clearTerminal() {
    document.getElementById('terminal').innerHTML = '';
    stats = { steps: 0, files: 0, cmds: 0, errors: 0 };
    updateStats();
    document.getElementById('iterCount').textContent = '0';
    document.getElementById('statTime').textContent = '0:00';
  }

  // Set model names from config
  document.getElementById('coderModel').textContent = 'CODER_MODEL_PLACEHOLDER';
  document.getElementById('reviewerModel').textContent = 'REVIEWER_MODEL_PLACEHOLDER';
</script>
</body>
</html>"""


def get_html():
    """Return the HTML with config values injected."""
    return (HTML_TEMPLATE
        .replace("CODER_MODEL_PLACEHOLDER", CODER_MODEL)
        .replace("REVIEWER_MODEL_PLACEHOLDER", REVIEWER_MODEL))
