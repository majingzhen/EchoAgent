from functools import lru_cache
import os
from pathlib import Path
from typing import Any, List

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseModel):
    name: str = "EchoAgent API"
    host: str = "0.0.0.0"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    secret_key: str = "replace_me"


class LLMConfig(BaseModel):
    api_key: str = "your_api_key"
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name: str = "qwen-plus"
    light_model_name: str | None = "qwen-turbo"
    vision_model_name: str = "qwen-vl-plus"

    @model_validator(mode="after")
    def normalize_light_model(self) -> "LLMConfig":
        if not self.light_model_name:
            self.light_model_name = self.model_name
        return self


class SQLiteConfig(BaseModel):
    path: str = "data/echo_agent.db"


class SearchConfig(BaseModel):
    provider: str = "duckduckgo"  # duckduckgo / bing / serper
    api_key: str = ""
    max_results: int = 5


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    app: AppConfig = Field(default_factory=AppConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    sqlite: SQLiteConfig = Field(default_factory=SQLiteConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def app_host(self) -> str:
        return self.app.host

    @property
    def app_port(self) -> int:
        return self.app.port

    @property
    def frontend_url(self) -> str:
        return self.app.frontend_url

    @property
    def cors_origins(self) -> List[str]:
        return self.app.cors_origins

    @property
    def llm_api_key(self) -> str:
        return self.llm.api_key

    @property
    def llm_base_url(self) -> str:
        return self.llm.base_url

    @property
    def llm_model_name(self) -> str:
        return self.llm.model_name

    @property
    def llm_light_model_name(self) -> str:
        return self.llm.light_model_name or self.llm.model_name

    @property
    def secret_key(self) -> str:
        return self.app.secret_key


def _load_yaml_config() -> dict[str, Any]:
    default_path = Path(__file__).resolve().parent.parent / "config" / "app.yaml"
    config_path = Path(os.getenv("ECHO_AGENT_CONFIG_PATH", str(default_path)))
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as fp:
        payload = yaml.safe_load(fp) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(**_load_yaml_config())
