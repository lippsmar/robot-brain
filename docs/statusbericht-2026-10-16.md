# Statusbericht und Qualitätskontrolle Schlaubi – 16.10.2026

Stand: Commit nach b53f788, geprüft am 16.10.2026 (vier Projekttage seit 13.10.2026). Spiegel: Notion „Statusbericht 16.10.2026“.

## Kurzfassung
- **Software fürs Gehirn:** Die Bausteine sind fertig und streng geprüft. Es sind 846 Tests, alle grün, und 354 absichtlich eingebaute Fehler, alle erkannt. Keine Secrets, alle Pakete fest und mit Prüfsummen.
- **Was fehlt:** der Zusammenbau. Die Bausteine laufen nur in Tests, es gibt noch kein Programm, das Schlaubi startet. Dafür braucht es den Laptop, den API-Key und den Würfel.
- **Hardware:** Es ist noch nichts gekauft oder aufgebaut. Der Engpass ist der Laptop-Steckbrief (Marvin).
- **Größtes Risiko:** Das Repo ist öffentlich. Es enthält das Sicherheitskonzept und die Logik für Marvins Gewohnheiten.

## Stand nach Bereich
| Bereich | Design | Bauplan | Umsetzung |
|---|---|---|---|
| Körper (Würfel) | freigegeben 13.10. | bestätigt 13.10. | Nichts gebaut, Teile Stufe 1 nicht bestellt. Testweg mit dem Handy als Würfel ist geplant |
| Gehirn | freigegeben 13.10. | bestätigt 13.10. | Software-Bausteine fertig: Event-Log, Budget-Wächter (7), Gedächtnis-Kern (10), Bilder ohne Metadaten (11.2). Phasen 0–6, 8, 9, 12, 14–16 brauchen den Laptop |
| Charakter | freigegeben 14.10. | bestätigt 14.10. | Phasen 1–5, 10, 11 fertig. Die Zahlen der Regler warten auf Marvins Bestätigung |
| Datensammlung | freigegeben 14.10. | bestätigt 14.10. | Teile auf dem Gehirn fertig (Data Lake, Kühlung, Zustand, Muster), mit Testdaten. Teile auf dem Würfel fehlen |
| Code-Skills | freigegeben 15.10. | bestätigt 15.10. | Nicht begonnen, die Sandbox läuft auf dem Laptop |
| Data Lakehouse | freigegeben 16.10. | bestätigt 16.10. | Phase 1 fertig. Phase 2 (Vektoren) folgt nach der Prüfung von sqlite-vec und fastembed |
| Wissensarchitektur | freigegeben 16.10. | bestätigt 16.10. | Stufe 1 fertig |
| Recherche | – | Gehirn 13 | Such-API offen (Staan wartet auf Freischaltung). Kostenlose Quellen laufen: Wikipedia-Artikel und Marginalia |
| Prototyp A (Chat-Seite) | – | – | Gebaut, der Test durch Marvin steht aus |

## Messwerte
- **Prüflauf:** 846 Tests grün, ruff und mypy ohne Befund. Alle 354 eingebauten Fehler werden erkannt.
- **Umfang:** etwa 6.000 Zeilen Code unter `brain/` (ohne Tests), 24 Testdateien, 27 Dokumente, 16 Skills, 132 Commits.
- **Secrets:** Weder der Arbeitsstand noch die Git-Historie enthalten echte Schlüssel. Treffer sind nur Test-Attrappen wie `sk-ant-api03-abcdefghijklmnop`.
- **Pakete:** Alle drei requirements-Dateien sind fest gepinnt, jedes Paket hat Prüfsummen.
- **Skill-Zips** (fachliteratur, roboter-projekt, social-media-ansehen) entsprechen dem Stand im Repo.
- **Schutz-Hook für den festen Kern:** Er fragt bei Edit, Write und `sed` auf `kern.md` nach und lässt andere Dateien durch (von Hand geprüft).
- **Lessons Learned:** 43, mit Mechanismen in `docs/claude-optimierung.md`.

## Befunde
**Behoben bei dieser Prüfung**
1. **Fünf Notion-Titel zeigten einen alten Stand.** Betroffen waren Design Körper, Bauplan Körper, Design Charakter, Design Lakehouse und Design Wissen („in Klärung“ oder „Entwurf“, obwohl längst freigegeben). Die Titel sind korrigiert.
2. **Ortsangaben im öffentlichen Repo:** Ein Testdatensatz und ein Satz im Wissens-Design nannten Marvins Land. Beides ist neutral formuliert. In der Git-Historie stehen die Angaben noch, das löst nur ein privates Repo.
3. **Die Sicherheitsempfehlungen standen nur im Projektlog** (Repo privat stellen, Keys aus den Alt-Repos drehen). Sie sind jetzt ein offener Punkt in CLAUDE.md.
4. **`.gitignore` hatte Lücken:** `memory/journal`, `memory/working`, `memory/knowledge` und `data/datasets` waren nicht ausgeschlossen. Sie sind ergänzt, damit dort nie Laufzeitdaten ins Repo geraten.

