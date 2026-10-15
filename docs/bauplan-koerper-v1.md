# Bauplan Körper „Schlaubi“ – Version 1

Stand 13.10.2026. Grundlage: `docs/design-koerper.md` (von Marvin am 13.10.2026 freigegeben). **Dieser Plan wird erst umgesetzt, wenn Marvin ihn bestätigt.** Bestellungen macht Marvin selbst (sein Name, sein Geld).

## Kopf
- **Ziel:** Ein 10-cm-Holzwürfel, der auf „Schlaubi“ reagiert, Ton und Bild an das Gehirn schickt, über Bluetooth antwortet und 6 Stunden mit Akku läuft.
- **Architektur:** Raspberry Pi Zero 2 W im Würfel als Körper (Aktivierungswort, Mikrofon, Abstandssensor, LED, Summer, Bluetooth, WLAN/LTE). Marvins alter Laptop als Gehirn (Gespräch, Gedächtnis, Telegram, Mail), verbunden über ein privates Netz.
- **Technik:** aktuelles Raspberry Pi OS Lite 64-bit, Python, Bluetooth über BlueZ/PipeWire, I2S-Mikrofon, privates Netz (Tailscale oder gleichwertig), Software für das Aktivierungswort nach Prüfung.
- **Abgrenzung:** Die Gesprächslogik auf dem Laptop (Spracherkennung, Claude, Gedächtnis, Telegram, Mail) bekommt einen eigenen Plan. Hier reicht auf dem Laptop ein einfacher Test-Dienst, der Ton und Bilder entgegennimmt und bestätigt.

### Globale Vorgaben
| Vorgabe | Wert |
|---|---|
| Versorgung | 5 V über USB, Modem-Spitzen bis ca. 2 A, Pufferkondensator am Modem |
| Logikpegel | 3,3 V an allen GPIOs, nie 5 V auf einen GPIO |
| Laufzeit | mindestens 6 Stunden mit Akku, Durchschnittsverbrauch höchstens 4 W |
| Temperatur | Chip unter 70 °C nach 1 Stunde im geschlossenen Würfel, keine Drosselung |
| Budget | Version 1 ca. 193–304 €, Bestellung in zwei Stufen |
| Sicherheit | Akku nur als fertige Powerbank mit Schutzschaltung, nie kurzschließen, nicht im geschlossenen Holz laden ohne Lüftung |
| Secrets | WLAN-Passwort, SIM-PIN, Tokens nur im Secret-Store, nie im Repo |
| Protokoll | jedes Ergebnis als Logzeile in Notion „Entscheidungen und Projektlog“ |

### Pinbelegung (Pi Zero 2 W, BCM-Nummern, physischer Pin in Klammern)
| Bauteil | Signal | GPIO (Pin) |
|---|---|---|
| Mikrofon INMP441 | BCLK / SCK | GPIO18 (12) |
| | LRCL / WS | GPIO19 (35) |
| | DOUT → Pi DIN | GPIO20 (38) |
| | VDD | 3,3 V (1) |
| | GND und L/R | GND (6) |
| RGB-LED WS2812 | Daten | GPIO12 (32), Versorgung 5 V (2), GND (9) |
| Piezo-Summer (passiv) | Signal über 100-Ω-Widerstand | GPIO16 (36), GND (34) |
| Taster (sauber herunterfahren / wecken) | Kontakt | GPIO3 (5), GND (39) |
| Abstandssensor VL53L8CX (Änderung 15.10.2026, statt Kamera) | SDA / SCL | am selben Software-I2C wie die Sensoren (GPIO22/23), 3,3 V, GND. Adresse 0x29. Übrige Pins der Pololu-Platine laut Pololu-Doku |
| Sensoren BME280, BMP280 und BH1750 (I2C, Ergänzung 14.10.2026) | SDA / SCL | Software-I2C (`i2c-gpio`) auf GPIO22 (15) und GPIO23 (16), 3,3 V (17), GND (20). Grund: Der Hardware-I2C nutzt GPIO2/GPIO3, und GPIO3 ist schon der Taster mit Weckfunktion. Vor dem Löten mit der Pinbelegung des LTE-HAT abgleichen (Schritt 10.1) |
| LTE-HAT | laut Waveshare-Wiki | Pins in Schritt 10.1 prüfen, Konflikte mit 3, 12, 16, 18–20 ausschließen |

