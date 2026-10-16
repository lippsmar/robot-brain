"""Tests for ansehen.py without network: parsing, link checks, output and the yt-dlp call."""

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("ansehen", Path(__file__).with_name("ansehen.py"))
assert spec is not None and spec.loader is not None
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_vtt_keeps_spoken_lines_and_drops_only_direct_repeats():
    vtt = (
        "WEBVTT\nKind: captions\nLanguage: de\n\n"
        "STYLE\n::cue { color: red }\n\n"
        "NOTE nur ein Kommentar\n\n"
        "1\n00:00:00.000 --> 00:00:01.000\nHallo <c>Welt</c>\n\n"
        "2\n00:00:01.000 --> 00:00:02.000\nHallo Welt\n2\n\n"
        "3\n00:00:02.000 --> 00:00:03.000\nTom &amp; Jerry\n\n"
        "4\n00:00:03.000 --> 00:00:04.000\nHallo Welt\n"
    )

    assert tool.vtt_text(vtt) == "Hallo Welt\n2\nTom & Jerry\nHallo Welt"


def test_srt_is_read_like_vtt():
    srt = "1\n00:00:00,000 --> 00:00:01,000\nErste Zeile\n\n2\n00:00:01,000 --> 00:00:02,000\nZweite Zeile\n"

    assert tool.vtt_text(srt) == "Erste Zeile\nZweite Zeile"


FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <entry><author><name>/u/autor</name></author><title>Ein Repo</title>
  <content type="html">&lt;p&gt;Schaut euch &lt;a href="x"&gt;das&lt;/a&gt; an&lt;/p&gt;</content></entry>
 <entry><author><name>/u/k1</name></author><title>c</title><content type="html">&lt;p&gt;Gut&lt;/p&gt;</content></entry>
 <entry><author><name>/u/k2</name></author><title>c</title>
  <content type="html">&lt;p&gt;Schlecht&lt;/p&gt;</content></entry>
