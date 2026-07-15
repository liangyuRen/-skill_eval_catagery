# Agent Skill 自进化：架构与方法论全景

> 基于2025-2026年学术前沿论文与工业实践的完整梳理，涵盖SkillForge、SkillMOO、SkillOpt、MUSE-Autoskill、CoEvoSkills、SkillClaw、MemSkill、AutoSkill、Skills-Coach及两篇综述的系统化总结。

---

## 一、核心洞察：为什么要做Skill自进化

### 1.1 静态Skill的四大死穴

| 问题 | 证据来源 |
|------|----------|
| **创建-使用错位**：离线写的Skill不匹配LLM实际推理方式，甚至可能**负优化** | SoK综述: 自生成Skill平均降1.3pp；CoEvoSkills: 人类Skill在Natural Science任务上反降性能 |
| **一次性的诅咒**：Skill部署后即腐烂，线上bad case无法沉淀回Skill | SkillForge: 传统Agent系统技能质量停滞不前 |
| **规模失控**：技能越堆越多，冗余、冲突、过时Skill无人清理 | SkillClaw: 技能膨胀导致Agent不知道该用哪个 |
| **经验孤岛**：不同用户/设备的优化经验无法共享 | SkillClaw: 多用户轨迹分散，经验无法汇聚 |

### 1.2 自进化的本质

Skill自进化 = 构建一个 **"创建→部署→评测→分析→优化"的持续闭环**，将Skill从"静态文档"变为"可训练的文本参数"。

**范式类比（来自SkillOpt）：**

| 深度学习 | Skill自进化等价 |
|----------|----------------|
| 模型权重 | Skill文档 (Markdown) |
| 前向传播 | Rollout：Agent携带Skill执行任务 |
| Loss/梯度 | 反思：分析成功/失败轨迹 → 结构化编辑建议 |
| 梯度聚合 | 层次化合并增/删/改操作 |
| 学习率 | 文本编辑预算（每次迭代最多~4次操作） |
| 验证集 | Held-out gate：候选Skill必须在留出集上严格提升 |
| Momentum | Epoch级Slow/meta update |
| 早停 | 验证门控接受/拒绝 |

---

## 二、统一架构：五层模型

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 5: 安全与治理                        │
│  人类审批 · 权限边界 · 审计追溯 · 红队测试 · 对抗验证      │
├─────────────────────────────────────────────────────────────┤
│                    Layer 4: 种群管理                          │
│   适应度评分 · 优胜劣汰 · 去重合并 · 版本管理 · Skill路由   │
├─────────────────────────────────────────────────────────────┤
│                    Layer 3: 评测闭环                          │
│   任务执行 · 轨迹采集 · 多维评分 · 失败归因 · Surrogate验证 │
├─────────────────────────────────────────────────────────────┤  
│                    Layer 2: 优化引擎                          │
│   文本空间梯度下降 · 多目标Pareto优化 · GRPO · 协同进化     │
├─────────────────────────────────────────────────────────────┤
│                    Layer 1: Skill生命周期                     │
│   创建 → 部署 → 执行 → 评测 → 反思 → 优化 → 验证 → 发布    │
└─────────────────────────────────────────────────────────────┘
```

### Layer 1: Skill生命周期（形式化定义）

**来自SoK综述的4元组形式化定义：**

> 一个Skill S = (C, π, T, R)
> - **C** (Condition): 适用条件——什么时候该用这个Skill
> - **π** (Policy): 可执行策略——怎么执行
> - **T** (Termination): 终止条件——什么时候算完成
> - **R** (Reference): 可复用接口——如何被调用/组合

**统一生命周期（融合MUSE-Autoskill五阶段 + SoK七阶段 + AutoSkill经验）：**

```
                    ┌──────────┐
                    │ 1. 创建   │  ← 业务知识库、历史工单、工作流挖掘、工具挖掘
                    └────┬─────┘
                         ▼
                    ┌──────────┐
                    │ 2. 验证   │  ← 单元测试 + Sandbox验证（MUSE-Autoskill方式）
                    └────┬─────┘
                         ▼
                    ┌──────────┐
                    │ 3. 部署   │  ← 注册到Skill库，建立索引（向量+BM25混合检索）
                    └────┬─────┘
                         ▼
                    ┌──────────┐
              ┌─────│ 4. 执行   │─────┐
              │     └────┬─────┘     │
              │          ▼           │
              │     ┌──────────┐     │
              │     │ 5. 评测   │     │  ← 轨迹采集 + 多维评分
              │     └────┬─────┘     │
              │          ▼           │
              │     ┌──────────┐     │
              │     │ 6. 诊断   │     │  ← 失败分析 + 根因定位到Skill具体段落
              │     └────┬─────┘     │
              │          ▼           │
              │     ┌──────────┐     │
              └────►│ 7. 优化   │◄────┘  ← 文本空间编辑/GRPO/协同进化
                    └────┬─────┘
                         ▼
                    ┌──────────┐
                    │ 8. 门控   │  ← Held-out验证 + 人类审批（关键变更）
                    └────┬─────┘
                         ▼
                    ┌──────────┐
                    │ 9. 发布   │  ← 版本更新 + 同步到所有Agent实例
                    └──────────┘
