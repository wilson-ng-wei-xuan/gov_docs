from __future__ import annotations

import asyncio
import json
import re
import textwrap
from pathlib import Path
from types import SimpleNamespace
from typing import Any, AsyncGenerator

import httpx
import markdown
import structlog
from aibots.constants import (
    ACCEPTED_LLM_PARAMS,
    DEFAULT_CITATION_INSTRUCTIONS,
    DEFAULT_LLM_MODEL_ID,
    DEFAULT_PLAYGROUND_AGENT,
    DEFAULT_SYSTEM_PROMPT_TEMPLATE,
    DEFAULT_SYSTEM_PROMPT_VARIABLES,
)
from aibots.models import Chat, ChatFull, ChatMessage, RAGQuery
from aibots.rags import RAGEngine
from atlas.asgi.exceptions import AtlasAPIException
from atlas.asgi.schemas import APIGet, APIPostPut, AtlasASGIConfig, IDResponse
from atlas.beanie import BeanieDataset, BeanieService
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.genai import AtlasLLMException
from atlas.genai.schemas import (
    AtlasLLMInteractionBase,
    ChatInteractionStream,
    ModelID,
    PromptTemplate,
    Query,
    Tokens,
)
from atlas.httpx import HttpxService
from atlas.nous import NousService
from atlas.schemas import AtlasError, Email, UserLogin, Uuid
from atlas.services import ServiceManager
from atlas.structlog import StructLogService
from beanie.operators import In
from fastapi import APIRouter, Depends, Form, Response, status
from fastapi import Query as FastAPIQuery
from fastapi.responses import StreamingResponse
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import Json, StrictStr

from chats.environ import AIBotsChatEnviron
from chats.models import (
    AgentDB,
    ChatDB,
    ChatMessageDB,
    KnowledgeBaseDB,
    RAGConfigDB,
)

__doc__ = """
Contains all the API calls for the Chat API

Attributes:
    router (APIRouter): Chat API Router
"""


__all__ = ("router",)

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "prefix": "",
        "tags": ["Chats"],
        "dependencies": [
            Depends(AtlasDependencies.get_registry_item("reject_api_key"))
        ],
        "responses": {
            **AtlasRouters.response("401_authentication_error"),
            **AtlasRouters.response("403_permissions_error"),
            **AtlasRouters.response("500_internal_server_error"),
        },
    }
)


class AgentChatPost(APIPostPut):
    """
    POST representation for creating a Chat with a specific agent

    Attributes:
        name (StrictStr): Name of the Chat
        user_prompt (PromptTemplate): User prompt template value,
                                      defaults to default prompt
                                      template values
        system_prompt (PromptTemplate): System prompt template value,
                                        defaults to default AIBots
                                        system prompt values
        params (dict[str, Any]): AI Model parameters for the Chat,
                                 defaults to an empty dictionary
        properties (dict[str, Any]): Additional business properties
                                     for the Chat, defaults to an empty
                                     dictionary
        model (ModelID): AI Model ID
        pinned (bool): Indicate if the chat is to be pinned, defaults to
                       False
    """

    name: StrictStr = ""
    user_prompt: PromptTemplate = PromptTemplate()
    system_prompt: PromptTemplate = PromptTemplate(
        template=DEFAULT_SYSTEM_PROMPT_TEMPLATE,
        variables=DEFAULT_SYSTEM_PROMPT_VARIABLES,
    )
    params: dict[str, Any] = {}
    properties: dict[str, Any] = {}
    model: ModelID = ModelID(DEFAULT_LLM_MODEL_ID)
    pinned: bool = False


class ChatPut(APIPostPut):
    """
    PUT representation for updating a Chat

    Attributes:
        name (StrictStr | None): Name of the Chat, defaults
                                 to None
        user_prompt (PromptTemplate | None): User prompt
                                             template value,
                                             defaults to None
        system_prompt (PromptTemplate | None): System prompt
                                               template value,
                                               defaults to None
        params (dict[str, Any] | None): AI Model parameters for
                                        the Chat, defaults to None
        properties (dict[str, Any]  | None): Additional business
                                             properties for the Chat,
                                             defaults to None
        model (ModelID | None): AI Model ID, defaults to None
        pinned (bool | None): Indicate if the chat is to be pinned,
                              defaults to None
    """

    name: StrictStr | None = None
    user_prompt: PromptTemplate | None = None
    system_prompt: PromptTemplate | None = None
    params: dict[str, Any] | None = None
    properties: dict[str, Any] | None = None
    model: ModelID | None = None
    pinned: bool | None = None


class ChatGet(APIGet, Chat):
    """
    GET representation of a Chat conversation.

    Attributes:
        id (Uuid): UUID string
        name (StrictStr): Name field, defaults to an empty string
        user_prompt (Optional[PromptTemplate]): User prompt template, defaults to
                                                None
        modifications (ModificationDict): Modifications made to the Chat, inherited

        tokens (Tokens): Number of tokens cumulatively consumed, defaults to
                             default Tokens values
        model (ModelID): LLM model associated with Chat Message, inherited
        system_prompt (PromptTemplate): System prompt template, defaults
                                        to default Prompt Template values
        params (dict[str, Any]): AI Model parameters used to generate the Chat Message,
                                 inherited
        properties (dict[str, Any]): Additional properties used in the business logic,
                                     inherited
    """  # noqa: E501

    tokens: TokensGet


class ChatFullGet(APIGet, ChatFull):
    """
    GET representation of a full chat conversation with contextual messages.

    Attributes:
        id (Uuid): UUID string, inherited
        name (constr): Name field, only allows hexadecimal values,
                       hyphen and underscore, inherited
        user_prompt (Optional[PromptTemplate]): User prompt template, inherited
        modifications (ModificationDict): Modifications made to the Chat, inherited
        messages (list[ChatMessageGet]): Chat Messages associated with the conversation,
                                         defaults to an empty list

        tokens (Tokens): Number of tokens cumulatively consumed, inherited
        model (ModelID): LLM model associated with Chat Message, inherited
        system_prompt (PromptTemplate): System prompt template, defaults
                                        to default Prompt Template values
        params (dict[str, Any]): AI Model parameters used to generate the Chat Message,
                                 inherited
        properties (dict[str, Any]): Additional properties used in the business logic,
                                     inherited
    """  # noqa: E501

    tokens: TokensGet
    messages: list[ChatMessageGet] = []


