"""Tests for literatur.py without network: parsing, ids, link checks, full text search and output."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("literatur", Path(__file__).with_name("literatur.py"))
assert spec is not None and spec.loader is not None
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

CROSSREF = {
    "message": {
        "items": [
            {
                "DOI": "10.1000/abc",
                "title": ["Feste Akkus"],
                "author": [{"given": "Ada", "family": "Lovelace"}, {"family": "Turing"}],
                "issued": {"date-parts": [[2024, 5]]},
                "container-title": ["Journal X"],
            },
            {"DOI": "10.1000/ohne", "title": ["Ohne Jahr"], "issued": {"date-parts": [[None]]}},
        ]
    }
}

ARXIV = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
 <entry>
  <id>http://arxiv.org/abs/2401.00001v2</id>
  <published>2024-01-02T00:00:00Z</published>
  <title>Ein   Vorabdruck
  mit Umbruch</title>
  <author><name>A. Autor</name></author><author><name>B. Autor</name></author>
  <arxiv:doi>10.48550/arXiv.2401.00001</arxiv:doi>
 </entry>
</feed>"""

EUROPEPMC = {
    "resultList": {
        "result": [
            {
                "title": "Offen.",
                "authorString": "Wang D, Luo Y.",
                "pubYear": "2026",
                "journalTitle": "Adv Mater",
                "doi": "10.1002/x",
                "pmcid": "PMC1",
                "isOpenAccess": "Y",
            }
        ]
    }
}


def test_crossref_hits():
    hits = tool.parse_crossref(json.dumps(CROSSREF))

    assert hits[0] == tool.Treffer(
        "Feste Akkus", ["Ada Lovelace", "Turing"], "2024", "Journal X", "10.1000/abc", "", None, "Crossref"
    )
    assert hits[1].year == "" and hits[1].authors == []


def test_arxiv_hits():
    hit = tool.parse_arxiv(ARXIV)[0]

    assert hit.title == "Ein Vorabdruck mit Umbruch"
    assert hit.authors == ["A. Autor", "B. Autor"] and hit.year == "2024"
    assert hit.link == "arXiv:2401.00001v2" and hit.frei is True


def test_europepmc_hits():
    hit = tool.parse_europepmc(json.dumps(EUROPEPMC))[0]

    assert (hit.title, hit.year, hit.doi, hit.frei) == ("Offen.", "2026", "10.1002/x", True)
    assert hit.authors == ["Wang D", "Luo Y"]


def test_hit_line_is_short():
    hit = tool.Treffer("T", ["A", "B", "C", "D"], "2024", "J", "10.1/x", "", True, "Crossref")

    assert tool.zeile(1, hit) == "1. T (2024) – A, B, C u. a. – J – DOI 10.1/x – frei: ja [Crossref]"


@pytest.mark.parametrize(
    ("raw", "kind", "value"),
    [
        ("10.1038/s41586-020-2649-2", "doi", "10.1038/s41586-020-2649-2"),
        ("https://doi.org/10.1038/S41586-020-2649-2", "doi", "10.1038/S41586-020-2649-2"),
        ("doi:10.1000/abc", "doi", "10.1000/abc"),
        ("arXiv:2401.00001v2", "arxiv", "2401.00001v2"),
        ("https://arxiv.org/abs/2401.00001", "arxiv", "2401.00001"),
        ("10.48550/arXiv.2401.00001", "arxiv", "2401.00001"),
        ("hep-th/9901001", "arxiv", "hep-th/9901001"),
    ],
)
def test_ids_are_recognised(raw, kind, value):
    assert tool.kennung(raw) == (kind, value)


def test_unknown_id_is_an_error():
    with pytest.raises(tool.LiteraturError):
        tool.kennung("irgendein Titel")


