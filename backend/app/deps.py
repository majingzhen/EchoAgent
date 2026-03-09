from app.config import get_settings
from app.db.memory_store import MemoryStore
from app.db.sqlite import SQLiteDatabase
from app.llm.client import LLMClient
from app.llm.search_client import SearchClient
from app.repositories.focus_group_repository import FocusGroupRepository
from app.repositories.market_repository import MarketRepository
from app.repositories.persona_memory_repository import PersonaMemoryRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.sentiment_guard_repository import SentimentGuardRepository
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.strategy_advisor_repository import StrategyAdvisorRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.workflow_repository import WorkflowRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.services.focus_group_service import FocusGroupService
from app.services.market_service import MarketService
from app.services.persona_service import PersonaService
from app.services.search_service import SearchService
from app.services.sentiment_guard_service import SentimentGuardService
from app.services.simulation_engine import SimulationEngine
from app.services.strategy_advisor_service import StrategyAdvisorService
from app.services.task_service import TaskService
from app.services.workflow_engine import WorkflowEngine
from app.services.workshop_service import WorkshopService
from app.ws.manager import WSConnectionManager

settings = get_settings()

sqlite_db = SQLiteDatabase(settings)
memory_store = MemoryStore()
llm_client = LLMClient(settings)

persona_repository = PersonaRepository(sqlite_db)
persona_memory_repository = PersonaMemoryRepository(sqlite_db)
focus_group_repository = FocusGroupRepository(sqlite_db)
simulation_repository = SimulationRepository(sqlite_db)
workshop_repository = WorkshopRepository(sqlite_db)
market_repository = MarketRepository(sqlite_db)
task_repository = TaskRepository(memory_store)
sentiment_guard_repository = SentimentGuardRepository(sqlite_db)
strategy_advisor_repository = StrategyAdvisorRepository(sqlite_db)
workflow_repository = WorkflowRepository(sqlite_db)

ws_manager = WSConnectionManager()
task_service = TaskService(task_repository)
persona_service = PersonaService(persona_repository, llm_client, ws_manager, task_service)
focus_group_service = FocusGroupService(focus_group_repository, llm_client, ws_manager, task_service, persona_memory_repository)
simulation_engine = SimulationEngine(simulation_repository, persona_repository, ws_manager, task_service, llm_client, persona_memory_repository)
market_service = MarketService(market_repository, llm_client)
workshop_service = WorkshopService(workshop_repository, persona_repository, simulation_engine, market_repository, llm_client, ws_manager, task_service)
sentiment_guard_service = SentimentGuardService(sentiment_guard_repository, llm_client, ws_manager, task_service)
strategy_advisor_service = StrategyAdvisorService(strategy_advisor_repository, llm_client, ws_manager, task_service)
_search_client = SearchClient(
    provider=settings.search.provider,
    api_key=settings.search.api_key,
    max_results=settings.search.max_results,
)
search_service = SearchService(_search_client, llm_client)

workflow_engine = WorkflowEngine(
    repository=workflow_repository,
    workshop_service=workshop_service,
    simulation_engine=simulation_engine,
    sentiment_guard_service=sentiment_guard_service,
    strategy_advisor_service=strategy_advisor_service,
    market_service=market_service,
    task_service=task_service,
    ws_manager=ws_manager,
)
