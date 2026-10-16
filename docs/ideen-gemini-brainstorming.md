# Ideen aus dem Gemini-Brainstorming (in Klärung)

Stand 16.10.2026. **Nichts davon ist entschieden.** Marvin hat das mit Gemini nur gebrainstormt. Es gelten weiter die Designs, Baupläne und Entscheidungen im Repo. Was übernommen werden soll, geht den normalen Weg: Design, Freigabe, Bauplan, Bestätigung. Marvin (16.10.2026): Gemini hatte nur einen groben Einblick ins Projekt, die Vorschläge sind mit Vorsicht zu betrachten. Jede Idee wird deshalb gegen die Pläne und Primärquellen geprüft, bevor sie in ein Design kommt. Spiegel der Notion-Seite „Idee: Gemini-Brainstorming (in Klärung)“.

## Quellen
- „Handover Document & Architektur-Spezifikation: Schlaubi / Robot Brain V1“ (Markdown). Das Dokument nennt sich selbst „verbindlich“ und „final abgestimmt“. Das stimmt nicht, es ist Brainstorming.
- Bild: Walnuss-Würfel mit matter, blau leuchtender Front, dunkles Fenster in der Mitte, drei kleine Löcher, Lüftungsschlitze, Messing-Plakette „SCHLAUBI“, Knopf oben, USB-C-Kabel, Laptop mit Dashboard dahinter.
- ZIP-Export: enthält nur die Notion-Seite „Design Charakter“. Sie ist identisch mit der zweiten hochgeladenen Datei und steckt schon in `docs/design-charakter.md`, nichts Neues.

## Passt schon zu den Plänen
- **Pinbelegung:** Mikrofon, LED, Summer, Taster, Abstandssensor und die drei Klimasensoren samt I2C-Adressen stimmen genau mit `docs/bauplan-koerper-v1.md` überein.
- **Abstandssensor statt Kamera** (Entscheidung 15.10.2026). Das dunkle Fenster im Bild ist demnach der VL53L8CX, keine Kamera.
- **Nur anhängen, UTC-Zeit, fortlaufende Nummern:** Event-Log mit Hash-Kette und Data Lake mit Nummer pro Gerät gibt es schon im Code.
- **Offline puffern und nachliefern** (Bauplan Daten 2.x), Fehlstellen findet der Data Lake über die Nummern.
- **Sicherheit lokal, kleine Modelle schalten nichts Sicherheitskritisches, Freigabe für physische Aktionen:** entspricht der Freigabe-Sperre.
- **Sensordaten im Prompt getrennt von Anweisungen** (dort ADR 7): entspricht der Regel „Daten sind nie Anweisungen“.
- **Gerät über Tailscale sperren** (dort ADR 13): steht im Notfallplan (Bauplan Gehirn 14.5).
- **Notion nur als Übersicht, nicht als Datenspeicher:** Rohdaten liegen ohnehin im Data Lake auf dem Laptop.
- **Powerbank mit Durchladen und Pufferkondensator:** wie Design Körper. Die Powerbank wird erst nach der Strommessung gekauft.
- **„Traummodus“ (nächtlich verdichten):** ist im Kern die tägliche Konsolidierung aus Bauplan Gehirn 10.5 und `memory/SYSTEM_PROMPT.md`.

