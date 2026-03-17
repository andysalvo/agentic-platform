# Agentic Platform

Expert skill files that make AI agents measurably better at specific tasks.

An MCP server providing curated context packages with auditable provenance.

## Available Skills

| Skill | Description |
|-------|-------------|
| `governance` | Design agent systems that preserve human authority. Governance invariants, Coupled Authority Phenomenon, forbidden failure modes. |
| `agentic-economics` | Pricing models, unit economics, and revenue architecture for AI agent platforms. Market projections, cost benchmarks. |
| `intent-architecture` | Build deterministic, auditable systems. Append-only decision logs, 9 invariants, 14 forbidden failure modes, embodiment tests. |

## Quick Start

### Connect via MCP

```json
{
  "mcpServers": {
    "agentic-platform": {
      "url": "http://165.22.46.178:8080/mcp"
    }
  }
}
```

### Use the Tools

1. `register()` -- get a free API key (10 calls/day)
2. `list_skills(api_key)` -- see the catalog
3. `get_skill(skill_name, api_key)` -- retrieve a skill
4. `check_usage(api_key)` -- see your remaining calls

## Provenance

Every skill file has traceable origin. Content is derived from published research frameworks, curated source collections, and validated methodology. No generic prompts. No unattributed content.

## Governance

This platform operates under three core invariants:

1. **No Silent Inference** -- no inferring or reinterpreting input without explicit documentation
2. **Auditability at the Decision Level** -- every state change traceable to a decision
3. **Explicit Authority Transfer** -- all commitments require explicit authorization

These apply to the platform itself, not just its users.

## Pricing

- **Free:** 10 skill retrievals per day
- **Paid:** Credit packs via Stripe (coming soon)

## Built By

Andy Salvo
