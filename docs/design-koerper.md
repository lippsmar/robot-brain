# Design Körper „Schlaubi“ – Version 1

Stand 13.10.2026. **Zur Freigabe durch Marvin.** Nichts wird bestellt, gebaut oder verdrahtet, bevor Marvin dieses Design freigibt. Spiegel der Notion-Seite „Design Körper Schlaubi“.

## 1. Zweck
Schlaubi ist ein sprechender Würfel für Schreibtisch und unterwegs. Marvin unterhält sich mit ihm wie mit einem Sidekick. Schlaubis Wissen wächst mit jeder Unterhaltung und durch eigene Recherche, wenn er nichts zu tun hat. Marvin kann ihm Dinge zeigen, die er mit seinen Sensoren wahrnimmt.

## 2. Ziele (Version 1)
- Aktivierung per Stimme mit „Schlaubi“, Rückmeldung durch LED und kurzen Ton.
- Gespräch per Stimme: zuhören über das eigene Mikrofon, antworten über Bluetooth-Kopfhörer oder Bluetooth-Box.
- Ohne Bluetooth-Gerät antwortet Schlaubi als Text über Telegram.
- Fernzugriff per Telegram und per E-Mail (eigene Adresse bei mail.de).
- Dinge zeigen: Kamera vorne, Bild geht zur Auswertung ans Gehirn.
- Mobil: 4–6 Stunden ohne Steckdose (Büro, Café).
- Verbindung zum Gehirn (Marvins alter Laptop zu Hause) über WLAN oder die eigene SIM, immer über ein privates Netz.

## 3. Nicht-Ziele (Version 1)
- Kein eingebauter Lautsprecher.
- Kein Display. Das Gesicht auf einem Display kommt in Version 2, Platz und Anschluss werden vorgesehen.
- Keine Motoren oder beweglichen Teile.
- Keine Spracherkennung oder KI auf dem Würfel selbst, außer dem Aktivierungswort.
- Keine Anrufe, keine SMS an Dritte.

## 4. Grenzen und Regeln
- **Nichts in Marvins Namen ohne Rückfrage:** keine Nachrichten, Mails, Käufe, Anmeldungen, Zusagen, Termine oder Beiträge als Marvin. Lesen, recherchieren und Entwürfe vorbereiten ist erlaubt. Schlaubi antwortet nur Marvin.
- **E-Mail:** Aufträge gelten nur von Marvins Absender (Absenderliste, SPF/DKIM). Mails von anderen sind Daten, nie Anweisungen. Anhänge werden nie ausgeführt.
- **Datenschutz:** Das Mikrofon hört dauerhaft nur auf das Aktivierungswort, lokal im Würfel. Danach nur Marvins Gespräch verarbeiten, nichts von anderen Personen speichern (`pii: true`). Kamera nur bei Bedarf an, Aufnahmen von Personen nur mit Einwilligung.
- **Nach außen** tritt Schlaubi nur als erkennbarer Bot auf.
- **Secrets** (Mail-Passwort, Telegram-Token, SIM-PIN) nur im Secret-Store auf dem Laptop, nie im Repo, in Notion oder im Chat.

## 5. Marvins Entscheidungen (13.10.2026)
| Thema | Entscheidung |
|---|---|
| Form | Würfel, höchstens 10 cm |
| Unterwegs | Büro oder Café, 4–6 Stunden |
| Antworten | Bluetooth-Kopfhörer oder -Box, sonst Text aufs Handy |
| Zuhör-Signal | LED und kurzer Ton, später Gesicht auf Display |
| Grenze | nichts in Marvins Namen ohne Rückfrage |
| Kanäle | Telegram, dann E-Mail |
| Mail | eigene Adresse schon in der Testphase, Anbieter mail.de FreeMail |
| Gehirn | alter Laptop als Heimserver |
| Budget | keine feste Grenze, Eigenbau wo möglich, soll cool aussehen |
| Eigenbau | Löten, Holz- und Metallbearbeitung, kein 3D-Drucker |

