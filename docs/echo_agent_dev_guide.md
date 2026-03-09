# EchoAgent - 开发实施文档

## 一、项目目录结构

```
echo-agent/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                         # FastAPI 入口
│   │   ├── config.py                       # 配置管理
│   │   ├── dependencies.py                 # 依赖注入
│   │   │
│   │   ├── api/                            # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── router.py                   # 路由注册
│   │   │   ├── persona.py                  # 画像管理
│   │   │   ├── focus_group.py              # 焦点小组
│   │   │   ├── workshop.py                 # 内容工坊
│   │   │   ├── simulation.py               # 沙盘推演
│   │   │   ├── market.py                   # 市场智脑
│   │   │   ├── sentiment.py                # 舆情哨兵
│   │   │   ├── strategy.py                 # 策略参谋
│   │   │   ├── task.py                     # 异步任务
│   │   │   └── ws.py                       # WebSocket 端点
│   │   │
│   │   ├── models/                         # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── persona.py                  # 画像相关
│   │   │   ├── simulation.py               # 模拟相关
│   │   │   ├── workshop.py                 # 创作相关
│   │   │   ├── market.py                   # 市场相关
│   │   │   ├── sentiment.py                # 舆情相关
│   │   │   ├── strategy.py                 # 策略相关
│   │   │   └── common.py                   # 通用响应
│   │   │
│   │   ├── services/                       # 核心业务逻辑
│   │   │   ├── __init__.py
│   │   │   ├── persona_service.py          # 画像生成与管理
│   │   │   ├── focus_group_service.py      # 焦点小组
│   │   │   ├── simulation_engine.py        # 模拟引擎
│   │   │   ├── simulation_analyzer.py      # 模拟结果分析
│   │   │   ├── workshop_service.py         # 内容创作编排
│   │   │   ├── market_service.py           # 市场图谱与洞察
│   │   │   ├── sentiment_service.py        # 舆情分析
│   │   │   ├── strategy_service.py         # 策略分析
│   │   │   ├── workflow_engine.py          # 工作流编排
│   │   │   └── task_service.py             # 异步任务管理
│   │   │
│   │   ├── agents/                         # Agent 实现
│   │   │   ├── __init__.py
│   │   │   ├── base.py                     # Agent 基座
│   │   │   ├── persona_agent.py            # 虚拟用户 Agent
│   │   │   ├── strategist_agent.py         # 策划 Agent
│   │   │   ├── copywriter_agent.py         # 文案 Agent
│   │   │   ├── brand_guardian_agent.py     # 品牌守护 Agent
│   │   │   ├── thinking_model_agent.py     # 思维模型 Agent
│   │   │   └── prompts/                    # Prompt 模板
│   │   │       ├── __init__.py
│   │   │       ├── persona_prompts.py
│   │   │       ├── simulation_prompts.py
│   │   │       ├── workshop_prompts.py
│   │   │       ├── market_prompts.py
│   │   │       ├── sentiment_prompts.py
│   │   │       └── strategy_prompts.py
│   │   │
│   │   ├── platforms/                      # 平台模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py                     # 平台基类
│   │   │   ├── xiaohongshu.py
│   │   │   ├── douyin.py
│   │   │   ├── wechat.py
│   │   │   └── weibo.py
│   │   │
│   │   ├── llm/                            # LLM 封装
│   │   │   ├── __init__.py
│   │   │   └── client.py                   # LLM 客户端
│   │   │
│   │   ├── db/                             # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── mysql.py                    # MySQL 连接
│   │   │   ├── neo4j.py                    # Neo4j 连接
│   │   │   └── redis.py                    # Redis 连接
│   │   │
│   │   ├── ws/                             # WebSocket
│   │   │   ├── __init__.py
│   │   │   └── manager.py                  # 连接管理
│   │   │
│   │   └── utils/                          # 工具函数
│   │       ├── __init__.py
│   │       ├── file_parser.py              # 文件解析
│   │       ├── text_processor.py           # 文本处理
│   │       └── logger.py                   # 日志
│   │
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── api/                            # API 封装
│   │   │   ├── index.ts                    # Axios 实例
│   │   │   ├── persona.ts
│   │   │   ├── focus_group.ts
│   │   │   ├── workshop.ts
│   │   │   ├── simulation.ts
│   │   │   ├── market.ts
│   │   │   ├── sentiment.ts
│   │   │   └── strategy.ts
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/                         # Pinia 状态
│   │   │   ├── user.ts
│   │   │   └── app.ts
│   │   ├── composables/                    # 组合式函数
│   │   │   ├── useWebSocket.ts
│   │   │   └── usePolling.ts
│   │   ├── views/
│   │   │   ├── Dashboard.vue
│   │   │   ├── persona/
│   │   │   │   ├── PersonaList.vue
│   │   │   │   ├── PersonaCreate.vue
│   │   │   │   ├── PersonaGroupDetail.vue
│   │   │   │   └── PersonaChat.vue
│   │   │   ├── focus_group/
│   │   │   │   ├── FocusGroupList.vue
│   │   │   │   └── FocusGroupSession.vue
│   │   │   ├── workshop/
│   │   │   │   ├── WorkshopCreate.vue
│   │   │   │   └── WorkshopSession.vue
│   │   │   ├── simulation/
│   │   │   │   ├── SimulationCreate.vue
│   │   │   │   ├── SimulationRun.vue
│   │   │   │   ├── SimulationReport.vue
│   │   │   │   └── ABTestResult.vue
│   │   │   ├── market/
│   │   │   │   ├── MarketGraph.vue
│   │   │   │   └── MarketInsights.vue
│   │   │   ├── sentiment/
│   │   │   │   ├── SentimentAnalyze.vue
│   │   │   │   └── SentimentReport.vue
│   │   │   └── strategy/
│   │   │       ├── StrategyAnalyze.vue
│   │   │       └── StrategyReport.vue
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── AppHeader.vue
│   │   │   │   ├── AppSidebar.vue
│   │   │   │   └── LoadingSpinner.vue
│   │   │   ├── persona/
│   │   │   │   ├── PersonaCard.vue
│   │   │   │   └── PersonaRadar.vue
│   │   │   ├── simulation/
│   │   │   │   ├── NetworkGraph.vue
│   │   │   │   ├── MetricsPanel.vue
│   │   │   │   └── ActionFeed.vue
│   │   │   ├── workshop/
│   │   │   │   ├── AgentChatBubble.vue
│   │   │   │   └── ContentPreview.vue
│   │   │   └── chart/
│   │   │       ├── RadarChart.vue
│   │   │       ├── LineChart.vue
│   │   │       └── BarChart.vue
│   │   └── types/
│   │       ├── persona.ts
│   │       ├── simulation.ts
│   │       ├── workshop.ts
│   │       └── common.ts
│   │
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
├── .env.example
└── README.md
```

## 二、环境配置

### 2.1 环境变量（.env）

```env
# LLM 配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL_NAME=qwen-plus
# 轻量模型（简单判断用，降低成本）
LLM_LIGHT_MODEL_NAME=qwen-turbo

# MySQL
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=echo_agent
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=echo_agent

# Neo4j
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# 应用
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your_secret_key
```

### 2.2 后端依赖（pyproject.toml）

