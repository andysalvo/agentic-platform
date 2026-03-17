"""
Free Tool: Agent Cost Estimator

Estimates the cost of running an agent task across different models.
Includes cost-optimization suggestions.

No API key required. No inference costs. Static pricing data.
Pricing data last updated: March 2026.
"""

# Pricing per 1M tokens (input/output) in USD -- March 2026
MODEL_PRICING = {
    "claude-opus-4": {"input": 15.00, "output": 75.00, "provider": "Anthropic", "tier": "premium"},
    "claude-sonnet-4": {"input": 3.00, "output": 15.00, "provider": "Anthropic", "tier": "standard"},
    "claude-haiku-4": {"input": 0.80, "output": 4.00, "provider": "Anthropic", "tier": "fast"},
    "gpt-4.1": {"input": 2.00, "output": 8.00, "provider": "OpenAI", "tier": "standard"},
    "gpt-4.1-mini": {"input": 0.40, "output": 1.60, "provider": "OpenAI", "tier": "fast"},
    "gpt-4.1-nano": {"input": 0.10, "output": 0.40, "provider": "OpenAI", "tier": "ultra-fast"},
    "gemini-2.5-pro": {"input": 1.25, "output": 10.00, "provider": "Google", "tier": "standard"},
    "gemini-2.5-flash": {"input": 0.15, "output": 0.60, "provider": "Google", "tier": "fast"},
    "llama-3.1-405b": {"input": 3.00, "output": 3.00, "provider": "Meta (hosted)", "tier": "standard"},
    "llama-3.1-70b": {"input": 0.60, "output": 0.60, "provider": "Meta (hosted)", "tier": "fast"},
    "llama-3.1-8b": {"input": 0.05, "output": 0.05, "provider": "Meta (hosted)", "tier": "ultra-fast"},
    "mistral-large": {"input": 2.00, "output": 6.00, "provider": "Mistral", "tier": "standard"},
    "deepseek-v3": {"input": 0.27, "output": 1.10, "provider": "DeepSeek", "tier": "fast"},
    "deepseek-r1": {"input": 0.55, "output": 2.19, "provider": "DeepSeek", "tier": "standard"},
}


def run_cost_estimate(
    model: str = "",
    input_tokens: int = 1000,
    output_tokens: int = 500,
    num_calls: int = 1,
    task_description: str = "",
) -> str:
    """Estimate agent task costs across models."""

    if input_tokens <= 0:
        input_tokens = 1000
    if output_tokens <= 0:
        output_tokens = 500
    if num_calls <= 0:
        num_calls = 1

    lines = [
        "# Agent Cost Estimate",
        "",
    ]

    if task_description:
        lines.append(f"**Task:** {task_description}")
        lines.append("")

    lines.extend([
        f"**Input tokens:** {input_tokens:,}",
        f"**Output tokens:** {output_tokens:,}",
        f"**Calls per run:** {num_calls}",
        f"**Total tokens per run:** {(input_tokens + output_tokens) * num_calls:,}",
        "",
        "---",
        "",
        "## Cost Comparison",
        "",
        "| Model | Provider | Tier | Cost/Call | Cost/Run | Cost/Day (50 runs) |",
        "|-------|----------|------|----------|----------|-------------------|",
    ])

    costs = []
    for model_name, pricing in MODEL_PRICING.items():
        cost_input = (input_tokens / 1_000_000) * pricing["input"]
        cost_output = (output_tokens / 1_000_000) * pricing["output"]
        cost_per_call = cost_input + cost_output
        cost_per_run = cost_per_call * num_calls
        cost_per_day = cost_per_run * 50

        costs.append((model_name, pricing, cost_per_call, cost_per_run, cost_per_day))

    # Sort by cost per run
    costs.sort(key=lambda x: x[3])

    for model_name, pricing, cpc, cpr, cpd in costs:
        highlight = " **" if model and model.lower() in model_name.lower() else ""
        lines.append(
            f"| {highlight}{model_name}{highlight} | {pricing['provider']} | "
            f"{pricing['tier']} | ${cpc:.4f} | ${cpr:.4f} | ${cpd:.2f} |"
        )

    # Cheapest and most expensive
    cheapest = costs[0]
    most_expensive = costs[-1]
    savings = most_expensive[4] - cheapest[4]

    lines.extend([
        "",
        "---",
        "",
        "## Optimization Tips",
        "",
        f"- **Cheapest option:** {cheapest[0]} at ${cheapest[3]:.4f}/run",
        f"- **Most expensive:** {most_expensive[0]} at ${most_expensive[3]:.4f}/run",
        f"- **Daily savings switching to cheapest:** ${savings:.2f}/day (at 50 runs)",
        f"- **Monthly savings:** ${savings * 30:.2f}/month",
        "",
    ])

    # Task-specific tips
    if input_tokens > 10000:
        lines.append("- **High input tokens detected.** Consider summarizing or chunking input to reduce costs.")
    if output_tokens > 5000:
        lines.append("- **High output tokens detected.** Use structured output (JSON) to reduce verbosity.")
    if num_calls > 10:
        lines.append("- **Many calls per run.** Consider batching operations or using a faster model for routine calls.")

    # Stripe fee context
    lines.extend([
        "",
        "## Pricing Your Agent Service",
        "",
        "If you charge for this task, rule of thumb:",
        f"- **Cost floor:** ${cheapest[3]:.4f}/call (your cheapest compute cost)",
        f"- **3x markup:** ${cheapest[3] * 3:.4f}/call",
        f"- **5x markup:** ${cheapest[3] * 5:.4f}/call",
        "",
        f"At 3x markup with 100 calls/day: **${cheapest[3] * 3 * 100:.2f}/day** revenue",
        "",
        "For detailed pricing strategies, unit economics benchmarks, and market "
        "projections through 2030, see the **`agentic-economics`** skill.",
        "",
        "Use `get_skill(skill_name='agentic-economics', api_key=YOUR_KEY)` to retrieve. "
        "Free tier: 10 calls/day.",
    ])

    return "\n".join(lines)
