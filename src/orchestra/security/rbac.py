"""Role-Based Access Control (RBAC).

Roles: owner > admin > member > viewer
Each role has a defined set of permissions. Higher roles inherit lower permissions.
"""

from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

from orchestra.core.exceptions import AuthorizationError

logger = structlog.get_logger("security.rbac")


class Role(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class Permission(str, Enum):
    # Campaigns
    CAMPAIGN_VIEW = "campaign:view"
    CAMPAIGN_CREATE = "campaign:create"
    CAMPAIGN_EDIT = "campaign:edit"
    CAMPAIGN_DELETE = "campaign:delete"
    CAMPAIGN_PUBLISH = "campaign:publish"

    # Platforms
    PLATFORM_VIEW = "platform:view"
    PLATFORM_CONNECT = "platform:connect"
    PLATFORM_DISCONNECT = "platform:disconnect"

    # Analytics
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

    # Budget & Bidding
    BUDGET_VIEW = "budget:view"
    BUDGET_EDIT = "budget:edit"
    BUDGET_APPROVE = "budget:approve"

    # Users & Tenant
    USER_VIEW = "user:view"
    USER_INVITE = "user:invite"
    USER_REMOVE = "user:remove"
    USER_CHANGE_ROLE = "user:change_role"

    # Settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_EDIT = "settings:edit"

    # Kill switch
    KILL_SWITCH_VIEW = "kill_switch:view"
    KILL_SWITCH_ACTIVATE = "kill_switch:activate"

    # Data management
    DATA_EXPORT = "data:export"
    DATA_DELETE = "data:delete"

    # Orchestrator
    ORCHESTRATOR_RUN = "orchestrator:run"
    ORCHESTRATOR_VIEW = "orchestrator:view"

    # Audit
    AUDIT_VIEW = "audit:view"


ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.VIEWER: {
        Permission.CAMPAIGN_VIEW,
        Permission.PLATFORM_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.BUDGET_VIEW,
        Permission.SETTINGS_VIEW,
        Permission.ORCHESTRATOR_VIEW,
    },
    Role.MEMBER: {
        # Inherits VIEWER +
        Permission.CAMPAIGN_CREATE,
        Permission.CAMPAIGN_EDIT,
        Permission.CAMPAIGN_PUBLISH,
        Permission.PLATFORM_CONNECT,
        Permission.ANALYTICS_EXPORT,
        Permission.ORCHESTRATOR_RUN,
    },
    Role.ADMIN: {
        # Inherits MEMBER +
        Permission.CAMPAIGN_DELETE,
        Permission.PLATFORM_DISCONNECT,
        Permission.BUDGET_EDIT,
        Permission.BUDGET_APPROVE,
        Permission.USER_VIEW,
        Permission.USER_INVITE,
        Permission.SETTINGS_EDIT,
        Permission.KILL_SWITCH_VIEW,
        Permission.DATA_EXPORT,
        Permission.AUDIT_VIEW,
    },
    Role.OWNER: {
        # Inherits ADMIN +
        Permission.USER_REMOVE,
        Permission.USER_CHANGE_ROLE,
        Permission.KILL_SWITCH_ACTIVATE,
        Permission.DATA_DELETE,
    },
}

# Build cumulative permissions (role inherits all lower role permissions)
_ROLE_HIERARCHY = [Role.VIEWER, Role.MEMBER, Role.ADMIN, Role.OWNER]


def _build_cumulative() -> dict[Role, set[Permission]]:
    cumulative: dict[Role, set[Permission]] = {}
    accumulated: set[Permission] = set()
    for role in _ROLE_HIERARCHY:
        accumulated = accumulated | ROLE_PERMISSIONS[role]
        cumulative[role] = set(accumulated)
    return cumulative


CUMULATIVE_PERMISSIONS = _build_cumulative()


def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        r = Role(role)
    except ValueError:
        return False
    return permission in CUMULATIVE_PERMISSIONS.get(r, set())


def check_permission(role: str, permission: Permission) -> None:
    """Check permission and raise AuthorizationError if denied."""
    if not has_permission(role, permission):
        logger.warning(
            "permission_denied",
            role=role,
            permission=permission.value,
        )
        raise AuthorizationError(
            f"Role '{role}' lacks permission: {permission.value}",
            details={"role": role, "required_permission": permission.value},
        )


def get_permissions(role: str) -> list[str]:
    """Get all permissions for a role (including inherited)."""
    try:
        r = Role(role)
    except ValueError:
        return []
    return sorted(p.value for p in CUMULATIVE_PERMISSIONS.get(r, set()))


def get_role_hierarchy() -> list[dict[str, Any]]:
    """Get the role hierarchy with permission counts."""
    return [
        {
            "role": role.value,
            "level": i,
            "direct_permissions": len(ROLE_PERMISSIONS[role]),
            "total_permissions": len(CUMULATIVE_PERMISSIONS[role]),
        }
        for i, role in enumerate(_ROLE_HIERARCHY)
    ]
