"""A hard daily ceiling on LLM spend for the open demo. In process, accurate at --max-instances 1."""

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
            # Refusals must not accumulate, or rejected requests would keep the budget exhausted.
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
