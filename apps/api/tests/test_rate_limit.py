import pytest

from src.rate_limit import (
    RateLimiter,
    Rule,
    client_ip,
    resolve_client,
    rule_for_path,
)


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_limiter(limit=3, window=60.0):
    clock = FakeClock()
    limiter = RateLimiter(default=Rule(limit=limit, window_seconds=window), clock=clock)
    return limiter, clock


def test_requests_under_the_limit_are_allowed():
    limiter, _ = make_limiter(limit=3)
    for _ in range(3):
        assert limiter.check("1.1.1.1", "/search").allowed is True


def test_request_over_the_limit_is_rejected():
    limiter, _ = make_limiter(limit=3)
    for _ in range(3):
        limiter.check("1.1.1.1", "/search")
    decision = limiter.check("1.1.1.1", "/search")
    assert decision.allowed is False


def test_rejection_reports_seconds_until_a_slot_frees():
    limiter, clock = make_limiter(limit=1, window=60.0)
    limiter.check("1.1.1.1", "/search")
    clock.advance(20.0)
    decision = limiter.check("1.1.1.1", "/search")
    assert decision.allowed is False
    assert decision.retry_after == 40


def test_window_slides_so_old_requests_stop_counting():
    limiter, clock = make_limiter(limit=2, window=60.0)
    limiter.check("1.1.1.1", "/search")
    limiter.check("1.1.1.1", "/search")
    assert limiter.check("1.1.1.1", "/search").allowed is False
    clock.advance(61.0)
    assert limiter.check("1.1.1.1", "/search").allowed is True


def test_clients_are_limited_independently():
    limiter, _ = make_limiter(limit=1)
    assert limiter.check("1.1.1.1", "/search").allowed is True
    assert limiter.check("2.2.2.2", "/search").allowed is True
    assert limiter.check("1.1.1.1", "/search").allowed is False


def test_paths_with_different_rules_have_separate_budgets():
    clock = FakeClock()
    limiter = RateLimiter(
        default=Rule(limit=5, window_seconds=60.0),
        rules={"/chat": Rule(limit=1, window_seconds=60.0)},
        clock=clock,
    )
    assert limiter.check("1.1.1.1", "/chat").allowed is True
    assert limiter.check("1.1.1.1", "/chat").allowed is False
    # Exhausting /chat must not consume the /search budget.
    assert limiter.check("1.1.1.1", "/search").allowed is True


def test_remaining_counts_down():
    limiter, _ = make_limiter(limit=3)
    assert limiter.check("1.1.1.1", "/search").remaining == 2
    assert limiter.check("1.1.1.1", "/search").remaining == 1


def test_idle_clients_are_evicted_so_memory_does_not_grow_forever():
    limiter, clock = make_limiter(limit=3, window=60.0)
    for i in range(100):
        limiter.check(f"10.0.0.{i}", "/search")
    clock.advance(3600.0)
    limiter.check("1.1.1.1", "/search")
    assert limiter.tracked_clients() == 1


def test_health_checks_are_never_limited():
    assert rule_for_path("/health") is None


def test_chat_is_limited_more_tightly_than_search():
    chat = rule_for_path("/chat")
    search = rule_for_path("/search")
    assert chat is not None and search is not None
    chat_per_hour = chat.limit * (3600 / chat.window_seconds)
    search_per_hour = search.limit * (3600 / search.window_seconds)
    assert chat_per_hour < search_per_hour


@pytest.mark.parametrize(
    "path", ["/auth/signin", "/auth/signup", "/auth/forgot-password"]
)
def test_auth_endpoints_are_rate_limited(path):
    # Unlimited password guesses against hand-rolled auth is the whole problem.
    assert rule_for_path(path) is not None


def test_client_ip_uses_socket_peer_when_no_proxy_is_trusted():
    assert client_ip("9.9.9.9", peer="5.5.5.5", trusted_hops=0) == "5.5.5.5"


def test_client_ip_skips_the_trusted_proxy_entry():
    # Cloud Run appends its own hop, so the caller is second from the right.
    assert (
        client_ip("203.0.113.7, 130.211.0.1", peer="130.211.0.1", trusted_hops=1)
        == "203.0.113.7"
    )


def test_client_ip_ignores_extra_spoofed_entries_to_the_left():
    # A client can prepend anything it likes; only the trusted tail is reliable.
    assert (
        client_ip(
            "1.2.3.4, 203.0.113.7, 130.211.0.1", peer="130.211.0.1", trusted_hops=1
        )
        == "203.0.113.7"
    )


def test_client_ip_falls_back_to_peer_when_header_is_missing():
    assert client_ip(None, peer="5.5.5.5", trusted_hops=1) == "5.5.5.5"


def test_client_ip_handles_unknown_peer():
    assert client_ip(None, peer=None, trusted_hops=0) == "unknown"


# --- Client identity behind the Next.js proxy -------------------------------
# Browser traffic reaches this API through the web app's server-side proxy, so
# every request arrives from the same handful of hosting egress addresses. Keyed
# on those, one visitor's traffic would exhaust the budget for everyone.


def test_uses_proxy_supplied_ip_when_the_shared_secret_matches():
    assert (
        resolve_client(
            proxy_client_ip="203.0.113.7",
            proxy_secret_header="s3cret",
            proxy_secret="s3cret",
            forwarded_for=None,
            peer="10.0.0.1",
            trusted_hops=1,
        )
        == "203.0.113.7"
    )


def test_ignores_proxy_supplied_ip_when_the_secret_is_wrong():
    assert (
        resolve_client(
            proxy_client_ip="203.0.113.7",
            proxy_secret_header="wrong",
            proxy_secret="s3cret",
            forwarded_for=None,
            peer="10.0.0.1",
            trusted_hops=1,
        )
        == "10.0.0.1"
    )


def test_ignores_proxy_supplied_ip_when_no_secret_is_configured():
    # Without a configured secret the header is attacker-controlled: anyone
    # could send a random address per request and never hit a limit.
    assert (
        resolve_client(
            proxy_client_ip="203.0.113.7",
            proxy_secret_header="anything",
            proxy_secret=None,
            forwarded_for=None,
            peer="10.0.0.1",
            trusted_hops=1,
        )
        == "10.0.0.1"
    )


def test_falls_back_to_the_forwarded_chain_when_proxy_header_absent():
    assert (
        resolve_client(
            proxy_client_ip=None,
            proxy_secret_header=None,
            proxy_secret="s3cret",
            forwarded_for="198.51.100.9, 130.211.0.1",
            peer="130.211.0.1",
            trusted_hops=1,
        )
        == "198.51.100.9"
    )
