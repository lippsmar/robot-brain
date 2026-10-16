---
name: paket-abschluss
description: "Schließt ein Arbeitspaket in robot-brain ab: alle Prüfungen, Code-Prüfung, Skill-Zips, ein Commit, Push und ein Notion-Eintrag. Nur auf Marvins oder Claudes ausdrücklichen Aufruf am Ende eines Pakets."
disable-model-invocation: true
---

# Paket abschließen (robot-brain)

Regeln aus CLAUDE.md §3 (16.10.2026): ein Commit und ein Notion-Eintrag pro Paket, Code-Prüfung und volle Fehler-Einbau-Prüfung einmal pro Paket. Befunde gegen den Code prüfen, nicht blind übernehmen.

## Ablauf
1. **Prüfen:** `tools/dev/pruefen.sh --voll` (pytest, ruff und mypy gleichzeitig, danach alle eingebauten Fehler). Ohne `--voll` nur geänderte Dateien, für Zwischenstände.
2. **Code-Prüfung:** Skill `code-review` auf den Diff des Pakets. Jeden Befund am Code nachvollziehen. Behobene Befunde bekommen einen Test und, wo sinnvoll, einen eingebauten Fehler in `brain/tests/mutations.json`. Begründet abgelehnte Befunde im Commit und im Projektlog nennen.
3. **Nach Änderungen** aus Schritt 2: Schritt 1 noch einmal, ohne `--voll` reicht, wenn nur die geänderten Dateien betroffen sind.
4. **Skill-Zips:** Für jeden geänderten Ordner unter `skills/` die Zip neu packen: `cd skills && zip -qrX ../dist/skills/<name>.zip <name>`. In `skills/INDEX.md` vermerken, dass er in Claude hochzuladen ist (https://claude.ai/customize/skills).
5. **Doku:** README-Stand (Testzahl, eingebaute Fehler), Bauplan-Häkchen, offene Punkte in CLAUDE.md, Lessons in `docs/claude-optimierung.md`, wenn etwas schiefging.
6. **Commit und Push:** ein Commit mit allem, deutsche Nachricht, Zahlen aus Schritt 1, Zeilen zur Mitwirkung laut System-Hinweis. `git push -u origin main`, bei Netzfehlern bis zu viermal mit 2, 4, 8, 16 s Pause.
7. **Notion:** ein Eintrag am Ende von „Entscheidungen und Projektlog“ (Seite 3f80298a4d3b81f8abffd4d9b73583f3) mit dem echten Commit-Hash (aus `git log --oneline -1`, nie aus dem Gedächtnis). Neue Entscheidungen von Marvin zusätzlich als Zeile in die ADR-Tabelle.
8. **Bericht an Marvin:** kurz, Ergebnis zuerst, was er tun muss (z. B. Skill hochladen), am Ende genau eine Frage.

## Nicht
- Keine Schritte überspringen, um Zeit zu sparen. Schneller wird es durch das gleichzeitige Prüfen, nicht durch Weglassen.
- Keine Zahlen berichten, die nicht aus einem frischen Lauf stammen.
