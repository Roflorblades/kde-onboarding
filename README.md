# KDE Onboarding-Skript

Richtet einmalig nach einer frischen KDE-Installation Desktop-Verknüpfungen, Weblinks und Dokumente für den aktuellen Benutzer ein. Läuft komplett ohne externe Python-Abhängigkeiten.

## Schnellstart

1. Konfiguration kopieren und anpassen:
   ```bash
   cp .env.example .env
   nano .env
   ```
2. Skript ausführen (**nicht** als `root`):
   ```bash
   python3 kde-onboarding.py
   ```

## Funktionsweise

* Liest Weblinks aus der `.env` und legt `.desktop`-Dateien im Anwendungsstarter (`~/.local/share/applications`) und auf dem Desktop an.
* Kopiert passende Icons aus `./icons/` in die lokalen Benutzerdaten.
* Kopiert eine ODT-Vorlage in den Dokumente-Ordner und erstellt einen Symlink auf dem Desktop.
* Schreibt einen Marker (`~/.local/share/desktop-onboarding/.erledigt`), damit das Skript standardmäßig nur einmal durchläuft.

## Optionen

* `--force` erzwingt die Ausführung, selbst wenn der Marker bereits existiert:
  ```bash
  python3 kde-onboarding.py --force
  ```
