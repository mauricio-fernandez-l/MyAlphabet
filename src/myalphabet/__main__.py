"""Entry point for running MyAlphabet as a module or script."""

import argparse
import sys
from pathlib import Path


def main() -> int:
    """Main entry point for the alphabet game."""
    parser = argparse.ArgumentParser(
        description="MyAlphabet - An alphabet learning game for young children",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  myalphabet                      Run with default config search
  myalphabet -c /path/config.yaml Run with specific config file
  myalphabet --help               Show this help message
        """,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to the configuration file (config.yaml)",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Show version information",
    )

    args = parser.parse_args()

    if args.version:
        from . import __version__

        print(f"MyAlphabet version {__version__}")
        return 0

    config_path = Path(args.config) if args.config else None

    if config_path and not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        return 1

    from .game import run_game

    run_game(config_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