Hinweise zur Belegung: Die LED nutzt den PWM-Baustein an GPIO12. Der Summer liegt deshalb bewusst nicht an GPIO13 (zweiter PWM-Kanal), sondern an GPIO16 mit Software-Ton. Die WS2812 läuft mit 5 V, das Datensignal mit 3,3 V funktioniert meist. Falls die LED flackert, einen Pegelwandler (z. B. 74AHCT125) einsetzen.

Harter Not-Aus: Schalter im USB-Stromkabel zwischen Akku und Elektronik. Der Taster an GPIO3 fährt sauber herunter, damit die Speicherkarte nicht beschädigt wird.

Ablauf jedes Schritts: **Messung oder Test festlegen → ausführen (erwartet: schlägt fehl oder Ausgangswert) → umsetzen → erneut prüfen (besteht) → Logzeile.**

---

## Phase 1 – Bestellung Stufe 1 (Testteile, ca. 50–70 €)
**1.1 Teile bestellen (Marvin):** nach `docs/einkauf-stufe1.md` (Pi Zero 2 WH, microSD, INMP441, 27-W-USB-C-Netzteil, USB-C-Tester, Adapter USB-C auf Micro-USB, Jumperkabel), ca. 56–60 € plus Versand.
- Prüfung: Lieferung vollständig, Pi und Karte unbeschädigt.

## Phase 2 – Grundsystem
**Schritt-für-Schritt-Anleitung:** `docs/anleitung-phase2.md`.

**2.1 System aufspielen:** Raspberry Pi OS Lite 64-bit mit Raspberry Pi Imager, Benutzer, WLAN und SSH-Schlüssel vorab einstellen (kein Passwort-Login).
- Test vorher: `ssh schlaubi` schlägt fehl (Pi aus).
- Test nachher: `ssh schlaubi` verbindet ohne Passwort, `uname -m` zeigt `aarch64`.

**2.2 Absichern:** System aktualisieren, Passwort-Login für SSH aus, Firewall (nur SSH aus dem Heimnetz), automatische Sicherheitsupdates.
- Test: SSH mit Passwort wird abgelehnt, `sudo ufw status` zeigt nur SSH erlaubt.

**2.3 Temperatur und Drosselung prüfen:** `vcgencmd measure_temp` und `vcgencmd get_throttled`.
- Erwartet: Temperatur unter 60 °C im Leerlauf, `throttled=0x0`.

## Phase 3 – Strom Grundlast
**3.1 Leerlauf messen:** Pi am Strommessgerät, 10 Minuten Leerlauf mit WLAN.
- Festhalten: Durchschnitt in mA und W. Das ist der Ausgangswert für alle weiteren Messungen.

## Phase 4 – Mikrofon
**4.1 Verdrahten (Strom aus):** INMP441 nach Pinbelegung, vor dem Einschalten mit Multimeter prüfen: 3,3 V an VDD, kein Kurzschluss zwischen 3,3 V und GND.
**4.2 I2S einschalten:** passendes Overlay in `/boot/firmware/config.txt`, Neustart.
- Test vorher: `arecord -l` zeigt kein I2S-Gerät.
- Test nachher: `arecord -l` zeigt das Mikrofon. Eine 10-Sekunden-Aufnahme in 1 m Abstand ist verständlich, Pegel nicht übersteuert.
**4.3 Stromaufnahme:** Messung mit laufender Daueraufnahme. Differenz zu 3.1 festhalten.

