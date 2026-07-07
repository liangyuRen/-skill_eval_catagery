# Agent Skill 评测方法总结

> 基于 2025-2026 年国内外最新论文与实战项目的综合梳理

---

## 一、什么是 Skill 评测

**Skill（技能）** 是赋予 AI Agent 特定领域能力的模块化知识包，通常包含指令文档、代码示例、配置文件和参考资源。Agent 在执行任务时加载对应 Skill，从而获得超出模型预训练知识范围的专业能力。

**Skill 评测** 则是对这些技能模块的效用、安全性、可靠性和可复用性进行系统化测量。它不同于传统的模型基准评测（如 MMLU、HumanEval），评测对象不是裸模型，而是 "**模型 + Skill + Agent 框架**" 三者组合的系统工程表现。

---

## 二、Skill 评测的核心方法论

### 2.1 基本范式：A/B 对照实验

几乎所有 Skill 评测框架都遵循同一个核心范式：

```
┌─────────────────────────────────────────────────────┐
│  同一任务 × 同一模型 × 同一框架                        │
│                                                     │
│  条件 A（基线）：Agent 仅接收任务描述                  │
│  条件 B（实验）：Agent 接收任务描述 + 目标 Skill        │
│                                                     │
│  对比 A vs B 的通过率 / 质量 / 成本差异 → Skill 增量   │
└─────────────────────────────────────────────────────┘
```

**SkillsBench** 在此基础上增加了第三种条件——**自生成 Skill**（让 Agent 先自己写一个 Skill 再用它执行任务），用于评测模型自主生成程序性知识的能力。

**SkillBenchmark** 进一步强化了盲审设计：Judge 评判时**看不到原始任务描述**，仅基于评分标准（rubric）打分，防止任务本身的信息污染评判结果。

### 2.2 评测执行流程

```
1. 任务构造
   ├── 人工专家编写任务（SkillsBench、ALE）
   ├── 自动从仓库/文档生成（SkillGenBench、OpenSkillEval）
   └── 动态演化生成（DARG、Prism）

2. 环境准备
   ├── 容器化沙箱（SkillsBench 使用 Docker）
   ├── 确定性环境快照（SkillGenBench）
   └── 实时环境交互（WebArena、AppWorld）

3. 执行与轨迹采集
   ├── Agent 在环境中自主执行
   ├── 记录每步工具调用、推理过程、Token 消耗
   └── 保留环境快照用于复现（PawBench）

4. 结果判分
   ├── 确定性验证器（SkillsBench — 代码直接检查输出）
   ├── LLM-as-a-Judge（SkillVetBench — 语义级评判）
   ├── 盲审对比（SkillBenchmark — Welch t-interval）
   └── 人工评估（ALE — 专家评审）
```

### 2.3 关键设计原则

| 原则 | 说明 | 代表框架 |
|------|------|----------|
| **确定性判分** | 避免 LLM-as-Judge 的不稳定性 | SkillsBench |
| **盲审设计** | Judge 不知任务原文，防止污染 | SkillBenchmark |
| **多轮重复** | 同一任务跑 N 次取置信区间 | SkillBenchmark |
| **环境隔离** | Docker 容器 + 干净上下文 | SkillsBench, VeAgentBench |
| **可复现** | 保留完整轨迹和环境快照 | PawBench |

---

## 三、Skill 评测的多维指标体系

### 3.1 效用维度（Utility）

```
效用评分 = 条件B通过率 - 条件A通过率（即 Skill 增量 delta）
```

| 指标 | 含义 |
|------|------|
| **Pass Rate (通过率)** | 任务完成的百分比 |
| **Delta (增量)** | 使用 Skill 后通过率的绝对变化（+16.2pp 为 SkillsBench 均值）|
| **Normalized Gain** | Delta / (100% - 基线通过率)，衡量 Skill 填补剩余能力缺口的能力 |
| **Completion Quality** | 任务完成度评分（0-1），不只看是否通过，还看完成质量 |
| **Task Coverage** | Skill 覆盖了多少类型的任务 |

**关键发现**：SkillsBench 中 16/84 任务出现**负增量**——Skill 有时会误导 Agent。这意味着每个 Skill 必须经过独立评测，不能假定"有 Skill 就一定更好"。

### 3.2 效率维度（Efficiency）

| 指标 | 含义 | 来源 |
|------|------|------|
| **Token 消耗** | Skill 加载 + 执行的总 Token 数 | skill-insight |
| **时间消耗** | 任务完成的总耗时 | skill-insight |
| **工具调用次数** | Agent 执行过程中调用的工具总数 | Claude Code eval rubric |
| **ROI（投入产出比）** | Delta / Token 成本，衡量 Skill 的效率 | skill-insight |
| **Skill 压缩率** | SkillCraft 演示缓存复用可减少 80% Token | SkillCraft |

