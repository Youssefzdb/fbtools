#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token Watcher — background thread that monitors token expiry
and auto-refreshes before it expires.
"""

import time
import threading
import logging
from datetime import datetime

logger = logging.getLogger("fbtools")


class TokenWatcher(threading.Thread):
    """
    Runs in background, checks every N seconds if token is
    about to expire and triggers refresh automatically.
    """

    def __init__(self, session, authenticator, check_interval: int = 300):
        super().__init__(daemon=True)
        self.session        = session
        self.authenticator  = authenticator
        self.check_interval = check_interval  # default: check every 5 min
        self._stop_event    = threading.Event()
        self._refresh_lock  = threading.Lock()

    def run(self):
        logger.info("TokenWatcher started.")
        while not self._stop_event.is_set():
            try:
                self._check_and_refresh()
            except Exception as e:
                logger.error(f"TokenWatcher error: {e}")
            self._stop_event.wait(self.check_interval)

    def stop(self):
        self._stop_event.set()
        logger.info("TokenWatcher stopped.")

    def _check_and_refresh(self):
        if not self.session.is_logged_in():
            return

        expires_at = self.session.get("token_expires_at", 0)
        time_left  = expires_at - time.time()

        if time_left <= 0:
            logger.warning("Token EXPIRED — attempting refresh.")
            with self._refresh_lock:
                self.authenticator.refresh_if_needed()

        elif time_left <= 3600:  # Less than 1 hour → refresh proactively
            logger.info(f"Token expiring in {int(time_left//60)} min — refreshing proactively.")
            with self._refresh_lock:
                self.authenticator.refresh_if_needed()

    def status(self) -> dict:
        """Return watcher status info."""
        expires_at = self.session.get("token_expires_at", 0)
        time_left  = max(0, expires_at - time.time())
        return {
            "running":    self.is_alive(),
            "time_left":  int(time_left),
            "expires_at": self.session.get("token_expires_str", "N/A"),
            "page":       self.session.get("page_name", "N/A"),
            "page_id":    self.session.get("page_id", "N/A"),
        }
