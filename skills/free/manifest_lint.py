"""
Free Tool: MCP Manifest Linter

Checks MCP tool definitions for anti-patterns, missing fields, and
quality issues. The only MCP linter that exists.

No API key required. No inference costs. Pure rule-based checking.
"""

import json

RULES = [
    {
        "id": "description-missing",
        "severity": "critical",
        "check": lambda t: bool(t.get("description")),
        "message": "Tool has no description. Agents cannot discover tools without descriptions.",
        "fix": "Add a clear, one-sentence description of what this tool does.",
    },
    {
        "id": "description-too-short",
        "severity": "warning",
        "check": lambda t: len(t.get("description", "")) >= 30,
        "message": "Description is too short (< 30 chars). Agents need context to decide whether to call this tool.",
        "fix": "Expand the description to explain what the tool does, what it returns, and when to use it.",
    },
    {
        "id": "description-too-long",
        "severity": "info",
        "check": lambda t: len(t.get("description", "")) <= 500,
        "message": "Description is very long (> 500 chars). May be truncated in some MCP clients.",
        "fix": "Lead with the most important information. Move details to parameter descriptions.",
    },
    {
        "id": "name-too-generic",
        "severity": "warning",
        "check": lambda t: t.get("name", "").lower() not in [
            "run", "execute", "do", "process", "handle", "get", "set",
            "tool", "function", "action", "task", "query",
        ],
        "message": "Tool name is too generic. Agents cannot distinguish this from other tools.",
        "fix": "Use a specific, descriptive name like 'analyze_code' instead of 'run'.",
    },
    {
        "id": "params-missing",
        "severity": "warning",
        "check": lambda t: "inputSchema" in t or "parameters" in t or "input_schema" in t,
        "message": "No parameter schema defined. Agents won't know what arguments to pass.",
        "fix": "Add an inputSchema with JSON Schema definitions for each parameter.",
    },
    {
        "id": "param-descriptions-missing",
        "severity": "warning",
        "check": lambda t: _check_param_descriptions(t),
        "message": "Some parameters lack descriptions. Agents may pass incorrect values.",
        "fix": "Add a description to every parameter explaining what it expects.",
    },
    {
        "id": "no-error-docs",
        "severity": "info",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["error", "fail", "invalid", "return"]
        ),
        "message": "No mention of error cases in description. Agents won't know how to handle failures.",
        "fix": "Document what the tool returns on error or invalid input.",
    },
    {
        "id": "no-example",
        "severity": "info",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["example", "e.g.", "for instance", "such as"]
        ),
        "message": "No usage example in description. Examples help agents understand expected input.",
        "fix": "Add a brief example showing a typical input and output.",
    },
    {
        "id": "no-rate-info",
        "severity": "info",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["rate", "limit", "quota", "throttl", "calls per"]
        ),
        "message": "No rate limit information. Agents may call too frequently and get blocked.",
        "fix": "Mention any rate limits or usage quotas in the description.",
    },
    {
        "id": "no-auth-info",
        "severity": "info",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["api key", "auth", "token", "credential", "require"]
        ),
        "message": "No authentication requirements mentioned.",
        "fix": "If the tool requires authentication, mention it in the description.",
    },
    {
        "id": "name-has-spaces",
        "severity": "critical",
        "check": lambda t: " " not in t.get("name", ""),
        "message": "Tool name contains spaces. This will break most MCP clients.",
        "fix": "Use snake_case or camelCase for tool names.",
    },
    {
        "id": "name-too-long",
        "severity": "warning",
        "check": lambda t: len(t.get("name", "")) <= 40,
        "message": "Tool name is very long (> 40 chars). May be truncated in some clients.",
        "fix": "Shorten the name. Use the description for additional context.",
    },
    {
        "id": "no-provenance",
        "severity": "info",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["author", "source", "provenance", "version", "maintained"]
        ),
        "message": "No provenance information. Users cannot verify the source or maintenance status.",
        "fix": "Add author, version, or source information to build trust.",
        "skill_ref": "governance",
    },
    {
        "id": "no-authority-spec",
        "severity": "warning",
        "check": lambda t: any(
            word in t.get("description", "").lower()
            for word in ["read", "write", "modify", "create", "delete", "side effect", "mutation"]
        ),
        "message": "No authority specification. Users don't know if this tool reads or writes data.",
        "fix": "Specify whether this tool is read-only or has side effects (creates, modifies, deletes).",
        "skill_ref": "intent-architecture",
    },
]


