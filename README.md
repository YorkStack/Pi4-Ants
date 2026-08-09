# Pi4-Ants

Ein leichtgewichtiges Raspberry-Pi-4-Projekt fuer eine interaktive Kunstinstallation, bei der Ameisen die Form einer Person auf dem Bildschirm andeuten.

## Projektziel

Geplant ist ein Setup mit:

- Raspberry Pi 4
- USB-Kamera, aktuell vorgesehen: Logitech Brio 500
- HDMI-Monitor, zunaechst Waveshare 1600x600
- Render-Loop mit `pygame`
- spaeter Kamera-Input und Bildanalyse mit `OpenCV`

## Aktueller Stand

Aktuell im Repo:

- technische Analyse der Referenzinstallation in [INSTALLATION_ANALYSE.md](/Users/yorkvonloew/Documents/Codex/Pi4-Ants/INSTALLATION_ANALYSE.md)
- erste Pi-taugliche Kamera-Demo in [src/ants_display_demo.py](/Users/yorkvonloew/Documents/Codex/Pi4-Ants/src/ants_display_demo.py)

Die Demo nutzt bereits:

- USB-Kamera via `OpenCV`
- gespiegeltes Livebild
- einfache Hintergrund-/Bewegungsmaske
- Ameisen mit Trail-Feld, die auf erkannte Zielpunkte reagieren

Falls keine Kamera-Ziele erkannt werden, faellt die Demo auf Maussteuerung zurueck.

## Start auf dem Raspberry Pi

Systempakete:

```bash
sudo apt update
sudo apt install -y python3-opencv python3-numpy python3-pygame python3-pip python3-venv v4l-utils ffmpeg git
```

Repo holen:

```bash
git clone https://github.com/YorkStack/Pi4-Ants.git
cd Pi4-Ants
python3 src/ants_display_demo.py
```

## Demo-Steuerung

- `f`: Fullscreen umschalten
- `r`: Ameisen neu verteilen
- `c`: Hintergrundmodell neu anlernen
- `Esc`: beenden
- Mausbewegung: Fallback-Ziel, wenn keine Kamera-Ziele aktiv sind

## Naechste Schritte

1. Parameter der Zielmasken fuer verschiedene Kameras feinjustieren
2. mehrere Ameisen-Spawn-Zonen statt rein zufaelliger Verteilung
3. Dichtefeld naeher an die Referenzinstallation bringen
4. Brio 500 spaeter als Hauptkamera einmessen
