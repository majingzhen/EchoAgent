# EchoAgent - 企业 AI 营销智能体平台 设计文档

## 一、项目概述

### 1.1 定位

EchoAgent 是一个面向企业的综合 AI 营销智能体平台。核心能力是通过多 Agent 群体模拟，让企业在真正投放前"听到"市场的回声——预见目标用户的反应、验证营销策略的效果、预判舆情风险。

**一句话**：不只帮你做内容，还能帮你模拟市场来验证内容。

### 1.2 核心差异化

| 维度 | 传统 AI 营销工具 | EchoAgent |
|------|-----------------|-----------|
| 内容生产 | 单 Agent 生成文案 | 多 Agent 协作生产（策划+文案+消费者视角碰撞） |
| 效果验证 | 写完就投，赌效果 | 写完先模拟，验证后再投 |
| 用户理解 | 人工定义用户画像 | AI 自动构建可对话的虚拟用户群 |
| 工具关系 | 单点工具，互不关联 | 完整闭环，数据在模块间自动流转 |
| 决策支持 | 给一个答案 | 多视角分析，展示决策全貌 |

### 1.3 核心壁垒

**你能模拟目标客户群体**。别的工具只能帮企业"生成内容"，EchoAgent 能帮企业"预见反应"。

### 1.4 技术传承

基于 MiroFish 多智能体预测引擎的核心能力演化而来：

| 能力 | MiroFish | EchoAgent |
|------|---------|-----------|
| Agent 人设生成 | 从文档提取实体 | 多来源（描述/CRM/调研数据） |
| 社交模拟 | OASIS 学术框架 | 自研模拟引擎，可定制国内平台 |
| 报告生成 | ReACT 单 Agent | ReACT + 多 Agent 交叉验证 |
| 知识图谱 | Zep Cloud（第三方） | 自建 Neo4j（完全可控） |
| Web 框架 | Flask（同步） | FastAPI（异步） |
| 数据存储 | 文件系统 JSON | MySQL + Neo4j + Redis |
| 实时通信 | 前端轮询 | WebSocket 实时推送 |
| 多租户 | 无 | 企业级多租户隔离 |

## 二、平台架构总览

### 2.1 营销闭环

六个模块形成完整的营销链路，数据在模块间自动流转：

```
  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │   ① 市场智脑 ──→ ③ 内容工坊 ──→ ④ 沙盘推演         │
  │       ↑              ↑     ↗         │               │
  │       │         洞察指导创作    模拟结果反馈优化       │
  │       │              │                │               │
  │       │    ② 画像工厂 ─────→ 提供模拟群体            │
  │       │                               │               │
  │       │         ⑤ 舆情哨兵 ←── 异常触发              │
  │       │              │                                │
  │       │              ↓                                │
  │       └──── ⑥ 策略参谋 ← 需要深度分析时调用          │
  │                                                      │
  └──────────────────────────────────────────────────────┘
```

### 2.2 分层架构

```
┌─────────────────────────────────────────────┐
│                  接入层                      │
│   Web 工作台 | REST API | 企业系统对接       │
├─────────────────────────────────────────────┤
│                  应用层                      │
│  市场智脑 | 画像工厂 | 内容工坊             │
│  沙盘推演 | 舆情哨兵 | 策略参谋             │
├─────────────────────────────────────────────┤
│                  编排层                      │
│  工作流引擎（模块间数据管道 + 触发器）       │
├─────────────────────────────────────────────┤
│                  Agent 层                    │
│  人格系统 | 记忆系统 | 工具系统 | 情绪系统   │
├─────────────────────────────────────────────┤
│                  知识层                      │
│  企业知识图谱(Neo4j) | 用户画像库 | 行业库  │
├─────────────────────────────────────────────┤
│                  基础设施                    │
│  FastAPI | MySQL | Redis | LLM API | Docker │
└─────────────────────────────────────────────┘
```

### 2.3 技术栈

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 前端框架 | Vue 3 + Composition API | 响应式，组件化 |
| 前端 UI | Tailwind CSS 4 | 快速构建界面 |
| 数据可视化 | ECharts + D3.js | 图表 + 图谱 |
| 后端框架 | FastAPI | 异步，WebSocket 原生支持 |
| LLM 集成 | OpenAI SDK 兼容格式 | 灵活切换模型 |
| 知识图谱 | Neo4j | 图数据库，复杂关系查询 |
| 关系数据库 | MySQL | 结构化业务数据 |
| 缓存 | Redis | 会话状态、排行、限流 |
| 部署 | Docker Compose | 一键启动 |

## 三、模块一：画像工厂（Persona Factory）

### 3.1 定位

将抽象的"目标用户"变成**可对话、可复用的 Agent 群体**。企业描述目标人群特征，系统自动生成多个差异化的虚拟用户 Agent，每个都有独立的性格、消费习惯、决策逻辑。

### 3.2 画像生成流程

```
用户输入目标人群描述
  |
  v
PersonaPlanner（LLM）
  |- 分析人群描述
  |- 确定关键差异维度（消费力/决策风格/信息渠道/价值观）
  |- 规划 N 个典型画像的分布（如：30% 价格敏感 / 40% 品质导向 / 30% 尝鲜型）
  |
  v
PersonaGenerator（LLM x N）
  |- 为每个画像生成完整人设：
  |  |- 基础属性（姓名/年龄/性别/城市/职业/收入）
  |  |- 性格特征（MBTI/大五人格/沟通风格）
  |  |- 消费画像（价格敏感度/品牌忠诚度/决策因素/购买频率）
  |  |- 信息渠道（常用社交平台/关注的KOL/获取信息的方式）
  |  |- 价值观标签（环保/性价比/颜值/健康/便捷）
  |  |- 社交行为模式（发帖频率/互动偏好/意见领袖程度）
  |
  v
画像入库（画像库 + Neo4j 关系网络）
  |- 画像间建立社交关系（朋友/同事/家人/KOL-粉丝）
  |- 标注影响力传播路径
```

