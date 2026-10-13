---
name: "roboter-brainstorming-plan"
description: "Vor jedem neuen Feature, Bauteil oder Umbau am KI-Roboter: erst klären, was Marvin wirklich will, Design schreiben und freigeben lassen, dann einen kleinschrittigen Plan erstellen."
---

# Brainstorming und Plan für den KI-Roboter

Angepasst aus den Skills brainstorming und writing-plans von obra/superpowers (MIT-Lizenz, Copyright (c) 2025 Jesse Vincent). Entscheidungsbaum und Faktensuche angepasst aus dem Skill grilling von mattpocock/skills (MIT-Lizenz, Copyright (c) 2026 Matt Pocock).

## Erst prüfen: Was ist bekannt?
- Alles Wichtige steht in der Anfrage: direkt umsetzen und sagen, was gemacht wurde.
- Etwas Wesentliches fehlt: Gespräch beginnen. Marvin kann jederzeit sagen, dass er ohne Fragen loslegen will.

## Gespräch
- Pro Nachricht genau eine offene Frage, ohne Antwortliste. Klare, einfache Sprache.
- Konkret fragen: "Wann hast du dir das zuletzt gewünscht?", "Was würde dich stören, wenn es falsch läuft?"
- Klären: Zweck, Erfolg, Nicht-Ziele, was es auf keinen Fall tun darf, vorhandene Teile, Budget, welche Entscheidungen Marvin selbst treffen will.
- Offene Entscheidungen als **Entscheidungsbaum** führen: Jede Entscheidung hat Folgeentscheidungen, die erst nach ihr sinnvoll sind. Immer die Frage stellen, deren Voraussetzungen schon geklärt sind. Nichts stillschweigend annehmen.
- **Fakten selbst nachschlagen**, Entscheidungen Marvin überlassen: Was in Notion, im Repo, in Datenblättern oder in der Doku steht, selbst suchen statt Marvin zu fragen. Nur echte Entscheidungen (Wünsche, Budget, Abwägungen) gehen an ihn.
- Eigene Annahmen als Annahmen kennzeichnen, nie als Marvins Entscheidung ausgeben.
- Zwischendurch in 200 bis 300 Wörtern zurückspiegeln und fragen, was fehlt oder falsch ist.
- Ein schneller Wegwerf-Prototyp ist erlaubt, wenn Marvin zustimmt. Er bleibt Wegwerf.
- Das Gespräch ist fertig, wenn im Entscheidungsbaum keine offene Frage mehr übrig ist und Marvin bestätigt, dass das Verständnis stimmt.

## Größe festlegen
- Kleine Aufgabe: direkt machen.
- Kleine Änderung: Beschreibung im Chat, nach Freigabe bauen.
- Projekt: schriftliches Design als Unterseite unter "Robot Brain" in Notion (Zweck, Ziele, Nicht-Ziele, Einschränkungen, Marvins Entscheidungen, offene Punkte).

## Freigabe-Sperre
Nichts wird gebaut, bestellt, installiert oder verdrahtet, bevor Marvin die Beschreibung oder das Design freigegeben hat. Lesen und Recherchieren ist erlaubt.

## Plan schreiben (nach Freigabe)
- Kopf: Ziel in einem Satz, Architektur in zwei bis drei Sätzen, Technik, Link zum Design, globale Vorgaben (Pins, Spannungen, Versionen, Budget).
- Aufgaben so klein, dass jede einzeln prüfbar ist. Pro Schritt eine Aktion mit prüfbarem Ergebnis: Test oder Messung schreiben, ausführen (schlägt fehl), umsetzen, erneut prüfen (besteht), festhalten.
- Für Hardware: Messpunkte, erwartete Werte und Sicherheitsprüfung (Strom, Not-Aus) als eigene Schritte.
- Selbstprüfung: Jede Anforderung hat eine Aufgabe? Namen und Schnittstellen einheitlich? Keine Platzhalter wie "TBD"? Plan nicht länger als nötig?
- Plan in Notion ablegen, Marvin lesen lassen und erst nach Bestätigung umsetzen.