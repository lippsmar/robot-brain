# Design Umgebungsbewusstsein und Datensammlung – Version 1

Stand 14.10.2026. **Zur Freigabe durch Marvin.** Spiegel der Notion-Seite „Idee: Umgebungsbewusstsein und Datensammlung“, dort stehen Herleitung und Recherche.

## 1. Zweck
Schlaubi soll seine Umgebung so gut wie möglich verstehen, Muster in Marvins Alltag erkennen und später mit den Daten eigene Modelle trainieren. Gesammelt wird, was nicht personenbezogen ist oder nur Marvin betrifft.

## 2. Ziele (Version 1)
- **Geräusche** auswerten: Lautstärke, Geräuschklassen (z. B. Regen, Kaffeemaschine, Verkehr, Musik), ob gesprochen wird und ungefähr wie viele Stimmen.
- **Gesprochenes** verarbeiten:
  - nur von Marvin
  - aus Gesprächen, bei denen alle Beteiligten zugestimmt haben (sichtbar angezeigt)
  - öffentlich Gesprochenes wie Durchsagen, Radio, Fernsehen, öffentliche Vorträge
- **Messwerte** jede Minute:
  - Zuluft-Temperatur (BMP280)
  - Abluft-Temperatur, Luftfeuchte, Luftdruck (BME280)
  - Helligkeit (BH1750)
  - Chip-Temperatur und Drosselung des Pi
  - Modem-Temperatur
  - Akku, Funk
- **Kontext:** grober Ort (zu Hause, Büro, Café, z. B. anhand des WLANs), Tageszeit, Gerätezustand.
- **Kühlung überwachen:** Unterschied zwischen Zuluft und Abluft, zusammen mit Chip- und Modemtemperatur. Warnung ab 70 °C oder bei Drosselung.
- **Bewusste Aufnahmen** auf Marvins „Nimm das auf“, nur ohne andere Menschen.
- Gesammelt wird **immer, wenn der Würfel an ist**.

## 3. Nicht-Ziele (Version 1)
- **Bilder in der Datensammlung:** kommen später. Die Kamera bleibt in Version 1 nur bei Bedarf an.
- **Gespräche anderer:** Sie werden weder mitgehört noch ausgewertet, auch nicht anonymisiert (§ 201 StGB). Das ist eine feste Grenze.
- **Keine Stimmprofile Fremder**, keine Emotionserkennung aus Stimmen.
- **Kein Verkauf von Daten** ohne eigene Entscheidung (siehe Abschnitt 8).

## 4. Grenzen und Regeln
- **Merkmale statt Rohdaten:** Der Würfel bzw. das Gehirn wertet aus und speichert Ergebnisse, nicht Rohton.
- **Sprache:** Erkennt die lokale Sprechererkennung nicht Marvin und gibt es keine Zustimmung, wird Sprache sofort verworfen. Der Puffer für das Aktivierungswort bleibt nur Sekunden im Arbeitsspeicher.
- **Muster über Marvin** sind personenbezogen:
  - Markierung `pii: true`
  - nur lokal
  - jederzeit einsehbar und löschbar
- **An Claude** gehen nur Zusammenfassungen, wenn Schlaubi im Gespräch darauf zugreift. Rohdaten gehen nie in die Cloud.
- **Trainingsdaten** für eigene Modelle sind nur Daten ohne Personenbezug.

## 5. Ablage
- **Data Lake (L5)** im Memory Core:
  - Zeitreihen mit Zeit, Gerät, Kanal, Wert, Einheit und Qualität
  - Geräuschklassen mit Zeit und Sicherheit
  - Manifest mit PII-Status
- **Beschriftungen** durch Marvin, z. B. „Das war Regen“. Sie verbessern später eigene Modelle.
- **Aufbewahrung (Marvin, 14.10.2026):**
  - Messwerte und Geräuschklassen: für immer (wenig Speicher, grob einige Dutzend Megabyte pro Jahr)
  - bewusste Aufnahmen: gelten als gemerkt und bleiben
  - Sicherung wie das übrige Gedächtnis