### 3.3 画像数据结构

```python
class PersonaProfile:
    # 基础信息
    id: str
    name: str
    age: int
    gender: str
    city: str
    occupation: str
    monthly_income: int

    # 性格模型
    personality: PersonalityModel
    mbti: str                          # ENFP / ISTJ 等
    communication_style: str           # 直接型/委婉型/分析型/感性型

    # 消费画像
    consumer: ConsumerProfile
    price_sensitivity: float           # 0-1，价格敏感度
    brand_loyalty: float               # 0-1，品牌忠诚度
    decision_factors: list[str]        # ["口碑", "价格", "颜值", "功效"]
    purchase_frequency: str            # 冲动型/计划型/比价型
    monthly_disposable: int            # 月可支配消费金额

    # 信息行为
    media: MediaBehavior
    platforms: list[str]               # ["小红书", "抖音", "微信"]
    content_preference: list[str]      # ["测评", "种草", "教程"]
    influence_susceptibility: float    # 0-1，被影响程度
    influence_power: float             # 0-1，影响他人能力

    # 社交行为
    social: SocialBehavior
    post_frequency: str                # 高频/低频/潜水
    interaction_style: str             # 点赞派/评论派/转发派/沉默派
    stance_on_ads: str                 # 反感/中立/感兴趣

    # Agent 行为参数
    agent_config: AgentBehaviorConfig
    activity_level: float              # 0-1，整体活跃度
    sentiment_bias: float              # -1~1，情感倾向
    critical_thinking: float           # 0-1，批判性思维程度
    herd_mentality: float              # 0-1，从众程度
```

### 3.4 虚拟焦点小组

画像工厂的核心交互模式——企业可以直接和虚拟用户群对话：

```
企业提问："你觉得这款产品定价 299 元贵吗？"
  |
  v
系统将问题发送给画像库中选定的 N 个 Agent
  |
  v
每个 Agent 基于自己的人设独立回答：
  |- Agent_张小花（价格敏感型）："299 有点贵了，同类产品 XX 才 199..."
  |- Agent_李明（品质导向型）："如果品质够好可以接受，关键看成分表..."
  |- Agent_王大锤（尝鲜型）："新品牌没听过，但包装好看可以试试..."
  |
  v
FocusGroupAnalyzer（LLM）汇总：
  |- 共识点：XX% 认为价格偏高
  |- 分歧点：品质派 vs 价格派的核心争议
  |- 关键洞察：消费者最关心的是 XXX
  |- 建议：可考虑 XXX 定价策略
```

### 3.5 画像来源支持

| 来源 | 输入格式 | 适用场景 |
|------|---------|---------|
| 文本描述 | "25-35岁一线城市白领女性..." | 快速生成，无数据积累时 |
| 用户调研 | 问卷结果 CSV / 调研报告 | 基于真实数据生成 |
| CRM 导出 | 客户列表 + 交易数据 | 现有客户群画像 |
| 社媒数据 | 评论/反馈文本 | 捕捉真实用户声音 |

## 四、模块二：沙盘推演（Sand Table）

### 4.1 定位

在模拟社交环境中测试营销内容/策略的效果。将画像工厂生成的虚拟用户群放入模拟社交平台，观察他们对内容的自然反应。

### 4.2 模拟平台模型

不同于 MiroFish 使用 OASIS 学术框架，EchoAgent 自研轻量模拟引擎，支持国内平台模型：

```python
class PlatformModel:
    """社交平台行为模型"""
    name: str                          # 平台名称
    content_types: list[str]           # 支持的内容类型
    interaction_types: list[str]       # 支持的互动类型
    algorithm_bias: dict               # 算法推荐偏好
    viral_threshold: float             # 传播临界点


# 预置平台模型
XIAOHONGSHU = PlatformModel(
    name="小红书",
    content_types=["图文笔记", "视频笔记", "直播"],
    interaction_types=["点赞", "收藏", "评论", "转发", "关注"],
    algorithm_bias={
        "engagement_weight": 0.4,      # 互动率权重高
        "freshness_weight": 0.3,       # 时效性
        "creator_weight": 0.2,         # 创作者权重
        "content_quality": 0.1         # 内容质量
    },
    viral_threshold=0.15               # 互动率超过 15% 进入推荐池
)

DOUYIN = PlatformModel(
    name="抖音",
    content_types=["短视频", "直播", "图文"],
    interaction_types=["点赞", "评论", "转发", "收藏", "关注", "完播"],
    algorithm_bias={
        "completion_rate": 0.35,       # 完播率最重要
        "engagement_weight": 0.3,
        "share_weight": 0.2,
        "freshness_weight": 0.15
    },
    viral_threshold=0.10
)

WECHAT_MOMENTS = PlatformModel(
    name="微信朋友圈",
    content_types=["图文", "链接", "视频"],
    interaction_types=["点赞", "评论", "私聊转发"],
    algorithm_bias={
        "relationship_weight": 0.6,    # 关系链权重极高
        "recency_weight": 0.3,
        "engagement_weight": 0.1
    },
    viral_threshold=0.05               # 私域传播阈值低
)

WEIBO = PlatformModel(
    name="微博",
    content_types=["文字", "图文", "视频", "话题"],
    interaction_types=["点赞", "评论", "转发", "超话"],
    algorithm_bias={
        "hot_topic_weight": 0.3,
        "engagement_weight": 0.3,
        "follower_weight": 0.25,
        "freshness_weight": 0.15
    },
    viral_threshold=0.08
)
```

### 4.3 模拟引擎

