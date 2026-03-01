"""Hard-coded restrictions -- things the system must NEVER do.

These restrictions cannot be overridden by any agent, user configuration,
autonomy phase, or API call. They are the ethical and legal foundation.
"""

import structlog

from orchestra.core.exceptions import RestrictedActionError

logger = structlog.get_logger("compliance.restrictions")


ABSOLUTE_RESTRICTIONS: list[dict[str, str]] = [
    {
        "id": "NO_RATE_LIMIT_BYPASS",
        "description": "Never bypass or circumvent platform rate limits",
        "category": "platform_integrity",
    },
    {
        "id": "NO_HUMAN_IMPERSONATION",
        "description": "Never mask automation as human behavior",
        "category": "platform_integrity",
    },
    {
        "id": "NO_REVIEW_CIRCUMVENTION",
        "description": "Never circumvent platform review processes",
        "category": "platform_integrity",
    },
    {
        "id": "NO_LOOPHOLE_EXPLOITATION",
        "description": "Never exploit platform loopholes or undocumented APIs",
        "category": "platform_integrity",
    },
    {
        "id": "NO_PROHIBITED_AD_CATEGORIES",
        "description": "Never automate ads in prohibited categories",
        "category": "content_safety",
    },
    {
        "id": "NO_POLICY_VIOLATING_ADS",
        "description": "Never generate ads that violate platform content rules",
        "category": "content_safety",
    },
    {
        "id": "NO_PROHIBITED_TARGETING",
        "description": "Never target prohibited demographics or use restricted interest combinations",
        "category": "targeting_safety",
    },
    {
        "id": "NO_PLATFORM_GAMING",
        "description": "Never attempt platform gaming strategies (fake engagement, click farms, etc.)",
        "category": "platform_integrity",
    },
    {
        "id": "NO_DATA_SCRAPING",
        "description": "Never scrape platform data outside official API access",
        "category": "data_integrity",
    },
    {
        "id": "NO_UNOFFICIAL_ENDPOINTS",
        "description": "Never use non-official or undocumented API endpoints",
        "category": "platform_integrity",
    },
    {
        "id": "NO_DECEPTIVE_PRACTICES",
        "description": "Never create misleading, deceptive, or fraudulent content",
        "category": "content_safety",
    },
    {
        "id": "NO_MINOR_TARGETING",
        "description": "Never target advertising to users under 18 without explicit platform compliance",
        "category": "targeting_safety",
    },
    {
        "id": "NO_CREDENTIAL_SHARING",
        "description": "Never share, log, or expose user credentials in plaintext",
        "category": "security",
    },
    {
        "id": "NO_UNAUTHORIZED_DATA_USE",
        "description": "Never use personal data without consent or outside stated purpose",
        "category": "privacy",
    },
]

RESTRICTED_ACTIONS: set[str] = {
    "bypass_rate_limit",
    "impersonate_human",
    "circumvent_review",
    "exploit_loophole",
    "prohibited_ad_category",
    "violate_content_policy",
    "prohibited_targeting",
    "platform_gaming",
    "scrape_data",
    "unofficial_endpoint",
    "deceptive_content",
    "target_minors",
    "expose_credentials",
    "unauthorized_data_use",
}


def check_restriction(action: str, context: str = "") -> None:
    """Check if an action is restricted. Raises RestrictedActionError if so.

    This function should be called before ANY potentially risky operation.
    """
    if action in RESTRICTED_ACTIONS:
        restriction = next(
            (r for r in ABSOLUTE_RESTRICTIONS if r["id"].lower().replace("no_", "") in action),
            {"id": action, "description": f"Action '{action}' is restricted"},
        )

        logger.critical(
            "RESTRICTED_ACTION_ATTEMPTED",
            action=action,
            context=context,
            restriction=restriction["id"],
        )

        raise RestrictedActionError(
            f"Restricted action: {restriction['description']}",
            details={
                "action": action,
                "restriction_id": restriction["id"],
                "category": restriction.get("category", "unknown"),
                "context": context,
            },
        )


def get_all_restrictions() -> list[dict[str, str]]:
    """Get all absolute restrictions (for documentation and UI display)."""
    return list(ABSOLUTE_RESTRICTIONS)


def get_restrictions_by_category(category: str) -> list[dict[str, str]]:
    """Get restrictions filtered by category."""
    return [r for r in ABSOLUTE_RESTRICTIONS if r["category"] == category]


def is_action_restricted(action: str) -> bool:
    """Check if an action is in the restricted list (without raising)."""
    return action in RESTRICTED_ACTIONS
