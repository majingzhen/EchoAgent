# EchoAgent Persistence Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用 MySQL/Neo4j/Redis 替换后端内存存储，并通过配置文件统一管理连接参数。

**Architecture:** 新增 `config/app.yaml` 作为主配置源，`Settings` 支持 YAML + 环境变量覆盖。后端新增 `db` 与 `repositories` 层：MySQL 持久化业务数据、Neo4j 存画像关系图、Redis 存异步任务状态。服务层改为调用仓储接口，保持 API 协议不变。

**Tech Stack:** FastAPI, Pydantic Settings, PyYAML, SQLAlchemy Async + aiomysql, redis-py, neo4j driver

---

### Task 1: 配置文件化与依赖升级

**Files:**
- Create: `echo-agent/backend/config/app.yaml`
- Modify: `echo-agent/backend/app/config.py`
- Modify: `echo-agent/backend/pyproject.toml`

**Step 1: 新增 YAML 配置模板**
- 建立 `app.yaml`，定义 app/mysql/neo4j/redis/llm 各项参数。

**Step 2: 实现配置加载链路**
- `config.py` 支持 `config/app.yaml` 读取；
- 环境变量保留覆盖能力（优先级：ENV > YAML 默认值）。

**Step 3: 增加持久化依赖**
- 增加 `PyYAML`、`SQLAlchemy`、`aiomysql`、`redis`、`neo4j`。

**Step 4: 验证**
Run: `python - <<'PY' ... from app.config import get_settings ... PY`
Expected: 可输出 MySQL/Neo4j/Redis 配置值。

### Task 2: 构建数据库连接与初始化模块

**Files:**
- Create: `echo-agent/backend/app/db/__init__.py`
- Create: `echo-agent/backend/app/db/mysql.py`
- Create: `echo-agent/backend/app/db/redis.py`
- Create: `echo-agent/backend/app/db/neo4j.py`
- Create: `echo-agent/backend/migrations/init.sql`
- Modify: `echo-agent/backend/app/main.py`

**Step 1: MySQL 连接与会话工厂**
- 构建异步 engine/sessionmaker；
- 增加 `run_migrations()` 自动执行 `init.sql`（仅创建表）。

**Step 2: Redis 客户端封装**
- 提供 get/set/hash + JSON 序列化辅助函数。

**Step 3: Neo4j 客户端封装**
- 提供画像节点与关系写入方法（upsert persona node / relation）。

**Step 4: 应用生命周期接入**
- FastAPI startup 初始化数据库与连接；
- shutdown 正确释放连接。

### Task 3: 仓储层改造（替代 InMemoryStore）

**Files:**
- Create: `echo-agent/backend/app/repositories/__init__.py`
- Create: `echo-agent/backend/app/repositories/persona_repository.py`
- Create: `echo-agent/backend/app/repositories/focus_group_repository.py`
- Create: `echo-agent/backend/app/repositories/simulation_repository.py`
- Create: `echo-agent/backend/app/repositories/task_repository.py`

**Step 1: Persona 仓储**
- 持久化 `persona_group/persona`，查询 group/detail/persona；
- 创建画像时同步写 Neo4j 画像节点和基本关系。

**Step 2: FocusGroup 仓储**
- 持久化 `focus_group_session/focus_group_message`；
- 支持消息增量写入与读取。

**Step 3: Simulation 仓储**
- 持久化 `simulation_session/simulation_action/simulation_report/ab_test`；
- 支持轮次状态更新与报告读取。

**Step 4: Task 仓储（Redis）**
- 用 Redis Hash 存储 task；
- 支持创建、更新、读取任务。

### Task 4: 服务层切换到仓储实现

**Files:**
- Modify: `echo-agent/backend/app/services/persona_service.py`
- Modify: `echo-agent/backend/app/services/focus_group_service.py`
- Modify: `echo-agent/backend/app/services/simulation_engine.py`
- Modify: `echo-agent/backend/app/services/task_service.py`
- Modify: `echo-agent/backend/app/deps.py`
- Modify: `echo-agent/backend/app/api/*.py`（若需 async 化）

**Step 1: 注入仓储依赖**
- `deps.py` 组装 repository + services，不再引用 `storage.py`。

**Step 2: 保持 API 兼容**
- 路由输入输出结构不变；
- 需要时将端点切换为 `async def`。

**Step 3: 清理内存存储依赖**
- `storage.py` 标记废弃或移除调用。

### Task 5: 验证与文档

**Files:**
- Modify: `echo-agent/README.md`
- Modify: `echo-agent/.env.example`

**Step 1: 增加配置文件说明**
- 描述 `config/app.yaml` 与环境变量覆盖规则；
- 增加 MySQL/Neo4j/Redis 启动依赖说明。

**Step 2: 运行验证**
Run: `python -m compileall echo-agent/backend/app`
Run: `python -m pytest -q`
Expected: 通过（或明确失败原因）。

**Step 3: 冒烟联调**
Run: 通过 TestClient 串行调用 personas -> focus-group -> simulations -> tasks -> report
Expected: 全链路返回 200。

