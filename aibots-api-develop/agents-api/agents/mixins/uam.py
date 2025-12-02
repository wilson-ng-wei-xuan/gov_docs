from __future__ import annotations

from datetime import datetime, timedelta, timezone
from io import BytesIO
from itertools import chain
from typing import Any, Dict, List, Optional, Tuple, Union

from atlas.asgi.exceptions import (
    AtlasAPIException,
    AtlasAuthException,
    AtlasPermissionsException,
)
from atlas.environ import E
from atlas.exceptions import AtlasServiceException
from atlas.jose import JoseService
from atlas.mixins import AtlasMixin
from atlas.schemas import (
    AccessRole,
    AccessRoleType,
    Email,
    Login,
    Ownership,
    Permissions,
    PermissionsType,
    ScimStringProperty,
    UserLogin,
    Uuid,
)
from atlas.services import DBS, DS, S
from atlas.utils import run_sync_as_async
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.find.logical import Or
from fastapi import status
from pydantic import EmailStr

from agents.models import (
    LoginDB,
    PermissionsDB,
    RoleDB,
    ScimGroupDB,
    ScimReference,
    ScimUserDB,
)

__all__ = (
    "PermissionsAPIMixin",
    "UsersAPIMixin",
    "LoginsAPIMixin",
)


class PermissionsAPIMixin(AtlasMixin):
    """
    Mixin for supporting Permissions APIs

    Attributes:
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        logger (StructLogService): Atlas logger
        permissions (DS): Permissions dataset
    """

    def __init__(self):
        super().__init__()

        self.environ: E = self.atlas.environ
        self.db: DBS = self.atlas.db
        self.logger: S = self.atlas.logger
        self.permissions: DS = self.atlas.db.atlas_dataset(
            PermissionsDB.Settings.name
        )

    async def atlas_delete_permissions(
        self,
        delete: List[Permissions],
        retrieved: Optional[List[PermissionsDB]] = None,
    ) -> List[PermissionsDB]:
        """
        Functionality to delete permissions

        Args:
            delete (list[Permissions]: Permissions to be deleted
            retrieved (
                list[PermissionsDB | None
            ): Permissions already retrieved

        Returns:
            list[PermissionsDB]: Permissions generated

        Raises:
            AtlasAPIException: Error deleting permissions
        """
        # Retrieve permissions to be updated or reuse if provided
        p_delete: List[PermissionsDB]
        if retrieved:
            p_delete = retrieved
            to_retrieve: List[str] = [
                d.item
                for d in delete
                if d.item not in [r.item for r in retrieved]
            ]
        else:
            p_delete = []
            to_retrieve = [d.item for d in delete]
        if to_retrieve:
            p_delete += await self.permissions.get_items(
                Or(*(PermissionsDB.item == r for r in to_retrieve))
            )

        # Remove delete scopes from permissions
        p_dict: dict[str, Permissions] = {p.item: p for p in delete}
        for p in p_delete:
            if p.item not in p_dict:
                continue
            p.scopes = [s for s in p.scopes if s not in p_dict[p.item].scopes]
        return p_delete

    async def atlas_add_permissions(
        self,
        add: List[Permissions],
        retrieved: Optional[List[PermissionsDB]] = None,
    ) -> List[PermissionsDB]:
        """
        Functionality to add permissions

        Args:
            add (list[Permissions]: Permissions to be added
            retrieved (
                list[PermissionsDB | None
            ): Permissions already retrieved

        Returns:
            list[PermissionsDB]: Permissions generated

        Raises:
            AtlasAPIException: Error adding permissions
        """
        # Retrieve permissions to be updated or reuse if provided
        p_add: List[PermissionsDB]
        if retrieved:
            p_add = retrieved
            to_retrieve: List[str] = [
                d.item
                for d in add
                if d.item not in [r.item for r in retrieved]
            ]
        else:
            p_add = []
            to_retrieve = [d.item for d in add]
        if to_retrieve:
            p_add += await self.permissions.get_items(
                Or(*(PermissionsDB.item == r for r in to_retrieve))
            )

        # Add new scopes to permissions
        p_dict: dict[str, Permissions] = {p.item: p for p in add}
        for a in p_add:
            if a.item not in p_dict:
                continue
            a.scopes += p_dict[a.item].scopes
        return p_add

    async def atlas_get_permissions(
        self, ids: List[str], p_type: PermissionsType = PermissionsType.user
    ) -> List[PermissionsDB]:
        """
        Retrieves all permissions items associated with a given type

        Args:
            ids (str): IDs of the permissions items to be retrieved
            p_type (PermissionsType): Type of permissions, defaults to user

        Returns:
            list[PermissionsDB]: List of permissions
        """
        return await self.permissions.get_items(
            In(PermissionsDB.item, ids), PermissionsDB.type == p_type.value
        )

    async def atlas_get_permission(
        self, p_id: Union[Uuid, str], p_type: PermissionsType
    ) -> PermissionsDB:
        """
        Convenience function for retrieving the item permission set

        Args:
            p_type (PermissionsType): Item Type
            p_id (Union[Uuid, str]): Item ID

        Returns:
            PermissionsDB: Retrieved Item Permissions Set

        Raises:
            AtlasAPIException: If Item Permissions set does not exist
        """
        permissions: Optional[PermissionsDB] = await self.permissions.get_item(
            PermissionsDB.type == p_type.value,
            PermissionsDB.item == p_id,
        )
        if not permissions:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Item Permission Set does not exist",
                details={"type": p_type.value, "item": p_id},
            )
        return permissions

    async def atlas_get_all_user_permissions(
        self, user: Union[ScimUserDB, Uuid, str]
    ) -> Tuple[PermissionsDB, PermissionsDB, List[PermissionsDB]]:
        """
        Convenience function for retrieving all permissions associated
        with a user

        Args:
            user (ScimUserDB | Uuid | str): User ID or object

        Returns:
            Tuple[PermissionsDB, PermissionsDB, List[PermissionsDB]]:
                User's permissions, system-wide permissions,
                group permissions
        """
        if isinstance(user, ScimUserDB):
            user_id: Union[Uuid, str] = user.id
        else:
            user_id: Union[Uuid, str] = user
        user_permissions: Optional[
            PermissionsDB
        ] = await self.permissions.get_item(
            PermissionsDB.type == PermissionsType.user.value,
            PermissionsDB.item == user_id,
        )
        group_permissions: List[
            PermissionsDB
        ] = await self.permissions.get_items(
            PermissionsDB.type == PermissionsType.group.value,
            In(PermissionsDB.item, user_permissions.groups),
        )
        all_permissions: Optional[
            PermissionsDB
        ] = await self.permissions.get_item(
            PermissionsDB.item == "*",
            PermissionsDB.type == PermissionsType.all.value,
        )
        return user_permissions, all_permissions, group_permissions

    async def atlas_get_ownership_role(
        self, user_id: Union[Uuid, str], ownership: Ownership
    ) -> AccessRoleType:
        """
        Checks the assumed role of a specified user as declared in
        the ownership matrix

        Args:
            user_id (Uuid | str): User ID
            ownership (Ownership): Ownership details

        Returns:
            AccessRoleType: Associated access role

        Raises:
            AtlasPermissionsException: User does not have access
                                       to the given resource
        """
        user: PermissionsDB
        groups: List[PermissionsDB]
        user, _, groups = await self.atlas_get_all_user_permissions(user_id)
        for role in AccessRoleType:
            roles: List[AccessRole] = getattr(ownership.access, role)
            if user.item in [
                r.id for r in roles if r.type == PermissionsType.user
            ] or any(
                g.item
                in [r.id for r in roles if r.type == PermissionsType.group]
                for g in groups
            ):
                return AccessRoleType[role]
        raise AtlasPermissionsException(
            user=user_id,
            message="User does not have access to the given resource",
        )

    @staticmethod
    def atlas_validate_permissions_matrix(
        user_id: Union[Uuid, str],
        role: AccessRoleType,
        delete: List[Permissions],
        add: List[Permissions],
    ) -> None:
        """
        Checks if the role that a user assumes according
        to the permissions matrix is able to modify the
        ownership matrix in the given manner

        Args:
            user_id (Uuid | str): ID of the user
            role (AccessRoleType): Role user assumes
            delete (list[Permissions]): List of permissions
                                        to be deleted
            add (list[Permissions]): List of permissions to
                                     be added

        Returns:
            None

        Raises:
            AtlasPermissionsException: Attempting to modify the
                                       ownership matrix with the
                                       wrong roles
            AtlasPermissionsException: Admins unable to modify
                                       owners details
        """
        # Prevent editors, users and viewers from modifying the
        # ownership matrix
        if role in [
            AccessRoleType.editor,
            AccessRoleType.user,
            AccessRoleType.viewer,
        ]:
            raise AtlasPermissionsException(
                user=user_id,
                message="Invalid resource role to modify Agent permissions",
            )

        # Prevent admins from modifying owner details
        if role == AccessRoleType.admin and any(
            i.role == AccessRoleType.owner for i in delete + add
        ):
            raise AtlasPermissionsException(
                user=user_id,
                message="Attempting to modify owner details with an "
                "admin role",
            )

    async def atlas_consolidate_permissions(
        self, delete: List[Permissions], add: List[Permissions]
    ) -> List[PermissionsDB]:
        """
        Consolidating all the permission changes into a
        single list to facilitate DB interactions

        Args:
            delete (list[Permissions]): Permissions to be deleted
            add (list[Permissions]): Permissions to be added

        Returns:
            list[PermissionsDB]: Consolidated permissions
        """
        # Remove delete scopes from permissions
        to_delete: list[PermissionsDB] = []
        if delete:
            to_delete = await self.atlas_delete_permissions(delete)

        # Insert add scopes to permissions
        to_add: list[PermissionsDB] = []
        if add:
            to_add = await self.atlas_add_permissions(add, to_delete)

        # Consolidating permissions
        return to_add + [
            d for d in to_delete if d.item not in [a.item for a in to_add]
        ]