```toml
[project]
name = "echo-agent"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.34.0",
    "openai>=1.0.0",
    "sqlalchemy>=2.0.0",
    "aiomysql>=0.2.0",
    "neo4j>=5.0.0",
    "redis>=5.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "python-multipart>=0.0.9",
    "websockets>=13.0",
    "httpx>=0.27.0",
    "PyMuPDF>=1.24.0",
    "chardet>=5.0.0",
    "networkx>=3.0",
    "python-jose>=3.3.0",
    "passlib>=1.7.0",
    "bcrypt>=4.0.0",
]
```

### 2.3 前端依赖（package.json）

```json
{
  "name": "echo-agent-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.5.0",
    "vue-router": "^4.5.0",
    "pinia": "^3.0.0",
    "axios": "^1.7.0",
    "d3": "^7.9.0",
    "echarts": "^5.6.0",
    "dayjs": "^1.11.0",
    "@vueuse/core": "^12.0.0"
  },
  "devDependencies": {
    "vite": "^6.0.0",
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.7.0",
    "vue-tsc": "^2.0.0",
    "@tailwindcss/vite": "^4.0.0",
    "tailwindcss": "^4.0.0"
  }
}
```

## 三、数据库

### 3.1 MySQL 建表语句

```sql
CREATE DATABASE IF NOT EXISTS echo_agent
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE echo_agent;

-- 企业/租户
CREATE TABLE tenant (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    plan VARCHAR(50) NOT NULL DEFAULT 'basic',
    config JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 用户
CREATE TABLE user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_username (username),
    INDEX idx_user_tenant_id (tenant_id)
);

-- 画像组
CREATE TABLE persona_group (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    source VARCHAR(50) NOT NULL DEFAULT 'description',
    source_input TEXT,
    persona_count INT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_persona_group_tenant_id (tenant_id)
);

-- 画像
CREATE TABLE persona (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    age INT,
    gender VARCHAR(10),
    city VARCHAR(100),
    occupation VARCHAR(200),
    monthly_income INT,
    personality JSON NOT NULL,
    consumer_profile JSON NOT NULL,
    media_behavior JSON NOT NULL,
    social_behavior JSON NOT NULL,
    agent_config JSON NOT NULL,
    full_persona TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_persona_tenant_id (tenant_id),
    INDEX idx_persona_group_id (group_id)
);

-- 营销内容
CREATE TABLE content (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    title VARCHAR(500),
    body TEXT NOT NULL,
    content_type VARCHAR(50) NOT NULL,
    platform VARCHAR(50),
    tags JSON,
    version INT DEFAULT 1,
    parent_id BIGINT,
    workshop_session_id BIGINT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_content_tenant_id (tenant_id)
);

-- 模拟会话
CREATE TABLE simulation_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    content_id BIGINT NOT NULL,
    persona_group_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    config JSON NOT NULL,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    total_rounds INT NOT NULL DEFAULT 20,
    current_round INT DEFAULT 0,
    ab_test_id BIGINT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_sim_session_tenant_id (tenant_id),
    INDEX idx_sim_session_content_id (content_id)
);

-- 模拟动作
CREATE TABLE simulation_action (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    round_num INT NOT NULL,
    persona_id BIGINT NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    action_detail JSON NOT NULL,
    comment_text TEXT,
    sentiment_score DECIMAL(4,2),
    purchase_intent DECIMAL(4,2),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sim_action_session_id (session_id),
    INDEX idx_sim_action_round (session_id, round_num)
);

-- 模拟报告
CREATE TABLE simulation_report (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL UNIQUE,
    metrics JSON NOT NULL,
    segment_analysis JSON NOT NULL,
    propagation JSON NOT NULL,
    comment_themes JSON,
    risks JSON,
    suggestions JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- A/B 测试
CREATE TABLE ab_test (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    persona_group_id BIGINT NOT NULL,
    platform VARCHAR(50) NOT NULL,
    status ENUM('pending', 'running', 'completed') NOT NULL DEFAULT 'pending',
    winner_variant_id BIGINT,
    result_summary JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
    INDEX idx_ab_variant_test_id (ab_test_id)
);

-- 焦点小组会话
CREATE TABLE focus_group_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    persona_group_id BIGINT NOT NULL,
    topic VARCHAR(500) NOT NULL,
    status ENUM('active', 'completed') NOT NULL DEFAULT 'active',
    summary JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_fg_session_tenant_id (tenant_id)
);

-- 焦点小组消息
CREATE TABLE focus_group_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    sender_type ENUM('user', 'persona', 'system') NOT NULL,
    persona_id BIGINT,
    content TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_fg_message_session_id (session_id)
);

-- 内容工坊会话
CREATE TABLE workshop_session (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    brief JSON NOT NULL,
    persona_group_id BIGINT,
    status ENUM('planning', 'drafting', 'reviewing', 'optimizing', 'completed') NOT NULL DEFAULT 'planning',
    current_step INT DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_ws_session_tenant_id (tenant_id)
);

-- 内容工坊消息
CREATE TABLE workshop_message (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id BIGINT NOT NULL,
    agent_role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    step INT NOT NULL,
    message_type ENUM('thinking', 'draft', 'feedback', 'revision', 'final') NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ws_message_session_id (session_id)
);

-- 知识图谱
CREATE TABLE knowledge_graph (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    neo4j_graph_id VARCHAR(100) NOT NULL,
    node_count INT DEFAULT 0,
    edge_count INT DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_kg_tenant_id (tenant_id)
);

-- 舆情分析
CREATE TABLE sentiment_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    event_description TEXT NOT NULL,
    mode ENUM('proactive', 'reactive') NOT NULL,
    risk_level DECIMAL(4,2),
    spread_simulation_id BIGINT,
    response_plans JSON,
    plan_simulations JSON,
    recommended_plan INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_sa_tenant_id (tenant_id)
);

-- 策略分析
CREATE TABLE strategy_analysis (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    question TEXT NOT NULL,
    models_used JSON NOT NULL,
    model_analyses JSON,
    cross_debates JSON,
    synthesis JSON,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_strat_tenant_id (tenant_id)
);

-- 异步任务
CREATE TABLE async_task (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    tenant_id BIGINT NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    ref_type VARCHAR(50),
    ref_id BIGINT,
    status ENUM('pending', 'running', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    progress INT DEFAULT 0,
    message VARCHAR(500),
    result JSON,
    error TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_task_tenant_id (tenant_id),
    INDEX idx_task_status (status)
);
```

### 3.2 Neo4j 图模型

```cypher
// 市场实体节点
CREATE (n:MarketEntity {
    id: $id,
    tenant_id: $tenant_id,
    graph_id: $graph_id,
    name: $name,
    entity_type: $entity_type,
    properties: $properties,
    created_at: datetime()
})

// 市场关系边
CREATE (a)-[r:MARKET_RELATION {
    relation_type: $relation_type,
    strength: $strength,
    description: $description,
    valid_from: $valid_from,
    valid_to: $valid_to
}]->(b)

// 画像社交网络节点
CREATE (p:Persona {
    id: $persona_id,
    tenant_id: $tenant_id,
    group_id: $group_id,
    name: $name,
    influence_power: $influence_power
})

// 画像间社交关系
CREATE (a)-[r:SOCIAL_LINK {
    relation_type: $relation_type,
    closeness: $closeness
}]->(b)

// 查询：获取某实体的竞争关系网
MATCH (n:MarketEntity {id: $entity_id})-[r:MARKET_RELATION]-(m:MarketEntity)
WHERE r.relation_type IN ['competes_with', 'substitutes']
RETURN n, r, m

// 查询：获取画像社交传播路径
MATCH path = (source:Persona {id: $source_id})-[:SOCIAL_LINK*1..3]->(target:Persona)
WHERE ALL(r IN relationships(path) WHERE r.closeness > 0.3)
RETURN path
```

