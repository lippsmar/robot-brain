# Mögliche Features für später

Stand 16.10.2026. Sammlung von Ideen, die nicht in Version 1 kommen. Nichts davon ist beschlossen. Vor der Umsetzung gilt der normale Weg: Design, Freigabe, Bauplan, Bestätigung. Spiegel der Notion-Seite „Mögliche Features (Zukunft)“. R = recherchiert, S = Schätzung.

## Sehen und 3D
- **ToF-Tiefenkamera am Würfel:** Arducam ToF-Kamera, 240×180, bis 4 m, ±2 cm, am Zero 2 W ca. 15 Bilder/s über den Kamera-Anschluss, der durch den Wegfall der Kamera frei ist. Doku von 2022, Unterstützung für aktuelles Raspberry Pi OS prüfen. (R)
- **3D-Scan am Laptop (Gehirn):** Orbbec Femto Bolt, Nachfolger der Azure Kinect, ca. 418 $ (R). Kinect v2 nur mit USB 3.0 und altem Treiber (libfreenect2), nicht am Pi Zero (R). Luxonis OAK-D Lite mit eigenem KI-Chip, 269 $ seit 9.7.2026 (R). Intel RealSense: Übernahme durch Cognex angekündigt, Zukunft offen (R).
- **Smartphone als Tiefensensor** (z. B. Fotogrammetrie aus mehreren Handyfotos). (S)

## Exotischere Sensoren (Preise nicht geprüft)
- mmWave-Radar: Anwesenheit, Bewegung, Atmung auf Abstand
- Wärmebildsensor (z. B. 32×24 Pixel)
- echter CO₂-Sensor (NDIR)
- Spektralsensor (Lichtfarbe, Tageslicht vs. Lampe)
- Lage- und Bewegungssensor (merkt, wenn er hochgehoben oder umgedreht wird)

## Schnittstellen für Zubehör
- I2C-Buchsen (Qwiic/STEMMA QT) außen am Würfel zum Einstecken von Sensoren
- USB-Hub, weil der einzige USB-Anschluss des Zero vom LTE-Modem belegt ist
- Bluetooth LE für kabelloses Zubehör
- Magnetische Kontakte (Pogo-Pins) für aufsteckbare Module

## Aus Marvins früheren Projekten (GitHub, 16.10.2026)
- **Pflanzen-Doktor:** Marvin hält eine Pflanze vor die Handykamera. Schlaubi schickt auf Frage ein Einzelbild an Claude und nimmt Luftfeuchte, Temperatur und Licht vom Würfel dazu. Vorbild: Dr. Greenthumb, Marvins Abschlussprojekt im Bootcamp. Das alte Tomaten-Modell wird nicht übernommen. Es kennt nur Laborfotos von Tomatenblättern, und die App liest die Klassen um eins verschoben aus. (S)

## Aus dem Gemini-Brainstorming (16.10.2026)
Einordnung und Widersprüche: `docs/ideen-gemini-brainstorming.md`.
- **Pfeifsprache wie R2-D2:** Triller und Pfeiftöne über den Summer, ergänzend zu den kurzen Tönen aus Design Charakter. (S)
- **NFC-Karten (PN532):** Karte auflegen schaltet einen Modus frei, z. B. Recherche oder Lernmodus. Pins und Bus vorher gegen die Pinbelegung prüfen. (S)
- **Gesten mit dem Abstandssensor:** z. B. Hand wischen statt „Schlaubi, fertig“. Baut auf Anwesenheit (Bauplan Körper 9.4) auf. (S)
- **Flüster-Modus:** Lautstärke oder Kanal (Kopfhörer, Telegram) je nach Umgebungslautstärke. (S)
- **Signierte Messblöcke (Ed25519):** ergänzt Hash-Kette und Anker im Event-Log um eine Signatur des Würfels. (S)
- **Austausch mit anderen Würfeln ohne Cloud:** Datenschutz und Sicherheit vorher klären, verwandt mit „Wissen teilen“. (S)

## Aus früheren Entscheidungen (Version 2)
- Display mit Gesicht (Design Körper)
- MCP-Schnittstelle: Schlaubi auf jedem Laptop derselbe (Design Gehirn 11a)
- Wissen teilen mit Gästen und anderen Schlaubis (Notion „Idee: Wissen und Fähigkeiten teilen“)
- Anbieter-Schicht für andere Modelle und EU-Anbieter (Design Gehirn 11b)
- Bilder in der Datensammlung (Design Daten)

## Quellen
- https://docs.arducam.com/Raspberry-Pi-Camera/Tof-camera/TOF-Camera/
- https://uk.robotshop.com/products/orbbec-femto-bolt-3d-vision-device
- https://shop.luxonis.com/pages/pricing-change-oak-lite-oak-1
- https://runtimewire.com/article/cognex-buy-realsense-500m-intel-spinout
- https://github.com/pierrep/ofxLibFreenect2/blob/master/README.md
