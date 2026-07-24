"""Static smoke tests for the evaluation framework.

This script does not call any LLM. It verifies that the dataset, prompts,
formatting, and metrics computation work end-to-end with mocked judge output.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.dataset import load_jsonl, format_diff, format_ground_truth_changes, is_clean_pr
from src.judge import _build_change_prompt, _build_clean_prompt
from src.metrics import analyze_one, aggregate_results


def test_dataset_load():
    dataset = load_jsonl("data/swr_datasets_d5c5.jsonl")
    assert len(dataset) == 1000, f"Expected 1000 items, got {len(dataset)}"
    print(f"✅ Dataset loaded: {len(dataset)} items")


def test_formatting():
    dataset = load_jsonl("data/swr_datasets_d5c5.jsonl")
    item = dataset[0]
    diff_text = format_diff(item)
    assert len(diff_text) > 0, "Diff formatting produced empty string"
    gt_text = format_ground_truth_changes(item)
    print(f"✅ Diff formatted ({len(diff_text)} chars), GT changes: {len(item.get('changes', []))}")


def test_prompts_build():
    dataset = load_jsonl("data/swr_datasets_d5c5.jsonl")
    change_item = next(d for d in dataset if not is_clean_pr(d))
    clean_item = next(d for d in dataset if is_clean_pr(d))

    change_prompt = _build_change_prompt(change_item, "This PR has a logic bug in foo.py.")
    clean_prompt = _build_clean_prompt(clean_item, "LGTM, no issues found.")

    assert "GT-POINT-1" in change_prompt, "GT points not inserted into change prompt"
    assert "PredictedReview" in clean_prompt, "PredictedReview tag missing in clean prompt"
    print("✅ Change and clean judge prompts build successfully")


def test_metrics():
    # Mock judge results.
    change_result = {
        "instance_id": "test-change",
        "pred_points": [
            {"id": "PRED-POINT-1", "description": "Logic bug", "change_category": "F.2", "severity_score": 7},
            {"id": "PRED-POINT-2", "description": "Style issue", "change_category": "E.2", "severity_score": 3},
        ],
        "gt_points": [
            {"id": "GT-POINT-1", "description": "Logic bug", "change_category": "F.2", "hit": "YES", "hit_by": "PRED-POINT-1"},
            {"id": "GT-POINT-2", "description": "Missing check", "change_category": "F.4", "hit": "NO", "hit_by": "N/A"},
        ],
        "identified_as_good": "NO",
    }
    clean_result = {
        "instance_id": "test-clean",
        "pred_points": [
            {"id": "PRED-POINT-1", "description": "False alarm", "change_category": "E.1.1", "severity_score": 2},
        ],
        "identified_as_good": "NO",
    }

    per_pr = [analyze_one(change_result, is_change=True), analyze_one(clean_result, is_change=False)]
    report = aggregate_results(per_pr)

    assert report["overall"]["tp"] == 1, report
    assert report["overall"]["fp"] == 1, report  # only PRED-POINT-2 on change-PR
    assert report["overall"]["fn"] == 1, report
    assert report["false_positives"]["total_fp_on_clean_prs"] == 1, report
    print(f"✅ Metrics computed: overall={report['overall']}, fp={report['false_positives']}")


if __name__ == "__main__":
    test_dataset_load()
    test_formatting()
    test_prompts_build()
    test_metrics()
    print("\n🎉 All smoke tests passed.")