## 四、后端核心实现

### 4.1 FastAPI 入口（app/main.py）

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import register_routes
from app.config import settings
from app.db.mysql import init_db, close_db
from app.db.neo4j import init_neo4j, close_neo4j
from app.db.redis import init_redis, close_redis


@asynccontextmanager
async def lifespan(application: FastAPI):
    await init_db()
    await init_neo4j()
    await init_redis()
    yield
    await close_db()
    await close_neo4j()
    await close_redis()


app = FastAPI(
    title="EchoAgent API",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_routes(app)
```

### 4.2 配置管理（app/config.py）

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_MODEL_NAME: str
    LLM_LIGHT_MODEL_NAME: str

    # MySQL
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str

    # Neo4j
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str

    # Redis
    REDIS_URL: str

    # App
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"
    SECRET_KEY: str

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    class Config:
        env_file = ".env"


settings = Settings()
```

### 4.3 路由注册（app/api/router.py）

```python
from fastapi import FastAPI

from app.api import persona, focus_group, workshop, simulation, market, sentiment, strategy, task, ws


def register_routes(app: FastAPI):
    app.include_router(persona.router, prefix="/api/personas", tags=["画像管理"])
    app.include_router(focus_group.router, prefix="/api/focus-groups", tags=["焦点小组"])
    app.include_router(workshop.router, prefix="/api/workshops", tags=["内容工坊"])
    app.include_router(simulation.router, prefix="/api/simulations", tags=["沙盘推演"])
    app.include_router(market.router, prefix="/api/market", tags=["市场智脑"])
    app.include_router(sentiment.router, prefix="/api/sentiment", tags=["舆情哨兵"])
    app.include_router(strategy.router, prefix="/api/strategy", tags=["策略参谋"])
    app.include_router(task.router, prefix="/api/tasks", tags=["任务管理"])
    app.include_router(ws.router, tags=["WebSocket"])
```

### 4.4 LLM 客户端（app/llm/client.py）

```python
import json

from openai import AsyncOpenAI

from app.config import settings


class LLMClient:
    def __init__(self, model_name: str = None):
        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        self.model = model_name or settings.LLM_MODEL_NAME

    async def generate(self, messages: list[dict], temperature: float = 0.7, max_tokens: int = 4096) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def generate_json(self, messages: list[dict], temperature: float = 0.3) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def generate_stream(self, messages: list[dict], temperature: float = 0.7):
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=True
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


# 全局实例
llm = LLMClient()
llm_light = LLMClient(model_name=settings.LLM_LIGHT_MODEL_NAME)
```

### 4.5 WebSocket 管理器（app/ws/manager.py）

```python
import json
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, channel: str, websocket: WebSocket):
        await websocket.accept()
        if channel not in self.connections:
            self.connections[channel] = []
        self.connections[channel].append(websocket)

    def disconnect(self, channel: str, websocket: WebSocket):
        if channel in self.connections:
            self.connections[channel].remove(websocket)
            if not self.connections[channel]:
                del self.connections[channel]

    async def emit(self, channel: str, event_type: str, data: dict):
        message = json.dumps({"type": event_type, **data}, ensure_ascii=False)
        if channel in self.connections:
            dead = []
            for ws in self.connections[channel]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.connections[channel].remove(ws)


ws_manager = ConnectionManager()
```

### 4.6 Agent 基座（app/agents/base.py）

```python
from abc import ABC, abstractmethod

from app.llm.client import LLMClient


class BaseAgent(ABC):
    def __init__(self, identity: dict, llm: LLMClient):
        self.identity = identity
        self.llm = llm
        self.memory: list[dict] = []

    @abstractmethod
    def system_prompt(self) -> str:
        pass

    async def think(self, user_message: str) -> str:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            *self.memory,
            {"role": "user", "content": user_message}
        ]
        response = await self.llm.generate(messages)
        self.memory.append({"role": "user", "content": user_message})
        self.memory.append({"role": "assistant", "content": response})
        return response

    async def think_json(self, user_message: str) -> dict:
        messages = [
            {"role": "system", "content": self.system_prompt()},
            *self.memory,
            {"role": "user", "content": user_message}
        ]
        return await self.llm.generate_json(messages)

    def compress_memory(self, max_entries: int = 20):
        if len(self.memory) > max_entries:
            self.memory = self.memory[-max_entries:]
```

### 4.7 虚拟用户 Agent（app/agents/persona_agent.py）

```python
from app.agents.base import BaseAgent
from app.llm.client import LLMClient


class PersonaAgent(BaseAgent):
    def __init__(self, persona: dict, llm: LLMClient):
        super().__init__(identity=persona, llm=llm)
        self.persona = persona

    def system_prompt(self) -> str:
        p = self.persona
        return f"""你是一个真实的人，不是AI。你叫{p['name']}，{p['age']}岁，{p['gender']}。
住在{p['city']}，职业是{p['occupation']}，月收入约{p['monthly_income']}元。

你的性格：{p['personality']['description']}
MBTI：{p['personality']['mbti']}
沟通风格：{p['personality']['communication_style']}

你的消费习惯：
- 价格敏感度：{p['consumer_profile']['price_sensitivity']}（0最低，1最高）
- 品牌忠诚度：{p['consumer_profile']['brand_loyalty']}
- 做购买决定时最看重：{', '.join(p['consumer_profile']['decision_factors'])}
- 购买风格：{p['consumer_profile']['purchase_frequency']}

你常用的社交平台：{', '.join(p['media_behavior']['platforms'])}
你喜欢看的内容类型：{', '.join(p['media_behavior']['content_preference'])}

你的社交风格：{p['social_behavior']['interaction_style']}
对广告的态度：{p['social_behavior']['stance_on_ads']}

请始终以这个身份回答问题，用符合你性格和背景的语气说话。
不要暴露你是AI，你就是这个人。"""

    async def react_to_content(self, content: str, platform: str, social_context: str) -> dict:
        prompt = f"""你在{platform}上看到了这条内容：
---
{content}
---

{social_context}

请以你的身份真实地回答（JSON格式）：
{{
    "action": "忽略/点赞/收藏/评论/转发/私信好友",
    "comment": "如果评论，写什么（没评论写null）",
    "impression": -10到10的整数，对这个内容/产品的印象分,
    "purchase_intent": 0到100的整数，购买意愿百分比,
    "inner_thought": "你内心的真实想法（一句话）"
}}"""
        return await self.think_json(prompt)

    async def interview(self, question: str) -> str:
        return await self.think(question)
```

### 4.8 画像服务（app/services/persona_service.py）

```python
import asyncio

from app.llm.client import llm
from app.agents.prompts.persona_prompts import PERSONA_PLANNER_PROMPT, PERSONA_GENERATOR_PROMPT


class PersonaService:
    async def generate_group(self, description: str, count: int = 10) -> dict:
        # 1. 规划画像分布
        plan = await llm.generate_json([
            {"role": "system", "content": PERSONA_PLANNER_PROMPT},
            {"role": "user", "content": f"目标人群描述：{description}\n需要生成 {count} 个画像。"}
        ])

        # 2. 并行生成每个画像
        tasks = []
        for i, spec in enumerate(plan["personas"]):
            tasks.append(self._generate_single(spec, i + 1))

        personas = await asyncio.gather(*tasks)

        # 3. 构建社交关系网络
        network = await self._build_social_network(personas)

        return {"personas": personas, "network": network}

    async def _generate_single(self, spec: dict, index: int) -> dict:
        result = await llm.generate_json([
            {"role": "system", "content": PERSONA_GENERATOR_PROMPT},
            {"role": "user", "content": f"画像规格：{spec}"}
        ])
        return result

    async def _build_social_network(self, personas: list[dict]) -> list[dict]:
        # 基于画像特征自动建立社交关系
        edges = []
        for i, p1 in enumerate(personas):
            for j, p2 in enumerate(personas):
                if i >= j:
                    continue
                closeness = self._calc_closeness(p1, p2)
                if closeness > 0.3:
                    edges.append({
                        "from": p1["name"],
                        "to": p2["name"],
                        "closeness": closeness,
                        "relation_type": self._infer_relation(p1, p2)
                    })
        return edges

    def _calc_closeness(self, p1: dict, p2: dict) -> float:
        score = 0.0
        if p1.get("city") == p2.get("city"):
            score += 0.2
        if p1.get("occupation") == p2.get("occupation"):
            score += 0.2
        age_diff = abs(p1.get("age", 0) - p2.get("age", 0))
        if age_diff <= 5:
            score += 0.2
        # 兴趣重叠
        interests1 = set(p1.get("media_behavior", {}).get("content_preference", []))
        interests2 = set(p2.get("media_behavior", {}).get("content_preference", []))
        if interests1 & interests2:
            score += 0.2 * len(interests1 & interests2) / max(len(interests1 | interests2), 1)
        return min(score, 1.0)

    def _infer_relation(self, p1: dict, p2: dict) -> str:
        if p1.get("occupation") == p2.get("occupation"):
            return "colleague"
        if p1.get("city") == p2.get("city"):
            return "acquaintance"
        return "online_friend"
```

### 4.9 模拟引擎（app/services/simulation_engine.py）

```python
import asyncio
import random

from app.agents.persona_agent import PersonaAgent
from app.llm.client import llm, llm_light
from app.ws.manager import ws_manager


class SimulationEngine:
    def __init__(self, session_id: int, content: dict, personas: list[dict],
                 platform: dict, config: dict):
        self.session_id = session_id
        self.content = content
        self.platform = platform
        self.config = config
        self.ws_channel = f"simulation:{session_id}"

        # 初始化 Agent 实例
        self.agents = {
            p["id"]: PersonaAgent(p, llm_light)
            for p in personas
        }

        # 状态
        self.exposed: set[int] = set()
        self.actions: list[dict] = []
        self.metrics_history: list[dict] = []

    async def run(self):
        # 初始曝光
        initial_count = int(len(self.agents) * self.config.get("initial_exposure_rate", 0.3))
        self.exposed = set(random.sample(list(self.agents.keys()), initial_count))

        for round_num in range(1, self.config["max_rounds"] + 1):
            round_actions = await self._run_round(round_num)
            self.actions.extend(round_actions)

            # 计算并推送指标
            metrics = self._calc_metrics(round_num)
            self.metrics_history.append(metrics)
            await ws_manager.emit(self.ws_channel, "metrics_update", metrics)
            await ws_manager.emit(self.ws_channel, "round_progress", {
                "round": round_num, "total": self.config["max_rounds"]
            })

            # 稳态检测
            if self._is_stable():
                break

        await ws_manager.emit(self.ws_channel, "simulation_complete", {
            "total_rounds": len(self.metrics_history)
        })
        return self.actions, self.metrics_history

    async def _run_round(self, round_num: int) -> list[dict]:
        # 确定本轮活跃 Agent
        active_ids = [
            pid for pid in self.exposed
            if random.random() < self.agents[pid].persona.get("agent_config", {}).get("activity_level", 0.5)
        ]

        # 并行执行 Agent 决策
        tasks = []
        for pid in active_ids:
            social_ctx = self._get_social_context(pid)
            tasks.append(self._agent_act(pid, social_ctx, round_num))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        round_actions = [r for r in results if isinstance(r, dict)]

        # 传播：转发/评论的 Agent 影响其社交圈
        for action in round_actions:
            if action["action_type"] in ("转发", "评论", "私信好友"):
                new_exposed = self._propagate(action["persona_id"])
                self.exposed.update(new_exposed)

        return round_actions

    async def _agent_act(self, persona_id: int, social_context: str, round_num: int) -> dict:
        agent = self.agents[persona_id]
        result = await agent.react_to_content(
            content=self.content["body"],
            platform=self.platform["name"],
            social_context=social_context
        )
        action = {
            "session_id": self.session_id,
            "round_num": round_num,
            "persona_id": persona_id,
            "persona_name": agent.persona["name"],
            "action_type": result["action"],
            "action_detail": result,
            "comment_text": result.get("comment"),
            "sentiment_score": result.get("impression", 0) / 10.0,
            "purchase_intent": result.get("purchase_intent", 0) / 100.0
        }
        await ws_manager.emit(self.ws_channel, "agent_action", {
            "persona": agent.persona["name"],
            "action": result["action"],
            "content": result.get("comment") or result.get("inner_thought", "")
        })
        return action

    def _get_social_context(self, persona_id: int) -> str:
        recent = [a for a in self.actions[-20:] if a["persona_id"] != persona_id]
        if not recent:
            return "你是第一批看到这条内容的人。"
        lines = []
        for a in recent[-5:]:
            if a["action_type"] == "评论":
                lines.append(f"{a['persona_name']}评论了：\"{a['comment_text']}\"")
            elif a["action_type"] != "忽略":
                lines.append(f"{a['persona_name']}{a['action_type']}了这条内容")
        return "你看到朋友圈/信息流中的互动：\n" + "\n".join(lines)

    def _propagate(self, persona_id: int) -> set[int]:
        # 基于社交网络传播到未曝光的邻居
        # 简化版：随机选取 1-3 个未曝光的 Agent
        unexposed = set(self.agents.keys()) - self.exposed
        count = min(random.randint(1, 3), len(unexposed))
        return set(random.sample(list(unexposed), count)) if unexposed else set()

    def _calc_metrics(self, round_num: int) -> dict:
        total = len(self.agents)
        exposed_count = len(self.exposed)
        interacted = [a for a in self.actions if a["action_type"] != "忽略"]
        sentiments = [a["sentiment_score"] for a in self.actions if a.get("sentiment_score") is not None]
        intents = [a["purchase_intent"] for a in self.actions if a.get("purchase_intent") is not None]
        return {
            "round": round_num,
            "reach_rate": exposed_count / total,
            "engagement_rate": len(interacted) / max(exposed_count, 1),
            "avg_sentiment": sum(sentiments) / max(len(sentiments), 1),
            "avg_purchase_intent": sum(intents) / max(len(intents), 1),
            "action_counts": self._count_actions()
        }

    def _count_actions(self) -> dict:
        counts = {}
        for a in self.actions:
            t = a["action_type"]
            counts[t] = counts.get(t, 0) + 1
        return counts

    def _is_stable(self) -> bool:
        if len(self.metrics_history) < 3:
            return False
        recent = self.metrics_history[-3:]
        reach_change = abs(recent[-1]["reach_rate"] - recent[-3]["reach_rate"])
        return reach_change < 0.01
```

### 4.10 焦点小组服务（app/services/focus_group_service.py）

```python
import asyncio

from app.agents.persona_agent import PersonaAgent
from app.llm.client import llm, llm_light
from app.ws.manager import ws_manager


class FocusGroupService:
    async def ask(self, session_id: int, personas: list[dict], question: str) -> list[dict]:
        ws_channel = f"focus-group:{session_id}"
        agents = [PersonaAgent(p, llm_light) for p in personas]

        # 并行让每个 Agent 回答
        tasks = [agent.interview(question) for agent in agents]
        responses = await asyncio.gather(*tasks)

        results = []
        for agent, response in zip(agents, responses):
            result = {
                "persona_id": agent.persona["id"],
                "persona_name": agent.persona["name"],
                "persona_brief": f"{agent.persona['age']}岁 {agent.persona['occupation']}",
                "response": response
            }
            results.append(result)
            await ws_manager.emit(ws_channel, "persona_response", result)

        await ws_manager.emit(ws_channel, "all_responses_complete", {})

        # 生成汇总
        summary = await self._summarize(question, results)
        return {"responses": results, "summary": summary}

    async def _summarize(self, question: str, results: list[dict]) -> dict:
        responses_text = "\n\n".join([
            f"[{r['persona_name']}]（{r['persona_brief']}）：{r['response']}"
            for r in results
        ])
        prompt = f"""以下是一个虚拟焦点小组对问题的回答：

问题：{question}

回答：
{responses_text}

请分析这些回答，输出JSON：
{{
    "consensus": ["所有人都同意的观点"],
    "divergence": ["存在分歧的观点"],
    "key_insights": ["最有价值的洞察"],
    "segment_summary": {{"群体类型": "该群体的共同看法"}},
    "recommendations": ["基于以上分析的行动建议"]
}}"""
        return await llm.generate_json([
            {"role": "system", "content": "你是一个专业的市场调研分析师。"},
            {"role": "user", "content": prompt}
        ])
```

### 4.11 内容工坊服务（app/services/workshop_service.py）

```python
from app.agents.base import BaseAgent
from app.llm.client import llm
from app.ws.manager import ws_manager
from app.agents.prompts.workshop_prompts import (
    STRATEGIST_PROMPT, COPYWRITER_PROMPT, BRAND_GUARDIAN_PROMPT
)


class StrategistAgent(BaseAgent):
    def system_prompt(self) -> str:
        return STRATEGIST_PROMPT.format(**self.identity)


class CopywriterAgent(BaseAgent):
    def system_prompt(self) -> str:
        return COPYWRITER_PROMPT.format(**self.identity)


class BrandGuardianAgent(BaseAgent):
    def system_prompt(self) -> str:
        return BRAND_GUARDIAN_PROMPT.format(**self.identity)


class WorkshopService:
    async def run_session(self, session_id: int, brief: dict, consumer_personas: list[dict]):
        ws_channel = f"workshop:{session_id}"
        strategist = StrategistAgent(brief, llm)
        copywriter = CopywriterAgent(brief, llm)
        guardian = BrandGuardianAgent(brief, llm)

        # Step 1: 策划 Agent 生成创意方向
        strategy = await strategist.think(
            f"为以下产品制定3个创意方向：\n"
            f"产品：{brief['product']}\n"
            f"目标人群：{brief['target_audience']}\n"
            f"平台：{brief['platform']}\n"
            f"品牌调性：{brief['brand_tone']}"
        )
        await ws_manager.emit(ws_channel, "agent_message", {
            "role": "strategist", "content": strategy, "step": 1
        })

        # Step 2: 文案 Agent 基于每个方向写内容
        drafts = []
        for i, direction in enumerate(self._parse_directions(strategy)):
            draft = await copywriter.think(
                f"基于以下创意方向写一篇{brief['platform']}营销文案：\n"
                f"方向：{direction}\n"
                f"品牌调性：{brief['brand_tone']}"
            )
            drafts.append(draft)
            await ws_manager.emit(ws_channel, "agent_message", {
                "role": "copywriter", "content": draft, "step": 2, "variant": i + 1
            })

        # Step 3: 消费者 Agent 评价
        from app.agents.persona_agent import PersonaAgent
        from app.llm.client import llm_light
        for draft in drafts:
            for persona_data in consumer_personas[:3]:
                consumer = PersonaAgent(persona_data, llm_light)
                feedback = await consumer.interview(
                    f"你在{brief['platform']}上看到这条内容，作为消费者你怎么看？\n\n{draft}"
                )
                await ws_manager.emit(ws_channel, "agent_message", {
                    "role": "consumer", "persona": persona_data["name"],
                    "content": feedback, "step": 3
                })

        # Step 4: 品牌守护 Agent 检查
        for draft in drafts:
            review = await guardian.think(
                f"检查以下营销内容是否符合品牌调性（{brief['brand_tone']}）：\n\n{draft}"
            )
            await ws_manager.emit(ws_channel, "agent_message", {
                "role": "brand_guardian", "content": review, "step": 4
            })

        await ws_manager.emit(ws_channel, "step_complete", {"step": 4})
        return drafts

    def _parse_directions(self, strategy: str) -> list[str]:
        lines = strategy.strip().split("\n")
        directions = [l.strip() for l in lines if l.strip() and any(l.strip().startswith(p) for p in ("1", "2", "3", "-", "*"))]
        return directions[:3] if directions else [strategy]
```

### 4.12 API 路由示例（app/api/persona.py）

```python
from fastapi import APIRouter, Depends

from app.models.persona import GeneratePersonaRequest, PersonaGroupResponse
from app.services.persona_service import PersonaService
from app.services.task_service import TaskService

router = APIRouter()


@router.post("/generate", response_model=dict)
async def generate_personas(req: GeneratePersonaRequest):
    task_svc = TaskService()
    task_id = await task_svc.create(
        tenant_id=req.tenant_id,
        task_type="persona_generate",
        ref_type="persona_group"
    )

    # 后台异步执行
    async def _run():
        svc = PersonaService()
        result = await svc.generate_group(req.description, req.count)
        # 存入数据库...
        await task_svc.complete(task_id, result)

    import asyncio
    asyncio.create_task(_run())
    return {"task_id": task_id}


@router.get("/groups")
async def list_groups(tenant_id: int):
    # 查询数据库返回画像组列表
    pass


@router.get("/groups/{group_id}")
async def get_group(group_id: int):
    # 查询画像组详情 + 画像列表
    pass


@router.get("/{persona_id}")
async def get_persona(persona_id: int):
    # 查询单个画像详情
    pass
```

### 4.13 API 路由示例（app/api/simulation.py）

```python
from fastapi import APIRouter

from app.models.simulation import CreateSimulationRequest, CreateABTestRequest
from app.services.simulation_engine import SimulationEngine
from app.services.task_service import TaskService

router = APIRouter()


@router.post("")
async def create_simulation(req: CreateSimulationRequest):
    # 创建模拟记录
    pass


@router.post("/{session_id}/start")
async def start_simulation(session_id: int):
    task_svc = TaskService()
    task_id = await task_svc.create(
        tenant_id=1,
        task_type="simulation_run",
        ref_type="simulation_session",
        ref_id=session_id
    )

    async def _run():
        # 加载内容、画像、平台配置
        # content = ...
        # personas = ...
        # platform = ...
        # config = ...
        engine = SimulationEngine(session_id, content, personas, platform, config)
        actions, metrics = await engine.run()
        # 保存结果到数据库
        await task_svc.complete(task_id, {"total_actions": len(actions)})

    import asyncio
    asyncio.create_task(_run())
    return {"task_id": task_id}


@router.get("/{session_id}/status")
async def get_status(session_id: int):
    pass


@router.get("/{session_id}/report")
async def get_report(session_id: int):
    pass


@router.post("/ab-test")
async def create_ab_test(req: CreateABTestRequest):
    # 创建多个模拟，并行运行，汇总对比
    pass


@router.get("/ab-test/{test_id}")
async def get_ab_test_result(test_id: int):
    pass
```

### 4.14 WebSocket 端点（app/api/ws.py）

```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.ws.manager import ws_manager

router = APIRouter()


@router.websocket("/ws/simulation/{session_id}")
async def simulation_ws(websocket: WebSocket, session_id: int):
    channel = f"simulation:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（暂停/恢复等）
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/focus-group/{session_id}")
async def focus_group_ws(websocket: WebSocket, session_id: int):
    channel = f"focus-group:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)


@router.websocket("/ws/workshop/{session_id}")
async def workshop_ws(websocket: WebSocket, session_id: int):
    channel = f"workshop:{session_id}"
    await ws_manager.connect(channel, websocket)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(channel, websocket)
```

## 五、Prompt 模板

### 5.1 画像规划 Prompt（app/agents/prompts/persona_prompts.py）

```python
PERSONA_PLANNER_PROMPT = """你是一个用户画像规划专家。

根据目标人群描述，规划一组差异化的用户画像。要求：
1. 覆盖不同消费类型（价格敏感/品质导向/尝鲜型/从众型等）
2. 覆盖不同年龄段、职业、收入层级
3. 每个画像要有独特性，避免雷同
4. 分布比例要合理，反映真实市场

输出JSON格式：
{
    "analysis": "对目标人群的简要分析",
    "distribution": {"类型": "占比"},
    "personas": [
        {
            "type": "消费类型标签",
            "age_range": "年龄范围",
            "gender_preference": "性别倾向或不限",
            "income_level": "收入层级",
            "key_traits": ["关键特征"],
            "role_in_group": "在消费群体中的角色（意见领袖/跟随者/旁观者）"
        }
    ]
}"""


PERSONA_GENERATOR_PROMPT = """你是一个用户画像生成专家。

根据画像规格生成一个完整、真实、有血有肉的虚拟用户画像。
这个画像要像一个真实存在的人，不是一个标签集合。

输出JSON格式：
{
    "name": "中文姓名",
    "age": 数字,
    "gender": "男/女",
    "city": "城市",
    "occupation": "职业",
    "monthly_income": 数字,
    "personality": {
        "mbti": "MBTI类型",
        "communication_style": "沟通风格",
        "description": "2-3句话的性格描述"
    },
    "consumer_profile": {
        "price_sensitivity": 0到1的小数,
        "brand_loyalty": 0到1的小数,
        "decision_factors": ["决策因素列表"],
        "purchase_frequency": "冲动型/计划型/比价型",
        "monthly_disposable": 数字
    },
    "media_behavior": {
        "platforms": ["常用平台"],
        "content_preference": ["喜欢的内容类型"],
        "influence_susceptibility": 0到1,
        "influence_power": 0到1
    },
    "social_behavior": {
        "post_frequency": "高频/低频/潜水",
        "interaction_style": "点赞派/评论派/转发派/沉默派",
        "stance_on_ads": "反感/中立/感兴趣"
    },
    "agent_config": {
        "activity_level": 0到1,
        "sentiment_bias": -1到1,
        "critical_thinking": 0到1,
        "herd_mentality": 0到1
    },
    "backstory": "2-3句话的人物背景故事"
}"""
```

### 5.2 模拟决策 Prompt（app/agents/prompts/simulation_prompts.py）

```python
CONTENT_REACTION_PROMPT = """你是 {name}，{age}岁，{occupation}，住在{city}。

性格特征：{personality_desc}
消费习惯：价格敏感度 {price_sensitivity}/10，品牌忠诚度 {brand_loyalty}/10
购买决策看重：{decision_factors}
社交风格：{interaction_style}
对广告态度：{stance_on_ads}

你在{platform}上看到了这条内容：
---
{content}
---

{social_context}

请以你的身份，真实回答（JSON格式）：
{{
    "action": "忽略/点赞/收藏/评论/转发/私信好友（选一个）",
    "comment": "如果你评论了写内容，否则null",
    "impression": -10到10的整数,
    "purchase_intent": 0到100的整数,
    "inner_thought": "一句话内心真实想法"
}}

注意：
- 保持你的身份一致性，不要跳出角色
- 大多数人看到广告的第一反应是忽略，只有真正打动你的才会互动
- 你的评论要符合你的年龄、职业和说话风格"""


SIMULATION_REPORT_PROMPT = """根据以下模拟数据生成一份营销效果预测报告：

内容：{content_summary}
平台：{platform}
模拟人数：{persona_count}
总轮次：{total_rounds}

各轮次指标：
{metrics_timeline}

行为统计：
{action_stats}

代表性评论：
{sample_comments}

请生成报告（JSON格式）：
{{
    "executive_summary": "3句话总结",
    "metrics": {{
        "reach_rate": "触达率及解读",
        "engagement_rate": "互动率及解读",
        "sentiment": "情感倾向及解读",
        "purchase_intent": "购买意愿及解读",
        "viral_potential": "传播潜力评估"
    }},
    "segment_insights": [
        {{"segment": "人群类型", "reaction": "反应描述", "key_concern": "核心关注点"}}
    ],
    "risks": ["风险点"],
    "optimization_suggestions": ["优化建议"],
    "recommended_changes": ["具体修改建议"]
}}"""
```

### 5.3 内容工坊 Prompt（app/agents/prompts/workshop_prompts.py）

```python
STRATEGIST_PROMPT = """你是一位资深营销策划专家，擅长洞察消费者需求并制定创意策略。

你的工作方式：
1. 分析产品卖点和目标人群的匹配度
2. 找到最有传播力的切入角度
3. 给出清晰的创意方向（不写具体文案）

当前品牌调性：{brand_tone}
目标平台：{platform}

输出要求：
- 给出3个差异化的创意方向
- 每个方向说明：核心卖点、情感诉求、内容角度
- 标注每个方向适合的人群类型"""


COPYWRITER_PROMPT = """你是一位{platform}平台的资深内容创作者。

你深谙{platform}的内容调性和传播规律：
- 什么样的标题能吸引点击
- 什么样的内容能引发互动
- 什么样的表达能促进转发

品牌调性：{brand_tone}

请基于给定的创意方向，写出一篇完整的{platform}营销内容。
包括：标题、正文、标签/话题、互动引导语（CTA）。

注意：
- 符合{platform}的内容风格
- 不要硬广感
- 要有真实感和共鸣点"""


BRAND_GUARDIAN_PROMPT = """你是品牌经理，负责确保所有营销内容符合品牌标准。

品牌调性：{brand_tone}

你需要从以下维度检查内容：
1. 品牌调性一致性（是否符合品牌形象）
2. 信息准确性（是否有夸大或误导）
3. 合规风险（是否有潜在的法律或舆论风险）
4. 受众适配度（是否适合目标人群）

给出评分（1-10）和具体修改建议。"""
```

## 六、前端核心实现

### 6.1 TypeScript 类型定义（src/types/persona.ts）

```typescript
export interface PersonaProfile {
  id: number
  name: string
  age: number
  gender: string
  city: string
  occupation: string
  monthly_income: number
  personality: {
    mbti: string
    communication_style: string
    description: string
  }
  consumer_profile: {
    price_sensitivity: number
    brand_loyalty: number
    decision_factors: string[]
    purchase_frequency: string
    monthly_disposable: number
  }
  media_behavior: {
    platforms: string[]
    content_preference: string[]
    influence_susceptibility: number
    influence_power: number
  }
  social_behavior: {
    post_frequency: string
    interaction_style: string
    stance_on_ads: string
  }
  backstory: string
}

export interface PersonaGroup {
  id: number
  name: string
  description: string
  persona_count: number
  created_at: string
}

export interface FocusGroupResponse {
  persona_id: number
  persona_name: string
  persona_brief: string
  response: string
}

export interface FocusGroupSummary {
  consensus: string[]
  divergence: string[]
  key_insights: string[]
  segment_summary: Record<string, string>
  recommendations: string[]
}
```

### 6.2 TypeScript 类型定义（src/types/simulation.ts）

```typescript
export interface SimulationMetrics {
  round: number
  reach_rate: number
  engagement_rate: number
  avg_sentiment: number
  avg_purchase_intent: number
  action_counts: Record<string, number>
}

export interface SimulationAction {
  persona_name: string
  action_type: string
  comment_text?: string
  sentiment_score: number
  purchase_intent: number
}

export interface SimulationReport {
  executive_summary: string
  metrics: Record<string, string>
  segment_insights: Array<{
    segment: string
    reaction: string
    key_concern: string
  }>
  risks: string[]
  optimization_suggestions: string[]
}

export interface ABTestResult {
  variants: Array<{
    label: string
    content_title: string
    metrics: SimulationMetrics
  }>
  winner: string
  comparison_summary: string
}

export type WSEvent =
  | { type: 'round_progress'; round: number; total: number }
  | { type: 'agent_action'; persona: string; action: string; content: string }
  | { type: 'metrics_update' } & SimulationMetrics
  | { type: 'simulation_complete'; total_rounds: number }
```

### 6.3 WebSocket Composable（src/composables/useWebSocket.ts）

```typescript
import { ref, onUnmounted } from 'vue'

export const useWebSocket = (path: string) => {
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const messages = ref<any[]>([])

  const connect = () => {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${location.hostname}:8000${path}`
    ws.value = new WebSocket(url)

    ws.value.onopen = () => { connected.value = true }
    ws.value.onclose = () => { connected.value = false }
    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      messages.value.push(data)
    }
  }

  const send = (data: any) => {
    ws.value?.send(JSON.stringify(data))
  }

  const disconnect = () => {
    ws.value?.close()
  }

  onUnmounted(() => disconnect())

  return { connected, messages, connect, send, disconnect }
}
```

### 6.4 API 封装（src/api/index.ts）

```typescript
import axios from 'axios'

