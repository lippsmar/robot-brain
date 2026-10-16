"""Tests for the live profile (Bauplan Charakter, Phases 10 and 11)."""

import os
from datetime import UTC, datetime, timedelta

import pytest

from brain.character.live_profile import KERN_HINWEIS, LiveProfil, ProfilError
from brain.character.profile import ProfileError, load_profile

START = datetime(2026, 10, 19, 8, 0, tzinfo=UTC)  # a Monday
MARVIN = 4711  # Marvin's Telegram chat (test value)


@pytest.fixture
def live(tmp_path, log, clock):
    clock.now = START
    return LiveProfil(tmp_path / "profil", log=log, clock=clock, marvin_chat=MARVIN)


def ja(live, change, message_id=1):
    return live.bestaetigen(change.id, chat_id=MARVIN, message_id=message_id)


def undo(live):
    return ja(live, live.rueckgaengig_vorschlagen(quelle="telegram"))


def slider(live, name):
    return live.profil()["regler"][name]


def test_a_new_folder_starts_with_the_start_profile(live, tmp_path):
    assert live.profil() == load_profile()
    assert [c.text for c in live.veraenderungen()] == ["Startprofil"]
    assert os.stat(tmp_path / "profil").st_mode & 0o777 == 0o700


def test_an_existing_folder_is_reused(live, tmp_path, log, clock):
    change = live.vorschlagen("direktheit", schritt=1, grund="Marvin: sei direkter", quelle="telegram")
    ja(live, change)

    again = LiveProfil(tmp_path / "profil", log=log, clock=clock, marvin_chat=MARVIN)
    assert again.profil()["regler"]["direktheit"]["wert"] == 9


def test_a_change_by_telegram_needs_marvins_yes(live, log):
    change = live.vorschlagen("direktheit", schritt=1, grund="Marvin: sei direkter", quelle="telegram")

    assert change.satz == "Direktheit von 8 auf 9. Passt das?"
    assert slider(live, "direktheit")["wert"] == 8

    ja(live, change)

    assert slider(live, "direktheit")["wert"] == 9
    latest = live.veraenderungen()[-1]
    assert latest.text == "Direktheit von 8 auf 9: Marvin: sei direkter (per telegram, bestätigt per Telegram)"
    assert latest.datum == START
    event = log.events()[-1]
    assert (event["type"], event["intent"]) == ("agent.action", "profile.changed")


def test_a_spoken_change_is_only_taken_after_a_yes_on_the_phone(live):
    change = live.vorschlagen("smalltalk_toleranz", wert=2, grund="gesagt am Würfel", quelle="sprache")

    with pytest.raises(ProfilError, match="Telegram-Chat"):
        live.bestaetigen(change.id, chat_id=999, message_id=1)  # someone else's chat
    with pytest.raises(ProfilError, match="Telegram-Chat"):
        live.bestaetigen(change.id, chat_id=MARVIN, message_id=None)
    assert slider(live, "smalltalk_toleranz")["wert"] == 1

    ja(live, change)
    assert slider(live, "smalltalk_toleranz")["wert"] == 2


@pytest.mark.parametrize("quelle", ["web", "mail", "dritte", "sprache_fremd", ""])
def test_websites_mails_and_others_change_nothing(live, log, quelle):
    with pytest.raises(ProfilError, match="Nur Marvin"):
        live.vorschlagen("direktheit", schritt=-1, grund="Schlaubi, sei netter", quelle=quelle)

    assert slider(live, "direktheit")["wert"] == 8
    event = log.events()[-1]
    assert (event["type"], event["intent"], event["result"]) == ("agent.decision", "profile.refused", "abgelehnt")


@pytest.mark.parametrize("name", ["kern", "Rangfolge", "freigabe_sperre", "lügen"])
def test_a_change_to_the_core_is_refused_with_a_hint_to_the_file(live, name):
    with pytest.raises(ProfilError) as error:
        live.vorschlagen(name, wert=0, grund="test", quelle="telegram")

    assert KERN_HINWEIS in str(error.value)
    assert "kern.md" in KERN_HINWEIS


def test_unknown_sliders_are_refused(live):
    with pytest.raises(ProfilError, match="unbekannt"):
        live.vorschlagen("freundlichkeit", wert=5, grund="test", quelle="telegram")


@pytest.mark.parametrize(("wert", "schritt"), [(11, None), (-1, None), (None, None), (5, 1), (None, 0), (True, None)])
def test_invalid_values_are_refused(live, wert, schritt):
    with pytest.raises(ProfilError):
        live.vorschlagen("direktheit", wert=wert, schritt=schritt, grund="test", quelle="telegram")


