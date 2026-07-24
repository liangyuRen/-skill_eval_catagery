"""Configuration for SWR-Bench skill evaluation."""
import os

# LLM client configuration for judge and optional baseline generation.
# Reads from environment variables; falls back to common defaults.
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Judge model used for hit-based evaluation.
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-2.5-flash-preview-04-17")
JUDGE_TEMPERATURE = float(os.getenv("JUDGE_TEMPERATURE", "0.0"))
JUDGE_MAX_TOKENS = int(os.getenv("JUDGE_MAX_TOKENS", "8192"))
JUDGE_MAX_RETRIES = int(os.getenv("JUDGE_MAX_RETRIES", "3"))

# Paths
DATASET_FILE = "data/swr_datasets_d5c5.jsonl"
PROMPT_DIR = "prompts"
RESULTS_DIR = "results"

# Evaluation behavior
DEFAULT_NUM_THREADS = int(os.getenv("DEFAULT_NUM_THREADS", "4"))
DEFAULT_SAMPLE_SIZE = os.getenv("DEFAULT_SAMPLE_SIZE")  # None means full dataset