class ChatMessagePut(APIPostPut):
    """
    PUT representation for updating a Chat Message

    Attributes:
        liked (bool | None): Indicates if the Chat Message is liked,
                             defaults to None
        pinned (bool | None): Indicates if the Chat Message is pinned,
                              defaults to None
    """

    liked: bool | None = None
    pinned: bool | None = None


class ChatMessageGet(APIGet, ChatMessage):
    """
    GET representation of a Chat Message

    Attributes:
        id (Uuid): UUID string, autogenerated
        chat (Uuid): UUID reference to the Chat, defaults to None
        query (ChatInteraction): Query to the LLM
        response (Optional[ChatInteraction]): Response from the LLM, defaults to
                                              None
        tokens (Tokens): Number of tokens consumed by the interaction, defaults to
                         default Tokens values
        model (ModelID): LLM model associated with Chat Message, inherited
        system_prompt (Optional[ChatInteraction]): System prompt template, defaults to
                                                   None
        params (dict[str, Any]): AI Model parameters used to generate the Chat Message,
                                 inherited
        properties (dict[str, Any]): Additional properties used in the business logic,
                                     inherited
        liked (bool): Indicates if the message has been liked, defaults to False
        pinned (bool): Indicates if the message has been pinned, defaults to False
    """  # noqa: E501

    tokens: TokensGet


class ChatInteractionStreamGet(APIGet, ChatInteractionStream):
    """
    GET Representation of a part of a streaming response from the LLM

    Attributes:
        role (str): Chat role [system, user, assistant, tool],
                    defaults to None
        content (str): Message content, defaults to None
        options (Optional[List[LLMContent]]): Additional options to be
                                              returned for the user to
                                              choose, defaults to None
    """


class TokensGet(APIGet, Tokens):
    """GET representation of the number of tokens consumed by the
    Chat Message

        Attributes:
        query (Annotated[StrictInt]): Query token count, defaults to 0
        system_prompt (Annotated[StrictInt]): System Prompt token count,
                                              defaults to 0
        query_with_context (Annotated[StrictInt]): Query with context
                                                   token count, defaults
                                                   to 0
        response (Annotated[StrictInt]): Response token count, defaults to 0
    """