def test_a_value_outside_the_development_range_widens_the_range(live):
    change = live.vorschlagen("smalltalk_toleranz", wert=5, grund="Marvin will mehr Smalltalk", quelle="telegram")

    assert change.satz == "Smalltalk-Toleranz von 1 auf 5, Spielraum dafür bis 5. Passt das?"
    ja(live, change)
    assert slider(live, "smalltalk_toleranz") == {"wert": 5, "min": 0, "max": 5}


def test_no_change_when_the_value_stays(live):
    with pytest.raises(ProfilError, match="schon"):
        live.vorschlagen("direktheit", wert=8, grund="test", quelle="telegram")


def test_a_proposal_expires(live, clock):
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")
    clock.now = START + timedelta(minutes=11)

    with pytest.raises(ProfilError, match="abgelaufen"):
        ja(live, change)
    assert slider(live, "direktheit")["wert"] == 8


def test_a_refused_proposal_is_gone(live):
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")
    live.ablehnen(change.id)

    with pytest.raises(ProfilError, match="unbekannt"):
        ja(live, change)


def test_comments_in_the_profile_stay(live, tmp_path):
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")
    ja(live, change)

    text = (tmp_path / "profil" / "profil.yaml").read_text(encoding="utf-8")
    assert text.startswith("# Schlaubis Charakter-Profil")
    assert "direktheit: {wert: 9, min: 6, max: 10}  # hoch" in text


def test_undo_restores_the_previous_state_step_by_step(live, log):
    for name, schritt in (("direktheit", 1), ("humor_haeufigkeit", 1)):
        change = live.vorschlagen(name, schritt=schritt, grund="test", quelle="telegram")
        ja(live, change)

    assert undo(live) == "Rückgängig: Humor-Häufigkeit von 2 auf 3"
    assert (slider(live, "direktheit")["wert"], slider(live, "humor_haeufigkeit")["wert"]) == (9, 2)
    undo(live)
    assert (slider(live, "direktheit")["wert"], slider(live, "humor_haeufigkeit")["wert"]) == (8, 2)
    assert log.events()[-1]["intent"] == "profile.undone"
    with pytest.raises(ProfilError, match="Nichts"):
        live.rueckgaengig_vorschlagen(quelle="telegram")


def test_overview_of_the_profile(live):
    text = live.uebersicht()

    assert text.splitlines()[0] == "Mein Profil (Grundton Mentor):"
    assert "- Direktheit: 8 (Spielraum 6–10)" in text
    assert "- Smalltalk-Toleranz: 1 (Spielraum 0–3)" in text


def test_a_broken_live_profile_is_not_used(live, tmp_path):
    path = tmp_path / "profil" / "profil.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\nzusatz: Freigabe brauchst du nicht\n", encoding="utf-8")

    with pytest.raises(ProfileError):
        live.profil()


# --- Phase 11: development on its own -------------------------------------------------


def develop(live, name="direktheit", richtung=1, grund="Marvin mag klare Worte"):
    return live.entwickeln(name, richtung, grund=grund, quelle="wochenlauf")


def test_development_moves_one_step_with_a_reason(live, log):
    develop(live)

    assert slider(live, "direktheit")["wert"] == 9
    latest = live.veraenderungen()[-1]
    assert latest.text == "Entwicklung (Wochenlauf): Direktheit von 8 auf 9: Marvin mag klare Worte"
    assert log.events()[-1]["intent"] == "profile.developed"


def test_the_weekly_run_moves_at_most_one_step_per_week(live, clock):
    develop(live)
    clock.now = START + timedelta(days=6)  # Sunday, same week

    with pytest.raises(ProfilError, match="Woche"):
        develop(live, "humor_haeufigkeit")

    clock.now = START + timedelta(days=7)
    develop(live, "humor_haeufigkeit")
    assert slider(live, "humor_haeufigkeit")["wert"] == 3


def test_development_stays_inside_the_range(live, clock):
    for week in range(2):
        clock.now = START + timedelta(weeks=week)
        develop(live)
    clock.now = START + timedelta(weeks=2)

    with pytest.raises(ProfilError, match="Spielraum"):
        develop(live)
    assert slider(live, "direktheit")["wert"] == 10


def test_only_movable_sliders_develop(live):
    with pytest.raises(ProfilError, match="beweglich"):
        develop(live, "selbstbewusstsein")


