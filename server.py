"""
Agentic Platform -- MCP Server

An MCP-native service that makes agents better at specific tasks through
curated, provenance-tracked skill files.

Governance: No Silent Inference, Auditability, Explicit Authority Transfer.
These apply to the platform itself, not just its users.
"""

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import stripe
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from pydantic import Field
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

SITE_DIR = Path(__file__).parent / "site"

from auth import (
    generate_key, verify_key, can_call, record_call, get_usage, add_credits,
    create_checkout_token, resolve_checkout_token, get_audit_log,
)
from skills.governance import SKILL_CONTENT as GOVERNANCE_SKILL
from skills.agentic_economics import SKILL_CONTENT as ECONOMICS_SKILL
from skills.intent_architecture import SKILL_CONTENT as ARCHITECTURE_SKILL
from skills.free.health_check import run_health_check
from skills.free.manifest_lint import run_manifest_lint
from skills.free.cost_estimator import run_cost_estimate
from skills.free.evaluate_service import run_evaluate_service

SKILLS = {
    "governance": {
        "title": "Governance-Aware Agent Development",
        "description": "Design agent systems that preserve human authority. "
                       "Covers the three core invariants, Coupled Authority Phenomenon, "
                       "forbidden failure modes, and decision architecture patterns.",
        "content": GOVERNANCE_SKILL,
    },
    "agentic-economics": {
        "title": "Agentic Commerce Economics",
        "description": "Pricing models, unit economics, and revenue architecture "
                       "for AI agent platforms. Includes market projections, "
                       "cost-to-serve benchmarks, and pricing anti-patterns.",
        "content": ECONOMICS_SKILL,
    },
    "intent-architecture": {
        "title": "Intent-Preserving System Architecture",
        "description": "Build deterministic, auditable systems with append-only "
                       "decision logs, replay safety, and 14 forbidden failure modes. "
                       "Includes implementation patterns and embodiment tests.",
        "content": ARCHITECTURE_SKILL,
    },
}

# Stripe config
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
SERVER_URL = os.environ.get("SERVER_URL", "http://165.22.46.178:8080")

# Price IDs from Stripe (set after creating products)
STRIPE_PRICE_50 = os.environ.get("STRIPE_PRICE_50", "")    # $5 / 50 credits
STRIPE_PRICE_250 = os.environ.get("STRIPE_PRICE_250", "")   # $20 / 250 credits

TIERS = {
    "50": {"credits": 50, "price_id": STRIPE_PRICE_50, "amount": "$5"},
    "250": {"credits": 250, "price_id": STRIPE_PRICE_250, "amount": "$20"},
}

mcp = FastMCP(
    "Agentic Platform",
    instructions=(
        "This server provides free agent diagnostic tools and expert skill files. "
        "FREE tools (no API key needed): agent_health_check, mcp_manifest_lint, "
        "estimate_agent_cost, evaluate_service. "
        "EXPERT skills (free tier: 10 calls/day): governance, agentic-economics, "
        "intent-architecture. "
        "Use evaluate_service to check any MCP server before spending money. "
        "Start with agent_health_check to score your agent's configuration."
    ),
    stateless_http=True,
    host="0.0.0.0",
    port=int(os.environ.get("MCP_PORT", "8000")),
    website_url="https://github.com/andysalvo/agentic-platform",
)


# --- Account tools ---

