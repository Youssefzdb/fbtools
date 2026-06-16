#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║           FBTools - Facebook Page Manager                ║
║           Authentication & Token Manager                 ║
║           Version: 1.0.0                                 ║
╚══════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import requests
import hashlib
import pickle
import logging
from datetime import datetime, timedelta
from pathlib import Path

# ─── Colors ───────────────────────────────────────────────
class Color:
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'
    BOLD    = '\033[1m'
    RESET   = '\033[0m'

def c(text, color):
    return f"{color}{text}{Color.RESET}"

# ─── Logging ──────────────────────────────────────────────
log_dir = Path(__file__).parent.parent / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    filename=str(log_dir / "fbtools.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("fbtools")

# ─── Config ───────────────────────────────────────────────
CONFIG_DIR  = Path(__file__).parent.parent / "config"
SESSION_FILE = CONFIG_DIR / "session.json"
COOKIES_FILE = CONFIG_DIR / "cookies.pkl"

CONFIG_DIR.mkdir(exist_ok=True)

# ─── Facebook API ─────────────────────────────────────────
FB_API_VERSION = "v19.0"
FB_API_BASE    = f"https://graph.facebook.com/{FB_API_VERSION}"
FB_LOGIN_URL   = "https://mbasic.facebook.com"

# ─── Token Lifetime (seconds) ─────────────────────────────
SHORT_TOKEN_LIFETIME  = 3600          # 1 hour
LONG_TOKEN_LIFETIME   = 60 * 24 * 3600  # 60 days


# ══════════════════════════════════════════════════════════
class SessionManager:
    """Manages session data: tokens, cookies, and page info."""

    def __init__(self):
        self.session_data = {}
        self.load()

    def load(self):
        if SESSION_FILE.exists():
            try:
                with open(SESSION_FILE, "r") as f:
                    self.session_data = json.load(f)
                logger.info("Session loaded from disk.")
            except Exception as e:
                logger.warning(f"Could not load session: {e}")
                self.session_data = {}

    def save(self):
        try:
            with open(SESSION_FILE, "w") as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
            logger.info("Session saved to disk.")
        except Exception as e:
            logger.error(f"Could not save session: {e}")

    def clear(self):
        self.session_data = {}
        SESSION_FILE.unlink(missing_ok=True)
        COOKIES_FILE.unlink(missing_ok=True)
        logger.info("Session cleared.")

    def set(self, key, value):
        self.session_data[key] = value
        self.save()

    def get(self, key, default=None):
        return self.session_data.get(key, default)

    def is_logged_in(self):
        return bool(self.session_data.get("access_token"))

    def is_token_expired(self):
        expires_at = self.session_data.get("token_expires_at", 0)
        return time.time() >= expires_at - 300  # 5 min buffer

    def save_cookies(self, cookies):
        with open(COOKIES_FILE, "wb") as f:
            pickle.dump(cookies, f)

    def load_cookies(self):
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, "rb") as f:
                return pickle.load(f)
        return None


