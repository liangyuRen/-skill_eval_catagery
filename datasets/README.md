# Code Review 基准数据集：本地获取说明

> 更新时间：2026-07-23
> 工作目录：`C:/Users/rly/Desktop/skill_eval/datasets/`
> **全部本地资料索引见 `INDEX.md`**

---

## SWR-Bench（完整仓库+完整数据已本地）

- **论文**：SWR-Bench: Assessing LLM Performance in Real-World Code Review Comment Generation，PACMSE/FSE 2026
- **arXiv**：[2509.01494](https://arxiv.org/abs/2509.01494)
- **官方仓库**：[ZZR0/SWRench](https://github.com/ZZR0/SWRench)
- **完整数据集**：`swrbench/repo/data/swr_datasets_d5c5.jsonl`（81MB，1000 条）

**本地样本**：
- `swrbench/samples/change_pr.json` — 一条 Change-PR
- `swrbench/samples/clean_pr.json` — 一条 Clean-PR
- `swrbench/samples/change_gt.json` — GT 单独抽出

**本地代码/Prompt**：
- `swrbench/code/evaluation_struct.py` — Judge prompt
- `swrbench/code/collect_pr_review.py` — 数据收集
- `swrbench/code/run_swr_agent.py` — Agent 执行脚本

---

## SWE-PRBench（仓库+代码已本地；数据集在 HuggingFace）

- **论文**：[arXiv:2603.26130](https://arxiv.org/abs/2603.26130)
- **官方仓库**：[FoundryHQ-AI/swe-prbench](https://github.com/FoundryHQ-AI/swe-prbench)
- **数据集**：[HuggingFace foundry-ai/swe-prbench](https://huggingface.co/datasets/foundry-ai/swe-prbench)

**本地已有**：完整仓库 `sweprbench/repo/`；核心代码 `sweprbench/code/`（judge.py、schema.py、run_eval.py、RUBRIC.md）；官方 README 解码版。

**获取完整数据集**：
```bash
pip install huggingface-cli
huggingface-cli download foundry-ai/swe-prbench --local-dir ./swe-prbench-data
```

---

## CodeFuse-CR-Bench / SWE-CARE（仓库+代码已本地；数据集在 HuggingFace）

- **论文**：[arXiv:2509.14856](https://arxiv.org/abs/2509.14856)
- **官方仓库**：[codefuse-ai/SWE-CARE](https://github.com/codefuse-ai/SWE-CARE)
- **数据集**：[HuggingFace inclusionAI/SWE-CARE](https://huggingface.co/datasets/inclusionAI/SWE-CARE)

**本地已有**：完整仓库 `codefuse/repo/`；核心代码 `codefuse/code/`（dataset.py、code_review.py、prompt YAML）。

**获取完整数据集**：
```python
from datasets import load_dataset
dataset = load_dataset("inclusionAI/SWE-CARE")
```

---

## 论文 PDF（后台下载中）

见 `datasets/papers/`，包含：
- `swrbench.pdf`（arXiv:2509.01494）
- `sweprbench.pdf`（arXiv:2603.26130）
- `codefuse_cr.pdf`（arXiv:2509.14856）

---

## 效果数据

见 `datasets/benchmark_results.md`

---

## 完整文件索引

见 `datasets/INDEX.md`
