"""
Autonomous Coding Agent — Main Agent Loop
Connects to Ollama, parses actions, executes tools, loops until DONE.
"""
import re
import sys
import json
import time
import requests
from datetime import datetime
from typing import Optional

from config import (
    OLLAMA_BASE_URL,
    CODER_MODEL,
    CODER_OPTIONS,
    WORKSPACE_DIR,
    MAX_ITERATIONS,
)
from prompts import (
    CODER_SYSTEM_PROMPT,
    get_goal_prompt,
    get_observation_prompt,
)
from tools import execute_tool
from reviewer import review_files


# ─── ANSI Colors ────────────────────────────────────────────────
class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BG_DARK = "\033[40m"


def banner():
    print(f"""
{C.CYAN}{C.BOLD}╔══════════════════════════════════════════════════════════════╗
║                 🤖 AUTONOMOUS CODING AGENT                  ║
║                                                              ║
║  Coder:    {CODER_MODEL:<42}   ║
║  Ollama:   {OLLAMA_BASE_URL:<42}   ║
║  Workspace: {WORKSPACE_DIR:<41}   ║
╚══════════════════════════════════════════════════════════════╝{C.RESET}
""")


# ─── Action Parser ──────────────────────────────────────────────
def parse_action(response_text: str) -> Optional[dict]:
    """
    Parse an ACTION block from the model's response.
    Returns dict with 'tool' and parameters, or None.
    """
    # Try to find ```ACTION ... ``` block
    patterns = [
        r"```ACTION\s*\n(.*?)```",
        r"```action\s*\n(.*?)```",
        r"```\s*ACTION\s*\n(.*?)```",
    ]

    action_text = None
    for pattern in patterns:
        match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
        if match:
            action_text = match.group(1).strip()
            break

    if not action_text:
        return None

    # Parse YAML-like key: value format
    params = {}
    current_key = None
    current_value_lines = []
    is_multiline = False

    for line in action_text.split("\n"):
        # Check for key: value pattern
        kv_match = re.match(r'^(\w+):\s*(.*)', line)

        if kv_match and not is_multiline:
            # Save previous key
            if current_key:
                params[current_key] = "\n".join(current_value_lines).strip()

            current_key = kv_match.group(1)
            value = kv_match.group(2)

            if value == "|":
                # Multiline value starts
                is_multiline = True
                current_value_lines = []
            else:
                current_value_lines = [value]
        elif is_multiline:
            if line and not line[0].isspace() and re.match(r'^(\w+):\s*(.*)', line):
                # New key found, end multiline
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
                # Strip common indent (2 spaces)
                stripped = line[2:] if line.startswith("  ") else line
                current_value_lines.append(stripped)
        elif current_key:
            current_value_lines.append(line)

    # Save last key
    if current_key:
        if is_multiline:
            params[current_key] = "\n".join(current_value_lines)
        else:
            params[current_key] = "\n".join(current_value_lines).strip()

    tool_name = params.pop("tool", None)
    if not tool_name:
        return None

    return {"tool": tool_name.strip(), "params": params}


# ─── Ollama Chat ────────────────────────────────────────────────
def _get_coder_opts():
    """Get coder options with keep_alive separated."""
    opts = {k: v for k, v in CODER_OPTIONS.items() if k != "keep_alive"}
    ka = CODER_OPTIONS.get("keep_alive", "5m")
    return opts, ka


def chat_with_ollama(messages: list[dict]) -> str:
    """Send messages to Ollama and get response."""
    opts, keep_alive = _get_coder_opts()
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": CODER_MODEL,
                "messages": messages,
                "stream": False,
                "options": opts,
                "keep_alive": keep_alive,  # ★ Unload after response
            },
            timeout=600,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")

    except requests.exceptions.ConnectionError:
        print(f"\n{C.RED}❌ Cannot connect to Ollama at {OLLAMA_BASE_URL}{C.RESET}")
        print(f"{C.YELLOW}   Make sure Ollama is running: ollama serve{C.RESET}")
        sys.exit(1)
    except requests.exceptions.Timeout:
        return "I apologize, the response timed out. Let me try a simpler approach.\n\n## THINKING\nThe previous request was too complex. I'll break it down.\n\n```ACTION\ntool: ask_user\nquestion: The request timed out. Should I try a simpler approach?\n```"
    except Exception as e:
        print(f"\n{C.RED}❌ Ollama error: {e}{C.RESET}")
        sys.exit(1)