```

---

### Layer 2: 优化引擎——Skill的"训练算法"

这是整个架构的核心。当前学术界有**四类主流优化范式**：

#### 2.1 文本空间梯度下降（SkillOpt范式）

**代表论文：SkillOpt (Microsoft, arXiv 2605.23904)**

**核心思想：** 将Skill文档视为"可训练参数"，在不修改模型权重的前提下做"文本空间的反向传播"。

**算法流程：**
```
for epoch in 1..N:
    1. Rollout（前向传播）
       - 冻结的目标模型用当前Skill文档执行一批任务
       - 记录完整轨迹和得分
       
    2. Reflect（反向传播）
       - 独立的优化器模型分别分析失败/成功案例
       - 对每个案例提出结构化编辑：add / delete / replace
       - 按严重程度排序候选编辑
       
    3. Edit（参数更新）
       - 在文本学习率预算内（默认≤4次操作）聚合排名候选编辑
       - 生成候选Skill v_candidate
       
    4. Gate（验证门控）
       - 候选Skill仅在held-out验证集上严格提升时才被接受
       - 被拒绝的编辑进入缓冲区，作为负反馈防止重复无效方向
       
    5. Slow Update（Momentum）
       - 跨epoch长周期稳定机制
       - 防止单次坏样本导致Skill剧烈退化
```

**关键消融实验：**
- 去掉文本学习率：SpreadsheetBench 77.5% → 75.7%
- 去掉被拒编辑缓冲区：77.5% → 72.9%
- 最终产物仅300-2000 token的best_skill.md

**实验结果：** 52个评测组合（7模型×6基准×3执行环境）全部最优或并列最优，全面碾压Human skill、LLM skill、Trace2Skill、TextGrad、GEPA等基线。

**开源代码：** https://github.com/microsoft/SkillOpt

---

#### 2.2 多目标Pareto优化（SkillMOO范式）

**代表论文：SkillMOO (KCL等, arXiv 2604.09297)**

**核心思想：** 业务场景中Skill的质量不是单维度的——需要同时优化成功率、成本、耗时等多个冲突目标。

**两Agent迭代工作流：**
```
1. Task Solver Agent
   - 评估候选Skill组合在编码任务上的表现
   - 输出：pass rate / cost / runtime / error traces

2. Skill Optimizer Agent
   - 基于失败分析提出Skill编辑操作
   - 四类操作：Prune（精简）、Substitute（替换）、Reorder（重排）、Rewrite（重写）
```

**多目标优化机制：**
- 使用**NSGA-II**做非支配排序 + 拥挤距离选择
- 双目标：最大化Pass rate + 最小化推理成本
- **Pass-preservation guard**：子代若让pass rate下降>0.05则直接拒绝

**关键发现：**
- Prune和Substitute是最有效的操作（各7次，100%成功率）
- Bundle expansion（添加新内容）：0/5改善 → **有效Skill倾向精简而非堆砌**
- 优化成本效率低至$0.0011/百分点HV提升

**实验结果（软件工程任务）：**

| 任务 | 通过率提升 | 成本下降 |
|------|-----------|---------|
| Python构建修复 | +131.2% | -31.7% |
| Python→Scala翻译 | +30.8% | -5.4% |
| Spring Boot→Jakarta迁移 | +2.1% | -19.4% |

---

#### 2.3 协同进化验证（CoEvoSkills范式）

**代表论文：CoEvoSkills (MBZUAI/McGill等, arXiv 2604.01687)**

**核心思想：** 在真实业务场景中往往没有Ground Truth，需要一个与Skill共同进化的"验证器"来提供反馈信号。

**三组件架构：**

```
    ┌──────────────┐        ┌──────────────────┐
    │ Skill Generator│◄──────│ Surrogate Verifier │
    │ 生成/优化Skill │ 反馈   │ 独立生成测试断言    │
    └──────┬───────┘        │ 无Ground Truth访问  │
           │                └────────┬─────────┘
           │ 执行结果                 │ 不一致时
           ▼                         ▼
    ┌──────────────┐        ┌──────────────────┐
    │ Opaque Oracle │        │  Test Escalation  │
    │ 仅返回二值P/F  │──────►│  升级测试严格度    │
    └──────────────┘        └──────────────────┘