def _check_param_descriptions(tool: dict) -> bool:
    schema = tool.get("inputSchema") or tool.get("parameters") or tool.get("input_schema", {})
    if not schema:
        return True  # No params = no missing descriptions
    props = schema.get("properties", {})
    if not props:
        return True
    return all("description" in v for v in props.values())


def run_manifest_lint(tools_json: str) -> str:
    """Lint MCP tool definitions and return a report."""
    # Parse input
    try:
        data = json.loads(tools_json)
    except json.JSONDecodeError:
        return (
            "Error: Invalid JSON. Please provide your MCP tool definitions as a JSON array.\n\n"
            "Expected format:\n"
            '```json\n[{"name": "my_tool", "description": "...", "inputSchema": {...}}]\n```'
        )

    # Accept either a list of tools or a single tool object
    if isinstance(data, dict):
        tools = [data]
    elif isinstance(data, list):
        tools = data
    else:
        return "Error: Expected a JSON array of tool definitions or a single tool object."

    if not tools:
        return "Error: No tools found in input."

    # Run checks
    all_results = []
    total_pass = 0
    total_fail = 0
    total_warn = 0

    for tool in tools:
        tool_name = tool.get("name", "(unnamed)")
        tool_results = []

        for rule in RULES:
            try:
                passed = rule["check"](tool)
            except Exception:
                passed = True  # Skip rules that error

            if not passed:
                tool_results.append(rule)
                if rule["severity"] == "critical":
                    total_fail += 1
                elif rule["severity"] == "warning":
                    total_warn += 1
            else:
                total_pass += 1

        all_results.append((tool_name, tool_results))

    total_rules = total_pass + total_fail + total_warn
    pass_rate = int((total_pass / total_rules) * 100) if total_rules > 0 else 0

    # Build report
    lines = [
        f"# MCP Manifest Lint Report",
        f"",
        f"**Tools checked:** {len(tools)}",
        f"**Pass rate:** {pass_rate}% ({total_pass}/{total_rules} rules passed)",
        f"**Critical:** {total_fail} | **Warnings:** {total_warn}",
        f"",
        f"---",
    ]

    skill_refs = set()

    for tool_name, issues in all_results:
        lines.append(f"")
        if not issues:
            lines.append(f"## `{tool_name}` -- All checks passed")
        else:
            lines.append(f"## `{tool_name}` -- {len(issues)} issue(s)")
            lines.append(f"")
            for rule in issues:
                sev = rule["severity"].upper()
                lines.append(f"**[{sev}] {rule['id']}**")
                lines.append(f"  {rule['message']}")
                lines.append(f"  Fix: {rule['fix']}")
                if "skill_ref" in rule:
                    skill_refs.add(rule["skill_ref"])
                lines.append(f"")

    if skill_refs:
        lines.append("---")
        lines.append("")
        lines.append("## Recommended Skills for Deeper Fixes")
        lines.append("")
        skill_descriptions = {
            'governance': 'Governance-Aware Agent Development -- authority boundaries, provenance patterns, and 14 forbidden failure modes.',
            'intent-architecture': 'Intent-Preserving System Architecture -- side effect documentation, authority specification, and audit patterns.',
        }
        for ref in skill_refs:
            desc = skill_descriptions.get(ref, ref)
            lines.append(f"- **`{ref}`**: {desc}")
        lines.append("")
        lines.append("Use `get_skill(skill_name, api_key)` to retrieve. Free tier: 10 calls/day.")

    return "\n".join(lines)
