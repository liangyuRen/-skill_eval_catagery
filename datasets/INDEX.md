# Code Review 基准数据集：本地全部资料索引

> 更新时间：2026-07-23 17:17
> 本目录：`C:/Users/rly/Desktop/skill_eval/datasets/`
> 说明：已将三个学术基准的仓库、论文、评测代码、SWR-Bench 完整数据集全部本地化。SWE-PRBench / CodeFuse 完整数据集因 HuggingFace 下载网络极不稳定，仅获取到部分样本，已记录状态。

---

## 目录结构速览

```
datasets/
├── README.md                      # 数据获取说明
├── INDEX.md                       # 本文件：全部本地资料索引
├── benchmark_results.md           # 各基准 AI review 效果数据
├── papers/                        # 论文 PDF（3/3 已下载）
│   ├── swrbench.pdf               # 1.7M
│   ├── sweprbench.pdf             # 599K
│   └── codefuse_cr.pdf            # 723K
├── swrbench/                      # SWR-Bench（完整数据集 + 样本 + 评测代码）
│   ├── repo/                      # 完整官方仓库（128M，含完整数据集）
│   ├── samples/                   # 抽取的真实样本
│   │   ├── change_pr.json         # 一条 Change-PR 完整样本
│   │   ├── clean_pr.json          # 一条 Clean-PR 完整样本
│   │   └── change_gt.json         # Change-PR 的 ground truth 单独抽出
│   ├── code/                      # 核心评测/数据收集代码
│   │   ├── evaluation_struct.py   # LLM Judge prompt（含 EVAL_CHANGE_PROMPT / EVAL_CLEAN_PROMPT）
│   │   ├── collect_pr_review.py   # 数据收集：从 PR 抽取 change-action GT
│   │   └── run_swr_agent.py       # Agent review 执行脚本 + 输入 prompt
│   └── SWRBench_sample_inspection.md  # 样本结构说明文档
├── sweprbench/                    # SWE-PRBench（仓库+代码完整，数据集部分下载）
│   ├── repo/                      # 完整官方仓库（评测 harness）
│   ├── code/                      # 核心代码与 rubric
│   │   ├── judge.py               # LLM Judge：CONFIRMED/PLAUSIBLE/FABRICATED 三分类完整 prompt
│   │   ├── schema.py              # 数据 schema
│   │   ├── run_eval.py            # 评测执行入口
│   │   └── RUBRIC.md              # 判定 rubric 原文
│   ├── data/                      # 部分下载的 HF 数据（见下方状态）
│   │   └── dataset/annotations/   # 76 条 human annotation JSON（约 1.4M）
│   ├── README_decoded.md          # 官方 README（含 leaderboard、HF 下载命令）
│   └── SWE_PRBench_schema_inspection.md  # schema 与效果总结
└── codefuse/                      # CodeFuse-CR-Bench / SWE-CARE（仓库+代码完整，数据集未下载）
    ├── repo/                      # 完整官方仓库
    ├── code/                      # 核心 schema、评估器、prompt 模板
    │   ├── dataset.py             # CodeReviewTaskInstance schema
    │   ├── code_review.py         # RuleBasedEvaluator + LLMEvaluator 实现
    │   ├── code_review_llm_evaluation.yaml  # LLM Judge prompt
    │   └── code_review_text_prompt.yaml     # 生成模型输入的 prompt 模板
    ├── data/                      # 仅 README（完整 parquet 未下载）
    ├── README_decoded.md          # 官方 README（含数据收集管线）
    └── CodeFuse_schema_inspection.md  # schema 与评估器权重说明
```

---

## 数据完整性状态

| 数据集 | 本地状态 | 文件数 | 大小 | 备注 |
|---|---|---|---|---|
| **SWR-Bench** | ✅ 完整 | 168 | 129M | 1000 PR 全量数据集 + 样本 + 代码 |
| **SWE-PRBench** | ⚠️ 部分 | 147 | 1.9M | 仓库+代码完整；annotations 下 76/350 条；contexts/prs.jsonl 未下 |
| **CodeFuse SWE-CARE** | ⚠️ 仅仓库 | 120 | 2.0M | 仓库+代码完整；dev/test parquet 未下 |
| **论文 PDF** | ✅ 完整 | 3 | 3.0M | 三篇论文全部下载成功 |

---

## SWR-Bench（数据最完整）

### 真实数据样本

| 文件 | 内容 | 大小 |
|---|---|---|
| `swrbench/samples/change_pr.json` | 一条 Change-PR 完整 JSON（含 GT、diff、时间线） | 126K |
| `swrbench/samples/clean_pr.json` | 一条 Clean-PR 完整 JSON（`change_introduced=false`） | 17K |
| `swrbench/samples/change_gt.json` | 上述 Change-PR 的 `changes[]` 单独抽出 | 3.8K |

### 完整数据集

