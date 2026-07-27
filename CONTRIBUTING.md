# Contributing to morfDashboard

Thanks for your interest! This is a small, focused project: a headless system
dashboard for the Raspberry Pi on a tiny SPI screen. Contributions that keep it
**simple, readable and dependency-light** are very welcome.

## 1. Philosophy

- **Small and legible.** The screen is 240 × 320: every pixel counts. Prefer
  clarity over features.
- **Standard library first.** The only runtime dependencies are `Pillow` and
  `psutil` (see `requirements.txt`). New third-party dependencies should be a
  last resort - the network listener (`beacon_listener.py`), for example, uses
  the standard library only.
- **Configuration in one place.** User-facing settings (thresholds, drivers,
  monitored services, watched apps, pin-out) live in `config.py`.

## 2. Architecture in one picture

```
dashboard.py          entry point + main loop
├── boot.py           boot animation
├── screen.py         picks the display driver from config (ili9341 / st7789)
│   ├── ili9341.py    hardware driver
│   └── st7789.py     hardware driver
├── display.py        composes the image (Pillow only, no hardware)
├── systeminfo.py     collects system info + service/app states
├── beacon_listener.py  UDP listener for morfBeacon heartbeats (desktop apps)
├── reboot_alert.py   detects the current boot's reboot report
└── config.py         settings, thresholds, drivers, services, watched apps
```

Full explanation: [docs/fr/ARCHITECTURE.md](docs/fr/ARCHITECTURE.md) *(FR)*.

**Where does my change go?**

- A new *metric or layout* → `display.py` (drawing) and/or `systeminfo.py`
  (data), never mixed with the hardware drivers.
- A new *setting, threshold, monitored service or watched app* → `config.py`.
- A new *display panel* → a hardware driver exposing the same `Display` API,
  selected in `screen.py`.

## 3. Running it

On a Raspberry Pi with the screen wired (see
[docs/fr/HARDWARE.md](docs/fr/HARDWARE.md) and
[docs/fr/CABLAGE.md](docs/fr/CABLAGE.md)):

``` bash
pip install -r requirements.txt
python3 dashboard.py            # Ctrl+C to stop
```

`display.py` can also be run on a regular machine to render a preview PNG without
any hardware (Pillow only).

Installation as a `systemd` service is described in
[docs/fr/INSTALL.md](docs/fr/INSTALL.md).

## 4. Coding conventions

- Python 3, PEP 8, small functions, clear names.
- Comments in French are fine (they match the existing code); keep them useful,
  not redundant.
- No secrets or machine-specific absolute paths hard-coded outside `config.py`.

## 5. Documentation language

By GitHub convention, the root documents (`README.md`, `CHANGELOG.md`,
`ROADMAP.md`, this file) are in **English**; a French `README.fr.md` is kept. The
in-depth guides live under `docs/fr/` (French, the reference language). If you
change behavior, update the matching document.

## 6. Reporting bugs / proposing changes

Please use **GitHub Issues** to report a problem or suggest an improvement, and
open a pull request for changes. Describe the Raspberry Pi model, the OS, the
screen (ILI9341 / ST7789) and, if relevant, a photo of the display.