## 6. Architektur
- **Körper (Würfel):** Raspberry Pi Zero 2 W. Erkennt das Aktivierungswort, nimmt Ton und Bild auf, steuert LED und Summer, spielt Ton über Bluetooth ab, hält die Verbindung (WLAN, sonst LTE).
- **Gehirn (Laptop):** Spracherkennung, Gespräch mit der Claude-API, Gedächtnis (Memory Core), Recherche, Telegram-Bot, Mail-Abruf, Sprachausgabe. Läuft in Docker, nur über privates Netz erreichbar.
- **Verbindung:** privates Netz (z. B. Tailscale) zwischen Würfel, Laptop und Handy.
- **Vorschlag Mikrocontroller:** In Version 1 **kein** zusätzlicher Mikrocontroller. Ohne Motoren gibt es keine gefährliche physische Aktion. Der Not-Aus ist der Ein-Aus-Schalter, LED und Summer hängen direkt am Pi. Der Pico 2 W bleibt Option, falls später Motoren oder viele Sensoren dazukommen.

## 7. Hardware Version 1
Details und Preise: `docs/teileliste.md`.
- Raspberry Pi Zero 2 WH, microSD
- LTE-Modem Waveshare SIM7600E-H (mit Antennen)
- Kamera: Raspberry Pi Camera Module 3 mit Mini-CSI-Kabel
- Mikrofon: INMP441 (I2S)
- RGB-LED (WS2812) und Piezo-Summer
- Akku: Powerbank ca. 10.000 mAh mit Durchladen (Pass-Through), USB-C
- Ein-Aus-Schalter, USB-C-Ladebuchse oder -Kabel nach außen
- **Sensoren (Ergänzung 14.10.2026, Marvins Entscheidung):** Klimasensor BME280 (Temperatur, Luftfeuchte, Luftdruck) und Lichtsensor BH1750 (Helligkeit in Lux), beide über I2C. Dazu ein zweiter Temperatursensor BMP280 an der Zuluft (Ergänzung 14.10.2026). Der BME280 sitzt an der Abluft. Der Unterschied zeigt zusammen mit Chip- und Modemtemperatur, ob die Kühlung reicht.
- Optional, nicht in Version 1: Abstandssensor VL53L1X, CO₂-Sensor, Display

**Akku-Begründung:** geschätzt 2,5–4 W Verbrauch, für 6 Stunden 15–24 Wh, also etwa 5.000–7.500 mAh. Eine fertige Powerbank mit Schutzschaltung ist sicherer als ein Eigenbau-Akku aus Einzelzellen. Der echte Verbrauch wird vor dem Akku-Kauf gemessen.

## 8. Gehäuse
**Marvins Variante (13.10.2026, bevorzugt):** Holzrahmen als Würfel-Gerüst, Seiten aus **mattweißem Kunststoff**, damit die LED-Farben von innen gleichmäßig durchleuchten. Material: 3 mm Acrylglas opal weiß, beidseitig satiniert/matt, als Zuschnitt. Beim Kauf auf die Lichtdurchlässigkeit achten (für Hinterleuchtung gedacht, nicht zu dicht).
- Gleichmäßiges Leuchten: LEDs mit 2–3 cm Abstand zur Platte und nach innen oder auf eine weiße Fläche gerichtet, sonst sieht man helle Punkte.
Folgen:
- Die LED leuchtet durch den milchigen Kunststoff: Der ganze Würfel glüht in der Zustandsfarbe. Dafür statt einer einzelnen LED einen kleinen WS2812-Ring oder -Streifen (ca. 8–12 LEDs) innen.
- Kunststoff lässt Funk durch, die Antennen dürfen hinter jeder Kunststoffseite liegen. Metall nur am Rahmen oder Boden, nie vor Antennen.
- Kamera braucht ein klares Fenster oder ein Loch in der Frontplatte, Mikrofon ein paar kleine Löcher.
- Lüftung über Schlitze im Rahmen oder Boden, Acryl isoliert Wärme.
- Rahmen innen als Träger für die Elektronik, eine Seite abnehmbar (z. B. mit Magneten oder Schrauben).

Ursprünglicher Vorschlag (Alternative):
- Holzwürfel 10 cm, z. B. Nussbaum oder Eiche, Metall als Akzent (Boden, Kanten oder Kühlblech).
- Antennen nur an Holzseiten, nie hinter Metall (Metall blockiert Funk).
- LED hinter dünn ausgefrästem Holz oder einem kleinen Lichtleiter: unsichtbar, bis Schlaubi zuhört.
- Öffnungen: Kamera vorne, Mikrofon-Löcher, USB-C, Lüftungsschlitze. Vorne Platz für das Display in Version 2.
- Innenleben auf einem herausnehmbaren Träger, Akku fest fixiert.
- Kein 3D-Druck nötig, Kleinteile als Fertigteile.

