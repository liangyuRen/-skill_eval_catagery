# CodeFuse-CR-Bench / SWE-CARE 真实样本结构说明

> 数据来源：官方仓库 [codefuse-ai/SWE-CARE](https://github.com/codefuse-ai/SWE-CARE)；完整数据集托管在 [HuggingFace inclusionAI/SWE-CARE](https://huggingface.co/datasets/inclusionAI/SWE-CARE)（本环境不可访问，未能下载真实数据样本）
> 论文：[arXiv:2509.14856](https://arxiv.org/abs/2509.14856)

## 1. 数据获取方式

```bash
# 方式一：HuggingFace（需能访问 HF）
from datasets import load_dataset
dataset = load_dataset("inclusionAI/SWE-CARE")

# 方式二：本地运行数据收集管线（需要 GitHub PAT）
git clone https://github.com/codefuse-ai/SWE-CARE.git
cd SWE-CARE
pip install uv
uv sync
# 按 README 中 "Data Collection" 步骤执行：get_top_repos → get_graphql_prs_data → classify_prs_data → build_code_review_dataset
```

本环境 HuggingFace 无法访问，因此未能在本地放置完整数据集或真实样本 JSON。**如需真实数据，请在能访问 HuggingFace 的网络环境下执行上述命令，或按仓库数据收集管线自行构建。**

## 2. 单条数据 schema（来自 `src/swe_care/schema/dataset.py`）

```python
@dataclass
class CodeReviewTaskInstance:
    instance_id: str                # 格式：owner__repo-{PR号}@{commit前7位}
    repo: str
    language: str
    pull_number: int
    title: str
    body: str
    created_at: str
    problem_statement: str          # 关联 issue 标题+正文
    hints_text: str
    resolved_issues: list[dict]     # [{number, title, body}, ...]
    base_commit: str
    commit_to_review: dict          # {head_commit, head_commit_message, patch_to_review}
    reference_review_comments: list[dict]   # 即 ground truth
    merged_commit: str
    merged_patch: str
    metadata: dict                  # {problem_domain, difficulty, estimated_review_effort(1-5)}
```

### GT 字段（`reference_review_comments[]` 每条）

```json
{
  "text": "<reviewer 评论原文>",
  "path": "src/...",
  "diff_hunk": "<diff hunk 文本>",
  "line": 147,
  "start_line": 140,
  "original_line": 145,
  "original_start_line": 140
}
```

## 3. 评估器：规则评估 + LLM 评估双层

来源：`src/swe_care/harness/evaluators/code_review.py`

### 3.1 RuleBasedEvaluator

- 先从预测 review 中抽取缺陷点，再与 reference comments 做贪心最佳匹配
- **位置相似度** = `path 精确匹配×0.7 + 行号接近度×0.15 + diff_hunk 行区间重叠率×0.15`
  - 行号接近度：同行 1.0，差 ≤5 行线性衰减，同文件远距离 0.1
- **描述相似度** = 4-gram BLEU（SmoothingFunction method4）
- **combined** = 0.5×位置 + 0.5×描述
  - `>0.1` 才算匹配
  - `>0.5` 计为 TP
  - 总分 = (F1 + 平均位置相似度 + 平均描述相似度) / 3

### 3.2 LLMEvaluator

按 4 个字段 × 5 个维度加权打分（0–1）：

| 字段 | 含义 |
|---|---|
| Functionality | 是否描述 patch 的功能、潜在功能或安全缺陷 |
| Quality | 代码质量描述准确性（复杂度、可读性、优化、可维护性） |
| Style | 是否遵循原始代码的命名/风格约定 |
| Documentation | 注释和文档是否清晰必要 |

| 维度 | 权重 | 含义 |
|---|---|---|
| Correctness | 0.3 | 技术上正确，无事实错误 |
| Relevance | 0.25 | 针对 issue、patch |
| Clarity | 0.2 | 清晰无冗余 |
| Consistency | 0.15 | 与 issue、代码库、patch 逻辑一致 |
| Language | 0.1 | 专业语言，便于知识传递 |

输出嵌套 JSON：
```json
{
  "function": {"correctness": 0.8, "relevance": 0.7, "clarity": 0.9, "consistency": 0.8, "language": 0.9},
  "quality": {...},
  "style": {...},
  "documentation": {...}
}
```

## 4. 已确认结论

- 规模：601 实例、70 个 Python 项目、9 个 PR 问题域
- 最强模型：**Gemini 2.5 Pro**（论文结论）
- 具体分数：本环境未下载到完整结果表

## 5. 对你们的借鉴

CodeFuse-CR-Bench 的 **RuleBasedEvaluator 权重设计**可以直接复用到你们的 Judge L1 定位匹配：

```
位置相似度 = path×0.7 + 行号接近×0.15 + hunk 重叠×0.15
combined   = 0.5×位置 + 0.5×语义（你们可用 embedding/LLM 替代 BLEU）
>0.5 计 TP
```

这比拍脑袋定阈值更有依据。
