#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║    ███████╗██████╗ ████████╗ ██████╗  ██████╗ ██╗     ███████╗      ║
║    ██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝      ║
║    █████╗  ██████╔╝   ██║   ██║   ██║██║   ██║██║     ███████╗      ║
║    ██╔══╝  ██╔══██╗   ██║   ██║   ██║██║   ██║██║     ╚════██║      ║
║    ██║     ██████╔╝   ██║   ╚██████╔╝╚██████╔╝███████╗███████║      ║
║    ╚═╝     ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚══════╝      ║
║                                                                      ║
║           Facebook Page Manager — Advanced CLI Tool                  ║
║           Works on: Kali Linux | Termux | Ubuntu | Debian            ║
║           Version: 1.0.0 | Author: FBTools Team                     ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import time
import getpass
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.auth        import FBAuthenticator, SessionManager, Color, c
from core.token_watcher import TokenWatcher


# ══════════════════════════════════════════════════════════
def print_banner():
    banner = f"""
{Color.CYAN}{Color.BOLD}
╔══════════════════════════════════════════════════════════════════════╗
║    ███████╗██████╗ ████████╗ ██████╗  ██████╗ ██╗     ███████╗      ║
║    ██╔════╝██╔══██╗╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██╔════╝      ║
║    █████╗  ██████╔╝   ██║   ██║   ██║██║   ██║██║     ███████╗      ║
║    ██╔══╝  ██╔══██╗   ██║   ██║   ██║██║   ██║██║     ╚════██║      ║
║    ██║     ██████╔╝   ██║   ╚██████╔╝╚██████╔╝███████╗███████║      ║
╚══════════════════════════════════════════════════════════════════════╝
{Color.RESET}
{Color.WHITE}  Facebook Page Manager — Advanced CLI Tool{Color.RESET}
{Color.YELLOW}  Works on: Kali Linux | Termux | Ubuntu | Debian{Color.RESET}
{Color.CYAN}  Version 1.0.0{Color.RESET}
"""
    print(banner)


def print_status(session: SessionManager, watcher: TokenWatcher = None):
    """Print current session status."""
    print(c("\n═══ Session Status ═══════════════════════════════", Color.CYAN))
    if not session.is_logged_in():
        print(c("  ✘ Not logged in", Color.RED))
        return

    st = watcher.status() if watcher else {}
    page_name = session.get("page_name", "N/A")
    page_id   = session.get("page_id",   "N/A")
    expires   = session.get("token_expires_str", "N/A")
    time_left = st.get("time_left", 0)

    hours_left = time_left // 3600
    mins_left  = (time_left % 3600) // 60

    color = Color.GREEN if time_left > 3600 else Color.YELLOW if time_left > 0 else Color.RED
    expiry_str = f"{hours_left}h {mins_left}m" if time_left > 0 else "EXPIRED"

    print(c(f"  ✔ Page    : {page_name}", Color.GREEN))
    print(c(f"  ✔ Page ID : {page_id}", Color.GREEN))
    print(c(f"  ✔ Expires : {expires}", Color.GREEN))
    print(c(f"  ✔ Time Left: {expiry_str}", color))
    if watcher:
        watch_status = c("Running ✔", Color.GREEN) if st.get("running") else c("Stopped ✘", Color.RED)
        print(c(f"  ✔ Watcher : {watch_status}", Color.CYAN))
    print(c("══════════════════════════════════════════════════\n", Color.CYAN))


def interactive_login(session: SessionManager, auth: FBAuthenticator):
    """Interactive login prompt."""
    print(c("\n━━━ Login ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", Color.CYAN))
    print(c("  Your credentials are stored LOCALLY only.\n", Color.YELLOW))

    page_id    = input(c("  Page ID      : ", Color.CYAN)).strip()
    email      = input(c("  Email        : ", Color.CYAN)).strip()
    password   = getpass.getpass(c("  Password     : ", Color.CYAN))

    print(c("\n  [Optional] Facebook App credentials for long-lived tokens:", Color.YELLOW))
    print(c("  (Leave blank to use short-lived token ~1h)", Color.YELLOW))
    app_id     = input(c("  App ID       : ", Color.CYAN)).strip() or None
    app_secret = getpass.getpass(c("  App Secret   : ", Color.CYAN)) if app_id else None

    success = auth.login(email, password, page_id, app_id, app_secret)
    return success