```python
class SimulationEngine:
    """社交传播模拟引擎"""

    async def run_simulation(
        self,
        content: MarketingContent,      # 待测试的营销内容
        personas: list[PersonaProfile],  # 参与模拟的虚拟用户
        platform: PlatformModel,         # 模拟平台
        config: SimulationConfig         # 模拟参数
    ) -> SimulationResult:

        # 1. 初始化社交网络
        network = self.build_social_network(personas)

        # 2. 内容曝光阶段（模拟算法推荐）
        exposed_agents = self.initial_exposure(
            content, personas, platform, config.initial_exposure_rate
        )

        # 3. 模拟循环
        for round_num in range(config.max_rounds):
            round_actions = []

            for agent in self.get_active_agents(personas, round_num):
                # Agent 决策：看到内容后怎么做
                action = await self.agent_decide(
                    agent=agent,
                    content=content,
                    platform=platform,
                    social_context=self.get_social_context(agent, network),
                    history=self.history
                )
                round_actions.append(action)

                # 行为传播：Agent 的行为影响其社交圈
                if action.is_spreading:  # 转发/分享/评论
                    new_exposed = self.propagate(agent, action, network, platform)
                    exposed_agents.extend(new_exposed)

            # 4. 更新平台状态（热度、排名等）
            self.update_platform_state(round_actions, platform)

            # 5. 实时指标计算
            metrics = self.calculate_metrics(round_num)
            await self.emit_progress(metrics)

            # 6. 检查是否达到稳态
            if self.is_stable(metrics):
                break

        return self.compile_result()
```

### 4.4 Agent 决策模型

每个 Agent 看到内容后的决策过程：

```python
class AgentDecisionEngine:
    """Agent 内容反应决策"""

    async def decide(
        self,
        agent: PersonaProfile,
        content: MarketingContent,
        social_context: SocialContext
    ) -> AgentAction:

        # 构建决策上下文
        prompt = f"""你是 {agent.name}，{agent.age}岁，{agent.occupation}。
性格：{agent.personality_description}
消费特征：价格敏感度 {agent.price_sensitivity}，品牌忠诚度 {agent.brand_loyalty}
决策因素：{agent.decision_factors}
社交风格：{agent.interaction_style}

你在{content.platform}上看到了这条内容：
---
{content.text}
---

你身边的朋友反应：
{social_context.friends_reactions}

请以你的身份，真实地回答：
1. 你会怎么做？（忽略/点赞/评论/转发/收藏/私信好友）
2. 如果评论，你会说什么？
3. 你对这个产品/品牌的印象如何？（-10到10分）
4. 你有购买意愿吗？（0-100%）
5. 简述你的真实想法（一句话）"""

        response = await self.llm.generate_json(prompt)
        return AgentAction.from_llm_response(response, agent.id)
```

### 4.5 模拟结果分析

```python
class SimulationAnalyzer:
    """模拟结果分析器"""

    def analyze(self, result: SimulationResult) -> SimulationReport:
        return SimulationReport(
            # 核心指标
            metrics=MetricsSummary(
                reach_rate=self.calc_reach_rate(),          # 触达率
                engagement_rate=self.calc_engagement_rate(), # 互动率
                sentiment_score=self.calc_sentiment(),       # 情感得分
                purchase_intent=self.calc_purchase_intent(), # 购买意愿
                viral_coefficient=self.calc_viral_coeff(),   # 传播系数
                nps_score=self.calc_nps()                    # 净推荐值
            ),

            # 人群细分分析
            segment_analysis=[
                SegmentResult(
                    segment="价格敏感型",
                    reaction="普遍觉得贵，但对XX功能感兴趣",
                    purchase_intent=0.25,
                    key_concern="价格"
                ),
                SegmentResult(
                    segment="品质导向型",
                    reaction="关注成分和效果，愿意尝试",
                    purchase_intent=0.65,
                    key_concern="功效证明"
                ),
                # ...
            ],

            # 传播路径分析
            propagation=PropagationAnalysis(
                key_spreaders=["Agent_XX", "Agent_YY"],     # 关键传播节点
                viral_triggers=["XX话题引发讨论"],           # 病毒传播触发点
                bottlenecks=["XX群体阻断了传播"],            # 传播瓶颈
                peak_time=5                                  # 传播峰值轮次
            ),

            # 评论词云
            comment_themes=["性价比", "包装", "成分", "竞品对比"],

            # 风险点
            risks=["XX群体可能产生负面评价，集中在XX方面"],

            # 优化建议
            suggestions=[
                "针对价格敏感群体，建议强调XX卖点",
                "文案中增加XX信息可提升XX群体的信任度",
                "建议在XX时间段投放，目标群体活跃度最高"
            ]
        )
```

### 4.6 A/B 测试模式

支持同时测试多版内容，对比效果：

```
输入：3 版营销文案 + 同一批虚拟用户
  |
  v
并行运行 3 次模拟（相同用户群 + 不同内容）
  |
  v
对比报告：
  | 指标         | 版本A  | 版本B  | 版本C  |
  |-------------|--------|--------|--------|
  | 触达率       | 45%    | 62%    | 38%    |
  | 互动率       | 8%     | 15%    | 12%    |
  | 情感得分     | 6.2    | 7.8    | 8.5    |
  | 购买意愿     | 22%    | 35%    | 40%    |
  | 传播系数     | 0.8    | 1.5    | 1.1    |
  | 风险指数     | 低     | 中     | 低     |
  |-------------|--------|--------|--------|
  | 推荐         |        | 爆款型 | 口碑型 |
```

## 五、模块三：内容工坊（Content Workshop）

### 5.1 定位

多 Agent 协作生产营销内容。不是单 Agent 直接生成文案，而是让策划、文案、消费者视角的 Agent 碰撞出更好的内容。