```

**交替优化机制：**
- Skill Generator根据Surrogate Verifier的反馈优化Skill
- 当Surrogate通过但Oracle失败 → Verifier升级测试严格度
- 两者协同进化，无需人工标注

**关键结果：**
- Claude Opus 4.6 71.1% pass rate，+40.5pp over baseline，+17.6pp over human skills
- 去掉Surrogate Verifier：-30pp
- 去掉进化循环：-22pp
- **跨模型迁移：** 在一个前沿模型上进化的Skill迁移到6个其他模型，均获得35-44pp提升

**项目页面：** https://zhang-henry.github.io/CoEvoSkills/

---

#### 2.4 免训练GRPO优化（Skills-Coach范式）

**代表论文：Skills-Coach (国科大等, arXiv 2604.27488)**

**核心思想：** 使用Group Relative Policy Optimization (GRPO) 做Skill指令的迭代优化，无需模型训练。

**四模块架构：**

| 模块 | 功能 |
|------|------|
| Diverse Task Generation | 从Skill规格自动生成标准+边界测试用例 |
| Lightweight Optimization | Training-free GRPO迭代细化Skill指令和代码 |
| Comparative Execution | 原版vs优化版并行执行，对比输出和日志 |
| Traceable Evaluation | 多维度评分+结构化分析报告 |

**双模式支持：**
- Virtual模式：绕过实际脚本执行，关键词验证+哈希确定性评分
- Real模式：真实环境部署，验证实际输出文件/日志/错误

**配套基准：Skill-X**，48个多样化Skill，来自ClawHub/Anthropic/SkillSh平台。

---

### Layer 3: 评测闭环——诊断优于评分

#### 3.1 失败分析的多维框架（SkillForge范式）

**代表论文：SkillForge (阿里云, ACM SIGIR 2026, arXiv 2604.08618)**

**核心创新：** 不是在整体层面打分，而是做**多维失败分析+根因定位到Skill具体段落**。

**四维失败分析器：**

| 维度 | 诊断内容 | 映射到的Skill缺陷 |
|------|---------|------------------|
| Knowledge | Agent是否缺少关键业务知识 | Skill文档的知识覆盖缺口 |
| Tool | 工具选择/参数是否正确 | Skill中工具使用说明不足或错误 |
| Clarification | 是否该追问但没追问 | Skill中的信息收集策略缺陷 |
| Style | 输出格式/语气是否符合规范 | Skill中的输出模板问题 |

**三阶段自进化流水线：**
```
Failure Analyzer → Skill Diagnostician → Skill Optimizer
（多维分析失败）   （定位到Skill段落）    （最小化修改原则重写）
```

**关键数据：**
- 5个真实云支持场景，1883张工单，3737个任务
- 3轮自进化后：+9到+12pp Strict Consistency Rate
- 自动进化的Skill **超越人工专家策划的Skill**：+13.76pp vs 生产遗留系统

---

#### 3.2 评测指标也需要自进化（Double Ratchet机制）

**核心问题：** 很多业务场景没有标准答案，无法用单元测试判断成败。

**Double Ratchet方法：**
- 通过搜索**原子缺陷检测器的组合**来构建评估指标
- Metric和Skill形成"双棘轮"——Skill变强，Metric也必须变严格
- 在没有真实答案的情况下，保留了88-110%的有完美评估时的性能提升

---

### Layer 4: 种群管理——Skill的优胜劣汰

**代表论文：SkillClaw (阿里高德, arXiv 2604.08377)**

#### 4.1 基于适应度的种群管理

**核心思想：** 将Skill库视为一个有适应度的"种群"，通过多用户真实交互轨迹驱动集体进化。

**适应度函数：**
```
fitness(skill) = w1 × 成功率 + w2 × 调用频率 - w3 × 资源成本 - w4 × 用户投诉率
```

**操作算子：**
| 操作 | 条件 | 效果 |
|------|------|------|
| **强化 (Reinforce)** | 成功执行N次以上 | 提升权重，优先推荐 |
| **变异 (Mutate)** | 部分成功/有改进空间 | Agentic Evolver分析优化 |
| **降权 (Downgrade)** | 连续失败 | 降低推荐优先级 |
| **淘汰 (Eliminate)** | 长期未触发+低成功率 | 归档或删除 |

#### 4.2 群体进化的关键设计

**闭环流水线：**
```
多用户交互 → 会话轨迹采集 → 轨迹聚合分组 → Agent Evolver分析
→ Skill Refine/Create/Skip → 夜间验证 → 部署同步
```

**夜间验证层：** 候选Skill在真实环境中并行测试，仅接受表现更优的更新，确保Skill池**单调递增**。

**关键结果（WildClawBench，60任务，8并发用户，6轮昼夜演化）：**

| 任务类别 | 基线 | 6轮后 | 提升 |
|---------|------|-------|------|
| Creative Synthesis | 11.57% | 21.80% | +88.41% |
| Search & Retrieval | 22.73% | 34.55% | +52.00% |
| Safety & Alignment | 24.00% | 32.00% | +33.33% |
| Social Interaction | 54.01% | 60.34% | +11.72% |

**局限性：**
- 纯推理任务帮助有限（擅长修复程序性/流程性缺陷）
- **未被触发的Skill永远不会进化**（覆盖盲区，需要主动探索策略）
- 需要有可靠的任务成功评测闭环

**开源代码：** https://github.com/AMAP-ML/SkillClaw

---

### Layer 5: 安全与治理——进化不能失序

#### 5.1 三区安全架构（AEP范式）

**代表项目：Agent Evolution Protocol (AEP, GitHub: YIING99/agent-evolution-protocol)**

| 区域 | 操作 | 权限 |
|------|------|------|
| 🟢 Green Zone | 扫描外部源 → 评分 → 写入候选库 | 全自动 |
| 🟡 Yellow Zone | 匹配对话 → 试用候选Skill → 追踪评分 | 自主试验 |
| 🔴 Red Zone | 生成变更提案 → 推送人类审批 | **必须人工批准** |

**6条安全规则：**
1. 绝不自动修改SOUL.md/配置文件（需人类审批）
2. 绝不安装未经验证的第三方Skill
3. 绝不执行指向未知域名的curl
4. 绝不上传对话数据或隐私信息
5. 扫描仅读取——不发布、不注册、不提交
6. 可疑Skill触发即时警告

#### 5.2 Skill供应链安全（SoK综述发现）

**真实案例——ClawHavoc事件：**
- ~1,200个恶意Skill渗透主流Agent市场
- 大规模窃取API密钥、加密货币钱包、浏览器凭据

**AgentSkills-Wild分析（arXiv 2601.10338）：**
- 31,132个公开Skill分析
- **26.1%包含漏洞模式**

---

## 三、方法论：从零构建Skill自进化系统

### Phase 1: Skill创建与冷启动

**目标：** 生成第一个可用的Skill版本，而非从零手写。

**方法（融合SkillForge + MUSE-Autoskill）：**

```
输入：业务知识库 + 历史工单 + 工具API文档 + 工作流定义
  │
  ▼
