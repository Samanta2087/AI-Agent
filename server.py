"""
Autonomous Coding Agent — Production Server
HTTP server with token-level SSE streaming for real-time UI.
"""
import os
import sys
import json
import threading
import queue
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from config import (
    OLLAMA_BASE_URL,
    CODER_MODEL,
    CODER_OPTIONS,
    KEEP_ALIVE,
    WORKSPACE_DIR,
    MAX_ITERATIONS,
)
from prompts import CODER_SYSTEM_PROMPT, get_goal_prompt, get_observation_prompt
from tools import execute_tool
from reviewer import review_files
from web_ui import get_html

import requests


WEB_PORT = int(os.getenv("WEB_PORT", "8090"))

# Global state
agent_thread = None
agent_stop = threading.Event()
event_queues: list[queue.Queue] = []


def emit(event: dict):
    """Broadcast an SSE event to all connected clients."""
    data = f"data: {json.dumps(event)}\n\n"
    dead = []
    for q in event_queues:
        try:
            q.put_nowait(data)
        except queue.Full:
            dead.append(q)
    for q in dead:
        try: event_queues.remove(q)
        except: pass


def get_workspace_files() -> list[str]:
    """List all files in workspace recursively."""
    files = []
    workspace = os.path.abspath(WORKSPACE_DIR)
    if not os.path.isdir(workspace):
        return files
    for root, dirs, fnames in os.walk(workspace):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {
            'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'
        }]
        for f in sorted(fnames):
            rel = os.path.relpath(os.path.join(root, f), workspace)
            files.append(rel.replace('\\', '/'))
    return files[:100]  # cap


def read_workspace_file(rel_path: str) -> str:
    """Read a file from workspace."""
    workspace = os.path.abspath(WORKSPACE_DIR)
    full = os.path.normpath(os.path.join(workspace, rel_path))
    if not full.startswith(workspace):
        return "(blocked)"
    if not os.path.isfile(full):
        return "(not found)"
    try:
        with open(full, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        if len(content) > 50000:
            content = content[:50000] + "\n\n... (truncated)"
        return content
    except Exception as e:
        return f"(error: {e})"


# ─── Action Parser ──────────────────────────────────────────────
def parse_action(text: str):
    """Parse ACTION block from response."""
    patterns = [
        r"```ACTION\s*\n(.*?)```",
        r"```action\s*\n(.*?)```",
    ]
    action_text = None
    for p in patterns:
        m = re.search(p, text, re.DOTALL | re.IGNORECASE)
        if m:
            action_text = m.group(1).strip()
            break
    if not action_text:
        return None

    params = {}
    cur_key = None
    cur_lines = []
    multiline = False

    for line in action_text.split("\n"):
        kv = re.match(r'^(\w+):\s*(.*)', line)
        if kv and not multiline:
            if cur_key:
                params[cur_key] = "\n".join(cur_lines).strip()
            cur_key = kv.group(1)
            val = kv.group(2)
            if val == "|":
                multiline = True
                cur_lines = []
            else:
                cur_lines = [val]
        elif multiline:
            if line and not line[0].isspace() and re.match(r'^(\w+):\s*(.*)', line):
                params[cur_key] = "\n".join(cur_lines)
                multiline = False
                kv = re.match(r'^(\w+):\s*(.*)', line)
                cur_key = kv.group(1)
                val = kv.group(2)
                if val == "|":
                    multiline = True
                    cur_lines = []
                else:
                    cur_lines = [val]
            else:
                stripped = line[2:] if line.startswith("  ") else line
                cur_lines.append(stripped)
        elif cur_key:
            cur_lines.append(line)

    if cur_key:
        params[cur_key] = "\n".join(cur_lines) if multiline else "\n".join(cur_lines).strip()

    tool = params.pop("tool", None)
    if not tool:
        return None
    return {"tool": tool.strip(), "params": params}


# ─── Agent Loop with Token Streaming ────────────────────────────
def run_agent_task(goal: str):
    """Main agent loop — streams tokens via SSE."""
    agent_stop.clear()
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    messages = [
        {"role": "system", "content": CODER_SYSTEM_PROMPT},
        {"role": "user", "content": get_goal_prompt(goal)},
    ]

    emit({"type": "log", "text": f"Goal: {goal}"})
    emit({"type": "files", "list": get_workspace_files()})

    for iteration in range(1, MAX_ITERATIONS + 1):
        if agent_stop.is_set():
            emit({"type": "log", "text": "Stopped by user."})
            return

        emit({"type": "iteration", "iteration": iteration})

        # ── Stream tokens from Ollama ──
        full_response = ""
        current_section = "thinking"

        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": CODER_MODEL,
                    "messages": messages,
                    "stream": True,
                    "options": CODER_OPTIONS,
                    "keep_alive": KEEP_ALIVE,
                },
                timeout=600,
                stream=True,
            )
            # ★ Capture actual error body from Ollama
            if resp.status_code != 200:
                try:
                    err_body = resp.text[:500]
                except:
                    err_body = f"HTTP {resp.status_code}"
                emit({"type": "error", "message": f"Ollama returned {resp.status_code}: {err_body}"})
                return

            # Detect sections and stream tokens
            for line in resp.iter_lines():
                if agent_stop.is_set():
                    return
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if not token:
                        if chunk.get("done"):
                            break
                        continue

                    full_response += token

                    # Detect section changes
                    lower = full_response[-200:].lower()
                    if "## thinking" in lower or "## analysis" in lower:
                        if current_section != "thinking":
                            current_section = "thinking"
                            emit({"type": "section", "name": "thinking", "label": "💭 Thinking"})
                    elif "## plan" in lower:
                        if current_section != "plan":
                            current_section = "plan"
                            emit({"type": "section", "name": "plan", "label": "📋 Plan"})
                    elif "```action" in lower or "```ACTION" in full_response[-200:]:
                        if current_section != "action":
                            current_section = "action"
                            emit({"type": "section", "name": "action", "label": "⚡ Action"})

                    emit({
                        "type": "token",
                        "text": token,
                        "section": current_section,
                    })

                    if chunk.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

        except requests.exceptions.ConnectionError:
            emit({"type": "error", "message": "Cannot connect to Ollama. Is it running?"})
            return
        except Exception as e:
            emit({"type": "error", "message": f"Ollama error: {e}"})
            return

        messages.append({"role": "assistant", "content": full_response})

        # ── Parse action ──
        action = parse_action(full_response)

        if not action:
            emit({"type": "log", "text": "⚠ No ACTION found. Retrying..."})
            messages.append({
                "role": "user",
                "content": "You did not output an ACTION block. Please provide exactly one ```ACTION ... ``` block.",
            })
            continue

        tool_name = action["tool"]
        params = action["params"]

        # Build detail string for UI
        detail = ""
        if tool_name == "create_file":
            detail = params.get("path", "")
        elif tool_name == "edit_file":
            detail = params.get("path", "")
        elif tool_name == "run_command":
            detail = params.get("command", "")
        elif tool_name == "git":
            detail = params.get("command", "")
        elif tool_name == "read_file":
            detail = params.get("path", "")

        emit({"type": "action", "tool": tool_name, "detail": detail})

        # ── Handle special tools ──
        if tool_name == "done":
            summary = params.get("summary", "Task completed.")
            emit({"type": "files", "list": get_workspace_files()})
            emit({"type": "done", "summary": summary})
            return

        if tool_name == "ask_user":
            question = params.get("question", "")
            emit({"type": "log", "text": f"❓ {question}"})
            messages.append({
                "role": "user",
                "content": get_observation_prompt("ask_user", "User says: continue with your best judgment.", True),
            })
            continue

        if tool_name == "review":
            files_str = params.get("files", "")
            file_list = [f.strip() for f in files_str.strip().split("\n") if f.strip()]
            emit({"type": "log", "text": f"🔍 Reviewing {len(file_list)} files..."})
            review_result = review_files(file_list)
            emit({"type": "result", "success": True, "output": review_result[:2000]})
            messages.append({
                "role": "user",
                "content": get_observation_prompt("review", review_result, True),
            })
            continue

        # ── Execute tool ──
        result = execute_tool(tool_name, params)

        # Extract code content for preview
        code = ""
        if tool_name == "create_file" and result["success"]:
            code = params.get("content", "")
        elif tool_name == "read_file" and result["success"]:
            code = result["output"]

        emit({
            "type": "result",
            "success": result["success"],
            "output": result["output"][:3000],
            "code": code[:5000] if code else "",
        })

        # Refresh file tree after file operations
        if tool_name in ("create_file", "edit_file", "delete_file", "git"):
            emit({"type": "files", "list": get_workspace_files()})

        messages.append({
            "role": "user",
            "content": get_observation_prompt(tool_name, result["output"], result["success"]),
        })

        # Trim history
        if len(messages) > 40:
            messages = [messages[0]] + messages[-30:]

    emit({"type": "error", "message": f"Max iterations ({MAX_ITERATIONS}) reached."})


