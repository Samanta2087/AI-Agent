# 🤖 Autonomous Coding Agent

A fully autonomous AI coding agent that runs on your VPS using **Ollama** with local Qwen 2.5 Coder models.

## Features

| Feature | Description |
|---------|-------------|
| 🎯 **Goal-driven** | Give it a task, it executes autonomously |
| 📝 **Plan creation** | Breaks goals into numbered action plans |
| 📄 **File creation** | Creates new files with full content |
| ✏️ **Diff-based editing** | Edits files using unified diff (minimal changes) |
| 🧪 **Test execution** | Runs commands and reads output |
| 🐛 **Error fixing** | Reads errors, analyzes root cause, creates patches |
| 🔄 **Autonomous loop** | Repeats until task is complete |
| 📦 **Git tracking** | Auto-commits with meaningful messages |
| 🔍 **Code review** | Uses 14b model to review code quality |
| 🌐 **Web UI** | Beautiful browser interface with live streaming |
| 🔒 **Sandboxed** | All operations confined to workspace directory |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    USER (CLI / Web)                  │
├─────────────────────────────────────────────────────┤
│                   agent.py / server.py               │
│          (Main loop — parse actions — execute)       │
├──────────────────┬──────────────────────────────────┤
│   prompts.py     │         tools.py                  │
│   (System        │   (create_file, edit_file,        │
│    prompts)      │    run_command, git, search)       │
├──────────────────┼──────────────────────────────────┤
│  reviewer.py     │         config.py                 │
│  (14b review)    │   (Models, paths, safety)         │
├──────────────────┴──────────────────────────────────┤
│                    Ollama API                        │
│        qwen2.5-coder:32b (coding)                   │
│        qwen2.5-coder:14b (review)                   │
└─────────────────────────────────────────────────────┘
```

## Models Used

| Model | Role | Purpose |
|-------|------|---------|
| `qwen2.5-coder:32b-instruct-q3_K_M` | Coder | Main coding agent — plans, writes, edits, debugs |
| `qwen2.5-coder:14b` | Reviewer | Reviews code for bugs, security, best practices |

## Quick Start (VPS)

### 1. Upload files to your VPS

```bash
scp -r ./* user@your-vps:/opt/coding-agent/
```

### 2. Run the setup script

```bash
ssh user@your-vps
cd /opt/coding-agent
chmod +x start.sh
./start.sh
```

The script will:
- ✅ Check Python 3 installation
- ✅ Check/install Ollama
- ✅ Pull required models
- ✅ Install Python dependencies
- ✅ Create workspace directory
- ✅ Launch in CLI or Web mode

### 3. Use CLI Mode

```bash
# Direct goal
python3 agent.py "Create a FastAPI REST API with user authentication"

# Goal from file
python3 agent.py --goal-file task.md

# Interactive (type goal when prompted)
python3 agent.py

# Custom workspace
python3 agent.py --workspace /home/user/myproject "Add unit tests"
```

### 4. Use Web Mode

```bash
python3 server.py
# Open browser: http://your-vps-ip:8080
```

## File Structure

```
coding-agent/
├── agent.py          # Main autonomous agent loop (CLI)
├── server.py         # Web server with SSE streaming
├── web_ui.py         # Web interface HTML/CSS/JS
├── tools.py          # Tool implementations
├── prompts.py        # System prompts for both models
├── reviewer.py       # Code review pipeline
├── config.py         # Configuration
├── requirements.txt  # Python dependencies
├── start.sh          # VPS setup & launch script
├── README.md         # This file
└── workspace/        # Agent's sandbox (created automatically)
```

## How It Works

1. **You give a GOAL** → `"Create a Flask blog with SQLite"`
2. **Agent THINKS** → Analyzes requirements, identifies tech stack
3. **Agent PLANS** → Creates numbered step-by-step plan
4. **Agent ACTS** → Executes ONE action per turn:
   - `create_file` — Creates new files
   - `edit_file` — Applies unified diff patches
   - `read_file` — Reads file contents
   - `run_command` — Executes shell commands
   - `search_files` — Grep-like search
   - `git` — Git add/commit/etc
   - `review` — Sends code to 14b reviewer
5. **Agent OBSERVES** → Reads the result (success/error)
6. **Agent LOOPS** → Repeats until all tests pass
7. **Agent COMMITS** → Git commits with meaningful message
8. **Agent DONE** → Reports completion summary

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_URL` | `http://localhost:11434` | Ollama API URL |
| `CODER_MODEL` | `qwen2.5-coder:32b-instruct-q3_K_M` | Coding model |
| `REVIEWER_MODEL` | `qwen2.5-coder:14b` | Review model |
| `WORKSPACE_DIR` | `./workspace` | Sandbox directory |
| `MAX_ITERATIONS` | `50` | Max agent iterations |
| `COMMAND_TIMEOUT` | `120` | Shell command timeout (sec) |
| `WEB_PORT` | `8080` | Web UI port |

### Custom Configuration

```bash
# Example: Use different models and port
export CODER_MODEL="qwen2.5-coder:32b-instruct"
export REVIEWER_MODEL="qwen2.5-coder:7b"
export WEB_PORT=3000
python3 agent.py "Build a todo app"
```

## Safety Features

- 🔒 **Path traversal protection** — Cannot access files outside workspace
- 🚫 **Dangerous command blocking** — Blocks `rm -rf /`, `mkfs`, etc.
- ⏱️ **Command timeout** — Auto-kills hung processes
- 📏 **Output truncation** — Prevents memory exhaustion
- 🔄 **Iteration limit** — Prevents infinite loops
- 📁 **Sandboxed workspace** — All operations in isolated directory

## Example Goals

```
"Create a Python CLI tool that converts CSV to JSON with error handling"

"Build a FastAPI REST API with:
- User registration and JWT login
- CRUD for blog posts
- SQLite with SQLAlchemy
- Unit tests with pytest"

"Fix the TypeError in src/parser.py line 42 — handle None input"

"Refactor the monolith in app.py into clean modules:
- routes/
- models/
- services/
- Add proper error handling"

"Add Docker support:
- Dockerfile (multi-stage build)
- docker-compose.yml
- .dockerignore
- Health check endpoint"
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `Cannot connect to Ollama` | Run `ollama serve` first |
| `Model not found` | Run `ollama pull qwen2.5-coder:32b-instruct-q3_K_M` |
| `No ACTION block found` | Model sometimes misformats — agent auto-retries |
| `Diff failed to apply` | Fuzzy matching handles most cases; model retries on failure |
| `Timeout` | Increase `COMMAND_TIMEOUT` or simplify the goal |
| `Max iterations reached` | Increase `MAX_ITERATIONS` or break goal into smaller tasks |

## License

MIT — Use freely.