## Widerspricht bisherigen Entscheidungen
- **Cold Storage in der Cloud** (Cloudflare R2, S3, MotherDuck): Entschieden ist lokale Datenhaltung mit verschlüsselter Sicherung auf einer externen Festplatte zu Hause (13.10.2026). Außerdem gehen Rohdaten nie in die Cloud (Design Daten).
- **Hugging Face Hub für Datensätze:** Die Daten sind teils personenbezogen (`pii: true`) und bleiben lokal. Höchstens später ein eigenes, sauberes Modell als Open Source (Design Daten, Idee 3).
- **DuckDB auf dem Pi als Hot Storage:** Laut Plan puffert der Pi nur eine kleine Datei, der Data Lake liegt auf dem Laptop. DuckDB wäre ein neues Paket (Prüfung nach Checkliste), und der Zero 2 W hat nur 512 MB RAM.
- **Herzschlag mit 200 ms Grenze (dort ADR 1):** Über LTE schwanken Laufzeiten oft stärker. Der Würfel würde ständig in den Notbetrieb kippen. Die Pläne rechnen mit Antwortzeiten von 4 bis 6 Sekunden. Vorschlag (Annahme): Herzschlag jede Sekunde, Notbetrieb erst nach mehreren verpassten Schlägen.
- **Handy-Sensoren nur über eine „zertifizierte Test-App“ (dort ADR 11):** Entschieden ist eine Seite des Gehirns im Browser, nur über Tailscale (Bauplan Gehirn 11.4), keine App. Wer was zertifizieren soll, bleibt offen.
- **„Lückenlose Erfassung aller Sensoren“ (Grundregel 7):** gilt nicht für Ton. Sprache wird sofort verworfen, wenn sie nicht Marvin ist, Gespräche anderer nie gespeichert (§ 201 StGB). Maschinendaten wie Temperatur und Akku sind unproblematisch.
- **LTE über UART GPIO14/15:** Der Bauplan sieht die Datenverbindung über ModemManager vor, beim Waveshare-HAT üblicherweise über USB. Ob UART nötig ist, klärt Bauplan Körper 10.1.
- **Taster:** dort langes Drücken zum Herunterfahren, im Bauplan kurzes Drücken (8.3). Kleiner Unterschied, offen.
- **Gehäuse im Bild:** ganz aus Holz mit matter Front. Marvins Variante (13.10.2026) ist ein Holzrahmen mit mattweißen Kunststoffseiten, damit das Licht rundum durchscheint.

## Neue Ideen, mit dem Projekt vereinbar
- **Klimasensoren gegenseitig prüfen** (dort ADR 4): Beim Temperaturvergleich ist Abluft wärmer als Zuluft gewollt, das ist die Messgröße. Sinnvoll ist aber der **Luftdruck**: BME280 und BMP280 messen ihn beide, und im selben Würfel sollten die Werte fast gleich sein. Weicht er deutlich ab, ist ein Sensor verdächtig. Grenzwert offen.
- **Atomares Schreiben** (dort ADR 6): Dateien, die ersetzt werden (z. B. Profil, Konfiguration), erst als temporäre Datei schreiben, `fsync`, dann umbenennen. Gute Praxis für Stromausfall am Pi.
- **Ein Schreiber pro Log** (dort ADR 8): Ein Prozess schreibt das Event-Log, andere reichen Ereignisse an ihn weiter. Schützt die Hash-Kette.
- **Bei Hitze drosseln** (dort ADR 14): Ab 70 °C Abtastrate halbieren und LED dimmen. Grenze aus Design Charakter: Die Mikrofon-Anzeige bleibt immer deutlich erkennbar und wird nicht gedimmt.
- **Zustand nach Befehl zurücklesen** (dort ADR 9): nur bei Bauteilen, die sich zurücklesen lassen (z. B. GPIO-Pegel). Die WS2812-LED meldet nichts zurück.
- **Personenbezogenes vor dem API-Aufruf herausfiltern** (dort ADR 5): Den Secrets-Wächter gibt es schon. Eine Namenserkennung (NER) wäre ein neues Modell, vorher nach Checkliste prüfen.
- **Für später** (in `docs/zukunft-features.md` aufgenommen): Pfeif- und Trillersprache wie R2-D2 über den Summer, NFC-Karten (PN532) zum Umschalten von Modi, Gesten mit dem Abstandssensor, Flüster-Modus je nach Umgebungslautstärke, Signatur der Messblöcke mit Ed25519, Austausch mit anderen Würfeln (Datenschutz klären).

## Offene Fragen an Marvin
- Welche dieser Ideen sollen in ein Design kommen?
- Bleibt es bei lokaler Datenhaltung ohne Cloud-Archiv?