def main_menu(session: SessionManager, auth: FBAuthenticator, watcher: TokenWatcher):
    """Main interactive menu."""
    while True:
        print_status(session, watcher)
        print(c("  ┌─────────────────────────────────────┐", Color.CYAN))
        print(c("  │         FBTools Main Menu            │", Color.CYAN))
        print(c("  ├─────────────────────────────────────┤", Color.CYAN))
        print(c("  │  [1] Login / Re-Login                │", Color.WHITE))
        print(c("  │  [2] Show Session Info               │", Color.WHITE))
        print(c("  │  [3] Manual Token Refresh            │", Color.WHITE))
        print(c("  │  [4] Logout (Clear Session)          │", Color.WHITE))
        print(c("  │  [0] Exit                            │", Color.WHITE))
        print(c("  └─────────────────────────────────────┘", Color.CYAN))

        choice = input(c("\n  Select option: ", Color.CYAN)).strip()

        if choice == "1":
            watcher.stop()
            success = interactive_login(session, auth)
            if success:
                watcher = TokenWatcher(session, auth)
                watcher.start()

        elif choice == "2":
            print_status(session, watcher)
            token = session.get("access_token", "")
            if token:
                print(c(f"\n  Token (first 40 chars): {token[:40]}...", Color.YELLOW))
                print(c(f"  Cookies saved: {(Path(__file__).parent / 'config' / 'cookies.pkl').exists()}", Color.YELLOW))

        elif choice == "3":
            print(c("\n[~] Forcing token refresh...", Color.YELLOW))
            ok = auth.refresh_if_needed()
            if ok:
                print(c("✔ Token refreshed.", Color.GREEN))
            else:
                print(c("✘ Refresh failed. Try re-logging in.", Color.RED))

        elif choice == "4":
            confirm = input(c("  Confirm logout? (y/N): ", Color.RED)).strip().lower()
            if confirm == "y":
                watcher.stop()
                session.clear()
                print(c("✔ Logged out. Session cleared.", Color.GREEN))

        elif choice == "0":
            watcher.stop()
            print(c("\n  Goodbye! 👋\n", Color.CYAN))
            sys.exit(0)

        else:
            print(c("  Invalid option.", Color.RED))

        time.sleep(0.5)


# ══════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="FBTools — Facebook Page Manager CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--login",   action="store_true", help="Direct login mode")
    parser.add_argument("--status",  action="store_true", help="Show session status")
    parser.add_argument("--refresh", action="store_true", help="Force token refresh")
    parser.add_argument("--logout",  action="store_true", help="Clear session")
    parser.add_argument("--no-banner", action="store_true", help="Skip banner")
    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    session = SessionManager()
    auth    = FBAuthenticator(session)
    watcher = TokenWatcher(session, auth)

    # Start watcher if already logged in
    if session.is_logged_in():
        watcher.start()

    # CLI mode
    if args.status:
        print_status(session, watcher)
        sys.exit(0)

    if args.refresh:
        ok = auth.refresh_if_needed()
        sys.exit(0 if ok else 1)

    if args.logout:
        session.clear()
        print(c("✔ Session cleared.", Color.GREEN))
        sys.exit(0)

    if args.login:
        success = interactive_login(session, auth)
        if success and not watcher.is_alive():
            watcher.start()
        if not success:
            sys.exit(1)

    # Interactive menu
    try:
        main_menu(session, auth, watcher)
    except KeyboardInterrupt:
        watcher.stop()
        print(c("\n\n  Interrupted. Goodbye! 👋\n", Color.CYAN))
        sys.exit(0)


if __name__ == "__main__":
    main()