## Phase 5 – Bluetooth-Ton und WLAN (Risiko 1)
**5.1 Kopfhörer koppeln:** Bluetooth-Kopfhörer und Box mit BlueZ/PipeWire koppeln, Testton abspielen.
- Test: Ton kommt an beiden Geräten an.
**5.2 Gleichzeitig Datenverkehr:** 5 Minuten Musik abspielen, gleichzeitig Datenübertragung über WLAN zum Laptop (z. B. `iperf3`).
- Bestanden: keine hörbaren Aussetzer, oder höchstens 1 kurzer Aussetzer in 5 Minuten.
- Nicht bestanden: Ursache nach Skill `roboter-debugging` suchen. Ausweich-Möglichkeit: Bluetooth-USB-Stick. Erst nach Lösung weiter.
**Sicherheit (14.10.2026):** Bluetooth nur mit Marvins Geräten koppeln, danach nicht mehr sichtbar. Aus, wenn kein Ton gebraucht wird.
- Test: Ein fremdes Handy findet den Würfel nicht.

## Phase 6 – Aktivierungswort „Schlaubi“ (Risiko 2)
**6.1 Software prüfen:** Kandidaten (z. B. openWakeWord, Porcupine) nach Checkliste in `skills/INDEX.md`: Lizenz, Datenschutz (läuft komplett lokal?), Netzwerkzugriffe, Konto nötig?
- Ergebnis mit Datum in Notion „Skill-Prüfstatus“. Marvin gibt die Wahl frei.
**6.2 Wort „Schlaubi“ einrichten** (trainieren oder anlegen, je nach Software).
**6.3 Erkennung messen:**
- 20-mal „Schlaubi“ aus 1 m Abstand: mindestens 18 erkannt.
- 1 Stunde Radio oder Gespräch im Hintergrund ohne „Schlaubi“: höchstens 1 Fehlauslösung.
- CPU-Last im Dauerbetrieb unter 50 %, Temperatur unter 70 °C.
- Nicht bestanden: Ursache suchen, andere Software oder Einstellungen. Erst nach Lösung weiter.

**Entscheidungspunkt 1 (Marvin):** Phase 5 und 6 bestanden? Nur dann Stufe 2 bestellen.

## Phase 7 – Bestellung Stufe 2
**7.1 Teile bestellen (Marvin):** LTE-Modem SIM7600E-H, Abstandssensor VL53L8CX (Pololu 3419), RGB-LED WS2812, Piezo-Summer, Taster, Schalter, USB-C-Buchse, Kleinteile, Pufferkondensator, Sensoren BME280 und BH1750. **Noch keine Powerbank** (erst nach Phase 11).
**7.2 SIM besorgen (Marvin):** Prepaid-SIM mit Daten, auf Marvin registriert. PIN nur im Secret-Store.

## Phase 8 – LED, Summer, Taster
**8.1 Verdrahten (Strom aus):** nach Pinbelegung, Multimeter-Prüfung wie 4.1.
**8.2 Zustände festlegen und testen:**
| Zustand | LED | Ton |
|---|---|---|
| Bereit | aus | – |
| Hört zu | blau | kurzer hoher Ton |
| Denkt nach | gelb pulsierend | – |
| Fehler / keine Verbindung | rot | tiefer Ton |
- Test: Ein Testskript schaltet alle Zustände nacheinander, jeder ist sichtbar und hörbar.
**8.3 Taster:** kurzer Druck fährt sauber herunter, erneuter Druck startet.
- Test: Herunterfahren ohne Fehler, Neustart funktioniert, Dateisystem sauber.