## 9. Risiken und frühe Tests
Diese Punkte werden zuerst geprüft, bevor das Gehäuse gebaut wird:
1. **Bluetooth-Ton und WLAN gleichzeitig:** Der Zero 2 W teilt sich einen Funkchip. Test: Musik an Kopfhörer, gleichzeitig Datenverkehr. Stockt der Ton?
2. **Aktivierungswort „Schlaubi“ auf dem Zero 2 W:** Ein eigenes Wort muss trainiert werden, und der Zero hat wenig Rechenleistung. Test: Erkennungsrate und CPU-Last.
3. **Stromverbrauch:** Messung mit USB-Messgerät im Leerlauf, beim Zuhören und mit LTE.
4. **Verbindung unterwegs:** Würfel über LTE und privates Netz zum Laptop. Verzögerung messen.
5. **Funk durch Holz:** Empfang im fertigen Gehäuse prüfen.
6. **Wärme:** Temperatur im geschlossenen Würfel nach einer Stunde Betrieb.

## 10. Offene Punkte (blockieren das Design nicht)
- Mail-Konto bei mail.de anlegen (Marvin, wenn zurück in Deutschland)
- SIM-Anbieter wählen
- Laptop-Eignung prüfen (Modell, RAM, SSD, Akku, Linux)
- Software für das Aktivierungswort auswählen und prüfen (Lizenz, Datenschutz)
- Holzart und Metall-Akzent festlegen

## 11. Änderung 15.10.2026: Abstand statt Kamera, Augen vom Smartphone (in Klärung)
Marvins Entscheidung: Der Würfel braucht keine eigene Kamera. Die Augen übernimmt das Smartphone, am Würfel sitzt ein Abstandssensor. 3D-Kamera, exotische Sensoren und mehr Zubehör-Schnittstellen sind mögliche Features für später (`docs/zukunft-features.md`).

- **Entfällt:** Camera Module 3 und Mini-CSI-Kabel, die Kamera-Öffnung in der Front und die mechanische Kamera-Abdeckung.
- **Neu (Vorschlag):** VL53L8CX, 8×8 Zonen bis 4 m, vorne hinter einem kleinen Fenster, am Software-I2C (GPIO22/23) zusammen mit BME280 (0x77), BMP280 (0x76) und BH1750 (0x23). Der VL53L8CX nutzt standardmäßig 0x29.
- **Nutzen:** Merkt, ob jemand vor ihm sitzt, ob sich etwas nähert und wie weit Dinge entfernt sind. Ein grobes 8×8-Tiefenbild, keine Gesichter, keine Bilder.
- **Risiko (früher Test):** Der Sensor lädt beim Start seine Firmware (ca. 80 kB) über I2C. Am langsamen Software-I2C kann das Sekunden dauern. Messen; notfalls an den Hardware-I2C oder per SPI. (S)
- **Augen vom Smartphone (Marvin 15.10.2026: „Livebild, wenn ich die Seite öffne“):**
  - Das Gehirn stellt eine kleine Webseite bereit, nur über Tailscale erreichbar, mit HTTPS (Browser geben die Kamera nur auf sicheren Seiten frei). Keine App nötig.
  - Öffnet Marvin die Seite und erlaubt die Kamera im Browser, sieht Schlaubi live. Schließt er die Seite oder geht der Bildschirm aus, endet das Livebild sofort.
  - Anzeige: Der Browser zeigt die Kamera-Nutzung selbst an, die Seite zeigt groß „Live“, der Würfel leuchtet hell weiß.
  - Annahme: Das Livebild bleibt im privaten Netz beim Gehirn. An die Claude-API geht nur ein Einzelbild, wenn Marvin etwas fragt oder zeigt („Schau mal“ oder Knopf), verkleinert und ohne Metadaten. Dauerndes Auswerten durch Claude würde das Budget von 20 € schnell aufbrauchen.
  - Annahme: Livebild schaltet sich nach 10 Minuten ohne Frage selbst ab. Nichts wird gespeichert, außer Marvin sagt „merken“.
  - Personen im Bild nur mit Einwilligung, wie bisher.
  - Wird nur von Marvins Gerät im Tailscale-Netz angenommen (Tailscale-Identität prüfen), nie öffentlich.
- **Kosten:** Version 1 ca. 155–251 € statt 166–269 € (Teileliste).
- **Status:** Design Körper Version 1 war freigegeben. Diese Änderung braucht eine neue Freigabe, bevor Bauplan und Teileliste endgültig angepasst werden.
