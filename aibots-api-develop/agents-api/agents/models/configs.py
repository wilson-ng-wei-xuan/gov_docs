from __future__ import annotations

from typing import Any

from aibots.constants import (
    DEFAULT_LLM_MODEL_ID,
    PRODUCT_ID,
)
from atlas.genai.schemas import ModelID
from atlas.schemas import Uuid
from beanie import Document
from pydantic import BaseModel, ConfigDict, StrictStr

__all__ = (
    "NousConfig",
    "ConfigDB",
)


class NousConfig(BaseModel):
    """
    Nous Config values

    Attributes:
        api_key (StrictStr): Nous API Key values
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    api_key: StrictStr = ""


class Defaults(BaseModel):
    """
    Default values to be utilised

    Attributes:
        llm_model_id (AIModelID): Default LLM Model ID
    """

    llm_model_id: ModelID = ModelID(DEFAULT_LLM_MODEL_ID)


class ConfigDB(Document):
    """
    Stores all the config values within Atlas

    Attributes:
        id (Uuid): Product ID
        nous (NousConfig): Nous Config values
        wiki (list[Uuid]): List of Wiki values, defaults to an
                           empty list
    """

    model_config: ConfigDict = ConfigDict(extra="allow")

    id: Uuid = PRODUCT_ID
    nous: NousConfig = NousConfig()
    wiki: list[Uuid] = []
    defaults: dict[str, Any] = {}

    class Settings:
        name: str = "configs"
