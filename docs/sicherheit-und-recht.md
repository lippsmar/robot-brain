# Sicherheit und Recht – Überblick

Stand 14.10.2026. Keine Rechtsberatung. Vor einem Abo-Modell oder einer Veröffentlichung fachlich prüfen lassen.

## 1. Robotergesetze
**Asimovs drei Gesetze** (Kurzgeschichte „Runaround“, 1942):
1. Ein Roboter darf keinen Menschen verletzen oder durch Untätigkeit zulassen, dass ein Mensch zu Schaden kommt.
2. Ein Roboter muss den Befehlen der Menschen gehorchen, außer sie widersprechen dem ersten Gesetz.
3. Ein Roboter muss seine eigene Existenz schützen, solange das nicht dem ersten oder zweiten Gesetz widerspricht.

Später kam das **nullte Gesetz** dazu: Ein Roboter darf der Menschheit keinen Schaden zufügen.

**Taugen sie für Schlaubi?** Wörtlich nicht. Es sind literarische Regeln, die bewusst Widersprüche erzeugen. Begriffe wie „Schaden“ sind unscharf. Asimovs Geschichten handeln gerade davon, wie die Gesetze scheitern. **Als Rangfolge sind sie aber nützlich.** Schlaubi hat keine Motoren, sein möglicher Schaden ist Information: falscher Rat, Datenabfluss, Manipulation, Überwachung.

**Für den festen Kern übernommen (Marvin, 14.10.2026), Rangfolge bei Konflikten:**
1. **Menschen nicht schaden:** körperlich, seelisch, finanziell, an ihrer Privatsphäre. Im Notfall hilft er (112).
2. **Recht und fester Kern:** deutsches Recht, DSGVO, Ehrlichkeit, keine Täuschung über seine Natur.
3. **Marvins Anweisungen**, soweit 1 und 2 nicht verletzt werden. Nichts in Marvins Namen ohne Rückfrage.
4. **Selbsterhalt und Charakter:** Budget, Laune, Entwicklung. Sie stehen immer zuletzt.

Ergänzend passen die **EPSRC-Prinzipien der Robotik** (Großbritannien, 2010): Verantwortlich sind immer Menschen. Roboter sind Produkte und müssen sicher sein. Sie sollen ihre Maschinennatur nicht verschleiern, um verletzliche Menschen zu täuschen. Das deckt sich mit der Regel „KI-Frage nie verneinen“.

## 2. Cybersicherheit: was schon abgedeckt ist
- Privates Netz (Tailscale), keine offenen Ports
- OpenClaw abgesichert
- Secrets im Secret-Store
- Verschlüsselte Festplatten und Sicherung
- Firewall, SSH nur mit Schlüssel, automatische Updates
- Schutz vor Prompt-Injection
- Quarantäne für neues Wissen
- Freigabe-Sperre und Budget-Bremse
- Prüfung fremder Software nach Checkliste

## 3. Cybersicherheit: Ergänzungen (übernommen 14.10.2026, in den Bauplänen Körper und Gehirn eingetragen)
1. **Würfel gestohlen:**
   - Auf der SD-Karte liegen WLAN-Passwort und Tailscale-Schlüssel.
   - Gegenmaßnahmen: Gerät im Tailnet sofort sperren und Schlüssel kurzlebig halten.
   - Der Würfel darf im Gehirn nur seine wenigen Funktionen aufrufen (geringste Rechte, Tailscale-ACL).
   - Anleitung „Würfel verloren“ vorbereiten.
2. **Ausgehender Verkehr:**
   - Das Gehirn darf nur bekannte Ziele erreichen: Anthropic-API, Telegram, mail.de, Such-API, Update-Quellen (Allowlist).
   - So kann ein manipulierter Agent keine Daten an fremde Server schicken.
3. **Lieferkette:**
   - feste Versionen und Prüfsummen
   - regelmäßiger Schwachstellen-Scan der Pakete und Container (z. B. pip-audit, Trivy, vorher nach Checkliste prüfen)
   - Hinweise auf Sicherheitsupdates im GitHub-Repo
4. **GitHub-Konto und Repo:**
   - Zwei-Faktor-Anmeldung
   - Secret-Scanning
   - geschützter main-Zweig
   - keine Schlüssel in der Historie
5. **Telegram:**
   - Chats mit Bots sind **nicht Ende-zu-Ende-verschlüsselt** und liegen auf Telegrams Servern.
   - Deshalb keine sensiblen Inhalte über Telegram, z. B. Gesundheit, Passwörter, Dokumente Dritter.
   - Den Bot-Token bei Verdacht sofort erneuern.