const service = axios.create({
  baseURL: '/api',
  timeout: 120000
})

service.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default service
```

### 6.5 API 封装示例（src/api/simulation.ts）

```typescript
import service from './index'

export const createSimulation = (data: {
  tenant_id: number
  content_id: number
  persona_group_id: number
  platform: string
  config: Record<string, any>
}) => service.post('/simulations', data)

export const startSimulation = (sessionId: number) =>
  service.post(`/simulations/${sessionId}/start`)

export const getSimulationStatus = (sessionId: number) =>
  service.get(`/simulations/${sessionId}/status`)

export const getSimulationReport = (sessionId: number) =>
  service.get(`/simulations/${sessionId}/report`)

export const createABTest = (data: {
  tenant_id: number
  name: string
  content_ids: number[]
  persona_group_id: number
  platform: string
}) => service.post('/simulations/ab-test', data)

export const getABTestResult = (testId: number) =>
  service.get(`/simulations/ab-test/${testId}`)
```

### 6.6 路由配置（src/router/index.ts）

```typescript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', component: () => import('@/views/Dashboard.vue') },

  // 画像工厂
  { path: '/personas', component: () => import('@/views/persona/PersonaList.vue') },
  { path: '/personas/create', component: () => import('@/views/persona/PersonaCreate.vue') },
  { path: '/personas/groups/:groupId', component: () => import('@/views/persona/PersonaGroupDetail.vue') },
  { path: '/personas/:id/chat', component: () => import('@/views/persona/PersonaChat.vue') },

  // 焦点小组
  { path: '/focus-groups', component: () => import('@/views/focus_group/FocusGroupList.vue') },
  { path: '/focus-groups/:id', component: () => import('@/views/focus_group/FocusGroupSession.vue') },

  // 内容工坊
  { path: '/workshop/create', component: () => import('@/views/workshop/WorkshopCreate.vue') },
  { path: '/workshop/:id', component: () => import('@/views/workshop/WorkshopSession.vue') },

  // 沙盘推演
  { path: '/simulation/create', component: () => import('@/views/simulation/SimulationCreate.vue') },
  { path: '/simulation/:id', component: () => import('@/views/simulation/SimulationRun.vue') },
  { path: '/simulation/:id/report', component: () => import('@/views/simulation/SimulationReport.vue') },
  { path: '/simulation/ab-test/:id', component: () => import('@/views/simulation/ABTestResult.vue') },

  // 市场智脑
  { path: '/market/graphs', component: () => import('@/views/market/MarketGraph.vue') },
  { path: '/market/insights', component: () => import('@/views/market/MarketInsights.vue') },

  // 舆情哨兵
  { path: '/sentiment/analyze', component: () => import('@/views/sentiment/SentimentAnalyze.vue') },
  { path: '/sentiment/:id', component: () => import('@/views/sentiment/SentimentReport.vue') },

  // 策略参谋
  { path: '/strategy/analyze', component: () => import('@/views/strategy/StrategyAnalyze.vue') },
  { path: '/strategy/:id', component: () => import('@/views/strategy/StrategyReport.vue') },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
