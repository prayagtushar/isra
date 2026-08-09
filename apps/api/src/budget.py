"""A hard ceiling on how much LLM work the public demo will do per day.

Per-IP rate limits stop one impatient visitor. They do not stop a bot pool, and
the demo is ungated so that recruiters can use it without signing up — so the
thing that actually protects the account balance is a single global counter with
a daily allowance. When it is spent, ``/chat`` stops calling the model and says
so, and retrieval keeps working because it costs nothing per request.

Held in process, which is accurate while the service runs with
``--max-instances 1``. A restart resets the day's tally, so this is a spend
ceiling rather than an audited ledger — the billing budget in GCP is still the
backstop.
"""

import time
from collections.abc import Callable
from dataclasses import dataclass

_SECONDS_PER_DAY = 86400


@dataclass(frozen=True)
class BudgetDecision:
    allowed: bool
    remaining: int
    resets_in_seconds: int


class DailyBudget:
    def __init__(self, limit: int, clock: Callable[[], float] = time.time):
        self._limit = limit
        self._clock = clock
        self._day = self._current_day()
        self._spent = 0

    def _current_day(self) -> int:
        return int(self._clock() // _SECONDS_PER_DAY)

    def _seconds_until_reset(self) -> int:
        now = self._clock()
        next_day_start = (int(now // _SECONDS_PER_DAY) + 1) * _SECONDS_PER_DAY
        return int(next_day_start - now)

    def _roll_over(self) -> None:
        today = self._current_day()
        if today != self._day:
            self._day = today
            self._spent = 0

    def try_spend(self, amount: int = 1) -> BudgetDecision:
        """Reserve `amount` of today's allowance, if there is enough left."""
        # A negative limit disables the ceiling entirely.
        if self._limit < 0:
            return BudgetDecision(
                allowed=True, remaining=-1, resets_in_seconds=self._seconds_until_reset()
            )

        self._roll_over()
        resets_in = self._seconds_until_reset()

        if self._spent + amount > self._limit:
            # Refusals must not accumulate, or a burst of rejected requests would
            # keep the budget exhausted after it should have recovered.
            return BudgetDecision(
                allowed=False,
                remaining=max(0, self._limit - self._spent),
                resets_in_seconds=resets_in,
            )

        self._spent += amount
        return BudgetDecision(
            allowed=True,
            remaining=self._limit - self._spent,
            resets_in_seconds=resets_in,
        )

    def snapshot(self) -> dict:
        if self._limit < 0:
            return {"limit": None, "spent": 0, "remaining": None}
        self._roll_over()
        return {
            "limit": self._limit,
            "spent": self._spent,
            "remaining": max(0, self._limit - self._spent),
        }
