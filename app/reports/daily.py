"""
Daily intelligence digest and HTML report generator.
"""

from datetime import datetime
import os
from typing import Optional
from jinja2 import Template

from app.reports.formatters import format_plain_text
from app.services.briefing_service import BriefingDigest

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Tsync Daily Intelligence Report — {{ digest.generated_at.strftime('%B %d, %Y') }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0B0F17;
      --card-bg: rgba(22, 27, 34, 0.85);
      --card-border: rgba(255, 255, 255, 0.08);
      --text: #F0F6FC;
      --text-muted: #8B949E;
      --accent: #58A6FF;
      --accent-glow: rgba(88, 166, 255, 0.2);
      --critical: #F85149;
      --high: #D29922;
      --medium: #3FB950;
      --low: #8B949E;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      padding: 2.5rem 1.5rem;
    }
    .container { max-width: 1040px; margin: 0 auto; }
    header {
      border-bottom: 1px solid var(--card-border);
      padding-bottom: 1.5rem;
      margin-bottom: 2rem;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .brand h1 {
      font-size: 1.85rem;
      font-weight: 700;
      background: linear-gradient(135deg, #FFF, #58A6FF);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }
    .brand p { color: var(--text-muted); font-size: 0.9rem; margin-top: 0.25rem; }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      padding: 0.35rem 0.75rem;
      border-radius: 9999px;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .badge-high { background: rgba(248, 81, 73, 0.15); color: var(--critical); border: 1px solid rgba(248, 81, 73, 0.3); }
    .badge-medium { background: rgba(210, 153, 34, 0.15); color: var(--high); border: 1px solid rgba(210, 153, 34, 0.3); }
    .badge-low { background: rgba(63, 185, 80, 0.15); color: var(--medium); border: 1px solid rgba(63, 185, 80, 0.3); }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 1rem;
      margin-bottom: 2.5rem;
    }
    .stat-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.25rem;
      backdrop-filter: blur(10px);
    }
    .stat-val { font-size: 2rem; font-weight: 700; color: #FFF; }
    .stat-label { font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }

    .section-title {
      font-size: 1.25rem;
      font-weight: 600;
      margin-bottom: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: #FFF;
    }
    .incident-list { display: flex; flex-direction: column; gap: 1.25rem; margin-bottom: 2.5rem; }
    .incident-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 1.5rem;
      transition: transform 0.15s ease, border-color 0.15s ease;
      backdrop-filter: blur(8px);
    }
    .incident-card:hover {
      transform: translateY(-2px);
      border-color: rgba(88, 166, 255, 0.4);
    }
    .incident-card.breaking {
      border-left: 4px solid var(--critical);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 0.75rem;
      gap: 1rem;
    }
    .card-title { font-size: 1.15rem; font-weight: 600; color: #FFF; }
    .card-meta { display: flex; gap: 0.5rem; align-items: center; flex-wrap: wrap; }
    .tag {
      font-size: 0.75rem;
      padding: 0.2rem 0.5rem;
      border-radius: 6px;
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-muted);
    }
    .summary { font-size: 0.95rem; margin-bottom: 0.85rem; color: #C9D1D9; }
    .impact-box {
      background: rgba(88, 166, 255, 0.07);
      border-left: 3px solid var(--accent);
      padding: 0.75rem 1rem;
      border-radius: 4px;
      font-size: 0.9rem;
      color: #E6EDF3;
    }
    .impact-box strong { color: var(--accent); }
    .sources { margin-top: 0.85rem; font-size: 0.8rem; color: var(--text-muted); }
    
    .meta-sidebar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 1.5rem;
    }
    .chips { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
    .chip {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      padding: 0.3rem 0.7rem;
      border-radius: 8px;
      font-size: 0.85rem;
    }
    footer {
      text-align: center;
      margin-top: 3.5rem;
      padding-top: 1.5rem;
      border-top: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 0.85rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <h1>Tsync Daily Intelligence</h1>
        <p>Operational briefing for {{ digest.generated_at.strftime('%A, %B %d, %Y') }}</p>
      </div>
      <div>
        <span class="badge badge-{{ digest.intensity.lower() }}">
          Intensity: {{ digest.intensity }}
        </span>
      </div>
    </header>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-val">{{ digest.total_incidents }}</div>
        <div class="stat-label">Total Incidents</div>
      </div>
      <div class="stat-card">
        <div class="stat-val" style="color: var(--critical);">{{ digest.breaking_count }}</div>
        <div class="stat-label">Breaking / Critical</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ digest.category_distribution|length }}</div>
        <div class="stat-label">Active Categories</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ digest.trends|length }}</div>
        <div class="stat-label">Trending Clusters</div>
      </div>
    </div>

    <h2 class="section-title">⚡ High-Signal Incidents & Intelligence</h2>
    <div class="incident-list">
      {% for inc in digest.incidents %}
      <div class="incident-card {% if inc.is_breaking %}breaking{% endif %}">
        <div class="card-header">
          <div class="card-title">
            {% if inc.is_breaking %}🚨 {% endif %}#{{ inc.id }} {{ inc.title }}
          </div>
          <div class="card-meta">
            <span class="tag">{{ inc.category.title() }}</span>
            <span class="tag">Score: {{ "%.1f"|format(inc.importance_score) }}</span>
            <span class="tag">{{ inc.status.value }}</span>
          </div>
        </div>
        <div class="summary">{{ inc.summary }}</div>
        {% if inc.why_it_matters %}
        <div class="impact-box">
          <strong>WHY IT MATTERS:</strong> {{ inc.why_it_matters }}
        </div>
        {% endif %}
        <div class="sources">
          Sources: {% for s in inc.sources %}@{{ s }}{% if not loop.last %}, {% endif %}{% endfor %}
        </div>
      </div>
      {% endfor %}
    </div>

    <div class="meta-sidebar">
      <div class="stat-card">
        <h3 class="section-title" style="font-size: 1rem;">📈 Trending Topics</h3>
        <div class="chips">
          {% for t in digest.trends %}
          <div class="chip">{{ t.topic }} <small style="color: var(--text-muted);">(×{{ t.count }})</small></div>
          {% endfor %}
        </div>
      </div>
      <div class="stat-card">
        <h3 class="section-title" style="font-size: 1rem;">🔍 Macro Observations</h3>
        <ul style="padding-left: 1.2rem; color: #C9D1D9; font-size: 0.9rem;">
          {% for p in digest.patterns %}
          <li style="margin-bottom: 0.4rem;">{{ p }}</li>
          {% endfor %}
        </ul>
      </div>
    </div>

    <footer>
      Tsync Modular Intelligence Engine • Generated automatically at {{ digest.generated_at.strftime('%Y-%m-%d %H:%M:%S') }} UTC
    </footer>
  </div>
</body>
</html>
"""


class DailyReportGenerator:
    """Generates standalone HTML and Plain Text daily reports."""

    @staticmethod
    def generate_html(digest: BriefingDigest, output_path: str = "report.html") -> str:
        """Render and save HTML report."""
        template = Template(HTML_TEMPLATE)
        html = template.render(digest=digest)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        return output_path

    @staticmethod
    def generate_text(digest: BriefingDigest, output_path: str = "report.txt") -> str:
        """Render and save plain text report."""
        text = format_plain_text(digest)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return output_path
