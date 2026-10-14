# Teileliste mit Kosten (Version 1, zur Freigabe)

Stand: 13.10.2026, angepasst an `docs/design-koerper.md`. **Zur Freigabe, nichts bestellen.** Preise sind Momentaufnahmen aus Shops und Preisvergleichen, inklusive MwSt., ohne Versand. Vor dem Kauf im Shop prüfen.

Legende: **R** = recherchierter Preis mit Quelle, **S** = Schätzung (kein belastbarer Preis gefunden).

Grundlage: Design Körper „Schlaubi“ Version 1. **Gehirn: Marvins alter Laptop als Heimserver**, daher keine Kosten fürs Gehirn. In Version 1 kein eigener Mikrocontroller (Vorschlag im Design, Abschnitt 6).

## 1. Körper „Schlaubi“ (Version 1)

| Teil | Vorschlag | Preis | Art | Quelle / Hinweis |
|---|---|---|---|---|
| Rechner | Raspberry Pi Zero 2 WH (mit Stiftleiste) | 0 € | – | **Vorhanden: Raspberry Pi Zero 2 W** (bestätigt 13.10.2026). Falls ohne Pins: Stiftleiste 2×20 anlöten, ca. 1 € |
| Speicherkarte | microSD 32–64 GB, A1/A2 | 10–20 € | S | Markenkarte |
| LTE-Modem | Waveshare SIM7600E-H 4G HAT (Europa-Bänder) | 72,90–99,00 € | R | Botland 72,90 €, Tinytronics 75,00 €, welectron 99,00 €. Antennen dabei |
| Akku | Powerbank ca. 10.000 mAh mit Pass-Through | 0 € | – | **Marvin hat Powerbanks.** Kapazität, Größe und Pass-Through in Phase 11 prüfen. Nur falls keine passt: 25–40 € |
| Kamera | Raspberry Pi Camera Module 3 (75° oder 120°) | 30–45 € | R | geizhals.at 40,00 € (120°), älter ca. 31 € (75°) |
| Kamerakabel | Mini-CSI-Kabel für Pi Zero | ca. 3 € | S | Zero hat kleineren Kamera-Anschluss |
| Mikrofon | INMP441 I2S-Modul | ca. 5 € | S | nur Dollarpreis gefunden (4,95 USD) |
| Status-Licht | WS2812-Ring oder -Streifen, 8–12 LEDs (leuchtet durch den milchigen Kunststoff) | 3–8 € | S | |
| Summer | Piezo-Summer | ca. 1 € | S | |
| Schalter | Ein-Aus-Schalter oder Metall-Taster | 3–8 € | S | dient als Not-Aus |
| Laden | USB-C-Einbaubuchse oder kurzes Durchführungskabel | 5–10 € | S | |
| Kleinteile | Kabel, Schrauben, Abstandshalter, Lichtleiter, Pufferkondensator | 15–30 € | S | |
| Gehäuse | Holzrahmen aus Marvins Bestand, Seiten aus Acrylglas opal weiß, matt/satiniert, 3 mm (Zuschnitt, für Hinterleuchtung) | 10–25 € | S | Marvins Variante 13.10.2026 |
| Klima-Sensor | BME280 (Temperatur, Luftfeuchte, Luftdruck), I2C | ca. 4–11 € | S | Ergänzung 14.10.2026. BerryBase-Preis nicht gefunden, andere Händler ca. 3,70–11,45 € |
| Licht-Sensor | BH1750 (GY-302), I2C | ca. 2,40 € | R | Ergänzung 14.10.2026, BerryBase (Preis indirekt gefunden, im Shop prüfen) |
| **Summe Version 1** | | **ca. 164–267 €** | | |

**Gestrichen gegenüber dem ersten Entwurf:** UPS HAT (C) (Akku zu klein, ca. 1 Stunde), Pico 2 W (ohne Motoren nicht nötig, bleibt Option).

**Optional, nicht in Version 1:**

| Teil | Vorschlag | Preis | Art |
|---|---|---|---|
| Abstands-Sensor | VL53L1X | 5–18 € | R |
| Mikrocontroller | Raspberry Pi Pico 2 W | 7,50 € | R |
| Display (Version 2) | kleines rundes oder eckiges SPI-Display | offen | – |

**Werkzeug für den ersten Test:** USB-Strommessgerät (USB-C) zum Messen des Verbrauchs, ca. 10–20 € (S).