### 5.2 创作 Agent 角色

```python
# 策划 Agent - 负责创意方向
STRATEGIST = AgentRole(
    role="营销策划",
    responsibility="分析市场洞察，确定创意方向和核心卖点",
    thinking_style="数据驱动 + 用户视角",
    output="创意 brief（目标、卖点、调性、切入角度）"
)

# 文案 Agent - 负责内容创作
COPYWRITER = AgentRole(
    role="资深文案",
    responsibility="基于 brief 创作具体文案内容",
    thinking_style="感性表达 + 传播力优先",
    output="完整的营销文案（标题、正文、CTA）"
)

# 消费者 Agent - 从画像工厂调用
CONSUMER_REVIEWER = AgentRole(
    role="目标消费者代表",
    responsibility="以真实消费者视角评价内容",
    thinking_style="基于自身人设的真实反应",
    output="评价反馈（吸引力/可信度/购买意愿/改进建议）"
)

# 品牌守护 Agent - 确保品牌一致性
BRAND_GUARDIAN = AgentRole(
    role="品牌经理",
    responsibility="检查内容是否符合品牌调性和规范",
    thinking_style="品牌价值观 + 合规性",
    output="品牌一致性评分 + 修改建议"
)
```

### 5.3 创作流程

```
Step 1: 策划 Agent 生成 3 个创意方向
  |
  v
Step 2: 文案 Agent 为每个方向各写一版内容
  |
  v
Step 3: 消费者 Agent（3-5个）评价每版内容
  |- "这个标题吸引我，但正文太长了"
  |- "卖点不够突出，我看不出为什么要买"
  |- "图片好看但文字太硬广了"
  |
  v
Step 4: 文案 Agent 根据消费者反馈优化
  |
  v
Step 5: 品牌守护 Agent 检查品牌一致性
  |
  v
Step 6: 输出最终版本（可选：送入沙盘推演做进一步验证）
```

### 5.4 内容类型支持

| 类型 | 输出格式 | 平台适配 |
|------|---------|---------|
| 种草笔记 | 标题 + 正文 + 标签 | 小红书 |
| 短视频脚本 | 分镜 + 口播文案 + 字幕 | 抖音/快手 |
| 朋友圈文案 | 短文案 + 配图建议 | 微信 |
| 产品详情页 | 卖点提炼 + 场景描述 | 电商平台 |
| 推文/博文 | 话题 + 正文 + 互动引导 | 微博 |
| 广告文案 | 标题 + 描述 + CTA | 信息流广告 |
| 营销邮件 | 主题行 + 正文 + CTA | EDM |
| 活动方案 | 主题 + 机制 + 传播策略 | 全渠道 |

## 六、模块四：市场智脑（Market Mind）

### 6.1 定位

自动构建行业竞争格局知识图谱，持续追踪市场变化，为其他模块提供市场洞察输入。

### 6.2 核心能力

```
输入：行业资料 / 竞品信息 / 研报 / 新闻
  |
  v
OntologyExtractor（LLM）
  |- 提取实体：品牌、产品、技术、人物、渠道、供应商
  |- 提取关系：竞争、合作、供应、投资、收购
  |- 提取属性：市场份额、定价、定位、优势、劣势
  |
  v
KnowledgeGraphBuilder（Neo4j）
  |- 构建行业关系网络
  |- 标注关系强度和时间有效性
  |- 支持增量更新（新资料追加）
  |
  v
InsightGenerator（LLM + 图谱查询）
  |- 竞品对比分析
  |- 市场空白识别
  |- 趋势预测
  |- 威胁预警
```

### 6.3 洞察输出

```python
class MarketInsight:
    competitive_landscape: CompetitiveLandscape
    # 竞品定位图（价格 x 功能矩阵）
    # 各品牌市场份额
    # 差异化程度评估

    market_gaps: list[MarketGap]
    # 价位空白
    # 功能空白
    # 人群空白
    # 渠道空白

    threats: list[Threat]
    # 新进入者威胁
    # 替代品威胁
    # 供应商议价力变化
    # 政策风险

    opportunities: list[Opportunity]
    # 趋势红利
    # 竞品弱点
    # 未满足需求
```

### 6.4 与其他模块的数据流

- 洞察 → **内容工坊**：自动注入市场背景，指导创意方向（"竞品在XX卖点上做得不够，我们可以主打"）
- 洞察 → **沙盘推演**：提供竞品信息给模拟 Agent（让 Agent 能做出"和竞品比较"的反应）
- 洞察 → **策略参谋**：作为决策分析的输入数据

## 七、模块五：舆情哨兵（Sentiment Guard）

### 7.1 定位

预判舆情风险，模拟负面事件的传播路径，自动生成应对方案并验证效果。

### 7.2 工作模式

#### 模式 A：事前预判

```
输入：一个潜在风险事件描述
  |
  v
RiskAssessor（LLM）
  |- 评估事件严重程度
  |- 识别可能被引爆的话题点
  |- 预测最先反应的人群类型
  |
  v
SpreadSimulator（模拟引擎）
  |- 生成不同立场的 Agent（消费者/媒体人/竞品/忠实粉/路人）
  |- 模拟事件在社交平台的传播
  |- 记录传播路径和转折点
  |
  v
ResponseGenerator（LLM）
  |- 生成 3 套应对方案
  |  |- 方案A：快速回应 + 道歉 + 补偿
  |  |- 方案B：冷处理 + 背景说明
  |  |- 方案C：正面回应 + 转移焦点
  |
  v
ResponseValidator（模拟引擎 x 3）
  |- 分别模拟每套方案的效果
  |- 对比舆情走势、情感变化、平息速度
  |
  v
输出：最优方案 + 预期效果 + 执行时间窗口
```

