# 多轮对话Agent评测——业内实践汇总

> 对应方案：状态点验证法、从session提取checkpoints、轨迹级评测

---

## 一、与你方案的直接对应

| 你的方案 | 业内对应实践 |
|---------|------------|
| 状态点验证法 | LangGraph Checkpoint Replay + AWS Bedrock GoalSuccessRate（按终态而非文本判分）；tau-bench 用数据库终态做ground truth |
| 从session提取checkpoints | LangSmith trajectory match evaluator 自动对比参考轨迹；AgentDiagnose 无需参考轨迹即可评分 |
| 多轮评测重心从文本转向行为 | 全行业共识：单轮工具调用准确率90%+，但多轮端到端成功率仅4-40%（Zendesk ALMITA数据）。Trace才是真相 |
| 分层评测集（单步/整轮/多轮） | LangChain生产实践：~50%测试是单步决策验证，剩余是整轮+多轮条件测试 |
| Session自动分流（A/B/C/D类） | Lyft：生产失败trace自动路由到人工标注队列；LangSmith Insights Agent自动聚类行为模式 |

---

## 二、核心框架与工具

### 2.1 LangSmith Multi-turn Evals（LangChain，2025年10月发布）

最贴近多轮session评测场景的工具：

- **原生Thread概念**：整段对话作为评测单元，对话完成后自动触发session级评分
- **条件化多轮测试**：根据agent输出分支测试逻辑，偏离时提前失败，避免级联误报
- **LangGraph Checkpoint Replay**：从失败点回放，A/B对比两个graph版本的轨迹差异
- **Insights Agent**：自动从生产trace中聚类行为模式和失败模式
- **Trajectory Match Evaluator**：支持strict/unordered/subset/superset四种模式对比参考轨迹
- **Pytest/Vitest集成**：每个测试用例独立断言轨迹（tool calls）、最终回复、状态产出物

### 2.2 tau-bench（Sierra Research / Princeton，2024）

评估范式与你方案高度一致：

- 模拟用户 + 领域API（Airline、Retail）
- **数据库状态作为ground truth**：比对最终数据库状态与标注目标状态
- **Pass@k指标**：同一任务跑k次看一致性——暴露了强模型重复运行时也显著退化
- 2025年最佳：Claude 3.7 Sonnet + think tool = 81.2% Retail Pass@1, 58.4% Airline
- Anthropic模型卡中大量使用
- 代码：github.com/sierra-research/tau-bench

### 2.3 MLflow v3.8 Session-Level Scorers

原生session级评估指标：

| 指标 | 含义 |
|------|------|
| ConversationCompleteness | 对话结束时agent是否解决了所有用户需求 |
| KnowledgeRetention | agent是否正确保持了前轮的信息（不丢失、不扭曲） |
| UserFrustration | 用户是否出现过挫败情绪，是否被解决 |
| ConversationalToolCallEfficiency | 检测冗余调用、遗漏批处理机会、工具选择不当 |
| ConversationalGuidelines | 是否在整个session中遵循了定义的支持规则 |

- `ConversationSimulator`：自动生成多轮对话测试用例
- `make_judge` API：支持 `{{ conversation }}` 模板变量传入完整对话历史做自定义评分

### 2.4 AWS Bedrock AgentCore Evaluations（2025年12月Preview）

13个预置评估器，三个层级：

- **Session级**：GoalSuccessRate（以完整多轮对话为评估单元）
- **Trace级（逐轮）**：Helpfulness, Coherence, InstructionFollowing, Refusal等
- **Tool级**：ToolSelectionAccuracy, ToolParameterAccuracy
- 两种模式：Online（实时持续监控）+ On-Demand（指定sessionID/traceID回放）
- AWS Labs `agent-evaluation`：开源框架，用LLM evaluator agent编排并发多轮对话，在对话过程中评估

### 2.5 ASSERT（Microsoft Research）

