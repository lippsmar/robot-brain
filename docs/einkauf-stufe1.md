# Einkaufsliste Stufe 1 (Bauplan Phase 1)

Stand 13.10.2026. Preise inkl. MwSt., ohne Versand, Momentaufnahmen. **Vor dem Kauf Preis und Verfügbarkeit im Shop prüfen.** Bestellung macht Marvin.

**Update 13.10.2026:** Marvin hat schon einen Pi, Powerbanks und ein USB-Netzteil. Damit bleibt:

| # | Teil | Wofür | Preis | Wo |
|---|---|---|---|---|
| 1 | Mikrofon INMP441 (I2S) | Phase 4 | 3,10 € | BerryBase: https://www.berrybase.de/en/inmp441-mems-omnidirectional-microphone-module-i2s-interface |
| 2 | USB-Strommessgerät **passend zum Netzteil**: bei USB-A UNI-T UT658A (8,90 €), bei USB-C KWS-1902C (ca. 7,50 €) | Strommessung Phase 3, 4, 11 | 7,50–8,90 € | BerryBase USB-Messgeräte: https://www.berrybase.de/en/workshop/measurement-technology/usb-testers/ |
| 3 | Kabel auf Micro-USB (USB-A oder USB-C, passend zum Messgerät), kurz und dick (für 2 A+) | Pi Zero hat Micro-USB | ca. 3–5 € (Schätzung) | **Vorhanden** (Marvin, 13.10.2026). Darauf achten: kurz und dick genug für 2 A, sonst Unterspannung |
| 4 | Jumperkabel Dupont **female-female**, 20 cm | Mikrofon, später LED/Summer | ab 1,60 € | BerryBase Jumperkabel: https://www.berrybase.de/bauelemente/prototyping/jumperkabel/ |
| 6 | Stiftleiste 2×20, 2,54 mm (nur falls am Pi noch keine Pins angelötet sind) | zum Anlöten am Pi Zero 2 W | ca. 1 € (Schätzung) | Elektronik-Shop deiner Wahl |
| 5 | microSD 32 GB, Markenkarte A1 | Betriebssystem. **Vorhanden** (Größe zu Hause prüfen). Nur kaufen, falls kleiner als 16 GB | ca. 7 € | z. B. https://www.ebay.de/itm/116572688443 |

**Summe: ca. 12–14 € plus Versand** (Mikrofon, USB-Messgerät, Jumperkabel, ggf. Stiftleiste).

**Nicht mehr nötig:** Pi (vorhanden: Raspberry Pi Zero 2 W, bestätigt 13.10.2026), Netzteil (vorhanden, mindestens 5 V / 2,5 A), Powerbank (vorhanden, in Phase 11 prüfen).

## Aufbau der Strommessung
Netzteil → USB-Messgerät → Kabel auf Micro-USB → Pi Zero (Strom-Buchse „PWR“). Später kommt statt des Netzteils die Powerbank davor. **Vor dem Kauf prüfen**, dass Stecker und Buchsen von Tester und Adapter zusammenpassen (Tester: USB-C-Stecker und -Buchse).

## Vermutlich schon vorhanden (prüfen)
- Lötkolben und Lötzinn: Beim INMP441 liegt die Stiftleiste oft lose bei und muss angelötet werden.
- Multimeter (Prüfung 4.1 und 8.1): **vorhanden**
- Bluetooth-Kopfhörer und Bluetooth-Box (Phase 5)
- microSD-Kartenleser am Laptop

## Nicht in Stufe 1
Modem, Kamera, LED, Summer, Taster, Powerbank kommen erst nach Entscheidungspunkt 1 bzw. nach der Strommessung.