**Offen, mit Vorschlag**
5. **Hoch – das Repo ist öffentlich.** Entscheidung und Umsetzung liegen bei Marvin (GitHub, Settings, Change visibility). Danach funktionieren die Download-Links der Skill-Zips nur noch angemeldet.
6. **Mittel – `memory/SYSTEM_PROMPT.md` ist veraltet.** Die Datei vom 13.10. legt Arbeitsgedächtnis, Journal und Rohdaten in Ordner im Repo. Das widerspricht „Laufzeitdaten nie im Repo“ und dem gebauten Code, der in SQLite außerhalb des Repos schreibt. CLAUDE.md verweist auf die Datei. Vorschlag: auf den gebauten Stand bringen (Notion „Memory Core“ mit), nach Marvins Ja.
7. **Mittel – die Bausteine sind nicht verbunden.** Es gibt kein Startprogramm und keinen Test über mehrere Bausteine hinweg (Gespräch, Laune, Gedächtnis, Budget, Log). Vorschlag: einen Zusammenbau-Test ohne Hardware vorziehen, mit Testdaten und ohne API-Key.
8. **Niedrig – einige Werkzeuge haben keine automatischen Tests:** die beiden Hooks, `export_prompt.py` und `mutation_check.py`. Vorschlag: kleine Tests für die Hooks, weil sie Regeln durchsetzen.
9. **Niedrig – sieben Craft-Skills fehlen in `dist/skills/`.** Sie stehen in `skills/INDEX.md` als „neue Fassung hochzuladen“, haben aber keine Zip. Vorschlag: Zips packen, wenn Marvin sie hochladen will.
10. **Niedrig – die Grundregel auf der Notion-Seite „Robot Brain“ ist überholt.** Sie nennt `memory/decisions/` als Ort für ADRs. Tatsächlich stehen sie in der ADR-Tabelle in Notion, im Repo liegt nur 0001. Vorschlag: die Regel anpassen.
11. **Niedrig – Marginalia beantwortet keine Suchen mit mehreren Wörtern.** Das liegt am Dienst. Vorschlag: einzelne Begriffe nacheinander abfragen oder die Such-API abwarten.

## Wartet auf Marvin (Reihenfolge nach Wirkung)
1. Repo auf privat stellen, Keys aus den Alt-Repos drehen (Spotify-Token, Google-Cloud-Projekt).
2. Laptop-Steckbrief: Modell, RAM, freier Platz (mindestens 100 GB), Akku, Betriebssystem, AVX2. Davon hängen die meisten Gehirn-Phasen ab.
3. Gehirn Phase 0: Bestandsaufnahme und Sicherung.
4. Prototyp A testen.
5. Die Zahlen der Charakter-Regler bestätigen.
6. Regel-Entscheidung: Darf Schlaubi die Wikipedia- und Wikidata-Schnittstelle trotz robots.txt nutzen?
7. Teile Stufe 1, SIM-Anbieter und mail.de-Konto.
8. Skill `fachliteratur` in Claude hochladen.

## Nachtrag 16.10.2026 (Marvin: „Ja, mach alles“)
- **Befund 6 erledigt:** `memory/SYSTEM_PROMPT.md` und die Notion-Seite „Memory Core“ zeigen den gebauten Stand: Laufzeitdaten im Datenordner, Ebenen L1–L5 mit Lakehouse-Stufen. `.gitignore` sperrt jetzt den ganzen Inhalt von `data/` und `logs/`.
- **Befund 7 erledigt:** Der Gesprächsablauf (`brain/gespraech.py`, Bauplan Gehirn 11.3, Textteil) verbindet die Bausteine. Ein Test über alle Bausteine läuft ohne API-Key.
- **Befund 8 erledigt:** Die beiden Hooks haben automatische Tests und eingebaute Fehler. Der Kern-Schutz prüft relative Pfade jetzt vom Sitzungsordner aus.
- **Befund 9 erledigt:** Die Zips der sieben Craft-Skills liegen in `dist/skills/`.
- **Befund 10 erledigt:** Die Grundregel auf „Robot Brain“ nennt die ADR-Tabelle in Notion.
- **Befund 11 bleibt:** Marginalia beantwortet Suchen mit mehreren Wörtern mal, mal nicht (beim Nachtest ging „barometer air pressure“, „luftdruck sensor“ lief in die Zeitgrenze). Das liegt am Dienst, Lösung ist die Such-API.
- **Befund 5 bleibt bei Marvin:** Repo privat stellen.
- **Prüfung danach:** 883 Tests grün, alle 382 eingebauten Fehler erkannt. Die Code-Prüfung fand 10 Befunde, alle sind behoben.
