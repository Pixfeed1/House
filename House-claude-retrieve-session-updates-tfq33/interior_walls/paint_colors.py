"""
COULEURS DE PEINTURE POPULAIRES POUR INTÉRIEURS
================================================

Top 10 des couleurs les plus utilisées dans les intérieurs modernes.
Valeurs RGBA (Red, Green, Blue, Alpha) normalisées 0.0-1.0.

Sources: Tendances déco 2024-2025, marques professionnelles (Dulux, Farrow & Ball, etc.)
"""

# ============================================================
# TOP 10 COULEURS PEINTURE INTÉRIEURE
# ============================================================

PAINT_COLOR_PRESETS = {
    'WHITE': (1.0, 1.0, 1.0, 1.0),  # Blanc pur - classique intemporel
    'BEIGE': (0.93, 0.87, 0.78, 1.0),  # Beige chaud (RAL 1015 approximatif)
    'GREY_LIGHT': (0.85, 0.85, 0.87, 1.0),  # Gris clair - tendance moderne
    'GREY': (0.62, 0.62, 0.64, 1.0),  # Gris moyen - élégant neutre
    'TAUPE': (0.57, 0.52, 0.48, 1.0),  # Taupe - gris-brun chaleureux
    'CREAM': (0.98, 0.96, 0.90, 1.0),  # Crème - blanc cassé doux
    'BLUE_PALE': (0.85, 0.91, 0.96, 1.0),  # Bleu pâle - apaisant
    'GREEN_SAGE': (0.70, 0.78, 0.72, 1.0),  # Vert sauge - naturel doux
    'PINK_POWDER': (0.95, 0.88, 0.90, 1.0),  # Rose poudré - féminin doux
    'YELLOW_SOFT': (0.98, 0.95, 0.80, 1.0),  # Jaune doux - lumineux chaleureux
}


def get_paint_color(preset_name):
    """Obtient la couleur RGBA depuis un preset

    Args:
        preset_name (str): Nom du preset ('WHITE', 'BEIGE', etc.)

    Returns:
        tuple: Couleur RGBA (4 floats) ou WHITE si preset inconnu
    """
    return PAINT_COLOR_PRESETS.get(preset_name, PAINT_COLOR_PRESETS['WHITE'])


def get_all_preset_names():
    """Retourne la liste de tous les noms de presets disponibles

    Returns:
        list: Liste des noms de presets
    """
    return list(PAINT_COLOR_PRESETS.keys())


# ============================================================
# COULEURS ADDITIONNELLES (pour extensions futures)
# ============================================================

# Couleurs accent (moins utilisées mais populaires)
ACCENT_COLORS = {
    'NAVY': (0.15, 0.25, 0.40, 1.0),  # Bleu marine - élégant
    'TERRACOTTA': (0.85, 0.50, 0.40, 1.0),  # Terracotta - méditerranéen
    'FOREST': (0.25, 0.40, 0.30, 1.0),  # Vert forêt - apaisant
    'BURGUNDY': (0.45, 0.20, 0.25, 1.0),  # Bordeaux - sophistiqué
    'CHARCOAL': (0.20, 0.20, 0.22, 1.0),  # Gris anthracite - moderne
}


# Couleurs vives (chambres enfants, accents)
VIBRANT_COLORS = {
    'CORAL': (1.0, 0.50, 0.45, 1.0),  # Corail vif
    'TURQUOISE': (0.25, 0.80, 0.85, 1.0),  # Turquoise
    'LEMON': (1.0, 0.95, 0.40, 1.0),  # Citron
    'LAVENDER': (0.75, 0.70, 0.90, 1.0),  # Lavande
}


# ============================================================
# HELPER: Conversion HEX -> RGBA
# ============================================================

def hex_to_rgba(hex_color):
    """Convertit une couleur hexadécimale en RGBA

    Args:
        hex_color (str): Couleur hex (#RRGGBB ou #RGB)

    Returns:
        tuple: Couleur RGBA (4 floats)

    Example:
        >>> hex_to_rgba('#FF5733')
        (1.0, 0.34, 0.2, 1.0)
    """
    hex_color = hex_color.lstrip('#')

    # Support format court #RGB
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])

    if len(hex_color) != 6:
        print(f"[PaintColors] ⚠️ Couleur hex invalide '{hex_color}', utilisation blanc")
        return (1.0, 1.0, 1.0, 1.0)

    try:
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return (r, g, b, 1.0)
    except ValueError:
        print(f"[PaintColors] ❌ Erreur conversion hex '{hex_color}'")
        return (1.0, 1.0, 1.0, 1.0)


def rgba_to_hex(rgba):
    """Convertit RGBA en hexadécimal

    Args:
        rgba (tuple): Couleur RGBA (4 floats)

    Returns:
        str: Couleur hex (#RRGGBB)
    """
    r = int(rgba[0] * 255)
    g = int(rgba[1] * 255)
    b = int(rgba[2] * 255)
    return f"#{r:02X}{g:02X}{b:02X}"
