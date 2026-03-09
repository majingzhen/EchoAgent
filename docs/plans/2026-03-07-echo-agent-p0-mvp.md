# EchoAgent P0 MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在当前仓库内落地 EchoAgent 的 P0 可运行最小版本（画像工厂 + 焦点小组 + 沙盘推演骨架），并提供前后端联调入口。

**Architecture:** 采用独立子项目 `echo-agent/`，后端使用 FastAPI 提供 REST + WebSocket，前端使用 Vue3 + Vite 提供最小工作台。业务先实现内存态与可替换接口，后续可无缝接入 MySQL/Neo4j/Redis。

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, Uvicorn, Vue 3, TypeScript, Vue Router, Axios, Vite, Docker Compose

---

### Task 1: 创建项目骨架与配置

**Files:**
- Create: `echo-agent/backend/app/main.py`
- Create: `echo-agent/backend/app/config.py`
- Create: `echo-agent/backend/pyproject.toml`
- Create: `echo-agent/frontend/package.json`
- Create: `echo-agent/docker-compose.yml`
- Create: `echo-agent/.env.example`

**Step 1: 创建后端基础目录与入口**

- 新建 `app/main.py`，包含 FastAPI 实例、健康检查、路由注册。

**Step 2: 创建配置模型**

- 新建 `app/config.py`，实现环境变量读取（LLM、数据库、应用端口）。

**Step 3: 创建后端依赖声明**

- 新建 `pyproject.toml`，补齐 FastAPI + Pydantic + Uvicorn 等依赖。

**Step 4: 创建前端基础配置**

- 新建 `frontend/package.json`，定义 `dev/build/preview` 脚本与核心依赖。

**Step 5: 增加运行环境文件**

- 新建 `docker-compose.yml` 与 `.env.example`。

**Step 6: 验证文件完整性**

Run: `rg --files echo-agent`
Expected: 显示 backend/frontend/docker 关键文件路径。

### Task 2: 实现后端 P0 API（画像 + 焦点小组 + 沙盘推演）

**Files:**
- Create: `echo-agent/backend/app/api/router.py`
- Create: `echo-agent/backend/app/api/persona.py`
- Create: `echo-agent/backend/app/api/focus_group.py`
- Create: `echo-agent/backend/app/api/simulation.py`
- Create: `echo-agent/backend/app/api/task.py`
- Create: `echo-agent/backend/app/api/ws.py`
- Create: `echo-agent/backend/app/models/common.py`
- Create: `echo-agent/backend/app/models/persona.py`
- Create: `echo-agent/backend/app/models/simulation.py`
- Create: `echo-agent/backend/app/services/persona_service.py`
- Create: `echo-agent/backend/app/services/focus_group_service.py`
- Create: `echo-agent/backend/app/services/simulation_engine.py`
- Create: `echo-agent/backend/app/services/task_service.py`
- Create: `echo-agent/backend/app/ws/manager.py`

**Step 1: 先写接口模型**

- 定义请求/响应结构（persona 组、focus group 消息、simulation 会话状态）。

**Step 2: 实现服务层最小能力**

- 画像生成采用规则+模板（无外部依赖）；
- 焦点小组返回按画像差异化回答；
- 模拟引擎输出轮次指标与动作流。

**Step 3: 组装 REST API**

- 覆盖文档中的 P0 关键端点（创建、查询、启动、报告、任务状态）。

**Step 4: 组装 WebSocket**

- 支持 `/ws/simulation/{id}` 与 `/ws/focus-group/{id}` 的连接与广播。

**Step 5: 本地验证**

Run: `python -m compileall echo-agent/backend/app`
Expected: 无语法错误。

### Task 3: 实现前端 P0 工作台

**Files:**
- Create: `echo-agent/frontend/index.html`
- Create: `echo-agent/frontend/vite.config.ts`
- Create: `echo-agent/frontend/tsconfig.json`
- Create: `echo-agent/frontend/src/main.ts`
- Create: `echo-agent/frontend/src/App.vue`
- Create: `echo-agent/frontend/src/router/index.ts`
- Create: `echo-agent/frontend/src/api/index.ts`
- Create: `echo-agent/frontend/src/api/persona.ts`
- Create: `echo-agent/frontend/src/api/simulation.ts`
- Create: `echo-agent/frontend/src/composables/useWebSocket.ts`
- Create: `echo-agent/frontend/src/views/Dashboard.vue`
- Create: `echo-agent/frontend/src/views/persona/PersonaCreate.vue`
- Create: `echo-agent/frontend/src/views/focus_group/FocusGroupSession.vue`
- Create: `echo-agent/frontend/src/views/simulation/SimulationRun.vue`

**Step 1: 搭建路由与导航**

- 最小 4 页：仪表盘、画像创建、焦点小组、模拟运行。

**Step 2: 封装 API 客户端**

- Axios 实例 + persona/simulation API 方法。

**Step 3: 封装 WebSocket composable**

- 连接状态、消息流、发送与断开。

**Step 4: 页面联通后端**

- 页面可发起创建请求并展示返回数据。

**Step 5: 前端构建验证**

Run: `npm --prefix echo-agent/frontend run build`
Expected: 构建成功。

### Task 4: 补充文档与运行说明

**Files:**
- Create: `echo-agent/README.md`

**Step 1: 写清启动流程**

- 本地启动、Docker 启动、关键 API 示例。

**Step 2: 写清下一阶段扩展点**

- MySQL/Neo4j/Redis 接入点、LLM 接入点。

**Step 3: 验证文档与实现一致**

Run: `rg "echo-agent" -n echo-agent/README.md`
Expected: 关键路径与命令存在。

