"""
Autonomous Coding Agent — Code Reviewer (Sequential GPU)
Uses qwen2.5-coder:14b to review code AFTER the coder model finishes.
Explicitly unloads coder model before loading reviewer, and vice versa.
"""
import requests
import time
from config import OLLAMA_BASE_URL, CODER_MODEL, REVIEWER_MODEL, REVIEWER_OPTIONS, WORKSPACE_DIR
from prompts import REVIEWER_SYSTEM_PROMPT, get_review_prompt
from tools import read_file


def _unload_model(model_name: str):
    """Force unload a model from GPU VRAM."""
    try:
        requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model_name, "keep_alive": 0},
            timeout=30,
        )
        time.sleep(2)  # Wait for VRAM to free up
    except Exception:
        pass


def _get_clean_options() -> dict:
    """Get reviewer options without keep_alive (it goes at top level)."""
    return {k: v for k, v in REVIEWER_OPTIONS.items() if k != "keep_alive"}


def review_files(file_paths: list[str]) -> str:
    """
    Send files to the reviewer model and get a structured review.
    SEQUENTIAL GPU FLOW:
      1. Unload coder model from GPU
      2. Load reviewer on GPU
      3. Run review
      4. Unload reviewer from GPU
    """
    # Read all files
    files_content = {}
    for path in file_paths:
        result = read_file(path)
        if result["success"]:
            content = result["output"].split("\n", 1)[-1] if "\n" in result["output"] else result["output"]
            files_content[path] = content
        else:
            files_content[path] = f"(could not read: {result['output']})"

    if not files_content:
        return "No files to review."

    # Build review prompt
    user_prompt = get_review_prompt(files_content)

    # ★ STEP 1: Unload coder model to free GPU VRAM
    _unload_model(CODER_MODEL)

    # ★ STEP 2: Call reviewer model (it will load into GPU)
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": REVIEWER_MODEL,
                "messages": [
                    {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
                "options": _get_clean_options(),
                "keep_alive": 0,  # Unload immediately after response
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        review_text = data.get("message", {}).get("content", "No review generated.")

    except requests.exceptions.ConnectionError:
        review_text = "❌ Cannot connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        review_text = "❌ Review timed out (300s). Try reviewing fewer files."
    except Exception as e:
        review_text = f"❌ Review failed: {e}"

    # ★ STEP 3: Unload reviewer to free GPU for coder
    _unload_model(REVIEWER_MODEL)

    return review_text


def review_diff(diff_text: str) -> str:
    """Review a diff/patch for quality. Sequential GPU usage."""
    # Unload coder first
    _unload_model(CODER_MODEL)

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": REVIEWER_MODEL,
                "messages": [
                    {"role": "system", "content": REVIEWER_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Review this code change:\n\n```diff\n{diff_text}\n```",
                    },
                ],
                "stream": False,
                "options": _get_clean_options(),
                "keep_alive": 0,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        result = data.get("message", {}).get("content", "No review generated.")
    except Exception as e:
        result = f"❌ Diff review failed: {e}"

    # Unload reviewer
    _unload_model(REVIEWER_MODEL)

    return result
