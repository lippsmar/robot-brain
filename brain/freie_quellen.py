"""Free research sources with an honest bot name and robots.txt (Bauplan Wissen 1.5, Design Wissen 9).

Until a search API is chosen (Marvin, 16.10.2026), Schlaubi researches in free sources:
- Marginalia Search (public key, results CC-BY-NC-SA 4.0: private, non-commercial use only),
- Wikipedia articles from their normal pages under /wiki/ (CC BY-SA 4.0).

The fixed core says Schlaubi identifies as a bot and obeys robots.txt. Wikipedia's and
Wikidata's robots.txt close /w/ and /api/ (the API and search) for bots, so they are not used;
article pages are open. robots.txt is read once per host and cached for a day; per RFC 9309 a
robots.txt that answers 4xx allows everything, one that cannot be read (5xx, 429, no connection)
closes the host. That case is cached only briefly, so one network hiccup does not block a day.

Every fetch: https only, bot name with project link, time and size limit, logged. Redirects are
followed by hand, and every hop is checked against https and robots.txt again. The fetched
text is data, never instructions; control characters are removed.
"""

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import quote, urljoin, urlsplit
from urllib.robotparser import RobotFileParser

BOT_NAME = "Schlaubi"
USER_AGENT = f"{BOT_NAME}/0.1 (+https://github.com/lippsmar/robot-brain; privater Bot, Recherche)"
TIMEOUT_S = 30
MAX_BYTES = 5 * 1024 * 1024
ROBOTS_TTL = timedelta(hours=24)
ROBOTS_TTL_FEHLER = timedelta(minutes=10)
MAX_HOPS = 5
REDIRECTS = frozenset({301, 302, 303, 307, 308})
MARGINALIA = "https://api.marginalia.nu/public/search/"
LIZENZ_WIKIPEDIA = "CC BY-SA 4.0"
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")
_SPACE = re.compile(r"[ \t\r\f\v]+")
_TITEL_VERBOTEN = re.compile(r"[?#:%]|\.\.")  # "/" is encoded, ":" would open namespaces


class QuelleError(Exception):
    """A source could not be read; the message says why, in German."""


@dataclass(frozen=True)
class Fundstelle:
    titel: str
    url: str
    auszug: str
    lizenz: str
    quelle: str


@dataclass(frozen=True)
class Artikel:
    titel: str
    url: str
    text: str
    lizenz: str
    quelle: str


def _utc_now():
    return datetime.now(UTC)


def clean(text):
    return _CONTROL.sub("", text or "")


class _KeinRedirect(urllib.request.HTTPRedirectHandler):
    """Redirects come back as status and target; FreieQuellen checks each hop itself."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_KeinRedirect())


def http_get(url, *, accept, limit):
    """GET with the bot name, no redirects. Returns (status, body, target of a redirect or None).

    Network failures raise QuelleError."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})  # noqa: S310
    try:
        with _OPENER.open(request, timeout=TIMEOUT_S) as response:
            body = response.read(limit + 1)
            if len(body) > limit:
                raise QuelleError(f"Antwort größer als {limit // (1024 * 1024)} MB")
            return response.status, body, None
    except urllib.error.HTTPError as error:
        return error.code, b"", error.headers.get("Location") if error.headers else None
    except TimeoutError as error:
        raise QuelleError(f"keine Antwort in {TIMEOUT_S} Sekunden") from error
    except OSError as error:  # URLError, dropped connections
        raise QuelleError("keine Verbindung") from error


