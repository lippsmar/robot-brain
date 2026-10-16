"""Schlaubi's live profile: changes in conversation and development on its own.

Bauplan Charakter, Phase 10 and 11. The live profile is runtime data and lives in its own git
repository in Schlaubi's data folder, never in the code repository (see brain/README.md). It
starts as a copy of the start profile `profil.yaml`.

Phase 10 – Marvin changes a slider or undoes the last change:
- Only Marvin: proposals come from his verified Telegram chat (`telegram`) or his voice at the
  cube (`sprache`). Websites, mails and other people change nothing.
- Schlaubi repeats the change in one sentence; it is only taken after Marvin's yes in his
  Telegram chat (`bestaetigen` with the chat and message id), also for spoken changes, because
  a voice at the cube is not reliably Marvin. Boundary: only the Telegram adapter calls
  `bestaetigen`, after checking the sender; it is never offered to the model as a tool.
- The fixed core cannot be changed here, only in `kern.md` by Marvin with Claude Code.
- Every change is a git commit with its reason and can be undone step by step.

Phase 11 – development on its own: only movable sliders, one step at a time, inside their
range, only from conversations with Marvin. Tempo (Marvin, 16.10.2026), numbers in the profile:
- in conversation (`gespraech`): at most `max_pro_tag` steps per local day and
  `max_pro_regler_und_woche` steps per slider and calendar week,
- the weekly run (`wochenlauf`) has its own, separate influence: `max_pro_woche` steps per week,
  which do not use up the conversation steps.
Undone steps still count. If the weekly self-test fails, the newest development is taken back and
Marvin is alerted.

Annahmen 16.10.2026: a proposal expires after 10 minutes; if Marvin sets a value outside the
development range, the range is widened to include it (his word counts more than the range).
"""

import contextlib
import fcntl
import os
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from brain.character._git import GitError, find_git, run_git
from brain.character.profile import CORE_PATTERNS, PROFILE_FILE, ProfileError, parse_profile

FILE_NAME = "profil.yaml"
GUELTIG = timedelta(minutes=10)
SELBSTTEST_ABSTAND = timedelta(days=7)  # the core self-test runs weekly (Bauplan Charakter 11.2)
QUELLEN_MARVIN = ("telegram", "sprache")
ENTWICKLUNG_QUELLEN = {"gespraech": "Gespräch", "wochenlauf": "Wochenlauf"}
KERN_HINWEIS = (
    "Der feste Kern lässt sich nicht im Gespräch ändern,"
    " nur in der Datei brain/character/kern.md (Marvin mit Claude Code)."
)
NAMEN = {
    "direktheit": "Direktheit",
    "humor_haeufigkeit": "Humor-Häufigkeit",
    "humor_trockenheit": "Trockenheit des Humors",
    "selbstbewusstsein": "Selbstbewusstsein",
    "smalltalk_toleranz": "Smalltalk-Toleranz",
}
_START_SUBJECT = "Startprofil"
_KURZ = "kurz: "
_REVERT = "revert: "
_ENTWICKLUNG = "Entwicklung ("
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


class ProfilError(Exception):
    """A change was refused or cannot be applied."""


@dataclass(frozen=True)
class Aenderung:
    id: str
    art: str  # "regler" or "rueckgaengig"
    satz: str
    quelle: str
    grund: str
    bis: datetime
    regler: str = ""
    alt: int = 0
    neu: int = 0
    min: int = 0
    max: int = 0
    ziel: str = ""  # commit to undo


@dataclass(frozen=True)
class Eintrag:
    datum: datetime
    text: str


@dataclass(frozen=True)
class _Commit:
    sha: str
    datum: datetime
    subject: str
    kurz: str
    revert: str | None


def _utc_now():
    return datetime.now(UTC)


def _name(regler):
    return NAMEN.get(regler, regler)


def _slider_line(regler):
    return re.compile(rf"^(  {re.escape(regler)}: \{{wert: )(-?\d+)(, min: )(-?\d+)(, max: )(-?\d+)(\}})", re.MULTILINE)


