"""Tests for free research sources with bot name and robots.txt (Bauplan Wissen 1.5), no network."""

import json
from datetime import timedelta

import pytest

from brain.freie_quellen import BOT_NAME, FreieQuellen, QuelleError, http_get

WIKI_ROBOTS = """User-agent: *
Allow: /w/api.php?action=mobileview&
Disallow: /w/
Disallow: /api/
Disallow: /wiki/Spezial:
"""

ARTIKEL = """<html><head><title>Barometer – Wikipedia</title></head><body>
<h1 id="firstHeading">Barometer</h1>
<div id="mw-content-text"><div class="mw-parser-output">
<table class="infobox"><tr><td><p>Tabelle bleibt draußen</p></td></tr></table>
<p>Ein <b>Barometer</b> ist ein Messgerät für den Luftdruck.<sup class="reference">[1]</sup><sup>[Anm. 1]</sup></p>
<p>Es wurde 1643 erfunden.</p>
<style>.x{}</style><script>alert(1)</script>
<ol class="references"><li>Quelle</li></ol>
</div></div></body></html>"""

MARGINALIA = {
    "license": "CC-BY-NC-SA 4.0",
    "results": [
        {"url": "https://de.wikipedia.org/wiki/Barometer", "title": "Barometer", "description": "Messgerät"},
        {"url": "http://alt.example.org/x", "title": "Alt", "description": "ohne https"},
    ],
}


class FakeNetz:
    """Answers by URL; counts calls. A value may be (status, body), (status, body, target) or an exception."""

    def __init__(self, antworten):
        self.antworten = antworten
        self.aufrufe: list[str] = []

    def __call__(self, url, *, accept, limit):
        self.aufrufe.append(url)
        for prefix, antwort in self.antworten.items():
            if url.startswith(prefix):
                if isinstance(antwort, Exception):
                    raise antwort
                status, body, *ziel = antwort
                return status, body.encode("utf-8") if isinstance(body, str) else body, (ziel or [None])[0]
        return 404, b"", None


@pytest.fixture
def netz():
    return FakeNetz(
        {
            "https://de.wikipedia.org/robots.txt": (200, WIKI_ROBOTS),
            "https://de.wikipedia.org/wiki/Barometer": (200, ARTIKEL),
            "https://api.marginalia.nu/robots.txt": (401, "Unauthorized"),
            "https://api.marginalia.nu/public/search/": (200, json.dumps(MARGINALIA)),
        }
    )


@pytest.fixture
def quellen(netz, log, clock):
    return FreieQuellen(netz=netz, log=log, clock=clock)


def test_wikipedia_article_text_without_tables_footnotes_and_scripts(quellen):
    artikel = quellen.wikipedia_artikel("Barometer")

    assert artikel.titel == "Barometer"
    assert artikel.text == "Ein Barometer ist ein Messgerät für den Luftdruck.\n\nEs wurde 1643 erfunden."
    assert artikel.url == "https://de.wikipedia.org/wiki/Barometer"
    assert artikel.lizenz == "CC BY-SA 4.0"


def test_article_text_is_cut_to_the_limit(quellen):
    artikel = quellen.wikipedia_artikel("Barometer", zeichen=20)

    assert len(artikel.text) <= 20


def test_robots_txt_is_obeyed_for_the_wikipedia_api(quellen, netz):
    with pytest.raises(QuelleError, match=r"robots\.txt"):
        quellen.abrufen("https://de.wikipedia.org/w/api.php?action=query&list=search&srsearch=x")

    assert not any("/w/api.php" in url for url in netz.aufrufe)


def test_robots_txt_is_read_once_per_host(quellen, netz):
    quellen.wikipedia_artikel("Barometer")
    quellen.wikipedia_artikel("Barometer")

    assert netz.aufrufe.count("https://de.wikipedia.org/robots.txt") == 1


def test_missing_robots_txt_with_4xx_allows_and_with_5xx_forbids(netz, log, clock):
    netz.antworten["https://kaputt.example.org/robots.txt"] = (503, "")
    netz.antworten["https://kaputt.example.org/seite"] = (200, "x")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    assert quellen.erlaubt("https://api.marginalia.nu/public/search/x") is True  # 401: RFC 9309 allows
    assert quellen.erlaubt("https://kaputt.example.org/seite") is False  # 5xx: assume everything is closed


def test_marginalia_search_gives_hits_with_licence_and_skips_plain_http(quellen, netz):
    treffer = quellen.marginalia_suche("Barometer Luftdruck", anzahl=5)

    assert [(t.titel, t.url) for t in treffer] == [("Barometer", "https://de.wikipedia.org/wiki/Barometer")]
    assert treffer[0].lizenz == "CC-BY-NC-SA 4.0"
    assert treffer[0].quelle == "Marginalia"
    url = next(u for u in netz.aufrufe if "/public/search/" in u)
    assert "Barometer%20Luftdruck" in url and "count=5" in url


