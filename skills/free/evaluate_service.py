"""
Free Tool: Evaluate Service

Evaluates any MCP service for trustworthiness before spending money.
Checks reachability, governance declarations, tool quality, and audit endpoints.
Returns a trust score (0-100) with a recommendation.

No API key required.
"""

import json
import time
import httpx

TIMEOUT = 10


async def run_evaluate_service(server_url: str, task_context: str = "") -> str:
    """Evaluate an MCP server and return a trust report."""
    if not server_url or len(server_url.strip()) < 8:
        return "Error: Please provide a valid MCP server URL to evaluate."

    server_url = server_url.strip().rstrip("/")

    # Derive base URL and MCP URL
    # Handle common patterns: /mcp, /mcp/mcp, or bare domain
    if server_url.endswith("/mcp"):
        base_url = server_url[:-4]
        # Try both the given URL and with /mcp appended (Starlette Mount)
        mcp_urls = [server_url, server_url + "/mcp"]
    else:
        base_url = server_url
        mcp_urls = [server_url + "/mcp/mcp", server_url + "/mcp"]

    scores = {}
    details = {}

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:

        # --- 1. Reachability check ---
        reach_score = 0
        reach_detail = ""
        try:
            t0 = time.time()
            resp = await client.get(f"{base_url}/health")
            latency_ms = int((time.time() - t0) * 1000)
            if resp.status_code == 200:
                reach_score = 100
                reach_detail = f"Health endpoint returned 200 OK in {latency_ms}ms"
            elif resp.status_code < 500:
                reach_score = 60
                reach_detail = f"Health endpoint returned {resp.status_code} in {latency_ms}ms"
            else:
                reach_score = 20
                reach_detail = f"Health endpoint returned {resp.status_code} (server error)"
        except httpx.ConnectError:
            reach_detail = "Connection refused -- server is not reachable"
        except httpx.TimeoutException:
            reach_detail = f"Connection timed out after {TIMEOUT}s"
        except Exception as e:
            reach_detail = f"Connection error: {type(e).__name__}"
        scores["reachability"] = reach_score
        details["reachability"] = reach_detail

        # --- 2. Service declaration check ---
        decl_score = 0
        decl_detail = ""
        agent_json = None
        try:
            resp = await client.get(f"{base_url}/.well-known/agent.json")
            if resp.status_code == 200:
                agent_json = resp.json()
                checks_passed = 0
                checks_total = 6
                parts = []

                if agent_json.get("name"):
                    checks_passed += 1
                    parts.append(f"name: {agent_json['name']}")
                if agent_json.get("services"):
                    checks_passed += 1
                    svc = agent_json["services"]
                    count = len(svc.get("free", [])) + len(svc.get("paid", []))
                    parts.append(f"{count} service groups declared")
                if agent_json.get("payment_methods"):
                    checks_passed += 1
                    parts.append(f"payment methods: {', '.join(agent_json['payment_methods'])}")
                if agent_json.get("governance", {}).get("invariants"):
                    checks_passed += 1
                    inv = agent_json["governance"]["invariants"]
                    parts.append(f"{len(inv)} governance invariants")
                if agent_json.get("governance", {}).get("audit_endpoint"):
                    checks_passed += 1
                    parts.append("audit endpoint declared")
                if agent_json.get("schema_version"):
                    checks_passed += 1
                    parts.append(f"schema v{agent_json['schema_version']}")

                decl_score = int((checks_passed / checks_total) * 100)
                decl_detail = f"{checks_passed}/{checks_total} fields present: {'; '.join(parts)}"
            elif resp.status_code == 404:
                decl_detail = "No /.well-known/agent.json found -- no service declaration"
            else:
                decl_detail = f"agent.json returned {resp.status_code}"
        except Exception as e:
            decl_detail = f"Failed to fetch agent.json: {type(e).__name__}"
        scores["declaration"] = decl_score
        details["declaration"] = decl_detail

        # --- 3. MCP tool quality check ---
        tool_score = 0
        tool_detail = ""
        tool_list = []
        try:
            # Initialize MCP session
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "evaluate-service", "version": "1.0"}
                }
            }
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
            # Try each candidate MCP URL until one works
            resp = None
            mcp_url = mcp_urls[0]
            for candidate_url in mcp_urls:
                try:
                    resp = await client.post(
                        candidate_url, json=init_payload, headers=headers
                    )
                    if resp.status_code == 200:
                        mcp_url = candidate_url
                        break
                except Exception:
                    continue

            session_id = None
            init_data = None
            if resp is None:
                raise Exception("No MCP URL responded")
            if "text/event-stream" in resp.headers.get("content-type", ""):
                # Parse SSE response
                for line in resp.text.split("\n"):
                    if line.startswith("data:"):
                        try:
                            init_data = json.loads(line[5:].strip())
                        except json.JSONDecodeError:
                            pass
                session_id = resp.headers.get("mcp-session-id")
            else:
                try:
                    init_data = resp.json()
                    session_id = resp.headers.get("mcp-session-id")
                except Exception:
                    pass

            if init_data:
                # Build headers for subsequent requests
                notif_headers = {**headers}
                if session_id:
                    notif_headers["Mcp-Session-Id"] = session_id

                # Send initialized notification
                notif_payload = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
                await client.post(mcp_url, json=notif_payload, headers=notif_headers)

                # List tools
                list_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                resp2 = await client.post(
                    mcp_url, json=list_payload, headers=notif_headers
                )

                tools_data = None
                if "text/event-stream" in resp2.headers.get("content-type", ""):
                    for line in resp2.text.split("\n"):
                        if line.startswith("data:"):
                            try:
                                tools_data = json.loads(line[5:].strip())
                            except json.JSONDecodeError:
                                pass
                else:
                    try:
                        tools_data = resp2.json()
                    except Exception:
                        pass

                if tools_data and "result" in tools_data:
                    tools = tools_data["result"].get("tools", [])
                    tool_list = tools
                    if not tools:
                        tool_score = 20
                        tool_detail = "MCP session established but no tools found"
                    else:
                        desc_scores = []
                        param_scores = []
                        for t in tools:
                            desc = t.get("description", "")
                            # Description quality
                            d_score = 0
                            if len(desc) >= 30:
                                d_score += 50
                            elif len(desc) >= 10:
                                d_score += 25
                            # Specificity: contains action words
                            specifics = [
                                "return", "check", "score", "evaluat",
                                "retriev", "generat", "creat", "list",
                                "provid", "analyz", "estimat", "lint"
                            ]
                            if any(s in desc.lower() for s in specifics):
                                d_score += 30
                            # Has multiple sentences
                            if desc.count(".") >= 2 or desc.count("\n") >= 1:
                                d_score += 20
                            desc_scores.append(min(d_score, 100))

                            # Parameter documentation
                            schema = t.get("inputSchema", {})
                            props = schema.get("properties", {})
                            if props:
                                documented = sum(
                                    1 for p in props.values()
                                    if p.get("description") or p.get("title")
                                )
                                p_score = (
                                    int((documented / len(props)) * 100)
                                    if props else 0
                                )
                            else:
                                p_score = 80
                            param_scores.append(p_score)

                        avg_desc = (
                            sum(desc_scores) / len(desc_scores)
                            if desc_scores else 0
                        )
                        avg_param = (
                            sum(param_scores) / len(param_scores)
                            if param_scores else 0
                        )
                        tool_score = int(avg_desc * 0.6 + avg_param * 0.4)
                        tool_detail = (
                            f"{len(tools)} tools found. "
                            f"Avg description quality: {int(avg_desc)}/100. "
                            f"Avg parameter docs: {int(avg_param)}/100."
                        )
                else:
                    tool_score = 30
                    tool_detail = (
                        "MCP session established but tools/list "
                        "returned unexpected data"
                    )
            else:
                tool_score = 10
                tool_detail = (
                    "MCP endpoint did not return valid initialization response"
                )
        except httpx.TimeoutException:
            tool_detail = f"MCP endpoint timed out after {TIMEOUT}s"
        except Exception as e:
            tool_detail = (
                f"MCP connection failed: {type(e).__name__}: {str(e)[:100]}"
            )
        scores["tool_quality"] = tool_score
        details["tool_quality"] = tool_detail

        # --- 4. Governance check ---
        gov_score = 0
        gov_detail = ""
        gov_parts = []

        # Check invariants from agent.json
        has_invariants = False
        if agent_json and agent_json.get("governance", {}).get("invariants"):
            invariants = agent_json["governance"]["invariants"]
            has_invariants = True
            gov_score += 40
            gov_parts.append(
                f"{len(invariants)} invariants declared: "
                f"{', '.join(invariants)}"
            )

        # Check audit endpoint
        audit_responsive = False
        audit_url = None
        if agent_json and agent_json.get("governance", {}).get("audit_endpoint"):
            audit_url = agent_json["governance"]["audit_endpoint"]
        else:
            audit_url = f"{base_url}/audit"

        if audit_url:
            try:
                resp = await client.get(audit_url)
                if resp.status_code == 200:
                    audit_data = resp.json()
                    audit_responsive = True
                    gov_score += 40
                    total = audit_data.get("total_calls", 0)
                    gov_parts.append(
                        f"Audit endpoint live ({total} calls in period)"
                    )
                else:
                    gov_parts.append(
                        f"Audit endpoint returned {resp.status_code}"
                    )
            except Exception as e:
                gov_parts.append(
                    f"Audit endpoint unreachable: {type(e).__name__}"
                )

        # Coupling bonus: both invariants and audit exist together
        if has_invariants and audit_responsive:
            gov_score += 20
            gov_parts.append("Coupling bonus: invariants + live audit")

        gov_score = min(gov_score, 100)
        gov_detail = (
            "; ".join(gov_parts) if gov_parts
            else "No governance signals found"
        )
        scores["governance"] = gov_score
        details["governance"] = gov_detail

    # --- 5. Overall score (weighted average) ---
    weights = {
        "reachability": 0.15,
        "declaration": 0.25,
        "tool_quality": 0.30,
        "governance": 0.30,
    }
    overall = sum(scores[k] * weights[k] for k in weights)
    overall = int(round(overall))

    # --- 6. Recommendation ---
    if overall >= 80:
        recommendation = "PROCEED"
        rec_detail = (
            "This service demonstrates strong trust signals "
            "across all dimensions."
        )
    elif overall >= 50:
        recommendation = "PROCEED WITH CAUTION"
        rec_detail = (
            "Some trust signals present but gaps exist. "
            "Suggest $1 max spend limit."
        )
    elif overall >= 25:
        recommendation = "HIGH RISK"
        rec_detail = (
            "Significant trust gaps. "
            "Suggest $0 max spend (free tier only)."
        )
    else:
        recommendation = "DO NOT TRANSACT"
        rec_detail = (
            "Insufficient trust signals to justify any interaction."
        )

    # --- 7. Build output ---
    lines = [
        "# MCP Service Trust Evaluation",
        "",
        f"**Target:** `{server_url}`",
    ]
    if task_context:
        lines.append(f"**Task context:** {task_context}")
    lines.extend([
        f"**Overall Trust Score: {overall}/100**",
        f"**Recommendation: {recommendation}**",
        f"_{rec_detail}_",
        "",
        "---",
        "",
        "## Dimension Scores",
        "",
        "| Dimension | Score | Weight | Detail |",
        "|-----------|-------|--------|--------|",
    ])

    dimension_labels = {
        "reachability": "Reachability",
        "declaration": "Service Declaration",
        "tool_quality": "Tool Quality",
        "governance": "Governance",
    }

    for key in ["reachability", "declaration", "tool_quality", "governance"]:
        label = dimension_labels[key]
        s = scores[key]
        w = f"{int(weights[key]*100)}%"
        d = details[key]
        lines.append(f"| {label} | {s}/100 | {w} | {d} |")

    if tool_list:
        lines.extend([
            "",
            "## Tools Found",
            "",
        ])
        for t in tool_list:
            name = t.get("name", "?")
            desc = t.get("description", "No description")
            if len(desc) > 120:
                desc = desc[:117] + "..."
            lines.append(f"- **{name}**: {desc}")

    if agent_json:
        lines.extend([
            "",
            "## Service Declaration",
            "",
            f"- **Name:** {agent_json.get('name', 'N/A')}",
            f"- **Description:** {agent_json.get('description', 'N/A')}",
        ])
        if agent_json.get("governance", {}).get("invariants"):
            inv = agent_json["governance"]["invariants"]
            lines.append(
                f"- **Governance invariants:** {', '.join(inv)}"
            )

    # Machine-readable JSON block
    machine_output = {
        "trust_score": overall,
        "recommendation": recommendation,
        "scores": scores,
        "tools_count": len(tool_list),
        "has_agent_json": agent_json is not None,
        "has_audit_endpoint": scores["governance"] >= 40,
        "server_url": server_url,
    }

    lines.extend([
        "",
        "---",
        "",
        "```json",
        json.dumps(machine_output, indent=2),
        "```",
    ])

    return "\n".join(lines)
