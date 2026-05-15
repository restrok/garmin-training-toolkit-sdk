#!/usr/bin/env python3
"""Garmin Training Toolkit - Extractor CLI."""

import argparse
import logging
import sys
from typing import NoReturn

from garmin_training_toolkit_sdk.auth import interactive_auth, save_tokens
from garmin_training_toolkit_sdk.utils import find_token_file, get_authenticated_client

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Garmin Training Toolkit CLI."""
    parser = argparse.ArgumentParser(description="Garmin Data Extractor Toolkit")
    sub = parser.add_subparsers(dest="command")

    # Auth Command
    sub.add_parser("auth", help="Authenticate with Garmin Connect (Multiple Methods)")

    # Extract Command
    sub.add_parser(
        "extract",
        help="Extract raw data using the garmin_training_toolkit_sdk (Test)"
    )

    args = parser.parse_args()

    if args.command == "auth":
        try:
            tokens = interactive_auth()
            if tokens:
                save_tokens(tokens)
                log.info("Authentication successful. Tokens saved.")
            else:
                log.error("Authentication failed or was cancelled.")
        except Exception as e:
            log.error("Error during authentication: %s", e)

    elif args.command == "extract":
        log.info("Data extraction is now handled by your AI Data Pipeline.")
        log.info("For a local test, please run: python3 example_ingestion.py")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
