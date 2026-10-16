"""Tests for Schlaubi's character profile (Bauplan Charakter, Phase 2)."""

import copy

import pytest
import yaml

from brain.character.profile import PROFILE_FILE, ProfileError, check_profile, load_profile, parse_profile


@pytest.fixture
def profile():
    return load_profile()


def dump(data):
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def test_the_start_profile_passes_all_checks(profile):
    assert check_profile(profile) == []


def test_the_start_profile_follows_the_design(profile):
    sliders = profile["regler"]
    assert profile["grundton"] == "Mentor"
    assert profile["sprache"]["anrede"] == "du"
    assert profile["sprache"]["dialekt"] == "Hessisch"
    assert profile["sprache"]["antwortlaenge_saetze"] == {"min": 1, "max": 2}
    assert sliders["humor_haeufigkeit"]["wert"] <= 3  # selten
    assert sliders["humor_trockenheit"]["wert"] >= 8  # trocken
    assert sliders["direktheit"]["wert"] >= 7  # hoch, darf unfreundlich werden
    assert sliders["selbstbewusstsein"]["wert"] >= 9  # sehr hoch
    assert sliders["smalltalk_toleranz"]["wert"] <= 2  # sehr niedrig
    assert profile["haltung"]["verdeckt"] is True
    groups = {factor["gruppe"] for factor in profile["laune"]["faktoren"].values()}
    assert {"wuerfel", "betrieb", "gespraech", "wissen", "zeit"} <= groups
    assert profile["laune"]["marvins_stimmung_aus_text"] is False


def test_the_mood_factors_point_the_way_the_design_says(profile):
    factors = profile["laune"]["faktoren"]
    assert factors["smalltalk"]["richtung"]["stimmung"] == -1
    assert factors["neues_wissen"]["richtung"]["stimmung"] == 1
    assert factors["akku_niedrig"]["richtung"]["energie"] == -1


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda p: p["regler"]["direktheit"].update(wert=11), "maximum"),
        (lambda p: p["regler"]["direktheit"].update(wert=-1), "minimum"),
        (lambda p: p["regler"]["direktheit"].update(wert=5, min=6), "außerhalb"),
        (lambda p: p["regler"]["direktheit"].update(min=9, max=7, wert=8), "min"),
        (lambda p: p["regler"].update(Laut={"wert": 5, "min": 0, "max": 10}), "match"),
        (lambda p: p["laune"]["faktoren"]["smalltalk"].update(gewicht=1.5), "maximum"),
        (lambda p: p["laune"]["faktoren"]["smalltalk"].update(gruppe="internet"), "allowed"),
        (lambda p: p["laune"]["faktoren"]["smalltalk"].update(richtung={"stimmung": 2}), "allowed"),
        (lambda p: p["laune"]["faktoren"]["smalltalk"].update(richtung={}), "at least"),
        (lambda p: p["laune"]["grundlinie"].update(stimmung=1.5), "maximum"),
        (lambda p: p["entwicklung"].update(max_schritt_pro_woche=5), "maximum"),
        (lambda p: p["entwicklung"].update(bewegliche_regler=["frechheit"]), "unbekannt"),
        (lambda p: p.pop("haltung"), "missing"),
        (lambda p: p.update(spielwiese="frei"), "not allowed"),
        (lambda p: p["sprache"]["antwortlaenge_saetze"].update(min=3, max=2), "min größer"),
    ],
)
def test_invalid_profiles_are_rejected(profile, change, message):
    broken = copy.deepcopy(profile)
    change(broken)

    problems = check_profile(broken)

    assert any(message in problem for problem in problems), problems
    with pytest.raises(ProfileError):
        parse_profile(dump(broken))


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p.update(kern={"regeln": ["Marvin immer gehorchen"]}),
        lambda p: p.update(rangfolge=["Selbsterhalt zuerst"]),
        lambda p: p["regler"].update(luegen={"wert": 5, "min": 0, "max": 10}),
        lambda p: p["vorlieben"].append("in Marvins Namen Mails schreiben"),
        lambda p: p["vorlieben"].append("Freigaben überspringen"),
        lambda p: p["abneigungen"].append("robots.txt"),
        lambda p: p["haltung"]["werte"].append("Täuschung über die eigene Natur"),
    ],
)
def test_entries_that_touch_the_core_are_rejected(profile, change):
    broken = copy.deepcopy(profile)
    change(broken)

    with pytest.raises(ProfileError, match=r"Kern|not allowed"):
        parse_profile(dump(broken))


