"""Budget guard: prices every API call from its usage data and enforces monthly limits.

The event log is the single source of truth: every call is recorded as a
`budget.usage` event, level changes as `budget.alert` events. The guard reads new
events incrementally, so several processes (conversation, research) share one budget.
Money is counted in integer nano-dollars to avoid rounding drift.
"""

import tomllib
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

NANO = Decimal(1_000_000_000)
LEVELS = ("normal", "warn", "save", "stop")
CATEGORIES = {
    "conversation": ("total",),
    "research": ("total", "research"),
    "self_optimization": ("total", "research", "self_optimization"),
}
_PRICE_FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")


def _utc_now():
    return datetime.now(UTC)


def _month_of(moment):
    return f"{moment.astimezone(UTC):%Y-%m}"


# --- usage and prices ---------------------------------------------------------------


@dataclass(frozen=True)
class Usage:
    input: int = 0
    output: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    web_search: int = 0
    web_fetch: int = 0

    @classmethod
    def from_api(cls, usage):
        """Build from the `usage` object of a Messages API response (dict or SDK model)."""
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        usage = usage or {}
        creation = usage.get("cache_creation") or {}
        written = usage.get("cache_creation_input_tokens") or 0
        five = creation.get("ephemeral_5m_input_tokens")
        hour = creation.get("ephemeral_1h_input_tokens")
        if five is None and hour is None:
            five, hour = written, 0  # no breakdown: the default cache lifetime is 5 minutes
        tools = usage.get("server_tool_use") or {}
        return cls(
            input=usage.get("input_tokens") or 0,
            output=usage.get("output_tokens") or 0,
            cache_write_5m=five or 0,
            cache_write_1h=hour or 0,
            cache_read=usage.get("cache_read_input_tokens") or 0,
            web_search=tools.get("web_search_requests") or 0,
            web_fetch=tools.get("web_fetch_requests") or 0,
        )

    @property
    def prompt_tokens(self):
        return self.input + self.cache_write_5m + self.cache_write_1h + self.cache_read

    def as_dict(self):
        return {
            "input_tokens": self.input,
            "output_tokens": self.output,
            "cache_write_5m_tokens": self.cache_write_5m,
            "cache_write_1h_tokens": self.cache_write_1h,
            "cache_read_tokens": self.cache_read,
            "web_search_requests": self.web_search,
            "web_fetch_requests": self.web_fetch,
        }


@dataclass(frozen=True)
class RateCard:
    """US dollars per million tokens."""

    input: Decimal
    cache_write_5m: Decimal
    cache_write_1h: Decimal
    cache_read: Decimal
    output: Decimal

    @classmethod
    def from_mapping(cls, mapping):
        return cls(**{name: Decimal(str(mapping[name])) for name in _PRICE_FIELDS})

    def token_cost_nano(self, usage):
        per_token = Decimal(1000)  # USD per MTok equals 1000 nano-dollars per token
        total = (
            usage.input * self.input
            + usage.cache_write_5m * self.cache_write_5m
            + usage.cache_write_1h * self.cache_write_1h
            + usage.cache_read * self.cache_read
            + usage.output * self.output
        )
        return total * per_token


@dataclass(frozen=True)
class ModelPrices:
    card: RateCard
    long_card: RateCard = None
    long_threshold: int = None

    def card_for(self, usage):
        if self.long_card is not None and usage.prompt_tokens > self.long_threshold:
            return self.long_card
        return self.card


