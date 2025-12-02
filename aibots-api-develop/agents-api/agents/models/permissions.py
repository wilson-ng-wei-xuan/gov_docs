from __future__ import annotations

from atlas.schemas import Permissions
from beanie import Document

__all__ = ("PermissionsDB",)


class PermissionsDB(Permissions, Document):
    """
    Consolidates all user, group, API Key and Public
    permissions

    Attributes:
        type (PermissionsType): Type of the permission set
        scopes (list[str]): List of scopes, defaults to an
                            empty list
        item (Uuid | str | None): ID of the item, defaults to
                                  None
        groups (list[Uuid]): Relevant groups associated with
                             permission set to get additional
                             permissions from
    """

    class Settings:
        name: str = "permissions"