#### 模式 B：事后应对

```
输入：已发生的负面事件 + 当前舆情状态
  |
  v
SituationAnalyzer（LLM）
  |- 分析当前局势
  |- 识别关键意见领袖和传播节点
  |- 评估剩余应对窗口
  |
  v
ResponseGenerator + ResponseValidator
  |（同模式 A，但基于当前真实状态）
  v
输出：紧急应对方案 + 分阶段执行步骤
```

## 八、模块六：策略参谋（Strategy Advisor）

### 8.1 定位

用多种思维模型同时分析同一个业务问题，让企业看到决策的全貌。

### 8.2 思维模型 Agent

```python
THINKING_MODELS = {
    "first_principles": {
        "name": "第一性原理",
        "approach": "剥离表象回到本质，从基本事实出发推理",
        "question": "这个问题的本质是什么？哪些是不可简化的基本事实？"
    },
    "game_theory": {
        "name": "博弈论",
        "approach": "分析各方利益和策略互动",
        "question": "各方的利益是什么？他们会怎么反应？纳什均衡在哪？"
    },
    "systems_thinking": {
        "name": "系统思维",
        "approach": "看整体结构和反馈回路",
        "question": "这个系统的关键反馈回路是什么？改变一处会如何影响全局？"
    },
    "inversion": {
        "name": "逆向思维",
        "approach": "反过来想，怎样才能失败",
        "question": "要让这件事彻底失败，需要怎么做？避免这些就是正确方向"
    },
    "customer_lens": {
        "name": "用户视角",
        "approach": "站在客户角度思考",
        "question": "如果我是客户，我真正需要什么？我会怎么选择？"
    }
}
```

### 8.3 分析流程

```
企业提问："我们要不要进入下沉市场？"
  |
  v
Phase 1: 独立分析
  |- 5 个思维模型 Agent 各自独立分析
  |- 每个给出结论 + 推理过程 + 关键假设
  |
  v
Phase 2: 交叉质疑
  |- 自动识别分歧最大的观点对
  |- 针对核心分歧进行 1v1 辩论
  |- 其他模型作为评审
  |
  v
Phase 3: 综合报告
  |- 共识点（所有模型都同意的）
  |- 分歧点（以及分歧的根源）
  |- 关键假设（哪些假设不同导致了结论不同）
  |- 盲区提醒（所有模型都可能忽略的）
  |- 决策建议（不是给答案，是给决策框架）
```

## 九、Agent 基座设计

### 9.1 统一 Agent 运行时

所有模块的 Agent 共享同一套基座能力：

```python
class BaseAgent:
    """Agent 基座"""

    # 身份系统
    identity: AgentIdentity
    name: str
    role: str
    persona: str                      # 完整人设描述

    # 记忆系统
    memory: AgentMemory
    short_term: list[Message]          # 短期记忆（当前会话）
    long_term: dict                    # 长期记忆（跨会话）
    episodic: list[Episode]            # 情景记忆（关键事件）

    # 工具系统
    tools: list[Tool]                  # 可调用的工具

    # 行为参数
    behavior: BehaviorConfig
    temperature: float                 # 创造性 vs 确定性
    response_style: str                # 回复风格

    async def think(self, context: str) -> str:
        """基于人设和上下文思考"""
        messages = self.build_messages(context)
        return await self.llm.generate(messages)

    async def react(self, stimulus: str, social_context: dict) -> AgentAction:
        """对刺激做出反应（用于模拟场景）"""
        pass

    async def interview(self, question: str) -> str:
        """接受采访/对话（用于焦点小组）"""
        pass
```

### 9.2 记忆管理

```python
class MemoryManager:
    """Agent 记忆管理"""

    def compress_history(self, messages: list[Message], max_tokens: int) -> list[Message]:
        """超过上下文窗口时自动压缩历史"""
        if self.count_tokens(messages) <= max_tokens:
            return messages
        # 保留最近的消息 + 压缩早期消息为摘要
        recent = messages[-10:]
        early = messages[:-10]
        summary = self.summarize(early)
        return [Message(role="system", content=f"之前的对话摘要：{summary}")] + recent

    def extract_key_memory(self, interaction: str) -> list[str]:
        """从交互中提取值得记住的关键信息"""
        pass

    def recall(self, query: str) -> list[str]:
        """根据查询检索相关记忆"""
        pass
```

## 十、编排层设计

### 10.1 工作流引擎

模块之间的数据流转通过工作流引擎管理：

```python
class WorkflowEngine:
    """模块间工作流编排"""

    # 预定义工作流
    WORKFLOWS = {
        "content_validation": {
            "name": "内容验证流",
            "steps": [
                {"module": "content_workshop", "action": "create"},
                {"module": "sand_table", "action": "simulate"},
                {"module": "content_workshop", "action": "optimize",
                 "input_from": "sand_table.result"}
            ]
        },
        "full_campaign": {
            "name": "完整营销活动流",
            "steps": [
                {"module": "market_mind", "action": "analyze"},
                {"module": "persona_factory", "action": "generate",
                 "input_from": "market_mind.target_audience"},
                {"module": "content_workshop", "action": "create",
                 "input_from": ["market_mind.insights", "persona_factory.personas"]},
                {"module": "sand_table", "action": "ab_test",
                 "input_from": ["content_workshop.contents", "persona_factory.personas"]},
                {"module": "sentiment_guard", "action": "risk_check",
                 "input_from": "sand_table.best_content"},
                {"module": "strategy_advisor", "action": "review",
                 "condition": "sentiment_guard.risk_level > 0.7"}
            ]
        }
    }

    async def execute(self, workflow_id: str, initial_input: dict):
        workflow = self.WORKFLOWS[workflow_id]
        context = initial_input

        for step in workflow["steps"]:
            # 检查条件
            if "condition" in step:
                if not self.evaluate_condition(step["condition"], context):
                    continue

            # 准备输入
            step_input = self.resolve_inputs(step, context)

            # 执行模块
            result = await self.execute_module(step["module"], step["action"], step_input)

            # 更新上下文
            context[f"{step['module']}.result"] = result

            # 推送进度
            await self.emit_progress(step, result)

        return context
```

