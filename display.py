
"""
display.py
Gestion de l'affichage du Dashboard.
Aucune dépendance au matériel : uniquement Pillow.
"""

import time

from PIL import Image, ImageDraw

from config import (
    WIDTH,
    HEIGHT,
    GREEN,
    GRAY,
    SERVICES_ROTATE_SECONDS,
    FONT_SIZE,
    TITLE_FONT_SIZE,
    FONT_ANTIALIAS,
    FONT_BODY_BOLD,
    load_font,
    CPU_WARNING,
    CPU_CRITICAL,
    RAM_WARNING,
    RAM_CRITICAL,
    SWAP_WARNING,
    SWAP_CRITICAL,
    TEMP_WARNING,
    TEMP_CRITICAL,
    SSD_WARNING,
    SSD_CRITICAL,
    LOAD_WARNING,
    LOAD_CRITICAL,
    health_color,
)

# Colonnes d'alignement (px) pour la zone système
DOT_X = 10          # pastille de santé
LABEL_X = 24        # début du libellé (CPU / RAM / Swap / SSD)
DETAIL_X = 148      # colonne secondaire (température, détail SSD)
SERVICE_DOT_X = 150  # pastille d'état des services


class DashboardDisplay:

    def __init__(self):
        self.font = load_font(FONT_SIZE, bold=FONT_BODY_BOLD)
        self.title_font = load_font(TITLE_FONT_SIZE, bold=True)

    def _dot(self, draw, y, color):
        draw.ellipse((DOT_X, y + 3, DOT_X + 8, y + 11), fill=color)

    def render(self, info):

        img = Image.new("RGB", (WIDTH, HEIGHT), "black")
        draw = ImageDraw.Draw(img)
        draw.fontmode = "L" if FONT_ANTIALIAS else "1"

        self._header(draw, info)
        self._system(draw, info)
        self._network(draw, info)
        self._runtime(draw, info)
        self._services(draw, info)

        return img

    def _header(self, draw, info):
        draw.rectangle((0, 0, WIDTH, 26), fill="#0055A5")

        # Nom d'hôte à gauche
        host = info["hostname"]
        draw.text((6, 7), host, fill="white", font=self.title_font)
        host_right = 6 + draw.textlength(host, font=self.title_font)

        # Heure à droite
        time_txt = info["time"]
        tw = draw.textlength(time_txt, font=self.title_font)
        time_left = WIDTH - 6 - tw
        draw.text((time_left, 7), time_txt, fill="white", font=self.title_font)

        # Version centrée : affichée seulement si elle tient sans chevaucher
        # (un nom d'hôte long a priorité sur l'affichage de la version).
        version = f"v{info.get('version', 'dev')}"
        vw = draw.textlength(version, font=self.title_font)
        vx = (WIDTH - vw) / 2
        if vx > host_right + 6 and vx + vw < time_left - 6:
            draw.text((vx, 7), version, fill="#BBD6F2", font=self.title_font)

    def _metric(self, draw, y, label, value, warning, critical):
        """Pastille de santé + libellé/valeur alignés. Texte toujours blanc."""
        self._dot(draw, y, health_color(value, warning, critical))
        draw.text((LABEL_X, y),
                  f"{label:<5}{value:>5.1f}%",
                  fill="white",
                  font=self.font)

    def _system(self, draw, info):
        y = 38

        # CPU + température (colonne secondaire)
        self._metric(draw, y, "CPU", info["cpu"], CPU_WARNING, CPU_CRITICAL)
        if info["temp"] is None:
            temp_txt, temp_col = "--", "gray"
        else:
            temp_txt = f"{info['temp']:.1f}°C"
            temp_col = health_color(info["temp"], TEMP_WARNING, TEMP_CRITICAL)
        draw.text((DETAIL_X, y), temp_txt, fill=temp_col, font=self.font)

        y += 20
        self._metric(draw, y, "RAM", info["ram_percent"], RAM_WARNING, RAM_CRITICAL)

        y += 20
        self._metric(draw, y, "Swap", info["swap_percent"], SWAP_WARNING, SWAP_CRITICAL)

        y += 20
        self._metric(draw, y, "SSD", info["disk_percent"], SSD_WARNING, SSD_CRITICAL)
        detail = f"{info['disk_used_gb']:.0f}/{info['disk_total_gb']:.0f}Gio"
        draw.text((DETAIL_X, y), detail, fill="gray", font=self.font)

        draw.line((10, 122, WIDTH-10, 122), fill="gray")

    def _network(self, draw, info):
        y = 132
        draw.text((10, y), f"ETH   {info['eth'] or '--'}", fill="white", font=self.font)
        y += 18
        draw.text((10, y), f"WIFI  {info['wifi'] or '--'}", fill="white", font=self.font)
        y += 18
        draw.text((10, y), f"mDNS  {info['hostname']}.local", fill="yellow", font=self.font)

        draw.line((10, 188, WIDTH-10, 188), fill="gray")

    def _runtime(self, draw, info):
        y = 198
        draw.text((10, y), f"Uptime {info['uptime']}", fill="lightgreen", font=self.font)
        self._reboot_badge(draw, y, info.get("reboot_alert", {}))

        y += 18
        la = info["load"]
        cores = info.get("cpu_cores", 1) or 1
        load_pct = la[0] / cores * 100  # charge 1 min rapportée au nb de cœurs

        self._dot(draw, y, health_color(load_pct, LOAD_WARNING, LOAD_CRITICAL))
        draw.text((LABEL_X, y),
                  f"{'Load':<5}{la[0]:.2f} {la[1]:.2f} {la[2]:.2f} {load_pct:>3.0f}%",
                  fill="lightblue",
                  font=self.font)

        draw.line((10, 242, WIDTH-10, 242), fill="gray")

    def _reboot_badge(self, draw, y, alert):
        if not alert.get("active"):
            return

        count = alert.get("count", 1)
        txt = "REBOOT!" if count <= 1 else f"REBOOT x{count}"
        pad_x = 4
        badge_h = 15
        tw = draw.textlength(txt, font=self.title_font)
        x0 = WIDTH - 10 - int(tw) - pad_x * 2
        y0 = y - 1
        draw.rectangle((x0, y0, WIDTH - 10, y0 + badge_h), fill="#C62828")
        draw.text((x0 + pad_x, y0 + 3), txt, fill="white", font=self.title_font)

    def _fit(self, draw, text, max_w):
        """Tronque 'text' pour tenir dans max_w px ; le termine par '.' si tronque."""
        if draw.textlength(text, font=self.font) <= max_w:
            return text
        while text and draw.textlength(text + ".", font=self.font) > max_w:
            text = text[:-1]
        return (text + ".") if text else ""

    @staticmethod
    def _is_alert(svc):
        # En alerte = pastille ni verte (ok) ni grise (inconnu / non supervise).
        # Un service rouge (hors ligne / erreur) ou orange (avertissement) l'est.
        return svc.get("color") not in (GREEN, GRAY)

    def _page_dots(self, draw, page, pages):
        # Petits points de pagination centres tout en bas : signalent la rotation.
        r = 2
        gap = 8
        x0 = (WIDTH - pages * gap) // 2 + gap // 2
        y = 313
        for p in range(pages):
            cx = x0 + p * gap
            draw.ellipse((cx - r, y - r, cx + r, y + r),
                         fill="white" if p == page else "#444")

    def _services(self, draw, info):
        # Zone en DEUX colonnes : 6 emplacements (3 par colonne). S'il y a plus de
        # services que de place, les ALERTES restent epinglees (toujours visibles)
        # et les services sains defilent automatiquement dans les cases restantes.
        # Chaque service porte deja son libelle et sa couleur de pastille.
        services = info.get("services", [])
        ROWS = 3
        y0 = 252
        row_h = 18
        columns = (   # (x du nom, x de la pastille) par colonne
            (8,   106),   # gauche
            (128, 226),   # droite
        )
        name_gap = 6
        capacity = ROWS * len(columns)      # 6
        ROTATE_SECONDS = SERVICES_ROTATE_SECONDS   # duree d'affichage d'une page (config)

        alerts = [s for s in services if self._is_alert(s)]
        healthy = [s for s in services if not self._is_alert(s)]

        pages = 1
        page = 0
        if len(services) <= capacity:
            shown = alerts + healthy                       # tout tient, alertes en tete
        elif len(alerts) >= capacity:
            pages = (len(alerts) + capacity - 1) // capacity
            page = (int(time.time()) // ROTATE_SECONDS) % pages
            shown = alerts[page * capacity: page * capacity + capacity]
        else:
            free = capacity - len(alerts)                  # places pour les services sains
            pages = (len(healthy) + free - 1) // free
            page = (int(time.time()) // ROTATE_SECONDS) % pages
            shown = alerts + healthy[page * free: page * free + free]

        for i, svc in enumerate(shown[:capacity]):
            name_x, dot_x = columns[i // ROWS]     # 0..2 -> gauche, 3..5 -> droite
            y = y0 + (i % ROWS) * row_h
            label = self._fit(draw, svc.get("label", ""), dot_x - name_x - name_gap)
            draw.text((name_x, y), label, fill="white", font=self.font)
            draw.ellipse((dot_x, y + 2, dot_x + 8, y + 10), fill=svc.get("color", "gray"))

        if pages > 1:
            self._page_dots(draw, page, pages)


if __name__ == "__main__":
    from systeminfo import get_system_info

    ui = DashboardDisplay()
    img = ui.render(get_system_info())
    img.save("dashboard_preview.png")
    print("dashboard_preview.png généré.")
