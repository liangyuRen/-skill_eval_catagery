# SWRBench

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SWRBench** (Software Review Benchmark) is a benchmark for evaluating AI systems on **automated pull request (PR) code review**.

Repository: [https://github.com/ZZR0/SWRench](https://github.com/ZZR0/SWRench) It provides a curated dataset of real GitHub PRs, multiple review baselines, and an LLM-as-a-judge evaluation pipeline.

Unlike benchmarks that focus on bug fixing (e.g., SWE-bench), SWRBench measures whether a model can **review code before merge**: detect real issues introduced by a PR, correctly approve clean PRs, and provide actionable feedback.

## Highlights

- **1,000 real PR instances** from 12 popular Python open-source projects
- **Balanced labels**: 500 PRs with reviewer-confirmed introduced changes, 500 clean PRs
- **Structured ground truth** with change categories, introducing commits, reviewer comments, and fix commits
- **Multiple review baselines**: prompt-based, iterative, PR-Agent-style, and agent-based approaches
- **Automated evaluation** using structured LLM judging with PR-level and point-level metrics

## Dataset

The main benchmark file is `data/swr_datasets_d5c5.jsonl` (JSONL format, one instance per line).

| Stat | Value |
|------|-------|
| Total instances | 1,000 |
| PRs with introduced changes | 500 |
| Clean PRs | 500 |
| Source repositories | 12 (e.g., scikit-learn, sympy, matplotlib, astropy) |

### Instance Fields

Each instance contains the following top-level fields:

| Field | Description |
|-------|-------------|
| `repo` | GitHub repository (e.g., `astropy/astropy`) |
| `instance_id` | Unique identifier (e.g., `astropy__astropy-187`) |
| `pr_title` | PR title |
| `pr_statement` | PR description |
| `change_introduced` | Core label: `true` if the PR introduced reviewer-confirmed issues; `false` for clean PRs |
| `base_commit` | Base commit SHA before merge |
| `created_at` | PR creation timestamp |
| `changes` | Ground-truth change list (empty for clean PRs) |
| `pr_commits` | Commits in the PR with structured diffs (main input for review models) |
| `pr_timeline` | Full PR timeline (commits, reviews, comments, review comments) |
| `all_commits` | Extended commit set including related commits outside the PR window |

### Ground-Truth Changes

For instances with `change_introduced=true`, each entry in `changes` includes:

- **`change_type`**: Category such as `F.2 Logic` (functional) or `E.3.2 Solution Approach` (evolvability)
- **`change_introducing`**: Commit SHA and code snippet that introduced the issue
- **`change_discussion`**: Reviewer comment, discussion summary, and first mention timestamp
- **`change_resolve_info`**: Fix commit, code snippet, and resolution explanation (may be absent for `F.6 Larger Defects`)

Change categories follow two top-level groups:

- **E (Evolvability)**: Documentation, formatting, structure, refactoring suggestions
- **F (Functional)**: Logic, interface, resource, validation, integration, and larger defects

## Project Structure

```
SWRBench-org/
├── data/                    # Benchmark dataset
├── swrbench/                # Core library
│   ├── generation.py        # Base / refine prompt review
│   ├── npr_review.py        # Iterative Native PR Review
│   ├── pr_agent.py          # PR-Agent-style review
│   ├── hybrid_review.py     # Hybrid review strategy
│   ├── evaluation_struct.py # LLM-as-judge evaluation (official)
│   ├── collect_repo_pr.py   # GitHub PR data collection
│   ├── collect_pr_review.py # Ground-truth annotation pipeline
│   └── build_dataset.py     # Dataset construction utilities
├── scripts/                 # Entry-point scripts
│   └── run.sh               # Unified runner for generation & evaluation
├── baselines/               # Third-party tools (PR-Agent, SWE-agent, etc.)
├── logs/                    # Experiment outputs
└── pyszz_v2/                # SZZ algorithm for bug-inducing commit detection (dataset construction)
```

## Installation

### Requirements

- Python 3.8+
- An OpenAI-compatible API endpoint (for review generation and evaluation)
- Docker (optional, required for `swr_agent` baseline)

### Python Dependencies

Install core dependencies:

```bash
pip install -r requirements.txt
```

For dataset construction and SZZ-based analysis, see `pyszz_v2/requirements.txt`.

### API Configuration

Set environment variables before running:

```bash
export OPENAI_API_BASE="https://your-api-endpoint/v1"
export OPENAI_API_KEY="your-api-key"
```

Multiple endpoints/keys can be provided as comma-separated lists for load balancing.

## Quick Start

### 1. Update the dataset path in `scripts/run.sh`

By default, `run.sh` points to an absolute path. Update it to your local dataset:

```bash
dataset=$workdir/data/swr_datasets_d5c5.jsonl
dataset_name=swr_datasets_d5c5
```

### 2. Generate reviews

```bash
bash scripts/run.sh gen <baseline> <model> <run_id>
```

**Example** — run PR-Agent-style review with Gemini:

```bash
bash scripts/run.sh gen pr_agent gemini-2.5-flash-preview PR-Agent/gemini-2.5-flash-preview
```

Output is written to `logs/<dataset_name>/<run_id>/generation.jsonl`.

### 3. Evaluate predictions

```bash
bash scripts/run.sh eval <judge_model> <run_id>
```

**Example**:

```bash
bash scripts/run.sh eval gemini-2.5-flash-preview-04-17 PR-Agent/gemini-2.5-flash-preview
```

Results are saved to `logs/<dataset_name>/<run_id>/evaluation__<judge_model>.json`.

## Review Baselines

| Baseline | Script | Description |
|----------|--------|-------------|
| `base_review` | `generation.py` | Single-turn LLM prompt review |
| `pr_agent` | `pr_agent.py` | PR-Agent-style diff-level review |
| `hybrid_review` | `hybrid_review.py` | Hybrid strategy combining diff extraction and agent logic |
| `npr_review` | `npr_review.py` | Iterative Native PR Review with token-budget management |
| `npr_refine_review` | `npr_review.py --refine` | NPR with refinement over prior reviews |
| `cr_agent` | `scripts/run_cr_agent.py` | CodeReviewAgent baseline |
| `swr_agent` | `scripts/run_swr_agent.py` | SWE-agent adapted for code review (requires Docker) |

### Direct Python Usage

You can also call scripts directly:

```bash
python swrbench/generation.py \
    --dataset-file data/swr_datasets_d5c5.jsonl \
    --model gemini-2.5-flash-preview \
    --output-file logs/my_run/generation.jsonl \
    --num-threads 32 \
    --temperature 0.2

python swrbench/evaluation_struct.py \
    --dataset-file data/swr_datasets_d5c5.jsonl \
    --pred-file logs/my_run/generation.jsonl \
    --output-file logs/my_run/evaluation.json \
    --model gemini-2.5-flash-preview-04-17 \
    --num-threads 32
```

Useful flags:

- `--instance-ids`: evaluate/generate only specific instances
- `--ignore-ids`: skip specific instances
- `--overwrite`: re-run evaluation from scratch (ignore cache)

## Evaluation

Evaluation is performed by `swrbench/evaluation_struct.py`, which uses an LLM judge with **structured JSON output** (JSON Schema via `response_format`).

### Metrics

**PR-level classification** (change vs. clean):

- Precision, Recall, F1, Accuracy

**Point-level matching** (predicted review points vs. ground-truth changes):

- TP / FP / FN at the review-point level
- Precision, Recall, F1 (`precision_point`, `recall_point`, `f1_point`)

**Clean PR analysis**:

- Whether the model correctly identifies the PR as good
- Severity of false-positive review points

**Breakdown by change type**:

- Separate statistics for E.* (evolvability) and F.* (functional) categories

The evaluation output JSON contains:

- `analysis_results`: aggregated metrics
- `details`: per-instance judge results

## Dataset Construction (Optional)

The repository includes tools to reproduce or extend the dataset:

1. **`collect_repo_pr.py`**: Fetch PR metadata, timelines, and diffs from GitHub (requires GitHub tokens)
2. **`collect_pr_review.py`**: LLM-assisted annotation of reviewer-discovered changes
3. **`build_dataset.py`**: Convert verified annotations into benchmark instances
4. **`pyszz_v2/`**: SZZ-based bug-inducing commit detection for fix-commit mining

These steps require additional data directories and API credentials beyond the released benchmark.

## Third-Party Baselines

The `baselines/` directory is intended for external tools:

- [PR-Agent](https://github.com/Codium-ai/pr-agent)
- [SWE-agent](https://github.com/SWE-agent/SWE-agent)
- CodeReviewAgent

Some baseline directories are excluded from git (see `.gitignore`) and must be cloned/set up separately before running `cr_agent`, `swr_agent`, or the standalone PR-Agent wrapper in `scripts/run_pr_agent.py`.

## Citation

If you use SWRBench in your research, please cite the project (bibtex to be added).

## License

This project is licensed under the [MIT License](LICENSE).
