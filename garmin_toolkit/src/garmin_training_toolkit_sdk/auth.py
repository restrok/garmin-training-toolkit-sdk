#!/usr/bin/env python3
"""Garmin Browser Authentication.

Uses Playwright to open a real browser for login, bypassing Cloudflare blocking.
"""

import getpass
import json
import logging
import re
import time
from typing import Any, Dict, Optional

import requests
from playwright.sync_api import sync_playwright
from requests_oauthlib import OAuth1Session

from .utils import save_tokens

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

OAUTH_CONSUMER_URL = "https://thegarth.s3.amazonaws.com/oauth_consumer.json"
ANDROID_UA = "com.garmin.android.apps.connectmobile"
MAX_WAIT = 300  # 5 minutes

SSO_URL = (
    "https://sso.garmin.com/sso/embed"
    "?id=gauth-widget"
    "&embedWidget=true"
    "&gauthHost=https://sso.garmin.com/sso"
    "&clientId=GarminConnect"
    "&locale=en_US"
    "&redirectAfterAccountLoginUrl=https://sso.garmin.com/sso/embed"
    "&service=https://sso.garmin.com/sso/embed"
)


def get_oauth_consumer() -> Dict[str, str]:
    """Fetch the shared OAuth consumer key/secret from garth's S3 bucket.

    Returns:
        A dictionary containing "consumer_key" and "consumer_secret".
    """
    resp = requests.get(OAUTH_CONSUMER_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_oauth1_token(ticket: str, consumer: Dict[str, str]) -> Dict[str, str]:
    """Exchange an SSO ticket for an OAuth1 token.

    Args:
        ticket: The SSO ticket captured from the login process.
        consumer: A dictionary containing "consumer_key" and "consumer_secret".

    Returns:
        A dictionary containing OAuth1 token information.
    """
    sess = OAuth1Session(
        consumer["consumer_key"],
        consumer["consumer_secret"],
    )
    url = (
        f"https://connectapi.garmin.com/oauth-service/oauth/"
        f"preauthorized?ticket={ticket}"
        f"&login-url=https://sso.garmin.com/sso/embed"
        f"&accepts-mfa-tokens=true"
    )
    resp = sess.get(url, headers={"User-Agent": ANDROID_UA}, timeout=15)
    resp.raise_for_status()
    parsed = {}
    for line in resp.text.split("&"):
        if "=" in line:
            k, v = line.split("=", 1)
            parsed[k] = v
    parsed["domain"] = "garmin.com"
    return parsed


def exchange_oauth2(oauth1: Dict[str, str], consumer: Dict[str, str]) -> Dict[str, Any]:
    """Exchange OAuth1 token for OAuth2 token.

    Args:
        oauth1: A dictionary containing OAuth1 token information.
        consumer: A dictionary containing "consumer_key" and "consumer_secret".

    Returns:
        A dictionary containing OAuth2 token information.
    """
    sess = OAuth1Session(
        consumer["consumer_key"],
        consumer["consumer_secret"],
        resource_owner_key=oauth1["oauth_token"],
        resource_owner_secret=oauth1["oauth_token_secret"],
    )
    url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
    # Specifically request 'all' scope which includes USER_PROFILE and activity scopes
    data: Dict[str, Any] = {"scope": "all"}
    resp = sess.post(
        url,
        headers={
            "User-Agent": ANDROID_UA,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data=data,
        timeout=15,
    )
    resp.raise_for_status()
    token = resp.json()

    if "scope" in token:
        log.info("Granted scopes: %s", token["scope"])

    token["expires_at"] = int(time.time() + token["expires_in"])
    token["refresh_token_expires_at"] = int(
        time.time() + token["refresh_token_expires_in"]
    )
    return token


def get_tokens_from_ticket(ticket: str) -> Dict[str, Any]:
    """Complete the OAuth exchange from an SSO ticket.

    Args:
        ticket: The SSO ticket (starts with ST-).

    Returns:
        A dictionary containing the DI tokens.
    """
    log.info("Fetching OAuth consumer credentials...")
    consumer = get_oauth_consumer()

    log.info("Exchanging ticket for OAuth1 token...")
    oauth1 = get_oauth1_token(ticket, consumer)

    log.info("Exchanging OAuth1 for OAuth2 token...")
    oauth2 = exchange_oauth2(oauth1, consumer)

    token_data = {
        "di_token": oauth2["access_token"],
        "di_refresh_token": oauth2["refresh_token"],
        "di_client_id": "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    }
    return token_data


def browser_login(headless: bool = False, max_wait: int = MAX_WAIT) -> str:
    """Open a real browser, let user log in, capture the SSO ticket.

    Args:
        headless: Whether to run the browser in headless mode.
        max_wait: Maximum time to wait for login in seconds.

    Returns:
        The captured SSO ticket.

    Raises:
        Exception: If the login times out or fails.
    """
    ticket = None

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=headless)
        except Exception as e:
            log.error("Failed to launch browser: %s", e)
            log.info("Ensure playwright is installed: playwright install chromium")
            raise e

        context = browser.new_context()
        page = context.new_page()

        page.goto(SSO_URL)

        log.info("Browser opened! Log in with your Garmin credentials.")
        if not headless:
            log.info("The window will close automatically when done.")

        start = time.time()

        while time.time() - start < max_wait:
            try:
                content = page.content()
                m = re.search(r"ticket=(ST-[A-Za-z0-9\-]+)", content)
                if m:
                    ticket = m.group(1)
                    log.info("Got ticket: %s...", ticket[:30])
                    break

                url = page.url
                if "ticket=" in url:
                    m = re.search(r"ticket=(ST-[A-Za-z0-9\-]+)", url)
                    if m:
                        ticket = m.group(1)
                        log.info("Got ticket from URL: %s...", ticket[:30])
                        break
            except Exception:
                pass

            page.wait_for_timeout(500)

        browser.close()

    if not ticket:
        raise Exception("Timed out waiting for login (%ds). Try again." % max_wait)

    return ticket


def credentials_login() -> Optional[Dict[str, Any]]:
    """Log in using email and password from terminal.

    Returns:
        The token data dictionary if successful, None otherwise.
    """
    from garminconnect import Garmin

    email = input("Garmin Email: ")
    password = getpass.getpass("Garmin Password: ")

    log.info("Attempting login for %s...", email)
    try:
        client = Garmin(email, password)
        client.login()
        log.info("Login successful!")
        return json.loads(client.client.dumps())
    except Exception as e:
        log.error("Login failed: %s", e)
        log.info("Tip: If you are seeing Cloudflare errors, try the Browser method.")
        return None


def manual_ticket_login() -> Optional[Dict[str, Any]]:
    """Log in by manually pasting an SSO ticket.

    Returns:
        The token data dictionary if successful, None otherwise.
    """
    log.info("1. Open this URL in your browser: ")
    log.info("   %s", SSO_URL)
    log.info("2. Log in and look at the final URL.")
    log.info("3. Copy the 'ticket=ST-XXXXXX' part and paste it below.")

    ticket_input = input("\nPaste your SSO Ticket (ST-XXXXXX): ").strip()

    # Extract ticket if full URL was pasted
    m = re.search(r"ST-[A-Za-z0-9\-]+", ticket_input)
    if not m:
        log.error("Invalid ticket format. Expected 'ST-XXXXXX'")
        return None

    ticket = m.group(0)
    try:
        return get_tokens_from_ticket(ticket)
    except Exception as e:
        log.error("Failed to exchange ticket: %s", e)
        return None


def interactive_auth() -> Optional[Dict[str, Any]]:
    """Interactive authentication menu.

    Returns:
        The token data dictionary if successful, None otherwise.
    """
    print("\n--- Garmin Connect Authentication ---")
    print("1) Terminal: Enter Email and Password (Classic)")
    print("2) Browser:  Automatic Login (Bypasses Cloudflare)")
    print("3) Manual:   Paste SSO Ticket from web (Most Reliable)")
    print("q) Quit")

    choice = input("\nSelect an option [1-3, q]: ").strip().lower()

    if choice == "1":
        return credentials_login()
    elif choice == "2":
        headless_choice = input("Run in background (headless)? [y/N]: ").strip().lower()
        try:
            ticket = browser_login(headless=(headless_choice == "y"))
            return get_tokens_from_ticket(ticket)
        except Exception as e:
            log.error("Browser login failed: %s", e)
            return None
    elif choice == "3":
        return manual_ticket_login()
    elif choice == "q":
        log.info("Authentication cancelled.")
        return None
    else:
        log.error("Invalid choice.")
        return None


def main() -> None:
    """Main execution function for Garmin Browser Authentication."""
    log.info("Garmin Authentication Toolkit")
    log.info("=" * 40)

    tokens = interactive_auth()
    if tokens:
        save_tokens(tokens)
        log.info("=" * 40)
        log.info("SUCCESS! Tokens saved.")
        log.info("You can now run the toolkit commands.")
    else:
        log.error("Authentication failed.")


if __name__ == "__main__":
    main()
