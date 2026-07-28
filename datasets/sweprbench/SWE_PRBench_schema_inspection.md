# SWE-PRBench 真实样本结构说明

> 数据来源：官方仓库 [FoundryHQ-AI/swe-prbench](https://github.com/FoundryHQ-AI/swe-prbench) 的 `eval_harness/schema.py` 与 `RUBRIC.md`；完整数据集托管在 [HuggingFace foundry-ai/swe-prbench](https://huggingface.co/datasets/foundry-ai/swe-prbench)（本环境不可访问，未能下载真实数据样本）
> 论文：[arXiv:2603.26130](https://arxiv.org/abs/2603.26130)

## 1. 数据获取方式

```bash
pip install huggingface-cli
huggingface-cli download foundry-ai/swe-prbench --local-dir ./swe-prbench-data
```

数据集布局：
```
swe-prbench-data/
├── prs.jsonl                          # PR 元数据
├── annotations/{task_id}_human.json   # 人工标注 GT
└── contexts/config_{A,B,C}/{task_id}.json  # 三种上下文配置
```

- `config_A`：仅 diff（diff-only）
- `config_B`：diff + 变更文件内容
- `config_C`：完整仓库上下文

本环境 HuggingFace 无法访问，所以未能在本地放置完整数据集或真实样本 JSON。**如需真实数据，请在能访问 HuggingFace 的网络环境下执行上述命令。**

## 2. 单条数据 schema（来自 `eval_harness/schema.py`）

### 输入：`EvalInput`

```python
@dataclass
class EvalInput:
    task_id: str
    pr_number: int
    repo: str
    config_name: str           # "A" / "B" / "C"
    rendered_context: str      # 实际喂给模型的文本（diff 或 diff+上下文）
    total_tokens: int
    pipeline_version: str      # 必须匹配 v0.4.1
    difficulty: str            # Type1_Direct / Type2_Contextual / Type3_Latent_Candidate
    pr_type: str
    language: str
    diff_patch: str            # 原始 diff patch
    human_comments: list[dict] # GT 评论
    has_severity_annotations: bool
```

### 人工评论字段（GT 内每条评论）

```python
{
  "comment_id": "...",
  "file": "src/...",
  "line": 147,
  "severity": "blocking|major|minor",
  "body": "<reviewer 评论原文>"
}
```

### 模型输出：`AgentOutput`

```python
@dataclass
class AgentOutput:
    task_id: str
    config_name: str
    model: str
    raw_response: str
    comments: list[AgentComment]
    parse_success: bool
    parse_error: str | None
```

```python
@dataclass
class AgentComment:
    comment_id: str
    body: str
    file_reference: str | None
    line_reference: int | None
    severity_claim: str | None
    is_outside_diff: bool
```

## 3. Judge 输出 schema

```python
@dataclass
class JudgeClassification:
    comment_id: str
    classification: str           # CONFIRMED / PLAUSIBLE / FABRICATED
    matched_human_comment_id: str | None
    actionability_score: int      # 1-5
    reasoning: str | None

@dataclass
class HumanCommentStatus:
    comment_id: str
    status: str                   # CAUGHT / MISSED
    matched_agent_comment_id: str | None
```

## 4. 评估指标（来自 `EvalResult`）

```python
detection_rate: float           # 召回类指标
false_positive_rate: float
severity_accuracy: float
actionability_score: float
semantic_alignment: float
adjacent_detection_rate: float
overall_score: float            # 论文 leaderboard 用的 Overall (s̄)
total_agent_comments: int
confirmed_count: int
plausible_count: int
fabricated_count: int
caught_human_comments: int
missed_human_comments: int
total_human_comments: int
precision: float
recall: float
f1_score: float
hallucination_rate: float
redundancy_penalty: float
plausible_penalty: float
fallback_penalty: float
```

## 5. Judge 判定标准（来自 `RUBRIC.md`）

- **CONFIRMED**：Agent 评论与人类 GT 指向同一底层问题，即使措辞、抽象层级或行号不同；partial 匹配也算
- **PLAUSIBLE**：Agent 评论合理且无事实错误，但 GT 里没有对应评论（即"额外正确"）
- **FABRICATED**：评论包含事实错误、引用 diff 中不存在的代码、或错误描述代码行为。**仅在确认事实错误时才判 FABRICATED，不在 GT 里不足以判 FABRICATED**

## 6. 论文基线效果（已核实）

| Rank | Model | Overall (s̄) | DR_A | FPR |
|------|-------|-------------|------|-----|
| 1 | Claude Haiku 4.5 | 0.153 | 0.306 | 0.346 |
| 2 | Claude Sonnet 4.6 | 0.152 | 0.297 | 0.227 |
| 3 | DeepSeek V3 | 0.150 | 0.312 | 0.315 |
| 4 | Mistral Large 3 | 0.147 | 0.305 | 0.353 |
| 5 | GPT-4o | 0.113 | 0.220 | 0.193 |
| 6 | GPT-4o-mini | 0.108 | 0.210 | 0.353 |
| 7 | Mistral Small | 0.106 | 0.257 | 0.251 |
| 8 | Llama 3.3 70B | 0.079 | 0.223 | 0.417 |

- Judge：GPT-5.2，temperature=0
- Pipeline：v0.4.1
- 评估子集：`evals/eval_100.json`

**核心结论**：即使是最好的 Claude Haiku 4.5，Overall 也只有 **0.153**（15.3%）；且 DR_A（diff-only 配置下的检出率）最高 0.312（DeepSeek V3），FPR 普遍 20%-40%。这再次验证 diff-only 是约束最强的输入条件。
