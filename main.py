"""
main.py — Tsync CLI Entrypoint (Thin Dispatcher).
Contains NO business logic. Delegates entirely to modular scripts and workflows.

Usage:
  python main.py              # Run hourly workflow
  python main.py --demo       # Run demo workflow with synthetic data
  python main.py --bot        # Start the Telegram bot
  python main.py --migrate    # Initialize/verify database schema
  python main.py --help       # Show command help
"""

import sys
import os
import subprocess

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def run_script(script_name: str, args: list[str]) -> int:
    script_path = os.path.join(ROOT_DIR, "scripts", script_name)
    cmd = [sys.executable, script_path] + args
    return subprocess.call(cmd)


def print_help():
    print("""
⚡ Tsync — Modular Intelligence Engine CLI
=========================================

Commands:
  python main.py              Run the standard hourly intelligence cycle
  python main.py --demo       Run demo with sample incidents (zero credentials needed)
  python main.py --bot        Start the Telegram Bot polling daemon
  python main.py --migrate    Create/verify database schema
  python main.py --help       Show this help message

Direct Modular Scripts:
  python scripts/hourly.py [--demo]
  python scripts/bot.py
  python scripts/migrate.py
""")


def main():
    args = sys.argv[1:]

    if not args:
        sys.exit(run_script("hourly.py", []))

    cmd = args[0]
    if cmd == "--demo":
        sys.exit(run_script("hourly.py", ["--demo"]))
    elif cmd == "--bot":
        sys.exit(run_script("bot.py", []))
    elif cmd == "--migrate":
        sys.exit(run_script("migrate.py", []))
    elif cmd in ("--help", "-h"):
        print_help()
    else:
        print(f"Unknown argument: {cmd}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