```

## 七、Docker 部署

### 7.1 docker-compose.yml

```yaml
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      mysql:
        condition: service_healthy
      neo4j:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root_password
      MYSQL_DATABASE: echo_agent
      MYSQL_USER: echo_agent
      MYSQL_PASSWORD: your_password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5
    restart: unless-stopped

  neo4j:
    image: neo4j:5
    environment:
      NEO4J_AUTH: neo4j/your_password
    ports:
      - "7474:7474"
      - "7687:7687"
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "neo4j", "status"]
      interval: 10s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  mysql_data:
  neo4j_data:
  redis_data:
```

### 7.2 后端 Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY backend/pyproject.toml backend/requirements.txt ./
RUN uv pip install --system -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.3 前端 Dockerfile

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

COPY frontend/ .
RUN pnpm build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## 八、开发路线图

### P0 - 最小可行产品

- [ ] 项目初始化（FastAPI + Vue 3 + MySQL + Redis）
- [ ] 数据库建表 + 基础 CRUD
- [ ] LLM 客户端封装
- [ ] WebSocket 连接管理
- [ ] **画像工厂**
  - [ ] 画像组创建（文本描述输入）
  - [ ] 画像生成（LLM 批量生成）
  - [ ] 画像列表/详情展示
  - [ ] 虚拟焦点小组（单问多答 + 汇总）
- [ ] **沙盘推演**
  - [ ] 单内容模拟（小红书平台）
  - [ ] 模拟引擎核心循环
  - [ ] WebSocket 实时推送
  - [ ] 模拟报告生成
- [ ] 前端基础框架 + 画像页 + 模拟页

### P1 - 内容闭环

- [x] **内容工坊**
    - [x] 创作 brief 输入
    - [x] 多 Agent 协作流程
    - [x] 消费者 Agent 评价（从画像库调用）
    - [x] 品牌守护检查
- [x] **A/B 测试**
    - [x] 多内容并行模拟
    - [x] 对比报告生成
- [x] 画像 → 模拟数据自动流转
- [x] 更多平台模型（抖音、微博、微信）

### P2 - 洞察闭环

- [x] **市场智脑**
    - [x] Neo4j 知识图谱构建
    - [x] 文档上传 + 实体提取
    - [x] D3/SVG 图谱可视化
    - [x] 竞品分析报告
- [x] 洞察自动注入内容工坊

### P2 验收记录

- 已新增内容工坊会话与运行接口：/api/workshop/sessions、/api/workshop/sessions/{id}/run。
- 已支持工坊一键发起 A/B：/api/workshop/sessions/{id}/ab-test，并输出 winner 与 summary。
- 已新增市场智脑图谱构建：/api/market/graphs/build、/api/market/graphs/upload。
- 已支持竞品分析报告：/api/market/graphs/{id}/report。
- 已支持洞察注入工坊：/api/workshop/sessions/{id}/inject-insights。

### P3 - 风控闭环

- [x] **舆情哨兵**
  - [x] 事前预判模式
  - [x] 应对方案生成 + 验证
- [ ] 触发器系统（跨模块自动触发）

### P3 验收记录

- 已新增舆情哨兵评估接口：POST /api/sentiment-guard/assess，异步返回 task_id + session_id。
- 已支持事前预判（proactive）与事后应对（reactive）两种模式。
- 4步评估流水线：风险评估(LLM) → 传播模拟(规则) → 方案生成(LLM,3套) → 方案验证(LLM并发x3)。
- WebSocket /ws/sentiment-guard/{id} 实时推送每步进度与结果。
- 前端页面含进度步骤条、风险评级条、传播模拟指标、3套方案卡片对比、推荐方案高亮。

### P4 - 决策闭环

- [x] **策略参谋**
  - [x] 5 种思维模型 Agent
  - [x] 交叉质疑机制
  - [x] 综合报告生成
- [ ] 完整工作流编排引擎

### P4 验收记录

- 已新增策略参谋分析接口：POST /api/strategy-advisor/analyze，异步返回 task_id + session_id。
- 3阶段分析流程：Phase1 5模型并发独立分析 → Phase2 交叉辩论(最大分歧对1v1) → Phase3 综合报告。
- 5种思维模型：第一性原理、博弈论、系统思维、逆向思维、用户视角，各自独立 LLM 调用。
- WebSocket /ws/strategy-advisor/{id} 逐个模型实时推送 model_done 事件。
- 前端页面含 Phase 进度条、5模型实时卡片、辩论对战面板、4象限综合报告 + 决策建议框。

### P5 - 企业级

- [ ] 多租户隔离
- [ ] 用户认证 + 权限管理
- [ ] API 开放（对外 SDK）
- [ ] 私有化部署方案
- [ ] 监控 + 日志 + 计费

## 九、测试策略

### 9.1 关键测试场景

| 场景 | 测试内容 | 验证标准 |
|------|---------|---------|
| 画像生成 | 10 个画像的差异性 | 无两个画像在 3 个以上维度相同 |
| 焦点小组 | Agent 回答与人设一致性 | 价格敏感型用户不会说"价格无所谓" |
| 模拟引擎 | 传播逻辑正确性 | 高互动内容的传播系数 > 低互动 |
| 模拟稳态 | 稳态检测 | 传播停止后不继续产生新动作 |
| A/B 对比 | 相同用户群的可比性 | 用户群一致，只有内容不同 |
| 内容工坊 | Agent 角色区分 | 策划不写文案，文案不做策划 |
| WebSocket | 实时推送 | 延迟 < 500ms |

### 9.2 测试示例

```python
import pytest
from app.services.persona_service import PersonaService


