---
name: "roboter-debugging"
description: "Systematisches Debugging und Nachweis vor Erfolgsmeldung für Hardware und Software des KI-Roboters (Pi, Modem, Sensoren, OpenClaw, Python). Bei jedem Fehler, Ausfall oder unerwartetem Verhalten."
---

# Roboter-Debugging

Angepasst aus den Skills systematic-debugging und verification-before-completion von obra/superpowers (MIT-Lizenz, Copyright (c) 2025 Jesse Vincent).

## Grundregel
Keine Reparatur ohne Ursache. Keine Erfolgsmeldung ohne frischen Nachweis.

## Phase 1: Ursache finden
1. Fehlermeldungen und Logs vollständig lesen (journalctl, dmesg, Event-Log des Memory Core).
2. Reproduzieren: genaue Schritte, tritt es immer auf?
3. Letzte Änderungen prüfen: Code, Config, Pakete, Verkabelung, Stromversorgung.
4. Bei mehreren Komponenten an jeder Grenze messen, was hinein- und herausgeht: Sensor → Microcontroller → Pi Zero → Message Bus → Gehirn-Rechner → API. So zeigt sich, an welcher Stelle es bricht.
5. Hardware-Klassiker zuerst ausschließen: Strom (Modem-Spitzen bis ca. 2 A, Brownout-Neustarts), Masse, Pegel 3,3 V/5 V, I2C-Adresse und Pull-ups, UART-Baudrate, SIM-Netz/Empfang, SD-Karte.

## Phase 2: Muster
- Funktionierendes Gegenbeispiel suchen und Unterschiede vollständig auflisten.
- Referenz (Datenblatt, Doku, Beispielcode) komplett lesen, nicht überfliegen.

## Phase 3: Hypothese
- Eine Hypothese aufschreiben: "X ist die Ursache, weil Y."
- Kleinste mögliche Änderung, eine Variable auf einmal.
- Nicht bestätigt: neue Hypothese, keine Fixes stapeln.
- Unklar: offen sagen und nachfragen oder recherchieren.

## Phase 4: Reparieren
- Erst einen reproduzierenden Test oder ein Prüfskript schreiben, dann eine einzige Änderung.
- Nach drei gescheiterten Fixes stoppen und mit Marvin die Architektur hinterfragen.
- Keine physischen Aktionen (Motoren, Relais) zum Testen ohne Freigabe.

## Nachweis vor jeder Erfolgsmeldung
1. Welcher Befehl oder Test beweist die Aussage?
2. Frisch und vollständig ausführen.
3. Ausgabe und Exit-Code lesen.
4. Nur melden, was die Ausgabe belegt, mit Beleg. Sonst den echten Stand nennen.
Warnzeichen: "sollte", "wahrscheinlich", "müsste jetzt gehen", Erfolg melden ohne Test, Agentenberichten blind vertrauen.

## Dokumentieren
Ursache, Fix und Nachweis als Logzeile in "Entscheidungen und Projektlog" in Notion.