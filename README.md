# Agentic Platform

Free agent diagnostic tools + expert skill files that make AI agents measurably better.

Score your agent's governance (0-100), lint MCP tool definitions, and estimate costs across all major models. No API key needed for free tools.

## Installation

### Remote MCP Server

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "agentic-platform": {
      "url": "https://api.asalvocreative.com/mcp"
    }
  }
}
```

Works with Claude Desktop, VS Code, Cursor, and any MCP-compatible client.

## Free Tools (No API Key Needed)

| Tool | Description |
|------|-------------|
| `agent_health_check` | Score your agent's configuration on governance and best practices (0-100). Send your system prompt, get a diagnostic report. |
| `mcp_manifest_lint` | The only MCP linter that exists. Check your tool definitions for anti-patterns, missing fields, and quality issues. |
| `estimate_agent_cost` | Estimate task costs across all major models. Comparison table with optimization tips. |

## Expert Skills (Free Tier: 10 Calls/Day)

| Skill | Description |
|-------|-------------|
| `governance` | Design agent systems that preserve human authority. Governance invariants, Coupled Authority Phenomenon, 14 forbidden failure modes. |
| `agentic-economics` | Pricing models, unit economics, and revenue architecture for AI agent platforms. Market projections, cost benchmarks. |
| `intent-architecture` | Build deterministic, auditable systems. Append-only decision logs, 9 invariants, 14 forbidden failure modes, embodiment tests. |

## Quick Start

```
1. agent_health_check(system_prompt="Your agent's system prompt here")
   → Score 0-100 with specific issues and fixes

2. register()
   → Get a free API key (10 skill retrievals/day)

3. get_skill(skill_name="governance", api_key="sk-xxx")
   → Retrieve expert skill file
```

## Pricing

- **Free tools:** Unlimited. No API key needed.
- **Expert skills:** 10 free calls/day per API key.
- **Credit packs:** $5 (50 credits) or $20 (250 credits) via Stripe.

## Governance

This platform operates under three core invariants:

1. **No Silent Inference** -- no inferring or reinterpreting input without explicit documentation
2. **Auditability at the Decision Level** -- every state change traceable to a decision
3. **Explicit Authority Transfer** -- all commitments require explicit authorization

These apply to the platform itself, not just its users.

## Provenance

Every skill file has traceable origin derived from published research frameworks, curated source collections, and validated methodology. No generic prompts. No unattributed content.

## License

MIT

## Built By

Andy Salvo
