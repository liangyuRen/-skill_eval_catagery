"""Interface for plugging your own code-review skill into the evaluator.

To use your own skill:

1. Create a subclass of `CodeReviewSkill` (e.g. `skills/my_cr_skill.py`).
2. Implement `review_pr(self, item) -> str` to return a markdown/string review.
3. In `run_eval.py`, replace `skill = ExampleCrSkill()` with `skill = MyCrSkill(...)`.

The input `item` is a raw dict from `swr_datasets_d5c5.jsonl`. It contains:
  - pr_title, pr_statement
  - pr_commits (with diff patches)
  - pr_timeline (review comments, commits, reviews)
  - base_commit, repo, instance_id
  - changes (ground truth; your skill should NOT read this)

The output should be a human-readable review report. It can be free text or
structured markdown. The judge will extract predicted points from it.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class CodeReviewSkill(ABC):
    """Abstract base class for a code-review skill."""

    @abstractmethod
    def review_pr(self, item: Dict[str, Any]) -> str:
        """Generate a code review for the given PR item.

        Args:
            item: A raw dataset instance from SWR-Bench.

        Returns:
            A string review report. It may include file paths, line numbers,
            issue descriptions, severity, and suggested fixes.
        """
        raise NotImplementedError

    def name(self) -> str:
        """Return the skill name for logging/results."""
        return self.__class__.__name__
