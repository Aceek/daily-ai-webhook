#!/usr/bin/env python3
"""
Markdown formatting utilities for Claude Service.

Functions to format execution summaries and workflow logs as Markdown.
"""

from loggers.models import ExecutionLog, WorkflowLog


def format_execution_summary(
    log: ExecutionLog,
    digest: dict | None,
    workflow: WorkflowLog | None,
) -> str:
    """Format the SUMMARY.md file content.

    Args:
        log: The execution log data.
        digest: Optional digest data from MCP.
        workflow: Optional workflow log data.

    Returns:
        Formatted Markdown string.
    """
    status = "SUCCESS" if log.success else "FAILED"
    status_emoji = "+" if log.success else "x"

    # Format duration
    duration_str = _format_duration(log.metrics.duration_seconds)

    # Cost
    cost_str = _format_cost(log.metrics.total_cost_usd)

    # Pipeline status
    pipeline = _build_pipeline_status(log, workflow, digest)

    # Digest stats
    digest_stats = _build_digest_stats(digest)

    # Top headlines
    top_headlines = _build_top_headlines(digest)

    # Storage status
    storage = _build_storage_status(workflow, digest)

    md = f"""# Execution {log.execution_id}

**Mission:** {log.mission}
**Status:** [{status_emoji}] {status}
**Date:** {log.timestamp.strftime("%Y-%m-%d %H:%M")}
**Duration:** {duration_str} | **Cost:** {cost_str}

## Pipeline

| Step | Status |
|------|--------|
{pipeline}

## Output ({digest_stats['total']} news)

| Category | Count |
|----------|-------|
| Headlines | {digest_stats['headlines']} |
| Research | {digest_stats['research']} |
| Industry | {digest_stats['industry']} |
| Watching | {digest_stats['watching']} |

## Top Stories

{top_headlines}
## Storage

| Target | Status | Details |
|--------|--------|---------|
{storage}

## Files

- [digest.json](./digest.json) - Final output
- [research.md](./research.md) - Research document
- [workflow.md](./workflow.md) - Workflow log
- [mcp.log](./mcp.log) - MCP operations log
"""

    if log.error:
        md += f"""
## Error

```
{log.error}
```
"""

    return md


def format_workflow_markdown(log: WorkflowLog) -> str:
    """Format workflow log as Markdown.

    Args:
        log: The workflow log data.

    Returns:
        Formatted Markdown string.
    """
    status_emoji = "[+]" if log.status == "success" else "[x]"
    duration_str = f"{log.duration_seconds:.1f}s"

    # Build nodes table
    nodes_table = _build_nodes_table(log)

    # Build storage section
    storage_section = _build_workflow_storage(log)

    # Source-specific header
    header_section = _build_workflow_header(log)

    md = f"""{header_section}

**Status:** {status_emoji} {log.status.upper()}
**ID:** `{log.workflow_execution_id}`
**Claude ID:** `{log.claude_execution_id or 'N/A'}`
**Duration:** {duration_str}

## Storage

{storage_section}

## Pipeline

{nodes_table}
"""

    if log.error_message:
        md += f"""
## Error

Node: `{log.error_node}`

```
{log.error_message}
```
"""

    return md


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}m {secs}s" if mins > 0 else f"{secs}s"


def _format_cost(cost_usd: float) -> str:
    """Format cost in USD."""
    return f"${cost_usd:.2f}" if cost_usd > 0 else "N/A"


def _build_pipeline_status(
    log: ExecutionLog,
    workflow: WorkflowLog | None,
    digest: dict | None,
) -> str:
    """Build pipeline status table rows."""
    collect_status = "[+]" if log.metrics.articles_received > 0 else "[x]"
    claude_status = "[+]" if log.success else "[x]"
    discord_status = "[+]" if workflow and workflow.discord_sent else "[x]"

    # Get metadata
    meta = digest.get("metadata", {}) if digest else {}
    web_searches = meta.get("web_searches", 0)
    deep_dives = meta.get("deep_dives", 0)

    return f"""| n8n collect | {collect_status} {log.metrics.articles_received} articles |
| Claude analyze | {claude_status} {web_searches} searches, {deep_dives} deep-dives |
| Discord send | {discord_status} |"""