### 10.2 触发器

```python
class TriggerManager:
    """跨模块触发器"""

    triggers = [
        # 沙盘推演发现高风险 → 自动触发舆情哨兵
        Trigger(
            source="sand_table",
            condition="risk_score > 0.7",
            target="sentiment_guard",
            action="risk_assessment"
        ),
        # 市场智脑发现竞品动作 → 通知策略参谋
        Trigger(
            source="market_mind",
            condition="competitor_event_detected",
            target="strategy_advisor",
            action="quick_analysis"
        ),
        # 画像更新 → 重新验证历史内容
        Trigger(
            source="persona_factory",
            condition="persona_updated",
            target="sand_table",
            action="revalidate_recent_content"
        )
    ]
```

## 十一、数据模型

### 11.1 核心表结构

```sql
-- 企业/租户
CREATE TABLE tenant (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'basic',
    config JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL
);

-- 用户
CREATE TABLE user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_user_tenant_id (tenant_id)
);

-- 画像库
CREATE TABLE persona (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    group_id BIGINT,
    name VARCHAR(100) NOT NULL,
    profile JSON NOT NULL,
    consumer_profile JSON NOT NULL,
    media_behavior JSON NOT NULL,
    social_behavior JSON NOT NULL,
    agent_config JSON NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_persona_tenant_id (tenant_id),
    INDEX idx_persona_group_id (group_id)
);

-- 画像组
CREATE TABLE persona_group (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    persona_count INT DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_persona_group_tenant_id (tenant_id)
);

-- 营销内容
CREATE TABLE content (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    title VARCHAR(500),
    body TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    metadata JSON,
    version INT DEFAULT 1,
    parent_id BIGINT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_content_tenant_id (tenant_id)
);

-- 模拟会话
CREATE TABLE simulation_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    content_id BIGINT,
    persona_group_id BIGINT,
    platform VARCHAR(50) NOT NULL,
    config JSON NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL,
    total_rounds INT DEFAULT 0,
    current_round INT DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_simulation_session_tenant_id (tenant_id),
    INDEX idx_simulation_session_content_id (content_id)
);

-- 模拟动作记录
CREATE TABLE simulation_action (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    round_num INT NOT NULL,
    persona_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_detail JSON NOT NULL,
    sentiment_score DECIMAL(3,2),
    purchase_intent DECIMAL(3,2),
    created_at DATETIME NOT NULL,
    INDEX idx_simulation_action_session_id (session_id),
    INDEX idx_simulation_action_round (session_id, round_num)
);

-- 模拟报告
CREATE TABLE simulation_report (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL UNIQUE,
    metrics JSON NOT NULL,
    segment_analysis JSON NOT NULL,
    propagation_analysis JSON NOT NULL,
    risks JSON,
    suggestions JSON,
    created_at DATETIME NOT NULL
);

-- A/B 测试
CREATE TABLE ab_test (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    persona_group_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status ENUM('pending', 'running', 'completed') NOT NULL,
    result_summary JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_ab_test_tenant_id (tenant_id)
);

-- A/B 测试变体
CREATE TABLE ab_test_variant (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    ab_test_id BIGINT NOT NULL,
    content_id BIGINT NOT NULL,
    session_id BIGINT,
    label VARCHAR(50) NOT NULL,
    metrics JSON,
    INDEX idx_ab_test_variant_test_id (ab_test_id)
);

-- 焦点小组会话
CREATE TABLE focus_group_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    persona_group_id BIGINT NOT NULL,
    topic TEXT NOT NULL,
    status ENUM('active', 'completed') NOT NULL,
    summary JSON,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_focus_group_tenant_id (tenant_id)
);

-- 焦点小组对话记录
CREATE TABLE focus_group_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    sender_type ENUM('user', 'persona', 'system') NOT NULL,
    persona_id BIGINT,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_focus_group_message_session_id (session_id)
);

-- 内容创作会话
CREATE TABLE workshop_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    brief JSON NOT NULL,
    status ENUM('planning', 'drafting', 'reviewing', 'optimizing', 'completed') NOT NULL,
    current_step INT DEFAULT 1,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_workshop_session_tenant_id (tenant_id)
);

-- 内容创作消息
CREATE TABLE workshop_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    agent_role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    step INT NOT NULL,
    created_at DATETIME NOT NULL,
    INDEX idx_workshop_message_session_id (session_id)
);

-- 知识图谱快照
CREATE TABLE knowledge_graph (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    neo4j_graph_id VARCHAR(100) NOT NULL,
    node_count INT DEFAULT 0,
    edge_count INT DEFAULT 0,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_knowledge_graph_tenant_id (tenant_id)
);

-- 舆情分析记录
CREATE TABLE sentiment_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    event_description TEXT NOT NULL,
    mode ENUM('proactive', 'reactive') NOT NULL,
    risk_level DECIMAL(3,2),
    simulation_results JSON,
    response_plans JSON,
    recommended_plan INT,
    created_at DATETIME NOT NULL,
    INDEX idx_sentiment_analysis_tenant_id (tenant_id)
);

-- 策略分析记录
CREATE TABLE strategy_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    question TEXT NOT NULL,
    model_analyses JSON NOT NULL,
    debates JSON,
    synthesis JSON,
    created_at DATETIME NOT NULL,
    INDEX idx_strategy_analysis_tenant_id (tenant_id)
);

-- 异步任务
CREATE TABLE async_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    ref_id BIGINT,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL,
    progress INT DEFAULT 0,
    result JSON,
    error TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    INDEX idx_async_task_tenant_id (tenant_id),
    INDEX idx_async_task_status (status)
);
```