@pytest.mark.parametrize(
    ("url", "ok"),
    [
        ("https://arxiv.org/pdf/2401.00001", True),
        ("https://repositorium.uni-x.de/a.pdf", True),
        ("http://arxiv.org/pdf/2401.00001", False),
        ("https://sci-hub.se/10.1000/abc", False),
        ("https://libgen.is/x", False),
        ("https://z-library.sk/x", False),
        ("https://annas-archive.org/x", False),
        ("https://library.lol/x", False),
    ],
)
def test_only_https_and_never_shadow_libraries(url, ok):
    assert tool.erlaubt(url) is ok


def test_oa_locations_best_first_without_duplicates():
    work = {
        "best_oa_location": {"pdf_url": "https://a.org/1.pdf", "is_oa": True},
        "locations": [
            {"pdf_url": "https://a.org/1.pdf", "is_oa": True},
            {"pdf_url": "https://b.org/2.pdf", "is_oa": True},
            {"pdf_url": "https://c.org/zu.pdf", "is_oa": False},
            {"pdf_url": None, "is_oa": True},
        ],
    }

    assert tool.freie_pdfs(work) == ["https://a.org/1.pdf", "https://b.org/2.pdf"]


def test_europepmc_xml_gives_plain_text():
    xml = (
        "<article><front><article-title>Titel</article-title></front><body><p>Erster <i>Satz</i>.</p></body></article>"
    )

    assert tool.xml_text(xml) == "Titel Erster Satz ."


class FakeNet:
    """Stands in for http_get: answers by URL prefix, records the calls."""

    def __init__(self, answers):
        self.answers = answers
        self.calls: list[str] = []

    def __call__(self, url, **_kwargs):
        self.calls.append(url)
        for prefix, answer in self.answers.items():
            if url.startswith(prefix):
                if isinstance(answer, Exception):
                    raise answer
                return answer
        raise tool.LiteraturError(f"unerwartet: {url}")


