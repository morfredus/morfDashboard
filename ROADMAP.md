# Roadmap

## Done

- **v1.5** - standby (screensaver) mode after SSH inactivity: a minimal moving
  frame (clock, uptime, three **G/P/S** status dots) with backlight dimming
  (software PWM). Presence is detected from SSH activity, pending a real sensor.
- **v1.4** - `beacon_status.py`, an SSH-run CLI that fetches the desktop apps'
  detailed `/status` metrics on demand and writes a human-friendly Markdown
  report (the headless screen only shows presence).
- **v1.3** - bilingual documentation restructure and GPL-3.0-only license.
- **v1.2** - LAN supervision of the desktop apps via morfBeacon heartbeats,
  two-column status area (up to 6 items), and self-monitoring of the dashboard
  service.
- **v1.1** - ST7789 support alongside ILI9341, embedded DejaVu Sans Mono font,
  unexpected-reboot badge.
- **v1.0.1** - version from the `VERSION` file, health dots (CPU/RAM/Swap/SSD/
  Load), SSD used/total, load as a percentage of cores, configurable services.

## Planned

- **Presence & luminosity sensors** to drive the standby mode and the backlight
  from hardware (PIR or mmWave radar for presence, BH1750 I²C for lux) - the
  standby logic already isolates the presence source (`activity.py`).
- GPU temperature.
- Wi-Fi RSSI (signal strength).
- Automatic screen rotation.
- Alert notifications.
- **`beacon_status.py`** - a small SSH-run CLI to fetch a desktop app's detailed
  `/status` metrics on demand (the headless screen only shows presence).
