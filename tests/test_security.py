"""Tests for RBAC permissions and encryption."""

from orchestra.security.rbac import (
    Permission,
    Role,
    has_permission,
    check_permission,
    get_permissions,
    CUMULATIVE_PERMISSIONS,
)
from orchestra.security.encryption import encrypt_token, decrypt_token
from orchestra.bidding.guardrails import ABSOLUTE_LIMITS

import pytest


def test_viewer_can_view_campaigns():
    assert has_permission("viewer", Permission.CAMPAIGN_VIEW) is True


def test_viewer_cannot_create_campaigns():
    assert has_permission("viewer", Permission.CAMPAIGN_CREATE) is False


def test_member_inherits_viewer_permissions():
    assert has_permission("member", Permission.CAMPAIGN_VIEW) is True
    assert has_permission("member", Permission.ANALYTICS_VIEW) is True


def test_member_can_create_campaigns():
    assert has_permission("member", Permission.CAMPAIGN_CREATE) is True


def test_admin_has_budget_edit():
    assert has_permission("admin", Permission.BUDGET_EDIT) is True


def test_admin_cannot_activate_kill_switch():
    assert has_permission("admin", Permission.KILL_SWITCH_ACTIVATE) is False


def test_owner_has_all_permissions():
    owner_perms = CUMULATIVE_PERMISSIONS[Role.OWNER]
    for p in Permission:
        assert p in owner_perms, f"Owner missing permission: {p.value}"


def test_owner_can_activate_kill_switch():
    assert has_permission("owner", Permission.KILL_SWITCH_ACTIVATE) is True


def test_invalid_role_returns_false():
    assert has_permission("superadmin", Permission.CAMPAIGN_VIEW) is False


def test_check_permission_raises_on_denied():
    from orchestra.core.exceptions import AuthorizationError

    with pytest.raises(AuthorizationError):
        check_permission("viewer", Permission.CAMPAIGN_DELETE)


def test_get_permissions_returns_sorted_list():
    perms = get_permissions("viewer")
    assert isinstance(perms, list)
    assert all(isinstance(p, str) for p in perms)
    assert perms == sorted(perms)


def test_get_permissions_empty_for_invalid_role():
    perms = get_permissions("nonexistent")
    assert perms == []


def test_encrypt_decrypt_roundtrip():
    original = "my-secret-oauth-token-12345"
    encrypted = encrypt_token(original)
    assert encrypted != original
    decrypted = decrypt_token(encrypted)
    assert decrypted == original


def test_encrypt_produces_different_ciphertexts():
    token = "same-token"
    e1 = encrypt_token(token)
    e2 = encrypt_token(token)
    assert e1 != e2


def test_absolute_limits_safety():
    assert ABSOLUTE_LIMITS["max_daily_spend_any_tenant"] == 50000.0
    assert ABSOLUTE_LIMITS["max_single_bid"] == 10000.0
    assert ABSOLUTE_LIMITS["min_budget"] == 1.0
