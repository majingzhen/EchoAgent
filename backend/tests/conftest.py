import os
from pathlib import Path

# 指向测试专用配置文件（含非占位符 Key，不触发 LLMClient 校验）
_test_config = Path(__file__).parent / "test_config" / "app.yaml"
os.environ["ECHO_AGENT_CONFIG_PATH"] = str(_test_config)

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app_client():
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