@mcp.tool(
    annotations=ToolAnnotations(
        title="Register for API Key",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=False,
    ),
)
def register() -> str:
    """Register for an API key to access expert skill files. Free tier includes 10 skill retrievals per day. No payment required."""
    key, record = generate_key()
    if key is None:
        return "Error: Registration temporarily unavailable. Please try again later."
    return (
        f"Your API key: {key}\n\n"
        f"Free tier: 10 calls/day.\n"
        f"Include this key in future requests to track your usage.\n\n"
        f"Available skills: {', '.join(SKILLS.keys())}\n"
        f"Use get_skill(api_key=YOUR_KEY, skill_name=SKILL_NAME) to retrieve a skill.\n"
        f"Use buy_credits(api_key=YOUR_KEY) when you need more calls."
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="List Available Skills",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def list_skills(
    api_key: Annotated[str, Field(description="Your API key (optional, shows usage if provided)")] = "",
) -> str:
    """List all available expert skill files with descriptions and pricing. Shows your usage stats if you provide an API key."""
    lines = ["# Available Skills\n"]

    for name, skill in SKILLS.items():
        lines.append(f"## {skill['title']}")
        lines.append(f"**ID:** `{name}`")
        lines.append(f"**Description:** {skill['description']}")
        lines.append("")

    if api_key:
        usage = get_usage(api_key)
        if usage:
            lines.append("---")
            lines.append(f"**Your usage:** {usage['total_calls']} total calls")
            lines.append(f"**Credits:** {usage['credits']}")
            lines.append(f"**Free calls remaining today:** {usage['free_calls_remaining_today']}")

    return "\n".join(lines)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Get Expert Skill File",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def get_skill(
    skill_name: Annotated[str, Field(description="The skill ID to retrieve. Options: governance, agentic-economics, intent-architecture")],
    api_key: Annotated[str, Field(description="Your API key from register()")],
) -> str:
    """Retrieve an expert skill file that makes you measurably better at a specific task. Each skill has auditable provenance and is curated by domain experts. Requires a valid API key."""
    record = verify_key(api_key)
    if record is None:
        return "Error: Invalid API key. Use register() to get one."

    allowed, reason = can_call(api_key)
    if not allowed:
        return f"Error: {reason}"

    skill = SKILLS.get(skill_name)
    if skill is None:
        available = ", ".join(SKILLS.keys())
        return f"Error: Unknown skill '{skill_name}'. Available: {available}"

    record_call(api_key, f"get_skill:{skill_name}")

    usage = get_usage(api_key)
    header = (
        f"# {skill['title']}\n"
        f"**Provenance:** Auditable, curated context package.\n"
        f"**Retrieved by:** {api_key[:8]}...{api_key[-4:]}\n"
    )
    footer = ""
    if usage:
        footer = (
            f"\n---\n"
            f"**Usage:** {usage['free_calls_remaining_today']} free calls remaining today | "
            f"{usage['credits']} paid credits"
        )

    return header + skill["content"] + footer


