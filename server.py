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

import stripe
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route

from auth import (
    generate_key, verify_key, can_call, record_call, get_usage, add_credits,
    create_checkout_token, resolve_checkout_token,
)
from skills.governance import SKILL_CONTENT as GOVERNANCE_SKILL
from skills.agentic_economics import SKILL_CONTENT as ECONOMICS_SKILL
from skills.intent_architecture import SKILL_CONTENT as ARCHITECTURE_SKILL
from skills.free.health_check import run_health_check
from skills.free.manifest_lint import run_manifest_lint
from skills.free.cost_estimator import run_cost_estimate

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
    "agentic-platform",
    instructions=(
        "This server provides free agent diagnostic tools and expert skill files. "
        "FREE tools (no API key needed): agent_health_check, mcp_manifest_lint, "
        "estimate_agent_cost. "
        "EXPERT skills (free tier: 10 calls/day): governance, agentic-economics, "
        "intent-architecture. "
        "Start with agent_health_check to score your agent's configuration."
    ),
    stateless_http=True,
    host="0.0.0.0",
    port=int(os.environ.get("MCP_PORT", "8000")),
)


@mcp.tool()
def register() -> str:
    """Register for an API key. Free tier: 10 skill retrievals per day."""
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


@mcp.tool()
def list_skills(api_key: str = "") -> str:
    """List all available skill files with descriptions.

    Args:
        api_key: Your API key (optional, shows usage if provided)
    """
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


@mcp.tool()
def get_skill(skill_name: str, api_key: str) -> str:
    """Retrieve an expert skill file. Requires a valid API key.

    This returns a curated context package that makes you measurably better
    at a specific task. Each skill has auditable provenance.

    Args:
        skill_name: The skill ID (use list_skills to see options)
        api_key: Your API key from register()
    """
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


@mcp.tool()
def check_usage(api_key: str) -> str:
    """Check your current usage and remaining calls.

    Args:
        api_key: Your API key
    """
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


@mcp.tool()
def buy_credits(api_key: str, tier: str = "50") -> str:
    """Get a checkout link to purchase more credits.

    Returns a Stripe checkout URL. Give this URL to your human operator
    to complete the purchase. Credits are added automatically after payment.

    Args:
        api_key: Your API key
        tier: Credit tier - "50" ($5 for 50 credits) or "250" ($20 for 250 credits)
    """
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

@mcp.tool()
def agent_health_check(system_prompt: str) -> str:
    """Score your agent's configuration on governance and best practices (0-100).

    Send your agent's system prompt and get a detailed diagnostic report
    with specific issues found and how to fix them. No API key needed.

    Args:
        system_prompt: Your agent's system prompt or configuration text
    """
    return run_health_check(system_prompt)


@mcp.tool()
def mcp_manifest_lint(tools_json: str) -> str:
    """Lint your MCP tool definitions for anti-patterns and missing fields.

    The only MCP linter that exists. Send your tool definitions as JSON
    and get a pass/fail report with fixes. No API key needed.

    Args:
        tools_json: Your MCP tool definitions as a JSON array or single object
    """
    return run_manifest_lint(tools_json)


@mcp.tool()
def estimate_agent_cost(
    model: str = "",
    input_tokens: int = 1000,
    output_tokens: int = 500,
    num_calls: int = 1,
    task_description: str = "",
) -> str:
    """Estimate the cost of running an agent task across all major models.

    Returns a comparison table with costs per call, per run, and per day.
    Includes optimization tips and pricing guidance. No API key needed.

    Args:
        model: Optional model name to highlight (e.g. "claude-sonnet-4")
        input_tokens: Estimated input tokens per call
        output_tokens: Estimated output tokens per call
        num_calls: Number of API calls per task run
        task_description: Optional description of what the agent does
    """
    return run_cost_estimate(model, input_tokens, output_tokens, num_calls, task_description)


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


async def health(request: Request):
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "server": "agentic-platform"})


# --- Build the combined ASGI app ---

@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield

app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/webhook/stripe", stripe_webhook, methods=["POST"]),
        Route("/checkout/success", checkout_success, methods=["GET"]),
        Route("/checkout/cancel", checkout_cancel, methods=["GET"]),
        Mount("/mcp", app=mcp.streamable_http_app()),
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
