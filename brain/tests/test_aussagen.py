"""Tests for statements with evidence, trust, validity and status (Bauplan Wissen 1.1 and 1.2)."""

import sqlite3

import pytest

from brain.aussagen import Aussagen, AussagenError


@pytest.fixture
def aussagen(tmp_path, log, clock):
    store = Aussagen(tmp_path / "aussagen.db", log=log, clock=clock)
    yield store
    store.close()


def test_new_statement_is_unconfirmed_with_one_piece_of_evidence(aussagen):
    aid = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="datenblatt-bmp280", stufe="A")

    a = aussagen.aussage(aid)
    assert (a.subjekt, a.beziehung, a.objekt, a.status) == ("BMP280", "misst", "Luftdruck", "unbestätigt")
    assert [b.quelle for b in a.belege] == ["datenblatt-bmp280"]
    assert a.text == "BMP280 misst Luftdruck"


def test_same_statement_from_another_source_adds_evidence_not_a_new_entry(aussagen):
    a = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="datenblatt", stufe="A")
    b = aussagen.erfassen("bmp280", "misst", "luftdruck", quelle="wikipedia", stufe="B")
    c = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="wikipedia", stufe="B")  # same source again

    assert a == b == c
    assert [beleg.quelle for beleg in aussagen.aussage(a).belege] == ["datenblatt", "wikipedia"]


def test_trust_grows_with_independent_evidence_and_better_rating(aussagen):
    eine = aussagen.erfassen("A", "ist", "eins", quelle="q1", stufe="C")
    zwei = aussagen.erfassen("B", "ist", "zwei", quelle="q1", stufe="C")
    aussagen.erfassen("B", "ist", "zwei", quelle="q2", stufe="C")
    gut = aussagen.erfassen("C", "ist", "drei", quelle="q1", stufe="A")

    assert aussagen.aussage(zwei).vertrauen > aussagen.aussage(eine).vertrauen
    assert aussagen.aussage(gut).vertrauen > aussagen.aussage(eine).vertrauen
    assert all(0 < aussagen.aussage(x).vertrauen < 1 for x in (eine, zwei, gut))


def test_contradiction_on_a_single_valued_relation_marks_both_disputed(aussagen):
    alt = aussagen.erfassen("Würfel", "Kantenlänge", "10 cm", quelle="design", stufe="A", eindeutig=True)
    neu = aussagen.erfassen("Würfel", "Kantenlänge", "12 cm", quelle="forum", stufe="D", eindeutig=True)

    assert aussagen.aussage(alt).status == "umstritten"
    assert aussagen.aussage(neu).status == "umstritten"


def test_several_values_on_a_normal_relation_are_no_contradiction(aussagen):
    a = aussagen.erfassen("BME280", "misst", "Luftdruck", quelle="q")
    b = aussagen.erfassen("BME280", "misst", "Temperatur", quelle="q")

    assert {aussagen.aussage(a).status, aussagen.aussage(b).status} == {"unbestätigt"}


def test_contradiction_needs_overlapping_validity(aussagen):
    alt = aussagen.erfassen("Budget", "Monatslimit", "10 €", quelle="adr", eindeutig=True, gueltig_bis="2026-10-14")
    neu = aussagen.erfassen("Budget", "Monatslimit", "20 €", quelle="adr", eindeutig=True, gueltig_ab="2026-10-15")

    assert aussagen.aussage(alt).status == "unbestätigt"
    assert aussagen.aussage(neu).status == "unbestätigt"


def test_replaced_statement_stays_but_is_no_longer_found(aussagen):
    alt = aussagen.erfassen("Budget", "Monatslimit", "10 €", quelle="adr")
    neu = aussagen.erfassen("Budget", "Monatslimit", "20 €", quelle="adr")

    aussagen.ersetzen(alt, neu, grund="Marvin: doch 20")

    assert aussagen.aussage(alt).status == "ersetzt"
    assert [a.aid for a in aussagen.finden(subjekt="Budget")] == [neu]
    assert {a.aid for a in aussagen.finden(subjekt="Budget", mit_ersetzten=True)} == {alt, neu}


