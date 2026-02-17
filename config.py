"""
Autonomous Coding Agent — Configuration (Speed Optimized)
"""
import os

# ─── Ollama Connection ──────────────────────────────────────────
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# ─── Models ─────────────────────────────────────────────────────
CODER_MODEL = os.getenv("CODER_MODEL", "qwen2.5-coder:32b-instruct-q3_K_M")
REVIEWER_MODEL = os.getenv("REVIEWER_MODEL", "qwen2.5-coder:14b")

# ─── Workspace ──────────────────────────────────────────────────
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", os.path.join(os.getcwd(), "workspace"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "50"))
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "120"))  # seconds

# ─── Safety ─────────────────────────────────────────────────────
BLOCKED_COMMANDS = [
    "rm -rf /", "mkfs", "dd if=", ":(){:|:&};:",
    "chmod -R 777 /", "shutdown", "reboot", "halt",
    "poweroff", "init 0", "init 6",
]

ALLOWED_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
    ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".env",
    ".md", ".txt", ".rst", ".csv",
    ".sh", ".bash", ".zsh",
    ".sql", ".graphql",
    ".dockerfile", ".dockerignore", ".gitignore",
    ".go", ".rs", ".java", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".kt",
    ".xml", ".svg", ".lock", ".sum",
]

# ─── ALL AI MODELS → GPU | WEB SERVER → CPU ────────────────────

# 32b Coder Model → GPU (main heavy coding work)
CODER_OPTIONS = {
    "temperature": 0.15,
    "top_p": 0.85,
    "top_k": 30,
    "num_predict": 4096,
    "num_ctx": 8192,
    "repeat_penalty": 1.05,
    "num_gpu": 99,             # ★ ALL layers on GPU
    "main_gpu": 0,
    "num_thread": 1,           # ★ Minimal CPU (GPU handles inference)
    "num_batch": 512,
    "mirostat": 0,
    "low_vram": False,
    "f16_kv": True,
}

# 14b Reviewer Model → GPU (review work)
REVIEWER_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 2048,
    "num_ctx": 4096,
    "num_gpu": 99,             # ★ ALL layers on GPU
    "main_gpu": 0,
    "num_thread": 1,           # ★ Minimal CPU (GPU handles inference)
    "num_batch": 512,
    "f16_kv": True,
}

# Note: Web server (server.py) runs on CPU automatically.
# Python HTTP + SSE streaming = lightweight CPU work.
# All AI inference = GPU only.


