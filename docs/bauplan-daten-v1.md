# Bauplan Umgebungsbewusstsein und Datensammlung – Version 1

Stand 14.10.2026. Grundlage: `docs/design-daten.md`, von Marvin am 14.10.2026 freigegeben. **Von Marvin am 14.10.2026 bestätigt.**

**Stand Code (16.10.2026):** Die Teile auf dem Gehirn sind gebaut und getestet, mit Daten aus Tests statt vom Würfel: Data Lake (7, 6.1, 8.2) in `brain/datalake.py`, Kühlung (3) in `brain/cooling.py`, Zustand (6.2) in `brain/context.py`, Muster (9.1–9.3) in `brain/patterns.py`. Die Tests mit echten Daten (z. B. „nach zwei Wochen drei zutreffende Muster“) folgen, sobald der Würfel oder das Handy als Test-Würfel Daten liefert. Schwellen und Tageszeiten sind Annahmen, siehe die Kopfkommentare der Dateien.

## Kopf
- **Ziel:** Der Würfel erfasst immer, wenn er an ist, Geräusche als Merkmale, Messwerte und groben Kontext. Das Gehirn legt alles sauber im Data Lake ab, erkennt Muster und nutzt sie für Schlaubis Umgebungsbewusstsein und Laune. Gespräche anderer werden nie mitgehört.
- **Architektur:**
  - Messwert-Dienst auf dem Pi
  - Ton-Merkmale auf dem Pi oder auf dem Laptop, je nach Messung
  - Ablage im Data Lake (L5) auf dem Gehirn
  - Muster-Auswertung auf dem Gehirn
- **Technik:** Python, I2C über Software-Bus, lokale Geräusch-Klassifizierung (Software nach Prüfung), SQLite oder Parquet für Zeitreihen.
- **Abhängigkeiten:**
  - Körper: Phase 4 (Mikrofon), Phase 8a (Sensoren), Phase 10 (Modem)
  - Gehirn: Phase 10 (Gedächtnis)
  - Charakter: Phase 8 (Sprechererkennung)

### Globale Vorgaben
| Vorgabe | Wert |
|---|---|
| Sprache anderer | nie gespeichert, nie ausgewertet, sofort verworfen |
| Rohton | nur im Arbeitsspeicher, wenige Sekunden. Gespeichert nur bei „Nimm das auf“ ohne andere Menschen |
| Cloud | keine Rohdaten an Claude, nur Zusammenfassungen im Gespräch |
| Messrate | Messwerte jede Minute, Ton-Merkmale in kurzen Fenstern (Wert legt Phase 1 fest) |
| Aufbewahrung | Messwerte und Geräuschklassen für immer, bewusste Aufnahmen gelten als gemerkt |
| Protokoll | jede bewusste Aufnahme und jeder Zustimmungs-Modus im Event-Log |

## Phase 1 – Geräusch-Erkenner auswählen
**1.1 Kandidaten suchen und nach Checkliste prüfen:** Lizenz, lokal lauffähig, keine Telemetrie, Datenschutz.
**1.2 Messen:** Läuft er auf dem Pi Zero (CPU-Last, Wärme, Strom) oder nur auf dem Laptop?
- **Entscheidungspunkt Ort:** Reicht der Pi nicht, rechnet der Laptop.
- Dann geht Ton verschlüsselt über das private Netz zum Laptop, wird dort nur im Arbeitsspeicher ausgewertet und danach verworfen.
- Gespeichert werden nur Merkmale.
- Marvin bestätigt diese Variante, weil dann Ton den Würfel verlässt (er bleibt aber bei Marvin).

## Phase 2 – Messwert-Dienst
**2.1 Sensoren auslesen:**
- Zuluft (BMP280), Abluft mit Luftfeuchte und Luftdruck (BME280), Licht (BH1750)
- Chip-Temperatur und Drosselung (`vcgencmd`)
- Modem-Temperatur (`AT+CPMUTEMP`)
- Akku (soweit messbar)
- WLAN- und LTE-Signal

**2.2 Übertragung:** jede Minute an das Gehirn.
- Ohne Verbindung puffert der Pi die Werte (kleine Datei) und überträgt sie nach.
- Jede Messung hat eine laufende Nummer, damit nichts doppelt oder verloren ist.

- Test:
  - Eine Stunde Betrieb ergibt 60 vollständige Datensätze.
  - Nach 10 Minuten ohne Netz kommen alle Werte nach.
  - Ein abgesteckter Sensor ergibt eine Fehlermeldung statt falscher Werte.

## Phase 3 – Kühlung
**3.1 Auswertung:** Zuluft gegen Abluft, Chip- und Modem-Temperatur. Trend über die letzte Stunde.
**3.2 Warnung** per Telegram ab 70 °C Chip-Temperatur oder bei Drosselung, dazu Laune-Ereignis „mir ist warm“.
- Test: Mit Last (z. B. Stresstest auf dem Pi) steigt die Abluft gegenüber der Zuluft. Bei künstlich gesenkter Warngrenze kommt die Warnung.

## Phase 4 – Ton-Merkmale
**4.1 Merkmale:** Lautstärke, Geräuschklassen mit Sicherheit, Sprache ja oder nein, ungefähre Zahl der Stimmen.
**4.2 Sprache:**
- Wird Sprache erkannt, prüft die Sprechererkennung (Bauplan Charakter Phase 8), ob es Marvin ist.
- Nur Marvins Sprache geht weiter an die Spracherkennung.
- Alles andere wird sofort verworfen, nur „Sprache, zwei Stimmen“ bleibt als Merkmal.

