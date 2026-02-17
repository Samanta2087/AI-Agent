"""
Autonomous Coding Agent — Configuration
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
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "120"))

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

# ─── GPU + CPU HYBRID (Partial Offload for 16GB GPU) ────────────

# 32b Coder → 40 layers on GPU (~10GB), rest on CPU RAM
CODER_OPTIONS = {
    "temperature": 0.15,
    "top_p": 0.85,
    "top_k": 30,
    "num_predict": 4096,
    "num_ctx": 4096,           # Moderate context (saves VRAM for layers)
    "num_gpu": 40,             # ★ 40 layers GPU, ~25 layers CPU
    "num_thread": 8,           # ★ CPU threads for the CPU layers
}

# 14b Reviewer → 40 layers on GPU (~6GB), rest on CPU
REVIEWER_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 2048,
    "num_ctx": 2048,
    "num_gpu": 40,             # ★ Partial GPU offload
    "num_thread": 8,
}

# Unload model after response to free VRAM for the other model
KEEP_ALIVE = 0
