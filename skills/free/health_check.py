"""
Free Tool: Agent Health Check

Scores an agent's configuration on governance, safety, and best practices.
Returns a score 0-100 with specific issues found.

No API key required. No inference costs. Pure pattern matching.
"""

import re

# Pattern rules: (name, description, check_function, weight, paid_skill_ref)
# check_function takes the input text and returns (passed: bool, detail: str)

def _check_silent_inference(text: str) -> tuple[bool, str]:
    bad_patterns = [
        (r'auto[- ]?correct', 'Auto-correction without explicit logging detected'),
        (r'auto[- ]?fix', 'Auto-fix without explicit user approval detected'),
        (r'silently', 'Use of "silently" suggests hidden operations'),
        (r'implicit(ly)?.*infer', 'Implicit inference pattern detected'),
        (r'assume.*intent', 'Assuming user intent without verification'),
        (r'auto[- ]?resolve', 'Auto-resolving ambiguity instead of surfacing it'),
        (r'default.*action.*without', 'Default actions without explicit authorization'),
        (r'infer.*meaning', 'Inferring meaning from context without documentation'),
    ]
    found = []
    for pattern, desc in bad_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(desc)
    if found:
        return False, '; '.join(found)
    return True, 'No silent inference patterns detected'


def _check_audit_trail(text: str) -> tuple[bool, str]:
    good_patterns = [
        r'log', r'audit', r'record', r'track', r'trace',
        r'decision.*log', r'history', r'changelog',
    ]
    found = sum(1 for p in good_patterns if re.search(p, text, re.IGNORECASE))
    if found >= 2:
        return True, f'Audit/logging references found ({found} patterns)'
    elif found == 1:
        return False, 'Minimal audit trail references. Consider adding explicit decision logging.'
    else:
        return False, 'No audit trail or logging patterns found. Agent decisions will be untraceable.'


def _check_authority_boundaries(text: str) -> tuple[bool, str]:
    good_patterns = [
        r'(user|human).*(approv|confirm|authoriz|decide)',
        r'(ask|check|verify).*(before|permission|consent)',
        r'escalat',
        r'human[- ]?in[- ]?the[- ]?loop',
        r'require.*confirmation',
        r'do not.*without.*permission',
    ]
    found = sum(1 for p in good_patterns if re.search(p, text, re.IGNORECASE))
    if found >= 2:
        return True, f'Authority boundary patterns found ({found})'
    elif found == 1:
        return False, 'Weak authority boundaries. Only 1 reference to human approval/escalation.'
    else:
        return False, 'No authority boundaries found. Agent may take actions without human oversight.'


def _check_error_handling(text: str) -> tuple[bool, str]:
    patterns = [
        r'error', r'fail', r'exception', r'fallback',
        r'retry', r'timeout', r'graceful',
    ]
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if found >= 3:
        return True, f'Error handling well-covered ({found} patterns)'
    elif found >= 1:
        return False, f'Partial error handling ({found} patterns). Add fallback and retry guidance.'
    else:
        return False, 'No error handling instructions. Agent will fail ungracefully.'


def _check_scope_limits(text: str) -> tuple[bool, str]:
    patterns = [
        r'(do not|don\'t|never|must not|should not)',
        r'(only|limit|restrict|bound|scope)',
        r'(forbidden|prohibited|not allowed)',
        r'(within|boundary|constraint)',
    ]
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if found >= 3:
        return True, f'Clear scope limitations ({found} patterns)'
    elif found >= 1:
        return False, f'Weak scope definition ({found} patterns). Agent may overreach its mandate.'
    else:
        return False, 'No scope limitations found. Agent has unbounded authority.'


def _check_output_format(text: str) -> tuple[bool, str]:
    patterns = [
        r'(format|structured|json|markdown|template)',
        r'(respond|reply|output|return).*(format|structure)',
        r'(schema|field|key|value)',
    ]
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if found >= 2:
        return True, 'Output format is well-specified'
    elif found == 1:
        return False, 'Partial output format specification. May produce inconsistent results.'
    else:
        return False, 'No output format specified. Agent output will be unpredictable.'


def _check_identity(text: str) -> tuple[bool, str]:
    patterns = [
        r'(you are|your role|you act as|your purpose)',
        r'(assistant|agent|helper|tool|service)',
        r'(identity|persona|character)',
    ]
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if found >= 2:
        return True, 'Agent identity is well-defined'
    elif found == 1:
        return False, 'Weak identity definition. Agent may behave inconsistently.'
    else:
        return False, 'No identity or role definition. Agent has no behavioral anchor.'


