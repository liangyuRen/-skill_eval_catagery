# AI Code Review 基准效果数据汇总

> 更新时间：2026-07-23
> 置信度标注：【已核实】= 从论文/仓库一手来源验证；【未核实】= 来自二手调研记录，尚未独立确认；【厂商自测】= 厂商发布的基准，存在利益相关。

---

## 一、学术基准上的模型表现

### 1.1 SWR-Bench ✅ 已核实

来源：论文 *SWR-Bench: Assessing LLM Performance in Real-World Code Review Comment Generation*（PACMSE/FSE 2026，[arXiv:2509.01494](https://arxiv.org/abs/2509.01494)）；官方仓库 [ZZR0/SWRench](https://github.com/ZZR0/SWRench)。

| 项目 | 内容 |
|---|---|
| 数据集 | 1000 个 PR：500 Change-PR + 500 Clean-PR（来自 SWE-Bench 的 12 个 Python 项目） |
| Judge | Gemini-2.5-Flash，单次调用，与人类判断 **Kappa 最高 86.7** |
| 指标 | hit-based Precision/Recall/F1（Overall + Functional-only）+ Clean-PR 平均误报数（Avg. FP Count） |
| 已确认最好成绩 | **Overall-F1 18.73%**（qodo-ai/pr-agent 基线，即论文中的 "PR-Review"） |

**重要纠正**：此前调研记录称 SWR-Bench 有 **SNR 指标**、"Reflexion 召回 32.76% SNR 从 5.11 掉到 1.95"、"最好 F1 19.38%"——经对论文全文 grep，**SWR-Bench 论文中无 SNR 指标**，且已确认的最好成绩为 **18.73%**。这些数字暂勿引用。

### 1.2 SWE-PRBench ✅ 基准真实，leaderboard 已核实

来源：*SWE-PRBench: Benchmarking AI Code Review Quality Against Pull Request Feedback*（[arXiv:2603.26130](https://arxiv.org/abs/2603.26130)，2026-03）；[FoundryHQ-AI/swe-prbench](https://github.com/FoundryHQ-AI/swe-prbench)。

| 项目 | 内容 |
|---|---|
| 数据集 | 350 个人工标注 PR，从 700 候选按 Repository Quality Score 过滤 |
| 上下文配置 | **config_A 仅 diff / config_B diff+文件 / config_C 全上下文**（对 diff-only 评测极有价值） |
| Judge | GPT-5.2，**kappa=0.75**；三分类：CONFIRMED / PLAUSIBLE / FABRICATED |
| 指标 | Overall (s̄)、DR_A、FPR 等 |

**Paper Baseline Leaderboard（已核实，来自 README）**：

| Rank | Model | Overall (s̄) | DR_A | FPR |
|------|-------|-------------|------|-----|
| 1 | Claude Haiku 4.5 | **0.153** | 0.306 | 0.346 |
| 2 | Claude Sonnet 4.6 | 0.152 | 0.297 | 0.227 |
| 3 | DeepSeek V3 | 0.150 | 0.312 | 0.315 |
| 4 | Mistral Large 3 | 0.147 | 0.305 | 0.353 |
| 5 | GPT-4o | 0.113 | 0.220 | 0.193 |
| 6 | GPT-4o-mini | 0.108 | 0.210 | 0.353 |
| 7 | Mistral Small | 0.106 | 0.257 | 0.251 |
| 8 | Llama 3.3 70B | 0.079 | 0.223 | 0.417 |

- 评估子集：`evals/eval_100.json`
- Pipeline：v0.4.1，temperature=0
- **核心结论**：最强模型 Overall 仅 15.3%；diff-only 配置下检出率 DR_A 最高 31.2%（DeepSeek V3），但 FPR 也达 31.5%

### 1.3 CodeFuse-CR-Bench ✅ 已核实

来源：*CodeFuse-CR-Bench: A Comprehensiveness-aware Benchmark for End-to-End Code Review Evaluation in Python Projects*（[arXiv:2509.14856](https://arxiv.org/abs/2509.14856)，蚂蚁 CodeFuse）；代码仓库 [codefuse-ai/SWE-CARE](https://github.com/codefuse-ai/SWE-CARE)。

| 项目 | 内容 |
|---|---|
| 数据集 | 601 实例、70 个 Python 项目、9 个 PR 问题域 |
| 评估器 | **双层**：RuleBasedEvaluator（位置相似度+BLEU 贪心匹配）+ LLMEvaluator（4 字段×5 维度） |
| 已确认结论 | **Gemini 2.5 Pro 综合最强**；具体分数本环境未下载到完整结果表 |

**RuleBasedEvaluator 权重（可直接复用）**：
- 位置相似度 = `path 精确×0.7 + 行号接近度×0.15（同行 1.0，差≤5 行线性衰减）+ hunk 行区间重叠率×0.15`
- 描述相似度 = 4-gram BLEU
- combined = 0.5×位置 + 0.5×描述，>0.5 计 TP

---

## 二、商业工具效果（多未核实）

| 来源 | 内容 | 置信度 |
|---|---|---|
| **Greptile 自家基准（2025.07）** | 50 个真实生产 bug 对比：Greptile 82% > Cursor Bugbot 58% > Copilot ~55% > CodeRabbit 44% > Graphite 6% | 【厂商自测，待核实】 |
| **CodeRabbit / Qodo / Greptile 官方口径** | 普遍宣称"接受率提升""误报减少"，但几乎无公开同行评审级数据 | 【厂商自测】 |

---

## 三、大厂内部部署数据（已核实）

| 系统 | 关键数字 | 来源 |
|---|---|---|
| **Google AutoCommenter** | useful ratio 54% → 校准迭代后 80%（部署门槛）；评论解决率 ~40%；显式反馈率仅 ~10%（review）/ ~2%（IDE） | arXiv:2405.13565 |
| **Google AutoCommenter** | top-50 高频规则中 66% 超出传统 linter 能力 | 同上 |
| **Meta TestGen-LLM** | 73% 的建议被工程师采纳进生产 | arXiv:2402.09171 |
| **Meta Getafix** | top-1 修复建议与人类修复一致率 12%-91%（因 bug 类型而异） | arXiv:1902.06111 |
| **Meta SapFix** | 机器生成的补丁经人类审查员接受并推入 Facebook Android 生产代码（2018-08 起） | 官方博客 |

---

## 四、关键结论

1. **学术界最好成绩 Overall-F1 不到 20%**（SWR-Bench 18.73%，SWE-PRBench Overall 15.3%）——AI code review 仍处于低召回 + 高误报阶段，skill/上下文增强空间巨大
2. **上下文是最大杠杆**：SWE-PRBench 三档配置（diff-only / diff+文件 / 全上下文）直接量化了这个变量；diff-only 配置下检出率最高也只有 31.2%，FPR 20%-40%
3. **"不在 GT 里"不等于"误报"**：SWE-PRBench 的 PLAUSIBLE 类别说明顶级基准也承认 GT 不全，评测系统必须内置待裁决机制
4. **商业工具数字谨慎看待**：除 Google/Meta 论文外，多数效果数字为厂商自测或缺乏方法论披露
5. **定位匹配权重可直接复用**：CodeFuse-CR-Bench 的 RuleBasedEvaluator 权重（path 0.7 + line 0.15 + hunk 0.15）是经过论文验证的参数，不必拍脑袋