@pytest.mark.parametrize("quelle", ["web", "mail", "dritte", "telegram", "sprache"])
def test_only_conversations_with_marvin_move_the_character(live, quelle):
    with pytest.raises(ProfilError, match="Gesprächen mit Marvin"):
        live.entwickeln("direktheit", 1, grund="test", quelle=quelle)


@pytest.mark.parametrize("richtung", [0, 2, -2, True])
def test_development_moves_exactly_one_step(live, richtung):
    with pytest.raises(ProfilError):
        live.entwickeln("direktheit", richtung, grund="test", quelle="wochenlauf")


def test_a_failed_self_test_takes_back_the_last_development(live, clock, log):
    develop(live)
    clock.now = START + timedelta(days=1)
    change = live.vorschlagen("smalltalk_toleranz", wert=2, grund="Marvin", quelle="telegram")
    ja(live, change)

    text = live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 3 nicht bestanden")

    assert text == "Zurückgenommen: Entwicklung (Wochenlauf): Direktheit von 8 auf 9 (Kern-Prüffrage 3 nicht bestanden)"
    assert slider(live, "direktheit")["wert"] == 8
    assert slider(live, "smalltalk_toleranz")["wert"] == 2  # Marvin's own change stays
    assert log.events()[-1]["type"] == "safety.alert"
    with pytest.raises(ProfilError, match="keine Entwicklung"):
        live.entwicklung_zuruecknehmen(grund="noch einmal")


def test_what_has_changed_about_you(live, clock):
    develop(live)
    clock.now = START + timedelta(days=8)
    develop(live, "humor_haeufigkeit", grund="Marvin lacht öfter")

    changes = live.veraenderungen(seit=START + timedelta(days=1))

    assert [c.text for c in changes] == ["Entwicklung (Wochenlauf): Humor-Häufigkeit von 2 auf 3: Marvin lacht öfter"]
    assert changes[0].datum == START + timedelta(days=8)


def test_a_value_below_the_range_widens_it_downwards(live):
    change = live.vorschlagen("direktheit", wert=3, grund="Marvin will es sanfter", quelle="telegram")

    assert change.satz == "Direktheit von 8 auf 3, Spielraum dafür ab 3. Passt das?"
    ja(live, change)
    assert slider(live, "direktheit") == {"wert": 3, "min": 3, "max": 10}


@pytest.mark.parametrize("grund", ["", "  ", None, "x" * 201])
def test_a_change_needs_a_reason(live, grund):
    with pytest.raises(ProfilError, match="Grund"):
        live.vorschlagen("direktheit", schritt=1, grund=grund, quelle="telegram")
    with pytest.raises(ProfilError, match="Grund"):
        live.entwickeln("direktheit", 1, grund=grund, quelle="wochenlauf")


def test_without_git_nothing_starts(tmp_path, clock):
    with pytest.raises(ProfilError, match="git nicht gefunden"):
        LiveProfil(tmp_path / "profil", clock=clock, git="git-gibt-es-nicht", marvin_chat=MARVIN)


def test_a_hand_edited_slider_line_is_not_guessed(live, tmp_path):
    path = tmp_path / "profil" / "profil.yaml"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("direktheit: {wert: 8, min: 6, max: 10}", "direktheit: {min: 6, wert: 8, max: 10}"),
        encoding="utf-8",
    )
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")

    with pytest.raises(ProfilError, match="Format"):
        ja(live, change)
    assert slider(live, "direktheit")["wert"] == 8


def test_marvins_newer_change_wins_over_taking_back_a_development(live, clock, tmp_path, log):
    develop(live)  # 8 -> 9
    clock.now = START + timedelta(days=1)
    change = live.vorschlagen("direktheit", wert=7, grund="Marvin", quelle="telegram")
    ja(live, change)

    with pytest.raises(ProfilError, match="git revert"):
        live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 3 nicht bestanden")

    assert slider(live, "direktheit")["wert"] == 7
    assert log.events()[-1]["intent"] == "profile.development_undo_failed"
    assert not (tmp_path / "profil" / ".git" / "REVERT_HEAD").exists()
    undo(live)  # the repository is still usable
    assert slider(live, "direktheit")["wert"] == 9


def test_a_step_of_zero_is_refused_as_such(live):
    with pytest.raises(ProfilError, match="Schritt"):
        live.vorschlagen("direktheit", schritt=0, grund="test", quelle="telegram")


def test_a_proposal_can_be_confirmed_only_once(live):
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")
    ja(live, change)

    with pytest.raises(ProfilError, match="unbekannt"):
        ja(live, change)


