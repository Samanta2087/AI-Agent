"""
Autonomous Coding Agent — Code Reviewer
Uses qwen2.5-coder:14b to review code produced by the main agent.
"""
import requests
from config import OLLAMA_BASE_URL, REVIEWER_MODEL, REVIEWER_OPTIONS, WORKSPACE_DIR
from prompts import REVIEWER_SYSTEM_PROMPT, get_review_prompt
from tools import read_file


def review_files(file_paths: list[str]) -> str:
    """
    Send files to the reviewer model and get a structured review.
    Returns the review text.
    """
    # Read all files
    files_content = {}
    for path in file_paths:
        result = read_file(path)
        if result["success"]:
            # Remove the header line
            content = result["output"].split("\n", 1)[-1] if "\n" in result["output"] else result["output"]
            files_content[path] = content
        else:
            files_content[path] = f"(could not read: {result['output']})"

    if not files_content:
        return "No files to review."

    # Build review prompt
    user_prompt = get_review_prompt(files_content)

    # Call reviewer model
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
                "options": REVIEWER_OPTIONS,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "No review generated.")

    except requests.exceptions.ConnectionError:
        return "❌ Cannot connect to Ollama. Is it running?"
    except requests.exceptions.Timeout:
        return "❌ Review timed out (300s). Try reviewing fewer files."
    except Exception as e:
        return f"❌ Review failed: {e}"


def review_diff(diff_text: str) -> str:
    """Review a diff/patch for quality."""
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
                "options": REVIEWER_OPTIONS,
            },
            timeout=300,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "No review generated.")
    except Exception as e:
        return f"❌ Diff review failed: {e}"