## 2. Gehirn

**Gewählt: alter Laptop als Heimserver, 0 €.** Der Laptop-Akku dient gleichzeitig als USV. Eignung noch prüfen (siehe unten). Die Pi-5-Variante bleibt als Rückfalloption stehen.

### Rückfalloption Raspberry Pi 5

| Teil | Vorschlag | Preis | Art | Quelle / Hinweis |
|---|---|---|---|---|
| Rechner | Raspberry Pi 5, 8 GB | 184,90 € | R | BerryBase, heise-Preisvergleich (Oktober 2026). Preis deutlich gestiegen |
| Netzteil | Offizielles 27-W-USB-C-Netzteil | 12,40 € | R | rasppishop.de |
| Kühlung | Raspberry Pi Active Cooler | 5,90 € | R | BerryBase, rasppishop.de |
| SSD-Adapter | Raspberry Pi M.2 HAT+ | 12,50 € | R | BerryBase, rasppishop.de |
| SSD | NVMe 256 GB, M.2 2230 oder 2242 | 30–60 € | S | kein aktueller Preis gefunden |
| **Summe Gehirn** | | **ca. 246–276 €** | | |
| Optional USV | Waveshare UPS HAT (E) für Pi 5 + 4× 21700-Akkus | 60–80 € | S | HAT ca. 39,90 € laut BerryBase-Hinweis, Akkus geschätzt |

**Variante Heimserver:** Läuft schon ein Rechner mit mindestens 8 GB RAM dauerhaft, entfällt das Gehirn (0 €). Docker und die OpenClaw-Absicherung gelten genauso.

## 3. Gesamt einmalig

| Variante | Summe |
|---|---|
| Körper Version 1 + Pi 5 ohne USV (Rückfall) | ca. 439–580 € |
| Körper Version 1 + Pi 5 mit USV (Rückfall) | ca. 499–660 € |
| **Körper Version 1 + alter Laptop als Gehirn (gewählt)** | **ca. 158–254 €** |

## 4. Laufende Kosten

| Posten | Preis | Art | Quelle / Hinweis |
|---|---|---|---|
| Prepaid-SIM mit SMS und Daten | ca. 5–9 € je 28 Tage | R | z. B. CallYa Start 4,99 € (2 GB), otelo Smart S 4,95 € (2 GB), ja!mobil 8,99 € (25 GB). Auf Marvin registriert |
| Claude-API | höchstens 30 $ / Monat (Schätzung normal ca. 25 $) | R | Limit in der Anthropic Console, Entscheidung 13.10.2026 |
| E-Mail-Adresse | 0 € | R | mail.de FreeMail (Entscheidung 13.10.2026) |
| Such-API für Recherche | offen | offen | Anbieter noch nicht gewählt |

## 5. Hinweise zur Hardware
- Der SIM7600-HAT kann über die GPIO-Leiste (UART) oder per USB-Kabel betrieben werden. Für mobiles Internet ist USB schneller. Der Zero hat nur einen freien USB-Port.
- Das LTE-HAT sitzt oben auf der Stiftleiste des Zero. Die Powerbank liegt daneben im Würfel und versorgt beide über USB. Passung im 10-cm-Würfel vor dem Kauf prüfen.
- Modem-Stromspitzen bis etwa 2 A: Stromversorgung mit Reserve, Pufferkondensator, kein schwaches Netzteil.

## 6. Offene Entscheidungen
- ~~Mikrocontroller und Sensorliste~~ Vorschlag im Design: Version 1 ohne Mikrocontroller, ohne Zusatzsensoren.
- ~~Gehirn: Pi 5 kaufen oder vorhandenen Heimserver nutzen.~~ Entschieden: alter Laptop.
- Laptop-Eignung: mindestens 8 GB RAM empfohlen, SSD, 64-Bit-Linux, Betrieb mit zugeklapptem Deckel, Akkuzustand (Dauerladen auf 100 % altert den Akku, Ladegrenze setzen wenn möglich), Stromverbrauch im Leerlauf.
- ~~Akku-Lösung~~ Vorschlag im Design: Powerbank ca. 10.000 mAh mit Pass-Through, Kauf erst nach Strommessung.
- ~~Budget-Obergrenze~~ Keine feste Grenze, Version 1 ca. 193–304 €. Offen: monatliches API-Limit.
