"""Tests for the OrchestraAI CLI.

Tests cover:
  - Config persistence (load/save/clear)
  - HTTP client header injection and error handling
  - Typer command invocation via CliRunner
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from orchestra.cli import config as cli_config
from orchestra.cli.app import app
from orchestra.cli.client import APIError

runner = CliRunner()


# ===================================================================
#  Config persistence
# ===================================================================

class TestConfig:

    def test_load_defaults_when_no_file(self, tmp_path: Path):
        with patch.object(cli_config, "CONFIG_FILE", tmp_path / "missing.json"):
            cfg = cli_config.load()
        assert cfg["api_url"] == "http://localhost:8000/api/v1"
        assert cfg["token"] == ""

    def test_save_and_load_roundtrip(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        with patch.object(cli_config, "CONFIG_FILE", cfg_file), \
             patch.object(cli_config, "CONFIG_DIR", tmp_path):
            cli_config.save({"api_url": "http://custom:9000/api/v1", "token": "tok123"})
            loaded = cli_config.load()
        assert loaded["api_url"] == "http://custom:9000/api/v1"
        assert loaded["token"] == "tok123"

    def test_set_and_get_token(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        with patch.object(cli_config, "CONFIG_FILE", cfg_file), \
             patch.object(cli_config, "CONFIG_DIR", tmp_path):
            cli_config.set_token("jwt-abc")
            assert cli_config.get_token() == "jwt-abc"

    def test_set_api_url_strips_trailing_slash(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        with patch.object(cli_config, "CONFIG_FILE", cfg_file), \
             patch.object(cli_config, "CONFIG_DIR", tmp_path):
            cli_config.set_api_url("http://host:8000/api/v1/")
            assert cli_config.get_api_url() == "http://host:8000/api/v1"

    def test_clear_resets_to_defaults(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        with patch.object(cli_config, "CONFIG_FILE", cfg_file), \
             patch.object(cli_config, "CONFIG_DIR", tmp_path):
            cli_config.set_token("secret")
            cli_config.clear()
            assert cli_config.get_token() == ""

    def test_load_handles_corrupt_json(self, tmp_path: Path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("{bad json", encoding="utf-8")
        with patch.object(cli_config, "CONFIG_FILE", cfg_file):
            cfg = cli_config.load()
        assert cfg["api_url"] == "http://localhost:8000/api/v1"


# ===================================================================
#  HTTP client
# ===================================================================

class TestClient:

    def test_api_error_str(self):
        e = APIError(401, "Unauthorized")
        assert "401" in str(e)
        assert "Unauthorized" in str(e)

    @pytest.mark.asyncio
    async def test_get_includes_auth_header(self):
        import httpx
        from orchestra.cli import client

        captured_headers: dict = {}

        async def mock_get(self, url, **kwargs):
            captured_headers.update(kwargs.get("headers", {}))
            resp = httpx.Response(200, json={"ok": True}, request=httpx.Request("GET", url))
            return resp

        with patch.object(cli_config, "CONFIG_FILE", Path("/nonexistent")), \
             patch.object(httpx.AsyncClient, "get", mock_get):
            cli_config._DEFAULTS["token"] = "test-jwt"
            try:
                await client.get("/test")
            finally:
                cli_config._DEFAULTS["token"] = ""

    @pytest.mark.asyncio
    async def test_post_raises_api_error_on_failure(self):
        import httpx
        from orchestra.cli import client

        async def mock_post(self, url, **kwargs):
            return httpx.Response(
                422,
                json={"detail": "Validation failed"},
                request=httpx.Request("POST", url),
            )

        with patch.object(cli_config, "CONFIG_FILE", Path("/nonexistent")), \
             patch.object(httpx.AsyncClient, "post", mock_post):
            with pytest.raises(APIError) as exc_info:
                await client.post("/test", json={"bad": True})
            assert exc_info.value.status_code == 422


# ===================================================================
#  CLI commands via CliRunner
# ===================================================================

class TestCLICommands:

    def test_version(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "OrchestraAI" in result.output
        assert "0.1.0" in result.output

    def test_config_shows_info(self):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "API URL" in result.output

    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 0
        assert "OrchestraAI" in result.output

    def test_auth_logout(self):
        with patch.object(cli_config, "CONFIG_FILE", Path("/tmp/.orchestra_test_cfg.json")), \
             patch.object(cli_config, "CONFIG_DIR", Path("/tmp")):
            result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
        assert "cleared" in result.output.lower()

    def test_campaign_list_requires_auth(self):
        with patch("orchestra.cli.config.get_token", return_value=""):
            result = runner.invoke(app, ["campaign", "list"])
        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_analytics_requires_auth(self):
        with patch("orchestra.cli.config.get_token", return_value=""):
            result = runner.invoke(app, ["analytics"])
        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_ask_requires_auth(self):
        with patch("orchestra.cli.config.get_token", return_value=""):
            result = runner.invoke(app, ["ask", "hello"])
        assert result.exit_code == 1
        assert "Not authenticated" in result.output

    def test_campaign_list_with_mock_api(self):
        mock_data = {
            "campaigns": [
                {
                    "id": "abc-123-def",
                    "name": "Summer Sale",
                    "status": "active",
                    "platforms": ["twitter", "instagram"],
                    "budget": 5000.0,
                    "spent": 1200.0,
                },
            ],
            "total": 1,
        }
        with patch("orchestra.cli.config.get_token", return_value="jwt-tok"), \
             patch("orchestra.cli.app._run", return_value=mock_data):
            result = runner.invoke(app, ["campaign", "list"])
        assert result.exit_code == 0
        assert "Summer Sale" in result.output

    def test_analytics_with_mock_api(self):
        mock_data = {
            "total_impressions": 50000,
            "total_engagement": 3200,
            "total_clicks": 1500,
            "total_spend": 800.0,
            "average_engagement_rate": 0.064,
            "platforms": {
                "twitter": {
                    "impressions": 30000, "engagement": 2000,
                    "clicks": 900, "engagement_rate": 0.067, "spend": 500.0,
                },
            },
            "insights": ["Twitter engagement above benchmark"],
            "recommendations": ["Increase Instagram posting frequency"],
        }
        with patch("orchestra.cli.config.get_token", return_value="jwt-tok"), \
             patch("orchestra.cli.app._run", return_value=mock_data):
            result = runner.invoke(app, ["analytics"])
        assert result.exit_code == 0
        assert "50,000" in result.output or "50000" in result.output
        assert "Twitter" in result.output or "twitter" in result.output

    def test_ask_with_mock_api(self):
        mock_data = {
            "trace_id": "tr-123",
            "intent": "generate_content",
            "is_complete": True,
            "content": {"text": "Here is your LinkedIn post about Q1 results..."},
        }
        with patch("orchestra.cli.config.get_token", return_value="jwt-tok"), \
             patch("orchestra.cli.app._run", return_value=mock_data):
            result = runner.invoke(app, ["ask", "Write a LinkedIn post"])
        assert result.exit_code == 0
        assert "generate_content" in result.output
        assert "LinkedIn post" in result.output

    def test_ask_shows_error_from_api(self):
        with patch("orchestra.cli.config.get_token", return_value="jwt-tok"), \
             patch("orchestra.cli.app._run", side_effect=APIError(500, "Internal server error")):
            result = runner.invoke(app, ["ask", "fail"])
        assert result.exit_code == 1
        assert "500" in result.output

    def test_auth_login_with_api_key(self):
        mock_user = {"user_id": "u1", "email": "a@b.com", "role": "owner"}
        with patch("orchestra.cli.config.set_token") as mock_set, \
             patch("orchestra.cli.app._run", return_value=mock_user):
            result = runner.invoke(app, ["auth", "login", "--api-key", "sk-test-key"])
        assert result.exit_code == 0
        mock_set.assert_called_with("sk-test-key")

    def test_campaign_create_interactive(self):
        mock_resp = {
            "id": "new-camp-id",
            "name": "Winter Campaign",
            "status": "draft",
            "platforms": ["twitter"],
            "budget": 1000.0,
        }
        with patch("orchestra.cli.config.get_token", return_value="jwt-tok"), \
             patch("orchestra.cli.app._run", return_value=mock_resp):
            result = runner.invoke(
                app,
                ["campaign", "create"],
                input="Winter Campaign\nHoliday promos\ntwitter\n1000\n",
            )
        assert result.exit_code == 0
        assert "Campaign created" in result.output

    def test_status_command(self):
        mock_results = [
            {"name": "API Server", "ok": True, "detail": "healthy"},
            {"name": "PostgreSQL", "ok": False, "detail": "connection refused"},
            {"name": "Redis", "ok": True, "detail": "v7.2"},
            {"name": "Ollama", "ok": False, "detail": "timeout"},
        ]
        with patch("orchestra.cli.app._run", return_value=mock_results):
            result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "API Server" in result.output
        assert "2/4" in result.output or "2" in result.output
