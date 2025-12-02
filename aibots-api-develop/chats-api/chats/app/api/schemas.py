from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, AtlasASGIConfig
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.genai.schemas import AIModel, AIModelType
from atlas.nous import NousService
from atlas.schemas import UserLogin
from atlas.structlog import StructLogService
from fastapi import APIRouter, Depends, Query, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version

from chats.environ import AIBotsChatEnviron

__doc__ = """
Contains all the API calls for the RAG API

Attributes:
    router (APIRouter): RAG API Router
"""


__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "prefix": "",
        "tags": ["Schemas"],
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("401_authentication_error"),
            **AtlasRouters.response("403_permissions_error"),
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class AIModelGet(APIGet, AIModel):
    """
    GET representation of an AI Model

    Attributes:
        id (ModelID): Model ID
        name (str): Name field, only allows hexadecimal values, hyphen and underscore
        description (str): Description field, defaults to an empty string
        type (AIModelType): AI model type
        security_classification (SecurityClassificationType): Security classification
                                                              type of the AI Model
        internal (bool): Indicates if the model is provided internally by GovTech,
                         defaults to False
        specs (AISpecificationsDict): AI Model specifications, defaults to a
                                      dictionary of AIParameter objects
        params (Dict[str, AIParameter]) Supported parameters of the AI Model,
                                        defaults to an empty dictionary
        streaming (bool): Indicates if streaming is supported, defaults to False
    """  # noqa: E501


@cbv(router)
class SchemasAPI:
    """
    Class-based view for representing the Schemas API

    Attributes:
        user (UserLogin): Authenticated user details
        atlas (AtlasConfig): Atlas Config class
        environ (AIBotsChatEnviron): Environment variables
        nous (NousService): Nous Service
        logger (StructLogService): Logging Service
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    def __init__(self):
        super().__init__()
        self.environ: AIBotsChatEnviron = self.atlas.environ
        self.messages: SimpleNamespace = SimpleNamespace(
            **self.environ.messages["schemas"]
        )
        self.nous: NousService = self.atlas.services.get("nous")
        self.logger: StructLogService = self.atlas.logger

    @router.get(
        "/schemas/ai/llms/",
        response_model=list[AIModelGet],
        include_in_schema=False,
    )
    @router.get(
        "/schemas/ai/llms",
        response_model=list[AIModelGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all AI Models that"
                "a user has access to",
                "content": {"application/json": {"example": []}},
                "model": AIModelGet,
            },
        },
    )
    @api_version(1, 0)
    async def get_ai_models(
        self,
        model_type: AIModelType | None = Query(None, alias="type"),
    ) -> list[dict[str, Any]]:
        """
        This endpoint allows users to retrieve all supported AI Models

        Args:
            model_type (str): Types of models to be retrieved

        Returns:
            list[dict[str, Any]]: List of all supported AIModels

        Raises:
            AtlasAPIException: If user does not have permissions to
                               retrieve all supported AI Models
        """

        # TODO: User access controls on the type of AI Models accessible

        if model_type is None:
            results = [model.model_dump() for model in self.nous.configs]

        else:
            results = [
                model.model_dump()
                for model in self.nous.configs
                if model.type == model_type
            ]

        return results

    @router.get(
        "/schemas/ai/llms/{llm_id}/",
        status_code=status.HTTP_200_OK,
        response_model=AIModelGet,
        include_in_schema=False,
    )
    @router.get(
        "/schemas/ai/llms/{llm_id}",
        status_code=status.HTTP_200_OK,
        response_model=AIModelGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved an AI Model that"
                "a user has access to",
                "content": {"application/json": {"example": []}},
                "model": AIModelGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_ai_model(self, llm_id: str) -> dict[str, Any]:
        """
        Retrieves full details of a supported AI Model

        Returns:
            dict[str, Any]: Full details of a supported AI Model
        """

        # TODO: User access controls on the type of AI Models accessible

        if llm_id not in self.nous.supported_models:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.message.api_schemas_ai_model_not_found_error_msg,
            )

        for m in self.nous.configs:  # noqa: RET503
            if m.id == llm_id:
                return m.model_dump()
