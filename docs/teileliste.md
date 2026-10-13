# Teileliste mit Kosten (Entwurf)

Stand: 13.10.2026. **Entwurf zur Freigabe, nichts bestellen.** Preise sind Momentaufnahmen aus Shops und Preisvergleichen, inklusive MwSt., ohne Versand. Vor dem Kauf im Shop prüfen.

Legende: **R** = recherchierter Preis mit Quelle, **S** = Schätzung (kein belastbarer Preis gefunden).

Grundlage: Architektur aus CLAUDE.md (zweistufiger Hub: Mikrocontroller plus Pi Zero 2 W als Körper). **Gehirn: Marvins alter Laptop als Heimserver** (Entscheidung 13.10.2026), daher keine Kosten fürs Gehirn. Mikrocontroller und Sensorliste sind noch **offen**, die Auswahl unten ist ein Vorschlag.

## 1. Körper (Pi Zero 2 W)

| Teil | Vorschlag | Preis | Art | Quelle / Hinweis |
|---|---|---|---|---|
| Rechner | Raspberry Pi Zero 2 WH (mit Stiftleiste) | 20,90 € | R | buyzero.de (Zero 2 W ohne Leiste 17,90 €, BerryBase 18,90 €). Verfügbarkeit schwankt |
| Speicherkarte | microSD 32–64 GB, A1/A2 | 10–20 € | S | Markenkarte, kein Extreme-Modell nötig |
| LTE-Modem | Waveshare SIM7600E-H 4G HAT (Europa-Bänder) | 72,90–99,00 € | R | Botland 72,90 €, Tinytronics 75,00 €, welectron 99,00 €. Antennen dabei |
| Akku / USV | Waveshare UPS HAT (C) für Pi Zero, 1000 mAh | 22,90 € | R | BerryBase, welectron. **Ob es die Modem-Spitzen bis 2 A schafft, ist unklar** (Datenblatt prüfen) |
| Alternative Akku | Powerbank 10.000 mAh mit Pass-Through-Laden + Netzteil 5 V 3 A | 30–40 € | S | Passt zur Annahme „ein bis zwei Tage Laufzeit“ aus dem Projektstart |
| Mikrocontroller | Raspberry Pi Pico 2 W (Not-Aus, Watchdog, Sensorik) | 7,50 € | R | BerryBase |
| Klima-Sensor | BME280 (Temperatur, Feuchte, Luftdruck) | 5–11 € | R | Makershop 5,80 €, AZ-Delivery 10,99 € |
| Abstands-Sensor | VL53L1X ToF, bis 4 m | 5–18 € | R | eBay-Angebote (Händler aus China günstiger, länger Lieferzeit) |
| Kamera | Raspberry Pi Camera Module 3 (75° oder 120°) | 30–45 € | R | geizhals.at 40,00 € (120°), älter ca. 31 € (75°) |
| Kamerakabel | Mini-CSI-Kabel für Pi Zero | ca. 3 € | S | Zero hat kleineren Kamera-Anschluss |
| Mikrofon | INMP441 I2S-Modul | ca. 5 € | S | nur Dollarpreis gefunden (4,95 USD) |
| Kleinteile | Gehäuse, Kabel, Steckbrett, Not-Aus-Taster, Pufferkondensator | 20–40 € | S | |
| **Summe Körper** | | **ca. 202–309 €** | | |

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
| Körper + Pi 5 ohne USV | ca. 448–585 € |
| Körper + Pi 5 mit USV | ca. 508–665 € |
| **Körper + alter Laptop als Gehirn (gewählt)** | **ca. 202–309 €** |

## 4. Laufende Kosten

| Posten | Preis | Art | Quelle / Hinweis |
|---|---|---|---|
| Prepaid-SIM mit SMS und Daten | ca. 5–9 € je 28 Tage | R | z. B. CallYa Start 4,99 € (2 GB), otelo Smart S 4,95 € (2 GB), ja!mobil 8,99 € (25 GB). Auf Marvin registriert |
| Claude-API | Ausgabenlimit legt Marvin fest | offen | Prepaid-Guthaben in der Anthropic Console |
| E-Mail-Adresse | offen | offen | Anbieter noch nicht gewählt |
| Such-API für Recherche | offen | offen | Anbieter noch nicht gewählt |

## 5. Hinweise zur Hardware
- Der SIM7600-HAT kann über die GPIO-Leiste (UART) oder per USB-Kabel betrieben werden. Für mobiles Internet ist USB schneller. Der Zero hat nur einen freien USB-Port.
- UPS HAT (C) sitzt unter dem Zero (Federkontakte), das LTE-HAT oben auf der Stiftleiste. Passung und Höhe vor dem Kauf prüfen.
- Modem-Stromspitzen bis etwa 2 A: Stromversorgung mit Reserve, Pufferkondensator, kein schwaches Netzteil.

## 6. Offene Entscheidungen
- Mikrocontroller bestätigen (Vorschlag Pico 2 W) und Sensorliste festlegen.
- ~~Gehirn: Pi 5 kaufen oder vorhandenen Heimserver nutzen.~~ Entschieden: alter Laptop.
- Laptop-Eignung: mindestens 8 GB RAM empfohlen, SSD, 64-Bit-Linux, Betrieb mit zugeklapptem Deckel, Akkuzustand (Dauerladen auf 100 % altert den Akku, Ladegrenze setzen wenn möglich), Stromverbrauch im Leerlauf.
- Akku-Lösung für den Körper: UPS HAT (C) oder Powerbank.
- Budget-Obergrenze für die Anschaffung und monatliches API-Limit.