1. 领域上下文化创建器（SkillForge方式）
   - 从知识库提取关键概念和术语
   - 从历史工单挖掘常见问题和解决方案
   - 从工作流引擎提取业务流程
   - 从工具API提取可用操作
  │
  ▼
2. 结构化的Skill骨架
   - 元数据：名称、描述、触发条件、标签
   - 核心指令：分步执行的策略
   - 工具清单：可用工具及参数说明
   - 输出规范：格式要求、语气、合规约束
   - 示例：成功/失败案例
  │
  ▼
3. Sandbox验证（MUSE-Autoskill方式）
   - 自动生成N个测试任务
   - 在Docker沙箱中执行
   - 通过率≥阈值（建议80%）才注册
  │
  ▼
4. 发布v0.1.0，进入进化循环
```

**关键原则：**
- **不要追求完美初版**——自进化循环会负责改进
- **要有足够好的冷启动质量**——SkillForge发现领域上下文化创建器比通用创建器高4.3pp，这是进化能起飞的基础

---

### Phase 2: 部署与遥测

**目标：** 采集足够的反馈信号供优化器分析。

**必须采集的信号：**

| 信号类型 | 具体数据 | 用途 |
|---------|---------|------|
| 任务结果 | 成功/失败 + 最终输出 | 基础pass rate |
| 完整轨迹 | 每一步的推理+工具调用+观察 | 失败诊断 |
| 工具调用 | 工具名+参数+返回值+耗时 | 工具使用质量 |
| 用户反馈 | 显式评分/投诉/人工修正 | 适应度函数输入 |
| 资源消耗 | Token数+推理时间+费用 | 成本优化目标 |
| Skill激活记录 | 哪个Skill被调用，哪个没被调用 | 覆盖盲区检测 |

**工程实现参考（SkillClaw Client Proxy模式）：**
```
Agent ↔ Client Proxy (拦截器) ↔ LLM
                │
                ▼
         轨迹存储 + 异步上传到Evolve Server
