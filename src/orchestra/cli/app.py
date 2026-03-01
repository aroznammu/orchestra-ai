"""OrchestraAI CLI -- Typer-based command interface."""

import asyncio
from typing import Any

import typer

app = typer.Typer(
    name="orchestra",
    help="OrchestraAI -- AI-Native Marketing Orchestration Platform",
    no_args_is_help=True,
)

campaign_app = typer.Typer(help="Campaign management commands")
connect_app = typer.Typer(help="Platform connection commands")
optimize_app = typer.Typer(help="Optimization commands")
report_app = typer.Typer(help="Reporting commands")

app.add_typer(campaign_app, name="campaign")
app.add_typer(connect_app, name="connect")
app.add_typer(optimize_app, name="optimize")
app.add_typer(report_app, name="report")


# --- Campaign commands ---


@campaign_app.command("list")
def campaign_list() -> None:
    """List all campaigns."""
    typer.echo("Campaigns: (none yet -- Phase 2+)")


@campaign_app.command("create")
def campaign_create(
    name: str = typer.Option(..., help="Campaign name"),
    budget: float = typer.Option(0.0, help="Campaign budget in USD"),
) -> None:
    """Create a new campaign."""
    typer.echo(f"Creating campaign '{name}' with budget ${budget:.2f}...")
    typer.echo("Campaign creation requires Phase 2 platform integrations.")


@campaign_app.command("status")
def campaign_status(campaign_id: str = typer.Argument(..., help="Campaign ID")) -> None:
    """Check campaign status."""
    typer.echo(f"Status for campaign {campaign_id}: (not yet implemented)")


# --- Connect commands ---


@connect_app.command("add")
def connect_add(
    platform: str = typer.Argument(..., help="Platform name (twitter, youtube, etc.)"),
) -> None:
    """Connect a platform account."""
    typer.echo(f"Connecting {platform}... (OAuth flow requires Phase 2)")


@connect_app.command("list")
def connect_list() -> None:
    """List connected platforms."""
    typer.echo("Connected platforms: (none yet)")


@connect_app.command("remove")
def connect_remove(
    platform: str = typer.Argument(..., help="Platform to disconnect"),
) -> None:
    """Disconnect a platform account."""
    typer.echo(f"Disconnecting {platform}... (requires Phase 2)")


# --- Optimize commands ---


@optimize_app.command("run")
def optimize_run(campaign_id: str = typer.Argument(..., help="Campaign to optimize")) -> None:
    """Run optimization on a campaign."""
    typer.echo(f"Optimizing campaign {campaign_id}... (requires Phase 3 agents)")


# --- Report commands ---


@report_app.command("generate")
def report_generate(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
    format: str = typer.Option("text", help="Output format (text, json, html)"),
) -> None:
    """Generate a campaign report."""
    typer.echo(f"Generating {format} report for campaign {campaign_id}... (requires Phase 3)")


@report_app.command("summary")
def report_summary() -> None:
    """Show platform-wide performance summary."""
    typer.echo("Performance summary: (requires Phase 3 analytics agent)")


# --- Top-level commands ---


@app.command()
def version() -> None:
    """Show OrchestraAI version."""
    from orchestra import __version__

    typer.echo(f"OrchestraAI v{__version__}")


async def _check_service(name: str, check_fn) -> dict[str, Any]:
    """Run a single service check with timeout."""
    try:
        result = await asyncio.wait_for(check_fn(), timeout=5.0)
        return {"name": name, "ok": True, "detail": result}
    except Exception as e:
        return {"name": name, "ok": False, "detail": str(e)}


async def _check_postgres() -> str:
    from sqlalchemy import text
    from orchestra.db.session import engine

    async with engine.connect() as conn:
        row = await conn.execute(text("SELECT version()"))
        ver = row.scalar() or ""
    return ver.split(",")[0] if ver else "connected"


async def _check_redis() -> str:
    import redis.asyncio as aioredis
    from orchestra.config import get_settings

    r = aioredis.from_url(get_settings().redis_url, socket_connect_timeout=3)
    try:
        info = await r.info("server")
        return f"v{info.get('redis_version', '?')}"
    finally:
        await r.aclose()


async def _check_kafka() -> str:
    from orchestra.config import get_settings

    import socket
    host, port_s = get_settings().kafka_bootstrap_servers.split(":")
    sock = socket.create_connection((host, int(port_s)), timeout=3)
    sock.close()
    return "reachable"


async def _check_qdrant() -> str:
    import httpx
    from orchestra.config import get_settings

    settings = get_settings()
    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.get(f"{settings.qdrant_url}/healthz")
        return "healthy" if resp.status_code == 200 else f"status {resp.status_code}"


async def _check_ollama() -> str:
    import httpx
    from orchestra.config import get_settings

    settings = get_settings()
    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.get(f"{settings.ollama_base_url}/api/tags")
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return f"{len(models)} model(s)" if models else "running (no models)"


async def _check_api() -> str:
    import httpx

    async with httpx.AsyncClient(timeout=3.0) as client:
        resp = await client.get("http://localhost:8000/health")
        if resp.status_code == 200:
            return "healthy"
        return f"status {resp.status_code}"


async def _run_all_checks() -> list[dict[str, Any]]:
    checks = [
        ("API Server", _check_api),
        ("PostgreSQL", _check_postgres),
        ("Redis", _check_redis),
        ("Kafka", _check_kafka),
        ("Qdrant", _check_qdrant),
        ("Ollama", _check_ollama),
    ]
    return await asyncio.gather(*[_check_service(name, fn) for name, fn in checks])


@app.command()
def status() -> None:
    """Show system status by checking all infrastructure services."""
    typer.echo()
    typer.echo("  OrchestraAI System Status")
    typer.echo("  " + "=" * 38)

    results = asyncio.run(_run_all_checks())

    for r in results:
        icon = typer.style(" OK ", fg=typer.colors.GREEN, bold=True) if r["ok"] else typer.style("FAIL", fg=typer.colors.RED, bold=True)
        detail = r["detail"] if len(str(r["detail"])) < 60 else str(r["detail"])[:57] + "..."
        typer.echo(f"  [{icon}] {r['name']:<14} {detail}")

    typer.echo()
    ok_count = sum(1 for r in results if r["ok"])
    total = len(results)
    if ok_count == total:
        typer.echo(typer.style(f"  All {total} services operational.", fg=typer.colors.GREEN, bold=True))
    else:
        typer.echo(typer.style(f"  {ok_count}/{total} services operational.", fg=typer.colors.YELLOW, bold=True))
    typer.echo()


if __name__ == "__main__":
    app()
