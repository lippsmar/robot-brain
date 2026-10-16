"""Tests for the "Sofort" tier: everything Schlaubi needs right now (Bauplan Lakehouse 1.4)."""

import time

import pytest

from brain.datalake import DataLake
from brain.memory import Memory
from brain.sofort import Sofort, SofortError, heutige_werte, standard_quellen
from brain.wissen import Wissen


@pytest.fixture
def lake(tmp_path, clock):
    store = DataLake(tmp_path / "lake.db", clock=clock)
    yield store
    store.close()


@pytest.fixture
def memory(tmp_path, clock):
    store = Memory(tmp_path / "memory.db", clock=clock)
    yield store
    store.close()


@pytest.fixture
def wissen(tmp_path, memory, clock):
    store = Wissen(tmp_path / "wissen.db", memory, clock=clock)
    yield store
    store.close()


def test_bundle_is_empty_until_built_and_then_holds_every_part(clock):
    sofort = Sofort({"a": lambda now: (1, False), "b": lambda now: ("x", True)}, clock=clock)
    assert sofort.buendel() == {}

    sofort.aufbauen()

    teile = sofort.buendel()
    assert {name: (teil.wert, teil.pii) for name, teil in teile.items()} == {"a": (1, False), "b": ("x", True)}
    assert teile["a"].stand == "2026-10-15T12:00:00.000Z"


def test_only_the_named_part_is_refreshed(clock):
    calls = {"a": 0, "b": 0}

    def quelle(name):
        def lesen(now):
            calls[name] += 1
            return calls[name], False

        return lesen

    sofort = Sofort({"a": quelle("a"), "b": quelle("b")}, clock=clock)
    sofort.aufbauen()

    sofort.nachfuehren("b")

    assert (sofort.teil("a").wert, sofort.teil("b").wert) == (1, 2)
    with pytest.raises(SofortError):
        sofort.nachfuehren("gibt-es-nicht")


def test_failing_source_does_not_stop_the_others(clock):
    def kaputt(now):
        raise RuntimeError("Sensor weg")

    sofort = Sofort({"gut": lambda now: (1, False), "kaputt": kaputt}, clock=clock)
    sofort.aufbauen()

    assert sofort.teil("gut").wert == 1
    teil = sofort.teil("kaputt")
    assert (teil.wert, teil.fehler) == (None, "RuntimeError: Sensor weg")


def test_bundle_is_a_copy(clock):
    sofort = Sofort({"a": lambda now: (1, False)}, clock=clock)
    sofort.aufbauen()

    sofort.buendel().clear()

    assert "a" in sofort.buendel()


def test_todays_values_per_channel(lake, clock):
    lake.name_place("buero-wlan", "Büro")
    lake.ingest("wuerfel", 1, clock(), {"licht": 100.0, "zuluft_temp": 21.0}, wlan="buero-wlan")
    clock.advance(minutes=1)
    lake.ingest("wuerfel", 2, clock(), {"licht": 300.0, "zuluft_temp": 22.0}, wlan="buero-wlan")

    werte, pii = heutige_werte(lake, clock())

    licht = werte["licht"]
    assert (licht.letzter, licht.minimum, licht.maximum, licht.anzahl, licht.einheit) == (300.0, 100.0, 300.0, 2, "lx")
    assert "akku" not in werte
    assert pii is True


def test_yesterdays_values_do_not_count(lake, clock):
    lake.ingest("wuerfel", 1, clock(), {"licht": 100.0})
    clock.advance(days=1)

    werte, pii = heutige_werte(lake, clock())

    assert werte == {}
    assert pii is False


def test_standard_sources_fill_the_bundle(lake, wissen, memory, clock):
    lake.ingest("wuerfel", 1, clock(), {"akku": 80.0, "licht": 120.0})
    pid = wissen.anlegen("Kühlung")
    wissen.nutzen(pid)
    uid = memory.remember("Marvin mag keinen Smalltalk.", kind="fact", source="gespraech", pii=True)
    memory.keep(uid)

    sofort = Sofort(standard_quellen(lake=lake, wissen=wissen, memory=memory), clock=clock)
    sofort.aufbauen()
    teile = sofort.buendel()

    assert teile["zustand"].wert.akku == 80.0
    assert teile["heute"].wert["licht"].letzter == 120.0
    assert [p.name for p in teile["aktive_pakete"].wert] == ["Kühlung"]
    assert [hit.uid for hit in teile["merkliste"].wert] == [uid]
    assert teile["merkliste"].pii is True
    assert teile["kuehlung"].fehler is None
    assert "budget" not in teile  # only with a budget guard
    assert all(teil.fehler is None for teil in teile.values())


def test_reading_the_bundle_takes_well_under_10_ms(lake, wissen, memory, clock):
    for seq in range(1, 61):
        lake.ingest("wuerfel", seq, clock(), {"licht": float(seq), "zuluft_temp": 20.0, "akku": 90.0})
        clock.advance(minutes=1)
    for name in ["A", "B", "C", "D", "E"]:
        wissen.nutzen(wissen.anlegen(name))
    sofort = Sofort(standard_quellen(lake=lake, wissen=wissen, memory=memory), clock=clock)
    sofort.aufbauen()

    start = time.perf_counter()
    for _ in range(1000):
        sofort.buendel()
    per_call = (time.perf_counter() - start) / 1000

    assert per_call < 0.010