class UsersAPIMixin(PermissionsAPIMixin):
    """
    Mixin for supporting User APIs

    Attributes:
        environ (AppraiserEnviron): Environment variables
        db (BeanieService): MongoDB Service
        logger (StructLogService): Atlas logger
        roles (DS): Roles dataset
        users (DS): Users dataset
        groups (DS): Groups dataset
        permissions (DS): Permissions dataset
    """

    def __init__(self):
        super().__init__()

        self.roles: DS = self.atlas.roles
        self.users: DS = self.atlas.users
        self.groups: DS = self.atlas.db.atlas_dataset(
            ScimGroupDB.Settings.name
        )

    async def atlas_validate_users(
        self, users: List[Union[Uuid, str]]
    ) -> None:
        """
        Validates that all specified users exist

        Args:
            users (list[Uuid | str]): Users to be validated

        Returns:
            None

        Raises:
            AtlasAPIException: If users do not exist
        """
        retrieved: List[ScimUserDB] = await self.users.get_items(
            In(ScimUserDB.id, users)
        )
        if invalid_users := set(users) - {u.id for u in retrieved}:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Users not found",
                details={"ids": list(invalid_users)},
            )

    async def atlas_validate_groups(
        self, groups: List[Union[Uuid, str]]
    ) -> None:
        """
        Validates that all specified groups exist

        Args:
            groups (list[Uuid | str]): Groups to be validated

        Returns:
            None

        Raises:
            AtlasAPIException: If groups do not exist
        """
        retrieved: List[ScimGroupDB] = await self.groups.get_items(
            In(ScimGroupDB.id, groups)
        )
        if invalid_groups := set(groups) - {g.id for g in retrieved}:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Groups not found",
                details={"ids": list(invalid_groups)},
            )

    async def atlas_validate_agency(self, agency: str) -> ScimGroupDB:
        """
        Validates the agency provided and returns the associated
        group

        Args:
            agency (str): Agency code

        Returns:
            ScimGroupDB: Group associated with agency
        """
        group: ScimGroupDB | None = await self.groups.get_item(
            ScimGroupDB.atlas_extensions.agency == agency,
            ScimGroupDB.atlas_extensions.allow == True,  # noqa: E712
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )
        if not group:
            raise AtlasAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Agency does not exist",
                details={"agency": agency},
            )

        return group

    async def atlas_create_user(
        self,
        email: EmailStr,
        name: str,
        username: str,
        group: ScimGroupDB,
        uid: Optional[Uuid] = None,
        verified: bool = True,
        active: bool = True,
        default_role: Optional[RoleDB] = None,
        superuser_role: Optional[RoleDB] = None,
    ) -> Tuple[ScimUserDB, RoleDB, PermissionsDB, ScimGroupDB]:
        """
        Convenience function for checking and creating a new user

        Args:
            email (EmailStr): Email address of the user
            name (str): Name of the user
            username (str): Username details
            group (ScimGroupDB): Scim Group that user belongs to
            uid (Uuid | None): User's UUID, defaults to None
            verified (bool): Indicates if the user is verified,
                             defaults to True
            active (bool): Indicates if the user is active,
                           defaults to True
            default_role (RoleDB | None): Default role of the system
            superuser_role (RoleDB | None): Default superuser role

        Returns:
            Tuple[ScimUserDB, RoleDB, PermissionsDB, ScimGroupDB]:
                Tuple of ScimUserDB, RoleDB, PermissionsDB, ScimGroupDB
        """

        # TODO: Generate Avatar
        # Populate default user values
        emails: List[ScimStringProperty[EmailStr]] = [
            ScimStringProperty[EmailStr](
                value=email.lower(),
                primary=True,
                type="Government Email",
                display=email,
            )
        ]
        groups: List[ScimGroupDB] = [group]
        groups_ref: List[ScimReference] = [
            ScimReference(
                ref=str(self.environ.project.pub_url)
                + f"latest/groups/{group.id}",
                type="groups",
                value=group.id,
                display=group.display_name,
            )
        ]

        # Retrieve group hierarchy
        parent_ref: Union[ScimReference, None] = group.atlas_extensions.parent
        while parent_ref is not None:
            parent: ScimGroupDB = await self.groups.get_item_by_id(
                parent_ref.value
            )
            groups_ref.insert(
                0,
                ScimReference(
                    ref=str(self.environ.project.pub_url)
                    + f"latest/groups/{parent.id}",
                    type="groups",
                    value=parent.id,
                    display=parent.display_name,
                ),
            )
            groups.insert(0, parent)
            parent_ref = parent.atlas_extensions.parent

        # Extract the appropriate user roles
        user_role: RoleDB
        if (
            self.environ.superusers
            and email.lower() in self.environ.superusers
        ):
            if superuser_role:
                user_role = superuser_role
            else:
                user_role = await self.roles.get_item(
                    RoleDB.superuser == True  # noqa: E712
                )
        elif (
            group is not None
            and group.atlas_extensions.default_role is not None
        ):
            user_role = await self.roles.get_item(
                RoleDB.id == group.atlas_extensions.default_role
            )
        else:
            if default_role:
                user_role = default_role
            else:
                user_role = await self.roles.get_item(
                    RoleDB.default == True  # noqa: E712
                )

        # Create new user
        if not uid:
            uid: Uuid = ScimUserDB.atlas_get_uuid(email)
        user: ScimUserDB = ScimUserDB.create_schema(
            user=uid,
            uid=uid,
            resource_type=ScimUserDB.Settings.name,
            location=str(self.environ.project.pub_url) + f"latest/users/{uid}",
            version=1,
            **{
                "external_id": uid,
                "name": {
                    "formatted": name,
                },
                "user_name": username,
                "display_name": name,
                "emails": emails,
                "groups": [groups_ref[-1]],
                "roles": [
                    ScimStringProperty[str](
                        value=user_role.id,
                        primary=True,
                        type="rbac",
                        display=user_role.name,
                    )
                ],
                "atlas_extensions": {
                    "description": "",
                    "agency": groups[0].atlas_extensions.agency,
                    "settings": self.environ.default_user_settings,
                    "favourites": {},
                    "details": {},
                    "verified": verified,
                    "api_keys": [],
                    "allow": True,
                    "active": active,
                    "salt": ScimUserDB.atlas_generate_randstr(),
                },
            },
        )

        # Add specific user's permissions
        permissions: PermissionsDB = PermissionsDB(
            type=PermissionsType.user.value,
            item=user.id,
            scopes=[],
            groups=[g.value for g in groups_ref],
        )

        # Adding User's membership to associated group
        group.members.append(
            ScimReference(
                ref=str(self.environ.project.pub_url)
                + f"latest/users/{user.id}",
                type="users",
                display=user.display_name,
                value=user.id,
            )
        )
        return user, user_role, permissions, group