### 3.3 安全维度（Security）

**SkillVetBench** 提出了 **SARS（Skill Agentic Risk Score）** 五维安全评分：

| 维度 | 缩写 | 含义 |
|------|------|------|
| 指令忠实度风险 | IFR | Skill 是否会诱使 Agent 偏离用户意图 |
| 数据引力 | DG | Skill 是否会不必要地收集/外传数据 |
| 操作不可逆性 | AI | Skill 执行的操作是否可撤销 |
| 爆炸半径 | BR | Skill 操作影响的范围和深度 |
| 链式放大 | CA | 与其他 Skill 组合时风险是否被放大 |

**SkillTrustBench** 按攻击手段（而非仅按后果）分类，覆盖九大安全威胁类型（T01-T09），含提示注入、内存投毒、权限滥用、数据窃取等。

**关键数据**：
- 36.82% 的公开 Skill 存在安全问题（Snyk 审计 3,984 个 Skill）
- 不同安全扫描器的共识极低：任意两类扫描的重合样本 ≤10.4%，仅 0.69% 恶意 Skill 被三类方案同时发现
- 静态代码分析（如 SkillSieve）仍有 15% 漏报率

### 3.4 触发与编排维度（Triggering & Orchestration）

| 指标 | 含义 |
|------|------|
| **Trigger Precision** | Skill 被触发时，有多少是真正需要的（越低 = 误触发越多）|
| **Trigger Recall** | 需要 Skill 时，有多少被成功触发（越低 = 漏触发越多）|
| **Trigger F1** | Precision 和 Recall 的调和平均 |
| **Orchestration Fitness** | Skill 是否做好纯粹的"执行者"，而非越权当"指挥者"|
| **Scope Calibration** | Skill 的适用范围是否恰当（过宽则误触发，过窄则无用）|

### 3.5 鲁棒性维度（Robustness）

| 指标 | 含义 |
|------|------|
| **Consistency (pass^k)** | 同一任务跑 k 次，通过率的一致性 |
| **Cross-model Transfer** | Skill 在不同模型上的效果差异（SkillsBench 发现模型差异约为框架差异的 3 倍）|
| **Cross-framework Transfer** | 同一 Skill 在 Claude Code/Codex CLI/Gemini CLI 等不同框架上的表现 |
| **Library Selection** | 从噪声 Skill 库中**检索并选择**正确 Skill 的能力（vs. 完美匹配 Skill）|

**关键发现**：当从"精选匹配"切换到"从噪声库中检索"时，Skill 收益**持续退化**——Agent 在选择、检索和适配 Skill 方面存在显著困难。

---

## 四、Skill 评测的不同层次

从上述论文和项目中，可以抽象出 Skill 评测的四个层次：

```
Level 1: Skill 使用评测
  └── 给定一个 Skill，Agent 能否正确使用它完成任务？
  └── 代表：SkillsBench, Skill-Usage in the Wild

Level 2: Skill 生成评测
  └── 给定一个领域，Agent 能否自己写出有效的 Skill？
  └── 代表：SkillGenBench（结论：当前模型做不到）

Level 3: Skill 进化评测
  └── Agent 能否在使用中持续改进 Skill？
  └── 代表：SkillAxe（自优化消除 47-67% 与人写的差距）

Level 4: Skill 生态评测
  └── 大规模 Skill 库的安全、质量、互操作性全貌
  └── 代表：SkillVetBench, SkillTrustBench, OpenSkillEval
```

---

## 五、典型的实战评测工作流

综合 SkillsBench、skill-creator（Anthropic 官方）和 skill-insight 的最佳实践：

### Step 1: 定义评测任务
```
- 确定评测领域（代码 / 医疗 / 设计 / 安全 / ...）
- 编写任务描述 + 验收标准
- 准备测试环境（Docker 镜像、依赖、API 密钥等）
- 编写确定性验证器（代码级 pass/fail 检查）
```

### Step 2: 建立基线
```
- 在无 Skill 条件下运行 N 次（通常 N≥5，保证统计效力）
- 记录通过率、Token 消耗、执行时间、工具调用序列
- 计算基线置信区间
```

### Step 3: Skill 介入评测
```
- 在相同任务上，加入目标 Skill 后运行 N 次
- 记录相同指标
- 使用 Welch t-test 检验增量是否统计显著
```

