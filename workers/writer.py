"""
workers/writer.py
Composes the final intelligence briefing report.

Improvement 5: API calls wrapped with exponential-backoff retry.
Improvement 6: focus_areas from the planner shape the report structure so the
               analyst addresses the angles the plan decided to investigate.
               A confidence signal is injected when verification results are weak.
"""

from datetime import datetime
from utils.ai_client import AIServiceError, chat_completion


def _confidence_note(verifications):
    """Return a plain-text caution line when verification results are weak."""
    if not verifications:
        return ""
    total = len(verifications)
    unverifiable = sum(1 for v in verifications if v["verdict"] == "Unverifiable")
    supported = sum(1 for v in verifications if v["verdict"].strip() == "Supported")

    if unverifiable == total:
        return (
            "\nCAUTION: Every claim in this briefing is unverifiable from the "
            "available sources. Treat all findings with caution.\n"
        )
    if unverifiable > supported:
        return (
            "\nCAUTION: More claims are unverifiable than supported by independent "
            "sources. Confidence in findings is limited.\n"
        )
    return ""


def write_briefing(topic, summaries, verifications, focus_areas, run_id, store, verbose=True):
    """
    Write a complete plain-text briefing report, persist it, and return it.

    Parameters
    ----------
    focus_areas : list[str] - from the planner; used to frame the analysis.
    """
    date_str = datetime.now().strftime("%B %d, %Y")

    focus_str = ""
    if focus_areas:
        areas = "\n".join(f"  - {a}" for a in focus_areas)
        focus_str = f"\nResearch angles to address:\n{areas}\n"

    summaries_block = "\n\n".join(
        f"SOURCE: {s['title']}\nURL: {s['url']}\nSUMMARY: {s['summary']}"
        for s in summaries
    )

    verifications_block = "\n".join(
        f"  - {v['claim']}\n"
        f"    Origin : {v.get('source_title', '')}\n"
        f"    Verdict: {v['verdict']} - {v['reasoning']}"
        for v in verifications
    )

    caution = _confidence_note(verifications)

    prompt = (
        "You are an intelligence analyst writing a professional briefing report for "
        "CFOs, AI consultants, DevOps teams, managers, knowledge workers, AI governance "
        "leads, and mid-market companies with 50-1000 employees.\n\n"
        f"Topic : {topic}\n"
        f"Date  : {date_str}\n"
        f"{focus_str}"
        f"{caution}\n"
        "ARTICLE SUMMARIES:\n"
        f"{summaries_block}\n\n"
        "FACT-CHECKED CLAIMS (verified against independent sources):\n"
        f"{verifications_block}\n\n"
        "Write a complete briefing report focused specifically on Claude Cowork and "
        "Claude Code cost optimization. Explain where costs increase, what behaviors "
        "create token, context, tool, or orchestration waste, how repo, folder, "
        "connector, context, skill, workflow, MCP, and automation scoping affect cost, "
        "and how to turn findings into an actionable operating model.\n\n"
        "Use these clearly labelled sections:\n\n"
        "EXECUTIVE SUMMARY\n"
        "KEY COST DRIVERS\n"
        "CLAUDE COWORK COST OPTIMIZATION FINDINGS\n"
        "CLAUDE CODE COST OPTIMIZATION FINDINGS\n"
        "SHARED COST OPTIMIZATION PATTERNS\n"
        "GOVERNANCE AND POLICY CONTROLS\n"
        "DEVOPS IMPLICATIONS\n"
        "MANAGEMENT AND KNOWLEDGE WORKER IMPLICATIONS\n"
        "RISK AND LIMITATION ANALYSIS\n"
        "RECOMMENDED OPERATING MODEL\n"
        "SOURCE EVIDENCE TABLE\n"
        "CLAIM VERIFICATION TABLE\n"
        "ACTION CHECKLIST\n\n"
        "Rules:\n"
        "- Write in professional prose.\n"
        "- Use plain-text section headings (no # symbols).\n"
        "- Keep the analysis specific to Claude Cowork and Claude Code cost optimization; do not turn it into a generic AI cost optimization report.\n"
        "- Do not use JSON or code blocks.\n"
        "- The report must be readable as plain text."
    )

    if verbose:
        print("  Composing briefing report...")

    try:
        response = chat_completion(
            [{"role": "user", "content": prompt}],
            max_tokens=2600,
            temperature=0.4,
        )
        report = response.choices[0].message.content.strip()
    except AIServiceError as exc:
        if not exc.recoverable:
            raise
        report = _fallback_report(topic, date_str, summaries, verifications, focus_areas)
    store.save_report(run_id, report)
    return report