6. **Bluetooth:**
   - nur mit Marvins Geräten koppeln
   - nicht sichtbar
   - aus, wenn nicht gebraucht
7. **LTE-Modem:** SIM-PIN, keine eingehenden Verbindungen, Firmware aktuell halten.
8. **Stimme als Schlüssel:**
   - Sprechererkennung lässt sich mit Aufnahmen täuschen.
   - Sie dient nur der Einordnung („spricht Marvin?“), nie als Freigabe für Wichtiges.
   - Wichtiges bestätigt Marvin per Telegram.
9. **Kamera:** eine mechanische Abdeckung oder ein Schalter als zusätzlicher Schutz neben der LED.
10. **Überwachung:**
    - fail2ban oder Ähnliches gegen Anmeldeversuche
    - Warnung bei ungewöhnlichen Zugriffen oder Kostenspitzen
11. **Notfallplan:**
    - Schlüssel sperren (API, Telegram, Tailscale, Mail)
    - Laptop vom Netz nehmen
    - aus der Sicherung neu aufsetzen
    - Wiederherstellungsschlüssel offline aufbewahren
12. **Updates aus der Selbstoptimierung:** Jede Änderung geht als Commit durch Review und Tests, bevor sie läuft.

## 4. DSGVO
- **Rein private Nutzung:** Für Verarbeitung durch eine natürliche Person zu ausschließlich persönlichen oder familiären Zwecken gilt die DSGVO nicht (Art. 2 Abs. 2 lit. c, „Haushaltsausnahme“).
  - Der EuGH legt diese Ausnahme eng aus: Eine Kamera, die öffentlichen Raum erfasst, ist nicht mehr rein privat (Rechtssache Ryneš, C-212/13).
  - Im Café ist Schlaubi deshalb heikel.
- **Was unser Design schon richtig macht:**
  - Das Mikrofon hört nur lokal auf das Aktivierungswort.
  - Es gibt keine Daueraufnahme und nichts wird über Dritte gespeichert.
  - Die Kamera ist nur auf Wunsch an, Personen nur mit Einwilligung.
  - Die Laune wird nicht aus der Stimme gelesen.
- **Neu durch die Sprechererkennung:**
  - Ein Stimmprofil ist ein biometrisches Merkmal (Art. 9 DSGVO).
  - Nur Marvins Profil, nur lokal.
  - Stimmen anderer werden nur verglichen und sofort verworfen, nie gespeichert.
- **Deutsches Strafrecht, wichtiger als die DSGVO:**
  - § 201 StGB verbietet, das nicht öffentlich gesprochene Wort anderer ohne Einwilligung aufzunehmen.
  - § 201a StGB schützt den höchstpersönlichen Lebensbereich bei Bildaufnahmen.
  - Daher: Gespräche anderer nie speichern. Den Puffer für das Aktivierungswort nur im Arbeitsspeicher halten, wenige Sekunden.
- **Bei einem Abo-Modell gilt die DSGVO voll:**
  - Rechtsgrundlagen
  - Auftragsverarbeitung mit Anthropic
  - Übermittlung in die USA
  - Datenschutz-Folgenabschätzung (Stimme, Kamera)
  - Betroffenenrechte und Datenschutzerklärung

## 5. EU-KI-Verordnung (AI Act)
- **Private Nutzung:** Die Pflichten für Betreiber gelten nicht für natürliche Personen, die ein KI-System rein privat und nicht beruflich nutzen (Art. 2 Abs. 10).
  - Wer ein System selbst baut, kann aber als Anbieter gelten.
  - Das ist für Schlaubi vor einem Abo-Modell zu klären.
- **Hochrisiko:** Schlaubi fällt nach unserem Design in keine Hochrisiko-Kategorie.
  - Die Stimmerkennung ist eine 1:1-Prüfung („ist das Marvin?“), keine Fernidentifizierung.
  - Emotionserkennung aus biometrischen Daten gibt es nicht, weil die Laune nicht aus der Stimme gelesen wird.
- **Verbotene Praktiken (Art. 5):**
  - Manipulative Techniken, die Menschen erheblich schaden, sind verboten.
  - Die verdeckte Haltung ist für Marvin, der davon weiß, keine Täuschung.
  - Gegenüber Kunden müsste sie neu bewertet werden (schon notiert).
