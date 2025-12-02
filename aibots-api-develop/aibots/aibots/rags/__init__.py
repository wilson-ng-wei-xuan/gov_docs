from .base import AtlasRAGException, RAGEngine
from .llm_stack import LLMStackEngine
from .aibots import AIBotsEngine
from .govtext import GovTextEngine


engines: dict[str, type[RAGEngine]] = {
    LLMStackEngine.type: LLMStackEngine,
    AIBotsEngine.type: AIBotsEngine,
    GovTextEngine.type: GovTextEngine,
}


__all__ = (
    "engines",
    "AtlasRAGException",
    "RAGEngine",
    "LLMStackEngine",
    "AIBotsEngine",
    "GovTextEngine",
)
