"""OrchestraAI CLI -- Typer + Rich command interface.

Usage:
    orchestra auth login
    orchestra campaign list
    orchestra campaign create
    orchestra analytics
    orchestra ask "Write a LinkedIn post about Q1 results"
    orchestra status
"""

from __future__ import annotations

import asyncio
from typing import Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from orchestra.cli import client, config
from orchestra.cli.client import APIError

console = Console()

app = typer.Typer(
    name="orchestra",
    help="OrchestraAI -- AI-Native Marketing Orchestration Platform",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

auth_app = typer.Typer(help="Authentication commands")
campaign_app = typer.Typer(help="Campaign management commands")
app.add_typer(auth_app, name="auth")
app.add_typer(campaign_app, name="campaign")


def _run(coro):  # noqa: ANN001, ANN202
    """Run an async coroutine from synchronous Typer commands."""
    return asyncio.run(coro)


def _require_auth() -> None:
    """Abort early if no token is stored."""
    if not config.get_token():
        console.print(
            "[bold red]Not authenticated.[/bold red] "
            "Run [cyan]orchestra auth login[/cyan] first."
        )
        raise typer.Exit(code=1)


def _handle_api_error(e: APIError) -> None:
    """Print a formatted API error and exit."""
    console.print(f"[bold red]API Error ({e.status_code}):[/bold red] {e.detail}")
    raise typer.Exit(code=1)


# ===================================================================
#  auth
# ===================================================================

@auth_app.command("login")
def auth_login(
    api_url: str = typer.Option(
        "", "--url", "-u",
        help="API base URL (default: http://localhost:8000/api/v1)",
    ),
    api_key: str = typer.Option("", "--api-key", "-k", help="Authenticate with an API key"),
    email: str = typer.Option("", "--email", "-e", help="Email for username/password login"),
    password: str = typer.Option("", "--password", "-p", help="Password for login", hide_input=True),
) -> None:
    """Authenticate with the OrchestraAI backend."""
    if api_url:
        config.set_api_url(api_url)
        console.print(f"[dim]API URL set to[/dim] {api_url}")

    if api_key:
        config.set_token(api_key)
        console.print("[green]Saved API key.[/green] Verifying...")
        try:
            user = _run(client.get("/auth/me"))
            console.print(
                f"[bold green]Authenticated[/bold green] as "
                f"[cyan]{user.get('email') or user.get('user_id')}[/cyan] "
                f"(role: {user.get('role', 'unknown')})"
            )
        except APIError:
            console.print("[yellow]Key saved but could not verify (server may be down).[/yellow]")
        return

    if not email:
        email = Prompt.ask("[bold]Email[/bold]")
    if not password:
        password = Prompt.ask("[bold]Password[/bold]", password=True)

    try:
        data = _run(client.post("/auth/login", json={"email": email, "password": password}))
    except APIError as e:
        _handle_api_error(e)
        return

    token = data.get("access_token", "")
    config.set_token(token)
    console.print("[bold green]Login successful![/bold green] Token saved to ~/.orchestra/config.json")


@auth_app.command("logout")
def auth_logout() -> None:
    """Clear stored credentials."""
    config.clear()
    console.print("[dim]Credentials cleared.[/dim]")


@auth_app.command("whoami")
def auth_whoami() -> None:
    """Show the currently authenticated user."""
    _require_auth()
    try:
        user = _run(client.get("/auth/me"))
    except APIError as e:
        _handle_api_error(e)
        return

    table = Table(title="Current User", show_header=False, border_style="cyan")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    table.add_row("User ID", user.get("user_id", ""))
    table.add_row("Email", user.get("email", ""))
    table.add_row("Name", user.get("full_name", ""))
    table.add_row("Tenant", user.get("tenant_id", ""))
    table.add_row("Role", user.get("role", ""))
    table.add_row("API URL", config.get_api_url())
    console.print(table)


@auth_app.command("register")
def auth_register(
    email: str = typer.Option("", "--email", "-e", help="Email address"),
    password: str = typer.Option("", "--password", "-p", help="Password (min 8 chars)", hide_input=True),
    name: str = typer.Option("", "--name", "-n", help="Full name"),
    tenant: str = typer.Option("", "--tenant", "-t", help="Organization / tenant name"),
) -> None:
    """Register a new account and save the token."""
    if not email:
        email = Prompt.ask("[bold]Email[/bold]")
    if not password:
        password = Prompt.ask("[bold]Password[/bold] (min 8 chars)", password=True)
    if not name:
        name = Prompt.ask("[bold]Full name[/bold]")
    if not tenant:
        tenant = Prompt.ask("[bold]Organization name[/bold]")

    try:
        data = _run(client.post("/auth/register", json={
            "email": email, "password": password,
            "full_name": name, "tenant_name": tenant,
        }))
    except APIError as e:
        _handle_api_error(e)
        return

    config.set_token(data.get("access_token", ""))
    console.print("[bold green]Registration successful![/bold green] You are now logged in.")


# ===================================================================
#  campaign
# ===================================================================

@campaign_app.command("list")
def campaign_list() -> None:
    """List all campaigns for the authenticated tenant."""
    _require_auth()
    try:
        data = _run(client.get("/campaigns"))
    except APIError as e:
        _handle_api_error(e)
        return

    campaigns = data.get("campaigns", [])
    if not campaigns:
        console.print("[dim]No campaigns found. Create one with[/dim] [cyan]orchestra campaign create[/cyan]")
        return

    table = Table(title=f"Campaigns ({data.get('total', len(campaigns))})", border_style="blue")
    table.add_column("Name", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Platforms")
    table.add_column("Budget", justify="right")
    table.add_column("Spent", justify="right")
    table.add_column("ID", style="dim")

    status_colors = {
        "draft": "yellow", "active": "green", "paused": "red",
        "completed": "cyan", "archived": "dim",
    }

    for c in campaigns:
        st = c.get("status", "")
        color = status_colors.get(st, "white")
        table.add_row(
            c.get("name", ""),
            f"[{color}]{st}[/{color}]",
            ", ".join(c.get("platforms", [])) or "-",
            f"${c.get('budget', 0):,.2f}",
            f"${c.get('spent', 0):,.2f}",
            c.get("id", "")[:8],
        )

    console.print(table)


@campaign_app.command("create")
def campaign_create() -> None:
    """Interactively create a new campaign."""
    _require_auth()

    name = Prompt.ask("[bold]Campaign name[/bold]")
    description = Prompt.ask("[bold]Description[/bold] (optional)", default="")
    platforms_raw = Prompt.ask(
        "[bold]Platforms[/bold] (comma-separated, e.g. twitter,instagram)",
        default="",
    )
    budget_raw = Prompt.ask("[bold]Budget (USD)[/bold]", default="0")

    platforms = [p.strip() for p in platforms_raw.split(",") if p.strip()]
    try:
        budget = float(budget_raw)
    except ValueError:
        budget = 0.0

    payload: dict[str, Any] = {"name": name, "platforms": platforms, "budget": budget}
    if description:
        payload["description"] = description

    try:
        data = _run(client.post("/campaigns", json=payload))
    except APIError as e:
        _handle_api_error(e)
        return

    console.print(
        Panel(
            f"[bold green]Campaign created![/bold green]\n\n"
            f"  ID:        [cyan]{data.get('id', '')}[/cyan]\n"
            f"  Name:      {data.get('name', '')}\n"
            f"  Status:    {data.get('status', '')}\n"
            f"  Platforms: {', '.join(data.get('platforms', [])) or '-'}\n"
            f"  Budget:    ${data.get('budget', 0):,.2f}",
            title="New Campaign",
            border_style="green",
        )
    )


@campaign_app.command("get")
def campaign_get(
    campaign_id: str = typer.Argument(..., help="Campaign ID"),
) -> None:
    """Show detailed info for a single campaign."""
    _require_auth()
    try:
        data = _run(client.get(f"/campaigns/{campaign_id}"))
    except APIError as e:
        _handle_api_error(e)
        return

    lines = [
        f"  [bold]Name:[/bold]      {data.get('name', '')}",
        f"  [bold]Status:[/bold]    {data.get('status', '')}",
        f"  [bold]Platforms:[/bold] {', '.join(data.get('platforms', [])) or '-'}",
        f"  [bold]Budget:[/bold]    ${data.get('budget', 0):,.2f}",
        f"  [bold]Spent:[/bold]     ${data.get('spent', 0):,.2f}",
    ]
    if data.get("description"):
        lines.insert(1, f"  [bold]Desc:[/bold]      {data['description']}")

    posts = data.get("posts", [])
    if posts:
        lines.append(f"\n  [bold]Posts ({len(posts)}):[/bold]")
        for p in posts:
            lines.append(f"    [{p.get('platform', '?')}] {p.get('status', '')} -- {p.get('content', '')[:60]}")

    console.print(Panel("\n".join(lines), title=f"Campaign {data.get('id', '')[:8]}", border_style="blue"))


@campaign_app.command("launch")
def campaign_launch(campaign_id: str = typer.Argument(..., help="Campaign ID")) -> None:
    """Launch a draft/paused campaign."""
    _require_auth()
    try:
        data = _run(client.post(f"/campaigns/{campaign_id}/launch"))
    except APIError as e:
        _handle_api_error(e)
        return
    console.print(f"[bold green]Campaign launched![/bold green] Status: {data.get('status', '')}")


@campaign_app.command("pause")
def campaign_pause(campaign_id: str = typer.Argument(..., help="Campaign ID")) -> None:
    """Pause a running campaign."""
    _require_auth()
    try:
        data = _run(client.post(f"/campaigns/{campaign_id}/pause"))
    except APIError as e:
        _handle_api_error(e)
        return
    console.print(f"[yellow]Campaign paused.[/yellow] Status: {data.get('status', '')}")


# ===================================================================
#  analytics
# ===================================================================

@app.command()
def analytics(
    days: int = typer.Option(30, "--days", "-d", help="Date range in days"),
) -> None:
    """Fetch cross-platform analytics overview."""
    _require_auth()
    with console.status("[bold cyan]Fetching analytics...[/bold cyan]"):
        try:
            data = _run(client.get("/analytics/overview", params={"days": days}))
        except APIError as e:
            _handle_api_error(e)
            return

    # Totals
    totals_text = (
        f"  [bold]Impressions:[/bold]    {data.get('total_impressions', 0):,}\n"
        f"  [bold]Engagement:[/bold]     {data.get('total_engagement', 0):,}\n"
        f"  [bold]Clicks:[/bold]         {data.get('total_clicks', 0):,}\n"
        f"  [bold]Spend:[/bold]          ${data.get('total_spend', 0):,.2f}\n"
        f"  [bold]Avg Eng. Rate:[/bold]  {data.get('average_engagement_rate', 0):.2%}"
    )
    console.print(Panel(totals_text, title=f"Analytics Overview ({days}d)", border_style="cyan"))

    # Per-platform
    platforms = data.get("platforms", {})
    if platforms:
        table = Table(title="By Platform", border_style="blue")
        table.add_column("Platform", style="bold")
        table.add_column("Impressions", justify="right")
        table.add_column("Engagement", justify="right")
        table.add_column("Clicks", justify="right")
        table.add_column("Eng. Rate", justify="right")
        table.add_column("Spend", justify="right")

        for name, m in platforms.items():
            table.add_row(
                name,
                f"{m.get('impressions', 0):,}",
                f"{m.get('engagement', 0):,}",
                f"{m.get('clicks', 0):,}",
                f"{m.get('engagement_rate', 0):.2%}",
                f"${m.get('spend', 0):,.2f}",
            )
        console.print(table)

    # Insights & recommendations
    insights = data.get("insights", [])
    recs = data.get("recommendations", [])
    if insights or recs:
        parts: list[str] = []
        if insights:
            parts.append("[bold]Insights[/bold]")
            parts.extend(f"  {i+1}. {text}" for i, text in enumerate(insights))
        if recs:
            parts.append("\n[bold]Recommendations[/bold]")
            parts.extend(f"  {i+1}. {text}" for i, text in enumerate(recs))
        console.print(Panel("\n".join(parts), border_style="green"))


# ===================================================================
#  ask  -- the magic command
# ===================================================================

@app.command()
def ask(
    prompt: str = typer.Argument(..., help="Natural language instruction for the AI orchestrator"),
) -> None:
    """Send a natural-language instruction to the OrchestraAI agent."""
    _require_auth()

    console.print(f"\n[bold cyan]You:[/bold cyan] {prompt}\n")

    with console.status("[bold cyan]Thinking...[/bold cyan]"):
        try:
            data = _run(client.post("/orchestrator", json={"input": prompt}))
        except APIError as e:
            _handle_api_error(e)
            return

    # Intent
    intent = data.get("intent")
    if intent:
        console.print(f"[dim]Intent:[/dim] [bold]{intent}[/bold]")

    # Compliance
    compliance = data.get("compliance")
    if compliance:
        passed = compliance.get("approved", compliance.get("passed"))
        status_str = "[green]passed[/green]" if passed else "[red]blocked[/red]"
        console.print(f"[dim]Compliance:[/dim] {status_str}")
        flags = compliance.get("flags") or compliance.get("issues") or []
        for f in flags:
            console.print(f"  [yellow]- {f}[/yellow]")

    # Content
    content = data.get("content")
    if content:
        text = content.get("text") or content.get("content", "")
        if text:
            console.print(Panel(str(text), title="Generated Content", border_style="green"))
        variations = content.get("variations", [])
        for i, v in enumerate(variations, 1):
            console.print(f"\n[bold]Variation {i}:[/bold]\n{v}")

    # Analytics
    analytics_data = data.get("analytics")
    if analytics_data:
        console.print(Panel(str(analytics_data), title="Analytics", border_style="blue"))

    # Optimization
    optimization = data.get("optimization")
    if optimization:
        console.print(Panel(str(optimization), title="Optimization", border_style="magenta"))

    # Error
    error = data.get("error")
    if error:
        console.print(f"\n[bold red]Error:[/bold red] {error}")

    # Trace
    trace_id = data.get("trace_id")
    if trace_id:
        console.print(f"\n[dim]trace_id: {trace_id}[/dim]")

    console.print()


# ===================================================================
#  status  -- infrastructure health check
# ===================================================================

async def _check_service(name: str, check_fn) -> dict[str, Any]:  # noqa: ANN001
    try:
        result = await asyncio.wait_for(check_fn(), timeout=5.0)
        return {"name": name, "ok": True, "detail": result}
    except Exception as e:
        return {"name": name, "ok": False, "detail": str(e)}


async def _check_api() -> str:
    import httpx as _httpx
    base = config.get_api_url().replace("/api/v1", "")
    async with _httpx.AsyncClient(timeout=3.0) as c:
        resp = await c.get(f"{base}/health")
    return "healthy" if resp.status_code == 200 else f"status {resp.status_code}"


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


async def _check_ollama() -> str:
    import httpx as _httpx
    from orchestra.config import get_settings
    async with _httpx.AsyncClient(timeout=3.0) as c:
        resp = await c.get(f"{get_settings().ollama_base_url}/api/tags")
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
    return f"{len(models)} model(s)" if models else "running (no models)"


async def _run_all_checks() -> list[dict[str, Any]]:
    checks = [
        ("API Server", _check_api),
        ("PostgreSQL", _check_postgres),
        ("Redis", _check_redis),
        ("Ollama", _check_ollama),
    ]
    return list(await asyncio.gather(*[_check_service(n, fn) for n, fn in checks]))


@app.command()
def status() -> None:
    """Check health of all OrchestraAI infrastructure services."""
    console.print()
    results = _run(_run_all_checks())

    table = Table(title="OrchestraAI System Status", border_style="cyan")
    table.add_column("Service", style="bold")
    table.add_column("Status", justify="center")
    table.add_column("Detail")

    for r in results:
        icon = "[bold green]OK[/bold green]" if r["ok"] else "[bold red]FAIL[/bold red]"
        detail = str(r["detail"])[:80]
        table.add_row(r["name"], icon, detail)

    console.print(table)

    ok_count = sum(1 for r in results if r["ok"])
    total = len(results)
    if ok_count == total:
        console.print(f"\n[bold green]All {total} services operational.[/bold green]\n")
    else:
        console.print(f"\n[bold yellow]{ok_count}/{total} services operational.[/bold yellow]\n")


# ===================================================================
#  version
# ===================================================================

@app.command()
def version() -> None:
    """Show OrchestraAI version."""
    from orchestra import __version__
    console.print(f"[bold]OrchestraAI[/bold] v{__version__}")


# ===================================================================
#  config
# ===================================================================

@app.command("config")
def show_config() -> None:
    """Show current CLI configuration."""
    cfg = config.load()
    table = Table(title="CLI Config", show_header=False, border_style="cyan")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("API URL", cfg.get("api_url", ""))
    token = cfg.get("token", "")
    masked = f"{token[:12]}...{token[-4:]}" if len(token) > 20 else ("(set)" if token else "(empty)")
    table.add_row("Token", masked)
    table.add_row("Config file", str(config.CONFIG_FILE))
    console.print(table)


if __name__ == "__main__":
    app()
