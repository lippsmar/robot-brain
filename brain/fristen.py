"""Deadline run with keep protection (Bauplan Gehirn 10.5, Design Gehirn 7).

Deadlines from the design (13.10.2026), counted from when an entry was stored:
conversation texts 1 year, other people's mails 30 days, raw research pages 90 days.
Audio and camera images are never stored in memory; the event log has its own rules
(hash chain, anchors) and is not touched here.

Before anything may go, every entry past its deadline is sorted:
- "bleibt": Marvin said "merken" (keep), or the importance check says it matters,
- "wartet": a conversation not yet condensed into knowledge ("Gesprächstexte: 1 Jahr, danach
  verdichtet"). It counts as taken over when a summary of this host (kind "zusammenfassung",
  source "konsolidierung") carries the tag `aus:<uid>`. Foreign mails and raw pages need no
  takeover: their deadline is about keeping little data on others; what mattered from a page
  went into statements and sections when it was read (assumption, to be confirmed by Marvin),
- "soll_bleiben": the importance check is unsure (e.g. disputed) – the list
  "Soll das bleiben?" for Marvin,
- "loeschbar": everything else.

Nothing is deleted by the run itself. Physical deletion needs Marvin's yes (`approved_by`
"marvin", Memory.delete). `loeschen` checks every entry again right before deleting it and
only takes "loeschbar" ones; entries from "Soll das bleiben?" only with `auch_unsichere=True`,
meaning Marvin decided on them one by one. Protected, important or not yet condensed ones never.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from brain.eventlog import format_ts
from brain.memory import MemoryStoreError

FRISTEN = {"gespraech": 365, "mail": 30, "rohseite": 90}  # kind -> days
VERDICHTEN = ("gespraech",)  # kinds that must be taken over into knowledge before they may go
ZUSAMMENFASSUNG = {"kind": "zusammenfassung", "source": "konsolidierung"}
FREIGEBER = ("marvin",)


class FristenError(Exception):
    """A deletion without Marvin's approval, or uids given in a wrong form."""


@dataclass(frozen=True)
class Fristfall:
    uid: str
    art: str
    ts: str
    grund: str


@dataclass
class Fristbericht:
    loeschbar: list = field(default_factory=list)
    soll_bleiben: list = field(default_factory=list)
    bleibt: list = field(default_factory=list)
    wartet: list = field(default_factory=list)

    def alle(self):
        return self.loeschbar + self.soll_bleiben + self.bleibt + self.wartet


def _utc_now():
    return datetime.now(UTC)


def wichtigkeit(hit):
    """Default importance check: confirmed entries matter, disputed ones are unsure, the rest not."""
    if hit.status == "confirmed":
        return "ja"
    if hit.status == "disputed":
        return "unsicher"
    return "nein"


class Fristen:
    def __init__(self, memory, *, log=None, clock=_utc_now, wichtig=wichtigkeit, fristen=None):
        self._memory = memory
        self._log = log
        self._clock = clock
        self._wichtig = wichtig
        self._fristen = dict(FRISTEN if fristen is None else fristen)

    def _uebernommen(self):
        return self._memory.tag_targets("aus:", **ZUSAMMENFASSUNG)

    def _einordnen(self, hit, uebernommen):
        """(list name, reason) for an entry past its deadline."""
        if hit.keep:
            return "bleibt", "merken"
        urteil = self._wichtig(hit)
        if urteil == "ja":
            return "bleibt", "wichtig"
        if hit.kind in VERDICHTEN and hit.uid not in uebernommen:
            return "wartet", "noch nicht ins Wissen übernommen"
        if urteil == "nein":
            return "loeschbar", f"Frist {self._fristen[hit.kind]} Tage abgelaufen"
        return "soll_bleiben", "unsicher"  # unsure, or an answer the check should not give: in doubt it stays

    def _faellig(self, hit, now):
        tage = self._fristen.get(hit.kind)
        return tage is not None and hit.ts < format_ts(now - timedelta(days=tage))

    def _bericht(self):
        now = self._clock()
        uebernommen = self._uebernommen()
        bericht = Fristbericht()
        for art, tage in self._fristen.items():
            for hit in self._memory.older_than(art, format_ts(now - timedelta(days=tage))):
                liste, grund = self._einordnen(hit, uebernommen)
                getattr(bericht, liste).append(Fristfall(hit.uid, hit.kind, hit.ts, grund))
        return bericht

    def pruefen(self):
        """Sort every entry past its deadline (see module docstring). Deletes nothing."""
        bericht = self._bericht()
        if self._log is not None:
            self._log.append(
                "agent.action",
                {name: len(getattr(bericht, name)) for name in ("loeschbar", "soll_bleiben", "bleibt", "wartet")},
                intent="fristen.pruefen",
            )
        return bericht

    def loeschen(self, uids, *, approved_by, auch_unsichere=False):
        """Delete the given entries after Marvin's yes, if they may still go. Returns the deleted uids."""
        if approved_by not in FREIGEBER:
            raise FristenError("Löschen nach Frist nur mit Marvins Ja (approved_by='marvin')")
        if isinstance(uids, str):
            raise FristenError("uids als Liste übergeben, nicht als einzelnen Text")
        uids = list(dict.fromkeys(uids))
        erlaubt = ("loeschbar", "soll_bleiben") if auch_unsichere else ("loeschbar",)
        geloescht, fehler = [], 0
        for uid in uids:
            hit = self._memory.get(uid)
            # checked again right before deleting: an earlier deletion in this batch may have changed things
            if hit is None or not self._faellig(hit, self._clock()):
                continue
            liste, grund = self._einordnen(hit, self._uebernommen())
            if liste not in erlaubt:
                continue
            try:
                self._memory.delete(uid, reason=f"Frist: {grund}", approved_by=approved_by, compact=False)
            except MemoryStoreError:
                fehler += 1  # e.g. marked keep in the meantime; the others still count
                continue
            geloescht.append(uid)
        if geloescht:
            self._memory.compact()
        if self._log is not None:
            self._log.append(
                "agent.action",
                {"angefragt": len(uids), "geloescht": len(geloescht), "fehler": fehler},
                intent="fristen.loeschen",
            )
        return geloescht