def _fallback_report(topic, date_str, summaries, verifications, focus_areas):
    """Compose a deterministic plain-text report when OpenAI is unreachable."""
    lines = [
        "EXECUTIVE SUMMARY",
        f"This briefing covers {topic} using the available sources collected on {date_str}. OpenAI report writing was temporarily unavailable, so this report uses deterministic local assembly from collected summaries and verification records.",
        "",
        "KEY COST DRIVERS",
    ]
    for summary in summaries[:5]:
        lines.append(f"- {summary['title']}: {summary['summary'][:350]}")

    lines.extend(["", "CLAUDE COWORK COST OPTIMIZATION FINDINGS"])
    lines.append(
        "Review collected evidence for management, knowledge-worker, connector, context, "
        "workflow, and automation patterns that can raise or reduce Claude Cowork usage."
    )

    lines.extend(["", "CLAUDE CODE COST OPTIMIZATION FINDINGS"])
    lines.append(
        "Review collected evidence for repository scope, folder scope, tool execution, "
        "MCP usage, DevOps workflows, and sub-agent orchestration patterns that can raise "
        "or reduce Claude Code usage."
    )

    lines.extend(["", "SHARED COST OPTIMIZATION PATTERNS"])
    if focus_areas:
        lines.append("Research angles reviewed: " + "; ".join(focus_areas) + ".")
    lines.append(
        "The collected summaries above should be treated as source-grounded notes. "
        "Review the verification section before relying on any individual claim."
    )

    lines.extend(["", "GOVERNANCE AND POLICY CONTROLS"])
    lines.append(
        "Define approved use cases, scope repositories and connectors deliberately, monitor "
        "token and tool-call patterns, and review automation runs for avoidable repetition."
    )

    lines.extend(["", "DEVOPS IMPLICATIONS"])
    lines.append(
        "DevOps teams should scope repositories and folders tightly, review MCP/tool execution "
        "patterns, and track repeated automation or sub-agent work that does not change outcomes."
    )

    lines.extend(["", "MANAGEMENT AND KNOWLEDGE WORKER IMPLICATIONS"])
    lines.append(
        "Managers and knowledge workers should scope files, connectors, and workflows to the "
        "decision at hand and avoid sending unnecessary context into routine Claude Cowork tasks."
    )

    lines.extend(["", "RISK AND LIMITATION ANALYSIS"])
    lines.append(
        "This fallback report is limited to locally assembled summaries and verification records. "
        "Review source evidence before making policy or budget decisions."
    )

    lines.extend(["", "RECOMMENDED OPERATING MODEL"])
    lines.append(
        "Assign ownership across finance, DevOps, governance, and business teams; define usage "
        "policies; monitor cost metrics; and review high-volume workflows regularly."
    )

    lines.extend(["", "SOURCE EVIDENCE TABLE"])
    for summary in summaries:
        lines.append(f"- {summary['title']} - {summary['url']}")

    lines.extend(["", "CLAIM VERIFICATION TABLE"])
    if verifications:
        for item in verifications:
            lines.append(
                f"- {item['claim']} Origin: {item.get('source_title', 'unknown')}. "
                f"Verdict: {item['verdict']}. {item['reasoning']}"
            )
    else:
        lines.append("- No claims were verified.")

    lines.extend(["", "ACTION CHECKLIST"])
    lines.append("- Identify high-cost Claude Cowork and Claude Code workflows.")
    lines.append("- Set scoping rules for repositories, folders, connectors, and context.")
    lines.append("- Track token usage, tool calls, automation runs, and rework.")
    lines.append("- Review policies with finance, DevOps, management, and governance owners.")
    return "\n".join(lines)
