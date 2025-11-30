"""
CLI entry point: python -m exo

This module enables running Exo as a module.
"""

import sys


def main() -> int:
    """Main entry point for the Exo CLI."""
    try:
        from exo.cli.main import main as cli_main

        return cli_main()
    except ImportError:
        # Click not installed - show helpful message
        from exo import __version__

        print(f"Exo v{__version__}")
        print("CLI requires click. Install with: pip install -e '.[cli]'")
        return 1


if __name__ == "__main__":
    sys.exit(main())