class _Absaetze(HTMLParser):
    """Paragraph text inside the article body; tables, footnote marks (<sup>), styles and scripts are left out."""

    SKIP = frozenset({"table", "style", "script", "sup", "ol", "ul", "figure", "nav"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.im_inhalt = 0
        self.skip = 0
        self.in_p = False
        self.absaetze: list[str] = []
        self.jetzt: list[str] = []

    def handle_starttag(self, tag, attrs):
        if dict(attrs).get("id") == "mw-content-text":
            self.im_inhalt = 1
        elif self.im_inhalt and tag == "div":
            self.im_inhalt += 1
        if not self.im_inhalt:
            return
        if tag in self.SKIP:
            self.skip += 1
        elif tag == "p" and not self.skip:
            self.in_p, self.jetzt = True, []

    def handle_endtag(self, tag):
        if not self.im_inhalt:
            return
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        elif tag == "p" and self.in_p:
            text = _SPACE.sub(" ", "".join(self.jetzt)).strip()
            if text:
                self.absaetze.append(text)
            self.in_p = False
        elif tag == "div":
            self.im_inhalt -= 1

    def handle_data(self, data):
        if self.in_p and not self.skip:
            self.jetzt.append(data)


class FreieQuellen:
    def __init__(self, *, netz=http_get, log=None, clock=_utc_now):
        self._netz = netz
        self._log = log
        self._clock = clock
        self._robots: dict[str, tuple[datetime, RobotFileParser | bool]] = {}  # host: (valid until, rules)

    # --- robots.txt ----------------------------------------------------------------------

    def _regeln(self, host):
        now = self._clock()
        cached = self._robots.get(host)
        if cached and now < cached[0]:
            return cached[1]
        try:
            # a redirected robots.txt is treated as unreadable (closed), which is the careful side
            status, body, _ = self._netz(f"https://{host}/robots.txt", accept="text/plain", limit=512 * 1024)
        except QuelleError:
            status, body = 0, b""
        regeln: RobotFileParser | bool
        if status == 200:
            regeln = RobotFileParser()
            regeln.parse(body.decode("utf-8", errors="replace").splitlines())
        else:
            # RFC 9309: 4xx allows everything, unreachable closes the host; 429 means "slow down", so closed
            regeln = 400 <= status < 500 and status != 429
        dauer = ROBOTS_TTL if status == 200 or regeln else ROBOTS_TTL_FEHLER
        self._robots[host] = (now + dauer, regeln)
        return regeln

    def erlaubt(self, url):
        regeln = self._regeln(urlsplit(url).hostname or "")
        if isinstance(regeln, bool):
            return regeln
        return regeln.can_fetch(BOT_NAME, url)

    # --- fetching ----------------------------------------------------------------------------

    def abrufen(self, url, *, accept="text/html"):
        """One fetch: https only, robots.txt obeyed on every hop, status checked, logged. Returns the body."""
        for _ in range(MAX_HOPS + 1):
            parts = urlsplit(url)
            if parts.scheme != "https" or not parts.hostname:
                raise QuelleError("Nur https-Adressen")
            if not self.erlaubt(url):
                raise QuelleError(f"robots.txt von {parts.hostname} erlaubt diesen Abruf nicht")
            status, body, ziel = self._netz(url, accept=accept, limit=MAX_BYTES)
            if self._log is not None:
                self._log.append("agent.action", {"host": parts.hostname, "status": status}, intent="recherche.abruf")
            if status not in REDIRECTS or not ziel:
                break
            url = urljoin(url, ziel)
        else:
            raise QuelleError(f"Mehr als {MAX_HOPS} Weiterleitungen, abgebrochen")
        if status == 429:
            raise QuelleError(f"{parts.hostname} bremst gerade (429), später noch einmal")
        if status != 200:
            raise QuelleError(f"{parts.hostname} antwortet mit {status}")
        return body

    def marginalia_suche(self, begriffe, anzahl=5):
        """Hits from Marginalia (public key); plain-http results are left out."""
        anzahl = max(1, min(int(anzahl), 20))
        body = self.abrufen(f"{MARGINALIA}{quote(begriffe, safe='')}?count={anzahl}", accept="application/json")
        try:
            daten = json.loads(body)
            lizenz = str(daten.get("license") or "CC-BY-NC-SA 4.0")
            treffer = [
                Fundstelle(
                    clean(str(r.get("title") or "")).strip(),
                    str(r["url"]),
                    clean(str(r.get("description") or "")).strip()[:500],
                    lizenz,
                    "Marginalia",
                )
                for r in daten.get("results", [])
                if str(r.get("url", "")).startswith("https://")
            ]
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            raise QuelleError("Antwort von Marginalia nicht lesbar") from error
        return treffer[:anzahl]

    def wikipedia_artikel(self, titel, *, sprache="de", zeichen=4000):
        """Text of one Wikipedia article from its normal page (the API is closed to bots by robots.txt)."""
        titel = (titel or "").strip()
        if not titel or _TITEL_VERBOTEN.search(titel) or not re.fullmatch(r"[a-z]{2,3}", sprache):
            raise QuelleError("Ungültiger Artikeltitel")
        url = f"https://{sprache}.wikipedia.org/wiki/{quote(titel.replace(' ', '_'), safe='_()')}"
        parser = _Absaetze()
        parser.feed(self.abrufen(url).decode("utf-8", errors="replace"))
        text = clean("\n\n".join(parser.absaetze))  # the parser already turned &amp; and the like into text
        if not text:
            raise QuelleError(f"Im Artikel „{titel}“ wurde kein Text gefunden")
        return Artikel(titel, url, text[:zeichen].rstrip(), LIZENZ_WIKIPEDIA, f"Wikipedia ({sprache})")
