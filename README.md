# EchoAgent

> 开源自托管 AI 虚拟用研工作台——用 AI 虚拟消费者代替真实焦点小组，加速营销内容从策略到落地的全流程。

## 功能模块

| 模块 | 说明 |
|------|------|
| **画像工厂** | 描述目标人群，AI 生成差异化虚拟消费者画像 |
| **焦点小组** | 向虚拟画像提问，支持独立作答和多轮讨论模式 |
| **内容工坊** | 多 Agent 流水线：策略方向 → 多版本文案 → 画像评分 → 品牌审核 |
| **沙盘推演** | 模拟内容在虚拟画像间的传播，预测互动趋势 |
| **市场智脑** | 上传竞品资料，AI 提取实体图谱并生成竞品分析报告 |
| **舆情哨兵** | 分析舆情风险，生成危机应对方案 |
| **策略参谋** | 多模型辩论式策略建议生成 |
| **工作流引导** | 按场景串联各模块，引导式完成完整营销活动流程 |

---

## 快速启动（Docker，推荐）

### 前置条件

- Docker & Docker Compose
- 任意兼容 OpenAI 接口的 LLM 服务（通义千问、OpenAI、Ollama 等）

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/your-org/echo-agent.git
cd echo-agent

# 2. 配置 LLM API Key（必填）
cp backend/config/app.yaml backend/config/app.yaml.bak
# 编辑 backend/config/app.yaml，填写 llm.api_key

# 3. 启动
docker compose up --build

# 前端：http://localhost:3000
# 后端 API 文档：http://localhost:8000/docs
```

> **数据持久化**：SQLite 数据库存储在 Docker 命名卷 `echo_agent_data`，重启不丢失。

---

## 本地开发

### 后端

```bash
cd backend

# 安装依赖（Python 3.11+）
pip install -e ".[dev]"

# 配置（编辑 config/app.yaml 填写 API Key）

# 启动（首次启动自动建表）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173（开发代理已配置，/api → localhost:8000）
```

---

## LLM 提供商配置

编辑 `backend/config/app.yaml` 的 `llm` 节点，支持任何兼容 OpenAI 接口的服务：

```yaml
# 通义千问（阿里云百炼）
llm:
  api_key: sk-xxx
  base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
  model_name: qwen-plus
  light_model_name: qwen-turbo
  vision_model_name: qwen-vl-plus

# OpenAI
# llm:
#   api_key: sk-xxx
#   base_url: https://api.openai.com/v1
#   model_name: gpt-4o
#   light_model_name: gpt-4o-mini
#   vision_model_name: gpt-4o

# Ollama（本地）
# llm:
#   api_key: ollama
#   base_url: http://localhost:11434/v1
#   model_name: qwen2.5:14b
#   light_model_name: qwen2.5:7b
#   vision_model_name: llava:13b

# DeepSeek
# llm:
#   api_key: sk-xxx
#   base_url: https://api.deepseek.com/v1
#   model_name: deepseek-chat

# Claude（Anthropic）
# llm:
#   api_key: sk-ant-xxx
#   base_url: https://api.anthropic.com/v1
#   model_name: claude-sonnet-4-6
```

启动时日志会打印当前使用的模型，便于确认配置生效。

---

## 环境变量

可用环境变量覆盖配置文件中的任意值（双下划线表示层级）：

```bash
LLM__API_KEY=your_key          # LLM API Key
LLM__MODEL_NAME=gpt-4o         # 主力模型
APP__CORS_ORIGINS=["http://..."]  # 跨域白名单
SQLITE__PATH=data/echo_agent.db   # 数据库路径
```

完整示例见 `.env.example`。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.11 · FastAPI · SQLAlchemy (async) · SQLite · OpenAI SDK |
| 前端 | Vue 3 · TypeScript · Vite · d3-force |
| 部署 | Docker · Nginx |
| LLM | 兼容 OpenAI 接口的任意提供商 |

---

## 主要 API

```
POST /api/personas/generate          生成画像组
POST /api/focus-groups/sessions      创建焦点小组
POST /api/focus-groups/{id}/ask      向画像提问
POST /api/workshop/sessions          创建内容工坊
POST /api/workshop/sessions/{id}/run 运行多 Agent 流程
POST /api/simulations                创建传播推演
POST /api/market/graphs              构建市场图谱
GET  /api/market/graphs/{id}/report  获取竞品分析报告
WS   /api/ws/workshop/{id}           内容工坊实时进度
WS   /api/ws/focus-group/{id}        焦点小组实时消息
WS   /api/ws/simulation/{id}         传播推演实时进度
```

完整文档：启动后访问 `http://localhost:8000/docs`

---

## 目录结构

```
echo-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI 路由
│   │   ├── services/     # 业务逻辑
│   │   ├── repositories/ # 数据访问
│   │   ├── models/       # Pydantic 模型
│   │   ├── llm/          # LLM 客户端
│   │   └── ws/           # WebSocket 管理
│   ├── config/
│   │   └── app.yaml      # 主配置文件（含 LLM 配置）
│   └── migrations/
│       └── init.sql      # 数据库建表 SQL（启动自动执行）
├── frontend/
│   └── src/
│       ├── views/        # 页面组件
│       ├── api/          # HTTP 接口封装
│       └── config/
│           └── templates.ts  # 内置模板库
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env.example
```