@pytest.mark.asyncio
async def test_persona_diversity():
    """测试生成的画像具有足够的差异性"""
    svc = PersonaService()
    result = await svc.generate_group("25-35岁一线城市女性白领", count=10)
    personas = result["personas"]

    # 确保生成了指定数量
    assert len(personas) == 10

    # 确保名字不重复
    names = [p["name"] for p in personas]
    assert len(set(names)) == 10

    # 确保消费类型有差异
    sensitivities = [p["consumer_profile"]["price_sensitivity"] for p in personas]
    assert max(sensitivities) - min(sensitivities) > 0.3

    # 确保年龄有分布
    ages = [p["age"] for p in personas]
    assert max(ages) - min(ages) >= 5


@pytest.mark.asyncio
async def test_persona_consistency():
    """测试 Agent 回答与人设一致"""
    from app.agents.persona_agent import PersonaAgent
    from app.llm.client import llm_light

    persona = {
        "id": 1,
        "name": "测试用户",
        "age": 25,
        "gender": "女",
        "city": "上海",
        "occupation": "设计师",
        "monthly_income": 15000,
        "personality": {
            "mbti": "ENFP",
            "communication_style": "活泼直接",
            "description": "开朗外向，喜欢尝试新事物"
        },
        "consumer_profile": {
            "price_sensitivity": 0.8,
            "brand_loyalty": 0.3,
            "decision_factors": ["价格", "颜值"],
            "purchase_frequency": "冲动型",
            "monthly_disposable": 5000
        },
        "media_behavior": {
            "platforms": ["小红书", "抖音"],
            "content_preference": ["种草", "测评"],
            "influence_susceptibility": 0.7,
            "influence_power": 0.4
        },
        "social_behavior": {
            "post_frequency": "高频",
            "interaction_style": "评论派",
            "stance_on_ads": "中立"
        }
    }

    agent = PersonaAgent(persona, llm_light)
    response = await agent.interview("一支口红卖599你觉得贵吗？")

    # 价格敏感度为 0.8 的用户应该觉得贵
    assert any(word in response for word in ["贵", "高", "价格", "不便宜", "划不来"])
```