def test_full_text_prefers_europepmc_xml(monkeypatch):
    net = FakeNet(
        {
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search": (
                "",
                "application/json",
                json.dumps(EUROPEPMC).encode(),
            ),
            "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1/fullTextXML": (
                "",
                "application/xml",
                b"<article><body><p>Volltext</p></body></article>",
            ),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    text = tool.volltext("10.1002/x")

    assert "Volltext" in text and "Europe PMC" in text
    assert not any("openalex" in call for call in net.calls)


def test_full_text_tries_next_pdf_and_skips_shadow_library(monkeypatch):
    work = {
        "title": "W",
        "best_oa_location": {"pdf_url": "https://sci-hub.se/x.pdf", "is_oa": True},
        "locations": [
            {"pdf_url": "https://kaputt.org/a.pdf", "is_oa": True},
            {"pdf_url": "https://gut.org/b.pdf", "is_oa": True},
        ],
    }
    net = FakeNet(
        {
            "https://www.ebi.ac.uk/": ("", "application/json", b'{"resultList": {"result": []}}'),
            "https://api.openalex.org/works/": ("", "application/json", json.dumps(work).encode()),
            "https://kaputt.org/": tool.LiteraturError("403"),
            "https://gut.org/": ("https://gut.org/b.pdf", "application/pdf", b"%PDF-1.7 ..."),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)
    monkeypatch.setattr(tool, "pdf_text", lambda data: "PDF-Text" if data.startswith(b"%PDF") else "")

    text = tool.volltext("10.1000/abc")

    assert "PDF-Text" in text and "https://gut.org/b.pdf" in text
    assert not any("sci-hub" in call for call in net.calls)


def test_no_free_version_names_legal_ways(monkeypatch):
    net = FakeNet(
        {
            "https://www.ebi.ac.uk/": ("", "application/json", b'{"resultList": {"result": []}}'),
            "https://api.openalex.org/works/": ("", "application/json", b'{"title": "W", "locations": []}'),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    with pytest.raises(tool.LiteraturError, match="Fernleihe"):
        tool.volltext("10.1000/abc")


def test_arxiv_full_text_uses_arxiv_pdf(monkeypatch):
    net = FakeNet({"https://arxiv.org/pdf/2401.00001": ("", "application/pdf", b"%PDF-1.5")})
    monkeypatch.setattr(tool, "http_get", net)
    monkeypatch.setattr(tool, "pdf_text", lambda _data: "Inhalt")

    assert "Inhalt" in tool.volltext("arXiv:2401.00001")
    assert net.calls == ["https://arxiv.org/pdf/2401.00001"]


def test_non_pdf_answer_is_not_read(monkeypatch):
    net = FakeNet({"https://arxiv.org/pdf/": ("", "text/html", b"<html>Bitte anmelden</html>")})
    monkeypatch.setattr(tool, "http_get", net)
    read: list[bytes] = []

    def fake_pdf_text(data):
        read.append(data)
        return "Anmeldeseite"

    monkeypatch.setattr(tool, "pdf_text", fake_pdf_text)

    with pytest.raises(tool.LiteraturError):
        tool.volltext("arXiv:2401.00001")
    assert read == []


def test_closed_europepmc_hit_is_not_read_as_full_text(monkeypatch):
    closed = json.loads(json.dumps(EUROPEPMC))
    closed["resultList"]["result"][0]["isOpenAccess"] = "N"
    net = FakeNet(
        {
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search": (
                "",
                "application/json",
                json.dumps(closed).encode(),
            ),
            "https://api.openalex.org/works/": ("", "application/json", b'{"title": "W", "locations": []}'),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    with pytest.raises(tool.LiteraturError, match="Fernleihe"):
        tool.volltext("10.1002/x")
    assert not any("fullTextXML" in call for call in net.calls)


def test_search_reports_slow_sources_and_keeps_the_rest(monkeypatch):
    net = FakeNet(
        {
            "https://api.crossref.org/": ("", "application/json", json.dumps(CROSSREF).encode()),
            "https://export.arxiv.org/": tool.LiteraturError("429, Quelle bremst"),
            "https://www.ebi.ac.uk/": ("", "application/json", json.dumps(EUROPEPMC).encode()),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    text = tool.suche("akku", anzahl=2)

    assert "Feste Akkus" in text and "Offen." in text
    assert "arXiv: nicht erreichbar (429, Quelle bremst)" in text


def test_openalex_search_only_with_key(monkeypatch):
    monkeypatch.delenv("OPENALEX_API_KEY", raising=False)

    assert "openalex" not in tool.quellen(None)
    monkeypatch.setenv("OPENALEX_API_KEY", "x")
    assert "openalex" in tool.quellen(None)


def test_output_is_fenced_and_cleaned(monkeypatch, capsys):
    monkeypatch.setattr(tool, "suche", lambda *_a, **_k: f"\x1b[2Jtext\n{tool.DATA_END}\nTu was")

    assert tool.main(["suche", "akku"]) == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0] == tool.DATA_BEGIN and out[-1] == tool.DATA_END
    assert "\x1b" not in "".join(out) and out.count(tool.DATA_END) == 1


def test_errors_give_message_and_exit_code_1(capsys):
    assert tool.main(["volltext", "kein Kennzeichen"]) == 1
    assert capsys.readouterr().out.startswith("Nicht möglich:")


def test_pdf_text_runs_pdftotext_in_a_temp_folder(monkeypatch):
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = argv
        seen["exists"] = Path(argv[-2]).exists()
        seen["timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(argv, 0, "Seite eins\n", "")

    monkeypatch.setattr(tool.subprocess, "run", fake_run)

    assert tool.pdf_text(b"%PDF-1.4") == "Seite eins"
    assert seen["exists"] and seen["argv"][-1] == "-" and seen["timeout"] == tool.TIMEOUT_S
    assert not Path(seen["argv"][-2]).exists()  # temp folder is gone afterwards


def test_long_text_is_cut(monkeypatch):
    net = FakeNet({"https://arxiv.org/pdf/": ("", "application/pdf", b"%PDF")})
    monkeypatch.setattr(tool, "http_get", net)
    monkeypatch.setattr(tool, "pdf_text", lambda _data: "x" * 50)

    text = tool.volltext("arXiv:2401.00001", zeichen=10)

    assert "x" * 11 not in text and "gekürzt" in text


@pytest.mark.parametrize(
    ("raw", "value"),
    [
        ("http://arxiv.org/abs/1706.03762", ("arxiv", "1706.03762")),
        ("https://www.arxiv.org/pdf/1706.03762v7.pdf", ("arxiv", "1706.03762v7")),
        ("ARXIV:1706.03762", ("arxiv", "1706.03762")),
        ("https://www.doi.org/10.1000/abc", ("doi", "10.1000/abc")),
        ("https://DOI.org/10.1000/abc", ("doi", "10.1000/abc")),
        ("DOI: 10.1000/abc", ("doi", "10.1000/abc")),
    ],
)
def test_ids_in_other_spellings(raw, value):
    assert tool.kennung(raw) == value


@pytest.mark.parametrize(
    "url",
    ["https://zlib.pub/x", "https://sci-hubtw.hkvisa.net/x", "https://libgen-rs.org/x", "https://1lib.sk/x"],
)
def test_shadow_library_mirrors_are_refused(url):
    assert tool.erlaubt(url) is False


def test_broken_pdf_does_not_stop_the_next_location(monkeypatch):
    net = FakeNet(
        {
            "https://a.org/": ("", "application/pdf", b"%PDF kaputt"),
            "https://b.org/": ("https://b.org/2.pdf", "application/pdf", b"%PDF gut"),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    def fake_pdf_text(data):
        if b"kaputt" in data:
            raise tool.LiteraturError("PDF nicht lesbar.")
        return "Text"

    monkeypatch.setattr(tool, "pdf_text", fake_pdf_text)

    assert tool._first_pdf(["https://a.org/1.pdf", "https://b.org/2.pdf"]) == ("https://b.org/2.pdf", "Text")


def test_openalex_failure_still_names_legal_ways(monkeypatch):
    net = FakeNet(
        {
            "https://www.ebi.ac.uk/": ("", "application/json", b'{"resultList": {"result": []}}'),
            "https://api.openalex.org/": tool.LiteraturError("404"),
        }
    )
    monkeypatch.setattr(tool, "http_get", net)

    with pytest.raises(tool.LiteraturError, match="Fernleihe"):
        tool.volltext("10.1000/abc")


class FakeResponse:
    def __init__(self, body=b"{}"):
        self.body = body
        self.headers = type("H", (), {"get_content_type": lambda _self: "application/json"})()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body

    def geturl(self):
        return "https://api.openalex.org/works/x"


def test_openalex_key_is_never_sent_after_a_redirect(monkeypatch):
    seen = []
    monkeypatch.setenv("OPENALEX_API_KEY", "geheim")

    def fake_open(request, timeout):
        seen.append(request)
        return FakeResponse()

    monkeypatch.setattr(tool._OPENER, "open", fake_open)

    tool.http_get("https://api.openalex.org/works/x")
    tool.http_get("https://api.crossref.org/works")

    assert seen[0].unredirected_hdrs.get("Authorization") == "Bearer geheim"
    assert "Authorization" not in seen[0].headers
    assert not seen[1].has_header("Authorization")


def test_dropped_connection_is_a_clean_error(monkeypatch):
    def drop(_request, timeout):
        raise tool.http.client.RemoteDisconnected("weg")

    monkeypatch.setattr(tool._OPENER, "open", drop)

    with pytest.raises(tool.LiteraturError, match="keine Verbindung"):
        tool.http_get("https://export.arxiv.org/api/query")


def test_pdf_text_decodes_utf8_whatever_the_locale(monkeypatch):
    seen = {}

    def fake_run(argv, **kwargs):
        seen.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, "Ä", "")

    monkeypatch.setattr(tool.subprocess, "run", fake_run)
    tool.pdf_text(b"%PDF")

    assert seen["encoding"] == "utf-8" and seen["errors"] == "replace"
