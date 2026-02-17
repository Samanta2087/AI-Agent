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

# ─── HYBRID VRAM OPTIMIZATION (For 16GB GPU) ──────────────────

# 32b Coder Model → Partial GPU Offload (To fit in 16GB)
CODER_OPTIONS = {
    "temperature": 0.15,
    "top_p": 0.85,
    "top_k": 30,
    "num_predict": 4096,
    "num_ctx": 4096,           # ★ Context 4k (16GB কার্ডে 8k ধরবে না)
    "num_gpu": 32,             # ★ কুইক লোডিং এর জন্য ৩২টি লেয়ার GPU-তে
    "main_gpu": 0,
    "num_thread": 4,           # ★ CPU + GPU কম্বিনেশন
    "num_batch": 128,          # ★ ছোট ব্যাচ মেমোরি বাঁচাবে
    "low_vram": True,          # ★ মাস্ট ট্রু হতে হবে ১৬জিবি-র জন্য
    "f16_kv": True,
}

# 14b Reviewer Model → CPU Only (To avoid GPU crash)
REVIEWER_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 1024,
    "num_ctx": 2048,
    "num_gpu": 0,              # ★ এটি CPU-তে চলবে যাতে 32b মডেলটি জায়গা পায়
    "num_thread": 8,
}


# Note: Web server (server.py) runs on CPU automatically.
# Python HTTP + SSE streaming = lightweight CPU work.
# All AI inference = GPU only.


