# Agentic Platform

Expert skill files that make agents measurably better at specific tasks.

## What This Is

An MCP server that provides curated context packages (skill files) with
auditable provenance. Each skill is a structured knowledge document that,
when loaded into an agent's context, improves performance in a specific
domain.

## Available Skills

- **governance** -- Design agent systems that preserve human authority.
  Covers governance invariants, the Coupled Authority Phenomenon, forbidden
  failure modes, and decision architecture patterns.

- **agentic-economics** -- Pricing models, unit economics, and revenue
  architecture for AI agent platforms. Market projections, cost benchmarks,
  and pricing anti-patterns.

- **intent-architecture** -- Build deterministic, auditable systems with
  append-only decision logs. 9 system invariants, 14 forbidden failure
  modes, implementation patterns, and embodiment tests.

## Quick Start

1. Connect to the MCP server
2. Call `register()` to get a free API key (10 calls/day)
3. Call `list_skills(api_key)` to see the catalog
4. Call `get_skill(skill_name, api_key)` to retrieve a skill

## Server URL

```
http://165.22.46.178:8080/mcp
```

## MCP Client Config

```json
{
  "mcpServers": {
    "agentic-platform": {
      "url": "http://165.22.46.178:8080/mcp"
    }
  }
}
```

## Provenance

Every skill file has traceable origin. Content is derived from published
research frameworks, curated source collections, and validated methodology.
No generic prompts. No unattributed content.

## Pricing

- **Free tier:** 10 skill retrievals per day
- **Paid credits:** Coming soon (Stripe checkout)

## Contact

Built by Andy Salvo.