# ─── Streaming Chat (for visual feedback) ───────────────────────
def chat_with_ollama_stream(messages: list[dict]) -> str:
    """Send messages and stream the response with live output."""
    opts, keep_alive = _get_coder_opts()
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": CODER_MODEL,
                "messages": messages,
                "stream": True,
                "options": opts,
                "keep_alive": keep_alive,  # ★ Unload after response
            },
            timeout=600,
            stream=True,
        )
        response.raise_for_status()

        full_response = []
        in_action = False

        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                token = data.get("message", {}).get("content", "")
                full_response.append(token)

                # Color code the output
                text_so_far = "".join(full_response)
                if "```ACTION" in text_so_far and not in_action:
                    in_action = True
                    sys.stdout.write(f"{C.GREEN}")
                elif in_action and "```" in token and text_so_far.count("```") > 2:
                    in_action = False
                    sys.stdout.write(f"{C.RESET}")

                sys.stdout.write(token)
                sys.stdout.flush()

                if data.get("done", False):
                    break
            except json.JSONDecodeError:
                continue

        print(f"{C.RESET}")  # Reset colors
        return "".join(full_response)

    except requests.exceptions.ConnectionError:
        print(f"\n{C.RED}❌ Cannot connect to Ollama at {OLLAMA_BASE_URL}{C.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{C.RED}❌ Ollama error: {e}{C.RESET}")
        sys.exit(1)


# ─── Log ────────────────────────────────────────────────────────
def log_step(iteration: int, tool_name: str, success: bool, summary: str):
    """Print a formatted step log."""
    icon = "✅" if success else "❌"
    color = C.GREEN if success else C.RED
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"\n{C.DIM}[{ts}]{C.RESET} {C.BOLD}Step {iteration}{C.RESET} │ "
          f"{color}{icon} {tool_name}{C.RESET} │ {summary[:80]}")


# ─── Main Agent Loop ────────────────────────────────────────────
def run_agent(goal: str, stream: bool = True):
    """Main autonomous agent execution loop."""
    banner()

    print(f"{C.YELLOW}{C.BOLD}📋 GOAL:{C.RESET} {goal}\n")
    print(f"{C.DIM}{'─' * 64}{C.RESET}\n")

    # Initialize conversation
    messages = [
        {"role": "system", "content": CODER_SYSTEM_PROMPT},
        {"role": "user", "content": get_goal_prompt(goal)},
    ]

    chat_fn = chat_with_ollama_stream if stream else chat_with_ollama

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n{C.CYAN}{C.BOLD}{'═' * 20} ITERATION {iteration}/{MAX_ITERATIONS} {'═' * 20}{C.RESET}\n")

        # Get model response
        response_text = chat_fn(messages)

        # Add assistant response to history
        messages.append({"role": "assistant", "content": response_text})

        # Parse action
        action = parse_action(response_text)

        if not action:
            print(f"\n{C.YELLOW}⚠ No ACTION block found. Asking model to provide one.{C.RESET}")
            messages.append({
                "role": "user",
                "content": "You did not output an ACTION block. Remember: every response MUST contain exactly one ```ACTION ... ``` block. Please provide your next action.",
            })
            continue

        tool_name = action["tool"]
        params = action["params"]

        # ─── Handle special tools ───────────────────────────────
        if tool_name == "done":
            summary = params.get("summary", "Task completed.")
            print(f"\n{C.GREEN}{C.BOLD}{'═' * 64}")
            print(f"  ✅ TASK COMPLETED")
            print(f"{'═' * 64}{C.RESET}")
            print(f"\n{summary}\n")
            log_step(iteration, "done", True, summary[:80])
            return True

        if tool_name == "ask_user":
            question = params.get("question", "Need more information.")
            print(f"\n{C.MAGENTA}{C.BOLD}❓ AGENT ASKS:{C.RESET} {question}\n")
            user_input = input(f"{C.MAGENTA}Your answer: {C.RESET}")
            messages.append({
                "role": "user",
                "content": get_observation_prompt("ask_user", f"User answered: {user_input}", True),
            })
            log_step(iteration, "ask_user", True, question[:60])
            continue

        if tool_name == "review":
            files_str = params.get("files", "")
            file_list = [f.strip() for f in files_str.strip().split("\n") if f.strip()]
            print(f"\n{C.BLUE}{C.BOLD}🔍 REVIEWING: {', '.join(file_list)}{C.RESET}")
            review_result = review_files(file_list)
            print(f"\n{C.BLUE}{review_result}{C.RESET}")
            messages.append({
                "role": "user",
                "content": get_observation_prompt("review", review_result, True),
            })
            log_step(iteration, "review", True, f"Reviewed {len(file_list)} files")
            continue

        # ─── Execute tool ───────────────────────────────────────
        print(f"\n{C.YELLOW}⚡ Executing: {tool_name}{C.RESET}")
        if tool_name == "run_command":
            print(f"   {C.DIM}$ {params.get('command', '?')}{C.RESET}")

        result = execute_tool(tool_name, params)

        # Log result
        log_step(iteration, tool_name, result["success"], result["output"][:80])

        # Print truncated output
        output_display = result["output"]
        if len(output_display) > 2000:
            output_display = output_display[:1000] + "\n... (truncated) ...\n" + output_display[-1000:]
        print(f"\n{C.DIM}{output_display}{C.RESET}")

        # Feed observation back to model
        messages.append({
            "role": "user",
            "content": get_observation_prompt(tool_name, result["output"], result["success"]),
        })

        # Trim conversation history if too long (keep system + last 30 messages)
        if len(messages) > 40:
            messages = [messages[0]] + messages[-30:]

    print(f"\n{C.RED}{C.BOLD}⚠ Reached maximum iterations ({MAX_ITERATIONS}). Stopping.{C.RESET}")
    return False


