#!/usr/bin/env python3
"""
Garmin Training Toolkit - Extractor CLI
"""

import argparse
import logging
import sys
from pathlib import Path

from garmin_toolkit.auth import browser_login, save_tokens
from garmin_toolkit.utils import get_authenticated_client, find_token_file

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Garmin Data Extractor Toolkit")
    sub = parser.add_subparsers(dest="command")
    
    # Auth Command
    p_auth = sub.add_parser("auth", help="Authenticate with Garmin Connect via browser")
    p_auth.add_argument("--headless", action="store_true", help="Run browser in background")
    
    # Extract Command
    p_extract = sub.add_parser("extract", help="Extract raw data using the garmin_toolkit (Test)")
    
    args = parser.parse_args()
    
    if args.command == "auth":
        log.info("Starting browser authentication...")
        try:
            tokens = browser_login(headless=args.headless)
            if tokens:
                save_tokens(tokens)
                log.info("Authentication successful. Tokens saved.")
            else:
                log.error("Authentication failed or was cancelled.")
        except Exception as e:
            log.error(f"Error during authentication: {e}")
            
    elif args.command == "extract":
        log.info("Data extraction is now handled by your AI Data Pipeline.")
        log.info("For a local test, please run: python3 example_ingestion.py")
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