# ─── HTTP Handler ───────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # silent

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(get_html().encode())

        elif path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "model": CODER_MODEL}).encode())

        elif path == "/api/files":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"files": get_workspace_files()}).encode())

        elif path == "/api/file":
            qs = parse_qs(parsed.query)
            fpath = qs.get("path", [""])[0]
            content = read_workspace_file(fpath)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"path": fpath, "content": content}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global agent_thread
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/start":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            goal = body.get("goal", "").strip()

            if not goal:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No goal"}).encode())
                return

            # SSE stream
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self._cors()
            self.end_headers()

            q = queue.Queue(maxsize=5000)
            event_queues.append(q)

            agent_stop.clear()
            agent_thread = threading.Thread(target=run_agent_task, args=(goal,), daemon=True)
            agent_thread.start()

            try:
                while agent_thread.is_alive() or not q.empty():
                    try:
                        data = q.get(timeout=0.5)
                        self.wfile.write(data.encode())
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                try: event_queues.remove(q)
                except: pass

        elif path == "/api/stop":
            agent_stop.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stopped"}).encode())

        else:
            self.send_response(404)
            self.end_headers()


# ─── Threaded Server ────────────────────────────────────────────
class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread for SSE."""
    allow_reuse_address = True
    daemon_threads = True

    def process_request(self, request, client_address):
        t = threading.Thread(target=self.__process, args=(request, client_address))
        t.daemon = True
        t.start()

    def __process(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            pass
        finally:
            self.shutdown_request(request)


def start_server():
    server = ThreadedHTTPServer(("0.0.0.0", WEB_PORT), Handler)
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              ⚡ Autonomous Coding Agent                     ║
║                                                              ║
║   🌐 Web UI:    http://0.0.0.0:{WEB_PORT:<26}   ║
║   🧠 Coder:     {CODER_MODEL:<40}   ║
║   🔍 Reviewer:  {os.getenv('REVIEWER_MODEL', 'qwen2.5-coder:14b'):<40}   ║
║   📁 Workspace: {WORKSPACE_DIR:<40}   ║
║                                                              ║
║   Press Ctrl+C to stop                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.server_close()


if __name__ == "__main__":
    start_server()
