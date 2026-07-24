"""Example code-review skill implementation.

This is a minimal placeholder that uses an LLM to review the diff. Replace it
with your own skill that reads the repo, runs CRG, etc.
"""
from typing import Dict, Any

from skills.cr_skill_interface import CodeReviewSkill
from src.dataset import format_diff
from src.llm_client import run_chat


class ExampleCrSkill(CodeReviewSkill):
    """A simple diff-only LLM reviewer."""

    def __init__(self, model: str = "gpt-4o", api_base: str = None, api_key: str = None):
        self.model = model
        self.api_base = api_base
        self.api_key = api_key

    def review_pr(self, item: Dict[str, Any]) -> str:
        prompt = (
            "You are a senior code reviewer. Review the following pull request.\n\n"
            f"Title: {item.get('pr_title', '')}\n\n"
            f"Description: {item.get('pr_statement', '')}\n\n"
            "Code Changes:\n"
            f"{format_diff(item)}\n\n"
            "Provide a concise, actionable code review. If you find no issues, "
            "explicitly state that the PR looks good. "
            "For each issue, mention the file path and a short description."
        )
        messages = [{"role": "user", "content": prompt}]
        return run_chat(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=4096,
            api_base=self.api_base,
            api_key=self.api_key,
            max_retries=2,
        ) or "No review generated."

    def name(self) -> str:
        return f"ExampleCrSkill({self.model})"
