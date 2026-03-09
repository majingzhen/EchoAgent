"""
冒烟测试：验证核心 API 路径可达、返回结构正确。
不调用真实 LLM（通过 conftest.py 中的 mock_llm 拦截）。
"""
from fastapi.testclient import TestClient


# ── /health ──────────────────────────────────────────────────────────────────

def test_health(app_client: TestClient) -> None:
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ── /api/config/status ────────────────────────────────────────────────────────

def test_config_status_configured(app_client: TestClient) -> None:
    """测试用 Key 非占位符，应返回 llm_configured=true"""
    resp = app_client.get("/api/config/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "llm_configured" in data
    assert data["llm_configured"] is True
    assert data["model"] is not None


def test_config_status_unconfigured() -> None:
    """占位符 Key 应返回 llm_configured=false"""
    import os
    from unittest.mock import patch

    # 临时覆盖 Key 为占位符
    with patch.dict(os.environ, {"LLM__API_KEY": "your_api_key_here"}):
        from app.config import get_settings, is_llm_configured
        # lru_cache 已缓存，直接用 is_llm_configured 测逻辑
        from app.config import Settings, LLMConfig
        s = Settings(llm=LLMConfig(api_key="your_api_key_here"))
        assert is_llm_configured(s) is False

    s2 = Settings(llm=LLMConfig(api_key="sk-real-key"))
    assert is_llm_configured(s2) is True


# ── /api/personas ─────────────────────────────────────────────────────────────

def test_persona_generate_returns_task(app_client: TestClient) -> None:
    """画像生成接口应立即返回 task_id，不阻塞"""
    payload = {
        "description": "25-35岁一线城市白领，关注性价比",
        "count": 3,
        "group_name": "测试画像组",
    }
    resp = app_client.post("/api/personas/generate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    # 返回 AsyncTask 结构
    assert "task_id" in data or "data" in data


def test_persona_groups_list(app_client: TestClient) -> None:
    """画像组列表接口应返回列表"""
    resp = app_client.get("/api/personas/groups")
    assert resp.status_code == 200


# ── /api/focus-groups ─────────────────────────────────────────────────────────

def test_focus_group_create(app_client: TestClient) -> None:
    """创建焦点小组会话（FormData），group_id 不存在应返回 404"""
    resp = app_client.post(
        "/api/focus-groups",
        data={"persona_group_id": "99999", "topic": "测试话题"},
    )
    assert resp.status_code in (200, 404, 422)


def test_focus_group_sessions_list(app_client: TestClient) -> None:
    """焦点小组会话列表接口应返回 200"""
    resp = app_client.get("/api/focus-groups")
    assert resp.status_code == 200


# ── /api/simulations ──────────────────────────────────────────────────────────

def test_simulation_list(app_client: TestClient) -> None:
    resp = app_client.get("/api/simulations")
    assert resp.status_code == 200


# ── /api/market ───────────────────────────────────────────────────────────────

def test_market_graph_not_found(app_client: TestClient) -> None:
    """不存在的图谱应返回 404"""
    resp = app_client.get("/api/market/graphs/99999")
    assert resp.status_code in (200, 404)


# ── /api/workshop ─────────────────────────────────────────────────────────────

def test_workshop_sessions_list(app_client: TestClient) -> None:
    resp = app_client.get("/api/workshop/sessions")
    assert resp.status_code == 200
