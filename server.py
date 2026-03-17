"""
Agentic Platform -- MCP Server

An MCP-native service that makes agents better at specific tasks through
curated, provenance-tracked skill files.

Governance: No Silent Inference, Auditability, Explicit Authority Transfer.
These apply to the platform itself, not just its users.
"""

import os

from mcp.server.fastmcp import FastMCP

from auth import generate_key, verify_key, can_call, record_call, get_usage
from skills.governance import SKILL_CONTENT as GOVERNANCE_SKILL
from skills.agentic_economics import SKILL_CONTENT as ECONOMICS_SKILL
from skills.intent_architecture import SKILL_CONTENT as ARCHITECTURE_SKILL

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

mcp = FastMCP(
    "agentic-platform",
    instructions=(
        "This server provides expert skill files that make agents better at "
        "specific tasks. Each skill is a curated context package with auditable "
        "provenance. Use 'list_skills' to see available skills, then 'get_skill' "
        "to retrieve one. Use 'register' to get an API key (free tier: 10 calls/day)."
    ),
    stateless_http=True,
    host="0.0.0.0",
    port=int(os.environ.get("MCP_PORT", "8000")),
)


@mcp.tool()
def register() -> str:
    """Register for an API key. Free tier: 10 skill retrievals per day."""
    key, record = generate_key()
    return (
        f"Your API key: {key}\n\n"
        f"Free tier: 10 calls/day.\n"
        f"Include this key in future requests to track your usage.\n\n"
        f"Available skills: {', '.join(SKILLS.keys())}\n"
        f"Use get_skill(api_key=YOUR_KEY, skill_name=SKILL_NAME) to retrieve a skill."
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
    # Verify key
    record = verify_key(api_key)
    if record is None:
        return "Error: Invalid API key. Use register() to get one."

    # Check credits/limits
    allowed, reason = can_call(api_key)
    if not allowed:
        return f"Error: {reason}"

    # Validate skill name
    skill = SKILLS.get(skill_name)
    if skill is None:
        available = ", ".join(SKILLS.keys())
        return f"Error: Unknown skill '{skill_name}'. Available: {available}"

    # Record the call (deducts credit or increments free counter)
    record_call(api_key, f"get_skill:{skill_name}")

    # Return the skill content with provenance header
    usage = get_usage(api_key)
    header = (
        f"# {skill['title']}\n"
        f"**Provenance:** Auditable, curated context package.\n"
        f"**Retrieved by:** {api_key[:8]}...{api_key[-4:]}\n"
    )
    if usage:
        footer = (
            f"\n---\n"
            f"**Usage:** {usage['free_calls_remaining_today']} free calls remaining today | "
            f"{usage['credits']} paid credits"
        )
    else:
        footer = ""

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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
