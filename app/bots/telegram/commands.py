"""
Thin Telegram bot command controllers.
Delegates all queries to services and formats responses with zero business logic.
"""

from app.reports.formatters import format_incident_detail, format_telegram_markdown
from app.services.briefing_service import BriefingService
from app.services.incident_service import IncidentService
from app.services.search_service import SearchService
from app.services.status_service import StatusService


def get_start_message() -> str:
    """Return welcome message."""
    return (
        "⚡ *Welcome to Tsync Intelligence Bot*\n\n"
        "I monitor, cluster, and track high-signal unfolding intelligence incidents in real-time.\n\n"
        "Available Commands:\n"
        "• `/incidents` — View all active incidents\n"
        "• `/details <id>` — Deep-dive into an incident and its timeline\n"
        "• `/search <query>` — Search incidents by keyword\n"
        "• `/briefing` — Generate current intelligence briefing\n"
        "• `/status` — View system health & monitored sources\n"
        "• `/help` — Show command instructions"
    )


def get_help_message() -> str:
    """Return help text."""
    return (
        "📖 *Tsync Command Reference*\n\n"
        "• `/incidents` — List active incidents sorted by importance\n"
        "• `/details <incident_id>` — Show full timeline, claims, and analysis\n"
        "• `/search <keyword>` — Find matching incidents\n"
        "• `/briefing` — Generate instant intelligence digest\n"
        "• `/status` — Check monitored channels and system health"
    )


async def execute_incidents_command(incident_service: IncidentService) -> str:
    """List active incidents."""
    incidents = await incident_service.get_hourly_updates(limit=15)
    if not incidents:
        return "ℹ️ *No active incidents currently being tracked.*"

    lines = ["⚡ *ACTIVE INTELLIGENCE INCIDENTS*", "━━━━━━━━━━━━━━━━━━━━━━", ""]
    for inc in incidents:
        icon = "🚨" if inc.is_breaking else "•"
        lines.append(f"{icon} *#{inc.id}* [{inc.category.title()}] *{inc.title}*")
        lines.append(f"  Score: `{inc.importance_score:.1f}` | Status: `{inc.status.value}`")
        lines.append(f"  _View:_ `/details_{inc.id}`")
        lines.append("")

    return "\n".join(lines)


async def execute_details_command(
    incident_id: int, incident_service: IncidentService
) -> str:
    """Get comprehensive incident detail."""
    incident = await incident_service.get_details(incident_id)
    if not incident:
        return f"❌ Incident `#{incident_id}` was not found."

    return format_incident_detail(incident)


async def execute_search_command(
    query: str, search_service: SearchService
) -> str:
    """Search incidents by query."""
    if not query.strip():
        return "⚠️ Please provide a search term: `/search <query>`"

    results = await search_service.search_incidents(query.strip(), limit=10)
    if not results:
        return f"🔍 No incidents found matching `\"{query}\"`."

    lines = [f"🔍 *SEARCH RESULTS FOR \"{query}\"*", "━━━━━━━━━━━━━━━━━━━━━━", ""]
    for inc in results:
        lines.append(f"• *#{inc.id}* {inc.title}")
        lines.append(f"  Score: `{inc.importance_score:.1f}` | Status: `{inc.status.value}`")
        lines.append(f"  _View:_ `/details_{inc.id}`")
        lines.append("")

    return "\n".join(lines)


async def execute_briefing_command(
    incident_service: IncidentService, briefing_service: BriefingService
) -> str:
    """Generate on-demand briefing digest."""
    incidents = await incident_service.get_hourly_updates(limit=20)
    if not incidents:
        return "ℹ️ No incidents available for briefing generation."

    digest = briefing_service.generate_digest(incidents, period="hourly")
    return format_telegram_markdown(digest)


async def execute_status_command(status_service: StatusService) -> str:
    """Check health and statistics."""
    stats = await status_service.get_system_status()
    sources_str = ", ".join([f"@{s}" for s in stats["sources"]]) if stats["sources"] else "None"

    return (
        f"🟢 *TSYNC SYSTEM STATUS: {stats['status'].upper()}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Active Sources:* `{stats['active_sources_count']}`\n"
        f"Channels: {sources_str}\n\n"
        f"⚡ *Active Incidents:* `{stats['active_incidents_count']}`\n"
        f"🚨 *Breaking Alerts Active:* `{stats['breaking_incidents_count']}`\n"
        f"🏷 *Monitored Categories:* {', '.join([c.title() for c in stats['monitored_categories']]) or 'None'}"
    )