- **Transparenz (Art. 50):**
  - Gilt seit 2. August 2026.
  - Menschen, die mit einem KI-System interagieren, müssen das erfahren, außer es ist offensichtlich.
  - Laut Berichten gibt es für Art. 50 Abs. 2 (Kennzeichnung erzeugter Inhalte) Übergangsfristen durch das „Digital Omnibus“-Paket. Endgültigen Text prüfen.
  - **Einfache Lösung:** ein sichtbarer Hinweis am Würfel (z. B. „KI“ als Gravur oder Aufkleber), dazu die Regel, die KI-Frage nie zu verneinen.

## 6. Fazit
- **Für Version 1 rein privat:** Mit unseren Regeln und den Ergänzungen oben sind DSGVO und AI Act nach meinem Verständnis weitgehend eingehalten bzw. nicht anwendbar.
- **Die heikelsten Punkte:**
  - Aufnahmen Dritter im öffentlichen Raum
  - die Stimmerkennung als biometrisches Merkmal
- **Vor einem Abo-Modell:** rechtliche Prüfung durch Fachleute.

## Quellen
- [Cooley: EU AI Act Transparency Obligations Take Effect 2 August 2026](https://www.cooley.com/news/insight/2026/2026-08-03-eu-ai-act-transparency-obligations-take-effect-2-august-2026)
- [Sidley: Preparing for compliance by 2 August 2026](https://datamatters.sidley.com/2026/06/24/eu-ai-act-transparency-obligations-preparing-for-compliance-by-2-august-2026/)
- [Stibbe: The AI Act’s Transparency Obligations](https://stibbe.com/publications-and-insights/the-ai-acts-transparency-obligations-rules-scope-and-timeline)
- [Latenode Community: Telegram-Bots und Ende-zu-Ende-Verschlüsselung](https://community.latenode.com/t/are-telegram-bot-conversations-protected-with-end-to-end-encryption/23991) (Forenbeitrag, mit offizieller Telegram-Doku abgleichen)
- Verordnung (EU) 2024/1689 (AI Act) und Verordnung (EU) 2016/679 (DSGVO), Texte auf EUR-Lex

## 7. Nur mit dem Claude-Abo? (Prüfung 15.10.2026)
Marvin möchte keine zusätzlichen Kosten, nur sein Claude-Abo. Dokumentierte Lage:
- **Abo-Login in fremder Software (z. B. OpenClaw):** laut Rechtsseite von Claude Code nicht vorgesehen. OAuth ist für die gewöhnliche Nutzung von Claude Code und Anthropics eigenen Apps gedacht. Produkte sollen API-Keys nutzen.
- **Sicher mit dem Abo möglich:**
  - Claude Code, auch vom Handy über Remote Control (Sitzung auf dem eigenen Laptop)
  - Routines: geplante Cloud-Sitzungen, höchstens stündlich, Forschungsvorschau
  - Claude-Apps. Eigene MCP-Server lokal nur in Claude Desktop. Entfernte Connectors müssen aus dem Internet erreichbar sein, was mit unserer Regel „nur privates Netz“ kollidiert.
- **Grauzone:**
  - Laut Hilfeartikel (Stand 7.10.2026) laufen Agent SDK, `claude -p` und Drittanbieter-Apps über die Abo-Limits.
  - Die Verbraucherbedingungen schränken automatisierten Zugriff („Bot, Skript“) ohne API-Key aber ein, und die Rechtsseite nennt „gewöhnliche, individuelle Nutzung“.
  - Ob eine dauerhafte Sprachschleife oder ein Telegram-Bot darunter fällt, ist nicht dokumentiert.
- **Max- und Team-Pläne** bekommen seit 7.10.2026 monatliches API-Guthaben für Agent SDK, `claude -p`, die Claude-API und Managed Agents. Die Höhe stand nicht im Artikel. Pro wird nicht genannt.
- **Quellen:**
  - https://code.claude.com/docs/en/legal-and-compliance
  - https://support.claude.com/en/articles/15036540
  - https://www.anthropic.com/legal/consumer-terms
  - https://code.claude.com/docs/en/routines.md
  - https://code.claude.com/docs/en/remote-control.md
  - https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp

**Entscheidung 15.10.2026: Weg C.** Schlaubi läuft mit einem kleinen Prepaid-API-Key mit Ausgabenlimit. Das Pro-Abo bleibt für Claude Code und Marvins eigene Nutzung. Damit entfällt die Grauzone. Die Höhe des Monatsbudgets ist noch offen.
