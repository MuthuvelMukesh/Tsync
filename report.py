"""
report.py — HTML report generator using Jinja2 templates.

Generates a clean, modern, dark-themed intelligence report
from processed message data.
"""

import os
import json
import statistics
from datetime import date, datetime
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from database import save_report_metadata


# Category color mapping for styled badges
CATEGORY_COLORS = {
    "technology": {"bg": "#6C3CE1", "text": "#E8DEFF"},
    "finance": {"bg": "#0EA47A", "text": "#D0FFF0"},
    "geopolitics": {"bg": "#CF4444", "text": "#FFE0E0"},
    "jobs": {"bg": "#D97D0E", "text": "#FFF0D0"},
    "science": {"bg": "#2B7DE9", "text": "#DCEEFF"},
    "regulation": {"bg": "#8B6914", "text": "#FFF5D0"},
    "other": {"bg": "#555555", "text": "#E0E0E0"},
    "unknown": {"bg": "#444444", "text": "#CCCCCC"},
}


def generate_report(
    selected_messages: list[dict],
    all_messages: list[dict],
    intensity: str,
    trends: list[dict],
    categories: dict[str, int],
    patterns: list[str],
    report_date: Optional[str] = None,
    output_dir: str = ".",
) -> str:
    """
    Generate the HTML intelligence report.

    Args:
        selected_messages: High-value messages with intelligence
        all_messages: All messages (for stats)
        intensity: 'LOW', 'MEDIUM', or 'HIGH'
        trends: Trending topics list
        categories: Category breakdown dict
        patterns: Detected patterns list
        report_date: Date string (defaults to today)
        output_dir: Where to write report.html

    Returns:
        Path to generated report.html
    """
    if report_date is None:
        report_date = date.today().isoformat()

    # Prepare template data
    scores = [m.get("importance_score", 0) for m in selected_messages]
    avg_score = statistics.mean(scores) if scores else 0

    # Add category colors to messages
    for msg in selected_messages:
        cat = msg.get("category", "other")
        colors = CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])
        msg["badge_bg"] = colors["bg"]
        msg["badge_text"] = colors["text"]
        msg["category_display"] = cat.title()

    # Intensity styling
    intensity_colors = {
        "LOW": {"color": "#4ADE80", "icon": "○"},
        "MEDIUM": {"color": "#FBBF24", "icon": "◉"},
        "HIGH": {"color": "#EF4444", "icon": "●"},
    }
    intensity_style = intensity_colors.get(intensity, intensity_colors["LOW"])

    # Format date for display
    try:
        dt = datetime.fromisoformat(report_date)
        display_date = dt.strftime("%B %d, %Y")
    except ValueError:
        display_date = report_date

    template_data = {
        "report_date": display_date,
        "report_date_iso": report_date,
        "intensity": intensity,
        "intensity_color": intensity_style["color"],
        "intensity_icon": intensity_style["icon"],
        "total_messages": len(all_messages),
        "selected_count": len(selected_messages),
        "avg_score": round(avg_score, 1),
        "messages": selected_messages,
        "trends": trends[:6],
        "categories": categories,
        "category_colors": CATEGORY_COLORS,
        "patterns": patterns,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Load and render template
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("report.html")
    html = template.render(**template_data)

    # Write report
    output_path = os.path.join(output_dir, "report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    # Copy CSS
    css_src = os.path.join(template_dir, "styles.css")
    css_dst = os.path.join(output_dir, "styles.css")
    if os.path.exists(css_src):
        import shutil
        shutil.copy2(css_src, css_dst)

    # Save report metadata to DB
    save_report_metadata(
        report_date=report_date,
        total_messages=len(all_messages),
        selected_count=len(selected_messages),
        intensity=intensity,
        categories=categories,
        trends=[t["topic"] for t in trends],
    )

    print(f"[REPORT] Generated: {output_path}")
    print(f"[REPORT] {len(selected_messages)} items | Intensity: {intensity}")
    return output_path


def generate_text_report(
    selected_messages: list[dict],
    intensity: str,
    trends: list[dict],
    categories: dict[str, int],
    patterns: list[str],
    report_date: Optional[str] = None,
) -> str:
    """
    Generate a plain-text version of the report.

    Returns the report as a string.
    """
    if report_date is None:
        report_date = date.today().isoformat()

    lines = []
    lines.append("=" * 60)
    lines.append("  DAILY INTELLIGENCE REPORT")
    lines.append(f"  Date: {report_date}")
    lines.append(f"  Intensity: {intensity}")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"📊 {len(selected_messages)} high-signal items selected")
    lines.append("")

    for i, msg in enumerate(selected_messages, 1):
        lines.append(f"{'─' * 50}")
        lines.append(f"  [{i}] {msg.get('headline', 'No headline')}")
        lines.append(f"  Category: {msg.get('category', 'unknown').title()}")
        lines.append(f"  Score: {msg.get('importance_score', 0):.1f}/10")
        lines.append(f"  Source: @{msg.get('source_channel', 'unknown')}")
        lines.append("")
        lines.append(f"  WHAT: {msg.get('summary', 'N/A')}")
        lines.append("")
        lines.append(f"  WHY IT MATTERS: {msg.get('why_it_matters', 'N/A')}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("  INSIGHTS")
    lines.append("=" * 60)
    lines.append("")

    if categories:
        lines.append("  Category Breakdown:")
        for cat, count in categories.items():
            lines.append(f"    • {cat.title()}: {count}")
        lines.append("")

    if trends:
        lines.append("  Trending Topics:")
        for t in trends[:6]:
            lines.append(f"    • {t['topic']} (×{t['count']})")
        lines.append("")

    if patterns:
        lines.append("  Patterns Detected:")
        for p in patterns:
            lines.append(f"    → {p}")
        lines.append("")

    lines.append("=" * 60)

    return "\n".join(lines)
