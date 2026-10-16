"""Tests for the mood calculator (Bauplan Charakter, Phase 4)."""

import copy
from datetime import UTC, datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from brain.character.mood import Mood, MoodEngine, MoodError, german_ordinal
from brain.character.profile import load_profile
from brain.tests.helpers import FakeClock

PROFILE = load_profile()


def simple_profile(**factors):
    """The start profile with a hand-made set of factors, for exact numbers."""
    profile = copy.deepcopy(PROFILE)
    profile["laune"]["faktoren"] = factors
    return profile


def factor(art="ereignis", gewicht=0.5, abklingzeit_min=60, grund="Test", **richtung):
    return {
        "gruppe": "gespraech",
        "art": art,
        "gewicht": gewicht,
        "richtung": richtung or {"stimmung": -1},
        "abklingzeit_min": abklingzeit_min,
        "grund": grund,
    }


@pytest.fixture
def engine(clock):
    return MoodEngine(PROFILE, clock=clock)


def test_without_events_the_mood_is_the_baseline(engine):
    mood = engine.current()

    assert (mood.stimmung, mood.energie, mood.gereiztheit) == (0.0, 0.0, 0.0)
    assert mood.reason == "nichts Besonderes"


def test_smalltalk_lowers_the_mood(engine):
    engine.record("smalltalk")

    mood = engine.current()
    assert mood.stimmung < 0
    assert mood.gereiztheit > 0


def test_new_knowledge_raises_the_mood(engine):
    engine.record("neues_wissen")

    assert engine.current().stimmung > 0


def test_a_low_battery_lowers_the_energy(engine):
    engine.record("akku_niedrig", value=12, strength=0.6)

    mood = engine.current()
    assert mood.energie < 0
    assert mood.reason == "Akku bei 12 %"


def test_contributions_fade_linearly(clock):
    engine = MoodEngine(simple_profile(kritik=factor(gewicht=0.5, abklingzeit_min=60)), clock=clock)
    engine.record("kritik")

    assert engine.current().stimmung == pytest.approx(-0.5)
    clock.advance(minutes=30)
    assert engine.current().stimmung == pytest.approx(-0.25)
    clock.advance(minutes=30)
    assert engine.current().stimmung == 0.0


def test_after_the_fading_time_the_mood_returns_to_the_baseline(clock):
    profile = copy.deepcopy(PROFILE)
    profile["laune"]["grundlinie"] = {"stimmung": 0.2, "energie": -0.1, "gereiztheit": 0.0}
    engine = MoodEngine(profile, clock=clock)
    for name in ("smalltalk", "lob", "fehler", "neues_wissen"):
        engine.record(name)
    engine.record("akku_niedrig", value=8, strength=1.0)

    clock.advance(minutes=max(f["abklingzeit_min"] for f in profile["laune"]["faktoren"].values()) + 1)

    mood = engine.current()
    assert (mood.stimmung, mood.energie, mood.gereiztheit) == (0.2, -0.1, 0.0)
    assert mood.reason == "nichts Besonderes"


def test_the_same_events_give_the_same_mood(clock):
    def run():
        engine = MoodEngine(PROFILE, clock=FakeClock())
        engine.record("smalltalk")
        engine.clock.advance(minutes=5)
        engine.record("lob")
        engine.record("akku_niedrig", value=20, strength=0.3)
        engine.clock.advance(minutes=7)
        return engine.current()

    assert run() == run()


def test_a_new_state_replaces_the_old_one(clock):
    engine = MoodEngine(simple_profile(akku=factor(art="zustand", gewicht=1.0, grund="Akku bei {wert} %")), clock=clock)
    engine.record("akku", value=30, strength=0.2)
    engine.record("akku", value=12, strength=0.6)

    mood = engine.current()
    assert mood.stimmung == pytest.approx(-0.6)
    assert mood.reason == "Akku bei 12 %"


def test_events_add_up_but_stay_within_the_scale(clock):
    engine = MoodEngine(simple_profile(kritik=factor(gewicht=0.4)), clock=clock)
    for _ in range(10):
        engine.record("kritik")

    assert engine.current().stimmung == -1.0


def test_the_reason_names_the_strongest_factors_in_order(engine):
    engine.record("akku_niedrig", value=12, strength=0.6)
    for _ in range(3):
        engine.record("smalltalk")

    assert engine.current().reason == "schon die dritte Smalltalk-Frage heute und Akku bei 12 %"


def test_the_reason_names_at_most_three_factors(engine):
    for name in ("smalltalk", "lob", "fehler", "neues_wissen", "kritik"):
        engine.record(name)

    assert len(engine.current().factors) == 3
    assert engine.current().reason.count(",") == 1
    assert " und " in engine.current().reason


