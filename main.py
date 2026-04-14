"""
main.py — Tsync Intelligence Engine orchestrator.

Single entry point that runs the entire pipeline:
  Ingest → Clean → Categorize → Score → Select → Generate → Report

Usage:
  python main.py              # Full pipeline
  python main.py --demo       # Demo with sample data (no Telegram needed)
  python main.py --channels   # List configured channels
  python main.py --add-channel <name>
  python main.py --remove-channel <name>
"""

import sys
import json
import asyncio
import statistics
from datetime import date

from database import (
    init_db,
    bulk_insert_messages,
    get_messages_by_date,
    get_unprocessed_messages,
    update_message_processing,
    get_selected_messages,
)
from telegram_client import (
    collect_all_messages,
    add_channel,
    remove_channel,
    list_channels,
)
from rules import prefilter_message, categorize_by_rules
from ai_processor import ai_categorize, batch_generate_intelligence
from scorer import score_message
from selector import dynamic_select, calculate_intensity
from trends import extract_topics, category_breakdown, detect_patterns
from report import generate_report, generate_text_report


def load_config() -> dict:
    with open("config.json", "r") as f:
        return json.load(f)


def run_pipeline(target_date: str = None) -> str:
    """
    Execute the full intelligence pipeline.

    Returns path to generated report.
    """
    if target_date is None:
        target_date = date.today().isoformat()

    print("\n" + "=" * 60)
    print("  ⚡ TSYNC INTELLIGENCE ENGINE")
    print(f"  Date: {target_date}")
    print("=" * 60 + "\n")

    config = load_config()

    # ─── STEP 1: Get messages from DB ─────────────────────────────
    print("[PIPELINE] Step 1: Loading messages...")
    all_messages = get_messages_by_date(target_date)
    print(f"  → {len(all_messages)} messages loaded for {target_date}")

    if not all_messages:
        print("[PIPELINE] No messages found. Run ingestion first.")
        return ""

    # ─── STEP 2: Pre-filter & Rule-based Categorization ──────────
    print("\n[PIPELINE] Step 2: Filtering & rule-based categorization...")
    processed = []
    skipped = 0
    needs_ai = []

    for msg in all_messages:
        result = prefilter_message(msg["text"])

        if result["skip"]:
            skipped += 1
            update_message_processing(
                msg["id"],
                category=result["category"],
                importance_score=0.0,
            )
            continue

        if result["needs_ai"]:
            needs_ai.append(msg)
        else:
            msg["category"] = result["category"]

        processed.append(msg)

    print(f"  → {len(processed)} passed filters, {skipped} skipped")
    print(f"  → {len(needs_ai)} need AI categorization")

    # ─── STEP 3: AI Categorization (fallback only) ───────────────
    if needs_ai:
        print(f"\n[PIPELINE] Step 3: AI categorization for {len(needs_ai)} messages...")
        for msg in needs_ai:
            category = ai_categorize(msg["text"])
            msg["category"] = category or "other"
            print(f"  → AI: '{msg['text'][:50]}...' → {msg['category']}")
    else:
        print("\n[PIPELINE] Step 3: No AI categorization needed ✓")

    # ─── STEP 4: Importance Scoring ──────────────────────────────
    print("\n[PIPELINE] Step 4: Scoring messages...")
    for msg in processed:
        msg["importance_score"] = score_message(
            msg["text"],
            msg.get("category", "unknown"),
            msg.get("source_channel", ""),
        )
        # Persist score and category
        update_message_processing(
            msg["id"],
            category=msg.get("category", "unknown"),
            importance_score=msg["importance_score"],
        )

    scores = [m["importance_score"] for m in processed]
    if scores:
        print(f"  → Score range: {min(scores):.1f} – {max(scores):.1f}")
        print(f"  → Mean: {statistics.mean(scores):.1f}")

    # ─── STEP 5: Dynamic Selection ───────────────────────────────
    print("\n[PIPELINE] Step 5: Dynamic selection...")
    selected = dynamic_select(processed)

    # Mark selected in DB
    for msg in selected:
        update_message_processing(
            msg["id"],
            category=msg.get("category", "unknown"),
            importance_score=msg["importance_score"],
            is_selected=True,
        )

    # ─── STEP 6: Intelligence Generation (AI — selected only) ───
    print(f"\n[PIPELINE] Step 6: Generating intelligence for {len(selected)} items...")
    selected = batch_generate_intelligence(selected)

    # Persist intelligence data
    for msg in selected:
        update_message_processing(
            msg["id"],
            category=msg.get("category", "unknown"),
            importance_score=msg["importance_score"],
            headline=msg.get("headline"),
            summary=msg.get("summary"),
            why_it_matters=msg.get("why_it_matters"),
            is_selected=True,
        )

    # ─── STEP 7: Trend Detection ────────────────────────────────
    print("\n[PIPELINE] Step 7: Detecting trends...")
    trends = extract_topics(selected)
    categories = category_breakdown(selected)
    patterns = detect_patterns(selected)

    print(f"  → {len(trends)} trending topics")
    print(f"  → {len(categories)} categories")
    print(f"  → {len(patterns)} patterns detected")

    # ─── STEP 8: Calculate Intensity ─────────────────────────────
    sel_scores = [m.get("importance_score", 0) for m in selected]
    avg_score = statistics.mean(sel_scores) if sel_scores else 0
    intensity = calculate_intensity(
        len(all_messages), len(selected), avg_score
    )

    # ─── STEP 9: Generate Reports ────────────────────────────────
    print("\n[PIPELINE] Step 9: Generating reports...")

    # HTML report
    report_path = generate_report(
        selected_messages=selected,
        all_messages=all_messages,
        intensity=intensity,
        trends=trends,
        categories=categories,
        patterns=patterns,
        report_date=target_date,
    )

    # Text report
    text_report = generate_text_report(
        selected_messages=selected,
        intensity=intensity,
        trends=trends,
        categories=categories,
        patterns=patterns,
        report_date=target_date,
    )

    # Save text report
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write(text_report)

    print("\n" + text_report)

    print("\n" + "=" * 60)
    print("  ✅ PIPELINE COMPLETE")
    print(f"  HTML Report: {report_path}")
    print(f"  Text Report: report.txt")
    print("=" * 60 + "\n")

    return report_path