# ══════════════════════════════════════════════════════════
class FBAuthenticator:
    """
    Handles Facebook authentication flow:
    1. Login with email/password → get short-lived token
    2. Exchange for long-lived user token
    3. Get page access token
    4. Auto-refresh when expired
    """

    # Facebook's unofficial app credentials (mobile)
    _FB_APP_ID     = "2220391788000475"
    _FB_APP_SECRET = ""  # Will use user-provided

    def __init__(self, session: SessionManager):
        self.session = session
        self.http = requests.Session()
        self.http.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 12; Pixel 5) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "ar,en;q=0.9",
        })
        # Restore saved cookies
        cookies = self.session.load_cookies()
        if cookies:
            self.http.cookies.update(cookies)

    # ── Public API ─────────────────────────────────────────

    def login(self, email: str, password: str, page_id: str,
              app_id: str = None, app_secret: str = None) -> bool:
        """
        Full login flow:
        - Authenticate user
        - Get long-lived user token
        - Get page access token
        Returns True on success.
        """
        print(c("\n[*] Starting authentication flow...", Color.CYAN))
        logger.info(f"Login attempt for page_id={page_id}")

        try:
            # Step 1: Get short-lived token via login
            short_token = self._login_step(email, password)
            if not short_token:
                return False

            # Step 2: Exchange for long-lived token
            if app_id and app_secret:
                long_token, expires_in = self._exchange_long_token(
                    short_token, app_id, app_secret
                )
            else:
                # Use short token directly (expires in ~1h)
                long_token = short_token
                expires_in = SHORT_TOKEN_LIFETIME
                print(c("[!] No App credentials provided — token valid ~1 hour.", Color.YELLOW))
                print(c("    Tip: Provide App ID & Secret for 60-day tokens.", Color.YELLOW))

            if not long_token:
                return False

            # Step 3: Get page token
            page_token, page_name = self._get_page_token(long_token, page_id)
            if not page_token:
                return False

            # Step 4: Save everything
            now = time.time()
            self.session.set("email", email)
            self.session.set("page_id", page_id)
            self.session.set("page_name", page_name)
            self.session.set("user_token", long_token)
            self.session.set("access_token", page_token)
            self.session.set("token_created_at", now)
            self.session.set("token_expires_at", now + expires_in)
            self.session.set("token_expires_str",
                str(datetime.fromtimestamp(now + expires_in)))
            self.session.set("app_id", app_id or "")
            self.session.set("app_secret", app_secret or "")
            self.session.save_cookies(dict(self.http.cookies))

            print(c(f"\n✔ Logged in successfully!", Color.GREEN + Color.BOLD))
            print(c(f"  Page  : {page_name} ({page_id})", Color.GREEN))
            print(c(f"  Token : {page_token[:30]}...", Color.GREEN))
            print(c(f"  Expires: {self.session.get('token_expires_str')}", Color.GREEN))
            logger.info(f"Login success. Page: {page_name} ({page_id})")
            return True

        except Exception as e:
            print(c(f"\n✘ Login error: {e}", Color.RED))
            logger.error(f"Login error: {e}", exc_info=True)
            return False

    def refresh_if_needed(self) -> bool:
        """Check token expiry and refresh if needed."""
        if not self.session.is_logged_in():
            return False

        if not self.session.is_token_expired():
            return True  # Still valid

        print(c("\n[~] Token expired — refreshing...", Color.YELLOW))
        logger.info("Token expired. Attempting refresh.")

        email      = self.session.get("email")
        app_id     = self.session.get("app_id")
        app_secret = self.session.get("app_secret")
        page_id    = self.session.get("page_id")

        if app_id and app_secret:
            # Try to refresh using existing user token
            user_token = self.session.get("user_token")
            new_long, expires_in = self._exchange_long_token(
                user_token, app_id, app_secret
            )
            if new_long:
                page_token, page_name = self._get_page_token(new_long, page_id)
                if page_token:
                    now = time.time()
                    self.session.set("user_token", new_long)
                    self.session.set("access_token", page_token)
                    self.session.set("token_created_at", now)
                    self.session.set("token_expires_at", now + expires_in)
                    self.session.set("token_expires_str",
                        str(datetime.fromtimestamp(now + expires_in)))
                    print(c("✔ Token refreshed successfully.", Color.GREEN))
                    logger.info("Token refreshed via long-lived exchange.")
                    return True

        print(c("[!] Could not auto-refresh. Please re-login.", Color.RED))
        return False

    def get_valid_token(self) -> str | None:
        """Returns valid page token, refreshing if needed."""
        if self.refresh_if_needed():
            return self.session.get("access_token")
        return None

    # ── Private Helpers ────────────────────────────────────

    def _login_step(self, email: str, password: str) -> str | None:
        """
        Authenticate via Facebook Graph API using
        facebook_login endpoint (requires app credentials)
        or mbasic flow to get access token.
        """
        print(c("  [1/3] Authenticating user...", Color.CYAN))

        # Try Graph API token endpoint
        try:
            resp = self.http.get(
                "https://graph.facebook.com/oauth/access_token",
                params={
                    "client_id": "124024574287414",  # FB Lite App ID
                    "client_secret": "",
                    "grant_type": "password",
                    "username": email,
                    "password": password,
                    "scope": "pages_manage_posts,pages_read_engagement,"
                             "pages_manage_engagement,pages_messaging,"
                             "pages_manage_metadata,publish_to_groups",
                },
                timeout=15
            )
            data = resp.json()
            if "access_token" in data:
                print(c("  ✔ User authenticated via Graph API.", Color.GREEN))
                return data["access_token"]
        except Exception:
            pass

        # Fallback: mobile mbasic flow
        return self._mbasic_login(email, password)

    def _mbasic_login(self, email: str, password: str) -> str | None:
        """Login via mbasic.facebook.com and extract token from cookies/redirect."""
        try:
            # Get login page
            r = self.http.get(f"{FB_LOGIN_URL}/login/", timeout=15)
            # Parse form fields
            from html.parser import HTMLParser

            class FormParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.fields = {}
                    self.action = ""
                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if tag == "input" and attrs.get("name"):
                        self.fields[attrs["name"]] = attrs.get("value", "")
                    if tag == "form" and attrs.get("action"):
                        self.action = attrs["action"]

            parser = FormParser()
            parser.feed(r.text)

            form_data = parser.fields
            form_data["email"]  = email
            form_data["pass"]   = password
            form_data["login"]  = "Log In"

            action = parser.action or f"{FB_LOGIN_URL}/login/device-based/regular/login/"

            resp = self.http.post(action, data=form_data,
                                  allow_redirects=True, timeout=15)

            # Save cookies
            self.session.save_cookies(dict(self.http.cookies))

            # Try to extract token from cookies
            for name, value in self.http.cookies.items():
                if name in ("c_user", "xs"):
                    # Build token from session
                    token = self._extract_token_from_cookies()
                    if token:
                        return token

            # Check for checkpoint / 2FA
            if "checkpoint" in resp.url or "two_step" in resp.text.lower():
                print(c("  [!] 2FA or checkpoint detected!", Color.YELLOW))
                code = input(c("  Enter 2FA code: ", Color.CYAN)).strip()
                return self._handle_2fa(resp, code)

            print(c("  ✘ mbasic login failed.", Color.RED))
            return None

        except Exception as e:
            logger.error(f"mbasic login error: {e}")
            return None

    def _handle_2fa(self, resp, code: str) -> str | None:
        """Handle two-factor authentication."""
        try:
            from html.parser import HTMLParser
            class FormParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.fields = {}
                    self.action = ""
                def handle_starttag(self, tag, attrs):
                    attrs = dict(attrs)
                    if tag == "input" and attrs.get("name"):
                        self.fields[attrs["name"]] = attrs.get("value", "")
                    if tag == "form" and attrs.get("action"):
                        self.action = attrs["action"]

            parser = FormParser()
            parser.feed(resp.text)
            form_data = parser.fields
            form_data["approvals_code"] = code

            action = parser.action
            if not action.startswith("http"):
                action = FB_LOGIN_URL + action

            r = self.http.post(action, data=form_data,
                               allow_redirects=True, timeout=15)
            self.session.save_cookies(dict(self.http.cookies))
            return self._extract_token_from_cookies()
        except Exception as e:
            logger.error(f"2FA error: {e}")
            return None

    def _extract_token_from_cookies(self) -> str | None:
        """Try to build or extract access token from session cookies."""
        cookies = dict(self.http.cookies)
        c_user = cookies.get("c_user")
        xs     = cookies.get("xs")
        if c_user and xs:
            # Use EAABsbCS0... style token from cookies if available
            # Otherwise return a placeholder that triggers Graph API flow
            for k, v in cookies.items():
                if v and v.startswith("EAA"):
                    return v
            # Return composite indicator — caller will use Graph flow
            return f"cookie_session:{c_user}:{xs}"
        return None

    def _exchange_long_token(self, short_token: str,
                              app_id: str, app_secret: str):
        """Exchange short-lived token for 60-day long-lived token."""
        print(c("  [2/3] Exchanging for long-lived token...", Color.CYAN))
        try:
            resp = self.http.get(
                f"{FB_API_BASE}/oauth/access_token",
                params={
                    "grant_type":        "fb_exchange_token",
                    "client_id":          app_id,
                    "client_secret":      app_secret,
                    "fb_exchange_token":  short_token,
                },
                timeout=15
            )
            data = resp.json()
            if "access_token" in data:
                expires_in = data.get("expires_in", LONG_TOKEN_LIFETIME)
                print(c(f"  ✔ Long-lived token obtained ({expires_in//86400} days).", Color.GREEN))
                return data["access_token"], expires_in
            else:
                print(c(f"  ✘ Token exchange failed: {data.get('error', {}).get('message', data)}", Color.RED))
                return None, 0
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None, 0

    def _get_page_token(self, user_token: str, page_id: str):
        """Get page-specific access token from user token."""
        print(c("  [3/3] Getting page access token...", Color.CYAN))
        try:
            resp = self.http.get(
                f"{FB_API_BASE}/me/accounts",
                params={"access_token": user_token, "limit": 50},
                timeout=15
            )
            data = resp.json()
            if "data" not in data:
                print(c(f"  ✘ Could not fetch pages: {data.get('error', {}).get('message', data)}", Color.RED))
                return None, None

            for page in data["data"]:
                if str(page.get("id")) == str(page_id):
                    print(c(f"  ✔ Page token obtained: {page['name']}", Color.GREEN))
                    return page["access_token"], page["name"]

            # List available pages if not found
            print(c(f"  ✘ Page ID {page_id} not found in your pages.", Color.RED))
            print(c("  Your pages:", Color.YELLOW))
            for page in data["data"]:
                print(c(f"    - {page['name']} → ID: {page['id']}", Color.YELLOW))
            return None, None

        except Exception as e:
            logger.error(f"Page token error: {e}")
            return None, None
