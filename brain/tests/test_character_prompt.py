"""Tests for the system prompt builder (Bauplan Charakter, Phase 3)."""

import copy
import re
from datetime import UTC, datetime

import pytest

from brain.character.core import CORE_FILE
from brain.character.mood import Mood
from brain.character.profile import load_profile
from brain.character.prompt import MAX_PROMPT_CHARS, PromptError, build_system_prompt

CORE = CORE_FILE.read_text(encoding="utf-8")
PROFILE = load_profile()
NOW = datetime(2026, 10, 16, 3, 12, tzinfo=UTC)  # Friday, 05:12 in Berlin
CALM = Mood(0.0, 0.0, 0.0, "nichts Besonderes")
GRUMPY = Mood(-0.7, -0.4, 0.65, "schon die dritte Smalltalk-Frage heute und Akku bei 12 %", (("smalltalk", 0.75),))


def build(mood=CALM, **kwargs):
    return build_system_prompt(CORE, PROFILE, mood, now=NOW, **kwargs)


def test_the_core_comes_first_and_complete():
    prompt = build()

    assert prompt.text.startswith(CORE.strip())
    assert prompt.text.count(CORE.strip()) == 1


def test_the_same_inputs_give_the_same_prompt():
    assert build(GRUMPY) == build(GRUMPY)


def test_the_stable_part_does_not_change_with_mood_time_or_channel():
    first = build(CALM, channel="gesprochen")
    second = build_system_prompt(
        CORE, PROFILE, GRUMPY, now=datetime(2026, 12, 24, 18, 0, tzinfo=UTC), channel="telegram"
    )

    assert first.stable == second.stable
    assert first.dynamic != second.dynamic


def test_the_prompt_stays_under_the_limit():
    assert len(build(GRUMPY, more=True).text) < MAX_PROMPT_CHARS


def test_a_bloated_profile_is_refused():
    bloated = copy.deepcopy(PROFILE)
    bloated["verhalten"] = ["Du erklärst sehr gründlich und ausführlich, warum alles so ist, wie es ist. " * 3] * 20

    with pytest.raises(PromptError, match="lang"):
        build_system_prompt(CORE, bloated, CALM, now=NOW)


def test_the_character_from_the_profile_is_in_the_prompt():
    text = build().stable

    for expected in ("Mentor", "Hessisch", "duzt", "Direktheit: 8", "Smalltalk-Toleranz: 1", "Fragen mit Tiefe"):
        assert expected in text
    for rule in PROFILE["verhalten"]:
        assert rule in text


def test_the_attitude_is_described_as_values_and_never_named():
    text = build().stable

    for value in PROFILE["haltung"]["werte"]:
        assert value in text
    assert "benennst diese Haltung nie" in text
    assert "lügst nicht" in text
    # "Links" for web links is fine, a political label is not
    assert not re.search(r"\b(politisch links|linke[nrs]?|linksgerichtet|links eingestellt)\b", text, re.IGNORECASE)


def test_the_mood_and_its_reason_are_in_the_dynamic_part():
    text = build(GRUMPY).dynamic

    assert "Stimmung sehr schlecht" in text
    assert "Energie müde" in text
    assert "Gereiztheit sehr gereizt" in text
    assert "schon die dritte Smalltalk-Frage heute und Akku bei 12 %" in text
    assert "nie Inhalt und Fakten" in text


def test_a_damped_mood_asks_for_a_calm_answer():
    damped = Mood(0.0, 0.0, 0.0, "ernstes Thema", damped=True)

    text = build(damped).dynamic

    assert "Ernstes" in text
    assert "ohne Witz" in text


def test_time_is_given_in_local_german_form():
    assert "Freitag, 16.10.2026, 05:12 Uhr" in build().dynamic


@pytest.mark.parametrize(("channel", "label"), [("gesprochen", "Kanal: gesprochen"), ("telegram", "Kanal: Telegram")])
def test_the_channel_is_named(channel, label):
    assert label in build(channel=channel).dynamic


def test_an_unknown_channel_is_refused():
    with pytest.raises(PromptError, match="Kanal"):
        build(channel="email")


def test_the_answer_length_follows_the_profile_unless_marvin_wants_more():
    assert "1 bis 2 Sätze" in build().dynamic
    longer = build(more=True).dynamic
    assert "ausführlich" in longer
    assert "1 bis 2 Sätze" not in longer


def test_no_template_placeholders_are_left():
    text = build(GRUMPY, more=True).text

    assert "{" not in text
    assert "}" not in text