## 十二、API 设计

### 12.1 画像管理

```
POST   /api/personas/generate              # 从描述生成画像组
POST   /api/personas/import                 # 从 CRM/CSV 导入
GET    /api/personas/groups                 # 画像组列表
GET    /api/personas/groups/{id}            # 画像组详情
GET    /api/personas/groups/{id}/personas   # 画像列表
GET    /api/personas/{id}                   # 单个画像详情
PUT    /api/personas/{id}                   # 编辑画像
DELETE /api/personas/{id}                   # 删除画像
```

### 12.2 焦点小组

```
POST   /api/focus-groups                    # 创建焦点小组会话
POST   /api/focus-groups/{id}/ask           # 向焦点小组提问
GET    /api/focus-groups/{id}/messages      # 获取对话记录
POST   /api/focus-groups/{id}/summarize     # 生成焦点小组总结
```

### 12.3 内容工坊

```
POST   /api/workshops                       # 创建创作会话
POST   /api/workshops/{id}/brief            # 提交创意 brief
GET    /api/workshops/{id}/progress         # 获取创作进度
GET    /api/workshops/{id}/drafts           # 获取草稿列表
POST   /api/workshops/{id}/feedback         # 提交用户反馈
GET    /api/workshops/{id}/final            # 获取最终版本
```

### 12.4 沙盘推演

```
POST   /api/simulations                     # 创建模拟
POST   /api/simulations/{id}/start          # 启动模拟
GET    /api/simulations/{id}/status         # 模拟状态
GET    /api/simulations/{id}/report         # 模拟报告
POST   /api/simulations/ab-test             # 创建 A/B 测试
GET    /api/simulations/ab-test/{id}        # A/B 测试结果
```

### 12.5 市场智脑

```
POST   /api/market/graphs                   # 创建知识图谱
POST   /api/market/graphs/{id}/documents    # 添加文档到图谱
GET    /api/market/graphs/{id}/data         # 获取图谱数据
POST   /api/market/graphs/{id}/query        # 图谱查询
POST   /api/market/insights                 # 生成市场洞察
```

### 12.6 舆情哨兵

```
POST   /api/sentiment/analyze               # 舆情分析（事前/事后）
GET    /api/sentiment/{id}/report           # 分析报告
GET    /api/sentiment/{id}/plans            # 应对方案列表
POST   /api/sentiment/{id}/validate-plan    # 验证某方案效果
```

### 12.7 策略参谋

```
POST   /api/strategy/analyze                # 发起策略分析
GET    /api/strategy/{id}/progress          # 分析进度
GET    /api/strategy/{id}/report            # 分析报告
```

### 12.8 通用

```
GET    /api/tasks/{id}                      # 查询异步任务状态
GET    /api/dashboard                       # 企业仪表盘数据
```

### 12.9 WebSocket

```
WS /ws/simulation/{session_id}
  # 服务端推送
  { "type": "round_progress", "round": 5, "total": 20 }
  { "type": "agent_action", "persona": "张小花", "action": "评论", "content": "..." }
  { "type": "metrics_update", "reach_rate": 0.45, "engagement": 0.12 }
  { "type": "simulation_complete", "report_id": 42 }

WS /ws/workshop/{session_id}
  # 服务端推送
  { "type": "agent_message", "role": "strategist", "content": "..." }
  { "type": "agent_message", "role": "copywriter", "content": "..." }
  { "type": "agent_message", "role": "consumer", "content": "..." }
  { "type": "step_complete", "step": 2, "next_step": 3 }

WS /ws/focus-group/{session_id}
  # 客户端发送
  { "type": "question", "content": "你觉得这个产品定价贵吗？" }
  # 服务端推送
  { "type": "persona_response", "persona_id": 1, "name": "张小花", "content": "..." }
  { "type": "persona_response", "persona_id": 2, "name": "李明", "content": "..." }
  { "type": "all_responses_complete" }

WS /ws/strategy/{session_id}
  # 服务端推送
  { "type": "model_analysis", "model": "first_principles", "content": "..." }
  { "type": "debate_start", "model_a": "game_theory", "model_b": "systems_thinking" }
  { "type": "debate_message", "model": "game_theory", "content": "..." }
  { "type": "synthesis_complete", "report_id": 15 }
```

## 十三、前端设计

### 13.1 页面结构

```
/                           # 首页仪表盘
/personas                   # 画像工厂
  /personas/create          # 创建画像组
  /personas/:groupId        # 画像组详情
  /personas/:id/chat        # 单画像对话
/focus-groups               # 焦点小组
  /focus-groups/:id         # 焦点小组会话
/workshop                   # 内容工坊
  /workshop/create          # 创建创作任务
  /workshop/:id             # 创作过程（实时展示 Agent 协作）
/simulation                 # 沙盘推演
  /simulation/create        # 创建模拟
  /simulation/:id           # 模拟运行（实时可视化）
  /simulation/:id/report    # 模拟报告
  /simulation/ab-test/:id   # A/B 测试结果对比
/market                     # 市场智脑
  /market/graphs            # 知识图谱列表
  /market/graphs/:id        # 图谱可视化
  /market/insights          # 市场洞察
/sentiment                  # 舆情哨兵
  /sentiment/analyze        # 新建分析
  /sentiment/:id            # 分析结果
/strategy                   # 策略参谋
  /strategy/analyze         # 新建分析
  /strategy/:id             # 分析过程（实时展示多模型碰撞）
/settings                   # 企业设置
```

