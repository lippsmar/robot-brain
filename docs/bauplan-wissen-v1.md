# Bauplan Wissensarchitektur – Version 1

Stand 16.10.2026. Design: `docs/design-wissen.md` (freigegeben 16.10.2026). Marvins „Ja“ galt dem Design und dem Start von Stufe 1. Die Stufen 2 bis 5 hängen an Paketprüfungen und am Laptop, sie werden vor dem Bau noch einmal kurz bestätigt.

## Kopf
- **Ziel:** Schlaubi nimmt Wissen aus allen Quellen auf und gibt es belegt, aktuell und schnell wieder.
- **Architektur:** sechs Schichten (Quelle, Abschnitt, Aussage, Begriff, Thema, Überblick). Jede zeigt auf ihre Herkunft. Große Bestände liegen als eigene Shards.
- **Technik:** Python 3.13 unter `brain/`, SQLite (STRICT, nur anhängen), Abschnitte im Gedächtnis-Kern, Pakete in `brain/wissen.py`.
- **Vorgaben:** erst Test, dann Code. Ein Commit und ein Notion-Eintrag pro Paket, Abschluss mit Skill `paket-abschluss`. Netz nur mit Bot-Kennung, robots.txt und offiziellen Schnittstellen. `pii` an jedem Datensatz.

## Stufe 1 – ohne neue Pakete
**1.1 Aussagen** (`brain/aussagen.py`): eine Aussage als Subjekt, Beziehung und Objekt mit Text, dazu Belege (Abschnitt-uid oder Quelle), Quellen-Stufe A–D, Vertrauen, gültig seit/bis, erfasst, Status unbestätigt/bestätigt/umstritten/ersetzt, `pii`.
- Test: Dieselbe Aussage aus zwei Quellen gibt eine Aussage mit zwei Belegen. Ein Widerspruch macht beide „umstritten“. Ersetzen behält die alte Aussage. Gültigkeit filtert nach Datum. Vertrauen steigt mit unabhängigen Belegen und guter Stufe.

**1.2 Löschen über die Herkunft:** Ein Beleg fällt weg, wenn seine Quelle gelöscht wird. Eine Aussage ohne Belege gilt als „ohne Beleg“ und wird nicht mehr genannt.
- Test: Aussage mit zwei Belegen verliert einen und bleibt. Mit dem letzten verschwindet sie aus Abfragen.

**1.3 Themenbaum** (in `brain/wissen.py`): Paket mit Oberthema, Baum ohne Kreise, Überblick (Themen mit Zahl der Abschnitte, aktiv/ruhend, laufendes Projekt).
- Test: Kreis wird abgewiesen. Überblick zählt richtig.

**1.4 Wissensmodule** (`brain/module.py`): Ordner mit `modul.yaml` und Markdown. Steckbrief geprüft (Schema, Pflichtfelder, Prüfsumme der Dateien), Text als Abschnitte in ein Paket, Vertrauen „gesichert“ oder „zu_pruefen“ am Paket. Neue Version ersetzt die alte (alte Abschnitte archiviert). Modul-Text ist Daten: auffällige Anweisungen werden markiert, nie befolgt.
- Test: falsche Prüfsumme wird abgewiesen. Gleiche Version zweimal ändert nichts. Neue Version archiviert die alte. Vertrauen kommt am Paket an. Datei außerhalb des Ordners (Link, `..`) wird abgewiesen.

**1.5 Kostenlose Quellen** (`brain/freie_quellen.py`): Wikipedia-Suche und Artikel-Auszug, Wikidata-Begriff, Marginalia-Suche. Bot-Kennung, nur https, Zeitlimit, Größenlimit. Ergebnisse mit Lizenz (CC BY-SA bzw. CC-BY-NC-SA) und Quelle. Text ist Daten.
- Test ohne Netz (ersetzte Abrufe): Treffer werden richtig gelesen, Lizenz hängt dran, Fehler und Sperren (429) geben eine klare Meldung.

**→ Zwischenstand:** Schlaubi legt Aussagen mit Belegen ab, liest Wissensmodule und recherchiert kostenlos in Wikipedia, Wikidata und Marginalia.

## Stufe 2 – Vektoren (nach Prüfung von sqlite-vec und fastembed, Lakehouse Phase 2)
Fast-Doppeltes über Vektor-Nähe, Hybridsuche über alle Bestände, Abfrage-Weiche (genau, breit, Beziehung, Zeit).

## Stufe 3 – Wissensgraph
Begriffe mit Synonymen (wo vorhanden mit Wikidata-Kennung) und Beziehungen aus den Aussagen. Beziehungsfragen über SQLite.

## Stufe 4 – Großer Bestand (nach Laptop-Steckbrief)
Leser für den Wikipedia-Abzug prüfen oder bauen, Messung mit 1 %, dann Wikipedia de als eigener Shard, Einlesen nachts und unterbrechbar, „bei Bedarf veredeln“.

## Stufe 5 – NFC
NFC-Leser (PN532) anbinden, Chip als Schlüssel `schlaubi-modul:<kennung>@<version>`, später Signatur.

## Offen
Voreinstellung Modul-Vertrauen (Live-Test), welcher große Bestand zuerst, Laptop-Platz.
