
"""
mock_display.py
Pilote d'écran SIMULÉ, sans aucun matériel.

Même API publique que st7789.py / ili9341.py (classe Display) : le reste du
projet ne voit aucune différence. Au lieu de piloter une dalle SPI, ce pilote
écrit la dernière image dans un PNG et, en option, l'affiche dans une fenêtre.

Pourquoi il existe
------------------
Les pilotes matériels importent spidev et RPi.GPIO dès leur chargement. Sur une
machine Linux SANS écran SPI (un PC de dev, un serveur), ces imports échouent :
le service morfDashboard plante alors au démarrage et systemd le relance en
boucle. Le mock ne dépend que de Pillow (déjà utilisé partout) : le service
tourne, on voit le rendu dans un PNG, et rien ne plante.

Le rétroéclairage est simulé en assombrissant l'image écrite : on visualise
ainsi la veille (BL_STANDBY) et l'extinction (BL_OFF) comme sur la vraie dalle.
"""

from pathlib import Path
import tempfile

from PIL import Image

from config import WIDTH, HEIGHT, MOCK_PNG_PATH, MOCK_WINDOW, BACKLIGHT_FULL


class MockDisplay:
    """Écran simulé : écrit un PNG (et, en option, met à jour une fenêtre)."""

    def __init__(self):
        self._backlight = BACKLIGHT_FULL
        self._png_path = self._resolve_png_path(Path(MOCK_PNG_PATH))
        self._last_image = Image.new("RGB", (WIDTH, HEIGHT), "black")
        # Fenêtre Tkinter optionnelle, créée paresseusement au premier rendu :
        # une interface graphique peut manquer (service sans serveur X), auquel
        # cas on reste au seul PNG, sans jamais faire échouer le service.
        self._tk = None
        self._tk_label = None
        self._tk_failed = False
        print(f"[mock_display] écran simulé actif -> {self._png_path}"
              + (" + fenêtre" if MOCK_WINDOW else ""))

    @staticmethod
    def _resolve_png_path(path: Path) -> Path:
        """Chemin PNG utilisable : crée le dossier, ou se replie sur /tmp.

        Le chemin par défaut vit sous /var/lib : un poste de dev n'y a pas
        forcément accès. Plutôt que de planter (l'inverse du but du mock), on
        se rabat sur un fichier temporaire.
        """
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Test d'inscriptibilité réel : un mkdir réussi ne garantit pas le droit d'écrire.
            path.touch(exist_ok=True)
            return path
        except OSError:
            fallback = Path(tempfile.gettempdir()) / "morfdashboard-screen.png"
            print(f"[mock_display] {path} non inscriptible, repli sur {fallback}")
            return fallback

    def _apply_backlight(self, image: Image.Image) -> Image.Image:
        """Assombrit l'image selon le niveau de rétroéclairage (0..100)."""
        level = max(0, min(100, int(self._backlight)))
        if level >= 100:
            return image
        # Un fond noir mélangé à l'image proportionnellement au niveau : à 0 %
        # l'écran est éteint (noir), à 15 % il est très sombre (veille).
        dark = Image.new("RGB", image.size, "black")
        return Image.blend(dark, image.convert("RGB"), level / 100.0)

    def _write(self, image: Image.Image):
        self._last_image = image
        shown = self._apply_backlight(image)
        try:
            shown.save(self._png_path, "PNG")
        except OSError as exc:
            print(f"[mock_display] écriture PNG impossible : {exc}")
        if MOCK_WINDOW and not self._tk_failed:
            self._update_window(shown)

    def _update_window(self, image: Image.Image):
        """Met à jour (ou crée) une fenêtre Tkinter unique, sans jamais planter."""
        try:
            import tkinter as tk
            from PIL import ImageTk
            if self._tk is None:
                self._tk = tk.Tk()
                self._tk.title("morfDashboard (mock)")
                self._tk.resizable(False, False)
                self._tk_label = tk.Label(self._tk)
                self._tk_label.pack()
            photo = ImageTk.PhotoImage(image)
            self._tk_label.configure(image=photo)
            self._tk_label.image = photo  # garder une référence (sinon GC efface l'image)
            self._tk.update_idletasks()
            self._tk.update()
        except Exception as exc:
            # Pas d'interface graphique, pas de Tk, fenêtre fermée... : on
            # renonce définitivement à la fenêtre, le PNG suffit.
            self._tk_failed = True
            self._tk = None
            print(f"[mock_display] fenêtre indisponible, PNG seul : {exc}")

    # --- API publique (identique aux pilotes matériels) ------------------

    def display_image(self, image):
        self._write(image)

    def clear(self, color="black"):
        self._write(Image.new("RGB", (WIDTH, HEIGHT), color))

    def set_backlight(self, level):
        # On mémorise le niveau et on réécrit la dernière image pour que la
        # variation (veille/extinction) soit visible tout de suite dans le PNG.
        self._backlight = level
        self._write(self._last_image)

    def close(self):
        if self._tk is not None:
            try:
                self._tk.destroy()
            except Exception:
                pass
            self._tk = None


class Display:
    """API publique du projet (identique à st7789.py / ili9341.py)."""

    def __init__(self):
        self.driver = MockDisplay()

    def display_image(self, image):
        self.driver.display_image(image)

    def clear(self, color="black"):
        self.driver.clear(color)

    def set_backlight(self, level):
        self.driver.set_backlight(level)

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    import time
    lcd = Display()
    lcd.clear("navy")
    time.sleep(1)
    lcd.clear("darkgreen")
    time.sleep(1)
    lcd.set_backlight(15)   # veille : PNG assombri
    time.sleep(1)
    lcd.clear("black")
    lcd.close()
