from logging import Filter, Logger, LogRecord, getLogger

from atlas.asgi.schemas import LS, AtlasMiddlewareConfig, AtlasProcessorConfig
from atlas.fastapi import AtlasApp, AtlasRouters
from chats.app.api import routers
from chats.app.lifespans import (
    aws_lifespan,
    init_cdn_lifespan,
    llms_lifespan,
    primary_db_lifespan,
    rags_lifespan,
)
from chats.app.services import service_registry
from chats.environ import AIBotsChatEnviron, get_environ
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

__all__ = ["create_app"]


class EndpointFilter(Filter):
    def filter(self, record: LogRecord) -> bool:
        return record.getMessage().find("GET /heartbeat ") == -1


def create_app(
    lifespans: LS | None = None,
    middlewares: list[AtlasMiddlewareConfig] | None = None,
) -> FastAPI:
    """
    Creates the AIBots app

    Args:
        lifespans (
            Callable[[FastAPI], AsyncContextManager[None]] | None
        ): Default lifespans functions, defaults to None
        middlewares (list[AtlasMiddlewareConfig] | None): List of middlewares,
                                                     defaults to None

    Returns:

    """  # noqa: E501

    if lifespans is None:
        lifespans = []
    lifespans.extend(
        [
            aws_lifespan,
            primary_db_lifespan,
            init_cdn_lifespan,
        ]
    )

    if middlewares is None:
        middlewares = [
            AtlasMiddlewareConfig(
                middleware=CORSMiddleware,
                kwargs={
                    "allow_origins": ["*"],
                    "allow_credentials": True,
                    "allow_methods": ["*"],
                    "allow_headers": ["*"],
                },
            )
        ]

    environ: AIBotsChatEnviron = get_environ()
    logger: Logger = getLogger(environ.loggers["base"])
    atlas: AtlasApp = AtlasApp()
    app: FastAPI = atlas.create_app(
        *(
            AtlasProcessorConfig(
                processor="add_environ", kwargs={"environ": environ}
            ),
            AtlasProcessorConfig(
                processor="add_service_registry",
                kwargs={"services": service_registry},
            ),
            AtlasProcessorConfig(
                processor="add_service_from_registry",
                kwargs={"service_name": "executor", "max_workers": 1000},
            ),
            AtlasProcessorConfig(
                processor="add_service_from_registry",
                kwargs={
                    "service_name": "httpx",
                    "service_key": "rest",
                    "verify": False,
                    "timeout": 5.0,
                },
            ),
            AtlasProcessorConfig(
                processor="add_email_service", kwargs={"email": environ.email}
            ),
            AtlasProcessorConfig(
                processor="add_routers", kwargs={"routers": routers}
            ),
            AtlasProcessorConfig(
                processor="add_middlewares",
                kwargs={"middlewares": middlewares},
            ),
            AtlasProcessorConfig(
                processor="add_lifespans",
                kwargs={"lifespans": lifespans},
            ),
            AtlasProcessorConfig(
                processor="add_jwt_auth", kwargs={"secret": environ.jwt}
            ),
            # TODO: Until we have a processor hook to add initial data
            #   we have to break up the initialisation into a 2-step
            #   process
            AtlasProcessorConfig(
                processor="add_lifespans",
                kwargs={"lifespans": [llms_lifespan, rags_lifespan]},
            ),
            AtlasProcessorConfig(processor="add_pagination"),
            AtlasProcessorConfig(processor="add_api_versioning"),
            AtlasProcessorConfig(
                processor="add_routers",
                kwargs={
                    "routers": [AtlasRouters.get_router("heartbeat", paths={})]
                },
            ),
        ),
        component=environ.component,
        logger=logger,
        use_defaults=False,
    )

    # Filter out /heartbeat
    getLogger("uvicorn.access").addFilter(EndpointFilter())

    return app
