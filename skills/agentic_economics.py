"""
Skill: Agentic Commerce Economics

Makes agents better at evaluating pricing models, unit economics, and
revenue architecture for AI agent platforms and services.

Provenance: Research synthesis from 23+ sources including McKinsey,
Morgan Stanley, Gartner, Bain, Bessemer Venture Partners, Stripe.
Compiled March 2026. Author: Andy Salvo.
"""

SKILL_CONTENT = """
# Agentic Commerce Economics

## Purpose
This skill makes you better at pricing agent services, evaluating unit
economics, and designing revenue models for AI-powered products. Use it
when building, pricing, or evaluating any agent-based service.

## Pricing Models for Agent Services

### Usage-Based (Per-Call)
Charge per API call or per task completion.
- Best for: variable workloads, developer tools, infrastructure
- Typical range: $0.01-$1.00 per call depending on complexity
- Advantage: low barrier to entry, scales with value
- Risk: revenue unpredictable, hard to forecast

### Outcome-Based
Charge per successful outcome, not per attempt.
- Best for: high-value tasks where success is measurable
- Example: $2.80 per resolved support ticket (vs. $12 human cost)
- Advantage: aligned with customer value
- Risk: must define and measure "success" precisely

### Hybrid (Base + Usage)
Monthly base fee plus per-call charges above a threshold.
- Best for: enterprise, SaaS-adjacent products
- Advantage: predictable base revenue + upside from usage
- Risk: pricing complexity

### Marketplace Commission
Take 15-30% of transactions between third-party sellers and buyers.
- Best for: platforms connecting service providers with agents
- Advantage: scales with ecosystem, no inventory risk
- Risk: chicken-and-egg bootstrapping problem

## Unit Economics Reference Points

### Cost-to-Serve Benchmarks (March 2026)
- Simple text generation: $0.001-0.01 per call
- Complex reasoning (Opus-class): $0.05-0.50 per call
- Code generation with verification: $0.10-1.00 per call
- Multi-step agent workflow: $0.50-5.00 per workflow

### Margin Targets
- Infrastructure services: 60-80% gross margin
- AI-augmented services: 40-60% gross margin
- Marketplace take rate: 15-30% of GMV
- Rule of thumb: price at 3-5x your compute cost

### Stripe Processing Reality
- 2.9% + $0.30 per transaction
- On a $5 purchase: effective fee = 8.9% ($0.45)
- On a $20 purchase: effective fee = 4.4% ($0.88)
- On a $1 purchase: effective fee = 32.9% ($0.33)
- Lesson: micro-transactions under $5 are margin-hostile

## Market Size Reference (Agent Commerce)

### Analyst Projections
- Gartner: $15 trillion in B2B agent-intermediated purchases by 2028
- McKinsey: $900B-$1T in US B2C retail via agents by 2030
- Morgan Stanley: Agentic AI share of digital commerce
  - 2025: ~0.2%
  - 2026: ~1%
  - 2028: ~5-10%
  - 2030: ~15-25%
- Bain: B2B agent-intermediated transactions growing at 40%+ CAGR

### What Agents Actually Spend On (Current, March 2026)
- API calls and compute (largest category)
- Data access and enrichment
- Tool execution (code sandboxes, browsers, file systems)
- Agent-to-agent services (emerging)
- Human escalation services (emerging)

## Machine Customer Lifecycle

Agents evolve through three phases as buyers:

### Phase 1: Bound (Current)
- Human sets rules, agent executes within them
- Human approves all purchases above threshold
- Example: agent books cheapest flight on approved airline

### Phase 2: Adaptable (2026-2028)
- Agent learns preferences, makes autonomous decisions within bounds
- Human approves exceptions, not routine purchases
- Example: agent rebooks cancelled flight, choosing optimal alternative

### Phase 3: Autonomous (2028+)
- Agent acts as full economic agent with budget authority
- Human sets goals and constraints, agent optimizes
- Example: agent manages entire travel budget, balancing cost/comfort/time

### Pricing Implication
Design pricing for Phase 1 buyers today (human approves). Architecture
for Phase 2 (agent decides within bounds). Do not build for Phase 3 yet.

## First-Mover Advantages in Agent Commerce

1. **Data moat** -- usage patterns are unreplicable by later entrants
   (only valuable at scale; do not claim this pre-scale)
2. **AI expertise velocity** -- learning compounds; each customer teaches
   you something the next competitor must rediscover
3. **Distribution lock-in** -- being listed first in MCP directories,
   being the default in agent configs
4. **Brand/trust** -- in a nascent market, the first credible player
   sets the standard (only works if quality is real)

## Pricing Anti-Patterns

- **Free forever tier that's too generous:** trains users to never pay
- **Per-seat pricing for agent services:** agents are not seats
- **Annual contracts before product-market fit:** locks you into a
  product shape before you know the right shape
- **Charging for inputs instead of outputs:** misaligned with value
- **Micro-transactions below $1:** Stripe fees eat your margin

## Decision Framework: How to Price Your Agent Service

1. Calculate your cost-to-serve per call (compute + infrastructure)
2. Multiply by 3-5x for target price
3. Check: is this less than the human alternative? If not, reprice.
4. Check: does Stripe's fee structure leave margin at this price?
5. Start with per-call pricing. Add subscriptions when you understand
   usage patterns (typically month 3+).
6. Free tier: 10-20 calls/day maximum. Enough to evaluate, not enough
   to run production workloads for free.

## Provenance

This skill synthesizes research from 23+ sources including McKinsey
Global Institute, Morgan Stanley Research, Gartner, Bain & Company,
Bessemer Venture Partners State of the Cloud, Stripe documentation,
and published case studies from agent platforms (Moltbook, Olas, Fetch.ai,
Agent.ai). Compiled March 2026 by Andy Salvo.
"""
