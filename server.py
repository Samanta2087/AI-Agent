"""
Autonomous Coding Agent — Web Server
HTTP server with SSE streaming for the web UI.
"""
import os
import sys
import json
import threading
import queue
import time
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

from config import (
    OLLAMA_BASE_URL,
    CODER_MODEL,
    CODER_OPTIONS,
    WORKSPACE_DIR,
    MAX_ITERATIONS,
)
from prompts import CODER_SYSTEM_PROMPT, get_goal_prompt, get_observation_prompt
from tools import execute_tool
from reviewer import review_files
from web_ui import get_html

import requests


WEB_PORT = int(os.getenv("WEB_PORT", "8080"))

# Global state
agent_thread = None
agent_stop_event = threading.Event()
event_queues: list[queue.Queue] = []


def broadcast_event(event: dict):
    """Send an event to all connected clients."""
    data = f"data: {json.dumps(event)}\n\n"
    for q in event_queues:
        try:
            q.put_nowait(data)
        except queue.Full:
            pass


def parse_action(response_text: str):
    """Parse ACTION block from response."""
    patterns = [
        r"```ACTION\s*\n(.*?)```",
        r"```action\s*\n(.*?)```",
    ]

    action_text = None
    for pattern in patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            action_text = match.group(1).strip()
            break

    if not action_text:
        return None

    params = {}
    current_key = None
    current_value_lines = []
    is_multiline = False

    for line in action_text.split("\n"):
        kv_match = re.match(r'^(\w+):\s*(.*)', line)
        if kv_match and not is_multiline:
            if current_key:
                params[current_key] = "\n".join(current_value_lines).strip()
            current_key = kv_match.group(1)
            value = kv_match.group(2)
            if value == "|":
                is_multiline = True
                current_value_lines = []
            else:
                current_value_lines = [value]
        elif is_multiline:
            if line and not line[0].isspace() and re.match(r'^(\w+):\s*(.*)', line):
                params[current_key] = "\n".join(current_value_lines)
                is_multiline = False
                kv_match = re.match(r'^(\w+):\s*(.*)', line)
                current_key = kv_match.group(1)
                value = kv_match.group(2)
                if value == "|":
                    is_multiline = True
                    current_value_lines = []
                else:
                    current_value_lines = [value]
            else:
                stripped = line[2:] if line.startswith("  ") else line
                current_value_lines.append(stripped)
        elif current_key:
            current_value_lines.append(line)

    if current_key:
        if is_multiline:
            params[current_key] = "\n".join(current_value_lines)
        else:
            params[current_key] = "\n".join(current_value_lines).strip()

    tool_name = params.pop("tool", None)
    if not tool_name:
        return None

    return {"tool": tool_name.strip(), "params": params}


def run_agent_task(goal: str):
    """Run the agent loop in a background thread, broadcasting events."""
    global agent_stop_event
    agent_stop_event.clear()

    messages = [
        {"role": "system", "content": CODER_SYSTEM_PROMPT},
        {"role": "user", "content": get_goal_prompt(goal)},
    ]

    broadcast_event({"type": "log", "text": f"Goal: {goal}"})

    for iteration in range(1, MAX_ITERATIONS + 1):
        if agent_stop_event.is_set():
            broadcast_event({"type": "log", "text": "Agent stopped by user."})
            return

        broadcast_event({"type": "iteration", "iteration": iteration})

        # Call Ollama
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": CODER_MODEL,
                    "messages": messages,
                    "stream": False,
                    "options": CODER_OPTIONS,
                },
                timeout=600,
            )
            resp.raise_for_status()
            response_text = resp.json().get("message", {}).get("content", "")
        except Exception as e:
            broadcast_event({"type": "error", "message": f"Ollama error: {e}"})
            return

        messages.append({"role": "assistant", "content": response_text})

        # Extract thinking
        thinking_match = re.search(r"## THINKING\s*\n(.*?)(?=\n##|\n```ACTION)", response_text, re.DOTALL)
        if thinking_match:
            broadcast_event({"type": "thinking", "text": thinking_match.group(1).strip()[:500]})

        # Parse action
        action = parse_action(response_text)
        if not action:
            broadcast_event({"type": "log", "text": "No ACTION block found. Retrying..."})
            messages.append({
                "role": "user",
                "content": "You did not output an ACTION block. Please provide your next action in a ```ACTION ... ``` block.",
            })
            continue

        tool_name = action["tool"]
        params = action["params"]

        broadcast_event({"type": "action", "tool": tool_name})

        # Handle done
        if tool_name == "done":
            summary = params.get("summary", "Task completed.")
            broadcast_event({"type": "done", "summary": summary})
            return

        # Handle ask_user (skip in web mode — continue)
        if tool_name == "ask_user":
            question = params.get("question", "")
            broadcast_event({"type": "log", "text": f"❓ Agent asks: {question}"})
            messages.append({
                "role": "user",
                "content": get_observation_prompt("ask_user", "User says: continue, use your best judgment.", True),
            })
            continue

        # Handle review
        if tool_name == "review":
            files_str = params.get("files", "")
            file_list = [f.strip() for f in files_str.strip().split("\n") if f.strip()]
            broadcast_event({"type": "log", "text": f"🔍 Reviewing: {', '.join(file_list)}"})
            review_result = review_files(file_list)
            broadcast_event({"type": "result", "success": True, "output": review_result[:500]})
            messages.append({
                "role": "user",
                "content": get_observation_prompt("review", review_result, True),
            })
            continue

        # Execute tool
        result = execute_tool(tool_name, params)
        broadcast_event({
            "type": "result",
            "success": result["success"],
            "output": result["output"][:1000],
        })

        messages.append({
            "role": "user",
            "content": get_observation_prompt(tool_name, result["output"], result["success"]),
        })

        # Trim history
        if len(messages) > 40:
            messages = [messages[0]] + messages[-30:]

    broadcast_event({"type": "error", "message": f"Max iterations ({MAX_ITERATIONS}) reached."})


class AgentHandler(BaseHTTPRequestHandler):
    """HTTP handler for the web UI."""

    def log_message(self, format, *args):
        pass  # Suppress default logging

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/" or path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(get_html().encode())

        elif path == "/api/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        global agent_thread
        path = urlparse(self.path).path

        if path == "/api/start":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            goal = body.get("goal", "")

            if not goal:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No goal"}).encode())
                return

            # SSE response
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            # Create event queue for this client
            q = queue.Queue(maxsize=1000)
            event_queues.append(q)

            # Start agent in background
            agent_stop_event.clear()
            agent_thread = threading.Thread(target=run_agent_task, args=(goal,), daemon=True)
            agent_thread.start()

            # Stream events to client
            try:
                while agent_thread.is_alive() or not q.empty():
                    try:
                        event_data = q.get(timeout=1)
                        self.wfile.write(event_data.encode())
                        self.wfile.flush()
                    except queue.Empty:
                        # Send keepalive
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                event_queues.remove(q)

        elif path == "/api/stop":
            agent_stop_event.set()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "stopped"}).encode())

        else:
            self.send_response(404)
            self.end_headers()


def start_server():
    """Start the web server."""
    server = HTTPServer(("0.0.0.0", WEB_PORT), AgentHandler)
    print(f"\n🌐 Web UI running at: http://localhost:{WEB_PORT}")
    print(f"   (accessible from network at: http://0.0.0.0:{WEB_PORT})\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
        server.server_close()


if __name__ == "__main__":
    start_server()