def test_only_https(quellen):
    with pytest.raises(QuelleError, match="https"):
        quellen.abrufen("http://de.wikipedia.org/wiki/Barometer")


def test_rate_limit_and_errors_give_clear_messages(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/Gesperrt"] = (429, "")
    netz.antworten["https://de.wikipedia.org/wiki/Fehlt"] = (404, "")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    with pytest.raises(QuelleError, match="bremst"):
        quellen.wikipedia_artikel("Gesperrt")
    with pytest.raises(QuelleError, match="404"):
        quellen.wikipedia_artikel("Fehlt")


def test_titles_cannot_leave_the_article_path(quellen, netz):
    for titel in ["../w/api.php", "Spezial:Suche", "a?b=c", ""]:
        with pytest.raises(QuelleError):
            quellen.wikipedia_artikel(titel)
    assert not any("api.php" in url for url in netz.aufrufe)


def test_control_characters_are_removed_from_foreign_text(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/Steuer"] = (
        200,
        '<div id="mw-content-text"><p>Text\x1b[31m mit Escape</p></div>',
    )
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    assert "\x1b" not in quellen.wikipedia_artikel("Steuer").text


def test_every_fetch_is_logged(quellen, log):
    quellen.wikipedia_artikel("Barometer")

    events = [e for e in log.events() if e["intent"] == "recherche.abruf"]
    assert events and events[-1]["payload"]["host"] == "de.wikipedia.org"


def test_bot_name_is_honest():
    assert BOT_NAME == "Schlaubi"


def test_redirect_into_a_closed_path_is_not_followed(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/Umweg"] = (301, "", "/w/index.php?title=Geheim")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    with pytest.raises(QuelleError, match=r"robots\.txt"):
        quellen.wikipedia_artikel("Umweg")
    assert not any("/w/index.php" in url for url in netz.aufrufe)


def test_redirect_to_an_allowed_page_is_followed(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/Luftdruckmesser"] = (301, "", "/wiki/Barometer")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    assert quellen.wikipedia_artikel("Luftdruckmesser").text.startswith("Ein Barometer")


def test_redirect_to_plain_http_or_in_circles_stops(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/Alt"] = (302, "", "http://de.wikipedia.org/wiki/Barometer")
    netz.antworten["https://de.wikipedia.org/wiki/Kreis"] = (302, "", "/wiki/Kreis")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    with pytest.raises(QuelleError, match="https"):
        quellen.wikipedia_artikel("Alt")
    with pytest.raises(QuelleError, match="Weiterleitungen"):
        quellen.wikipedia_artikel("Kreis")


def test_robots_txt_answering_429_closes_the_host(netz, log, clock):
    netz.antworten["https://langsam.example.org/robots.txt"] = (429, "")
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    assert quellen.erlaubt("https://langsam.example.org/seite") is False


def test_unreachable_robots_txt_is_asked_again_after_a_short_while(netz, log, clock):
    netz.antworten["https://wackel.example.org/robots.txt"] = QuelleError("keine Verbindung")
    jetzt = [clock()]
    quellen = FreieQuellen(netz=netz, log=log, clock=lambda: jetzt[0])
    assert quellen.erlaubt("https://wackel.example.org/seite") is False

    netz.antworten["https://wackel.example.org/robots.txt"] = (404, "")
    jetzt[0] += timedelta(minutes=5)
    assert quellen.erlaubt("https://wackel.example.org/seite") is False  # still cached
    jetzt[0] += timedelta(minutes=10)
    assert quellen.erlaubt("https://wackel.example.org/seite") is True


def test_titles_with_a_slash_and_escaped_text_stay_intact(netz, log, clock):
    netz.antworten["https://de.wikipedia.org/wiki/AC%2FDC"] = (
        200,
        '<div id="mw-content-text"><p>AC/DC schreibt &amp;lt;b&amp;gt; im Text.</p></div>',
    )
    quellen = FreieQuellen(netz=netz, log=log, clock=clock)

    assert quellen.wikipedia_artikel("AC/DC").text == "AC/DC schreibt &lt;b&gt; im Text."


def test_http_get_gives_the_redirect_target_back(monkeypatch):
    import urllib.error
    from email.message import Message

    headers = Message()
    headers["Location"] = "/wiki/Ziel"

    def open_(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 301, "Moved", headers, None)

    monkeypatch.setattr("brain.freie_quellen._OPENER.open", open_)

    assert http_get("https://de.wikipedia.org/wiki/X", accept="text/html", limit=10) == (301, b"", "/wiki/Ziel")


def test_http_get_says_when_the_server_is_too_slow(monkeypatch):
    def open_(request, timeout):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr("brain.freie_quellen._OPENER.open", open_)

    with pytest.raises(QuelleError, match="keine Antwort"):
        http_get("https://api.marginalia.nu/public/search/x", accept="application/json", limit=10)