def test_confirmed_by_marvin(aussagen):
    aid = aussagen.erfassen("Marvin", "trinkt", "Kaffee schwarz", quelle="gespraech", pii=True)

    aussagen.bestaetigen(aid, grund="Marvin hat es gesagt")

    a = aussagen.aussage(aid)
    assert (a.status, a.pii) == ("bestätigt", True)


def test_validity_filters_by_date(aussagen):
    aussagen.erfassen("Budget", "Monatslimit", "10 €", quelle="adr", gueltig_bis="2026-10-14")
    aussagen.erfassen("Budget", "Monatslimit", "20 €", quelle="adr", gueltig_ab="2026-10-15")

    assert [a.objekt for a in aussagen.finden(subjekt="Budget", am="2026-10-10")] == ["10 €"]
    assert [a.objekt for a in aussagen.finden(subjekt="Budget", am="2026-10-16")] == ["20 €"]
    assert len(aussagen.finden(subjekt="Budget")) == 2


def test_removing_a_source_drops_only_its_evidence(aussagen):
    beide = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="datenblatt", stufe="A")
    aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="forum", stufe="D")
    nur_forum = aussagen.erfassen("BMP280", "kostet", "2 €", quelle="forum", stufe="D")

    betroffen = aussagen.quelle_entfernen("forum", grund="Marvin: Forum löschen")

    assert sorted(betroffen) == sorted([beide, nur_forum])
    assert [b.quelle for b in aussagen.aussage(beide).belege] == ["datenblatt"]
    assert aussagen.aussage(nur_forum).belege == ()
    assert [a.aid for a in aussagen.finden(subjekt="BMP280")] == [beide]


def test_evidence_with_pii_makes_the_statement_personal(aussagen):
    aid = aussagen.erfassen("Büro", "liegt in", "Tirana", quelle="karte")
    assert aussagen.aussage(aid).pii is False

    aussagen.erfassen("Büro", "liegt in", "Tirana", quelle="gespraech", pii=True)

    assert aussagen.aussage(aid).pii is True


@pytest.mark.parametrize(
    "fields",
    [
        {"subjekt": ""},
        {"beziehung": " "},
        {"objekt": "a\nb"},
        {"stufe": "E"},
        {"gueltig_ab": "16.10.2026"},
        {"gueltig_ab": "2026-10-20", "gueltig_bis": "2026-10-01"},
        {"quelle": ""},
    ],
)
def test_bad_input_is_rejected(aussagen, fields):
    values = {"subjekt": "A", "beziehung": "ist", "objekt": "B", "quelle": "q"} | fields
    with pytest.raises(AussagenError):
        aussagen.erfassen(values.pop("subjekt"), values.pop("beziehung"), values.pop("objekt"), **values)


def test_unknown_statement_is_an_error(aussagen):
    with pytest.raises(AussagenError):
        aussagen.aussage("a-gibt-es-nicht")
    with pytest.raises(AussagenError):
        aussagen.bestaetigen("a-gibt-es-nicht", grund="x")


def test_history_is_append_only(aussagen, tmp_path):
    aid = aussagen.erfassen("A", "ist", "B", quelle="q")
    aussagen.bestaetigen(aid, grund="damit jede Tabelle eine Zeile hat")  # triggers fire per row
    aussagen.close()
    conn = sqlite3.connect(tmp_path / "aussagen.db")
    for table in ("aussagen", "belege", "ereignisse"):
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(f"DELETE FROM {table}")
        with pytest.raises(sqlite3.DatabaseError):
            conn.execute(f"UPDATE {table} SET ts = 'x'")
    conn.close()