### 13.2 核心交互设计

#### 沙盘推演页面

```
+------------------------------------------------------------------+
|  沙盘推演 - 小红书种草文案测试                          轮次 8/20 |
+------------------------------------------------------------------+
|                          |                                        |
|  [实时传播网络图]         |  实时动态                              |
|                          |                                        |
|  节点 = 虚拟用户          |  [张小花] 点赞了内容                   |
|  颜色 = 情感倾向          |  [李明] 评论："这个成分表不错，但价格.." |
|  连线 = 传播路径          |  [王大锤] 转发到朋友圈               |
|  大小 = 影响力            |  [赵六] 忽略了内容                    |
|                          |  [孙七] 收藏了内容                    |
|                          |  ...                                  |
+--------------------------+                                        |
|  实时指标                 |                                        |
|  触达率: 45% ████░░░░    |                                        |
|  互动率: 12% ██░░░░░░    |                                        |
|  情感值: 7.2 ████████░   |                                        |
|  购买意愿: 35% ███░░░░   |                                        |
+--------------------------+----------------------------------------+
```

#### 焦点小组页面

```
+------------------------------------------------------------------+
|  虚拟焦点小组 - "新品定价测试"                           8位参与者 |
+------------------------------------------------------------------+
|                                                                    |
|  [你] 你觉得这款产品定价 299 元合理吗？                            |
|                                                                    |
|  [张小花] 25岁 白领 价格敏感型                                     |
|  "299 有点贵了，同类产品 XX 才 199，除非有明显差异化..."            |
|                                                                    |
|  [李明] 32岁 程序员 品质导向型                                     |
|  "如果成分确实好的话可以接受，关键是要有权威背书..."                 |
|                                                                    |
|  [王芳] 28岁 宝妈 实用主义型                                       |
|  "一支用两个月的话其实还行，但需要看效果再回购..."                   |
|                                                                    |
|  ... (更多回答)                                                    |
|                                                                    |
|  [系统总结]                                                        |
|  共识：75% 认为价格偏高，但品质导向型群体可接受                    |
|  关键因素：成分背书 > 使用周期 > 竞品对比                          |
|  建议：强调用量持久 + 增加权威成分说明                              |
|                                                                    |
|  [输入框] 继续追问...                                  [发送]      |
+------------------------------------------------------------------+
```

## 十四、成本与性能

### 14.1 LLM 调用估算

| 功能 | 单次调用数 | token/次 | 场景 |
|------|----------|---------|------|
| 画像生成（10人） | 12 | ~800 | 1次规划 + 10次生成 + 1次关系构建 |
| 焦点小组（1问） | 11 | ~600 | 10个Agent回答 + 1次汇总 |
| 沙盘推演（20轮x50人） | ~200 | ~500 | 每轮活跃Agent决策 |
| 内容创作（1套） | ~15 | ~1000 | 策划x3 + 文案x3 + 消费者x6 + 优化x3 |
| 舆情分析 | ~80 | ~600 | 评估 + 模拟 + 3方案生成 + 3方案验证 |
| 策略分析 | ~30 | ~800 | 5模型分析 + 交叉质疑 + 综合 |

按 qwen-plus 定价估算：
- 画像生成：~0.3 元/组
- 焦点小组：~0.2 元/问
- 沙盘推演：~2.0 元/次
- 内容创作：~0.5 元/套
- 舆情分析：~1.5 元/次
- 策略分析：~0.8 元/次

### 14.2 性能优化

| 策略 | 说明 |
|------|------|
| 流式输出 | Agent 回复流式推送，用户不等完整生成 |
| 并行决策 | 同一轮次内无依赖的 Agent 并行调用 LLM |
| 缓存画像 | 画像生成后缓存，跨模块复用 |
| 轻量判断 | 简单决策（忽略/点赞）用规则引擎，复杂决策才用 LLM |
| 分级模型 | 简单任务用轻量模型，关键决策用强模型 |
| 会话压缩 | 超过上下文窗口自动压缩历史 |

## 十五、商业模式

### 15.1 定价层级

| 层级 | 月费 | 包含 | 目标客户 |
|------|------|------|---------|
| 体验版 | 免费 | 3次模拟/月 + 1个画像组 | 试用 |
| 基础版 | 299元 | 50次模拟 + 5个画像组 + 内容工坊 | 个体户/小团队 |
| 专业版 | 1999元 | 不限模拟 + 不限画像 + 全模块 | 中小企业/MCN |
| 企业版 | 按需 | 私有化部署 + 定制行业模型 + API | 品牌方/营销公司 |

### 15.2 增值服务

| 服务 | 说明 |
|------|------|
| 行业画像包 | 预置的行业典型用户画像库（母婴/美妆/3C/食品等） |
| 竞品情报订阅 | 持续追踪竞品动态，定期推送洞察 |
| 定制模拟模型 | 为特定行业定制传播模型和用户行为模型 |
| 培训服务 | 教企业团队如何使用平台做营销决策 |

## 十六、项目里程碑

| 阶段 | 目标 | 核心模块 |
|------|------|---------|
| **P0** | 最小可行产品 | 画像工厂（画像生成 + 焦点小组）+ 沙盘推演（单内容模拟 + 报告） |
| **P1** | 内容闭环 | + 内容工坊 + A/B 测试 + 画像→模拟数据自动流转 |
| **P2** | 洞察闭环 | + 市场智脑（知识图谱 + 竞品分析）+ 洞察驱动创作 |
| **P3** | 风控闭环 | + 舆情哨兵 + 触发器系统 |
| **P4** | 决策闭环 | + 策略参谋 + 完整工作流编排 |
| **P5** | 企业级 | 多租户 + 权限管理 + API 开放 + 私有化部署 |
