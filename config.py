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

# ─── GPU-ONLY Generation Parameters ─────────────────────────────
CODER_OPTIONS = {
    "temperature": 0.15,       # Lower = faster, more deterministic
    "top_p": 0.85,
    "top_k": 30,               # Limit token sampling for speed
    "num_predict": 4096,       # Enough for most actions
    "num_ctx": 8192,           # Balanced context window
    "repeat_penalty": 1.05,
    "num_gpu": 99,             # ★ ALL layers on GPU — no CPU inference
    "main_gpu": 0,             # ★ Use primary GPU (device 0)
    "num_thread": 1,           # ★ Minimal CPU threads (GPU handles everything)
    "num_batch": 512,          # ★ Larger batch = faster prompt processing on GPU
    "mirostat": 0,
    "low_vram": False,         # ★ Don't save VRAM — use full GPU memory for speed
    "f16_kv": True,            # ★ FP16 KV cache on GPU — faster + less VRAM
}

REVIEWER_OPTIONS = {
    "temperature": 0.3,
    "top_p": 0.9,
    "num_predict": 2048,
    "num_ctx": 4096,
    "num_gpu": 99,             # ★ ALL layers on GPU
    "main_gpu": 0,             # ★ Use primary GPU
    "num_thread": 1,           # ★ Minimal CPU threads
    "num_batch": 512,          # ★ Larger batch for speed
    "f16_kv": True,            # ★ FP16 KV cache
}