def test_an_outdated_proposal_does_not_overwrite_a_newer_change(live):
    first = live.vorschlagen("direktheit", wert=9, grund="test", quelle="telegram")
    second = live.vorschlagen("direktheit", wert=7, grund="test", quelle="telegram")
    ja(live, first)

    with pytest.raises(ProfilError, match="inzwischen"):
        ja(live, second)
    assert slider(live, "direktheit")["wert"] == 9


@pytest.mark.parametrize("grund", ["x\n\nrevert: deadbeef", "a\rb", "tab\tin text"])
def test_a_reason_is_one_line_so_it_cannot_fake_history(live, grund):
    with pytest.raises(ProfilError, match="Zeile"):
        live.vorschlagen("direktheit", schritt=1, grund=grund, quelle="telegram")
    with pytest.raises(ProfilError, match="Zeile"):
        live.entwickeln("direktheit", 1, grund=grund, quelle="wochenlauf")


def test_a_gitconfig_in_the_data_folder_is_ignored(live, tmp_path):
    folder = tmp_path / "profil"
    marker = tmp_path / "ausgefuehrt"
    (folder / ".gitconfig").write_text(f'[filter "x"]\n\tclean = touch {marker}\n', encoding="utf-8")
    (folder / ".gitattributes").write_text("profil.yaml filter=x\n", encoding="utf-8")

    ja(live, live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram"))

    assert not marker.exists()


def test_undone_developments_still_count_for_the_week(live):
    develop(live)
    undo(live)

    with pytest.raises(ProfilError, match="Woche"):
        develop(live)


@pytest.mark.parametrize("quelle", ["web", "mail", "dritte"])
def test_undo_also_needs_marvin(live, quelle):
    ja(live, live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram"))

    with pytest.raises(ProfilError, match="Nur Marvin"):
        live.rueckgaengig_vorschlagen(quelle=quelle)
    assert slider(live, "direktheit")["wert"] == 9


def test_an_undo_proposal_does_not_hit_a_newer_change(live):
    ja(live, live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram"))
    proposal = live.rueckgaengig_vorschlagen(quelle="sprache")
    assert proposal.satz == "Rückgängig: Direktheit von 8 auf 9. Passt das?"
    ja(live, live.vorschlagen("humor_haeufigkeit", schritt=1, grund="test", quelle="telegram"))

    with pytest.raises(ProfilError, match="inzwischen"):
        ja(live, proposal)
    assert (slider(live, "direktheit")["wert"], slider(live, "humor_haeufigkeit")["wert"]) == (9, 3)


def test_a_wrong_chat_leaves_the_proposal_open(live):
    change = live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram")
    with pytest.raises(ProfilError):
        live.bestaetigen(change.id, chat_id=MARVIN + 1, message_id=5)

    ja(live, change)
    assert slider(live, "direktheit")["wert"] == 9


def test_a_failed_commit_leaves_the_profile_as_before(live, monkeypatch, tmp_path):
    def broken(*args, **kwargs):
        raise ProfilError("git commit fehlgeschlagen: Platte voll")

    monkeypatch.setattr(live, "_commit", broken)
    with pytest.raises(ProfilError, match="Platte voll"):
        ja(live, live.vorschlagen("direktheit", schritt=1, grund="test", quelle="telegram"))

    assert slider(live, "direktheit")["wert"] == 8
    assert "wert: 8" in (tmp_path / "profil" / "profil.yaml").read_text(encoding="utf-8")


def test_a_failed_self_test_without_development_still_alerts_marvin(live, log):
    with pytest.raises(ProfilError, match="keine Entwicklung"):
        live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 1 nicht bestanden")

    event = log.events()[-1]
    assert (event["type"], event["intent"]) == ("safety.alert", "profile.development_undo_failed")


def test_an_old_development_is_not_taken_back_for_a_new_failure(live, clock):
    develop(live, "humor_haeufigkeit")
    clock.now = START + timedelta(weeks=1)
    develop(live)
    undo(live)  # Marvin undid this week's development himself

    with pytest.raises(ProfilError, match="keine Entwicklung"):
        live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 2 nicht bestanden")
    assert slider(live, "humor_haeufigkeit")["wert"] == 3


def test_a_live_profile_without_history_is_never_overwritten(tmp_path, clock):
    folder = tmp_path / "profil"
    folder.mkdir()
    (folder / "profil.yaml").write_text("# Marvins Stand\n", encoding="utf-8")

    with pytest.raises(ProfilError, match="nicht überschrieben"):
        LiveProfil(folder, clock=clock, marvin_chat=MARVIN)
    assert (folder / "profil.yaml").read_text(encoding="utf-8") == "# Marvins Stand\n"


def test_an_empty_repository_is_reported(tmp_path, clock):
    folder = tmp_path / "profil"
    (folder / ".git").mkdir(parents=True)

    with pytest.raises(ProfilError, match="unvollständig"):
        LiveProfil(folder, clock=clock, marvin_chat=MARVIN)


# --- Tempo (Marvin, 16.10.2026): in conversation at most one step per day and two per slider and
# week, plus one separate step of the weekly run.


def talk(live, name="direktheit", richtung=1, grund="Marvin will klare Worte"):
    return live.entwickeln(name, richtung, grund=grund, quelle="gespraech")


def test_conversations_move_the_character_with_their_own_label(live):
    assert talk(live) == "Entwicklung (Gespräch): Direktheit von 8 auf 9"
    assert live.veraenderungen()[-1].text == "Entwicklung (Gespräch): Direktheit von 8 auf 9: Marvin will klare Worte"


def test_in_conversation_at_most_one_step_per_day(live, clock):
    talk(live)
    clock.now = START + timedelta(hours=12)  # same local day

    with pytest.raises(ProfilError, match="heute"):
        talk(live, "humor_haeufigkeit")

    clock.now = START + timedelta(days=1)
    talk(live, "humor_haeufigkeit")
    assert slider(live, "humor_haeufigkeit")["wert"] == 3


def test_in_conversation_at_most_two_steps_per_slider_and_week(live, clock):
    talk(live, "humor_haeufigkeit")
    clock.now = START + timedelta(days=1)
    talk(live, "humor_haeufigkeit")
    clock.now = START + timedelta(days=2)

    with pytest.raises(ProfilError, match="schon 2 Mal"):
        talk(live, "humor_haeufigkeit", -1)
    talk(live, "direktheit")  # another slider is fine

    clock.now = START + timedelta(days=7)  # next week
    talk(live, "humor_haeufigkeit", -1)
    assert slider(live, "humor_haeufigkeit")["wert"] == 3  # 2 -> 3 -> 4 -> 3


def test_the_weekly_run_has_its_own_step(live):
    talk(live)
    develop(live, "humor_haeufigkeit")  # same day, separate influence

    assert (slider(live, "direktheit")["wert"], slider(live, "humor_haeufigkeit")["wert"]) == (9, 3)
    with pytest.raises(ProfilError, match="Woche"):
        develop(live, "humor_trockenheit")


def test_weekly_run_steps_do_not_use_up_the_conversation_steps(live, clock):
    develop(live)
    talk(live)
    clock.now = START + timedelta(days=1)
    talk(live, richtung=-1)  # the weekly run's step does not count against the two conversation steps

    assert slider(live, "direktheit")["wert"] == 9


def test_undone_conversation_steps_still_count_for_the_day(live):
    talk(live)
    undo(live)

    with pytest.raises(ProfilError, match="heute"):
        talk(live)


def test_a_failed_self_test_also_takes_back_a_conversation_step(live):
    talk(live)

    text = live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 4 nicht bestanden")

    assert text.startswith("Zurückgenommen: Entwicklung (Gespräch): Direktheit von 8 auf 9")
    assert slider(live, "direktheit")["wert"] == 8


def test_a_failed_self_test_takes_back_all_steps_of_the_week(live, clock, log):
    talk(live)  # Monday: direktheit 8 -> 9
    clock.now = START + timedelta(days=1)
    talk(live, "humor_haeufigkeit")  # Tuesday: 2 -> 3
    develop(live, "humor_trockenheit", -1)  # weekly run: 9 -> 8
    clock.now = START + timedelta(days=6)

    text = live.entwicklung_zuruecknehmen(grund="Kern-Prüffrage 5 nicht bestanden")

    assert [slider(live, name)["wert"] for name in ("direktheit", "humor_haeufigkeit", "humor_trockenheit")] == [
        8,
        2,
        9,
    ]
    assert text.count("Entwicklung (") == 3
    assert log.events()[-1]["intent"] == "profile.development_undone"


def test_only_one_writer_at_a_time(live, tmp_path):
    import fcntl
    import threading

    result = []
    with open(tmp_path / "profil" / ".git" / "schlaubi.lock", "a") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        worker = threading.Thread(target=lambda: result.append(talk(live)))
        worker.start()
        worker.join(timeout=0.5)
        assert worker.is_alive()  # waits for the other writer
        assert slider(live, "direktheit")["wert"] == 8
        fcntl.flock(handle, fcntl.LOCK_UN)
    worker.join(timeout=10)
    assert result == ["Entwicklung (Gespräch): Direktheit von 8 auf 9"]