- 将自然语言产品需求/策略转化为结构化测试用例
- 自动生成单轮和多轮场景
- Judge引用trace中的工具调用、路由决策、模型调用、延迟作为证据
- 框架无关：支持LangGraph、CrewAI、OpenAI Agents SDK、DSPy、LlamaIndex、AutoGen

---

## 三、评测粒度分层（行业共识）

| 层级 | 评测内容 | 代表指标 | 适用场景 |
|------|---------|---------|---------|
| **Node级**（状态转换） | 单次工具调用、状态转换 | Node-input/output correctness, Edge-routing correctness | LangGraph回归测试 |
| **Turn级**（单轮回复） | 单条消息质量 | Context Relevance, Tool Selection Accuracy | 细粒度质量分析 |
| **Trajectory级**（推理过程） | 推理过程质量 | Step Efficiency, Task Decomposition, Self-Verification | Agent调试和优化 |
| **Session级**（完整对话） | 整体对话质量 | Goal Success, UserFrustration, KnowledgeRetention | 生产监控、回归测试 |

LangChain生产实践发现：~50%的测试是单步（决策点验证），剩余是整轮+多轮条件测试。

---

## 四、关键生产案例

### 4.1 Lyft — 生产级Agent评测（2024）

- **规模**：7个生产agent、27万次AI交互/月（争议、损坏索赔、合规、税务）
- **核心教训——模拟器真实性差距**：LLM模拟的用户太礼貌，真实用户只发一两个字。离线模拟90分→上线表现差
- **方案**：LangGraph + LangSmith离线模拟 + 失败trace自动路由到人工标注队列
- **效果**：解决率从10%提升到35%

### 4.2 Zendesk — ALMITA Benchmark（2024-2025）

- 1,420条人工构建的多轮对话
- Pipeline：LLM生成用户意图 → 对话图构建（正常路径、分支、死胡同、绕路）→ 噪声注入 → 加权随机游走生成多轨迹 → 每条路径成为测试用例
- **核心数据**：单轮工具调用准确率90%+ → 多轮端到端仅4.2-14.1%
- 代码：github.com/zendesk/almita-dataset

### 4.3 Anthropic Claude Code — 编码Agent的多轮挑战

- 长会话（数小时）中，挑战从优化单次prompt转向管理跨数百轮的上下文
- Compaction在~100次迭代后用户仍感沮丧
- Sub-agent架构：将研究委托给子agent"炸掉它们的上下文窗口"读取文件，只返回最终报告
- SWE-bench Verified: 80.9%（Opus 4.5，业界最高）

---

## 五、轨迹对比与回放工具

| 工具 | 核心能力 |
|------|---------|
| **AgentLens**（Dreadnode） | ATIF标准化轨迹格式、shadow git变更追踪、四种重采样/回放方法 |
| **AgentDiagnose**（CMU） | 五种agent能力无参考评分、t-SNE可视化、state-transition导航图 |
| **AgentEvals**（LangChain） | 轨迹对比模式：strict/unordered/subset/superset + 无参考LLM Judge |
| **ECHO**（Microsoft/NYU） | 从失败尝试生成优化的反事实轨迹 |
| **RAFFLES** | 自动识别多轮轨迹中的决定性（因果性）故障，43.6% step级准确率 |

---

## 六、2025-2026行业共识

1. **单轮基准已基本解决**：模型单次工具调用90%+准确率。多轮对话成功率仍停留在4-40%
2. **主导评估范式**：无参考LLM-as-a-Judge + 周期性人工标注校准 + 确定性检查做二元/可验证输出
3. **三种评测粒度缺一不可**：node级（状态转换和工具调用）、trajectory级（推理过程质量）、session级（目标达成、挫败感、知识保持）
4. **生产评估必须线上线下结合**：模拟器-真实用户差距是反复出现的失败模式
5. **条件化多轮测试**：根据agent输出分支，而非硬编码输入序列，是避免级联误报的关键
6. **轨迹回放和checkpoint回归**：将每个生产失败转化为确定性测试用例正在成为标准做法
7. **架构至少和模型同等重要**：同一模型在不同agent框架下SWE-bench差距达15-17个任务（共731任务）
