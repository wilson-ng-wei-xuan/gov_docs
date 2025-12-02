from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from atlas.genai import DEFAULT_SYSTEM_PROMPT

__all__ = (
    "PRODUCT_ID",
    "DATABASE_NAME",
    "DEFAULT_LLM_MODEL_ID",
    "DEFAULT_SYSTEM_PROMPT_TEMPLATE",
    "DEFAULT_SYSTEM_PROMPT_VARIABLES",
    "DEFAULT_CITATION_INSTRUCTIONS",
    "DEFAULT_AGENT_WELCOME_MESSAGE",
    "DEFAULT_RAG_PIPELINE_TYPE",
    "ACCEPTED_LLM_PARAMS",
    "DEFAULT_PLAYGROUND_AGENT",
)

PRODUCT_ID: str = "6126033d61c74773b7196f5b540bc25f"
DATABASE_NAME: str = "aibots"

DEFAULT_LLM_MODEL_ID: str = "azure~gpt-4o"
DEFAULT_SYSTEM_PROMPT_TEMPLATE: str = (
    "You are a personal AI assistant with the personality: ${personality}\n\n"
    "Your purpose is: ${instructions}\n\n"
    "You must abide by the following rules: ${guardrails}\n\n"
    "You have knowledge of the following information: ${knowledgeBase}"
)
DEFAULT_SYSTEM_PROMPT_VARIABLES: dict[str, str] = {
    "personality": "helpful, clever, and very friendly",
    "instructions": "You serve as a personal assistant to public officers "
    "in Singapore",
    "guardrails": "You will not answer politically sensitive topics",
    "knowledgeBase": "",
}
DEFAULT_CITATION_INSTRUCTIONS: str = (
    "If any of the knowledge sources above is referenced in your response, "
    "you must cite the source document of the referenced source. "
    "Include clickable hyperlinks to the sources if applicable "
    "(i.e. those starting with http)."
)

DEFAULT_AGENT_WELCOME_MESSAGE: str = (
    "Hello! I am your assistant. How can I help you?"
)
DEFAULT_RAG_PIPELINE_TYPE: str = "aibots"

ACCEPTED_LLM_PARAMS: list[str] = [
    "temperature",
    "max_tokens",
    "top_p",
    "frequency_penalty",
    "presence_penalty",
]

DEFAULT_PLAYGROUND_AGENT: dict[str, Any] = {
    "_id": "804885b4423e485cb21592c7dfa8baa8",
    "name": "Playground Bot",
    "description": "Remember me from LaunchPad? With me, you can try out "
    "different language models and settings. This chatbot "
    "does not contain any knowledge base or pre-set system "
    "prompts.",
    "agency": "govtech",
    "clone": None,
    "featured": True,
    "sharing": {
        "url_path": "the-playground-bot",
        "public_url": "https://aibots.gov.sg/chats/the-playground-bot",
        "api_url": "https://api.aibots.gov.sg/v1.0/chats/the-playground-bot",
        "api_keys": [],
    },
    "files": [],
    "welcome_message": DEFAULT_AGENT_WELCOME_MESSAGE,
    "templates": [],
    "release_state": {
        "state": "production",
        "created": datetime.now(timezone.utc),
        "last_modified": None,
        "last_modified_user": "b26e7d5eec9f58209fb4dafa610c6dd2",
        "comments": [],
        "denied": False,
    },
    "knowledge_bases": [],
    "default_pipeline": None,
    "rags": [],
    "chat": {
        "model": "azure~gpt-35-turbo",
        "system_prompt": {
            "template": "${system}\n${instructions}",
            "variables": {
                "system": DEFAULT_SYSTEM_PROMPT,
                "instructions": "",
            },
        },
    },
    "tools": [],
    "settings": {"botAvatar": "/img/default-bots-icon/playground-bot84px.png"},
    "ownership": {
        "resource_key": "agents.804885b4423e485cb21592c7dfa8baa8",
        "visibility": "wog",
        "access": {
            "owner": [
                {"id": "b26e7d5eec9f58209fb4dafa610c6dd2", "type": "user"},
                {"id": "ba28efd54f14516faa4665a5d6dcff67", "type": "user"},
                {"id": "c0fdd683da18554f89345f51186e13c3", "type": "user"},
                {"id": "3f611e84215e515fad7086e86607212a", "type": "user"},
            ],
            "admin": [
                {"id": "37f26e41f7ac545a81eec23e7e7d86e4", "type": "user"},
                {"id": "f1000071d7c950b8b547fe8246125aa1", "type": "user"},
            ],
            "editor": [],
            "user": [],
            "viewer": [],
        },
    },
    "meta": {
        "resource_type": "agents",
        "owner": "ba28efd54f14516faa4665a5d6dcff67",
        "owner_type": "user",
        "created": datetime.now(timezone.utc),
        "last_modified": None,
        "last_modified_user": None,
        "deleted": None,
        "deleted_user": None,
        "archived": None,
        "archived_user": None,
        "location": "https://aibots.gov.sg/latest/agents/804885b4423e485cb21592c7dfa8baa8",
        "version": 1,
    },
    "modifications": {
        "create": {
            "type": "create",
            "user_type": "user",
            "user": "ba28efd54f14516faa4665a5d6dcff67",
            "details": {},
            "timestamp": "2024-05-30T11:57:53.338010",
        }
    },
}

DEFAULT_INTERNAL_API_KEY: dict[str, Any] = {
    "meta": {
        "resource_type": "default",
        "owner": None,
        "owner_type": None,
        "location": None,
        "version": None,
        "created": "2024-09-11T08:05:16.720633Z",
        "last_modified": None,
        "last_modified_user": None,
        "deleted": None,
        "deleted_user": None,
        "archived": None,
        "archived_user": None,
    },
    "modifications": {},
    "name": "test",
    "description": "",
    "_id": "ab287e303655499aacfe919c4e690232",
    "issuer": "atlas",
    "type": "test",
    "scopes": [],
    "checksum": "971ca3fdf3",
    "key": "481f8d48c06e4659b838ba2954e970f1",
    "expiry": None,
}
