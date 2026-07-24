"""Main evaluation runner for code-review skills on SWR-Bench.

Usage:
    # Run with the example skill on a small sample (recommended first)
    python run_eval.py --skill example --sample 10 --output results/example_sample10.json

    # Run your own skill
    python run_eval.py --skill my --sample 50 --output results/my_skill.json

    # Full evaluation (1000 PRs, expensive)
    python run_eval.py --skill my --output results/my_skill_full.json

    # Skip generation, evaluate existing review file
    python run_eval.py --reviews-file results/example_reviews.jsonl --output results/example_eval.json
"""
import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, Any, List

from loguru import logger

# Ensure project root is on path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import config
from src.dataset import load_jsonl, save_jsonl, is_clean_pr
from src.judge import judge_pr
from src.metrics import analyze_one, aggregate_results

# Import available skills.
from skills import ExampleCrSkill
from skills.my_cr_skill import MyCrSkill


SKILL_MAP = {
    "example": ExampleCrSkill,
    "my": MyCrSkill,
}


def generate_reviews(skill, dataset: List[Dict[str, Any]], num_threads: int = 1) -> List[Dict[str, Any]]:
    """Generate reviews for all PRs using the provided skill."""
    results = []

    def _review_one(item: Dict[str, Any]) -> Dict[str, Any]:
        instance_id = item.get("instance_id")
        logger.info(f"Reviewing {instance_id} ...")
        try:
            review = skill.review_pr(item)
        except Exception as e:
            logger.error(f"Skill failed on {instance_id}: {e}")
            review = f"[ERROR] {e}"
        return {
            "instance_id": instance_id,
            "skill": skill.name(),
            "review": review,
        }

    if num_threads <= 1:
        for item in dataset:
            results.append(_review_one(item))
    else:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(_review_one, item): item for item in dataset}
            for future in as_completed(futures):
                results.append(future.result())

    return results


def run_judge(reviews: List[Dict[str, Any]], dataset: List[Dict[str, Any]], num_threads: int = 1) -> List[Dict[str, Any]]:
    """Run judge on all generated reviews."""
    dataset_by_id = {item["instance_id"]: item for item in dataset}
    judge_results = []

    def _judge_one(review_entry: Dict[str, Any]) -> Dict[str, Any]:
        instance_id = review_entry["instance_id"]
        item = dataset_by_id.get(instance_id)
        if item is None:
            logger.error(f"Dataset item not found for {instance_id}")
            return None

        logger.info(f"Judging {instance_id} ...")
        result = judge_pr(item, review_entry["review"])
        if result is None:
            return None

        result["instance_id"] = instance_id
        result["review"] = review_entry["review"]
        return result

    if num_threads <= 1:
        for entry in reviews:
            res = _judge_one(entry)
            if res:
                judge_results.append(res)
    else:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = {executor.submit(_judge_one, entry): entry for entry in reviews}
            for future in as_completed(futures):
                res = future.result()
                if res:
                    judge_results.append(res)

    return judge_results


def main():
    parser = argparse.ArgumentParser(description="Evaluate a code-review skill on SWR-Bench.")
    parser.add_argument("--skill", choices=list(SKILL_MAP.keys()), default="example",
                        help="Which skill to evaluate.")
    parser.add_argument("--reviews-file", type=str, default=None,
                        help="Path to pre-generated reviews (JSONL). Skips generation.")
    parser.add_argument("--output", type=str, default="results/eval_result.json",
                        help="Path to write evaluation report.")
    parser.add_argument("--sample", type=int, default=None,
                        help="Evaluate on first N PRs only (for quick testing).")
    parser.add_argument("--num-threads", type=int, default=config.DEFAULT_NUM_THREADS,
                        help="Parallelism for generation and judging.")
    parser.add_argument("--model", type=str, default=None,
                        help="Override LLM model for the example skill.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or "results", exist_ok=True)

    # Load dataset.
    logger.info(f"Loading dataset from {config.DATASET_FILE}")
    dataset = load_jsonl(config.DATASET_FILE)
    if args.sample:
        dataset = dataset[:args.sample]
        logger.info(f"Using sample of {len(dataset)} PRs")

    # Load or generate reviews.
    if args.reviews_file:
        logger.info(f"Loading reviews from {args.reviews_file}")
        reviews = load_jsonl(args.reviews_file)
    else:
        skill_cls = SKILL_MAP[args.skill]
        skill_kwargs = {}
        if args.model and args.skill == "example":
            skill_kwargs["model"] = args.model
        skill = skill_cls(**skill_kwargs)
        logger.info(f"Generating reviews with skill: {skill.name()}")
        reviews = generate_reviews(skill, dataset, num_threads=args.num_threads)
        review_output = args.output.replace(".json", "_reviews.jsonl")
        save_jsonl(review_output, reviews)
        logger.info(f"Saved generated reviews to {review_output}")

    # Run judge.
    logger.info("Running judge...")
    judge_results = run_judge(reviews, dataset, num_threads=args.num_threads)

    # Compute metrics.
    per_pr = []
    for res in judge_results:
        item = next((d for d in dataset if d["instance_id"] == res["instance_id"]), None)
        if item is None:
            continue
        per_pr.append(analyze_one(res, is_change=not is_clean_pr(item)))

    report = aggregate_results(per_pr)
    report["meta"] = {
        "skill": args.skill,
        "sample_size": len(dataset),
        "judge_model": config.JUDGE_MODEL,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"Evaluation complete. Report saved to {args.output}")
    print(json.dumps(report["overall"], indent=2))
    print(json.dumps(report["false_positives"], indent=2))


if __name__ == "__main__":
    main()