## Phase 8a – Sensoren Temperatur und Licht (Ergänzung 14.10.2026)
**8a.1 Bestellung (Marvin):** BME280, BMP280 und BH1750 zusammen mit Stufe 2.
**8a.2 Anschluss:** Software-I2C auf GPIO22/23 (siehe Pinbelegung), alle drei Sensoren am selben Bus. BME280 (Abluft) auf Adresse 0x77, BMP280 (Zuluft) auf 0x76 (über den SDO-Pin einstellen), BH1750 auf 0x23.
- Test: `i2cdetect` auf dem Software-Bus zeigt alle drei Adressen.
**8a.3 Messen:** Temperatur, Luftfeuchte, Luftdruck und Helligkeit jede Minute an das Gehirn (Data Lake L5, Zeitreihe mit Gerät und Qualität).
- Test: Werte im Vergleich mit einem Zimmerthermometer und Handy-Helligkeitsmesser plausibel. Taschenlampe auf den Lichtsensor ergibt einen deutlichen Sprung.
**8a.4 Kühlung messen:** Zuluft (BMP280) und Abluft (BME280) gegenüberstellen, dazu Chip-Temperatur (`vcgencmd`) und Modem-Temperatur (`AT+CPMUTEMP`, in Phase 10 prüfen). Jede Minute ins Gehirn.
- Test: Vor dem Einbau messen beide Sensoren nebeneinander höchstens 0,5 °C verschieden (sonst Abgleich speichern). Im geschlossenen Würfel nach einer Stunde: Abluft wärmer als Zuluft, Chip unter 70 °C, keine Drosselung.
- Warnung an Marvin, wenn die Chip-Temperatur 70 °C erreicht oder der Pi drosselt.

## Phase 9 – Abstandssensor (Änderung 15.10.2026, ersetzt Kamera)
**9.1 Anschließen (Strom aus):** VL53L8CX an den Software-I2C (siehe Pinbelegung). Multimeter-Prüfung wie 4.1.
- Test: `i2cdetect` auf dem Software-I2C zeigt 0x23, 0x29, 0x76 und 0x77.
**9.2 Firmware-Start messen (Risiko):** Der Sensor lädt beim Start seine Firmware (ca. 80 kB) über I2C.
- Test: Zeit vom Einschalten bis zum ersten Messwert festhalten. Dauert es länger als 10 Sekunden, den Sensor an den Hardware-I2C oder per SPI anschließen und die Pinbelegung neu prüfen.
**9.3 Messen:** 8×8 Zonen, einige Male pro Sekunde, nur im Würfel ausgewertet.
- Test: Hand in 30 cm vor der Front: mittlere Zonen zeigen 25–35 cm. Freie Sicht: Werte über 1 m.
**9.4 Anwesenheit:** Sitzt jemand länger als 5 Sekunden näher als 1,2 m davor, meldet der Würfel „anwesend“ ans Gehirn, beim Weggehen „weg“. Keine Rohdaten der Tiefenbilder ans Gehirn, nur diese Ereignisse und eine Minutenzusammenfassung. Anwesenheit ist personenbezogen (`pii: true`).
- Test: 10 Mal hinsetzen und aufstehen, mindestens 9 Ereignisse richtig.
**9.5 Stromaufnahme** im Messbetrieb festhalten.
**Sicherheit:** Laut ST ist der Sensor ein augensicherer Laser der Klasse 1. Keine Kamera im Würfel, deshalb entfallen Kamera-Abdeckung und Kamera-Test.

## Phase 10 – LTE-Modem
**10.1 Pinbelegung des HAT prüfen** (Waveshare-Wiki) und gegen die eigene Pinbelegung abgleichen. Konflikte vor dem Aufstecken lösen.
**10.2 Anschließen (Strom aus)**, Pufferkondensator, Antennen dran, SIM einlegen.
- Test: Modem antwortet auf `AT`, `AT+CPIN?` meldet bereit nach PIN aus dem Secret-Store, `AT+CSQ` zeigt Empfang.
**10.3 Datenverbindung** über ModemManager.
- Test: Bei abgeschaltetem WLAN lädt der Pi eine Testseite über LTE.
**10.4 Stromspitzen messen:** beim Verbindungsaufbau.
- Bestanden: kein Neustart, kein Unterspannungs-Hinweis in `vcgencmd get_throttled`.
**Sicherheit (14.10.2026):** SIM-PIN aktiv (im Secret-Store), keine eingehenden Verbindungen über LTE, Modem-Firmware auf aktuellem Stand.
- Test: Von außen ist über die LTE-Adresse kein Port erreichbar.

