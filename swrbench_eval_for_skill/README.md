# SWR-Bench 业务 CR Skill 评测框架

这个目录是一个完整的、独立的评测框架，用来把你的 **code review skill** 放在 **SWR-Bench** 数据集上跑，算出：

- **召回率（Recall）**：真实问题里有多少被你找到了
- **精确率（Precision）**：你报的问题里有多少是真的
- **F1 Score**
- **误报率 / 平均每个 Clean-PR 的误报数**
- **漏报率 = 1 - Recall**

## 目录结构

```
swrbench_eval_for_skill/
├── data/
│   └── swr_datasets_d5c5.jsonl          # SWR-Bench 1000 条 PR 数据
├── prompts/
│   ├── judge_eval_change.txt            # Change-PR 评测 Judge prompt
│   └── judge_eval_clean.txt             # Clean-PR 评测 Judge prompt
├── skills/
│   ├── cr_skill_interface.py            # Skill 抽象接口
│   ├── example_cr_skill.py              # 示例：简单 diff-only LLM reviewer
│   └── my_cr_skill.py                   # ⭐ 你替换这里接入自己的 skill
├── src/
│   ├── config.py                        # 配置（从环境变量读取）
│   ├── dataset.py                       # 数据集加载/格式化
│   ├── llm_client.py                    # OpenAI-compatible LLM 调用
│   ├── judge.py                         # LLM-as-Judge 评测逻辑
│   └── metrics.py                       # P/R/F1、误报率计算
├── run_eval.py                          # 主入口
├── requirements.txt
├── .env.example
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd swrbench_eval_for_skill
pip install -r requirements.txt
```

### 2. 配置 API

```bash
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_BASE 和 OPENAI_API_KEY
source .env
```

### 3. 接入你的 Skill

编辑 `skills/my_cr_skill.py`，把 `review_pr()` 替换成你真实 skill 的调用逻辑：

```python
class MyCrSkill(CodeReviewSkill):
    def review_pr(self, item: Dict[str, Any]) -> str:
        # item 包含：
        #   - pr_title, pr_statement
        #   - pr_commits (diff patches)
        #   - pr_timeline (review 讨论、commit)
        #   - base_commit, repo, instance_id
        # 你的 skill 可以基于 base_commit checkout 仓库、跑 CRG、读业务规则...
        return your_agent.review(item)
```

### 4. 小样本测试（推荐先跑 10 条）

```bash
python run_eval.py --skill my --sample 10 --output results/my_skill_smoke.json
```

### 5. 全量评测

```bash
python run_eval.py --skill my --output results/my_skill_full.json
```

## 评测原理

完全复用 SWR-Bench 论文的评测方式：

1. **生成阶段**：你的 skill 对每个 PR 输出一段 review。
2. **Judge 阶段**：用 `Gemini-2.5-Flash`（可配置）作为 Judge，判断：
   - 模型提出的每个 point 是否命中 ground truth change-action（**语义匹配**）
   - Clean-PR 上产生了多少 false positive
3. **指标阶段**：
   - `TP`：命中 GT 的 predicted point
   - `FP`：没命中 GT 的 predicted point
   - `FN`：没被命中的 GT change-action
   - `Precision = TP / (TP + FP)`
   - `Recall = TP / (TP + FN)`
   - `F1 = 2PR/(P+R)`
   - `Avg. FP per Clean-PR`：误报严重程度

## 输出示例

```json
{
  "num_change_prs": 500,
  "num_clean_prs": 500,
  "overall": {
    "tp": 95,
    "fp": 520,
    "fn": 405,
    "precision": 0.1545,
    "recall": 0.1900,
    "f1": 0.1705
  },
  "macro_f1": 0.1650,
  "false_positives": {
    "avg_fp_per_clean_pr": 1.85,
    "total_fp_on_clean_prs": 925,
    "clean_pr_identified_as_good_rate": 0.62
  }
}
```

## 重要基准参考

SWR-Bench 论文里 diff-only / agent 基线的 Overall-F1：

| 方法 | Overall-F1 |
|------|-----------|
| LLM-Review (base_review, diff-only) | 12.49% |
| SWR-Agent (读仓库的 agent) | 12.61% |
| PR-Review (qodo-ai/pr-agent) | **18.73%** |

如果你的 skill + 仓库上下文 + CRG 影响半径能超过 **18.73%**，就说明比当前学术界公开 best practice 更强。

## 只用 diff 的基线示例

如果你只想先跑一个 diff-only 基线对照，可以直接用 `example` skill：

```bash
python run_eval.py --skill example --sample 50 --output results/example_sample50.json
```

## 跳过生成，只跑 Judge

如果你已经有 skill 生成的 review 文件（每行 JSON 包含 `instance_id` 和 `review`）：

```bash
python run_eval.py --reviews-file results/my_reviews.jsonl --output results/my_eval.json
```

## 自定义 Judge 模型

修改 `.env` 里的 `JUDGE_MODEL`。SWR-Bench 论文用 `gemini-2.5-flash-preview-04-17`，但任何支持 JSON Schema response_format 的 OpenAI-compatible 模型都可以。

## 数据来源

- 数据集：`SWR-Bench` (ZZR0/SWRench, arXiv:2509.01494)
- Judge prompt：来自 `swrbench/evaluation_struct.py`
