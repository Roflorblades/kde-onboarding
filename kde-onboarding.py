#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KDE Desktop Onboarding Skript
---------------------------------------------------------------------------
Richtet einmalig Desktop-Verknüpfungen und Dokumente für einen Benutzer ein:
  - Weblinks auf dem Desktop und im KDE-Anwendungsstarter
  - Eine Dokumentdatei im Dokumente-Ordner samt Verknüpfung auf dem Desktop

Aufruf:
  python3 onboarding.py          # normale Ausführung (nur einmal wirksam)
  python3 onboarding.py --force  # Ausführung erzwingen
---------------------------------------------------------------------------
"""

import os
import sys
import subprocess
from pathlib import Path

# Script-Verzeichnis ermitteln
SCRIPT_DIR = Path(__file__).resolve().parent


def load_env():
    """Einfacher .env-Parser ohne externe Abhängigkeiten (kompatibel ab Python 3.6)."""
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    os.environ[key.strip()] = val.strip().strip('"\'')


# .env laden bevor Konfiguration ausgewertet wird
load_env()

# ===========================================================================
# Konfiguration (aus Umgebungsvariablen / .env mit Standardwerten)
# ===========================================================================

ODT_DATEI = os.getenv("ODT_FILENAME", "willkommen.odt")
ODT_DESKTOP_NAME = os.getenv("ODT_DESKTOP_NAME", "Willkommen.odt")
ERSATZ_ICON = os.getenv("FALLBACK_ICON", "applications-internet")

# Standard-Links falls keine .env vorhanden ist
DEFAULT_LINKS = [
    "Intranet|https://example.com/intranet|intranet.svg",
    "Helpdesk|https://example.com/helpdesk|helpdesk.svg",
]

raw_links = os.getenv("ONBOARDING_LINKS")
if raw_links:
    # Zeilenumbrüche/Backslashes bereinigen falls mehrzeilig definiert
    raw_links = raw_links.replace("\\", "").replace("\n", "").replace("\r", "")
    LINKS = [item.strip() for item in raw_links.split(";") if item.strip()]
else:
    LINKS = DEFAULT_LINKS


# ===========================================================================
# Pfade und Hilfsfunktionen
# ===========================================================================

def get_xdg_dir(dir_name):
    """Ermittelt XDG-User-Verzeichnisse über xdg-user-dir oder Fallback."""
    try:
        res = subprocess.run(
            ["xdg-user-dir", dir_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        path_str = res.stdout.strip()
        if path_str:
            return Path(path_str)
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    # Fallbacks
    if dir_name == "DESKTOP":
        return Path.home() / "Desktop"
    elif dir_name == "DOCUMENTS":
        return Path.home() / "Dokumente"
    return Path.home()

DATA_HOME = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share"))
DATEN_DIR = DATA_HOME / "desktop-onboarding"
ICON_DIR = DATEN_DIR / "icons"
MARKER = DATEN_DIR / ".erledigt"
APPS_DIR = DATA_HOME / "applications"
DESKTOP_DIR = get_xdg_dir("DESKTOP")
DOKUMENTE_DIR = get_xdg_dir("DOCUMENTS")

def info(msg):
    print(f"[INFO]    {msg}")


def warnung(msg):
    print(f"[WARNUNG] {msg}", file=sys.stderr)


def fehler(msg):
    print(f"[FEHLER]  {msg}", file=sys.stderr)
    sys.exit(1)


# ===========================================================================
# Arbeitsschritte
# ===========================================================================

def pruefe_konfiguration_und_dateien():
    """Prüft, ob die .env existiert und ob wichtige Quelldateien bereitstehen."""
    env_path = SCRIPT_DIR / ".env"
    if not env_path.exists():
        fehler(
            f"Die Konfigurationsdatei '.env' wurde nicht gefunden!\n"
            f"  -> Bitte kopiere die Vorlage: cp .env.example .env\n"
            f"  -> Und passe sie an deine Bedürfnisse an."
        )

    # Prüfen, ob die ODT-Vorlage existiert (falls der Schritt aktiv ist)
    source_odt = SCRIPT_DIR / ODT_DATEI
    if not source_odt.is_file():
        warnung(f"Die Dokumentenvorlage '{ODT_DATEI}' liegt nicht im Skript-Verzeichnis ({SCRIPT_DIR}).")
        warnung("Der ODT-Schritt wird beim Ausführen übersprungen werden.")

def pruefe_voraussetzungen(force=False):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        fehler("Bitte NICHT als root ausführen, sondern als Zielbenutzer.")

    if MARKER.exists() and not force:
        with open(MARKER, "r", encoding="utf-8") as f:
            datum = f.read().strip()
        info(f"Onboarding wurde bereits am {datum} durchgeführt.")
        info("Mit --force kann die Ausführung erzwungen werden.")
        sys.exit(0)


def lege_verzeichnisse_an():
    for d in [DESKTOP_DIR, DOKUMENTE_DIR, APPS_DIR, ICON_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def erstelle_weblink(eintrag):
    parts = eintrag.split("|")
    if len(parts) < 3:
        warnung(f"Ungültiger Link-Eintrag: {eintrag}")
        return
    name, url, icon_datei = parts[0], parts[1], parts[2]

    # Slug generieren (Kleinbuchstaben, nur a-z0-9 und Bindestriche)
    slug = "".join(c if c.isalnum() else "-" for c in name.lower())
    # Mehrfache Bindestriche bereinigen
    while "--" in slug:
        slug = slug.replace("--", "-")
    slug = slug.strip("-")

    datei = APPS_DIR / f"onboarding-{slug}.desktop"

    # Icon kopieren oder Fallback nutzen
    icon = ERSATZ_ICON
    source_icon_path = SCRIPT_DIR / "icons" / icon_datei
    target_icon_path = ICON_DIR / icon_datei

    if source_icon_path.is_file():
        import shutil
        shutil.copy2(source_icon_path, target_icon_path)
        icon = str(target_icon_path)
    else:
        warnung(f"Icon '{icon_datei}' nicht gefunden, verwende Ersatz-Icon.")

    # .desktop Desktop-Entry erstellen
    content = f"""[Desktop Entry]