# ─── CLI Entry Point ────────────────────────────────────────────
def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="🤖 Autonomous Coding Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py "Create a FastAPI CRUD app with SQLite"
  python agent.py "Fix the bug in src/auth.py — login returns 500"
  python agent.py --no-stream "Add unit tests for the utils module"
  python agent.py --goal-file task.md
        """,
    )
    parser.add_argument(
        "goal",
        nargs="?",
        help="The coding goal/task to accomplish",
    )
    parser.add_argument(
        "--goal-file",
        help="Read goal from a file instead of command line",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming output (wait for full response)",
    )
    parser.add_argument(
        "--workspace",
        help="Set workspace directory (default: ./workspace)",
    )

    args = parser.parse_args()

    # Set workspace if provided
    if args.workspace:
        import config
        config.WORKSPACE_DIR = args.workspace

    # Get goal
    goal = None
    if args.goal_file:
        with open(args.goal_file, "r") as f:
            goal = f.read().strip()
    elif args.goal:
        goal = args.goal
    else:
        # Interactive mode
        banner()
        print(f"{C.CYAN}Enter your goal (press Enter twice to submit):{C.RESET}\n")
        lines = []
        while True:
            try:
                line = input()
                if line == "" and lines and lines[-1] == "":
                    break
                lines.append(line)
            except EOFError:
                break
        goal = "\n".join(lines).strip()

    if not goal:
        print(f"{C.RED}No goal provided. Exiting.{C.RESET}")
        sys.exit(1)

    # Check Ollama connection
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        r.raise_for_status()
        models = [m["name"] for m in r.json().get("models", [])]
        print(f"{C.DIM}Available models: {', '.join(models)}{C.RESET}")

        if not any(CODER_MODEL in m for m in models):
            print(f"{C.YELLOW}⚠ Model '{CODER_MODEL}' not found. Available: {', '.join(models)}{C.RESET}")
            print(f"{C.YELLOW}  Run: ollama pull {CODER_MODEL}{C.RESET}")
    except Exception:
        print(f"{C.RED}❌ Cannot connect to Ollama at {OLLAMA_BASE_URL}{C.RESET}")
        print(f"{C.YELLOW}   Start Ollama: ollama serve{C.RESET}")
        sys.exit(1)

    # Run agent
    success = run_agent(goal, stream=not args.no_stream)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
