# Skills zum Hochladen

Zips der Projekt-Skills, damit Marvin sie per Link vom Handy laden und in Claude hochladen kann (Anpassen → Skills).
Erzeugt aus `skills/<name>/` (Quelle bleibt dort). Bei jeder Änderung eines Skills neu packen:

```sh
cd skills && zip -qrX ../dist/skills/<name>.zip <name>
```

Download-Link: `https://github.com/lippsmar/robot-brain/raw/main/dist/skills/<name>.zip`
