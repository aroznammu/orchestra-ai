"""Tests for the content agent."""

from orchestra.agents.content import (
    PLATFORM_STYLE_GUIDES,
    _build_prompt,
    _extract_hashtags,
)


def test_platform_style_guides_has_all_platforms():
    expected = ["twitter", "youtube", "instagram", "facebook", "linkedin",
                "tiktok", "pinterest", "snapchat", "google_ads"]
    for p in expected:
        assert p in PLATFORM_STYLE_GUIDES
        assert "max_len" in PLATFORM_STYLE_GUIDES[p]
        assert "style" in PLATFORM_STYLE_GUIDES[p]


def test_build_prompt_contains_key_info():
    prompt = _build_prompt(
        topic="AI analytics launch",
        platform="twitter",
        tone="professional",
        max_len=280,
        style={"style": "concise", "cta_style": "reply"},
        variant_num=1,
    )
    assert "AI analytics launch" in prompt
    assert "twitter" in prompt
    assert "professional" in prompt
    assert "280" in prompt
    assert "variant #1" in prompt


def test_build_prompt_includes_audience():
    prompt = _build_prompt(
        topic="Test",
        platform="linkedin",
        tone="formal",
        max_len=3000,
        style={"style": "professional"},
        variant_num=1,
        target_audience={"age": "25-34", "interest": "tech"},
    )
    assert "Target audience" in prompt
    assert "tech" in prompt


def test_extract_hashtags():
    text = "Check this out #AI #Marketing #DataDriven and more"
    tags = _extract_hashtags(text)
    assert tags == ["#AI", "#Marketing", "#DataDriven"]


def test_extract_hashtags_empty():
    assert _extract_hashtags("No hashtags here") == []


def test_extract_hashtags_inline():
    text = "Love #Python and #FastAPI for building APIs"
    tags = _extract_hashtags(text)
    assert "#Python" in tags
    assert "#FastAPI" in tags


def test_twitter_max_len():
    assert PLATFORM_STYLE_GUIDES["twitter"]["max_len"] == 280


def test_google_ads_max_len():
    assert PLATFORM_STYLE_GUIDES["google_ads"]["max_len"] == 90