async def run_ingestion() -> int:
    """Run Telegram message ingestion."""
    print("\n[INGEST] Starting Telegram ingestion...")
    count = await collect_all_messages()
    print(f"[INGEST] Done. {count} new messages stored.\n")
    return count


def run_demo():
    """Run pipeline with sample data (no Telegram needed)."""
    print("\n[DEMO] Inserting sample data...")

    today = date.today().isoformat()

    sample_messages = [
        {
            "telegram_id": 90001,
            "text": "BREAKING: OpenAI announces GPT-5 with unprecedented reasoning capabilities. The new model achieves 95% on graduate-level science benchmarks and introduces native multimodal understanding. This represents a significant leap in artificial intelligence capabilities that could reshape enterprise software, scientific research, and education sectors. Early access begins next month for API partners.",
            "source_channel": "tech_news",
            "date": today,
        },
        {
            "telegram_id": 90002,
            "text": "Federal Reserve signals potential rate cut in September as inflation data shows cooling trend. CPI dropped to 2.4% year-over-year, below expectations of 2.6%. Markets rallied on the news with S&P 500 gaining 1.8%. Bond yields fell sharply as traders priced in higher probability of easing cycle beginning sooner than expected.",
            "source_channel": "finance_daily",
            "date": today,
        },
        {
            "telegram_id": 90003,
            "text": "EU passes comprehensive AI regulation framework requiring transparency disclosures for all AI systems deployed in member states. Companies must disclose training data sources, implement human oversight mechanisms, and conduct regular bias audits. Non-compliance penalties up to 6% of global revenue. Tech companies have 18 months to comply.",
            "source_channel": "regulation_watch",
            "date": today,
        },
        {
            "telegram_id": 90004,
            "text": "NVIDIA reports record quarterly revenue of $35.1 billion, driven by surging demand for AI training chips. Data center revenue up 427% year-over-year. CEO Jensen Huang announces next-generation Blackwell Ultra GPU architecture. Stock surges 12% in after-hours trading. Analysts raise price targets across the board.",
            "source_channel": "tech_news",
            "date": today,
        },
        {
            "telegram_id": 90005,
            "text": "Major cybersecurity breach at healthcare giant exposes 12 million patient records. Hackers exploited zero-day vulnerability in cloud infrastructure. The breach includes names, Social Security numbers, medical histories, and insurance details. FBI investigation launched. This is the largest healthcare data breach of the year.",
            "source_channel": "tech_news",
            "date": today,
        },
        {
            "telegram_id": 90006,
            "text": "China launches first quantum computing satellite enabling global quantum key distribution network. The satellite, named Micius-2, can generate entangled photon pairs across 4,600 kilometers. This breakthrough could make current encryption methods obsolete and reshape global cybersecurity landscape.",
            "source_channel": "science_today",
            "date": today,
        },
        {
            "telegram_id": 90007,
            "text": "Tech layoffs continue: Microsoft cuts 6,000 jobs across Azure and gaming divisions. Meta reduces workforce by 4,500 in reality labs. Combined with earlier announcements, over 45,000 tech workers have been laid off this quarter. The restructuring focuses on shifting resources toward AI development.",
            "source_channel": "jobs_market",
            "date": today,
        },
        {
            "telegram_id": 90008,
            "text": "NASA confirms discovery of organic molecules on Mars surface by Perseverance rover. The complex carbon-based compounds found in Jezero Crater sediments are consistent with biological activity, though geological origins cannot be ruled out. Sample return mission timeline accelerated to 2030.",
            "source_channel": "science_today",
            "date": today,
        },
        {
            "telegram_id": 90009,
            "text": "Bitcoin breaks $100,000 for the first time as institutional adoption accelerates. BlackRock's spot ETF surpasses $50 billion in AUM. Trading volume hits all-time high of $82 billion in 24 hours. Analysts project potential move to $150K if current momentum sustained through Q3.",
            "source_channel": "finance_daily",
            "date": today,
        },
        {
            "telegram_id": 90010,
            "text": "NATO emergency summit called as tensions escalate in South China Sea. Multiple naval vessels from China, US, Philippines, and Japan operating in close proximity. Diplomatic channels remain open but military readiness increased across all parties. Beijing warns against 'provocative actions'.",
            "source_channel": "geopolitics_wire",
            "date": today,
        },
        {
            "telegram_id": 90011,
            "text": "Google DeepMind achieves breakthrough in protein folding prediction, solving structures 1000x faster than AlphaFold 2. New model can predict protein interactions and drug binding sites with near-experimental accuracy. Pharma industry expected to save $4 billion annually in drug discovery costs.",
            "source_channel": "science_today",
            "date": today,
        },
        {
            "telegram_id": 90012,
            "text": "India announces $15 billion semiconductor fab construction in Gujarat with TSMC partnership. First chips expected by 2028. Government offers 50% capital subsidy. This positions India as major player in global chip supply chain diversification away from Taiwan concentration risk.",
            "source_channel": "tech_news",
            "date": today,
        },
        {
            "telegram_id": 90013,
            "text": "Join our premium channel for the best crypto signals! 100% guaranteed profits! DM me for free trial. Limited time offer — earn $500 daily with our automated trading bot!",
            "source_channel": "spam_channel",
            "date": today,
        },
        {
            "telegram_id": 90014,
            "text": "hi",
            "source_channel": "random",
            "date": today,
        },
        {
            "telegram_id": 90015,
            "text": "Remote work trend accelerates: 67% of Fortune 500 companies now offer permanent hybrid arrangements. Average tech salary for remote positions reaches $145K. New study shows remote workers 23% more productive but report higher burnout rates. Companies investing heavily in async collaboration tools.",
            "source_channel": "jobs_market",
            "date": today,
        },
    ]

    inserted = bulk_insert_messages(sample_messages)
    print(f"[DEMO] Inserted {inserted} sample messages.\n")
    return inserted


def main():
    """Entry point with CLI argument handling."""
    init_db()

    # Parse CLI args
    args = sys.argv[1:]

    if not args:
        # Full pipeline: ingest + process
        asyncio.run(run_ingestion())
        run_pipeline()

    elif args[0] == "--demo":
        run_demo()
        run_pipeline()

    elif args[0] == "--process":
        # Process only (skip ingestion)
        run_pipeline()

    elif args[0] == "--channels":
        list_channels()

    elif args[0] == "--add-channel" and len(args) > 1:
        add_channel(args[1])

    elif args[0] == "--remove-channel" and len(args) > 1:
        remove_channel(args[1])

    elif args[0] == "--help":
        print("""
Tsync Intelligence Engine
========================

Usage:
  python main.py                        Full pipeline (ingest + process)
  python main.py --demo                 Demo with sample data
  python main.py --process              Process only (skip Telegram)
  python main.py --channels             List configured channels
  python main.py --add-channel <name>   Add a channel
  python main.py --remove-channel <name> Remove a channel
  python main.py --help                 Show this help
        """)

    else:
        print(f"Unknown command: {' '.join(args)}")
        print("Run 'python main.py --help' for usage.")


if __name__ == "__main__":
    main()