def test_counting_per_day_follows_the_local_midnight():
    clock = FakeClock(datetime(2026, 10, 15, 21, 30, tzinfo=UTC))  # 23:30 in Berlin
    engine = MoodEngine(PROFILE, clock=clock)
    engine.record("smalltalk")
    clock.advance(minutes=60)  # 00:30 in Berlin, a new day
    engine.record("smalltalk")

    assert "die erste Smalltalk-Frage" in engine.current().reason


@pytest.mark.parametrize(("number", "word"), [(1, "erste"), (3, "dritte"), (7, "siebte"), (12, "zwölfte"), (13, "13.")])
def test_german_ordinals(number, word):
    assert german_ordinal(number) == word


def test_unknown_factors_are_refused(engine):
    with pytest.raises(MoodError, match="unbekannt"):
        engine.record("hass")


@pytest.mark.parametrize("strength", [-0.1, 1.1, float("nan")])
def test_strength_must_be_between_zero_and_one(engine, strength):
    with pytest.raises(MoodError, match="Stärke"):
        engine.record("lob", strength=strength)


@pytest.mark.parametrize(
    "text",
    ["Ich hab seit gestern Schmerzen in der Brust", "Mir macht das echt Sorgen", "Es gab einen Unfall", "NOTFALL!"],
)
def test_a_serious_topic_damps_the_mood_for_the_answer(engine, text):
    for _ in range(3):
        engine.record("smalltalk")

    mood = engine.for_answer(text)

    assert (mood.stimmung, mood.energie, mood.gereiztheit) == (0.0, 0.0, 0.0)
    assert mood.damped is True
    assert engine.current().stimmung < 0  # only the answer is damped, the mood itself stays


def test_the_caller_can_flag_a_serious_situation(engine):
    engine.record("kritik")

    assert engine.for_answer("Kannst du mir helfen?", serious=True).damped is True


def test_everyday_questions_keep_the_mood(engine):
    engine.record("smalltalk")

    assert engine.for_answer("Wie wird das Wetter morgen?") == engine.current()


def test_every_change_is_logged_with_its_reason(clock, log):
    engine = MoodEngine(PROFILE, log=log, clock=clock)
    engine.record("akku_niedrig", value=12, strength=0.6)

    event = log.events()[-1]
    assert event["type"] == "character.mood"
    assert event["payload"]["faktor"] == "akku_niedrig"
    assert event["payload"]["wert"] == 12
    assert event["payload"]["staerke"] == 0.6
    assert event["payload"]["grund"] == "Akku bei 12 %"
    assert set(event["payload"]["laune"]) == {"stimmung", "energie", "gereiztheit"}


def test_the_mood_can_be_restored_from_the_log(clock, log):
    original = MoodEngine(PROFILE, log=log, clock=clock)
    original.record("smalltalk")
    clock.advance(minutes=10)
    original.record("akku_niedrig", value=15, strength=0.5)
    clock.advance(minutes=3)

    restored = MoodEngine.from_log(PROFILE, log, clock=clock)

    assert restored.current() == original.current()


def test_values_must_be_plain_numbers_or_short_text(engine):
    with pytest.raises(MoodError, match="Wert"):
        engine.record("akku_niedrig", value={"geheim": 1})


@settings(max_examples=60, deadline=None)
@given(
    st.lists(
        st.tuples(
            st.sampled_from(sorted(PROFILE["laune"]["faktoren"])),
            st.floats(min_value=0, max_value=1),
            st.integers(min_value=0, max_value=180),
        ),
        max_size=25,
    )
)
def test_the_mood_always_stays_on_the_scale_and_fades_completely(steps):
    clock = FakeClock()
    engine = MoodEngine(PROFILE, clock=clock)
    for name, strength, minutes in steps:
        engine.record(name, value=1, strength=strength)
        clock.advance(minutes=minutes)
        mood = engine.current()
        assert all(-1.0 <= axis <= 1.0 for axis in (mood.stimmung, mood.energie, mood.gereiztheit))
    clock.advance(minutes=max(f["abklingzeit_min"] for f in PROFILE["laune"]["faktoren"].values()) + 1)
    assert engine.current() == Mood(0.0, 0.0, 0.0, "nichts Besonderes", ())


def test_nearly_faded_factors_are_not_named(engine, clock):
    engine.record("lob")
    clock.advance(minutes=PROFILE["laune"]["faktoren"]["lob"]["abklingzeit_min"] - 1)

    mood = engine.current()
    assert mood.stimmung > 0
    assert mood.reason == "nichts Besonderes"
