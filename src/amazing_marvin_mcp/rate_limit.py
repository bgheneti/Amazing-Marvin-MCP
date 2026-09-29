"""Client-side pacing for Marvin's documented API rate limits.

Marvin asks API users not to create more than 1 item per second, not to burst
more than 1 query every 3 seconds, and not to exceed 1440 queries per day:
https://github.com/amazingmarvin/MarvinAPI/wiki#rate-limits

The daily counter is kept in memory, so it only covers calls made through this
limiter by the current server process.
"""

import logging
import threading
import time
from collections.abc import Callable
from datetime import date

logger = logging.getLogger(__name__)

CREATE_INTERVAL_SECONDS = 1.0
QUERY_INTERVAL_SECONDS = 3.0
DAILY_REQUEST_LIMIT = 1440


class DailyLimitExceededError(Exception):
    """Raised when the daily request budget has been used up."""


class RateLimiter:
    """Spaces requests apart and enforces a per-day request budget."""

    def __init__(
        self,
        daily_limit: int = DAILY_REQUEST_LIMIT,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
        today: Callable[[], date] = date.today,
    ):
        self.daily_limit = daily_limit
        self._clock = clock
        self._sleep = sleep
        self._today = today
        self._lock = threading.Lock()
        self._last_request: float | None = None
        self._day = today()
        self._used_today = 0

    def _roll_day(self) -> None:
        current_day = self._today()
        if current_day != self._day:
            self._day = current_day
            self._used_today = 0

    @property
    def remaining_today(self) -> int:
        """Requests left in today's budget."""
        with self._lock:
            self._roll_day()
            return max(self.daily_limit - self._used_today, 0)

    def acquire(self, min_interval: float) -> None:
        """Wait until a request may be sent, then count it against today's budget.

        Raises:
            DailyLimitExceededError: if today's budget is already used up.
        """
        with self._lock:
            self._roll_day()
            if self._used_today >= self.daily_limit:
                raise DailyLimitExceededError(
                    f"Daily Marvin API budget of {self.daily_limit} requests used up"
                )
            if self._last_request is not None:
                wait = self._last_request + min_interval - self._clock()
                if wait > 0:
                    logger.debug("Rate limiting: sleeping %.2fs", wait)
                    self._sleep(wait)
            self._last_request = self._clock()
            self._used_today += 1


# Shared by all tools in this process so the daily budget spans tool calls.
default_rate_limiter = RateLimiter()