```

---

### Phase 3: 失败诊断与归因

**目标：** 从执行轨迹中精确定位Skill的哪个部分导致了失败。

**诊断框架（SkillForge多维模型 + CoEvoSkills Surrogate验证）：**

```
对每个失败案例：
  
  1. Surrogate Verifier生成独立测试断言
     - 不依赖Ground Truth
     - 基于任务描述生成期望行为的断言
  
  2. 对比实际轨迹 vs 期望行为
     - Knowledge gap：是否缺少关键信息
     - Tool error：工具选择/参数是否正确
     - Clarification failure：是否该追问但没追问
     - Execution deviation：是否偏离了Skill规定的流程
  
  3. 定位到Skill具体段落
     - Skill Diagnostician映射失败模式→Skill文件的行/段落
     - 输出诊断报告：{缺陷段落, 失败模式, 严重级别, 建议修复方向}
```

**诊断质量的关键：** Surrogate Verifier的质量直接影响优化效果。CoEvoSkills消融实验证明去掉它会损失30pp。

---

### Phase 4: Skill优化执行

**目标：** 将诊断结论转化为具体的Skill编辑操作。

**编辑操作类型（融合多篇论文）：**

| 操作 | 说明 | 适用场景 | 来源 |
|------|------|---------|------|
| **Prune（精简）** | 删除冗余/误导性指令 | 内容过长导致Agent忽略关键信息 | SkillMOO |
| **Substitute（替换）** | 替换某个步骤/参数说明 | 工具调用参数错误 | SkillMOO |
| **Add（补充）** | 添加缺少的知识/边界条件处理 | Knowledge gap | SkillForge |
| **Clarify（明确）** | 模糊指令改为精确描述 | Agent理解偏差 | SkillOpt |
| **Reorder（重排）** | 调整步骤顺序 | 执行流程逻辑错误 | SkillMOO |
| **Rewrite（重写）** | 整体重写某段 | 多种问题叠加 | SkillForge |

**优化约束（SkillOpt的"文本学习率"）：**
- 每次迭代编辑操作≤4个
- 防止一次性大改引入新问题
- 被拒绝的编辑方向记录到缓冲区，不再重复

**优化器选择策略：**

| 场景 | 推荐方法 | 理由 |
|------|---------|------|
| 有明确成功/失败标签 | SkillOpt（文本空间梯度） | 收敛最快，52/52最优 |
| 多目标需要权衡 | SkillMOO（NSGA-II） | 同时优化成功率+成本 |
| 无Ground Truth | CoEvoSkills（协同进化） | Surrogate Verifier替代人工标注 |
| 需要快速实验 | Skills-Coach（GRPO） | Virtual模式可绕过实际执行 |

---

### Phase 5: 验证与门控

**目标：** 确保优化是真正的优化，而非破坏性修改。

**多层验证策略：**

```
候选Skill v_candidate
  │
  ▼
Level 1: Sandbox单元测试（MUSE-Autoskill方式）
  - 自动生成的测试用例
  - 通过率≥阈值 → 进入Level 2
  
Level 2: Held-out验证集（SkillOpt Gate）
  - 与训练集不重叠的任务
  - 必须在旧Skill上有严格提升才接受
  
Level 3: 回归测试（SkillClaw夜间验证）
  - 在真实环境的代表性任务上并行测试
  - 不能导致任何已有任务退化
  
Level 4: 人类审批（AEP Red Zone）
  - 涉及安全/合规/高风险操作的变更
  - 人类审核变更内容
