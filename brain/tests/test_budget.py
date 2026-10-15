"""Tests for the budget guard (Bauplan Gehirn 7.3, CLAUDE.md section 4)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from brain.budget import BudgetConfig, BudgetGuard, PriceTable, Usage
from brain.eventlog import EventLog
from brain.tests.helpers import FakeClock

CONFIG_DIR = Path(__file__).resolve().parents[1] / "config"


@pytest.fixture
def prices():
    return PriceTable.from_file(CONFIG_DIR / "prices.toml")


@pytest.fixture
def config():
    return BudgetConfig.from_file(CONFIG_DIR / "budget.toml")


def small_config(total=1.0, research=0.5, self_opt=0.2, rate=1.0, rate_date="2026-10-15"):
    """Artificially low limits for threshold tests (Bauplan 7.3 test)."""
    return BudgetConfig(
        usd_per_eur=rate,
        rate_date=rate_date,
        max_rate_age_days=31,
        limits_eur={"total": total, "research": research, "self_optimization": self_opt},
        thresholds={"warn": 0.8, "save": 0.9, "stop": 1.0},
    )


# --- prices -----------------------------------------------------------------


def test_sonnet_cost_from_api_usage(prices):
    usage = Usage.from_api({"input_tokens": 1_000_000, "output_tokens": 100_000})
    assert prices.cost_usd("claude-sonnet-5-5", usage) == pytest.approx(2.0 + 1.0)


def test_cache_tokens_are_priced_separately(prices):
    usage = Usage.from_api(
        {
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 3_000_000,
            "cache_creation": {"ephemeral_5m_input_tokens": 1_000_000, "ephemeral_1h_input_tokens": 2_000_000},
        }
    )
    # Opus 5.5: read 0.20, 5m write 5.0, 1h write 8.0 per MTok
    assert prices.cost_usd("claude-opus-5-5", usage) == pytest.approx(0.20 + 5.0 + 16.0)


def test_cache_writes_without_breakdown_count_as_five_minute_writes(prices):
    usage = Usage.from_api({"input_tokens": 0, "output_tokens": 0, "cache_creation_input_tokens": 1_000_000})
    assert usage.cache_write_5m == 1_000_000 and usage.cache_write_1h == 0
    assert prices.cost_usd("claude-sonnet-5-5", usage) == pytest.approx(2.50)


def test_web_searches_cost_one_cent_each(prices):
    usage = Usage.from_api(
        {"input_tokens": 0, "output_tokens": 0, "server_tool_use": {"web_search_requests": 3, "web_fetch_requests": 5}}
    )
    assert prices.cost_usd("claude-haiku-5-5", usage) == pytest.approx(0.03)


def test_haiku_switches_to_the_long_prompt_rate_card(prices):
    short = Usage.from_api({"input_tokens": 100_000, "output_tokens": 1_000})
    long_ = Usage.from_api({"input_tokens": 60_000, "cache_read_input_tokens": 40_001, "output_tokens": 1_000})
    assert prices.cost_usd("claude-haiku-5-5", short) == pytest.approx(0.1 * 0.10 + 0.001 * 0.50)
    # over 100,000 prompt tokens (cache reads count): every category at the long-prompt prices
    assert prices.cost_usd("claude-haiku-5-5", long_) == pytest.approx(0.06 * 0.50 + 0.040001 * 0.05 + 0.001 * 2.50)


def test_unknown_model_is_reported(prices):
    with pytest.raises(KeyError):
        prices.cost_usd("claude-unknown-9", Usage.from_api({"input_tokens": 1, "output_tokens": 1}))


def test_price_table_names_its_source(prices):
    assert prices.source.startswith("https://platform.claude.com/")
    assert prices.checked == "2026-10-15"


# --- configuration ------------------------------------------------------------


def test_real_config_matches_the_decisions(config):
    assert config.limits_eur == {"total": 20.0, "research": 10.0, "self_optimization": 4.0}
    assert config.thresholds == {"warn": 0.8, "save": 0.9, "stop": 1.0}
    assert config.usd_per_eur > 0


def test_config_rejects_inconsistent_limits():
    with pytest.raises(ValueError):
        small_config(total=1.0, research=2.0)
    with pytest.raises(ValueError):
        small_config(research=0.5, self_opt=0.6)


# --- guard --------------------------------------------------------------------


def test_recorded_costs_appear_in_the_event_log(log, prices, config, clock):
    guard = BudgetGuard(log, prices, config, clock=clock)
    cost = guard.record(
        "conversation", "claude-sonnet-5-5", {"input_tokens": 1000, "output_tokens": 500}, request_id="req_1"
    )

    usage_events = list(log.iter_events(types={"budget.usage"}))
    assert len(usage_events) == 1
    payload = usage_events[0]["payload"]
    assert payload["category"] == "conversation"
    assert payload["model"] == "claude-sonnet-5-5"
    assert payload["request_id"] == "req_1"
    assert payload["cost_usd"] == pytest.approx(cost.usd)
    assert cost.eur == pytest.approx(cost.usd / config.usd_per_eur)


def test_levels_follow_the_thresholds(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)

    def spend(usd):
        # Sonnet output: 10 USD per MTok, so 100,000 output tokens cost 1 USD
        guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": int(usd * 100_000)})

    assert guard.check("conversation").level == "normal"
    spend(0.80)
    assert guard.check("conversation").level == "warn"
    spend(0.10)
    assert guard.check("conversation").level == "save"
    assert guard.check("conversation").allowed
    spend(0.10)
    decision = guard.check("conversation")
    assert decision.level == "stop" and not decision.allowed


def test_each_level_is_alerted_once(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    for _ in range(12):
        guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 10_000})  # 0.10 USD each

    alerts = [(e["payload"]["pot"], e["payload"]["level"]) for e in log.iter_events(types={"budget.alert"})]
    assert alerts == [("total", "warn"), ("total", "save"), ("total", "stop")]


def test_research_cannot_eat_the_conversation_budget(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(total=1.0, research=0.5, self_opt=0.2), clock=clock)
    guard.record("research", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 50_000})  # 0.50 USD

    assert guard.check("research").level == "stop"
    assert not guard.check("self_optimization").allowed  # part of research
    assert guard.check("conversation").allowed


def test_self_optimization_has_its_own_cap_inside_research(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(total=1.0, research=0.5, self_opt=0.2), clock=clock)
    guard.record("self_optimization", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 20_000})  # 0.20 USD

    assert not guard.check("self_optimization").allowed
    assert guard.check("research").level == "normal"  # 0.20 of 0.50 = 40 %
    assert guard.status()["pots"]["research"]["spent_eur"] == pytest.approx(0.20)


def test_estimate_prevents_crossing_the_limit(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 50_000})  # 0.50 USD
    assert guard.check("conversation", estimate_usd=0.40).allowed
    assert not guard.check("conversation", estimate_usd=0.60).allowed


def test_euro_limits_are_converted_with_the_rate(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(total=1.0, research=0.5, self_opt=0.2, rate=2.0), clock=clock)
    guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 100_000})  # 1 USD = 0.50 EUR
    status = guard.status()
    assert status["pots"]["total"]["spent_eur"] == pytest.approx(0.50)
    assert status["pots"]["total"]["level"] == "normal"


def test_a_new_month_starts_from_zero(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 100_000})
    assert not guard.check("conversation").allowed
    clock.now = datetime(2026, 11, 1, 0, 0, 1, tzinfo=UTC)
    assert guard.check("conversation").allowed
    assert guard.status()["month"] == "2026-11"


def test_a_restarted_guard_knows_the_spending_of_the_month(tmp_path, prices, clock):
    first = BudgetGuard(EventLog(tmp_path / "events", source="a", clock=clock), prices, small_config(), clock=clock)
    first.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 95_000})
    second = BudgetGuard(EventLog(tmp_path / "events", source="b", clock=clock), prices, small_config(), clock=clock)
    assert second.check("conversation").level == "save"


def test_spending_from_another_process_is_seen(tmp_path, prices, clock):
    guard = BudgetGuard(EventLog(tmp_path / "events", source="a", clock=clock), prices, small_config(), clock=clock)
    other = BudgetGuard(EventLog(tmp_path / "events", source="b", clock=clock), prices, small_config(), clock=clock)
    other.record("research", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 90_000})
    assert guard.check("conversation").level == "save"


def test_unknown_model_is_charged_at_the_most_expensive_price(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    cost = guard.record("conversation", "claude-unknown-9", {"input_tokens": 0, "output_tokens": 10_000})
    event = next(log.iter_events(types={"budget.usage"}))
    assert event["payload"]["price_fallback"] is True
    assert cost.usd == pytest.approx(0.01 * 20.0)  # Opus output price is the highest in the table


def test_unknown_category_is_rejected(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    with pytest.raises(ValueError):
        guard.check("shopping")


def test_a_stale_exchange_rate_is_alerted_once_per_month(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(rate_date="2026-08-01"), clock=clock)
    guard.record("conversation", "claude-haiku-5-5", {"input_tokens": 10, "output_tokens": 10})
    guard.record("conversation", "claude-haiku-5-5", {"input_tokens": 10, "output_tokens": 10})
    alerts = [e["payload"] for e in log.iter_events(types={"budget.alert"})]
    assert [(a["pot"], a["level"]) for a in alerts] == [("rate", "warn")]
    assert "rate_stale" in guard.status()["warnings"]


@settings(max_examples=40, deadline=None)
@given(tokens=st.lists(st.integers(min_value=0, max_value=60_000), min_size=1, max_size=15))
def test_stop_is_never_passed_when_checking_with_an_estimate(tmp_path_factory, tokens):
    """Property: a caller that asks with the worst-case estimate first never ends above the limit."""
    clock = FakeClock()
    log = EventLog(tmp_path_factory.mktemp("events"), source="prop", clock=clock)
    prices = PriceTable.from_file(CONFIG_DIR / "prices.toml")
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    for output_tokens in tokens:
        estimate = output_tokens * 10.0 / 1_000_000
        if guard.check("conversation", estimate_usd=estimate).allowed:
            guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": output_tokens})
    assert guard.status()["pots"]["total"]["spent_eur"] <= 1.0 + 1e-9


usage_parts = st.builds(
    Usage,
    input=st.integers(0, 50_000),
    output=st.integers(0, 50_000),
    cache_write_5m=st.integers(0, 20_000),
    cache_write_1h=st.integers(0, 20_000),
    cache_read=st.integers(0, 20_000),
    web_search=st.integers(0, 5),
    web_fetch=st.integers(0, 5),
)


@settings(max_examples=200, deadline=None)
@given(a=usage_parts, b=usage_parts)
def test_costs_add_up_exactly(a, b):
    """Additivity: two calls cost exactly as much as one call with both usages (same rate card)."""
    prices = PriceTable.from_file(CONFIG_DIR / "prices.toml")
    both = Usage(**{name: getattr(a, name) + getattr(b, name) for name in a.__dataclass_fields__})
    for model in ("claude-opus-5-5", "claude-sonnet-5-5"):
        assert prices.cost_nano(model, a) + prices.cost_nano(model, b) == prices.cost_nano(model, both)


# --- findings of the code review (15.10.2026) -----------------------------------------------


def test_the_guard_stops_before_the_console_limit(config):
    """Real config: 20 EUR would be 22.42 USD, above the Console limit of 22 USD."""
    assert config.limit_nano("total") == 22_000_000_000
    # research leaves at least 10 EUR (11.208 USD) for conversations
    assert config.limit_nano("research") == 22_000_000_000 - 11_208_000_000
    assert config.limit_nano("self_optimization") == 4_483_200_000


def test_research_always_leaves_the_conversation_minimum(log, prices, clock):
    config = BudgetConfig(
        usd_per_eur=1.0,
        rate_date="2026-10-15",
        max_rate_age_days=31,
        limits_eur={"total": 1.0, "research": 0.5, "self_optimization": 0.2},
        thresholds={"warn": 0.8, "save": 0.9, "stop": 1.0},
        min_conversation_eur=0.8,
    )
    assert config.limit_nano("research") == 200_000_000
    guard = BudgetGuard(log, prices, config, clock=clock)
    guard.record("research", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 20_000})  # 0.20 USD
    assert not guard.check("research").allowed
    assert guard.check("conversation").allowed


def test_a_minimum_that_leaves_nothing_for_research_is_refused():
    with pytest.raises(ValueError):
        BudgetConfig(
            usd_per_eur=1.0,
            rate_date="2026-10-15",
            max_rate_age_days=31,
            limits_eur={"total": 1.0, "research": 0.5, "self_optimization": 0.2},
            thresholds={"warn": 0.8, "save": 0.9, "stop": 1.0},
            min_conversation_eur=1.0,
        )


def test_a_broken_budget_event_does_not_hide_later_spending(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    log.append("budget.alert", {"pot": "total", "level": "info"})  # written by a buggy component
    log.append("budget.usage", {"category": "conversation", "cost_nano_usd": "viel"})
    guard.record("conversation", "claude-sonnet-5-5", {"input_tokens": 0, "output_tokens": 95_000})  # 0.95 USD

    assert guard.check("conversation").level == "save"
    assert "malformed_budget_events:2" in guard.status()["warnings"]


def test_a_model_without_prices_is_refused_before_the_call(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    decision = guard.check("conversation", model="claude-unknown-9")
    assert not decision.allowed and "no prices" in decision.reason
    assert guard.check("conversation", model="claude-sonnet-5-5").allowed


def test_an_unknown_model_is_alerted_once_per_month(log, prices, clock):
    guard = BudgetGuard(log, prices, small_config(), clock=clock)
    for _ in range(2):
        guard.record("conversation", "claude-unknown-9", {"input_tokens": 1, "output_tokens": 1})
    alerts = [e["payload"] for e in log.iter_events(types={"budget.alert"})]
    assert alerts == [{"pot": "prices", "level": "warn", "model": "claude-unknown-9"}]


def test_usage_in_a_foreign_format_is_refused():
    with pytest.raises(ValueError, match="unknown usage format"):
        Usage.from_api({"prompt_tokens": 10, "completion_tokens": 5})
