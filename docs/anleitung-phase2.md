# Anleitung Phase 2 – Grundsystem (Bauplan Körper V1)

Für den Raspberry Pi Zero 2 W. Braucht nur: Pi, microSD (mindestens 16 GB, besser 32 GB), Netzteil (mind. 5 V / 2,5 A), Laptop mit Kartenleser. Ergebnis jedes Schritts in Notion „Entscheidungen und Projektlog“ festhalten.

## 2.0 SSH-Schlüssel auf dem Laptop (einmalig)
```sh
ssh-keygen -t ed25519 -C "marvin-laptop"
```
Der private Schlüssel bleibt auf dem Laptop. Nur der öffentliche Teil (`~/.ssh/id_ed25519.pub`) kommt auf den Pi.

## 2.1 System aufspielen
1. **Raspberry Pi Imager** auf dem Laptop öffnen (von raspberrypi.com).
2. Gerät: **Raspberry Pi Zero 2 W**. System: **Raspberry Pi OS Lite (64-bit)**. Speicher: die microSD.
3. Bei den Einstellungen (OS-Anpassung):
   - Hostname: `schlaubi`
   - Benutzername wählen, Passwort setzen (im Passwort-Manager speichern)
   - WLAN: Heimnetz eintragen, Land **DE**
   - SSH aktivieren, **nur Anmeldung per öffentlichem Schlüssel**, den Inhalt von `id_ed25519.pub` einfügen
4. Schreiben, Karte in den Pi, Strom an, 2–3 Minuten warten.

**Test:** vom Laptop
```sh
ssh <benutzer>@schlaubi.local
uname -m        # erwartet: aarch64
```
Verbindet ohne Passwortabfrage = bestanden.

## 2.2 Absichern
Auf dem Pi:
```sh
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y ufw unattended-upgrades
# SSH nur aus dem Heimnetz erlauben (Adressbereich an dein Netz anpassen, z. B. 192.168.178.0/24 bei einer Fritzbox)
sudo ufw allow from 192.168.178.0/24 to any port 22 proto tcp
sudo ufw enable
sudo ufw status
grep -i '^PasswordAuthentication' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null
```
**Tests:**
- `ufw status` zeigt nur Port 22 aus dem Heimnetz.
- Passwort-Login ist aus (`PasswordAuthentication no`). Gegenprobe vom Laptop: `ssh -o PubkeyAuthentication=no <benutzer>@schlaubi.local` muss abgelehnt werden.

## 2.3 Temperatur und Drosselung
```sh
vcgencmd measure_temp     # erwartet: unter 60 °C im Leerlauf
vcgencmd get_throttled    # erwartet: throttled=0x0
```
Bei einem anderen Wert als `0x0` meldet der Pi Unterspannung oder Hitze: Netzteil und Kabel prüfen (Skill `roboter-debugging`).

## Fertig, wenn
- SSH per Schlüssel geht, Passwort-Login abgelehnt wird,
- Firewall aktiv ist,
- Temperatur und `throttled` passen.
Dann Logzeile in Notion und weiter mit Phase 3 (Strommessung), sobald das Messgerät da ist.
