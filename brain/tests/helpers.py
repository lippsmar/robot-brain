"""Shared test helpers."""

from datetime import UTC, datetime, timedelta


class FakeClock:
    """Deterministic UTC clock that can be moved forward."""

    def __init__(self, start=datetime(2026, 10, 15, 12, 0, tzinfo=UTC)):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)
