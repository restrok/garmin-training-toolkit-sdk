#!/usr/bin/env python3
"""
Garmin Authentication using garminconnect native DI OAuth.
Simplified version - uses garminconnect's built-in auth.
"""

import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)


def main():
    import argparse
    import getpass
    import os
    
    parser = argparse.ArgumentParser(description="Garmin Authentication")
    parser.add_argument("--email", "-e", help="Garmin email")
    parser.add_argument("--password", "-p", help="Garmin password (or use GARMIN_PASSWORD env)")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()
    
    log.info("Garmin Authentication")
    log.info("=" * 40)
    
    # Get credentials
    email = args.email or input("Garmin email: ")
    password = args.password or os.environ.get("GARMIN_PASSWORD") or getpass.getpass("Garmin password: ")
    
    from garminconnect import Garmin
    
    # Create client - will use browser for login
    garmin = Garmin(
        email=email,
        password=password,
        prompt_mfa=lambda: input("MFA code (check email): "),
    )
    
    log.info("Attempting login...")
    result, data = garmin.login()
    
    if result == "needs_mfa":
        log.info("MFA required. Please check your email for the code.")
        mfa_code = input("Enter MFA code: ")
        garmin.resume_login(data, mfa_code)
    
    # Save tokens to default location
    token_dir = os.path.expanduser("~/.garminconnect")
    garmin.client.dump(token_dir)
    
    log.info("=" * 40)
    log.info(f"SUCCESS! Tokens saved to {token_dir}")
    log.info("You can now run collect/upload!")


if __name__ == "__main__":
    main()