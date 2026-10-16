# Vergleich Such-APIs für Schlaubis Recherche (Bauplan Gehirn 13.1)

Stand 16.10.2026. Recherche durch einen Prüf-Agenten, die wichtigsten Angaben von Claude an der Primärquelle nachgeprüft (markiert mit „nachgeprüft“). Nichts angemeldet, kein Konto angelegt. **Auswahl trifft Marvin.**

## Vorgaben
- Recherche-Topf höchstens etwa 9,63 € im Monat (inklusive Modell-Kosten), grob 100–1.000 Suchen.
- Schlaubi gibt sich als Bot zu erkennen. Keine Dienste, die Google- oder Bing-Ergebnisse abkratzen (z. B. SerpAPI, Serper), kein SearXNG mit Kratz-Engines.
- Bevorzugt EU, wenig Logging, AVV möglich.
- **Wichtig:** Wir legen Fakten mit Quellen-URL im Gedächtnis ab. Die Bedingungen müssen das Speichern erlauben.

## Ergebnis kurz
1. **Staan** (European Search Perspective, Qwant und Ecosia, Paris): eigener europäischer Index, 2 € pro 1.000 Anfragen, die ersten 1.000 im Monat frei (nachgeprüft). Daten laut Anbieter unter EU-Recht in EU-Rechenzentren (nachgeprüft). US-Rückfall laut FAQ abschaltbar, AVV auf Anfrage. **Offen:** ob Ergebnisse gespeichert werden dürfen; die Bedingungen gibt es erst bei der Registrierung. Ein Ausgabenlimit fehlt, das zählt unser Budget-Wächter.
2. **Mojeek** (UK, eigener Index, Crawler beachtet robots.txt): Startup 2 £, Business 3 £ pro 1.000 (nachgeprüft). Business mit Speicherrechten „indefinite data retention“ (nachgeprüft). Die Seite ist bei Startup widersprüchlich (FAQ: 1 Stunde Cache), also schriftlich bestätigen lassen. Infrastruktur in Europa, Mojeek ist Auftragsverarbeiter (nachgeprüft). Anfragen werden 90 Tage gespeichert, ohne Speicherung auf Anfrage. Deutsch vermutlich schwächer.
3. **Web-Suche der Claude-API**: 10 $ pro 1.000 Suchen plus Token für die Ergebnisse. Läuft über den vorhandenen API-Key, aber USA (keine EU-Option) und spürbar teurer. Nur als Rückfall.

## Nicht geeignet
- **Brave Search API**: Bedingungen 3(b)(i) verbieten „store, cache, or create a database of Search Results“ außer kurzem Zwischenspeichern (nachgeprüft). Speicherrechte nur per gesondertem Vertrag. Damit wäre unsere Wissensablage nicht erlaubt.
- **Tavily**: Anfragen dürfen laut Bedingungen aufbewahrt und für Training genutzt werden.
- **Exa**: weitgehende Lizenz an Ein- und Ausgaben, Kopieren der Inhalte eingeschränkt.
- **Kagi**: Speichern verboten, 12 $ pro 1.000.
- **Google Custom Search JSON API**: für neue Kunden geschlossen. **Bing Search API**: am 11.8.2025 abgeschaltet.
- **Marginalia** (Schweden, frei für nicht kommerzielle Nutzung, Ergebnisse CC-BY-NC-SA): kleiner Index, höchstens als Ergänzung. **You.com**: Bedingungen ungeprüft.

## Empfehlung
Staan als Hauptquelle, Mojeek Business als zweite Quelle mit sicheren Speicherrechten, Claude-Web-Suche nur als Rückfall. Vor der Entscheidung:
1. Marvin registriert sich bei Staan (kostenlos bis 1.000 Anfragen) und gibt Claude die Nutzungsbedingungen zum Lesen. Dann prüfen: Speichern erlaubt? US-Rückfall aus? AVV?
2. Mojeek: Speicherrechte im Business-Plan schriftlich bestätigen lassen.
3. 10–20 deutsche Testfragen an beide, Treffer vergleichen.
Anmeldungen und Verträge macht Marvin (nichts in seinem Namen ohne ihn).

## Quellen (gelesen am 16.10.2026)
- https://staan.ai, https://staan.ai/faq, https://staan.ai/privacy-policy
- https://www.mojeek.com/services/search/web-search-api/
- https://api-dashboard.search.brave.com/terms-of-service
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool
- https://www.tavily.com/terms, https://exa.ai/terms, https://kagi.com/api/pricing
- https://developers.google.com/custom-search/v1/overview
- https://learn.microsoft.com/en-us/lifecycle/announcements/bing-search-api-retirement
- https://about.marginalia-search.com/article/api/
