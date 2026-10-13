# Checkliste Phase 0 – Gehirn vorbereiten

Stand 13.10.2026. Gehört zu `docs/bauplan-gehirn-v1.md`, Phase 0. Spiegel der Notion-Seite „Checkliste Phase 0 Gehirn“ (zum Abhaken am Handy).

**Wichtig:** Löschen ist **nicht** freigegeben (Marvin, 13.10.2026). In Phase 0 wird nichts gelöscht, formatiert oder neu installiert. Erst wenn alle Inhalte gesichert und geprüft sind, entscheidet Marvin über das Löschen. Das gilt für jeden Laptop und für die externe Festplatte einzeln.

Keine Passwörter, PINs oder Wiederherstellungsschlüssel in Notion, im Repo oder im Chat. Nur notieren, **dass** es sie gibt und wo sie sicher liegen.

## A. Bestandsaufnahme (pro Laptop)
- [ ] Hersteller und Modell (Aufkleber unten, z. B. „Lenovo ThinkPad T460“)
- [ ] Startet er? (ja / nein / nur mit Netzteil)
- [ ] Bekannte Defekte (Display, Tastatur, Akku, RAM, Lüfter)
- [ ] Betriebssystem (Windows, macOS, Linux, unbekannt)
- [ ] Kann ich mich anmelden? (Passwort bekannt: ja / nein, nicht aufschreiben)
- [ ] Prozessor, RAM, Festplatte oder SSD mit Größe. Unter Windows: Einstellungen → System → Info. Unter macOS: Apple-Menü → Über diesen Mac.
- [ ] Ist die Festplatte verschlüsselt? Windows: „BitLocker“ oder „Geräteverschlüsselung“. Mac: „FileVault“. Ohne Wiederherstellungsschlüssel kommt man bei einem Defekt nicht mehr an die Daten.
- [ ] Netzteil vorhanden und passend?

## B. Bestandsaufnahme externe Festplatte
- [ ] Hersteller, Größe, Anschluss (USB-A, USB-C)
- [ ] Was ist darauf? Eigene Daten, alte Sicherungen?
- [ ] Wird sie noch für etwas anderes gebraucht?

## C. Inhalte sichern (pro Laptop und für die externe Platte)
**Sicherungsziel:** ein Laufwerk oder Speicher, der **nicht** Schlaubis künftige Sicherungsplatte ist und nicht gelöscht wird. Wohin genau, entscheidet Marvin.

Was ansehen und sichern:
- [ ] Eigene Dateien: Dokumente, Bilder, Videos, Musik, Desktop, Downloads
- [ ] Fotos aus Apps (z. B. Fotos-App, iPhoto)
- [ ] E-Mails, falls ein Mail-Programm lokal gespeichert hat (Outlook-PST, Thunderbird-Profil)
- [ ] Browser: Lesezeichen exportieren. Gespeicherte Passwörter nur in einen Passwort-Manager übernehmen, nie als offene Datei liegen lassen.
- [ ] Lizenzschlüssel und Seriennummern von Programmen, die du noch brauchst (sicher ablegen)
- [ ] Schlüssel und Zugänge: SSH-Schlüssel, Krypto-Wallets, 2-Faktor-Apps, Zertifikate. Diese Dinge nie in Notion oder in die Cloud ohne Verschlüsselung legen.
- [ ] Spielstände, Projektordner, alles, was nur auf diesem Gerät liegt

**Laptop startet nicht?** Festplatte ausbauen und mit einem USB-Adapter (SATA oder M.2, je nach Platte) an einem anderen Rechner auslesen. Den Adapter kauft Marvin bei Bedarf. Ist die Platte mit BitLocker oder FileVault verschlüsselt, braucht man den Wiederherstellungsschlüssel (bei Windows oft im Microsoft-Konto hinterlegt).

## D. Sicherung prüfen (vor jeder Löschfreigabe)
- [ ] Ordnergröße und Dateianzahl auf Quelle und Ziel vergleichen
- [ ] Stichprobe: 10 zufällige Dateien auf dem Ziel öffnen (Fotos, Dokumente, Videos)
- [ ] Sicherung an einem anderen Rechner lesbar
- [ ] Verschlüsselte Inhalte lassen sich mit dem Schlüssel öffnen
- [ ] Notiz in Notion: „Laptop X gesichert am …, geprüft am …“ (ohne Passwörter)

## E. Material für Phase 1
- [ ] USB-Stick ab 8 GB (wird für Memtest86+ und das Live-Linux überschrieben, vorher Inhalt sichern)
- [ ] LAN-Kabel, falls vorhanden
- [ ] Externer Monitor oder Fernseher mit HDMI, Tastatur (für Laptops mit kaputtem Display)
- [ ] Größe der microSD-Karte für den Würfel nachsehen (offener Punkt Körper)

## F. Abschluss Phase 0
- [ ] Alle Steckbriefe in Notion
- [ ] Alle Inhalte gesichert und geprüft (Teil D)
- [ ] **Danach:** Marvin entscheidet einzeln, welcher Laptop und ob die externe Platte gelöscht werden darf.

Hinweis: Die Tests in Phase 1 (Memtest86+ und Live-Linux vom USB-Stick) starten nur vom Stick und schreiben nichts auf die Laptop-Festplatte. Sie dürfen nach der Sicherung schon laufen. Phase 2 (Neuinstallation) und Phase 5.2 (externe Platte) beginnen erst nach Marvins Löschfreigabe.