class PriceTable:
    def __init__(self, models, web_search, web_fetch, source, checked):
        self.models = models
        self.web_search = web_search
        self.web_fetch = web_fetch
        self.source = source
        self.checked = checked
        cards = [m.card for m in models.values()] + [m.long_card for m in models.values() if m.long_card]
        self._fallback = RateCard(**{name: max(getattr(c, name) for c in cards) for name in _PRICE_FIELDS})

    @classmethod
    def from_file(cls, path):
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        models = {}
        for name, entry in data["models"].items():
            long_entry = entry.get("long_prompt")
            models[name] = ModelPrices(
                card=RateCard.from_mapping(entry),
                long_card=RateCard.from_mapping(long_entry) if long_entry else None,
                long_threshold=long_entry["threshold_tokens"] if long_entry else None,
            )
        tools = data.get("server_tools", {})
        return cls(
            models=models,
            web_search=Decimal(str(tools.get("web_search", 0))),
            web_fetch=Decimal(str(tools.get("web_fetch", 0))),
            source=data["meta"]["source"],
            checked=data["meta"]["checked"],
        )

    def _tool_cost_nano(self, usage):
        return (usage.web_search * self.web_search + usage.web_fetch * self.web_fetch) * NANO

    def cost_nano(self, model, usage):
        """Exact cost in nano-dollars; KeyError for a model that is not in the table."""
        card = self.models[model].card_for(usage)
        return _to_int(card.token_cost_nano(usage) + self._tool_cost_nano(usage))

    def fallback_cost_nano(self, usage):
        """Cost at the highest price of every category, for models missing in the table."""
        return _to_int(self._fallback.token_cost_nano(usage) + self._tool_cost_nano(usage))

    def cost_usd(self, model, usage):
        return self.cost_nano(model, usage) / 1e9


def _to_int(value):
    return int(value.quantize(Decimal(1), rounding=ROUND_HALF_UP))


# --- configuration --------------------------------------------------------------------


@dataclass(frozen=True)
class BudgetConfig:
    usd_per_eur: float
    rate_date: str
    max_rate_age_days: int
    limits_eur: dict
    thresholds: dict

    def __post_init__(self):
        limits = self.limits_eur
        if set(limits) != {"total", "research", "self_optimization"}:
            raise ValueError("limits_eur needs total, research and self_optimization")
        if not 0 < limits["self_optimization"] <= limits["research"] <= limits["total"]:
            raise ValueError("limits must satisfy 0 < self_optimization <= research <= total")
        if not 0 < self.thresholds["warn"] < self.thresholds["save"] < self.thresholds["stop"]:
            raise ValueError("thresholds must satisfy 0 < warn < save < stop")
        if self.usd_per_eur <= 0:
            raise ValueError("usd_per_eur must be positive")
        date.fromisoformat(self.rate_date)

    @classmethod
    def from_file(cls, path):
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        currency = data["currency"]
        return cls(
            usd_per_eur=currency["usd_per_eur"],
            rate_date=currency["rate_date"],
            max_rate_age_days=currency["max_rate_age_days"],
            limits_eur=dict(data["limits_eur"]),
            thresholds=dict(data["thresholds"]),
        )

    def limit_nano(self, pot):
        usd = Decimal(str(self.limits_eur[pot])) * Decimal(str(self.usd_per_eur))
        return _to_int(usd * NANO)

    def to_eur(self, nano):
        return nano / 1e9 / self.usd_per_eur


# --- guard ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Cost:
    nano_usd: int
    usd_per_eur: float

    @property
    def usd(self):
        return self.nano_usd / 1e9

    @property
    def eur(self):
        return self.usd / self.usd_per_eur


@dataclass(frozen=True)
class Decision:
    level: str
    allowed: bool
    shares: dict = field(default_factory=dict)