**4.3 Öffentlich Gesprochenes** (Durchsagen, Radio, TV): nur verarbeiten, wenn Marvin es ausdrücklich verlangt (z. B. „Was wurde gerade durchgesagt?“). Kein automatisches Mitschreiben.
- Test (mit zwei Personen, die vorher eingewilligt haben): Sie unterhalten sich zehn Minuten neben dem Würfel.
  - Bestanden, wenn im Data Lake kein Wortlaut, kein Thema und kein Stimmprofil der beiden landet, nur Merkmale.
  - Auch der Arbeitsspeicher-Puffer wird geprüft: nach dem Fenster leer.

## Phase 5 – Zustimmungs-Modus
**5.1 Start durch Marvin:** z. B. „Schlaubi, alle sind einverstanden, hör mit“ per Sprache, bestätigt per Telegram.
**5.2 Anzeige und Ansage:**
- Schlaubi sagt laut „Ich höre jetzt mit“.
- Ein eigenes Lichtmuster bleibt sichtbar, solange der Modus läuft: langsames blaues Kreisen.
- Wer nicht einverstanden ist, kann „Schlaubi, stopp“ sagen.
- Der Modus endet von selbst nach einer festen Zeit oder auf „Schlaubi, fertig“.

**5.3 Daten** aus dem Modus werden als `pii: true` markiert, mit Hinweis auf die Zustimmung.
- Test: Ohne Bestätigung per Telegram startet der Modus nicht. Nach der festen Zeit endet er. „Stopp“ von irgendeiner Stimme beendet ihn sofort.

## Phase 6 – Kontext
**6.1 Grober Ort** über bekannte WLANs, die Marvin benennt (z. B. „Das ist das Büro“). Ohne bekanntes WLAN gilt „unterwegs“. Kein GPS.
**6.2 Zustand:** Tageszeit, Akku, Verbindung, ob ein Gespräch läuft.
- Test: Wechsel zwischen zwei benannten WLANs ergibt den richtigen Ort. Ein fremdes WLAN ergibt „unterwegs“.

## Phase 7 – Ablage im Data Lake
**7.1 Zeitreihen** (Zeit, Gerät, Kanal, Wert, Einheit, Qualität) und Geräuschklassen (Zeit, Klasse, Sicherheit) im Data Lake (L5).
**7.2 Manifest** mit PII-Status pro Datensatz.
**7.3 Aufbewahrung** für immer. Bewusste Aufnahmen gelten als gemerkt.
**7.4 Sicherung** über die bestehende Sicherung des Gehirns.
- Test: Ein Monat Daten lässt sich nach Zeit, Ort und Kanal abfragen. Eine Wiederherstellung aus der Sicherung enthält sie vollständig.

## Phase 8 – Bewusste Aufnahmen und Beschriftungen
**8.1 „Nimm das auf“:**
- kurze Aufnahme, nur wenn keine fremden Stimmen erkannt werden
- sonst Hinweis „Hier sprechen andere, das nehme ich nicht auf“

**8.2 Beschriftungen:**
- Marvin bestätigt oder korrigiert Geräuschklassen, z. B. per Telegram „Das war Regen“.
- Die Beschriftungen werden für spätere eigene Modelle gespeichert.

- Test: Eine Aufnahme mit einer zweiten Stimme im Hintergrund wird abgelehnt. Eine Beschriftung ändert die Klasse im Data Lake mit Vermerk.

## Phase 9 – Muster erkennen
**9.1 Tägliche und wöchentliche Auswertung,** z. B.:
- wann Marvin wo arbeitet
- wie laut und warm es dabei ist
- wann der Akku knapp wird

**9.2 Nutzung:** Schlaubi kennt seine Umgebung im Gespräch („Im Café ist es heute lauter als sonst“). Muster fließen in die Laune und in Hinweise ein.

**9.3 Datenschutz:**
- Muster über Marvin sind `pii: true` und bleiben lokal.
- Auf „Was weißt du über meinen Alltag?“ zeigt Schlaubi sie.
- Marvin kann sie löschen.

- Test: Nach zwei Wochen echter Daten nennt Schlaubi mindestens drei zutreffende Muster. Marvin bestätigt sie. Löschen eines Musters wirkt.

## Phase 10 – Abschluss
**10.1 Speicher und Strom:** Datenmenge und zusätzlicher Stromverbrauch nach einem Monat prüfen.
**10.2 Endtest:** alle Ziele aus dem Design, mit Belegen in Notion.
**10.3 Rückblick** mit Skill `roboter-retro`.

---

## Selbstprüfung
- **Jedes Ziel aus dem Design hat einen Schritt:**
  - Geräusche: 1, 4
  - Gesprochenes: 4, 5
  - Messwerte: 2
  - Kontext: 6
  - Kühlung: 3
  - bewusste Aufnahmen: 8
  - immer an: 2, 4
  - Ablage und Aufbewahrung: 7
  - Muster und Laune: 9
- **Jedes Risiko aus dem Design hat einen Test:**
  - Sprache wird nicht verworfen: 4
  - Erkenner zu schwer: 1.2
  - Abwärme: Körper 8a.4 und 3
  - Speicher: 10.1
- **Offene Punkte aus dem Design gelöst:**
  - Geräusch-Software: Phase 1
  - Zustimmung: Phase 5
  - Bilder: bleiben für später
- **Entscheidungspunkt Ort des Geräusch-Erkenners** (1.2) ist markiert, nichts ist erfunden.