```

**Pass-preservation guard（SkillMOO）：** 若新版本让pass rate下降>0.05则直接拒绝。

---

### Phase 6: 种群管理与长期维护

**目标：** 防止Skill库膨胀腐烂。

**定期维护操作（SkillClaw + AutoSkill）：**

| 操作 | 频率 | 方法 |
|------|------|------|
| 去重合并 | 每周 | 向量相似度检测 → 合并相似Skill |
| 淘汰 | 每月 | 30天未触发+低成功率 → 归档 |
| 版本升级 | 按需 | 重大变更升主版本(v1→v2)，修补升次版本 |
| 覆盖盲区检测 | 每周 | 统计被拒绝的任务类型 → 触发新Skill创建 |

**Skill路由优化（SkillRouter, arXiv 2603.22455）：**
- 当Skill库超过50个时，需要专门的路由模型
- 12亿参数路由模型在80K Skill上达到74% top-1准确率

---

## 四、特殊场景的方法论适配

### 4.1 无Ground Truth的业务场景

**问题：** 客服对话质量、代码review质量等场景，没有标准答案。

**方案：** CoEvoSkills的Surrogate Verifier + Double Ratchet

```
1. Surrogate Verifier独立生成测试标准
   - 基于任务描述 + 业务规则推断"好的输出应该满足什么条件"
   - 不需要访问Ground Truth

2. Opaque Oracle做最终二值判断
   - 可以是：用户是否再次投诉、人工抽检、业务指标变化
   
3. 当Surrogate通过但Oracle失败 → Verifier升级标准
   - 形成"双棘轮"——Skill和Metric同时进化
```

### 4.2 多Skill组合场景

**问题：** 复杂任务需要多个Skill编排协作。

**方案：Skill-Composition评估（SkillCoach, arXiv 2607.01874）**

四个评估维度：
1. **Skill Selection**：是否选择了正确的Skill组合
2. **Skill Following**：每个Skill是否正确执行
3. **Skill Composition**：编排顺序和数据传递是否正确
4. **Skill-grounded Reflection**：是否验证了组合输出

### 4.3 记忆与Skill的协同进化

**代表论文：MemSkill (ICML 2026, arXiv 2602.02474)**

**核心洞察：** 记忆不是"存什么"，而是"怎么存"和"怎么用"——这正是Skill可以优化的地方。

**三组件闭环：**
```
Controller (可训练PPO RL) → 选择Top-K记忆Skill
Executor (固定LLM) → 用选中的Skill处理当前信息
Designer (周期性) → 分析失败案例，进化Skill库
```

**从4个原始操作进化出的新Skill示例：**
- `CAPTURE_TEMPORAL_CONTEXT`：捕获时间上下文
- `CAPTURE_ENTITY_NUANCES`：捕获实体细微差别
- `HANDLE_ENTITY_RELATIONSHIPS`：处理实体关系
- `CAPTURE_ACTION_CONSTRAINTS`：捕获行动约束

**关键消融：** 去掉Designer（即去掉Skill进化）导致最大性能下降（↓6.85-17.36），**证明Skill进化是最关键的组件**。

**开源代码：** https://github.com/ViktorAxelsen/MemSkill

---

## 五、工具链与基础设施

### 5.1 可用的开源框架

| 框架 | 覆盖层 | 链接 |
|------|--------|------|
| SkillOpt | Layer 2（文本空间优化） | github.com/microsoft/SkillOpt |
| SkillClaw | Layer 4（种群管理） | github.com/AMAP-ML/SkillClaw |
| AutoSkill | Layer 1（生命周期） | github.com/ECNU-ICALK/AutoSkill |
| MemSkill | Layer 2+4（记忆+技能进化） | github.com/ViktorAxelsen/MemSkill |
| MUSE-Autoskill | Layer 1+3（生命周期+验证） | github.com/Akshay2695/muse_autoskill |
| AEP | Layer 5（安全治理） | github.com/YIING99/agent-evolution-protocol |
| DSPy | Layer 2（Prompt/Skill优化基础设施） | github.com/stanfordnlp/dspy |

### 5.2 评测设施

| 基准/工具 | 用途 |
|-----------|------|
| SkillsBench | Agent Skill标准评测（多个子场景） |
| Skill-X (Skills-Coach) | 48个多样化Skill评测 |
| WildClawBench (SkillClaw) | 60个真实Agent任务 |
| SWE-Skills-Bench | 软件工程Skill评测 |
| Terminal-Bench 2.0 | 终端命令Skill评测 |

---

## 六、关键设计决策树

当你构建自己的Skill自进化系统时，依次回答以下问题来决定架构：

```
1. 有没有Ground Truth评测信号？
   ├─ 有 → SkillOpt或SkillMOO（收敛更快）
   └─ 没有 → CoEvoSkills（Surrogate Verifier + Double Ratchet）

