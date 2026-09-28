"""
Report and message formatting utilities for multiple channels (Telegram, WhatsApp, Plain Text, HTML).
"""

from app.domain.incidents import Incident
from app.services.briefing_service import BriefingDigest


def format_incident_detail(incident: Incident) -> str:
    """Format single incident for Telegram bot detailed view."""
    sources_str = ", ".join([f"@{s}" for s in incident.sources]) if incident.sources else "Unknown"
    entities_str = ", ".join([e.name for e in incident.entities[:5]]) if incident.entities else "None"

    lines = [
        f"⚡ *INCIDENT #{incident.id}: {incident.title}*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"📌 *Category:* {incident.category.title()}",
        f"🚦 *Status:* `{incident.status.value}` | *Severity:* `{incident.severity.value}`",
        f"🎯 *Importance:* `{incident.importance_score:.1f}/10` | *Confidence:* `{int(incident.confidence_score * 100)}%`",
        f"📡 *Sources:* {sources_str}",
        f"🏷 *Key Entities:* {entities_str}",
        "",
        f"📝 *Summary:*",
        f"{incident.summary or 'No summary recorded.'}",
        "",
        f"💡 *Why It Matters:*",
        f"{incident.why_it_matters or 'Standard analytical observation.'}",
    ]

    if incident.timeline:
        lines.append("")
        lines.append("⏱ *Timeline Events:*")
        for entry in incident.timeline[-5:]:
            marker = "🚨" if entry.is_major_event else "•"
            ts = entry.timestamp.strftime("%H:%M UTC") if entry.timestamp else ""
            lines.append(f"  {marker} `{ts}` {entry.content} (@{entry.source_channel})")

    if incident.contradictions_count > 0:
        lines.append("")
        lines.append(f"⚠️ *Warning:* {incident.contradictions_count} conflicting claims detected on this incident.")

    return "\n".join(lines)


def format_telegram_markdown(digest: BriefingDigest) -> str:
    """Format briefing digest for Telegram channel delivery."""
    period_title = digest.period.upper()
    lines = [
        f"🌐 *TSYNC {period_title} INTELLIGENCE BRIEFING*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 *Incidents:* {digest.total_incidents} | *Breaking:* {digest.breaking_count} | *Intensity:* `{digest.intensity}`",
        "",
    ]

    for idx, inc in enumerate(digest.incidents[:8], 1):
        icon = "🚨" if inc.is_breaking else "•"
        lines.append(f"{icon} *#{inc.id} [{inc.category.title()}]* {inc.title}")
        lines.append(f"  Score: `{inc.importance_score:.1f}` | Status: `{inc.status.value}`")
        if inc.summary:
            lines.append(f"  _{inc.summary[:140]}..._")
        lines.append("")

    if digest.trends:
        trend_strs = [f"{t.topic} (×{t.count})" for t in digest.trends[:4]]
        lines.append(f"📈 *Trending Topics:* {', '.join(trend_strs)}")

    return "\n".join(lines)


def format_whatsapp_text(digest: BriefingDigest) -> str:
    """Format briefing digest for WhatsApp delivery."""
    lines = [
        f"*TSYNC {digest.period.upper()} BRIEFING*",
        f"Incidents: {digest.total_incidents} | Intensity: {digest.intensity}",
        "--------------------------------",
        "",
    ]

    for idx, inc in enumerate(digest.incidents[:5], 1):
        lines.append(f"[{idx}] *{inc.title}*")
        lines.append(f"Category: {inc.category.title()} (Score: {inc.importance_score:.1f})")
        lines.append(f"WHAT: {inc.summary[:150]}...")
        lines.append(f"WHY: {inc.why_it_matters[:100]}...")
        lines.append("")

    return "\n".join(lines)


def format_plain_text(digest: BriefingDigest) -> str:
    """Format briefing digest as clean plain text."""
    lines = [
        "=" * 60,
        f"  TSYNC {digest.period.upper()} INTELLIGENCE DIGEST",
        f"  Generated: {digest.generated_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"  Total Incidents: {digest.total_incidents} | Intensity: {digest.intensity}",
        "=" * 60,
        "",
    ]

    for idx, inc in enumerate(digest.incidents, 1):
        lines.append(f"[{idx}] {inc.title}")
        lines.append(f"    Category: {inc.category.title()} | Status: {inc.status.value} | Score: {inc.importance_score:.1f}")
        lines.append(f"    Sources: {', '.join(['@' + s for s in inc.sources])}")
        lines.append(f"    WHAT: {inc.summary}")
        lines.append(f"    WHY:  {inc.why_it_matters}")
        lines.append("-" * 50)

    if digest.trends:
        lines.append("\nTRENDING TOPICS:")
        for t in digest.trends:
            lines.append(f"  • {t.topic} (count: {t.count}, relevance: {t.relevance_score})")

    if digest.patterns:
        lines.append("\nDETECTED MACRO PATTERNS:")
        for p in digest.patterns:
            lines.append(f"  → {p}")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)