def _build_digest_stats(digest: dict | None) -> dict:
    """Build digest statistics."""
    if not digest:
        return {"headlines": 0, "research": 0, "industry": 0, "watching": 0, "total": 0}

    headlines = len(digest.get("headlines", []))
    research = len(digest.get("research", []))
    industry = len(digest.get("industry", []))
    watching = len(digest.get("watching", []))
    total = headlines + research + industry + watching

    return {
        "headlines": headlines,
        "research": research,
        "industry": industry,
        "watching": watching,
        "total": total,
    }


def _build_top_headlines(digest: dict | None) -> str:
    """Build top headlines section."""
    if not digest or not digest.get("headlines"):
        return "*No headlines*\n"

    lines = []
    for i, h in enumerate(digest["headlines"][:3], 1):
        lines.append(f"{i}. {h.get('title', 'N/A')}")
    return "\n".join(lines) + "\n"


def _build_storage_status(
    workflow: WorkflowLog | None,
    digest: dict | None,
) -> str:
    """Build storage status table rows."""
    # Database status
    if workflow and workflow.db_saved:
        db_status = "[+]"
        db_details = f"digest_id={workflow.digest_id}, {workflow.articles_saved} articles"
    elif digest and digest.get("digest_id"):
        db_status = "[+]"
        db_details = f"digest_id={digest.get('digest_id')}"
    else:
        db_status = "[x]"
        db_details = "Not saved"

    # Discord status
    if workflow and workflow.discord_sent:
        discord_status = "[+]"
        discord_details = f"msg={workflow.discord_message_id}" if workflow.discord_message_id else "Sent"
    else:
        discord_status = "[x]"
        discord_details = "Not sent"

    return f"""| Database | {db_status} | {db_details} |
| Discord | {discord_status} | {discord_details} |"""


def _build_nodes_table(log: WorkflowLog) -> str:
    """Build nodes execution table."""
    lines = ["| Step | Status |", "|------|--------|"]
    for node in log.nodes_executed:
        status = "[+]" if node.status == "success" else "[x]"
        lines.append(f"| {node.name} | {status} |")
    return "\n".join(lines)


def _build_workflow_storage(log: WorkflowLog) -> str:
    """Build workflow storage section."""
    db_status = "[+] Saved" if log.db_saved else "[x] Not saved"
    db_details = f"digest_id={log.digest_id}" if log.digest_id else ""

    discord_status = "[+] Sent" if log.discord_sent else "[x] Not sent"
    discord_details = f"msg={log.discord_message_id}" if log.discord_message_id else ""

    return f"""| Target | Status | Details |
|--------|--------|---------|
| Database | {db_status} | {db_details} |
| Discord | {discord_status} | {discord_details} |"""


def _build_workflow_header(log: WorkflowLog) -> str:
    """Build workflow-specific header section."""
    if log.source == "discord_command":
        header = "# Discord Command Log"
        user_info = ""
        if log.discord_user:
            user_info = f"\n**User:** {log.discord_user.name} (`{log.discord_user.id}`)"
        if log.discord_guild:
            guild_name = log.discord_guild.name or log.discord_guild.id
            user_info += f"\n**Server:** {guild_name}"
        if log.discord_channel:
            channel_name = log.discord_channel.name or log.discord_channel.id
            user_info += f"\n**Channel:** #{channel_name}"
        if log.command_args:
            args_str = ", ".join(
                f"{k}={v}" for k, v in log.command_args.items() if v is not None
            )
            user_info += f"\n**Args:** {args_str}" if args_str else ""
        return header + user_info
    else:
        return "# n8n Workflow Log"
