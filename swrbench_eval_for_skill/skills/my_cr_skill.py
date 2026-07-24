"""Template for your own code-review skill.

Replace the implementation in `review_pr()` with your real skill logic.

What you likely want to do here:
  1. Check out the repo at `item["base_commit"]` (or use the diff directly).
  2. Run your local agent / CRG tool to compute the impact radius.
  3. Apply your company's code-style and security rules.
  4. Return a structured review report.

The item dict contains all fields from `swr_datasets_d5c5.jsonl`:
  - instance_id, repo, base_commit, pr_title, pr_statement
  - pr_commits (with diff patches)
  - pr_timeline (review comments, commits, reviews)
  - changes (ground truth; do NOT peek for evaluation)
"""
from typing import Dict, Any

from skills.cr_skill_interface import CodeReviewSkill


class MyCrSkill(CodeReviewSkill):
    """Your business-specific code-review skill."""

    def __init__(self):
        # Load your agent/skill configuration here.
        pass

    def review_pr(self, item: Dict[str, Any]) -> str:
        """TODO: replace this stub with your real skill."""
        instance_id = item.get("instance_id", "")
        repo = item.get("repo", "")
        base_commit = item.get("base_commit", "")

        # Example skeleton of what your skill might do:
        # 1. Clone/checkout repo at base_commit.
        # 2. Apply the PR diff.
        # 3. Run CRG / static analysis to find impacted functions.
        # 4. Call your agent with company rules.
        # 5. Format the result as markdown.

        return (
            f"# Review for {instance_id}\n\n"
            f"This is a placeholder review for `{repo}` @ `{base_commit}`.\n\n"
            "Please implement `MyCrSkill.review_pr()` to invoke your real agent.\n"
        )

    def name(self) -> str:
        return "MyCrSkill"
