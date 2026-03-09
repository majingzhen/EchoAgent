import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import get_settings, is_llm_configured
from app.deps import sqlite_db, memory_store

logger = logging.getLogger(__name__)
settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(_: Request, exc: RuntimeError) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.exception_handler(Exception)
async def generic_error_handler(_: Request, exc: Exception) -> JSONResponse:
    name = type(exc).__name__
    # 网络超时单独给 504
    if "Timeout" in name or "timeout" in name.lower():
        return JSONResponse(status_code=504, content={"detail": f"LLM 请求超时，请稍后重试（{name}）"})
    return JSONResponse(status_code=500, content={"detail": f"{name}: {exc}"})


@app.on_event("startup")
async def startup_init() -> None:
    await sqlite_db.ensure_ready()
    llm_cfg = settings.llm
    logger.info(
        "EchoAgent started | model=%s | base_url=%s",
        llm_cfg.model_name,
        llm_cfg.base_url,
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/config/status")
def config_status() -> dict:
    configured = is_llm_configured(settings)
    return {
        "llm_configured": configured,
        "model": settings.llm.model_name if configured else None,
        "base_url": settings.llm.base_url if configured else None,
    }


app.include_router(api_router)


@app.on_event("shutdown")
async def shutdown_resources() -> None:
    await sqlite_db.close()
    await memory_store.close()