@cbv(router)
class ChatsAPI:
    """
    Class-based view for representing the Chats API

    Attributes:
        user (UserLogin): Authenticated user details
        atlas (AtlasConfig): Atlas Config class
        environ (AIBotsChatEnviron): Environment variables
        db (BeanieService): MongoDB Service
        chats (BeanieDataset): Chats Dataset
        chat_messages (BeanieDataset): ChatMessages Dataset
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
            **self.environ.messages["chats"]
        )
        self.db: BeanieService = self.atlas.db
        self.chats: BeanieDataset = self.db.atlas_dataset(ChatDB.Settings.name)
        self.chat_messages: BeanieDataset = self.db.atlas_dataset(
            ChatMessageDB.Settings.name
        )
        self.agents: BeanieDataset = self.db.atlas_dataset(
            AgentDB.Settings.name
        )
        self.knowledge_bases: BeanieDataset = self.db.atlas_dataset(
            KnowledgeBaseDB.Settings.name
        )
        self.rag_configs: BeanieDataset = self.db.atlas_dataset(
            RAGConfigDB.Settings.name
        )
        self.rag: ServiceManager = self.atlas.services.get("rag")
        self.nous: NousService = self.atlas.services.get("nous")
        self.rest: HttpxService = self.atlas.rest
        self.logger: StructLogService = self.atlas.logger

    def generate_email_from_chat(self, chat: ChatDB) -> Email:
        """
        Structures the chat as an email

        Args:
            chat (ChatDB): Contextual Chat database

        Returns:
            Email: Email structure to be sent
        """

        def add_style_to_raw_html_table(html: str):
            return (
                html.replace(
                    "<table>", "<table cellspacing='3' cellpadding='3'>"
                )
                .replace(
                    "<th>",
                    "<th style='background-color: #3B3E50; color: #ffffff'>",
                )
                .replace("<td>", "<td style='background-color: #ffffff'>")
            )

        def find_placeholders_in_text(
            org_str: str, pattern="{{([a-zA-Z0-9_-]+)}}"
        ) -> list[str]:
            """
            File all placeholders {{*}} in a string.
            """
            return re.findall(pattern, org_str)

        def replace_all_substrings(text: str, dic: dict[str, str]) -> str:
            """
            Replace all placeholders in the text
            Args:
                text: original text
                dic: Dictionary with key=old-substring value=new-substring
            Return:
                Updated text
            """
            for old_str, new_str in dic.items():
                text = text.replace(old_str, new_str)
            return text

        def find_and_replace_placeholders(
            text: str, replacements: dict[str, str]
        ) -> str:
            """
            Replace placeholders marked within {{}}
            """
            placeholders = find_placeholders_in_text(
                text, pattern="{{([a-zA-Z0-9_-]+)}}"
            )
            dic = {f"{{{{{k}}}}}": replacements[k] for k in placeholders}
            return replace_all_substrings(text, dic)

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        auth: dict[str, Any] = json.loads(self.environ.emails_api.auth)

        email_job = Email.model_construct(
            to=[self.user.email],
            sender=auth["SMTP_FROM"],
            subject="Your conversation on AIBots",
        )

        # The email body for recipients with non-HTML email clients.
        email_job.text = "\n\n".join(
            [
                f"You:\n\n+{msg.query.content}"
                + f"AI:\n\n+{msg.response.content}"
                for msg in chat.messages
            ]
        )
        template_folder = Path.cwd() / "chats/email_templates"

        logger.info("Email template folder: %s", template_folder)

        logger.info(
            "Reading email_header.html template: %s",
            str(template_folder / "email_header.html"),
        )

        header_html = (template_folder / "email_header.html").read_text()

        logger.info("Retrieved email_header.html template: %s", header_html)

        user_html = (template_folder / "user_template.html").read_text()
        ai_html = (template_folder / "ai_template.html").read_text()
        footer_html = (template_folder / "email_footer.html").read_text()

        email_job.html = header_html

        logger.info("Assembling email from templates")

        for msg in chat.messages:
            email_job.html += find_and_replace_placeholders(
                user_html,
                {
                    "email": self.user.email,
                    "prompt": add_style_to_raw_html_table(
                        markdown.markdown(
                            msg.query.content, extensions=["tables"]
                        )
                    ),
                },
            )

            email_job.html += find_and_replace_placeholders(
                ai_html,
                {
                    "response": add_style_to_raw_html_table(
                        markdown.markdown(
                            msg.response.content, extensions=["tables"]
                        )
                    )
                },
            )
        email_job.html += find_and_replace_placeholders(
            footer_html,
            {"domain": auth["SMTP_FROM"].split("@")[1]},
        )

        logger.info("Assembled email: %s", email_job.model_dump_json())

        return email_job

    @staticmethod
    def censor_pii(text: str) -> str:
        """
        Basic PII censoring that only
        replaces emails and NRICs

        Args:
            content (str): Content to be redacted

        Returns:
            str: Content with PII redacted
        """
        emails = re.findall(r"[\w\.-]+@[\w\.-]+", text)
        nrics = re.findall(r"(?i)[STFG]\d{7}[A-Z]", text)

        output = text
        if emails:
            output = re.sub("|".join(emails), "<EMAIL>", output)
        if nrics:
            output = re.sub("|".join(nrics), "<NRIC>", output)

        return output

    async def cloak_pii(
        self, content: str, score_threshold: float = 0.3
    ) -> str:
        """
        Redacts PII from the content using Cloak API

        Args:
            content (str): Content to be redacted

        Returns:
            str: Content with PII redacted
        """
        # TODO: Refactor Cloak into a seperate service
        # TODO: Load endpoint, cloak_id, cloak_apikey from envvar

        CLOAK_BASE_URL = "https://api.cloak.gov.sg"

        cloak_id = "CLOAK_PROD_ID"
        cloak_apikey = "CLOAK_PROD_APIKEY"

        url = f"{CLOAK_BASE_URL}/prod/L3/transform"
        headers = {"Authorization": f"ENCRYPT-AUTH {cloak_id}:{cloak_apikey}"}
        payload = {
            "text": content,
            "language": "en",
            "score_threshold": score_threshold,
            "entities": [
                "SG_NRIC_FIN",
                "SG_ADDRESS",
                "CREDIT_CARD",
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "SG_BANK_ACCOUNT_NUMBER",
                "IBAN_CODE",
                "IP_ADDRESS",
                "SG_UEN",
            ],
            "anonymizers": {
                "SG_NRIC_FIN": {
                    "type": "replace",
                    "new_value": "<SG_NRIC_FIN>",
                },
                "SG_ADDRESS": {"type": "replace", "new_value": "<SG_ADDRESS>"},
                "CREDIT_CARD": {
                    "type": "replace",
                    "new_value": "<CREDIT_CARD>",
                },
                "PHONE_NUMBER": {
                    "type": "mask",
                    "masking_char": "*",
                    "chars_to_mask": 4,
                    "from_end": False,
                },
                "EMAIL_ADDRESS": {
                    "type": "replace",
                    "new_value": "<EMAIL_ADDRESS>",
                },
                "SG_BANK_ACCOUNT_NUMBER": {
                    "type": "replace",
                    "new_value": "<SG_BANK_ACCOUNT_NUMBER>",
                },
                "IBAN_CODE": {
                    "type": "replace",
                    "new_value": "<IBAN_CODE>",
                },
                "IP_ADDRESS": {
                    "type": "replace",
                    "new_value": "<IP_ADDRESS>",
                },
                "SG_UEN": {
                    "type": "replace",
                    "new_value": "<SG_UEN>",
                },
            },
        }

        try:
            resp: httpx.Response = await self.rest.post(
                url, headers=headers, json=payload, timeout=30
            )

            resp_json: dict = resp.json()

            if resp_json.get("text"):
                return resp_json.get("text")

        except Exception as e:
            logger: structlog.typing.FilteringBoundLogger = (
                self.logger.get_structlog_logger(self.environ.loggers["api"])
            )
            logger.exception(e)

            # Failsafe (basic censorship of PII)
            # if Cloak API fails to return valid response
            return ChatsAPI.censor_pii(content)

    async def generate_title(
        self, content: str, max_length: int = 50, suffix="..."
    ) -> str:
        """
        Generates a chat title based on the query text
        contents <= max_length will be converted to title case
        contents > max_length will have title generated by
                the default LLM (gpt-35-turbo)
        Any LLM generation error will fallback to returning first
        max_length chars of query text in title case

        Args:
            content (str): Query content to be sent

        Returns:
            str: Generated title for the query

        """

        if not content:
            return ""

        if len(content) <= max_length:
            return content.title()

        try:
            title_response: Query = await self.nous.atlas_achat(
                query=self.nous.atlas_generate_query(
                    interaction=self.nous.atlas_generate_chat_interaction(
                        prompt=f"Generate a short title to describe the\
                                following query prompt:\n{content}\n\nTitle:\n"
                    ),
                    llm_base=AtlasLLMInteractionBase(
                        model="azure~gpt-35-turbo",
                        system_prompt={
                            "template": "",
                            "variables": {},
                        },
                        params={
                            "temperature": 0,
                            "max_tokens": 25,
                        },
                        properties={},
                    ),
                )
            )
            return (
                title_response.response_content
                or textwrap.shorten(
                    content, width=max_length, placeholder=suffix
                ).title()
            )
        except Exception as e:
            logger: structlog.typing.FilteringBoundLogger = (
                self.logger.get_structlog_logger(self.environ.loggers["api"])
            )
            logger.exception(str(e))
            return textwrap.shorten(
                content, width=max_length, placeholder=suffix
            ).title()

    async def atlas_get_chat_messages(
        self, chat_id: Uuid, messages: list[Uuid] | None = None
    ) -> list[ChatMessageDB]:
        """
        Retrieves all the chat messages associated with a Chat

        Args:
            chat_id (Uuid): ID of the Chat
            messages (list[Uuid] | None): List of chat messages,
                                          defaults to None

        Returns:
            list[ChatMessageDB]: List of Chat Messages
        """
        query_filters: list[Any] = [ChatMessageDB.chat == chat_id]
        if messages:
            query_filters.append(In(ChatMessageDB.id, messages))
        return await self.chat_messages.get_items(
            *query_filters, sort=[(ChatMessageDB.query.timestamp, 1)]
        )

    async def atlas_get_chat(
        self, chat_id: Uuid, messages: bool = True
    ) -> ChatDB:
        """
        Convenience function for retrieving the chat,
        includes a messages flag to indicate if messages
        are to be retrieved

        Args:
            chat_id (Uuid): Chat Uuid
            messages (bool): Indicates if Chat messages
                             are to be included

        Returns:
            ChatDB: Chat retrieved

        Raises:
            AtlasAPIException: If Chat does not exist
        """

        # Retrieve Chat and check if it exists
        chat: ChatDB | None = await self.chats.get_item(
            ChatDB.id == chat_id,
            ChatDB.meta.owner == self.user.id,
            ChatDB.meta.deleted == None,  # noqa: E711
        )
        if not chat:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_not_found_msg,
                details={"id": chat_id},
            )

        # Retrieve all associated chat messages in sorted order
        if messages:
            chat.messages = await self.atlas_get_chat_messages(
                chat_id, messages=chat.messages
            )

        return chat

    async def atlas_get_agent(self, agent_id: Uuid) -> AgentDB:
        """
        Convenience function for retrieving and checking if
        an Agent exists

        Args:
            agent_id (Uuid): ID of the Agent

        Returns:
            AgentDB: Agent retrieved

        Raises:
            AtlasAPIException: If Agent does not exist
        """
        # Check that all agents are valid
        agent: AgentDB | None = await self.agents.get_item_by_id(agent_id)
        if agent is None:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_agent_not_found_msg,
                details={"id": agent_id},
            )
        return agent

    @router.post(
        "/chats/",
        response_model=IDResponse,
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        include_in_schema=False,
    )
    @router.post(
        "/chats",
        response_model=IDResponse,
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_multiagent_chat(
        self,
        chat_details: AgentChatPost,
    ) -> dict[str, str]:
        """
        Create a new Chat with a single Agent or multiple Agents
        Single agents can be specified using the path or payload
        Multiple agents only be specified using the payload

        Args:
            chat_details (AgentChatPost): Details of the Chat

        Returns:
            dict[str, str]: ID of the Chat

        Raises:
            AtlasAPIException: If user does not have permissions to
                               access selected AI Model
        """

    @router.get(
        "/chats/",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatGet],
        include_in_schema=False,
    )
    @router.get(
        "/chats",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all a User's Chats",
                "content": {"application/json": {"example": []}},
                "model": list[ChatGet],
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_chats(self) -> list[dict[str, Any]]:
        """
        Retrieves all the chats associated with the user

        Returns:
            list[dict[str, Any]]: List of all chats
        """
        # Retrieve and return a user's chats
        # Note: Retrieve only user's chats from modifications dictionary
        return [
            i.model_dump(exclude={"messages"})
            for i in await self.chats.get_items(
                ChatDB.meta.owner == self.user.id,
                ChatDB.meta.deleted == None,  # noqa: E711
            )
        ]

    @router.delete(
        "/chats/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/chats",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_chats(
        self, ids: list[Uuid], response: Response
    ) -> Response:
        """
        Retrieves all the chats associated with the user

        Args:
            ids (list[Uuid]): IDs of Chats to be deleted
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If duplicate IDs are found in deletion list
            AtlasAPIException: If some of the Chats could not be retrieved
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )
        # Check for repeated IDs in deletion list
        if len(ids) != len(set(ids)):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_chat_delete_duplicate_id_msg,
                details={"ids": ids},
            )

        # Retrieve all Chats
        chats: list[ChatDB] = await self.chats.get_items(
            In(ChatDB.id, ids),
            ChatDB.meta.owner == self.user.id,
            ChatDB.meta.deleted == None,  # noqa: E711
        )

        # Raise error if some of the Chats could not be retrieved
        if len(chats) != len(ids):
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_delete_missing_error_msg,
                details={"ids": ids},
            )

        # Update their modification status using the delete_schema function
        for chat in chats:
            chat.delete_schema(user=self.user.id)

        # Update in DB
        await logger.ainfo(
            self.messages.api_chats_chat_delete_fmt.format(
                [c.id for c in chats]
            ),
        )
        if not await self.chats.update_items(*chats):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_delete_fmt.format(
                    [chat.id for chat in chats]
                ),
                details={"ids": ids},
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.post(
        "/chats/{agent_id}/",
        response_model=IDResponse,
        include_in_schema=False,
    )
    @router.post(
        "/chats/{agent_id}",
        response_model=IDResponse,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
        },
    )
    @api_version(1, 0)
    async def create_chat(
        self,
        chat_details: AgentChatPost,
        agent_id: Uuid = DEFAULT_PLAYGROUND_AGENT.get("_id"),
    ) -> dict[str, str]:
        """
        Create a new Chat with a single Agent.

        Args:
            chat_details (AgentChatPost): Details of the Chat
            agent_id (Uuid | None, optional): ID of the Agent.
                                           Defaults to None.

        Returns:
            dict[str, str]: ID of the Chat

        Raises:
            AtlasAPIException: Invalid AI Parameters
            AtlasAPIException: If user does not have permissions to
                               access selected AI Model
            AtlasAPIException: If errors occur during chat creation
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Validate params only contains valid keys
        if chat_details.params and not all(
            key in ACCEPTED_LLM_PARAMS for key in chat_details.params
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_invalid_params_msg,
                details=chat_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            )

        # TODO: Check if user has permissions to access selected
        #       AI Model (V2.0)
        # TODO: Check if AI param values are supported by AI Model

        await self.atlas_get_agent(agent_id)

        # TODO: Check if user has permission to access selected Agents

        # Create Chat
        uid: Uuid = ChatDB.atlas_get_uuid()
        chat: ChatDB = ChatDB.create_schema(
            user=self.user.id,
            resource_type=ChatDB.Settings.name,
            uid=uid,
            location=str(self.environ.project.pub_url) + f"v1.0/chats/{uid}",
            version=1,
            **{**chat_details.model_dump(), "agents": [agent_id]},
        )
        await logger.ainfo(
            self.messages.api_chats_chat_create_msg,
            data=chat.model_dump_json(),
        )

        # Insert Chat into DB
        if not await self.chats.create_item(chat):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_create_error_msg,
                details=chat.model_dump(exclude_unset=True, mode="json"),
            )

        # Return ID response
        return {"id": chat.id}

    @router.put(
        "/chats/{chat_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/chats/{chat_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_chat(
        self, chat_id: Uuid, chat_details: ChatPut, response: Response
    ) -> Response:
        """
        Updates the chat details

        Args:
            chat_id (Uuid): ID of the Chat
            chat_details (ChatPut): Details to update chat with
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If LLM parameters are invalid
            AtlasAPIException: If the Chat does not exist
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # TODO: Use LLM model params to perform the validation
        # Validate params only contains valid keys
        if chat_details.params and not all(
            key in ACCEPTED_LLM_PARAMS for key in chat_details.params
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_invalid_params_msg,
                details={"params": chat_details.params},
            )

        # Check that edits were made
        if not chat_details.model_dump(exclude_unset=True):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_chat_no_updates_msg,
                details={"id": chat_id},
            )

        # Retrieve and check if Chat exists
        chat: ChatDB = await self.atlas_get_chat(chat_id, messages=False)

        # TODO: Check if user can access selected AI Model (V2.0)
        # TODO: If AI param values were changed, check if they are supported by
        #  AI Model

        # Update Chat using the update_schema function
        updated: ChatDB = chat.update_schema(
            user=self.user.id,
            version=chat.meta.version + 1,
            **chat_details.model_dump(exclude_unset=True),
        )

        # Replace in database
        logger.info(
            self.messages.api_chats_chat_update_fmt.format(chat_id),
            data=updated.model_dump_json(),
        )
        if not await self.chats.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_update_error_fmt.format(
                    chat_id
                ),
                details=chat_details.model_dump(
                    exclude_unset=True, mode="json"
                ),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/chats/{chat_id}/",
        status_code=status.HTTP_200_OK,
        response_model=ChatFullGet,
        include_in_schema=False,
    )
    @router.get(
        "/chats/{chat_id}",
        status_code=status.HTTP_200_OK,
        response_model=ChatFullGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved a Chat",
                "content": {"application/json": {"example": {}}},
                "model": ChatFullGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_chat(self, chat_id: Uuid) -> dict[str, Any]:
        """
        Retrieves a Chat

        Args:
            chat_id (Uuid): ID of the Chat

        Returns:
            dict[str, Any]: Chat retrieved

        Raises:
            AtlasAPIException: If the Chat does not exist
        """
        # Retrieve Chat and check if it exists
        chat: ChatDB = await self.atlas_get_chat(chat_id)
        return chat.model_dump()

    @router.delete(
        "/chats/{chat_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/chats/{chat_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_chat(self, chat_id: Uuid, response: Response) -> Response:
        """
        Deletes a Chat

        Args:
            chat_id (Uuid): ID of the Chat
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If the Chat does not exist
        """

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Retrieve Chat and check if it exists
        chat_item: ChatDB = await self.atlas_get_chat(chat_id, messages=False)

        # Delete the chat
        chat_item.delete_schema(user=self.user.id)
        logger.info(
            self.messages.api_chats_chat_delete_fmt.format(chat_item.id),
        )
        if not await self.chats.replace_item(chat_item):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_delete_fmt.format(
                    chat_item.id
                ),
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/chats/{chat_id}/email/",
        status_code=status.HTTP_202_ACCEPTED,
        include_in_schema=False,
    )
    @router.get(
        "/chats/{chat_id}/email",
        status_code=status.HTTP_202_ACCEPTED,
        responses={
            status.HTTP_202_ACCEPTED: {
                "description": "Successfully processed email request"
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_chat_email(
        self, chat_id: Uuid, response: Response
    ) -> Response:
        """
        Retrieves a Chat

        Args:
            chat_id (Uuid): ID of the Chat
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If the Chat does not exist
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        chat: ChatDB = await self.atlas_get_chat(chat_id)

        # Transform chat into email
        email: Email = self.generate_email_from_chat(chat)

        # Reference aibots/app/api/email_otps.py on email sending functionality
        await logger.ainfo(
            self.messages.api_chats_send_email_fmt.format(chat_id, email.to)
        )
        if self.environ.use_aws:
            auth: dict[str, Any] = json.loads(self.environ.emails_api.auth)
            email.sender = auth["SMTP_FROM"]
            email_body: dict[str, Any] = {
                **email.model_dump(),
                "smtp_key": auth,
                "sender_name": self.environ.email.name,
            }
            resp: httpx.Response = await self.rest.post(
                str(self.environ.emails_api.url),
                content=json.dumps(email_body).encode("utf-8"),
            )
            try:
                resp.raise_for_status()
            except (httpx.HTTPError, httpx.StreamError):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Error when sending email login via Email ",
                    details=await resp.json(),
                ) from None
        else:
            auth: dict[str, Any] = json.loads(self.environ.emails_api.auth)
            email.sender = auth["SMTP_FROM"]
            self.atlas.emails.atlas_send_email(email=email)

        response.status_code = status.HTTP_202_ACCEPTED
        return response

    async def atlas_update_response(
        self,
        chat: ChatDB,
        query: ChatMessageDB,
        logger: Any = None,
    ) -> None:
        """
        Updates the chat response

        Args:
            chat (ChatDB): Chat details
            query (ChatMessageDB): Chat Message details
            logger (Any): Logger for logging details, defaults to None

        Returns:
            None
        """
        chat: ChatDB = self.nous.atlas_update_response(
            user=self.user.id,
            query=query.id,
            context=chat,
            updated_tokens=query.tokens,
        )

        # Update Chat and Chat Message
        if not await self.chats.replace_item(chat):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_message_create_error_msg,
            )
        if logger:
            await logger.ainfo(
                self.messages.api_chats_chat_message_create_msg,
                data=query.model_dump_json(),
            )
        if not await self.chat_messages.create_item(query):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_message_create_error_msg,
            )

    @router.post(
        "/chats/{chat_id}/messages/",
        response_model=ChatMessageGet,
        include_in_schema=False,
    )
    @router.post(
        "/chats/{chat_id}/messages",
        response_model=ChatMessageGet,
        responses={
            **AtlasRouters.response("created_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
            **AtlasRouters.response("415_unsupported_media_type_error"),
            **AtlasRouters.response("422_invalid_creation_error"),
            # **AtlasRouters.response("429_rate_limit_error"),
        },
    )
    @api_version(1, 0)
    async def create_chat_message(
        self,
        chat_id: Uuid,
        content: str = Form(),
        params: Json = Form({}),
        properties: Json = Form({}),
        streaming: bool = FastAPIQuery(False),
        cloak: bool = FastAPIQuery(False),
        pipeline: Uuid | None = FastAPIQuery(None),
    ) -> StreamingResponse | dict[str, Any]:
        """
        Create a new Chat Message

        Args:
            chat_id (Uuid): ID of the Chat
            content (str): Chat Message content
            params (Json): Params field
            properties (Json): Additional business properties for
                               creating a chat message, defaults to
                               an empty dictionary
            streaming (bool): Indicates if response is to be streamed,
                              defaults to False
            cloak (bool): Indicates if Cloak should be used to censure
                          PII, defaults to True
            pipeline (Uuid | None): RAG pipeline to be queried

        Returns:
            StreamingResponse | dict[str, Any]: ID of the Chat Message

        Raises:
            AtlasAPIException: If the Chat does not exist
            AtlasAPIException: If the AI Model does not support streaming
        """

        async def stream_generator(
            subscription: AsyncGenerator[ChatInteractionStream | Query],
            p_chat: ChatDB,
            p_query: ChatMessageDB,
            p_title_task: asyncio.Task[str] | None = None,
            logger: Any = None,
        ) -> AsyncGenerator[str]:
            try:
                async for chunk in subscription:
                    if isinstance(chunk, ChatInteractionStream):
                        yield (
                            ChatInteractionStreamGet(
                                **chunk.model_dump()
                            ).model_dump_json(
                                by_alias=True,
                                include={"role", "content", "finish_reason"},
                            )
                            + "\n"
                        )

                    elif isinstance(chunk, Query):
                        # TODO: refactor this in a better way
                        p_query: ChatMessageDB = ChatMessageDB(
                            **{
                                **chunk.model_dump(),
                                "rag": {
                                    **p_query.rag.model_dump(),
                                    "chunks": [
                                        c.model_dump(by_alias=True)
                                        for c in p_query.rag.chunks
                                    ],
                                },
                            }
                        )
                        if p_query.properties.get("citations"):
                            p_query.rag.get_citations(p_query.response_content)

                        yield (
                            ChatMessageGet(
                                **{
                                    **chunk.model_dump(),
                                    "rag": {
                                        **p_query.rag.model_dump(),
                                        "chunks": [
                                            c.model_dump(by_alias=True)
                                            for c in p_query.rag.chunks
                                        ],
                                    },
                                }
                            ).model_dump_json(by_alias=True)
                            + "\n"
                        )

                    else:
                        yield (
                            AtlasError(
                                message=self.messages.api_queries_unrecognised_stream_msg,
                                details={
                                    "body": str(chunk),
                                    "status_code": 500,
                                    "type": None,
                                    "params": None,
                                    "query": p_query.model_dump(
                                        exclude_unset=True, mode="json"
                                    ),
                                },
                            ).model_dump_json()
                            + "\n"
                        )
                        break

            except AtlasLLMException as exc:
                yield (
                    AtlasError(
                        message=exc.message,
                        details=exc.details,
                    ).model_dump_json()
                    + "\n"
                )

            finally:
                # Wait for title task to complete to update chat name
                if p_title_task:
                    if not p_title_task.done():
                        p_chat.name = await p_title_task
                    else:
                        p_chat.name = p_title_task.result()

                # Update chat and chat message
                await self.atlas_update_response(p_chat, p_query, logger)

        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        # Validate params only contains valid keys
        if params and not all(key in ACCEPTED_LLM_PARAMS for key in params):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_invalid_params_msg,
                details={"params": params},
            )

        # Check if the Chat exists
        # Note only fetch a user's chats using the modifications dictionary
        chat: ChatDB = await self.atlas_get_chat(chat_id)

        # Retrieve the first Agent chat config
        agent: AgentDB = await self.atlas_get_agent(chat.agents[0])
        if not agent.chat:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_agent_chat_config_not_found_msg,
                details={"id": agent.id},
            )

        # TODO: Check if the AI Model selected supports streaming if selected

        # TODO: Check if the Rate Limits have exceeded

        # Redact PII if cloak is enabled
        if cloak:
            content = ChatsAPI.censor_pii(content)
            # content = await self.cloak_pii(content)

        # Construct llm_base using hierarchy of defaults:
        # model < app < agent < chat < query properties
        llm_base: AtlasLLMInteractionBase = (
            AtlasLLMInteractionBase.model_construct(
                **{
                    **self.nous.defaults.model_dump(),
                    **self.environ.llm_defaults.model_dump(),
                    **agent.chat.model_dump(),
                    **chat.model_dump(
                        include={
                            "id",
                            "model",
                            "system_prompt",
                        },
                    ),
                    **{
                        "params": {
                            **agent.chat.params,
                            **chat.params,
                            **params,
                        },
                        "properties": {
                            **agent.chat.properties,
                            **chat.properties,
                            **properties,
                        },
                    },
                }
            )
        )

        # Playground Agent will not use RAG
        # Only query RAG if agent has knowledge bases and RAG configurations
        rag_query: RAGQuery = RAGQuery()
        if (
            agent.id != DEFAULT_PLAYGROUND_AGENT.get("_id")
            and agent.knowledge_bases
            and agent.rags
        ):
            # Query relevant chunks from the RAG engine in the order
            # declared by the RAG pipeline order declared
            knowledge_bases: list[
                KnowledgeBaseDB
            ] = await self.knowledge_bases.get_items(
                KnowledgeBaseDB.agent == agent.id
            )
            rag_configs: list[RAGConfigDB] = await self.rag_configs.get_items(
                RAGConfigDB.agent == agent.id
            )
            for rag in rag_configs:
                engine: RAGEngine = self.rag.get(rag.type)
                try:
                    chunks = await engine.atlas_aquery(
                        prompt=content,
                        agent=agent,
                        rag_config=rag,
                        knowledge_bases=knowledge_bases,
                    )
                    rag_query: RAGQuery = RAGQuery(
                        id=rag.id,
                        type=rag.type,
                        chunks=chunks,
                    )
                except Exception as e:
                    await logger.ainfo(
                        self.messages.api_chats_chat_message_rag_query_error_fmt.format(
                            e.__class__.__name__, str(e), agent.id, rag.type
                        )
                    )
                    continue

        # Append citation instructions if enabled
        citation_instructions = ""
        if llm_base.properties.get("citations"):
            citation_instructions = "\n" + DEFAULT_CITATION_INSTRUCTIONS

        # Append user custom instructions if enabled
        custom_instructions = ""
        if llm_base.properties.get("custom_instructions"):
            custom_instructions = (
                "/n/nAdditional Instructions:/n"
                + llm_base.properties["custom_instructions"]
            )

        # Create Chat Message
        prepared_query: ChatMessageDB = ChatMessageDB(
            **{
                "rag": rag_query,
                **self.nous.atlas_generate_query(
                    interaction=self.nous.atlas_generate_chat_interaction(
                        prompt=content
                    ),
                    llm_base=llm_base,
                    # Variables from agent config
                    personality=agent.chat.system_prompt.variables.get(
                        "personality",
                        DEFAULT_SYSTEM_PROMPT_VARIABLES.get("personality"),
                    ),
                    instructions=agent.chat.system_prompt.variables.get(
                        "instructions",
                        DEFAULT_SYSTEM_PROMPT_VARIABLES.get("instructions"),
                    )
                    + custom_instructions,
                    # Citation instructions appended after KB
                    knowledgeBase=rag_query.prepare_chunks()
                    + citation_instructions,
                ).model_dump(),
            }
        )

        # Generate chat name in parallel task if it's blank
        title_task: asyncio.Task | None = None
        if not chat.name:
            title_task = asyncio.create_task(
                self.generate_title(content=content)
            )

        # Send Streaming Chat Message
        if streaming:
            return StreamingResponse(
                stream_generator(
                    subscription=await self.nous.atlas_astreaming(
                        query=prepared_query, context=chat, logger=logger
                    ),
                    p_chat=chat,
                    p_query=prepared_query,
                    p_title_task=title_task,
                ),
                media_type="text/event-stream",
            )

        # Send Request-Response Chat Message
        try:
            query: ChatMessageDB = ChatMessageDB(
                **(
                    await self.nous.atlas_achat(
                        query=prepared_query,
                        context=chat,
                    )
                ).model_dump()
            )
            if query.properties.get("citations"):
                query.rag.get_citations(query.response_content)
        except AtlasLLMException as e:
            raise AtlasAPIException(
                status_code=e.status_code,
                message=e.message,
                details=e.details,
            ) from e

        # Wait for title task to complete to update chat name
        if title_task:
            if not title_task.done():
                chat.name = await title_task
            else:
                chat.name = title_task.result()

        # Updating the chat and query responses
        await self.atlas_update_response(chat, query, logger)

        # Return created chat message
        return query.model_dump()

    @router.get(
        "/chats/{chat_id}/messages/",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatMessageGet],
        include_in_schema=False,
    )
    @router.get(
        "/chats/{chat_id}/messages",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatMessageGet],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved all Chat Messages "
                "in a Chat",
                "content": {"application/json": {"example": []}},
                "model": list[ChatMessageGet],
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_chat_messages(self, chat_id: Uuid) -> list[dict[str, Any]]:
        """
        Retrieves all the Chat Messages associated with a Chat

        Args:
            chat_id (Uuid): ID of the Chat

        Returns:
            list[dict[str, Any]]: List of all Chat Messages

        Raises:
            AtlasAPIException: If Chat does not exist
        """
        # Check if chat exists
        chat: ChatDB = await self.atlas_get_chat(chat_id)
        return [m.model_dump() for m in chat.messages]

    @router.delete(
        "/chats/{chat_id}/messages/",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatMessageGet],
        include_in_schema=False,
    )
    @router.delete(
        "/chats/{chat_id}/messages",
        status_code=status.HTTP_200_OK,
        response_model=list[ChatMessageGet],
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_chat_messages(
        self, chat_id: Uuid, ids: list[Uuid], response: Response
    ) -> Response:
        """
        Deletes Chat Messages associated with a Chat

        Args:
            chat_id (Uuid): ID of the Chat
            ids (list[Uuid]): IDs of Chat Messages to be deleted
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If Chat does not exist
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        chat: ChatDB = await self.atlas_get_chat(chat_id, messages=False)

        # Check if all the Chat Messages exist in the Chat
        if invalid_messages := set(ids) - {
            m.id if isinstance(m, ChatMessage) else m for m in chat.messages
        }:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_message_not_found_msg,
                details={"ids": invalid_messages},
            )

        # Convert list to all UUIDs
        messages_uuids = [
            m.id if isinstance(m, ChatMessage) else m for m in chat.messages
        ]

        # Remove all specified Chat Messages from the Chat
        chat.messages = [m for m in messages_uuids if m not in ids]

        # Auto delete chat if no more messages
        if not chat.messages:
            chat.delete_schema(user=self.user.id)

            # Update in DB
            await logger.ainfo(
                self.messages.api_chats_chat_delete_fmt.format(chat.id),
                data={"id": chat.id},
            )

        # Update Chat in the DB
        await logger.ainfo(
            self.messages.api_chats_chat_message_update_chat_fmt.format(
                ids, chat.id
            ),
            data=chat.model_dump_json(),
        )
        if not await self.chats.replace_item(chat):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_update_error_msg,
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.put(
        "/chats/{chat_id}/messages/{chat_message_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.put(
        "/chats/{chat_id}/messages/{chat_message_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("updated_response"),
            **AtlasRouters.response("400_invalid_parameters_error"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def update_chat_message(
        self,
        chat_id: Uuid,
        chat_message_id: Uuid,
        chat_message_details: ChatMessagePut,
        response: Response,
    ) -> Response:
        """
        Updates the Chat Message details

        Args:
            chat_id (Uuid): ID of the Chat
            chat_message_id (Uuid): ID of the Chat message
            chat_message_details (ChatMessagePut): Details to update
                                                   message with
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If no edits were made
            AtlasAPIException: If the Chat does not exist
            AtlasAPIException: If the Chat Message does not exist
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        try:
            chat_message: ChatMessageDB = (
                await self.atlas_get_chat_messages(
                    chat_id, messages=[chat_message_id]
                )
            )[0]
        except IndexError:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_message_not_found_msg,
                details=chat_message_details.model_dump(
                    mode="json", exclude_unset=True
                ),
            ) from None

        # Check that edits were made
        if not chat_message_details.model_dump(exclude_unset=True):
            raise AtlasAPIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=self.messages.api_chats_chat_message_no_updates_msg,
                details={"id": chat_message_id},
            )

        updated: ChatMessageDB = chat_message.model_copy(
            update=chat_message_details.model_dump(exclude_unset=True)
        )

        await logger.ainfo(
            self.messages.api_chats_chat_message_update_fmt.format(chat_id),
            data=updated.model_dump_json(),
        )
        if not self.chat_messages.replace_item(updated):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_message_update_error_msg,
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response

    @router.get(
        "/chats/{chat_id}/messages/{chat_message_id}/",
        status_code=status.HTTP_200_OK,
        response_model=ChatMessageGet,
        include_in_schema=False,
    )
    @router.get(
        "/chats/{chat_id}/messages/{chat_message_id}",
        status_code=status.HTTP_200_OK,
        response_model=ChatMessageGet,
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved a Chat Message",
                "content": {"application/json": {"example": {}}},
                "model": ChatMessageGet,
            },
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def get_chat_message(
        self, chat_id: Uuid, chat_message_id: Uuid
    ) -> dict[str, Any]:
        """
        Retrieved a Chat Message

        Args:
            chat_id (Uuid): ID of the Chat
            chat_message_id (Uuid): ID of the Chat Message

        Returns:
            dict[str, Any]: Chat Message retrieved

        Raises:
            AtlasAPIException: If the Chat does not exist
            AtlasAPIException: If the Chat Message does not exist
        """
        chat: ChatDB = await self.atlas_get_chat(chat_id)

        # Retrieve Chat Message ID from Chat and check if it exists
        if chat_message_id not in [m.id for m in chat.messages]:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_message_not_found_msg,
                details={"id": chat_message_id},
            )

        # Return Chat Message
        return (
            await self.atlas_get_chat_messages(
                chat_id, messages=[chat_message_id]
            )
        )[0].model_dump()

    @router.delete(
        "/chats/{chat_id}/messages/{chat_message_id}/",
        status_code=status.HTTP_204_NO_CONTENT,
        include_in_schema=False,
    )
    @router.delete(
        "/chats/{chat_id}/messages/{chat_message_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={
            **AtlasRouters.response("deleted_response"),
            **AtlasRouters.response("404_not_found_error"),
        },
    )
    @api_version(1, 0)
    async def delete_chat_message(
        self, chat_id: Uuid, chat_message_id: Uuid, response: Response
    ) -> Response:
        """
        Deletes a Chat Message

        Args:
            chat_id (Uuid): ID of the Chat
            chat_message_id (Uuid): ID of the Chat Message
            response (Response): FastAPI Response

        Returns:
            Response: FastAPI Response

        Raises:
            AtlasAPIException: If the Chat does not exist
            AtlasAPIException: If the Chat Message does not exist
        """
        logger: structlog.typing.FilteringBoundLogger = (
            self.logger.get_structlog_logger(self.environ.loggers["api"])
        )

        chat: ChatDB = await self.atlas_get_chat(chat_id, messages=False)

        if chat_message_id not in [
            m.id if isinstance(m, ChatMessage) else m for m in chat.messages
        ]:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message=self.messages.api_chats_chat_message_not_found_msg,
                details={"id": chat_message_id},
            )

        # Remove specified Chat Messages from the Chat
        chat.messages.remove(chat_message_id)

        # Auto delete chat if no more messages
        if not chat.messages:
            chat.delete_schema(user=self.user.id)

            # Update in DB
            await logger.ainfo(
                self.messages.api_chats_chat_delete_fmt.format(chat.id),
                data={"id": chat.id},
            )

        # Update Chat in the DB
        await logger.ainfo(
            self.messages.api_chats_chat_message_update_chat_fmt.format(
                [chat_message_id], chat.id
            ),
            data=chat.model_dump_json(),
        )
        if not await self.chats.replace_item(chat):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=self.messages.api_chats_chat_update_error_msg,
            )

        response.status_code = status.HTTP_204_NO_CONTENT
        return response
