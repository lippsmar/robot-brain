# brain – Code für Schlaubis Gehirn

Stand 15.10.2026. Der Code entsteht nach `docs/bauplan-gehirn-v1.md`, testgetrieben, mit Python 3.13 (wie Debian 13 auf dem Gehirn-Laptop).

## Bausteine

| Datei | Zweck | Bauplan |
|---|---|---|
| `eventlog.py` | Event-Log: eine JSONL-Datei pro Tag (UTC), fortlaufende Nummer, Hash-Kette gegen unbemerkte Änderungen, Anker (`head()`) gegen Kürzen und Neuschreiben, Prüfung gegen `schemas/event.schema.json`, Secrets werden abgewiesen, Dateien nur für Schlaubis Konto lesbar | Grenzen und Regeln: „Jede Aktion wird protokolliert“ |
| `budget.py` | Budget-Wächter: Kosten aus den Nutzungsdaten der API, Grenzen in Euro, Töpfe Gesamt, Recherche und Selbstoptimierung, Stufen Warnung, Sparmodus, Stopp. Stoppt vor dem Console-Limit, lässt Gesprächen immer das Minimum, weist Modelle ohne Preise ab | 7.3 |
| `memory.py` | Gedächtnis-Kern: SQLite (STRICT-Tabellen, nur anhängen, auch gegen `INSERT OR REPLACE` gesichert), Herkunft, `pii`, `teilbar`, Merk-Schutz, Archiv statt Löschen, Löschen nur mit Marvins Freigabe (Inhalt wird überschrieben), Volltextsuche nach Wörtern (ß/ss, ä/ae gleichwertig) und Wortteilen, Eingang für Einträge anderer Hosts | 10.2, 10.2a |
| `schema.py` | kleine Prüfung gegen JSON-Schema (nur die Schlüsselwörter, die unsere Schemas nutzen) | – |
| `secrets_guard.py` | erkennt Secrets in Daten, bevor sie gespeichert werden (Schlüsselnamen auch in camelCase, bekannte Key-Formate, HTTP-Auth). Zahlen wie GPIO-Pins bleiben erlaubt | Arbeitsregeln |
| `config/prices.toml` | Preise der Claude-API mit Quelle und Prüfdatum | 7.2 |
| `config/budget.toml` | Grenzen in Euro, Wechselkurs mit Datum, Schwellen | 7.1, 7.3 |

Vektorsuche (sqlite-vec, fastembed, LanceDB), Fristen-Lauf, Themenseiten und Quellen-Bewertung folgen in eigenen Schritten (Bauplan 10.1, 10.3 bis 10.6).

## Tests

```sh
python3 -m venv .venv
.venv/bin/pip install --require-hashes -r brain/requirements-dev.txt
.venv/bin/python -m pytest                      # alle Tests
.venv/bin/ruff check brain                      # Code-Prüfung
.venv/bin/mypy                                  # Typprüfung
.venv/bin/python -m coverage run -m pytest && .venv/bin/python -m coverage report
.venv/bin/python tools/dev/mutation_check.py    # erkennen die Tests eingebaute Fehler?
# danach in Claude Code: /code-review brain/ high
```

Stand 15.10.2026: 166 Tests grün, Abdeckung 97 %, mypy ohne Befund, alle 35 eingebauten Fehler werden erkannt. Danach lief die eingebaute Code-Prüfung von Claude Code (`/code-review`); ihre 14 berechtigten Befunde sind behoben und mit Tests abgesichert.

## Regeln für den Code
- Erst der Test, dann der Code. Fertig ist etwas erst, wenn ein frischer Testlauf es belegt.
- Für jede wichtige Regel einen eingebauten Fehler in `brain/tests/mutations.json` ergänzen. Überlebt er, fehlt ein Test.
- Laufzeitdaten (Event-Log, Datenbank) liegen nie im Repo. Pfade kommen aus der Config.
- Keine Secrets in Code, Tests, Logs oder Gedächtnis. Nur Referenzen auf den Secret-Store.
- Fremde Pakete nur nach Prüfung (`skills/INDEX.md`), mit fester Version, mindestens 14 Tage alt, Installation nur mit Prüfsummen (`--require-hashes`).
- Bezeichner und Kommentare im Code auf Englisch, Doku für Marvin auf Deutsch.
