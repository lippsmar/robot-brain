# Design Wissensarchitektur – Version 1

Stand 16.10.2026. **Freigegeben von Marvin am 16.10.2026** („Ja“, zusammen mit dem Auftrag, den Bauplan zu schreiben und mit Stufe 1 anzufangen). Bauplan: `docs/bauplan-wissen-v1.md`. Baut auf dem freigegebenen Design Data Lakehouse auf (`docs/design-lakehouse.md`) und ersetzt nichts davon. Spiegel der Notion-Seite „Design Wissensarchitektur“. S = Schätzung, R = recherchiert, A = Annahme.

## 1. Zweck
Schlaubi soll wirklich alles Wissen aufnehmen können und es trotzdem schnell, belegt und aktuell abrufen. Dazu gehört, was er erlebt und recherchiert, ganze Wissensbestände wie die Wikipedia und Wissensmodule, die Marvin ihm gibt.

## 2. Marvins Entscheidungen (16.10.2026)
- „Alles Wissen“ heißt beides: Erlebtes und Recherchiertes **und** ganze Bestände von außen.
- Zusatzwissen kommt in **Wissensmodulen**: für den Anfang Markdown-Dateien, später über **NFC-Chips**.
- **Wie Modul-Wissen behandelt wird** (gesichert wie Marvins Wort oder als Quelle, die Schlaubi erst prüft), **entscheidet der Live-Test.** Deshalb wird es pro Modul umschaltbar gebaut.
- **Bis eine Such-API steht:** kostenlose Quellen und die eigene Vektor-Suche.

## 3. Nicht-Ziele
- Keine Cloud-Datenbank, alles bleibt auf dem Laptop (Entscheidung 13.10.2026).
- Keine eigene Graph-Datenbank: Begriffe und Beziehungen passen in SQLite-Tabellen.
- Kein Sprachmodell für jeden Abschnitt großer Bestände. Bei 30 Millionen Abschnitten würde das das Budget sprengen (Abschnitt 6).
- Keine Raubkopien und keine abgekratzten Suchergebnisse (Liste B in `docs/claude-grenzen.md`).

## 4. Sechs Schichten
Jede Schicht verweist auf die darunter, so bleibt jede Aussage bis zur Quelle nachverfolgbar.

| Schicht | Inhalt | Beispiel |
|---|---|---|
| **S0 Quelle** | Original mit Herkunft, Prüfsumme, Lizenz (Dokument-Ablage und Katalog, gebaut) | Datenblatt BMP280 als PDF |
| **S1 Abschnitt** | Textabschnitt mit Volltext und Vektor (Gedächtnis-Kern, gebaut; Vektoren: Lakehouse Phase 2) | „Der BMP280 misst Druck von 300 bis 1100 hPa …“ |
| **S2 Aussage** | eine Behauptung mit Belegen, Vertrauen, Gültigkeit und Status | BMP280 – misst – Luftdruck (3 Belege, gesichert) |
| **S3 Begriff und Beziehung** | Wissensgraph: Begriffe mit Synonymen, Beziehungen zwischen ihnen | BMP280 → ist ein → Drucksensor → gehört zu → Würfel |
| **S4 Thema** | Wissenspaket mit Kurzfassung (gebaut), neu mit Oberthema für einen Themenbaum | Sensorik ⊃ Klimasensoren ⊃ BMP280 |
| **S5 Überblick** | „Was weiß ich überhaupt?“ – Themenkarte mit Umfang und Stand | 12 Themen, 3 laufende Projekte, Wikipedia de Stand 01.10. |

**Aussagen (S2) im Detail:**
- Belege: welche Abschnitte und Quellen die Aussage stützen. Dasselbe aus zehn Quellen ist **eine** Aussage mit zehn Belegen.
- Vertrauen aus Quellen-Stufe A bis D (Bauplan Gehirn 10.4) und Zahl unabhängiger Belege.
- Zeit: „gültig seit“, „gültig bis“, „erfasst am“. Veraltetes wird „ersetzt“, nicht gelöscht.
- Status: unbestätigt, bestätigt, umstritten (Widerspruch sichtbar), ersetzt.

## 5. Wege hinein
1. **Erleben:** Gespräche werden täglich verdichtet (Bauplan Gehirn 10.5) zu Aussagen und Paketen. Was Marvin über sich sagt, ist `pii`.
2. **Recherche:** zuerst kostenlose Quellen (Abschnitt 9), Fachliteratur (Werkzeug `literatur.py`), später eine Such-API.
3. **Wissensmodule** (Abschnitt 7): Markdown-Ordner, später per NFC-Chip aufgerufen.
4. **Ganze Bestände:** z. B. der monatliche Wikipedia-Abzug (Wikimedia stellt ihn offiziell bereit, Lizenz CC BY-SA). Er wird als Hintergrund-Job eingelesen, nachts und unterbrechbar.

