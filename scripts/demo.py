"""
OrchestraAI Demo Script

Demonstrates core platform capabilities through the API.
Run with: poetry run python scripts/demo.py
Requires: API running at http://localhost:8000
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

import httpx

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"


async def step(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")
    await asyncio.sleep(0.5)


async def show(label: str, data: Any) -> None:
    import json

    if isinstance(data, dict):
        print(f"\n  {label}:")
        for k, v in data.items():
            val = json.dumps(v, indent=4) if isinstance(v, (dict, list)) else v
            print(f"    {k}: {val}")
    else:
        print(f"\n  {label}: {data}")


async def main() -> None:
    print("\n" + "=" * 60)
    print("  OrchestraAI — Platform Demo")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Health Check
        await step("1. Health Check")
        resp = await client.get(f"{BASE_URL}/health")
        await show("Health", resp.json())

        resp = await client.get(f"{BASE_URL}/ready")
        await show("Readiness", resp.json())

        # 2. Register a user
        await step("2. Register Demo User")
        user_data = {
            "email": "demo@orchestra-ai.dev",
            "password": "DemoPassword123!",
            "tenant_name": "Demo Organization",
        }
        resp = await client.post(f"{API}/auth/register", json=user_data)
        if resp.status_code == 200:
            reg = resp.json()
            await show("Registered", {"user_id": reg.get("user_id"), "tenant": reg.get("tenant_name")})
        elif resp.status_code == 409:
            print("  User already exists, proceeding to login...")
        else:
            await show("Register response", {"status": resp.status_code, "body": resp.text})

        # 3. Login
        await step("3. Login")
        login_data = {
            "email": "demo@orchestra-ai.dev",
            "password": "DemoPassword123!",
        }
        resp = await client.post(f"{API}/auth/login", json=login_data)
        if resp.status_code != 200:
            print(f"  Login failed ({resp.status_code}): {resp.text}")
            print("  Continuing demo without auth...")
            headers = {}
        else:
            token = resp.json().get("access_token", "")
            headers = {"Authorization": f"Bearer {token}"}
            print(f"  Logged in. Token: {token[:20]}...")

        # 4. List platforms
        await step("4. Available Platforms")
        resp = await client.get(f"{API}/platforms/connections", headers=headers)
        if resp.status_code == 200:
            platforms = resp.json()
            await show("Platforms", platforms)
        else:
            print(f"  ({resp.status_code}) — auth may be required")

        # 5. Orchestrator
        await step("5. AI Orchestrator")
        orchestrate_payload = {
            "message": "Create a product launch announcement for our new AI-powered analytics tool. Target Twitter and LinkedIn.",
        }
        resp = await client.post(
            f"{API}/orchestrator",
            json=orchestrate_payload,
            headers=headers,
        )
        if resp.status_code == 200:
            result = resp.json()
            await show("Orchestrator Result", result)
        else:
            print(f"  ({resp.status_code}) — {resp.text[:200]}")

        # 6. Kill Switch Status
        await step("6. Kill Switch Status")
        resp = await client.get(f"{API}/kill-switch/status", headers=headers)
        if resp.status_code == 200:
            await show("Kill Switch", resp.json())
        else:
            print(f"  ({resp.status_code}) — may require elevated permissions")

        # 7. Audit Log
        await step("7. Audit Log (recent)")
        resp = await client.get(f"{API}/audit?limit=5", headers=headers)
        if resp.status_code == 200:
            entries = resp.json()
            print(f"  Found {len(entries) if isinstance(entries, list) else 'N/A'} recent entries")
        else:
            print(f"  ({resp.status_code}) — may require admin role")

        # Done
        print("\n" + "=" * 60)
        print("  Demo complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("  - Connect a real platform: POST /api/v1/platforms/auth/init")
        print("  - Create a campaign via the orchestrator")
        print("  - Explore the API docs at http://localhost:8000/docs")
        print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except httpx.ConnectError:
        print("\nError: Cannot connect to OrchestraAI API at http://localhost:8000")
        print("Start the API first: poetry run uvicorn orchestra.main:app --reload")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nDemo interrupted.")
