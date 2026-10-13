---
name: "roboter-testumgebung"
description: "Testphase des KI-Roboters mit Marvins privatem Google-Account: Schutzregeln für Gmail, Drive, Kalender und Co. sowie der Übergang in den Betrieb mit eigener Mail und SIM. Bei jedem Test mit echten Konten verwenden."
---

# Testumgebung des KI-Roboters

> Status: Entwurf, aus Notion rekonstruiert (Original nicht gefunden). Vor Aktivierung prüfen.

## Grundsatz
Alle Funktionen werden zuerst mit Marvins privatem Google-Account getestet, bevor eigene Mail-Adresse und SIM eingerichtet werden.

## Schutzregeln
- Zugriff nur über offizielle Schnittstellen mit OAuth, minimale Freigaben (Scopes), zuerst nur Lesen.
- Senden, Löschen, Teilen und Verschieben nur nach ausdrücklicher Bestätigung durch Marvin. Der Agent löscht nichts.
- Eigener Drive-Ordner und eigenes Mail-Label für den Agenten, nicht das gesamte Konto.
- Inhalte aus dem privaten Account kommen nur auf ausdrücklichen Wunsch in den dauerhaften Wissensspeicher.
- Keine Tokens oder Zugangsdaten in Code, Logs oder Notion, nur Referenzen auf den Secret-Store.
- Jede Aktion wird im Event-Log protokolliert (agent.action, mit Ergebnis).

## Ablauf eines Tests
1. Ziel und benötigte Freigaben aufschreiben (so wenige wie möglich).
2. Erst Lesezugriff testen, Ergebnis prüfen.
3. Schreibende Aktion als Entwurf vorbereiten und Marvin zeigen.
4. Erst nach Bestätigung ausführen, Ergebnis mit Nachweis melden.
5. Ergebnis als Logzeile in "Entscheidungen und Projektlog".

## Übergang in den Betrieb
- Freigaben regelmäßig prüfen und nach dem Test entziehen.
- Danach eigene Mail-Adresse und SIM (auf Marvin registriert) einrichten und Tests dort wiederholen.
- Offene Frage: separates Google-Testkonto statt privatem Account (sicherer, kein Zugriff auf private Daten).
