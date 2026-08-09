from src.budget import DailyBudget

# 2026-08-08T00:00:00Z
DAY_START = 1786492800.0
HOUR = 3600.0


class FakeClock:
    def __init__(self, now: float = DAY_START):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_budget(limit=3, at=DAY_START):
    clock = FakeClock(at)
    return DailyBudget(limit=limit, clock=clock), clock


def test_spends_are_allowed_up_to_the_limit():
    budget, _ = make_budget(limit=3)
    assert [budget.try_spend().allowed for _ in range(3)] == [True, True, True]


def test_spend_beyond_the_limit_is_refused():
    budget, _ = make_budget(limit=2)
    budget.try_spend()
    budget.try_spend()
    assert budget.try_spend().allowed is False


def test_refused_spend_does_not_consume_budget():
    budget, clock = make_budget(limit=1)
    budget.try_spend()
    for _ in range(5):
        budget.try_spend()
    # Next day the full allowance is back, not a backlog of refusals.
    clock.advance(24 * HOUR)
    assert budget.try_spend().allowed is True


def test_allowance_resets_at_the_next_utc_day():
    budget, clock = make_budget(limit=1)
    assert budget.try_spend().allowed is True
    clock.advance(23 * HOUR)
    assert budget.try_spend().allowed is False
    clock.advance(2 * HOUR)
    assert budget.try_spend().allowed is True


def test_reports_remaining_allowance():
    budget, _ = make_budget(limit=3)
    assert budget.try_spend().remaining == 2
    assert budget.try_spend().remaining == 1


def test_refusal_reports_seconds_until_reset():
    budget, clock = make_budget(limit=1)
    budget.try_spend()
    clock.advance(6 * HOUR)
    decision = budget.try_spend()
    assert decision.allowed is False
    assert decision.resets_in_seconds == int(18 * HOUR)


def test_zero_limit_blocks_everything():
    # A deliberate kill switch: set the limit to 0 to stop all spending.
    budget, _ = make_budget(limit=0)
    assert budget.try_spend().allowed is False


def test_negative_limit_means_unlimited():
    budget, _ = make_budget(limit=-1)
    assert all(budget.try_spend().allowed for _ in range(50))