class LoginsAPIMixin(UsersAPIMixin):
    # TODO: Request details to be extracted and bound to logger
    def __init__(self):
        super().__init__()
        self.s3: S = self.atlas.services.get("s3")
        self.jwt: JoseService = self.atlas.services.get("jwt")
        self.logins: DS = self.atlas.logins

    async def atlas_login_user(
        self,
        user_permissions: PermissionsDB,
        all_permissions: PermissionsDB,
        group_permissions: List[PermissionsDB],
        new_user: bool,
        user: ScimUserDB,
        user_role: RoleDB,
        error_details: Dict[str, Any],
        agency_id: Optional[Uuid] = None,
        logger: Any = None,
    ) -> UserLogin:
        """
        Convenience function for generating a login token
        for a user and uploading analytics details to S3

        Args:
            user_permissions (PermissionsDB): User permissions
            all_permissions (PermissionsDB): System-wide permissions
            group_permissions (list[PermissionsDB]): Group permissions
            new_user (bool): Indicates if the user is logging in for
                             the first time
            user (ScimUserDB): User details
            user_role (RoleDB): User role
            error_details (dict[str, Any]): Error details
            agency_id (Optional[Uuid]): Agency UUID, defaults to None
            logger (Any): Logger for logging details

        Returns:
            UserLogin: Generated Login token details

        Raises:
            AtlasAPIException: Error generating JWT token
            AtlasAPIException: Error creating user login
            AtlasAPIException: Error adding user login token
                               to analytics bucket
        """

        # Generate User Login and issue JWT token
        user_login: UserLogin = UserLogin(
            id=user.id,
            issuer=self.environ.issuer,
            product=self.environ.project.public_domain,
            start_use=datetime.now(timezone.utc),
            expiry=datetime.now(timezone.utc)
            + timedelta(hours=self.environ.expiry.jwt),
            name=user.display_name,
            email=user.emails.primary.value,
            new_user=new_user,
            scopes=user_role.scopes,
            item_scopes=all_permissions.scopes
            + list(chain(*(g.scopes for g in group_permissions)))
            + user_permissions.scopes,
            role=user_role.id,
            superuser=user_role.superuser,
            agency=user.atlas_extensions.agency,
            agency_id=agency_id,
        )
        try:
            login: Login = self.jwt.atlas_encode(user_login)
        except AtlasServiceException as e:
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error generating JWT",
                details=user_login.model_dump(exclude_unset=True, mode="json"),
            ) from e

        # Insert User Login into DB
        if logger:
            await logger.ainfo(
                "Created User Login", data=user_login.model_dump_json()
            )
        if not await self.logins.create_item(
            LoginDB.model_construct(**login.model_dump())
        ):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error creating User Login",
                details=error_details,
            )

        # Insert User Login record for analytics purposes
        try:
            login_file: BytesIO = BytesIO(
                bytes(
                    user_login.model_dump_json(
                        exclude={"token", "access_token"}
                    ),
                    "utf-8",
                )
            )
            await run_sync_as_async(
                self.s3.upload_fileobj,
                **{
                    "Fileobj": login_file,
                    "Bucket": self.environ.analytics.bucket,
                    "Key": f"{self.environ.analytics.path}"
                    f"{user_login.timestamp.date().isoformat()}/"
                    f"logins/{user_login.id}_{str(user_login.timestamp.timestamp())}.json",
                    "ExtraArgs": {
                        "ContentType": "application/json",
                        "Metadata": {
                            "checksum": self.s3.get_checksum(login_file)
                        },
                    },
                },
            )
        except Exception as e:
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error upload User Login token to analytics bucket",
                details=error_details,
            ) from e

        return user_login

    async def atlas_get_login(self, user: ScimUserDB) -> LoginDB:
        """
        Check if user is already logged in and reuse their token

        Args:
            user (ScimUserDB): User details

        Returns:
            LoginDB: User login details
        """
        # Presently we don't have the background schedule to handle
        # clearing of data in an automated manner. Hence we will need
        # to explicitly log a user out and log them back again.
        # TODO: Implement TTL index and test
        user_login: Optional[LoginDB] = await self.logins.get_item_by_id(
            user.id
        )
        if user_login and not await self.logins.delete_item_by_id(user.id):
            raise AtlasAPIException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error logging out user",
            )
        return user_login

    async def atlas_update_unverified_user(self, user) -> None:
        """
        Update unverified user details

        Args:
            user (ScimUserDB): Unverified user

        Returns:
            None

        Raises:
            AtlasAPIException: Unable to change user's verified status
        """

        # Check if the user is unverified and change their status to verified
        if user.atlas_extensions.verified is False:
            user.atlas_extensions.verified = True
            user.atlas_extensions.active = True
            if not await self.users.replace_item(user):
                raise AtlasAPIException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    message="Unable to change user's verified status",
                )

    async def atlas_block_unauthorised_group(
        self, email: EmailStr
    ) -> ScimGroupDB:
        """
        Convenience function for checking if the group is authorised

        Args:
            email (EmailStr): Email of the group

        Returns:
            ScimGroupDB: Authorised group
        """

        # Check if group is authorised
        group: Optional[ScimGroupDB] = await self.groups.get_item(
            ScimGroupDB.atlas_extensions.domain
            == Email.atlas_get_domain(email),
            ScimGroupDB.atlas_extensions.allow == True,  # noqa: E712
            ScimGroupDB.meta.deleted == None,  # noqa: E711
        )

        if group is None:
            # TODO: Attempt to authenticate with Techpass
            # TODO: Vendors should be created with a vendor role
            raise AtlasAuthException(
                "Attempting to log in with unauthorised email",
                user=email,
            )
        return group

    @staticmethod
    async def atlas_block_unauthorised_user(user: ScimUserDB) -> None:
        """
        Block an unauthorised user

        Args:
            user (ScimUserDB): User to be verified

        Returns:
            None

        Raises:
            AtlasAuthException: Block an unauthorised user
        """
        # Block all unauthorised users
        if user.atlas_extensions.allow is False:
            raise AtlasAuthException(
                message="Unauthorised user",
                user=user.id,
            )
