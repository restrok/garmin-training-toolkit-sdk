#!/usr/bin/env python3
"""
Garmin Browser Authentication
Uses Playwright to open a real browser for login, bypassing Cloudflare blocking.
"""

import json
import logging
import re
import sys
import time
from pathlib import Path

import requests
from playwright.sync_api import sync_playwright
from requests_oauthlib import OAuth1Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from garmin_utils import save_tokens

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger(__name__)

OAUTH_CONSUMER_URL = "https://thegarth.s3.amazonaws.com/oauth_consumer.json"
ANDROID_UA = "com.garmin.android.apps.connectmobile"
MAX_WAIT = 300  # 5 minutes


def get_oauth_consumer():
    """Fetch the shared OAuth consumer key/secret from garth's S3 bucket."""
    resp = requests.get(OAUTH_CONSUMER_URL, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_oauth1_token(ticket: str, consumer: dict) -> dict:
    """Exchange an SSO ticket for an OAuth1 token."""
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
    for line in resp.text.split('&'):
        if '=' in line:
            k, v = line.split('=', 1)
            parsed[k] = v
    parsed["domain"] = "garmin.com"
    return parsed


def exchange_oauth2(oauth1: dict, consumer: dict) -> dict:
    """Exchange OAuth1 token for OAuth2 token."""
    sess = OAuth1Session(
        consumer["consumer_key"],
        consumer["consumer_secret"],
        resource_owner_key=oauth1["oauth_token"],
        resource_owner_secret=oauth1["oauth_token_secret"],
    )
    url = "https://connectapi.garmin.com/oauth-service/oauth/exchange/user/2.0"
    data = {}
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
    token["expires_at"] = int(time.time() + token["expires_in"])
    token["refresh_token_expires_at"] = int(
        time.time() + token["refresh_token_expires_in"]
    )
    return token


def browser_login(headless=False, max_wait=MAX_WAIT) -> str:
    """Open a real browser, let user log in, capture the SSO ticket."""
    ticket = None
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context()
        page = context.new_page()
        
        sso_url = (
            "https://sso.garmin.com/sso/embed"
            "?id=gauth-widget"
            "&embedWidget=true"
            "&gauthHost=https://sso.garmin.com/sso"
            "&clientId=GarminConnect"
            "&locale=en_US"
            "&redirectAfterAccountLoginUrl=https://sso.garmin.com/sso/embed"
            "&service=https://sso.garmin.com/sso/embed"
        )
        
        page.goto(sso_url)
        
        log.info("Browser opened! Log in with your Garmin credentials.")
        log.info("The window will close automatically when done.")
        
        start = time.time()
        
        while time.time() - start < max_wait:
            try:
                content = page.content()
                m = re.search(r'ticket=(ST-[A-Za-z0-9\-]+)', content)
                if m:
                    ticket = m.group(1)
                    log.info(f"Got ticket: {ticket[:30]}...")
                    break
                
                url = page.url
                if "ticket=" in url:
                    m = re.search(r'ticket=(ST-[A-Za-z0-9\-]+)', url)
                    if m:
                        ticket = m.group(1)
                        log.info(f"Got ticket from URL: {ticket[:30]}...")
                        break
            except Exception:
                pass
            
            page.wait_for_timeout(500)
        
        browser.close()
    
    if not ticket:
        raise Exception(f"Timed out waiting for login ({max_wait}s). Try again.")
    
    return ticket


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Garmin Browser Authentication")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--timeout", type=int, default=300, help="Max wait time in seconds (default: 300)")
    args = parser.parse_args()
    
    log.info("Garmin Browser Authentication")
    log.info("=" * 40)
    
    log.info("Fetching OAuth consumer credentials...")
    consumer = get_oauth_consumer()
    log.info(f"Consumer: {consumer['consumer_key'][:20]}...")
    
    log.info("Launching browser...")
    ticket = browser_login(headless=args.headless, max_wait=args.timeout)
    
    log.info("Exchanging ticket for OAuth1 token...")
    oauth1 = get_oauth1_token(ticket, consumer)
    log.info(f"OAuth1 token: {oauth1['oauth_token'][:20]}...")
    
    log.info("Exchanging OAuth1 for OAuth2 token...")
    oauth2 = exchange_oauth2(oauth1, consumer)
    log.info(f"OAuth2 access_token: {oauth2['access_token'][:20]}...")
    log.info(f"Expires in: {oauth2['expires_in']}s")
    log.info(f"Refresh expires in: {oauth2['refresh_token_expires_in']}s")
    
    log.info("Verifying tokens...")
    verify_resp = requests.get(
        "https://connectapi.garmin.com/userprofile-service/socialProfile",
        headers={
            "User-Agent": "GCM-iOS-5.7.2.1",
            "Authorization": f"Bearer {oauth2['access_token']}",
        },
        timeout=15,
    )
    verify_resp.raise_for_status()
    profile = verify_resp.json()
    log.info(f"Authenticated as: {profile.get('displayName', 'unknown')}")
    
    token_data = {
        "di_token": oauth2["access_token"],
        "di_refresh_token": oauth2["refresh_token"],
        "di_client_id": "GARMIN_CONNECT_MOBILE_ANDROID_DI_2025Q2",
    }
    
    save_tokens(token_data)
    
    log.info("=" * 40)
    log.info("SUCCESS! Tokens saved.")
    log.info("You can now run the workout uploader!")
    log.info("The browser authentication will be used automatically.")


if __name__ == "__main__":
    main()
