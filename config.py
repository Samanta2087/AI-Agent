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

# ─── SPEED OPTIMIZED Generation Parameters ─────────────────────
CODER_OPTIONS = {
    "temperature": 0.15,       # Lower = faster, more deterministic
    "top_p": 0.85,
    "top_k": 30,               # Limit token sampling for speed
    "num_predict": 4096,       # Reduced from 8192 — still enough for most actions
    "num_ctx": 8192,           # Reduced from 16384 — big speed improvement
    "repeat_penalty": 1.05,    # Slightly lower for speed
    "num_gpu": 99,             # Offload all layers to GPU
    "num_thread": 8,           # Use multiple CPU threads
    "mirostat": 0,             # Disable mirostat for speed
}

REVIEWER_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 2048,
    "num_ctx": 4096,
    "num_gpu": 99,
    "num_thread": 8,
}