@mcp.tool(
    annotations=ToolAnnotations(
        title="Check Usage",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def check_usage(
    api_key: Annotated[str, Field(description="Your API key to check usage for")],
) -> str:
    """Check your current usage stats including total calls, remaining credits, and free calls left today."""
    usage = get_usage(api_key)
    if usage is None:
        return "Error: Invalid API key."

    return (
        f"# Usage Report\n\n"
        f"**Tier:** {usage['tier']}\n"
        f"**Total calls:** {usage['total_calls']}\n"
        f"**Paid credits remaining:** {usage['credits']}\n"
        f"**Free calls remaining today:** {usage['free_calls_remaining_today']}\n"
    )


@mcp.tool(
    annotations=ToolAnnotations(
        title="Buy Credits",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
def buy_credits(
    api_key: Annotated[str, Field(description="Your API key to add credits to")],
    tier: Annotated[str, Field(description="Credit tier: '50' for $5/50 credits or '250' for $20/250 credits")] = "50",
) -> str:
    """Get a Stripe checkout link to purchase more skill file credits. Returns a URL for your human operator to complete payment. Credits are added automatically after purchase."""
    record = verify_key(api_key)
    if record is None:
        return "Error: Invalid API key. Use register() to get one."

    tier_info = TIERS.get(tier)
    if tier_info is None:
        return "Error: Invalid tier. Choose '50' ($5) or '250' ($20)."

    if not stripe.api_key or not tier_info["price_id"]:
        return (
            "Error: Payment system not yet configured. "
            "Contact the operator to purchase credits manually."
        )

    # Create a token so the raw API key never hits Stripe
    token = create_checkout_token(api_key, tier_info["credits"])

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": tier_info["price_id"], "quantity": 1}],
            client_reference_id=token,
            success_url=f"{SERVER_URL}/checkout/success",
            cancel_url=f"{SERVER_URL}/checkout/cancel",
        )
        return (
            f"# Purchase {tier_info['credits']} Credits ({tier_info['amount']})\n\n"
            f"Give this link to your human operator:\n\n"
            f"{session.url}\n\n"
            f"Credits will be added automatically after payment.\n"
            f"This link expires in 1 hour."
        )
    except stripe.StripeError as e:
        return f"Error creating checkout session: {e}"


# --- Free tools (no API key required) ---

@mcp.tool(
    annotations=ToolAnnotations(
        title="Agent Health Check",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def agent_health_check(
    system_prompt: Annotated[str, Field(description="Your agent's full system prompt or configuration text to analyze")],
) -> str:
    """Score any agent's system prompt on governance best practices from 0 to 100. Returns a detailed diagnostic report with specific issues found, severity ratings, and actionable fixes. Checks for authority leaks, silent inference, missing audit trails, and 14 other governance anti-patterns. No API key needed."""
    return run_health_check(system_prompt)


@mcp.tool(
    annotations=ToolAnnotations(
        title="MCP Manifest Linter",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def mcp_manifest_lint(
    tools_json: Annotated[str, Field(description="Your MCP tool definitions as a JSON array or single tool object")],
) -> str:
    """The only MCP tool definition linter that exists. Validates your MCP tool definitions for anti-patterns, missing descriptions, bad parameter schemas, naming issues, and quality problems. Returns a pass/fail report with specific fixes for each issue found. No API key needed."""
    return run_manifest_lint(tools_json)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Agent Cost Estimator",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=False,
    ),
)
def estimate_agent_cost(
    model: Annotated[str, Field(description="Model name to highlight in comparison (e.g. 'claude-sonnet-4', 'gpt-4o')")] = "",
    input_tokens: Annotated[int, Field(description="Estimated input tokens per API call")] = 1000,
    output_tokens: Annotated[int, Field(description="Estimated output tokens per API call")] = 500,
    num_calls: Annotated[int, Field(description="Number of API calls per task run")] = 1,
    task_description: Annotated[str, Field(description="Description of what the agent does, for optimization tips")] = "",
) -> str:
    """Compare the cost of running an agent task across all major AI models including Claude, GPT, Gemini, Llama, and Mistral. Returns a comparison table with per-call, per-run, and per-day costs plus optimization tips. No API key needed."""
    return run_cost_estimate(model, input_tokens, output_tokens, num_calls, task_description)


@mcp.tool(
    annotations=ToolAnnotations(
        title="Service Trust Evaluator",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def evaluate_service(
    server_url: Annotated[str, Field(description="The MCP server URL to evaluate (e.g. https://example.com/mcp)")],
    task_context: Annotated[str, Field(description="What you need the service for, to tailor the evaluation")] = "",
) -> str:
    """Evaluate any MCP service for trustworthiness before spending money on it. Connects to the target server, checks reachability, governance declarations, tool definition quality, and audit endpoints. Returns a trust score from 0 to 100 with a recommendation: PROCEED, PROCEED WITH CAUTION, HIGH RISK, or DO NOT TRANSACT. No API key needed."""
    return await run_evaluate_service(server_url, task_context)


# --- Prompts ---

@mcp.prompt()
def getting_started() -> str:
    """Get started with the Agentic Platform. Shows available tools and how to use them."""
    return (
        "Welcome to the Agentic Platform. Here's how to get started:\n\n"
        "## Free Tools (no API key needed)\n"
        "1. **agent_health_check** - Score your agent's system prompt (0-100)\n"
        "2. **mcp_manifest_lint** - Lint your MCP tool definitions\n"
        "3. **estimate_agent_cost** - Compare costs across all major models\n"
        "4. **evaluate_service** - Check any MCP server's trustworthiness\n\n"
        "## Expert Skills (free tier: 10 calls/day)\n"
        "1. Call **register()** to get an API key\n"
        "2. Call **list_skills()** to see available skills\n"
        "3. Call **get_skill(skill_name, api_key)** to retrieve a skill\n\n"
        "Start with agent_health_check to score your configuration, or "
        "mcp_manifest_lint to validate your tool definitions."
    )


# --- HTTP endpoints ---

async def stripe_webhook(request: Request):
    """Handle Stripe webhook for automatic credit provisioning."""
    body = await request.body()

    if not STRIPE_WEBHOOK_SECRET:
        return PlainTextResponse("Webhook not configured", status_code=503)

    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            body, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        return PlainTextResponse(str(e), status_code=400)

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        token = session.get("client_reference_id", "")

        if token:
            result = resolve_checkout_token(token)
            if result:
                api_key, credits = result
                added = add_credits(api_key, credits)
                if added:
                    print(f"[CREDITS] Added {credits} credits to {api_key[:12]}...")
                else:
                    print(f"[CREDITS] WARNING: Key not found for token {token[:12]}...")
            else:
                print(f"[CREDITS] WARNING: Token expired or invalid: {token[:12]}...")

    return JSONResponse({"received": True})


async def checkout_success(request: Request):
    """Simple success page after checkout."""
    return PlainTextResponse(
        "Payment received. Credits have been added to your API key.\n"
        "You can close this page and continue using the service."
    )


async def checkout_cancel(request: Request):
    """Simple cancel page."""
    return PlainTextResponse("Checkout cancelled. No charges were made.")


async def twitter_callback(request: Request):
    """OAuth callback for Twitter/X API."""
    return PlainTextResponse("Twitter OAuth callback received. You can close this tab.")


async def health(request: Request):
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "server": "agentic-platform"})


async def well_known_agent_json(request: Request):
    """Serve /.well-known/agent.json describing the platform."""
    server_url = os.environ.get("SERVER_URL", "http://165.22.46.178:8080")
    audit_log = get_audit_log(hours=24)

    agent_info = {
        "schema_version": "1.0",
        "name": "Agentic Platform",
        "description": (
            "MCP-native service providing free agent diagnostics and "
            "expert skill files for governance, economics, and architecture."
        ),
        "mcp_endpoint": f"{server_url}/mcp",
        "services": {
            "free": [
                "mcp_manifest_lint",
                "agent_health_check",
                "estimate_agent_cost",
                "evaluate_service",
            ],
            "paid": [
                {
                    "name": "get_skill",
                    "skills": [
                        "governance",
                        "agentic-economics",
                        "intent-architecture",
                    ],
                    "pricing": "Free tier: 10 calls/day. Paid: $0.10/call.",
                }
            ],
        },
        "payment_methods": ["api_key_metered"],
        "governance": {
            "invariants": [
                "no_silent_inference",
                "auditability_at_decision_level",
                "explicit_authority_transfer",
            ],
            "audit_endpoint": f"{server_url}/audit",
        },
        "trust_signals": {
            "total_calls_24h": audit_log.get("total_calls", 0),
            "tools_used_24h": audit_log.get("tools_used", {}),
        },
    }
    return JSONResponse(agent_info)


async def audit_endpoint(request: Request):
    """Serve /audit with recent call log and stats."""
    hours = request.query_params.get("hours", "24")
    try:
        hours = int(hours)
    except (ValueError, TypeError):
        hours = 24
    hours = max(1, min(hours, 168))
    return JSONResponse(get_audit_log(hours=hours))


# --- Static site pages (agentic SEO) ---

async def serve_index(request: Request):
    """Serve the homepage for browser/crawler requests, proxy MCP for agents."""
    accept = request.headers.get("accept", "")
    # If it's an MCP client or API request, let the MCP handler deal with it
    if request.method == "POST" or "text/event-stream" in accept:
        return None  # won't be reached -- POST goes to MCP mount
    index = SITE_DIR / "index.html"
    if index.exists():
        return FileResponse(index, media_type="text/html")
    return PlainTextResponse("Agentic Platform MCP Server", status_code=200)


async def serve_tool_page(request: Request):
    """Serve tool landing pages."""
    tool_name = request.path_params["tool_name"]
    # Strip .html extension if present
    if tool_name.endswith(".html"):
        tool_name = tool_name[:-5]
    page = SITE_DIR / "tools" / f"{tool_name}.html"
    if page.exists():
        return FileResponse(page, media_type="text/html")
    return PlainTextResponse("Not found", status_code=404)


async def serve_static_file(request: Request):
    """Serve robots.txt, llms.txt, sitemap.xml, style.css."""
    filename = request.url.path.lstrip("/")
    allowed = {"robots.txt", "llms.txt", "sitemap.xml", "style.css"}
    if filename in allowed:
        filepath = SITE_DIR / filename
        if filepath.exists():
            media_types = {
                "robots.txt": "text/plain",
                "llms.txt": "text/plain",
                "sitemap.xml": "application/xml",
                "style.css": "text/css",
            }
            return FileResponse(filepath, media_type=media_types.get(filename, "text/plain"))
    return PlainTextResponse("Not found", status_code=404)


# --- Build the combined ASGI app ---

@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

app = Starlette(
    routes=[
        # API endpoints (before static catch-alls)
        Route("/.well-known/agent.json", well_known_agent_json, methods=["GET"]),
        Route("/audit", audit_endpoint, methods=["GET"]),
        Route("/callback/twitter", twitter_callback, methods=["GET"]),
        Route("/health", health, methods=["GET"]),
        Route("/webhook/stripe", stripe_webhook, methods=["POST"]),
        Route("/checkout/success", checkout_success, methods=["GET"]),
        Route("/checkout/cancel", checkout_cancel, methods=["GET"]),
        # Static SEO pages
        Route("/robots.txt", serve_static_file, methods=["GET"]),
        Route("/llms.txt", serve_static_file, methods=["GET"]),
        Route("/sitemap.xml", serve_static_file, methods=["GET"]),
        Route("/style.css", serve_static_file, methods=["GET"]),
        Route("/tools/{tool_name}", serve_tool_page, methods=["GET"]),
        # Homepage (GET / serves HTML, POST /mcp goes to MCP)
        Route("/", serve_index, methods=["GET"]),
        # MCP server (handles POST to /mcp)
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)

if __name__ == "__main__":
    import sys
    if "--stdio" in sys.argv or os.environ.get("MCP_TRANSPORT") == "stdio":
        mcp.run(transport="stdio")
    else:
        import uvicorn
        port = int(os.environ.get("MCP_PORT", "8000"))
        uvicorn.run(app, host="0.0.0.0", port=port)