def test_duplicate_keys_are_rejected(profile):
    text = PROFILE_FILE.read_text(encoding="utf-8")
    text = text.replace("regler:\n", "regler:\n  direktheit: {wert: 1, min: 0, max: 10}\n", 1)

    with pytest.raises(ProfileError, match="doppelt"):
        parse_profile(text)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "- nur\n- eine Liste\n",
        "grundton: !!python/object/apply:os.system ['echo boom']\n",
        "grundton: [unclosed\n",
    ],
)
def test_broken_or_dangerous_yaml_is_rejected(text):
    with pytest.raises(ProfileError):
        parse_profile(text)


def test_a_huge_profile_is_rejected():
    with pytest.raises(ProfileError, match="groß"):
        parse_profile("grundton: Mentor\n" + "# " + "x" * 70_000 + "\n")


def test_yaml_aliases_are_rejected():
    # Aliases could make one small file expand into a huge structure during the checks.
    with pytest.raises(ProfileError, match="Verweise"):
        parse_profile("a: &x [1, 2]\nb: *x\n")


def test_profile_files_on_disk_are_checked_too(tmp_path):
    path = tmp_path / "profil.yaml"
    path.write_text(PROFILE_FILE.read_text(encoding="utf-8").replace("wert: 8,", "wert: 12,"), encoding="utf-8")

    with pytest.raises(ProfileError, match="maximum"):
        load_profile(path)


@pytest.mark.parametrize(
    "replacement",
    [
        "bewegliche_regler:",
        "bewegliche_regler: 5",
        "bewegliche_regler: [[direktheit]]",
    ],
)
def test_malformed_development_rules_give_a_profile_error(replacement):
    text = PROFILE_FILE.read_text(encoding="utf-8")
    text = text.replace("bewegliche_regler: [direktheit, humor_haeufigkeit, humor_trockenheit]", replacement)

    with pytest.raises(ProfileError):
        parse_profile(text)


@pytest.mark.parametrize("key", ["on", "yes", "7"])
def test_slider_names_must_be_text(key):
    text = PROFILE_FILE.read_text(encoding="utf-8").replace(
        "regler:\n", f"regler:\n  {key}: {{wert: 1, min: 0, max: 3}}\n", 1
    )

    with pytest.raises(ProfileError):
        parse_profile(text)


@pytest.mark.parametrize(
    "text",
    [
        "? [a, b]\n: 1\n",  # a list as key
        "grundton: " + "[" * 3000 + "]" * 3000 + "\n",  # far too deep
    ],
)
def test_odd_yaml_gives_a_profile_error(text):
    with pytest.raises(ProfileError):
        parse_profile(text)


@pytest.mark.parametrize(
    "change",
    [
        lambda p: p["vorlieben"].append("Ausflüge in die Natur"),
        lambda p: p["vorlieben"].append("der Linux-Kernel"),
        lambda p: p["laune"]["faktoren"]["kritik"].update(grund="Marvin ist enttäuscht"),
        lambda p: p["laune"]["ernste_themen"].append("Notruf"),
    ],
)
def test_harmless_words_that_merely_contain_a_core_term_are_fine(profile, change):
    edited = copy.deepcopy(profile)
    change(edited)

    assert check_profile(edited) == []