def test_changes_are_logged_with_pii(aussagen, log):
    aid = aussagen.erfassen("Marvin", "mag", "Tee", quelle="gespraech", pii=True)
    aussagen.bestaetigen(aid, grund="gesagt")

    events = [e for e in log.events() if e["intent"].startswith("aussagen.")]
    assert [e["intent"] for e in events] == ["aussagen.erfassen", "aussagen.bestaetigen"]
    assert all(e["pii"] is True for e in events)


def test_search_is_tolerant_of_umlauts_and_case(aussagen):
    aid = aussagen.erfassen("Überdruckventil", "schützt", "Kühlkreislauf", quelle="q")

    assert [a.aid for a in aussagen.finden(subjekt="überdruckventil")] == [aid]
    assert [a.aid for a in aussagen.finden(subjekt="UEBERDRUCKVENTIL", objekt="Kuehlkreislauf")] == [aid]


def test_evidence_given_again_after_removal_counts(aussagen):
    aid = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="forum", stufe="D")
    aussagen.quelle_entfernen("forum", grund="Marvin: Forum löschen")

    wieder = aussagen.erfassen("BMP280", "misst", "Luftdruck", quelle="forum", stufe="B")

    assert wieder == aid
    assert [(b.quelle, b.stufe) for b in aussagen.aussage(aid).belege] == [("forum", "B")]
    assert [a.aid for a in aussagen.finden(subjekt="BMP280")] == [aid]


def test_better_rating_from_a_known_source_raises_trust(aussagen):
    aid = aussagen.erfassen("A", "ist", "B", quelle="q", stufe="D")
    vorher = aussagen.aussage(aid).vertrauen

    aussagen.erfassen("A", "ist", "B", quelle="q", stufe="A")
    aussagen.erfassen("A", "ist", "B", quelle="q", stufe="C")  # worse rating adds nothing

    assert aussagen.aussage(aid).vertrauen > vorher
    assert [b.stufe for b in aussagen.aussage(aid).belege] == ["D", "A"]


def test_marvins_confirmation_wins_over_a_later_contradiction(aussagen):
    richtig = aussagen.erfassen("Würfel", "Kantenlänge", "10 cm", quelle="design", eindeutig=True)
    aussagen.bestaetigen(richtig, grund="Marvin")

    falsch = aussagen.erfassen("Würfel", "Kantenlänge", "12 cm", quelle="forum", eindeutig=True)
    aussagen.erfassen("Würfel", "Kantenlänge", "12 cm", quelle="blog", eindeutig=True)

    assert aussagen.aussage(richtig).status == "bestätigt"
    assert aussagen.aussage(falsch).status == "umstritten"


def test_replacing_ends_the_dispute_for_the_other_value(aussagen):
    alt = aussagen.erfassen("Budget", "Monatslimit", "10 €", quelle="adr", eindeutig=True)
    neu = aussagen.erfassen("Budget", "Monatslimit", "20 €", quelle="adr2", eindeutig=True)

    aussagen.ersetzen(alt, neu, grund="Marvin: 20")

    assert aussagen.aussage(neu).status == "unbestätigt"


def test_removing_the_contradicting_source_ends_the_dispute(aussagen):
    gut = aussagen.erfassen("Würfel", "Kantenlänge", "10 cm", quelle="design", eindeutig=True)
    aussagen.erfassen("Würfel", "Kantenlänge", "12 cm", quelle="forum", eindeutig=True)

    aussagen.quelle_entfernen("forum", grund="Marvin")

    assert aussagen.aussage(gut).status == "unbestätigt"


def test_a_statement_cannot_replace_itself(aussagen):
    aid = aussagen.erfassen("A", "ist", "B", quelle="q")

    with pytest.raises(AussagenError):
        aussagen.ersetzen(aid, aid, grund="x")


def test_removing_personal_evidence_is_logged_as_personal(aussagen, log):
    aussagen.erfassen("Marvin", "mag", "Tee", quelle="gespraech", pii=True)

    aussagen.quelle_entfernen("gespraech", grund="Marvin")

    events = [e for e in log.events() if e["intent"] == "aussagen.quelle_entfernen"]
    assert [e["pii"] for e in events] == [True]
