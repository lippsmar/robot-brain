"""Fixtures shared by all test files."""

import pytest

from brain.eventlog import EventLog
from brain.tests.helpers import FakeClock


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def log(tmp_path, clock):
    return EventLog(tmp_path / "events", source="test", clock=clock)