- 位置：`swrbench/repo/data/swr_datasets_d5c5.jsonl`
- 规模：1000 条（500 Change + 500 Clean），约 81MB
- 覆盖：10 个 Python 项目，3927 个 commit
- 来源：官方仓库 [ZZR0/SWRench](https://github.com/ZZR0/SWRench)

### 核心代码 / Prompt

| 文件 | 作用 |
|---|---|
| `swrbench/code/evaluation_struct.py` | LLM Judge：含 `EVAL_CHANGE_PROMPT` 和 `EVAL_CLEAN_PROMPT` |
| `swrbench/code/collect_pr_review.py` | 数据收集：如何从 PR review 讨论中抽取 change-action GT |
| `swrbench/code/run_swr_agent.py` | 调用 Agent 对 PR 做 review 的脚本 + 输入 prompt |

### 已确认效果

- 最好 Overall-F1：**18.73%**（qodo PR-Review 基线）
- Judge 与人类判断 Kappa 最高：**86.7**（Gemini-2.5-Flash）

---

## SWE-PRBench（仓库+代码本地，数据集部分下载）

### 本地有的

| 文件 | 内容 |
|---|---|
| `sweprbench/repo/` | 完整评测 harness 仓库 |
| `sweprbench/code/judge.py` | LLM Judge：CONFIRMED / PLAUSIBLE / FABRICATED 三分类完整 prompt |
| `sweprbench/code/schema.py` | 数据 schema |
| `sweprbench/code/run_eval.py` | 评测执行入口 |
| `sweprbench/code/RUBRIC.md` | 判定 rubric |
| `sweprbench/data/dataset/annotations/` | 76 条真实 human annotation JSON（已可查看结构） |
| `sweprbench/README_decoded.md` | 官方 README（含 leaderboard、HF 下载命令） |
| `sweprbench/SWE_PRBench_schema_inspection.md` | schema 与三种 context 配置说明 |

### 本地未完整下载的

- `dataset/prs.jsonl`（28MB，PR 主数据）
- `dataset/contexts/config_{A,B,C}/`（三种上下文配置，各 350 条）
- 其余 `dataset/annotations/*.json`（350 - 76 = 274 条）

### 获取方式

```bash
# 方式一：HuggingFace 官方（需能访问 HF）
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
pip install -U hf-transfer
hf download foundry-ai/swe-prbench --repo-type dataset --local-dir ./sweprbench/data

# 方式二：hf-mirror 镜像（当前环境 SSL 极不稳定，需反复重试）
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export HF_ENDPOINT=https://hf-mirror.com
hf download foundry-ai/swe-prbench --repo-type dataset --local-dir ./sweprbench/data
```

### 已确认效果（leaderboard）

| Model | Overall (s̄) | DR_A | FPR |
|---|---|---|---|
| Claude Haiku 4.5 | **0.153** | 0.306 | 0.346 |
| Claude Sonnet 4.6 | 0.152 | 0.297 | 0.227 |
| DeepSeek V3 | 0.150 | **0.312** | 0.315 |
| GPT-4o | 0.113 | 0.220 | 0.193 |
| Llama 3.3 70B | 0.079 | 0.223 | 0.417 |

---

## CodeFuse-CR-Bench / SWE-CARE（仓库+代码本地，数据集未下载）

### 本地有的

| 文件 | 内容 |
|---|---|
| `codefuse/repo/` | 完整官方仓库 |
| `codefuse/code/dataset.py` | `CodeReviewTaskInstance` 数据 schema |
| `codefuse/code/code_review.py` | RuleBasedEvaluator（位置+BLEU 匹配）+ LLMEvaluator |
| `codefuse/code/code_review_llm_evaluation.yaml` | LLM Judge prompt（4 字段 × 5 维度） |
| `codefuse/code/code_review_text_prompt.yaml` | 生成模型输入的 prompt 模板 |
| `codefuse/README_decoded.md` | 官方 README（含数据收集管线） |
| `codefuse/CodeFuse_schema_inspection.md` | schema 与评估器权重说明 |

### 本地未下载的

- `data/dev-00000-of-00001.parquet`（125MB）
- `data/test-00000-of-00001.parquet`（12MB）

### 获取方式

```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
hf download inclusionAI/SWE-CARE --repo-type dataset --local-dir ./codefuse/data
```

### 已确认效果

- 规模：601 实例、70 Python 项目、9 问题域
- 最强模型：**Gemini 2.5 Pro**

---

## 论文 PDF（3/3 已下载）

| 文件 | 论文 | 大小 |
|---|---|---|
| `papers/swrbench.pdf` | SWR-Bench, arXiv:2509.01494 | 1.7M |
| `papers/sweprbench.pdf` | SWE-PRBench, arXiv:2603.26130 | 599K |
| `papers/codefuse_cr.pdf` | CodeFuse-CR-Bench, arXiv:2509.14856 | 723K |

---

## 辅助下载脚本（项目根目录）

| 文件 | 作用 |
|---|---|
| `download_with_retry.py` | 带代理+重试的单文件下载脚本（用于 arXiv PDF） |
| `download_datasets.py` | 遍历 HF dataset 全量下载脚本（因 SSL 不稳定已暂停） |

---

## 推荐查看顺序

1. 先看样本：`swrbench/samples/change_pr.json` + `clean_pr.json`
2. 再看 SWE-PRBench 的 annotation 结构：`sweprbench/data/dataset/annotations/accelerate__3890_human.json`
3. 再看 schema：`sweprbench/code/schema.py` + `codefuse/code/dataset.py`
4. 再看 Judge prompt：`swrbench/code/evaluation_struct.py`、`sweprbench/code/judge.py`、`codefuse/code/code_review_llm_evaluation.yaml`
5. 最后看效果：`datasets/benchmark_results.md`