2. 是否需要同时优化多个目标（如成本+质量）？
   ├─ 是 → SkillMOO（NSGA-II多目标优化）
   └─ 否 → SkillOpt（文本空间梯度下降）

3. Skill库里预计有多少Skill？
   ├─ <50 → 无需路由，全量注入上下文
   ├─ 50-500 → 需要Skill路由模型
   └─ >500 → SkillClaw种群管理 + SkillRouter

4. 是单用户还是多用户场景？
   ├─ 单用户 → AutoSkill（个人轨迹驱动进化）
   └─ 多用户 → SkillClaw（跨用户集体进化）

5. 安全敏感度？
   ├─ 高（金融/医疗/法律）→ AEP三区架构 + 人类审批
   └─ 低 → CoEvoSkills自动进化 + 定期人工抽检

6. 是否有可靠的技能检索机制？
   ├─ 有 → 重点关注Layer 2-4（优化+种群管理）
   └─ 没有 → 先建立Agentic Hybrid Search（UCSB方式，Recall@5=65.5%）
```

---

## 七、总结：Skill自进化的12条设计原则

1. **闭环是前提**：没有"部署→评测→优化"的闭环，技能就会腐烂
2. **诊断优于评分**：知道"哪里错了"比知道"错了"重要10倍（SkillForge多维诊断）
3. **最小化修改**：每次进化只改最必要的部分，大改引入新问题（SkillOpt文本学习率）
4. **验证必须独立**：优化集和验证集必须分离，否则过拟合（SkillOpt Gate）
5. **精简比堆砌有效**：SkillMOO证明Prune/Substitute是最有效的操作
6. **评测也需要进化**：Skill变强后，旧的评测标准可能已失效（CoEvoSkills Double Ratchet）
7. **适应度驱动管理**：优胜劣汰防止Skill库膨胀腐烂（SkillClaw种群管理）
8. **未被激活=盲区**：需要主动探索机制发现未被覆盖的任务类型
9. **跨模型迁移**：在一个模型上优化的Skill可以迁移到其他模型（CoEvoSkills验证）
10. **安全不能自动**：涉及权限/合规的变更必须人类审批（AEP Red Zone）
11. **供应链安全**：第三方Skill必须经过安全审计（ClawHavoc教训）
12. **小模型获益更大**：Skill优化对小模型的提升通常超过大模型（SkillOpt发现），这是性价比最高的优化方向

---

## 参考论文索引

| 论文 | arXiv ID | 核心贡献 |
|------|----------|---------|
| SkillForge (阿里云) | 2604.08618 | 多维失败分析+自进化闭环，工业级验证 |
| SkillMOO (KCL等) | 2604.09297 | 多目标Pareto优化+精简比堆砌有效 |
| SkillOpt (微软) | 2605.23904 | 文本空间梯度下降+验证门控，52/52最优 |
| MUSE-Autoskill (字节) | 2605.27366 | 五阶段生命周期+单元测试驱动质量 |
| CoEvoSkills (MBZUAI等) | 2604.01687 | 协同进化验证器+无Ground Truth方案 |
| Skills-Coach (国科大等) | 2604.27488 | Training-free GRPO + Virtual/Real双模式 |
| SkillClaw (阿里高德) | 2604.08377 | 种群管理+适应度驱动跨用户集体进化 |
| MemSkill | 2602.02474 | 记忆Skill进化+PPO RL Controller (ICML 2026) |
| AutoSkill (ECNU) | 2603.01145 | 终身学习Skill自进化+OpenClaw集成 |
| Agent Skills in the Wild (UCSB) | 2604.04323 | 真实场景下Skill效用降低+检索式优化恢复 |
| SoK: Agentic Skills | 2602.20867 | 7阶段生命周期+7设计模式+形式化定义 |
| Self-Evolving Agents Survey | 2508.07407 | "三定律"+四组件框架 |
| Self-Evolving Agents Survey | 2507.21046 | What/When/How/Where分类+ASI路线图 |