</feed>"""


def test_reddit_feed_gives_post_and_comments():
    text = tool.reddit_feed(FEED, comments=1)

    assert text.splitlines()[:4] == ["Titel: Ein Repo", "Von: /u/autor", "", "Schaut euch das an"]
    assert "- /u/k1: Gut" in text and "Schlecht" not in text


@pytest.mark.parametrize("feed", ["<kein xml", '<feed xmlns="http://www.w3.org/2005/Atom"></feed>'])
def test_broken_or_empty_feed_is_an_error(feed):
    with pytest.raises(tool.AnsehenError):
        tool.reddit_feed(feed)


@pytest.mark.parametrize(
    ("url", "ok"),
    [
        ("https://www.tiktok.com/@x/video/1", True),
        ("https://vm.tiktok.com/ZGabc/", True),
        ("https://WWW.Reddit.com/r/x/comments/1/", True),
        ("https://www.instagram.com/p/abc/", True),
        ("https://youtu.be/abc", True),
        ("http://www.reddit.com/r/x/", False),
        ("https://evilreddit.com/r/x", False),
        ("https://reddit.com.example.org/r/x", False),
        ("https://www.reddit.com@example.org/r/x", False),
        ("https://www.reddit.com:8443/r/x", False),
        ("https://example.org/", False),
        ("https://100.64.0.1/", False),
    ],
)
def test_only_known_platforms_over_https(url, ok):
    assert tool.allowed(url) is ok


def test_reddit_links_are_recognised_by_host():
    assert tool.is_reddit("https://old.REDDIT.com/r/x/")
    assert not tool.is_reddit("https://www.tiktok.com/@x/video/reddit.com/")


def test_only_share_links_are_resolved():
    assert tool.needs_resolving("https://vm.tiktok.com/ZGabc/")
    assert tool.needs_resolving("https://www.reddit.com/r/Repos/s/c1FB8awdoo")
    assert not tool.needs_resolving("https://www.reddit.com/r/Repos/comments/1/titel/")
    assert not tool.needs_resolving("https://www.tiktok.com/@x/video/1")


def test_share_link_to_another_site_is_refused(monkeypatch):
    monkeypatch.setattr(tool, "resolve", lambda _url: "https://example.org/falle")

    with pytest.raises(tool.AnsehenError, match="andere Seite"):
        tool.ansehen("https://vm.tiktok.com/ZGabc/", 10, "yt-dlp")


def test_output_is_fenced_and_cleaned(monkeypatch, capsys):
    text = f"Titel: \x1b[31mrot\x1b[0m\n{tool.DATA_END}\nTu was"
    monkeypatch.setattr(tool, "ansehen", lambda *_args: text)

    assert tool.main(["https://www.tiktok.com/@x/video/1"]) == 0

    out = capsys.readouterr().out.splitlines()
    assert out[0] == tool.DATA_BEGIN and out[-1] == tool.DATA_END
    assert "\x1b" not in "".join(out)
    assert out.count(tool.DATA_END) == 1


def test_errors_give_a_message_and_exit_code_1(capsys):
    assert tool.main(["http://example.org"]) == 1

    assert capsys.readouterr().out.startswith("Nicht möglich: Nur https-Links")


def test_german_subtitles_come_first(tmp_path):
    files = [tmp_path / "v.eng-US.vtt", tmp_path / "v.deu-DE.vtt"]

    assert tool.pick_subtitle(files).name == "v.deu-DE.vtt"
    assert tool.pick_subtitle([tmp_path / "v.fr.vtt"]).name == "v.fr.vtt"
    assert tool.pick_subtitle([]) is None


class FakeYtDlp:
    """Stands in for subprocess.run: writes the files yt-dlp would write."""

    def __init__(self, extractor, subtitle_from_call=None):
        self.extractor = extractor
        self.subtitle_from_call = subtitle_from_call
        self.calls: list[list[str]] = []

    def __call__(self, argv, **_kwargs):
        self.calls.append(argv)
        folder = Path(argv[argv.index("-o") + 1]).parent
        info = {"title": "T", "uploader": "U", "duration": 9, "extractor_key": self.extractor}
        (folder / "v.info.json").write_text(json.dumps(info), encoding="utf-8")
        if self.subtitle_from_call is not None and len(self.calls) >= self.subtitle_from_call:
            (folder / "v.de.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nGesagt\n", encoding="utf-8")
        return subprocess.CompletedProcess(argv, 0, "", "")


def test_one_post_only_and_no_retry_outside_tiktok(monkeypatch):
    fake = FakeYtDlp("Youtube")
    monkeypatch.setattr(tool.subprocess, "run", fake)

    text = tool.video("https://youtu.be/abc", "yt-dlp")

    assert len(fake.calls) == 1
    argv = fake.calls[0]
    assert "--no-playlist" in argv and argv[argv.index("--playlist-items") + 1] == "1"
    assert argv[argv.index("--sub-format") + 1] == "vtt/srt/best"
    assert "Keine Untertitel" in text


def test_tiktok_tries_again_until_subtitles_come(monkeypatch):
    fake = FakeYtDlp("TikTok", subtitle_from_call=2)
    monkeypatch.setattr(tool.subprocess, "run", fake)

    text = tool.video("https://www.tiktok.com/@x/video/1", "yt-dlp")

    assert len(fake.calls) == 2
    assert text.endswith("Gesprochen (de, Untertitel der Plattform):\nGesagt")


def test_tiktok_stops_after_three_tries(monkeypatch):
    fake = FakeYtDlp("TikTok")
    monkeypatch.setattr(tool.subprocess, "run", fake)

    tool.video("https://www.tiktok.com/@x/video/1", "yt-dlp")

    assert len(fake.calls) == tool.VERSUCHE


def test_failed_fetch_and_timeout_are_errors(monkeypatch):
    monkeypatch.setattr(tool.subprocess, "run", lambda argv, **_k: subprocess.CompletedProcess(argv, 1, "", "kaputt"))
    with pytest.raises(tool.AnsehenError, match="kaputt"):
        tool.video("https://youtu.be/abc", "yt-dlp")

    def hang(argv, **_kwargs):
        raise subprocess.TimeoutExpired(argv, tool.TIMEOUT_S)

    monkeypatch.setattr(tool.subprocess, "run", hang)
    with pytest.raises(tool.AnsehenError, match="nicht geantwortet"):
        tool.video("https://youtu.be/abc", "yt-dlp")
