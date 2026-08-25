"""
shutdown_notice.py
Écran plein cadre « Arrêt » / « Redémarrage » affiché quand le bouton
d'alimentation a été utilisé (confirmation visuelle avant que le système coupe).

Rendu seulement : produit une image PIL. C'est la boucle principale (seule
propriétaire de l'écran SPI) qui l'envoie à l'afficheur.
"""

from PIL import Image, ImageDraw

from config import WIDTH, HEIGHT, FONT_ANTIALIAS, load_font


def render(action):
    """Image plein cadre pour l'action demandée ("reboot" | "shutdown")."""
    title = "Redémarrage" if action == "reboot" else "Arrêt"

    img = Image.new("RGB", (WIDTH, HEIGHT), "black")
    draw = ImageDraw.Draw(img)
    draw.fontmode = "L" if FONT_ANTIALIAS else "1"

    big = load_font(30, bold=True)
    small = load_font(16, bold=False)

    tw = draw.textlength(title, font=big)
    draw.text(((WIDTH - tw) / 2, HEIGHT / 2 - 40), title, fill="white", font=big)

    sub = "en cours..."
    sw = draw.textlength(sub, font=small)
    draw.text(((WIDTH - sw) / 2, HEIGHT / 2 + 8), sub, fill="#F59E0B", font=small)

    return img
