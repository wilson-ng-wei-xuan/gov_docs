from __future__ import annotations

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import re
from typing import Any, Dict, List

from atlas.asgi.schemas import APIGet, AtlasASGIConfig
from atlas.environ import E
from atlas.fastapi import AtlasDependencies, AtlasRouters
from atlas.schemas import UserLogin, Uuid
from atlas.services import DS
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.find.logical import Or
from fastapi import APIRouter, Depends, Query, status
from fastapi_utils.cbv import cbv
from fastapi_versionizer import api_version
from pydantic import StringConstraints

from agents.models import ScimGroupDB

router: APIRouter = AtlasRouters.atlas_get_router(
    **{
        "tags": ["Agencies"],
        "prefix": "",
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


class Agency(APIGet):
    """
    GET representation of Agency

    Attributes:
        id (Uuid): ID of the Group
        agency (str): Name of the Agency
        code (str): Agency code
        domain (str): Domain of the Agency
    """

    id: Uuid
    agency: str
    domain: str
    code: str


@cbv(router)
class AgencyAPI:
    """
    Class-based view for representing the APIs for managing
    SCIM Groups

    Attributes:
        user (UserLogin): User login details
        atlas (AtlasASGIConfig): Atlas application config
        environ (E): Application environment variables
        groups (DS): Scim Group database collection
    """

    user: UserLogin = Depends(
        AtlasDependencies.get_registry_item("auth_session")
    )
    atlas: AtlasASGIConfig = Depends(
        AtlasDependencies.get_registry_item("get_atlas")
    )

    # TODO: Request details to be extracted and bound to logger
    def __init__(self):
        super().__init__()
        self.environ: E = self.atlas.environ
        self.groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )

    @router.get(
        "/queries/agencies/",
        status_code=status.HTTP_200_OK,
        response_model=List[Agency],
        include_in_schema=False,
    )
    @router.get(
        "/queries/agencies",
        status_code=status.HTTP_200_OK,
        response_model=List[Agency],
        responses={
            status.HTTP_200_OK: {
                "description": "Successfully retrieved Agencies",
                "content": {"application/json": {"example": []}},
                "model": List[Agency],
            },
        },
    )
    @api_version(1, 0)
    async def get_agencies(
        self,
        domains: List[
            Annotated[str, StringConstraints(to_lower=True)]
        ] = Query([]),
        names: List[Annotated[str, StringConstraints(to_lower=True)]] = Query(
            []
        ),
    ) -> List[Dict[str, Any]]:
        """
        Retrieves all verified agencies, provides a list of
        domains to query against

        Args:
            domains (list[str]): Domain strings
            names (list[str]): Agency name strings

        Returns:
            List[Dict[str, Any]]: Verified agencies
        """
        # If domains empty set no filters
        conditions: List[Any] = [
            ScimGroupDB.atlas_extensions.agency != None,  # noqa: E711
            ScimGroupDB.atlas_extensions.domain != None,  # noqa: E711
        ]

        additional_conditions: List[Any] = []
        if len(domains) > 0:
            additional_conditions.append(
                In(
                    ScimGroupDB.atlas_extensions.domain,
                    [
                        re.compile(r"{}".format(domain), re.IGNORECASE)
                        for domain in domains
                    ],
                ),
            )
        if len(names) > 0:
            additional_conditions.append(
                In(
                    ScimGroupDB.display_name,
                    [
                        re.compile(r"{}".format(name), re.IGNORECASE)
                        for name in names
                    ],
                ),
            )
        if additional_conditions:
            conditions.append(Or(*additional_conditions))

        return [
            {
                "id": group.id,
                "code": group.atlas_extensions.agency,
                "domain": group.atlas_extensions.domain,
                "agency": group.display_name,
            }
            for group in await self.groups.get_items(
                *conditions, sort=[(ScimGroupDB.display_name, 1)]
            )
        ]
