"""Metric computation for SWR-Bench-style evaluation."""
from typing import Dict, List, Any


def calculate_prf1(tp: int, fp: int, fn: int) -> Dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def analyze_one(result: Dict[str, Any], is_change: bool) -> Dict[str, Any]:
    """Compute per-PR metrics from a judge result."""
    pred_points = result.get("pred_points", [])
    pred_ids = {p["id"] for p in pred_points}

    if is_change:
        gt_points = result.get("gt_points", [])
        hit_by_ids = {gt["hit_by"] for gt in gt_points if gt.get("hit") == "YES" and gt.get("hit_by") in pred_ids}
        tp = len(hit_by_ids)
        fp = len(pred_ids - hit_by_ids)
        fn = len(gt_points) - len(hit_by_ids)
        return {
            "instance_id": result.get("instance_id"),
            "is_change": True,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            **calculate_prf1(tp, fp, fn),
            "pred_count": len(pred_points),
            "gt_count": len(gt_points),
            "identified_as_good": result.get("identified_as_good") == "YES",
            "severity_avg": sum(p.get("severity_score", 0) for p in pred_points) / len(pred_points) if pred_points else 0,
        }
    else:
        # Clean PR: every predicted point is a false positive.
        fp = len(pred_points)
        identified_as_good = result.get("identified_as_good") == "YES"
        return {
            "instance_id": result.get("instance_id"),
            "is_change": False,
            "tp": 0,
            "fp": fp,
            "fn": 0,
            "precision": 0.0,
            "recall": 0.0,
            "f1": 0.0,
            "pred_count": fp,
            "gt_count": 0,
            "identified_as_good": identified_as_good,
            "severity_avg": sum(p.get("severity_score", 0) for p in pred_points) / len(pred_points) if pred_points else 0,
        }


def aggregate_results(per_pr_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate per-PR metrics into overall report."""
    change_results = [r for r in per_pr_results if r.get("is_change")]
    clean_results = [r for r in per_pr_results if not r.get("is_change")]

    # Micro-average over all Change-PR points.
    tp_total = sum(r["tp"] for r in change_results)
    fp_total = sum(r["fp"] for r in change_results)
    fn_total = sum(r["fn"] for r in change_results)
    overall = calculate_prf1(tp_total, fp_total, fn_total)

    # Macro-average (mean of per-PR F1).
    macro_f1 = sum(r["f1"] for r in change_results) / len(change_results) if change_results else 0.0

    # False-positive rate on clean PRs.
    clean_fp_total = sum(r["fp"] for r in clean_results)
    clean_pr_count = len(clean_results)
    avg_fp_per_clean_pr = clean_fp_total / clean_pr_count if clean_pr_count else 0.0
    clean_identified_good_rate = sum(r["identified_as_good"] for r in clean_results) / clean_pr_count if clean_pr_count else 0.0

    return {
        "num_change_prs": len(change_results),
        "num_clean_prs": len(clean_results),
        "overall": {
            "tp": tp_total,
            "fp": fp_total,
            "fn": fn_total,
            **overall,
        },
        "macro_f1": round(macro_f1, 4),
        "false_positives": {
            "avg_fp_per_clean_pr": round(avg_fp_per_clean_pr, 4),
            "total_fp_on_clean_prs": clean_fp_total,
            "clean_pr_identified_as_good_rate": round(clean_identified_good_rate, 4),
        },
        "per_pr": per_pr_results,
    }
