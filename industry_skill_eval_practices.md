# 业内AI Agent/Skill评测实践汇总

## 前沿实验室的内部评测实践

### Anthropic: Worker + Evaluator 双模型架构
- Claude Code内置evaluator：Worker模型(Claude)执行任务，Evaluator模型(Haiku)在每一步后检查目标条件是否满足
- 条件为可度量的终态：测试退出码、构建结果、文件计数、干净的git status
- 内部dogfooding：多agent模式（一个构建、一个检查/总结、人类review）
- 外部安全测试：UK AISI和Apollo Research获得API访问权限>3周，测试misalignment威胁

### OpenAI: AgentKit + 外部红队
- AgentKit提供evaluation hooks作为agent生命周期的一部分
- 预发布评估：~8个外部组织获得>2周连续访问，测试生物风险、网络攻击、rogue replication等
- 内部dogfooding通过Codex：账单争议解决、自动仪表板、法律披露检查

### Google DeepMind: Vertex AI + ADK
- ADK支持LoopAgent模式，开发者构建critic节点和终止逻辑
- "customer zero"策略：Gemini agent处理供应商发票（5x更快审查）和合同比较
- 外部评估：多个组织获得>3-5周无安全过滤的API访问

**共同模式：内部dogfooding → 结构化外部安全/红队测试 → 基准测试驱动评估 → 环内验证**

---

## 核心开源/商业评测工具

### 开源工具

| 工具 | 适用场景 | 核心优势 |
|---|---|---|
| **DeepEval** | CI/CD agent skill单元测试 | 50+指标、确定性tool correctness、pytest集成 |
| **Ragas** | RAG + tool-call评估 | ToolCallF1（无序部分评分，无需LLM） |
| **Arize Phoenix** | OTel原生可观测性 | OpenInference规范、框架无关 |
| **MCPEval (Salesforce)** | MCP agent评估 | 双层：确定性工具匹配 + LLM判断 |
| **AgentBench (ETH)** | 编码agent评估 | 多上下文(NONE/LLM/HUMAN)、可复现Docker |
| **HAL (Princeton)** | 统一基准测试 | 10+基准、统一CLI、成本感知 |
| **Promptfoo** | 安全/红队测试 | Prompt注入、越狱检测、对抗验证 |

### 商业平台

| 平台 | 适用场景 | 核心优势 |
|---|---|---|
| **LangSmith** | LangChain/LangGraph团队 | 轨迹评估、图评估 |
| **Braintrust** | 跨职能团队 | 人机协同review、Money Table失败模式分析 |
| **Galileo** | 受监管企业 | Luna SLM评估器(<200ms)、Action Advancement Metric |
| **Maxim AI** | 全栈agent评估 | 三层框架、4种SDK语言 |
| **AWS Agent Evaluation** | Bedrock/Q Business用户 | 并发多轮对话评估、CI/CD集成 |

---

## 关键技术

### 1. Agent-as-a-Judge
- 从LLM-as-a-Judge演进：单模型评分 → 多Agent辩论 → 全Agentic评估器
- Agent-as-a-Judge (Zhuge et al., 2025)：评估器agent具备与被测系统相同的工具，与人类专家仅~0.3%分歧
- 关键漏洞：操纵agent的chain-of-thought可使误判率提升90%
- 最佳实践：紧致评分标准、固定版本（judge模型+prompt+rubric全部版本化）、不同模型家族、人工golden set每月校准、要求rationale

### 2. 领域特定合成数据生成
- **MAG-V**: 多agent生成客户查询并反向工程替代问题用于轨迹验证
- **AgentFrontier**: 基于最近发展区理论，LKP vs MKO对抗校准
- **Agentic Adversarial QA**: TextGrad风格可微分提示，生成最大化弱vs强模型差异的问题

### 3. Agent红队测试
- **GOAT (Meta, ICML 2025)**: 7种红队攻击技术，96% ASR@10对Llama 3.1
- **UDora (ICML 2025)**: 动态劫持agent自身推理过程
- **AgentSecOps (Straiker)**: CI/CD嵌入对抗测试，指标包括Contract Violation Rate、Context Leakage Score
- **CSA Agentic AI Red Teaming Guide (2025年5月)**: 覆盖权限提升、幻觉利用、编排缺陷、记忆操纵、供应链风险

### 4. 行为测试（CI集成）
- **断言文件系统状态而非agent解释**：在Docker/Testcontainers中启动干净工作区，注入skill，运行agent，断言结果文件系统状态
- 三种评估类型：Positive Trigger Test、Negative Trigger Test、Collision Resolution
- 核心规则："如果两个skill在相同查询上可能触发，至少有一个设计错误"

---

## Agent Skill评估 vs LLM输出评估的核心区别

| 维度 | LLM评估 | Agent Skill评估 |
|---|---|---|
| 评估单元 | 单次(input → output) | 完整轨迹（推理步骤+工具调用+观察+最终输出） |
| 失败模式 | 幻觉、毒性、事实错误 | 错误工具、错误参数、遗漏工具、过度调用、错误恢复失败、无限重试循环、计划偏离 |
| 可复现性 | 高（给定seed） | 低（环境状态、工具结果、延迟都影响结果） |
| 真值标准 | 期望的答案文本 | 期望的终态 + 有效执行路径 |
| 评分粒度 | 单一输出质量分 | 每步评分：计划质量、工具选择、参数正确性、结果利用、最终结果 |
| 复合错误 | 不适用 | k步agent的端到端成功率 ≈ 每步成功率的乘积（95%/step × 8步 ≈ 66%） |
| 所需基础设施 | 模型API | 容器化环境、工具模拟器、状态追踪、超时管理 |

**核心洞察：看起来正确的回复可能来自错误的工具+错误的参数靠运气得到；看起来错误的回复可能来自评分标准未预见的正确轨迹。Trace才是真相。**

Agent独有的四个能力维度：
1. 规划与推理 (Plan Quality, Node F1, Step Success Rate)
2. 工具使用 (Selection accuracy, parameter F1, result utilization, error recovery)
3. 记忆与上下文保持 (Factual recall after N turns, consistency score)
4. 多Agent协作 (Coordination quality, role adherence, information sharing)