## 6. Verwendung
- **Umgebung verstehen:** Schlaubi weiß, wo er ist, wie laut, hell und warm es ist und ob die Kühlung reicht.
- **Muster:** z. B. wann Marvin wo arbeitet, wie laut es dabei ist und wann Gespräche gut laufen. Schlaubi nutzt das für Hinweise und seine Laune.
- **Laune:** Temperatur, Lärm, Akku und Licht sind Laune-Faktoren (Design Charakter).
- **Später eigene Modelle**, z. B. ein Geräusch-Erkenner für Schlaubis Alltag oder eine Vorhersage von Temperatur und Akkulaufzeit.

## 7. Hardware (Ergänzung zum Design Körper)
- BME280 an der Abluft (0x77), BMP280 an der Zuluft (0x76), BH1750 (0x23).
- Software-I2C an GPIO22/23, weil GPIO3 der Taster ist.
- Teileliste Version 1 jetzt ca. 166–269 €. Details: Bauplan Körper Phase 8a.

## 8. Können die Daten Geld für den Selbsterhalt bringen? (Einschätzung)
**Ehrliche Antwort: Rohdaten eines einzelnen Würfels sind wenig wert.**
- **Verkauf von Sensordaten:** Für einzelne Geräte gibt es praktisch keinen Markt. Wetterdienste nehmen Daten von Außenstationen, nicht von einem Würfel im Café.
- **Datensätze für maschinelles Lernen**, z. B. Geräusche aus Büro und Café:
  - Gibt es schon in großer Menge kostenlos.
  - Rechtlich heikel, sobald irgendwo Sprache enthalten ist.
  - Kaum verkäuflich.

**Wo die Daten tatsächlich Wert haben:**
1. **Sparen statt verdienen (der größte Hebel):**
   - Ein eigener lokaler Geräusch-Erkenner oder einfache Muster ersparen Aufrufe an Claude.
   - Gelernte Gewohnheiten helfen, Recherche und Gespräche günstiger zu takten.
   - Jeder gesparte Aufruf ist Budget.
2. **Inhalte über das Projekt selbst:**
   - Messreihen zu Strom, Wärme und Kühlung eines Pi Zero im Holzwürfel, dazu der Bauweg von Schlaubi.
   - Das ist Stoff für Bauanleitungen, Artikel oder Videos, die Marvin veröffentlichen oder verkaufen kann.
   - Passt zur beschlossenen „Zuarbeit“ (Schlaubi bereitet vor, Marvin prüft und verkauft).
3. **Eigene Modelle später:** Ein gut trainierter, kleiner Geräusch-Erkenner oder ein Kühlungsmodell für Pi-Gehäuse könnte als Open Source mit Spendenmöglichkeit oder als Teil eines Bausatzes Wert haben. Nur mit Trainingsdaten ohne Personenbezug.
4. **Bürgerwissenschaft** (z. B. Lärm- oder Luftmessnetze): bringt kein Geld, aber Sichtbarkeit. Nur Außenwerte sind dort sinnvoll.

Alle Verwertungen laufen über Marvin, nach deutschem Recht, mit Einzelfreigabe (Selbsterhalt-Regeln aus dem Design Gehirn). In Version 1 wird nur gesammelt und gespart, nicht verkauft.

## 9. Risiken und frühe Tests
1. **Sprache wird nicht zuverlässig verworfen:** Test mit Gesprächen zweier anderer Personen (mit deren Einverständnis). Bestanden, wenn kein Wortlaut und keine Themen gespeichert werden.
2. **Geräusch-Erkenner zu schwer für den Zero:** Läuft er auf dem Pi oder nur auf dem Laptop? Messen. Auf dem Laptop gilt: nur Merkmale übertragen, kein Rohton.
3. **Temperaturmessung verfälscht durch Abwärme:** Abgleich beider Sensoren vor dem Einbau (Bauplan 8a.4).
4. **Speicher:** tatsächliche Datenmenge nach einem Monat prüfen.

## 10. Offene Punkte
- Software für die Geräuschklassen auswählen und nach Checkliste prüfen (Lizenz, Datenschutz, lokal lauffähig)
- Wie Schlaubi die Zustimmung aller Beteiligten bei Gesprächen einholt und anzeigt
- Bilder in einer späteren Version
