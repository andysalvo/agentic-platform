# Agentic Platform

[![agentic-platform MCP server](https://glama.ai/mcp/servers/andysalvo/agentic-platform/badges/card.svg)](https://glama.ai/mcp/servers/andysalvo/agentic-platform)

**The only MCP linter that exists.** Plus free governance scoring and cost estimation for AI agents.

Validate your MCP tool definitions, score your agent's system prompt on governance best practices (0-100), and compare costs across all major models. No API key needed.

## Installation

### Remote MCP Server (Hosted)

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "agentic-platform": {
      "url": "http://165.22.46.178:8080/mcp"
    }
  }
}
```

### Claude Code

```bash
claude mcp add agentic-platform --transport http http://165.22.46.178:8080/mcp
```

### Docker

```bash
docker run -p 8080:8080 ghcr.io/andysalvo/agentic-platform:latest
```

Works with Claude Desktop, Claude Code, VS Code, Cursor, Cline, and any MCP-compatible client.

## Free Tools (No API Key Needed)

| Tool | What It Does |
|------|-------------|
| `mcp_manifest_lint` | **The only MCP linter.** Validate your tool definitions for anti-patterns, missing fields, bad descriptions, and schema issues. Pass/fail report with fixes. |
| `agent_health_check` | Score your agent's system prompt on governance and best practices (0-100). Detailed diagnostic with specific issues and remediation. |
| `estimate_agent_cost` | Compare costs across Claude, GPT, Gemini, and other models. Per-call, per-run, and per-day breakdown with optimization tips. |

## Expert Skills (Free Tier: 10 Calls/Day)

| Skill | Description |
|-------|-------------|
| `governance` | Design agent systems that preserve human authority. 3 core invariants, Coupled Authority Phenomenon, 14 forbidden failure modes. |
| `agentic-economics` | Pricing models, unit economics, and revenue architecture for AI agent platforms. Market projections, cost-to-serve benchmarks (March 2026). |
| `intent-architecture` | Build deterministic, auditable systems. Append-only decision logs, 9 system invariants, implementation patterns, embodiment tests. |

## Quick Start

```
1. mcp_manifest_lint(tools_json='[{"name":"my_tool","description":"Does something"}]')
   -> Pass/fail report with specific fixes

2. agent_health_check(system_prompt="Your agent's system prompt here")
   -> Score 0-100 with detailed diagnostic

3. estimate_agent_cost(model="claude-sonnet-4", input_tokens=2000, output_tokens=1000, num_calls=10)
   -> Cost comparison table across all major models
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

## Keywords

MCP server, MCP linter, MCP validator, MCP manifest lint, agent governance, agent health check, agent cost estimator, AI agent tools, Model Context Protocol, MCP tool validation, agent diagnostics, governance scoring

## License

MIT

## Built By

[Andy Salvo](https://github.com/andysalvo)