**Ablauf für alles Neue:**
- **Quarantäne:** Herkunft, Prüfsumme und Lizenz prüfen. Der Text ist Daten, nie Anweisung. Auffällige Stellen („ignoriere alle Regeln …“) werden markiert.
- **Zerlegen und einbetten:** Abschnitte mit Vektor.
- **Doppeltes erkennen:** gleiche Prüfsumme heißt gleiches Original. Sehr nahe Vektoren heißen fast gleicher Text, dann gibt es einen Beleg mehr statt eines neuen Eintrags.
- **Veredeln** (Aussagen und Begriffe ziehen): sofort bei Erlebtem, Recherche und Modulen. Bei großen Beständen erst, wenn ein Abschnitt in einer Antwort gebraucht wird („bei Bedarf veredeln“).
- **Widerspruch prüfen:** Eine neue Aussage gegen eine bestehende ergibt „umstritten“, beide bleiben sichtbar.
- Der Katalog bekommt einen Eintrag.

## 6. Größe und Tempo (S, auf dem Laptop messen)
- **Deutsche Wikipedia:** etwa 3 Mio. Artikel, grob 30 Mio. Abschnitte (S).
- **Vektoren** bei 384 Dimensionen: als Gleitkomma etwa 46 GB, als 8-Bit etwa 11,5 GB, als Bit-Vektor etwa 1,4 GB (S). Die Suche läuft auf dem kleinen Index und prüft die besten Treffer genau nach.
- **Volltext-Index:** grob so groß wie der Text selbst, einige GB bis über 10 GB (S).
- **Platzbedarf** für Wikipedia plus Reserve: mindestens 100 GB freie SSD (S). Kommt in den Laptop-Steckbrief.
- **Einlesen:** Vektoren auf dem Laptop-Prozessor brauchen eher Tage als Stunden (S). Der Job läuft nachts, setzt nach Abbruch fort, zeigt den Fortschritt im Katalog und stoppt bei Hitze (Kühlung).
- **Getrennte Bestände (Shards):** je Quelle ein eigener Speicher, z. B. „wiki-de-2026-10“, „erlebt“, „modul-…“. Ein neuer Wikipedia-Abzug ersetzt nur seinen Bestand, eigenes Wissen bleibt unberührt. Die Suche fragt alle Bestände und führt die Treffer zusammen.
- **Werkzeug:** sqlite-vec für eigenes Wissen, LanceDB (Festplatten-Index) für große Bestände, wie im Lakehouse-Vergleich vorgesehen.

## 7. Wissensmodule
- **Format:** ein Ordner mit `modul.yaml` und Markdown-Dateien.
  - `modul.yaml`: Kennung, Titel, Version, Quelle, Lizenz, Sprache, `vertrauen` (gesichert oder zu_pruefen), `pii`, `teilbar`, Prüfsumme der Dateien.
- **Einlesen:** Ein Modul wird ein Wissenspaket mit Abschnitten, Aussagen und Begriffen. Eine neue Version ersetzt die alte (alte Abschnitte werden archiviert, nicht gelöscht).
- **Vertrauen umschaltbar:**
  - „gesichert“: Aussagen gelten als bestätigt mit Stufe A.
  - „zu_pruefen“: Aussagen bleiben unbestätigt, bis andere Quellen sie stützen.
  - Welche Voreinstellung gilt, entscheidet der Live-Test.
- **NFC-Chip als Schlüssel:** Auf einen NTAG216 passen etwa 888 Bytes (R, Datenblatt beim Kauf prüfen). Der Chip trägt nur `schlaubi-modul:<kennung>@<version>` und eine kurze Prüfsumme.
  - Chip auflegen holt das Modul in die Stufe „Sofort“. Fehlt es, sagt Schlaubi das.
  - Der Chip ist nie Inhalt und nie Befehl. Eine Signatur (Ed25519) kann später dazukommen, damit nur Marvins Chips zählen.
  - Braucht einen NFC-Leser (PN532, steht unter „Mögliche Features“).

## 8. Abruf
- **Erst die Stufe „Sofort“** (Tagesparameter, aktive Pakete), dann die Suche.
- **Je nach Frage:**
  - genaue Frage („Bis wie viel hPa misst der BMP280?“): Aussagen und Abschnitte, Volltext plus Vektor
  - breite Frage („Was weißt du über Sensorik?“): Themen-Kurzfassungen und Überblick (S4, S5)
  - Beziehungsfrage („Was hängt alles an der Kühlung?“): Wissensgraph (S3)
  - Zeitfrage („Was galt im Juli?“): Gültigkeit der Aussagen