### Step 4: 盲审对比（可选但推荐）
```
- 随机混洗 "有 Skill" 和 "无 Skill" 的输出
- Judge 仅基于评分标准打分（不知道哪个用了 Skill）
- 计算盲审 Delta，排除 Judge 偏见
```

### Step 5: 多维度分析
```
- 效用：Delta 通过率，按领域/任务类型分组
- 效率：Token 增量，时间增量，ROI
- 安全：SARS 五维评分，静态+语义扫描
- 触发：Precision/Recall，误触发/漏触发分析
- 轨迹：工具调用正确性，执行路径偏差
```

### Step 6: 迭代优化
```
- 根据评测结果调整 Skill 内容（精简、去歧义、加示例）
- 重新评测，对比前后版本
- 达标后发布，并建立持续监控（回归测试）
```

---

## 六、代表框架对比

| 框架 | 评测对象 | 判分方式 | 安全评测 | 开源 | 规模 |
|------|----------|----------|----------|------|------|
| **SkillsBench** | Skill 增量效用 | 确定性验证器 | 否 | 是 | 86 任务 / 7,308 轨迹 |
| **SkillBenchmark** | 单个 Skill 质量 | 盲审 LLM Judge | 否 | 是 | 单 Skill 级 |
| **SkillGenBench** | Skill 生成管线 | 确定性执行检查 | 否 | 是 | 代码+文档双源 |
| **SkillVetBench** | Skill 安全风险 | LLM-as-Judge | 是（SARS）| 是 | 100 样本验证 |
| **SkillTrustBench** | Skill 安全威胁 | 按攻击类型分类 | 是（9 类威胁）| 是 | 5,520 用例 |
| **SkillTester** | 效用+安全双评 | 执行对比 | 是（三级标签）| 是 | - |
| **OpenSkillEval** | 开源 Skill 生态 | 自动动态生成 | 否 | 是 | 600+ 动态任务 |
| **skillrank** | Skill 增量打分 | 盲审 CLI | 否 | 是（npm）| 单 Skill 级 |
| **skill-insight** | 多维观测分析 | 集成标准数据集 | 否 | 是（npm）| 全链路 |

---

## 七、关键结论与实战建议

### 7.1 从已有研究中提炼的核心教训

1. **不要假设 Skill 一定有用**：SkillsBench 中 16/84 任务出现了负增益，每个 Skill 必须独立评测验证
2. **精简至上**：2-3 个聚焦模块 + 中等长度文档是最优配置，长篇综合文档反而有害
3. **模型自生成 Skill 目前不可靠**：多篇论文一致结论——模型无法自主编写有效的程序性知识
4. **安全评测不可省略**：36.8% 的公开 Skill 存在安全问题，且不同扫描器共识极低，需要多工具交叉验证
5. **框架-模型匹配至关重要**：同一 Skill 在不同框架/模型组合下效果差异可达数倍
6. **评测应在真实检索条件下进行**：从噪声 Skill 库中检索的效果远低于完美匹配，评测必须反映这一现实

### 7.2 如果要搭建自己的 Skill 评测体系

推荐的 minimal viable pipeline：

```
1. 选型：SkillsBench（效用基准）+ SkillTester（安全扫描）
2. 定制：在自己的领域写 10-20 个代表性任务 + 确定性验证器
3. 基线：先用裸模型跑 5 次，记录基线
4. 评测：加入 Skill 跑 5 次，计算 Delta
5. 安全：用至少两种扫描器交叉验证
6. 迭代：根据结果优化 Skill → 重新评测 → 达标发布
```

---

## 八、参考资源索引

| 资源 | 链接 |
|------|------|
| SkillsBench 代码 | github.com/benchflow-ai/skillsbench |
| SkillsBench 论文 | arxiv.org/abs/2602.12670 |
| SkillBenchmark | github.com/TiesPetersen/SkillBenchmark |
| SkillTester | github.com/skilltester-ai/skilltester |
| SkillTrustBench | matrix.tencent.com/skilltrustbench |
| skill-insight | npm: skills-insight |
| skillrank | npm: skillrank |
| AgentSkill Survey | github.com/Cassie07/AgentSkill_Survey |
| ALE (Agent's Last Exam) | arxiv.org/abs/2606.05405 |
| Anthropic skill-creator | claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills |
| VeAgentBench | modelscope: bytedance-research/veAgentBench |
| PawBench | 阿里通义实验室 |
| FeatureBench | ICLR 2026 西安交通大学 |

---

> 文档生成日期：2026-06-18
> 基于 30+ 篇论文和 15+ 个开源项目的综合分析
