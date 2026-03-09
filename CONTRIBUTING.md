# Contributing to EchoAgent

感谢你对 EchoAgent 的关注！以下是参与贡献的完整指南。

---

## 开始之前

- 提交 Bug 前，请先搜索 [Issues](../../issues) 确认没有重复
- 提交新功能前，建议先开 Issue 讨论方向，避免返工
- PR 请基于 `main` 分支创建

---

## 本地开发环境

### 后端

```bash
# Python 3.11+
cd backend
cp config/app.yaml.example config/app.yaml
# 编辑 config/app.yaml，填写 llm.api_key

pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 运行测试

```bash
cd backend
pytest
```

---

## 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 新功能 | `feat/描述` | `feat/knowledge-base` |
| Bug 修复 | `fix/描述` | `fix/focus-group-ws` |
| 文档 | `docs/描述` | `docs/api-examples` |
| 重构 | `refactor/描述` | `refactor/persona-service` |
| 测试 | `test/描述` | `test/simulation-smoke` |

---

## Commit 规范

遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

```
<type>(<scope>): <描述>

feat(persona): 添加画像记忆持久化
fix(focus-group): 修复 WebSocket 断连后消息丢失
docs(readme): 更新快速启动步骤
test(api): 添加市场图谱冒烟测试
refactor(workshop): 拆分 WorkshopService 子模块
```

**type 枚举**：`feat` / `fix` / `docs` / `test` / `refactor` / `chore`

---

## Pull Request

1. 确保 `pytest` 全部通过
2. 新功能需附带对应测试
3. 保持 PR 粒度小，一个 PR 做一件事
4. PR 标题遵循 commit 规范
5. 填写 PR 模板中的说明项

### PR 模板

```markdown
## 改动说明
简述本次 PR 做了什么。

## 关联 Issue
Closes #xxx

## 测试方式
说明如何验证这次改动。

## Checklist
- [ ] 本地测试通过
- [ ] 新增了对应测试（如适用）
- [ ] 文档已更新（如适用）
```

---

## 代码规范

### 后端（Python）

- 遵循 PEP8，函数和变量用 `snake_case`
- 所有函数加 type hints
- 异步函数用 `async def`，非阻塞操作用 `asyncio.create_task()`
- 不要在 Service 层直接捕获所有异常，让错误冒泡到全局处理器

```python
# 好
async def generate(self, req: GenerateRequest) -> AsyncTask:
    task_id = self.task_service.create()
    asyncio.create_task(self._run(task_id, req))
    return AsyncTask(task_id=task_id)

# 不好
async def generate(self, req):
    try:
        ...
    except Exception as e:
        print(e)
```

### 前端（Vue 3 + TypeScript）

- Composition API + `<script setup>` 语法
- 方法用 `const fn = () => {}` 而非 `function fn() {}`
- CSS 写在组件 `<style scoped>` 中
- API 调用统一在 `src/api/` 目录封装

---

## 项目结构

```
backend/
  app/
    api/          # 路由层，只做参数校验和响应包装
    services/     # 业务逻辑，调用 LLM 和 Repository
    repositories/ # 数据访问，封装 SQLite 操作
    models/       # Pydantic 数据模型
    llm/          # LLM 客户端和搜索客户端
    ws/           # WebSocket 连接管理
  tests/          # pytest 测试

frontend/
  src/
    views/        # 页面组件
    api/          # HTTP 接口封装
    router/       # 路由配置
```

---

## 需要帮助？

- 提 [Issue](../../issues) 描述你的问题
- 查看 [ROADMAP.md](./ROADMAP.md) 了解当前开发计划
- 后端 API 文档：启动后访问 `http://localhost:8000/docs`