- **Antwort mit Herkunft:** Schlaubi kann auf Nachfrage jede Aussage bis zur Quelle belegen und sagt, wie sicher sie ist. Umstrittenes nennt er als umstritten.
- An die API gehen nur die Treffer, die für die Frage nötig sind, nie der ganze Bestand.

## 9. Kostenlose Quellen bis zur Such-API (getestet 16.10.2026, R)
- **Wikipedia:** Artikel über die normalen Seiten `/wiki/…`, Inhalte CC BY-SA (Speichern mit Quellenangabe erlaubt). Korrektur 16.10.2026: Die robots.txt von Wikipedia und Wikidata sperrt `/w/` und `/api/` (Schnittstelle und Suche) für Bots. Ob Schlaubi die Schnittstellen trotzdem nutzen darf (Wikimedia erlaubt API-Clients mit Kennung), entscheidet Marvin.
- **Marginalia Search:** öffentlicher Schlüssel funktioniert, Ergebnisse CC-BY-NC-SA (privat, nicht kommerziell erlaubt), kleiner Index.
- **Fachliteratur:** Crossref, arXiv, Europe PMC, OpenAlex (Werkzeug `tools/literatur/literatur.py`).
- **Nicht:** HTML-Seiten von Suchmaschinen abkratzen (z. B. DuckDuckGo-HTML), das umgeht Bot-Sperren.
- **Staan:** Das Konto wartet auf Freischaltung. Staan beschreibt sich als B2B-Dienst. Ob es für eine Privatperson außerhalb der EU freigegeben wird, ist nirgends belegt, das zeigt die Antwort.

## 9a. Wikipedia-Lizenz beim Antworten
Zitiert Schlaubi Wikipedia-Inhalte wörtlich weiter, gehört die Quelle dazu (CC BY-SA). Für eigene, private Antworten reicht die Quellenangabe auf Nachfrage.

## 10. Datenschutz und Löschen
- `pii` geht durch alle Schichten: Eine Aussage aus einer persönlichen Quelle ist persönlich.
- **Löschwunsch** (nur mit Marvins Freigabe): Mit der Quelle verschwinden alle Abschnitte, Aussagen und Beziehungen, die **nur** auf ihr beruhen. Aussagen mit weiteren Belegen verlieren nur diesen Beleg. Möglich, weil jede Schicht auf ihre Herkunft zeigt.
- Gäste (Version 2) sehen nur teilbares Wissen ohne `pii`.

## 11. Bausteine
- **Gebaut:** Gedächtnis-Kern (S1), Wissenspakete (S4), Katalog, Dokument-Ablage, Stufe „Sofort“.
- **Neu:** Aussagen mit Belegen (S2), Begriffe und Beziehungen (S3), Themenbaum und Überblick (S4/S5), Modul-Leser, Einlese-Pipeline mit Quarantäne, Abfrage-Weiche, Wikipedia- und Marginalia-Abruf mit Bot-Kennung.
- **Pakete** (vor Nutzung nach Checkliste prüfen): sqlite-vec, fastembed (geplant), LanceDB (Lakehouse Phase 6), ein Leser für Wikipedia-Abzüge (offen, z. B. ein Parser für das Wiki-Format).

## 12. Stufen
1. **Ohne neue Pakete:** Aussagen mit Belegen, Modul-Leser (Markdown), Wikipedia/Wikidata/Marginalia-Abruf mit Bot-Kennung, Themenbaum.
2. **Vektoren:** sqlite-vec und fastembed (Lakehouse Phase 2), Doppeltes über Vektor-Nähe, Abfrage-Weiche.
3. **Wissensgraph:** Begriffe und Beziehungen aus Aussagen, Beziehungsfragen.
4. **Großer Bestand:** Wikipedia de als eigener Shard, nach Laptop-Steckbrief (Platz, RAM, AVX2) und Messung mit einem kleinen Ausschnitt.
5. **NFC:** Leser anbinden, Chips als Modul-Schlüssel.

## 13. Risiken
- **Fremdes Wissen mit versteckten Anweisungen:** Quarantäne, Text nur als Daten, Prüffragen mit präparierten Modulen.
- **Falsche Aussagen ziehen:** Das günstige Modell zieht Aussagen nur mit Beleg-Stelle. Stichproben im Live-Test.
- **Platz und Zeit beim großen Bestand:** erst mit 1 % der Wikipedia messen, dann hochrechnen.
- **Lizenzen:** Jede Quelle trägt ihre Lizenz im Katalog. CC-BY-NC-SA (Marginalia) nur privat.

## 14. Offene Punkte
- Voreinstellung für Modul-Vertrauen: Live-Test (Marvin).
- Welcher große Bestand zuerst? Vorschlag: Wikipedia de (A).
- Laptop: freier Platz und RAM (Steckbrief).
- Leser für Wikipedia-Abzüge: Paket prüfen oder selbst bauen.