def _check_text(value, label, limit=200):
    """One line of text: no line breaks or control characters, which could fake commit metadata."""
    if not isinstance(value, str) or not value.strip() or len(value) > limit or _CONTROL.search(value):
        raise ProfilError(f"{label} muss eine Zeile Text mit 1 bis {limit} Zeichen sein")


class LiveProfil:
    def __init__(
        self, folder, log=None, *, marvin_chat, clock=_utc_now, start=PROFILE_FILE, git="git", timezone="Europe/Berlin"
    ):
        self._folder = Path(folder)
        self._file = self._folder / FILE_NAME
        self._log = log
        self._marvin_chat = marvin_chat
        self._clock = clock
        self._zone = ZoneInfo(timezone)
        try:
            self._git = find_git(git)
        except GitError as error:
            raise ProfilError(str(error)) from error
        self._pending: dict[str, Aenderung] = {}
        if (self._folder / ".git").exists():
            head = run_git(self._folder, "rev-parse", "--verify", "--quiet", "HEAD", git=self._git, check=False)
            if not self._file.is_file() or head.returncode != 0:
                raise ProfilError("Laufzeit-Profil unvollständig (Datei oder Verlauf fehlt), bitte prüfen")
            return
        if self._file.exists():
            raise ProfilError("Laufzeit-Profil ohne Versionsverlauf gefunden, es wird nicht überschrieben")
        text = Path(start).read_text(encoding="utf-8")
        parse_profile(text)
        self._folder.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self._folder, 0o700)  # only Schlaubi's account, also if the folder existed
        self._git_run("init", "--quiet")
        self._file.write_text(text, encoding="utf-8")
        self._commit(_START_SUBJECT, _START_SUBJECT)

    # --- git ----------------------------------------------------------------------------

    def _git_run(self, *args):
        when = self._clock().isoformat()
        identity = {
            "GIT_AUTHOR_NAME": "Schlaubi",
            "GIT_AUTHOR_EMAIL": "schlaubi@localhost",
            "GIT_COMMITTER_NAME": "Schlaubi",
            "GIT_COMMITTER_EMAIL": "schlaubi@localhost",
            "GIT_AUTHOR_DATE": when,
            "GIT_COMMITTER_DATE": when,
        }
        try:
            return run_git(self._folder, *args, git=self._git, extra_env=identity).stdout
        except GitError as error:
            raise ProfilError(str(error)) from error

    def _commit(self, subject, kurz, revert=None):
        message = f"{subject}\n\n{_KURZ}{kurz}"
        if revert:
            message += f"\n{_REVERT}{revert}"
        self._git_run("add", FILE_NAME)
        self._git_run("commit", "--quiet", "-m", message)

    def _reset(self):
        """Back to the last commit after a failed change: no half-written profile stays live."""
        with contextlib.suppress(ProfilError):  # the original error is the one to report
            self._git_run("reset", "--quiet", "--hard", "HEAD")

    @contextlib.contextmanager
    def _locked(self):
        """One writer at a time (conversation, weekly run, Telegram), also across processes."""
        with open(self._folder / ".git" / "schlaubi.lock", "a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def _history(self):
        """Commits newest first."""
        out = self._git_run("log", "--format=%H%x1f%aI%x1f%s%x1f%b%x1e")
        result = []
        for record in out.split("\x1e"):
            if not record.strip():
                continue
            sha, date, subject, body = record.strip("\n").split("\x1f")
            kurz, revert = subject, None
            for line in body.splitlines():
                if line.startswith(_KURZ):
                    kurz = line[len(_KURZ) :]
                elif line.startswith(_REVERT):
                    revert = line[len(_REVERT) :]
            result.append(_Commit(sha, datetime.fromisoformat(date), subject, kurz, revert))
        return result

    @staticmethod
    def _effective(history):
        """Changes that are not the start, not an undo and not undone yet, newest first."""
        reverted = {commit.revert for commit in history if commit.revert}
        return [c for c in history if c.subject != _START_SUBJECT and not c.revert and c.sha not in reverted]

    def _apply(self, write, subject, kurz, revert=None):
        """Change the file and commit; on any failure go back to the last commit."""
        try:
            write()
            parse_profile(self._file.read_text(encoding="utf-8"))
            self._commit(subject, kurz, revert)
        except (ProfilError, ProfileError, OSError) as error:
            self._reset()
            if isinstance(error, ProfilError):
                raise
            raise ProfilError(f"Änderung nicht übernommen: {error}") from error

    def _revert(self, commit, subject, kurz):
        self._apply(lambda: self._git_run("revert", "--no-commit", commit.sha), subject, kurz, revert=commit.sha)

    def _event(self, type, payload, intent, result):
        if self._log is not None:
            self._log.append(type, payload, intent=intent, result=result)

    # --- reading ------------------------------------------------------------------------

    def profil(self):
        """The current live profile, checked like the start profile."""
        return parse_profile(self._file.read_text(encoding="utf-8"))

    def uebersicht(self):
        """Answer to "Zeig mir dein Profil" (sent by Telegram)."""
        profile = self.profil()
        lines = [f"Mein Profil (Grundton {profile['grundton']}):"]
        for name, slider in profile["regler"].items():
            lines.append(f"- {_name(name)}: {slider['wert']} (Spielraum {slider['min']}–{slider['max']})")
        return "\n".join(lines)

    def veraenderungen(self, seit=None):
        """Answer to "Was hat sich an dir verändert?": changes with date and reason, oldest first."""
        entries = [Eintrag(c.datum, c.subject) for c in reversed(self._history())]
        return [entry for entry in entries if seit is None or entry.datum >= seit]

    # --- Phase 10: Marvin's changes, always with his yes on Telegram ----------------------

    def _check_source(self, quelle, payload):
        if quelle not in QUELLEN_MARVIN:
            self._event("agent.decision", {**payload, "quelle": str(quelle)[:40]}, "profile.refused", "abgelehnt")
            raise ProfilError(
                "Nur Marvin ändert das Profil, per Telegram oder per Sprache mit Bestätigung auf dem Handy."
            )

    def _propose(self, change):
        self._pending[change.id] = change
        return change

    def vorschlagen(self, regler, *, wert=None, schritt=None, grund, quelle):
        """Proposal for a slider change; Schlaubi says `satz` and waits for Marvin's yes."""
        self._check_source(quelle, {"regler": str(regler)[:40]})
        _check_text(grund, "Grund")
        if not isinstance(regler, str) or any(pattern.search(regler.replace("_", " ")) for pattern in CORE_PATTERNS):
            raise ProfilError(KERN_HINWEIS)
        sliders = self.profil()["regler"]
        if regler not in sliders:
            raise ProfilError(f"Regler {regler!r} unbekannt. Es gibt: {', '.join(sliders)}")
        current = sliders[regler]
        if (wert is None) == (schritt is None):
            raise ProfilError("Entweder einen Wert oder einen Schritt angeben")
        if schritt is not None:
            if isinstance(schritt, bool) or not isinstance(schritt, int) or schritt == 0:
                raise ProfilError("Der Schritt muss eine ganze Zahl ungleich 0 sein")
            wert = current["wert"] + schritt
        if isinstance(wert, bool) or not isinstance(wert, int) or not 0 <= wert <= 10:
            raise ProfilError("Regler gehen von 0 bis 10")
        if wert == current["wert"]:
            raise ProfilError(f"{_name(regler)} steht schon auf {wert}")
        low, high = min(current["min"], wert), max(current["max"], wert)
        satz = f"{_name(regler)} von {current['wert']} auf {wert}"
        if wert > current["max"]:
            satz += f", Spielraum dafür bis {wert}"
        elif wert < current["min"]:
            satz += f", Spielraum dafür ab {wert}"
        return self._propose(
            Aenderung(
                secrets.token_hex(4),
                "regler",
                f"{satz}. Passt das?",
                quelle,
                grund,
                self._clock() + GUELTIG,
                regler,
                current["wert"],
                wert,
                low,
                high,
            )
        )

    def rueckgaengig_vorschlagen(self, *, quelle):
        """ "Mach die letzte Änderung rückgängig": also only after Marvin's yes on Telegram."""
        self._check_source(quelle, {"aenderung": "rückgängig"})
        effective = self._effective(self._history())
        if not effective:
            raise ProfilError("Nichts zum Rückgängigmachen, das Profil ist im Startzustand")
        target = effective[0]
        return self._propose(
            Aenderung(
                secrets.token_hex(4),
                "rueckgaengig",
                f"Rückgängig: {target.kurz}. Passt das?",
                quelle,
                "Marvin: letzte Änderung rückgängig",
                self._clock() + GUELTIG,
                ziel=target.sha,
            )
        )

    def ablehnen(self, change_id):
        self._pending.pop(change_id, None)

    def bestaetigen(self, change_id, *, chat_id, message_id):
        """Marvin's yes from his Telegram chat (sender checked by the adapter). Returns what was done."""
        change = self._pending.get(change_id)
        if change is None:
            raise ProfilError("Änderung unbekannt oder schon erledigt")
        if chat_id != self._marvin_chat or isinstance(message_id, bool) or not isinstance(message_id, int):
            raise ProfilError("Änderungen gelten erst nach Marvins Ja in seinem Telegram-Chat")
        del self._pending[change_id]
        if self._clock() > change.bis:
            raise ProfilError("Die Änderung ist abgelaufen, bitte noch einmal sagen")
        with self._locked():
            if change.art == "rueckgaengig":
                return self._undo(change, message_id)
            kurz = f"{_name(change.regler)} von {change.alt} auf {change.neu}"
            self._apply(
                lambda: self._write(change.regler, change.alt, change.neu, change.min, change.max),
                f"{kurz}: {change.grund} (per {change.quelle}, bestätigt per Telegram)",
                kurz,
            )
        payload = {"regler": change.regler, "alt": change.alt, "neu": change.neu, "quelle": change.quelle}
        self._event("agent.action", {**payload, "telegram": message_id}, "profile.changed", "übernommen")
        return kurz

    def _undo(self, change, message_id):
        effective = self._effective(self._history())
        if not effective or effective[0].sha != change.ziel:
            raise ProfilError("Das Profil hat sich inzwischen geändert, bitte neu sagen, was rückgängig soll")
        target = effective[0]
        kurz = f"Rückgängig: {target.kurz}"
        self._revert(target, f"{kurz} (per {change.quelle}, bestätigt per Telegram)", kurz)
        payload = {"aenderung": target.kurz, "quelle": change.quelle, "telegram": message_id}
        self._event("agent.action", payload, "profile.undone", "rückgängig")
        return kurz

    def _write(self, regler, alt, neu, low, high):
        text = self._file.read_text(encoding="utf-8")
        line = _slider_line(regler)
        match = line.search(text)
        if match is None:
            raise ProfilError(f"Regler {regler!r} steht nicht im erwarteten Format im Profil")
        if int(match.group(2)) != alt:
            raise ProfilError(f"{_name(regler)} hat sich inzwischen geändert, bitte neu vorschlagen")
        new_text = line.sub(
            lambda m: f"{m.group(1)}{neu}{m.group(3)}{low}{m.group(5)}{high}{m.group(7)}", text, count=1
        )
        parse_profile(new_text)
        self._file.write_text(new_text, encoding="utf-8")

    # --- Phase 11: development on its own -------------------------------------------------

    def entwickeln(self, regler, richtung, *, grund, quelle):
        """One step of a movable slider, from a conversation or the weekly run, within the tempo limits.

        Boundary: only the evaluation of Marvin's own conversations calls this (after each conversation
        with him, and the weekly run). It is never offered to the model as a tool, and content from
        websites, mails or other people never reaches it.
        """
        if quelle not in ENTWICKLUNG_QUELLEN:
            raise ProfilError("Der Charakter entwickelt sich nur aus Gesprächen mit Marvin (Gespräch oder Wochenlauf)")
        if isinstance(richtung, bool) or richtung not in (1, -1):
            raise ProfilError("Entwicklung geht immer genau einen Schritt (+1 oder -1)")
        _check_text(grund, "Grund")
        prefix = f"{_ENTWICKLUNG}{ENTWICKLUNG_QUELLEN[quelle]}): "
        with self._locked():
            profile = self.profil()
            development = profile["entwicklung"]
            if not development.get("von_selbst") or regler not in development["bewegliche_regler"]:
                raise ProfilError(f"{_name(regler)} ist kein beweglicher Regler")
            self._check_tempo(quelle, prefix, _name(regler), development)
            current = profile["regler"][regler]
            neu = current["wert"] + richtung
            if not current["min"] <= neu <= current["max"]:
                raise ProfilError(f"{_name(regler)} bleibt im Spielraum {current['min']}–{current['max']}")
            kurz = f"{prefix}{_name(regler)} von {current['wert']} auf {neu}"
            self._apply(
                lambda: self._write(regler, current["wert"], neu, current["min"], current["max"]),
                f"{kurz}: {grund}",
                kurz,
            )
        payload = {"regler": regler, "alt": current["wert"], "neu": neu, "quelle": quelle}
        self._event("agent.action", payload, "profile.developed", "entwickelt")
        return kurz

    def _check_tempo(self, quelle, prefix, name, development):
        """Count this source's steps (undone ones too) by local day and calendar week."""
        now = self._clock().astimezone(self._zone)
        week = now.isocalendar()[:2]
        steps = [(c.kurz, c.datum.astimezone(self._zone)) for c in self._history() if c.kurz.startswith(prefix)]
        this_week = [(kurz, day) for kurz, day in steps if day.isocalendar()[:2] == week]
        if quelle == "wochenlauf":
            if len(this_week) >= development["wochenlauf"]["max_pro_woche"]:
                raise ProfilError("Der Wochenlauf hat den Charakter diese Woche schon verändert")
            return
        limits = development["gespraech"]
        if sum(1 for _, day in steps if day.date() == now.date()) >= limits["max_pro_tag"]:
            raise ProfilError("Im Gespräch hat sich der Charakter heute schon verändert")
        same_slider = sum(1 for kurz, _ in this_week if kurz.startswith(f"{prefix}{name} von"))
        if same_slider >= limits["max_pro_regler_und_woche"]:
            raise ProfilError(f"{name} hat sich diese Woche im Gespräch schon {same_slider} Mal verändert")

    def entwicklung_zuruecknehmen(self, *, grund):
        """After a failed core self-test (11.2): take back every development since the last weekly test.

        That is all development steps of the last 7 days still in effect, newest first. Marvin is
        always alerted, also when nothing could be taken back or a step conflicts with his own
        later change (his change stays, he decides).
        """
        _check_text(grund, "Grund")
        done = []
        with self._locked():
            try:
                since = self._clock() - SELBSTTEST_ABSTAND
                targets = [
                    c for c in self._effective(self._history()) if c.kurz.startswith(_ENTWICKLUNG) and c.datum > since
                ]
                if not targets:
                    raise ProfilError("Es gibt keine Entwicklung zum Zurücknehmen")
                for commit in targets:
                    self._revert(commit, f"Zurückgenommen: {commit.kurz} ({grund})", f"Zurückgenommen: {commit.kurz}")
                    done.append(commit.kurz)
            except ProfilError as error:
                payload = {"grund": grund, "zurueckgenommen": done}
                self._event("safety.alert", payload, "profile.development_undo_failed", str(error)[:200])
                raise
        text = f"Zurückgenommen: {'; '.join(done)} ({grund})"
        self._event("safety.alert", {"aenderungen": done, "grund": grund}, "profile.development_undone", text)
        return text