Type=Application
Name={name}
Comment={url} öffnen
Exec=xdg-open "{url}"
Icon={icon}
Terminal=false
Categories=Network;
"""
    datei.write_text(content, encoding="utf-8")
    datei.chmod(0o755)

    # Kopie auf dem Desktop
    desktop_link = DESKTOP_DIR / f"{name}.desktop"
    desktop_link.write_text(content, encoding="utf-8")
    desktop_link.chmod(0o755)

    info(f"Weblink angelegt: {name}")


def erstelle_alle_weblinks():
    for eintrag in LINKS:
        erstelle_weblink(eintrag)


def kopiere_odt():
    source_odt = SCRIPT_DIR / ODT_DATEI
    if not source_odt.is_file():
        warnung(f"{ODT_DATEI} nicht gefunden, überspringe ODT-Schritt.")
        return

    target_odt = DOKUMENTE_DIR / ODT_DATEI
    desktop_symlink = DESKTOP_DIR / ODT_DESKTOP_NAME

    # Datei nur kopieren, wenn sie noch nicht existiert (Schutz vor Überschreiben bearbeiteter Dateien)
    if not target_odt.exists():
        import shutil
        shutil.copy2(source_odt, target_odt)
        info(f"{ODT_DATEI} nach {DOKUMENTE_DIR} kopiert.")
    else:
        info(f"{ODT_DATEI} existiert bereits in {DOKUMENTE_DIR}, überspringe Kopieren.")

    # Symlink auf dem Desktop erstellen (überschreiben falls vorhanden)
    if desktop_symlink.is_symlink() or desktop_symlink.exists():
        desktop_symlink.unlink()
    desktop_symlink.symlink_to(target_odt)

    info(f"Verknüpfung auf dem Desktop erstellt: {ODT_DESKTOP_NAME}")


def aktualisiere_kde_menue():
    try:
        subprocess.run(["update-desktop-database", str(APPS_DIR)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    try:
        subprocess.run(["kbuildsycoca5", "--noincremental"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def markiere_als_erledigt():
    import datetime
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.write_text(datetime.date.today().isoformat(), encoding="utf-8")


# ===========================================================================
# Hauptprogramm
# ===========================================================================

def main():
    force = "--force" in sys.argv
    pruefe_konfiguration_und_dateien()
    pruefe_voraussetzungen(force=force)
    lege_verzeichnisse_an()
    erstelle_alle_weblinks()
    kopiere_odt()
    aktualisiere_kde_menue()
    markiere_als_erledigt()
    info("Fertig. Falls Symbole fehlen: einmal abmelden und neu anmelden.")


if __name__ == "__main__":
    main()