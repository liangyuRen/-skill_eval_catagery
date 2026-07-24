"""Dataset loading and formatting utilities."""
import json
from typing import Dict, List, Any


def load_jsonl(path: str) -> List[Dict[str, Any]]:
    """Load a JSONL file."""
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def save_jsonl(path: str, data: List[Dict[str, Any]]) -> None:
    """Save a list of dicts as JSONL."""
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def format_diff(item: Dict[str, Any]) -> str:
    """Format all commits' diffs into a single string."""
    parts = []
    for commit in item.get("pr_commits", []):
        parts.append(f"Commit: {commit.get('sha', '')}")
        parts.append(f"Message: {commit.get('message', '')}")
        parts.append("Code Changes:")
        for diff in commit.get("diff", []):
            parts.append(f"File: {diff.get('file', '')}")
            parts.append("```")
            parts.append(diff.get("patch", ""))
            parts.append("```")
    return "\n".join(parts)


def format_timeline(item: Dict[str, Any]) -> str:
    """Format PR timeline as context string."""
    parts = []
    for event in item.get("pr_timeline", []):
        etype = event.get("type", "")
        if etype == "description":
            continue
        elif etype == "comment":
            parts.append(
                f"<Comment by {event.get('user', '')} at {event.get('created_at', '')}>\n"
                f"{event.get('body', '')}\n</Comment>"
            )
        elif etype == "review_comment":
            parts.append(
                f"<ReviewComment file={event.get('path', '')}>\n"
                f"{event.get('diff_hunk', '')}\n"
                f"{event.get('body', '')}\n</ReviewComment>"
            )
        elif etype == "commit":
            parts.append(
                f"<Commit {event.get('sha', '')}>\n{event.get('message', '')}\n</Commit>"
            )
        elif etype == "review":
            parts.append(
                f"<Review by {event.get('user', '')}>\n"
                f"{event.get('body', '')}\n</Review>"
            )
    return "\n\n".join(parts)


def format_ground_truth_changes(item: Dict[str, Any]) -> str:
    """Format ground-truth changes for the judge prompt."""
    parts = []
    for i, change in enumerate(item.get("changes", [])):
        ct = change.get("change_type", "")
        disc = change.get("change_discussion", {})
        intro = change.get("change_introducing", {})
        parts.append(
            f"        <Ground Truth Change GT-POINT-{i + 1}>\n"
            f"            Change Category: {ct}\n"
            f"            Change Description: {disc.get('discussion_summary', '')}\n"
            f"            Change Code Snippet: {intro.get('code_snippet', '')}\n"
            f"        </Ground Truth Change GT-POINT-{i + 1}>\n"
        )
    return "\n".join(parts)


def is_clean_pr(item: Dict[str, Any]) -> bool:
    """Return True if this is a clean PR (no changes)."""
    return len(item.get("changes", [])) == 0
