from fastapi import APIRouter

from app.api import export, focus_group, market, persona, search, sentiment_guard, simulation, strategy_advisor, task, utils, workflow, workshop, ws

api_router = APIRouter(prefix="/api")
api_router.include_router(persona.router)
api_router.include_router(export.router)
api_router.include_router(search.router)
api_router.include_router(utils.router)
api_router.include_router(focus_group.router)
api_router.include_router(simulation.router)
api_router.include_router(workshop.router)
api_router.include_router(market.router)
api_router.include_router(task.router)
api_router.include_router(sentiment_guard.router)
api_router.include_router(strategy_advisor.router)
api_router.include_router(workflow.router)
api_router.include_router(ws.router)