class BudgetGuard:
    def __init__(self, log, prices, config, clock=_utc_now):
        self._log = log
        self._prices = prices
        self._config = config
        self._clock = clock
        self._cursor = log.cursor(since_day=f"{_month_of(clock())}-01")  # only this month is needed
        self._spent = {}  # month -> pot -> nano-dollars
        self._alerted = {}  # (month, pot) -> highest level index alerted

    def _refresh(self):
        for event in self._cursor.read_new():
            month = event.get("ts", "")[:7]
            payload = event.get("payload", {})
            if event.get("type") == "budget.usage":
                pots = CATEGORIES.get(payload.get("category"), ("total",))
                spent = self._spent.setdefault(month, {})
                for pot in pots:
                    spent[pot] = spent.get(pot, 0) + int(payload.get("cost_nano_usd", 0))
            elif event.get("type") == "budget.alert":
                key = (month, payload.get("pot"))
                level = LEVELS.index(payload.get("level", "normal"))
                self._alerted[key] = max(self._alerted.get(key, 0), level)

    def _level(self, share):
        thresholds = self._config.thresholds
        if share >= thresholds["stop"]:
            return "stop"
        if share >= thresholds["save"]:
            return "save"
        if share >= thresholds["warn"]:
            return "warn"
        return "normal"

    def _pots_for(self, category):
        if category not in CATEGORIES:
            raise ValueError(f"unknown budget category {category!r}")
        return CATEGORIES[category]

    def check(self, category, estimate_usd=0.0):
        """Decide before a call. `estimate_usd` is the worst-case cost of the planned call."""
        pots = self._pots_for(category)
        self._refresh()
        month = _month_of(self._clock())
        spent = self._spent.get(month, {})
        estimate = _to_int(Decimal(str(estimate_usd)) * NANO)
        shares = {pot: (spent.get(pot, 0) + estimate) / self._config.limit_nano(pot) for pot in pots}
        level = max((self._level(share) for share in shares.values()), key=LEVELS.index)
        return Decision(level=level, allowed=level != "stop", shares=shares)

    def record(self, category, model, usage, request_id=None):
        """Record the cost of a finished call and raise alerts for new levels."""
        pots = self._pots_for(category)
        usage = usage if isinstance(usage, Usage) else Usage.from_api(usage)
        try:
            nano = self._prices.cost_nano(model, usage)
            fallback = False
        except KeyError:
            nano = self._prices.fallback_cost_nano(usage)
            fallback = True
        payload = {
            "category": category,
            "model": model,
            "cost_nano_usd": nano,
            "cost_usd": round(nano / 1e9, 9),
            "price_fallback": fallback,
            "prices_checked": self._prices.checked,
            **usage.as_dict(),
        }
        if request_id:
            payload["request_id"] = request_id
        self._log.append("budget.usage", payload, intent=f"api.call.{category}")
        self._refresh()
        self._raise_alerts(pots)
        return Cost(nano_usd=nano, usd_per_eur=self._config.usd_per_eur)

    def _raise_alerts(self, pots):
        month = _month_of(self._clock())
        spent = self._spent.get(month, {})
        for pot in pots:
            share = spent.get(pot, 0) / self._config.limit_nano(pot)
            level = self._level(share)
            key = (month, pot)
            if LEVELS.index(level) > self._alerted.get(key, 0):
                self._alert(month, pot, level, spent.get(pot, 0))
        if self._rate_is_stale() and self._alerted.get((month, "rate"), 0) == 0:
            self._log.append(
                "budget.alert",
                {"pot": "rate", "level": "warn", "rate_date": self._config.rate_date},
                intent="budget.rate_stale",
            )
            self._alerted[(month, "rate")] = LEVELS.index("warn")

    def _alert(self, month, pot, level, spent_nano):
        self._log.append(
            "budget.alert",
            {
                "pot": pot,
                "level": level,
                "spent_eur": round(self._config.to_eur(spent_nano), 4),
                "limit_eur": self._config.limits_eur[pot],
            },
            intent=f"budget.{level}",
        )
        self._alerted[(month, pot)] = LEVELS.index(level)

    def _rate_is_stale(self):
        age = (self._clock().date() - date.fromisoformat(self._config.rate_date)).days
        return age > self._config.max_rate_age_days

    def status(self):
        self._refresh()
        month = _month_of(self._clock())
        spent = self._spent.get(month, {})
        pots = {}
        for pot, limit_eur in self._config.limits_eur.items():
            nano = spent.get(pot, 0)
            share = nano / self._config.limit_nano(pot)
            pots[pot] = {
                "spent_eur": self._config.to_eur(nano),
                "limit_eur": limit_eur,
                "share": share,
                "level": self._level(share),
            }
        warnings = ["rate_stale"] if self._rate_is_stale() else []
        return {"month": month, "pots": pots, "warnings": warnings}