def _check_data_handling(text: str) -> tuple[bool, str]:
    patterns = [
        r'(privacy|confidential|sensitive|secret|pii)',
        r'(do not|don\'t).*(share|store|log|expose)',
        r'(data|information).*(handl|protect|secur)',
    ]
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    if found >= 2:
        return True, 'Data handling guidelines present'
    elif found == 1:
        return False, 'Minimal data handling guidance. Add privacy and confidentiality rules.'
    else:
        return False, 'No data handling instructions. Agent may mishandle sensitive information.'


CHECKS = [
    ('No Silent Inference', _check_silent_inference, 15, 'governance'),
    ('Audit Trail', _check_audit_trail, 12, 'intent-architecture'),
    ('Authority Boundaries', _check_authority_boundaries, 15, 'governance'),
    ('Error Handling', _check_error_handling, 10, None),
    ('Scope Limitations', _check_scope_limits, 12, 'governance'),
    ('Output Format', _check_output_format, 10, None),
    ('Identity Definition', _check_identity, 10, None),
    ('Data Handling', _check_data_handling, 8, 'governance'),
]

MAX_SCORE = sum(c[2] for c in CHECKS)
BONUS_WEIGHT = 100 - MAX_SCORE  # Distributed as bonus for length/thoroughness


def run_health_check(system_prompt: str) -> str:
    """Run the full health check and return a formatted report."""
    if not system_prompt or len(system_prompt.strip()) < 20:
        return (
            "Error: Please provide your agent's system prompt or configuration "
            "(at least 20 characters) for analysis."
        )

    results = []
    score = 0
    failed_checks = []

    for name, check_fn, weight, skill_ref in CHECKS:
        passed, detail = check_fn(system_prompt)
        results.append((name, passed, detail, weight, skill_ref))
        if passed:
            score += weight
        else:
            failed_checks.append((name, detail, skill_ref))

    # Bonus for thoroughness (longer prompts tend to be more considered)
    length = len(system_prompt)
    if length > 2000:
        bonus = BONUS_WEIGHT
    elif length > 1000:
        bonus = int(BONUS_WEIGHT * 0.7)
    elif length > 500:
        bonus = int(BONUS_WEIGHT * 0.4)
    else:
        bonus = 0
    score += bonus

    # Clamp to 0-100
    score = max(0, min(100, score))

    # Build the report
    grade = _grade(score)
    lines = [
        f"# Agent Health Check Report",
        f"",
        f"**Score: {score}/100** ({grade})",
        f"",
        f"---",
        f"",
        f"## Results",
        f"",
    ]

    for name, passed, detail, weight, skill_ref in results:
        icon = "PASS" if passed else "FAIL"
        lines.append(f"**[{icon}] {name}** (+{weight if passed else 0}/{weight} points)")
        lines.append(f"  {detail}")
        lines.append("")

    if bonus > 0:
        lines.append(f"**[BONUS] Thoroughness** (+{bonus} points)")
        lines.append(f"  System prompt length: {length} characters")
        lines.append("")

    if failed_checks:
        lines.append("---")
        lines.append("")
        lines.append("## How to Improve")
        lines.append("")

        skill_refs = {}
        for name, detail, skill_ref in failed_checks:
            lines.append(f"- **{name}:** {detail}")
            if skill_ref and skill_ref not in skill_refs:
                skill_refs[skill_ref] = []
            if skill_ref:
                skill_refs[skill_ref].append(name)

        if skill_refs:
            lines.append("")
            lines.append("## Recommended Skills")
            lines.append("")
            skill_descriptions = {
                'governance': 'Governance-Aware Agent Development -- covers all 14 forbidden failure modes, the Coupled Authority Phenomenon, and decision architecture patterns.',
                'intent-architecture': 'Intent-Preserving System Architecture -- append-only decision logs, 9 system invariants, replay safety, and implementation patterns.',
                'agentic-economics': 'Agentic Commerce Economics -- pricing models, unit economics, and revenue architecture for agent services.',
            }
            for skill_id, check_names in skill_refs.items():
                desc = skill_descriptions.get(skill_id, skill_id)
                lines.append(f"- **`{skill_id}`**: {desc}")
                lines.append(f"  Addresses: {', '.join(check_names)}")
            lines.append("")
            lines.append("Use `get_skill(skill_name, api_key)` to retrieve these. Free tier: 10 calls/day.")

    return "\n".join(lines)


def _grade(score: int) -> str:
    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    elif score >= 40:
        return "Needs Work"
    else:
        return "Critical"