## Phase 11 – Verbindung zum Gehirn und Gesamtstrom (Risiko 3 und 4)
**11.1 Privates Netz** auf Pi, Laptop und Handy einrichten (Prüfung des Programms nach Checkliste).
- Test: Pi erreicht den Laptop über WLAN und über LTE, Handy erreicht den Pi.
**11.2 Test-Dienst auf dem Laptop:** nimmt Ton und Bild vom Pi entgegen und bestätigt.
- Test: Nach „Schlaubi“ leuchtet die LED blau, 5 Sekunden Ton kommen auf dem Laptop an, LED geht aus. Verzögerung über WLAN und LTE messen.
**11.3 Gesamtverbrauch messen:** 1 Stunde realistischer Betrieb (Zuhören, 4 Aktivierungen, Abstandssensor an, LTE an).
- Bestanden: Durchschnitt höchstens 4 W.
- Daraus Akkugröße berechnen. **Powerbank erst jetzt bestellen (Marvin)**, mit Pass-Through laut Datenblatt.
**Sicherheit (14.10.2026):** Würfel gestohlen oder verloren: Anleitung „Würfel verloren“ (Gerät im Tailnet sperren, WLAN-Passwort ändern, SIM sperren lassen). Der Würfel hat im Gehirn nur seine wenigen Funktionen (Tailnet-Regeln).
- Test: Würfel im Tailnet sperren, er erreicht das Gehirn nicht mehr. Wieder freigeben.

## Phase 12 – Gehäuse
**12.1 Innenaufbau auf Träger** (Holz- oder Metallplatte), Akku fest, Kabelwege, Abstand zu Antennen.
**12.2 Holzwürfel bauen:** 10 cm, Fenster für den Abstandssensor vorne (klar, nicht opal), Öffnungen für Mikrofon, USB-C, Lüftung, LED-Fenster, vorne Platz fürs spätere Display. Metall nur an Boden oder Kanten, nie vor Antennen.
**12.3 Funk durch Holz (Risiko 5):** Empfang mit und ohne Gehäuse vergleichen (`AT+CSQ`, WLAN-Signal).
- Bestanden: keine Verbindungsabbrüche, Signal höchstens leicht schwächer.
**12.4 Wärme (Risiko 6):** 1 Stunde Betrieb im geschlossenen Würfel.
- Bestanden: unter 70 °C, `throttled=0x0`. Sonst Lüftung vergrößern.
**12.5 Laufzeittest:** voll geladene Powerbank, realistischer Betrieb.
- Bestanden: mindestens 6 Stunden.
**Hinweis KI-Verordnung (14.10.2026):** sichtbarer Hinweis „KI“ am Würfel, z. B. Gravur im Holzrahmen oder Aufkleber.

## Phase 13 – Abschluss
**13.1 Endtest:** alle Ziele aus dem Design nacheinander prüfen (Aktivierung, Bluetooth, Abstandssensor, Livebild übers Handy, LTE unterwegs, Laufzeit). Ergebnis mit Belegen in Notion.
**13.2 Rückblick** mit Skill `roboter-retro`.
**13.3 Nächster Plan:** Gesprächslogik auf dem Laptop (Spracherkennung, Claude, Gedächtnis, Telegram, Mail).

---

## Selbstprüfung
- Jedes Ziel aus dem Design hat einen Schritt: Aktivierung (6, 8, 11), Bluetooth (5), Text-Fallback und Telegram/Mail (eigener Plan, Abgrenzung im Kopf), Abstand (9), Livebild übers Handy (Bauplan Gehirn 11.4), Mobilität und Akku (3, 11, 12.5), Verbindung (10, 11), Gehäuse (12).
- Jedes Risiko aus dem Design hat einen Test: 1 → 5.2, 2 → 6.3, 3 → 11.3, 4 → 11.2, 5 → 12.3, 6 → 12.4.
- Keine Platzhalter. Offene Werte sind bewusst Messungen (Strom, Verzögerung).
- Bestellungen in zwei Stufen. Teure Teile erst nach Entscheidungspunkt 1, Powerbank erst nach Messung.
