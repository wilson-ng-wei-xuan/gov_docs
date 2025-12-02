from .agents import router as agent_router
from .knowledge_bases import router as knowledge_bases_router
from .rag_configs import router as rag_configs_router
from .approvals import router as approvals_router
from .rag_status import router

__all__ = (router,)

router.include_router(approvals_router)
router.include_router(agent_router)
router.include_router(knowledge_bases_router)
router.include_router(rag_configs_router)
