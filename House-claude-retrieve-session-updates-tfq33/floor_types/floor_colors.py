"""
COULEURS ET STYLES POUR SOLS
=============================

Mappings de couleurs et propriétés pour différents types de sols.
"""

# ============================================================
# ESSENCES DE BOIS (PARQUET)
# ============================================================

WOOD_COLORS = {
    'OAK': {
        'name': "Chêne",
        'color': (0.54, 0.42, 0.27, 1.0),  # Chêne clair naturel
        'roughness': 0.3,
        'description': "Classique, durable"
    },
    'WALNUT': {
        'name': "Noyer",
        'color': (0.35, 0.22, 0.15, 1.0),  # Brun foncé
        'roughness': 0.25,
        'description': "Brun foncé, élégant"
    },
    'MAPLE': {
        'name': "Érable",
        'color': (0.85, 0.75, 0.60, 1.0),  # Beige très clair
        'roughness': 0.2,
        'description': "Clair, moderne"
    },
    'CHERRY': {
        'name': "Cerisier",
        'color': (0.65, 0.35, 0.25, 1.0),  # Rougeâtre
        'roughness': 0.28,
        'description': "Rougeâtre, chaleureux"
    },
    'ASH': {
        'name': "Frêne",
        'color': (0.72, 0.65, 0.55, 1.0),  # Beige clair nervuré
        'roughness': 0.32,
        'description': "Beige clair, nervuré"
    },
}


def get_wood_color(wood_type):
    """Obtient la couleur RGBA pour une essence de bois

    Args:
        wood_type (str): Type de bois ('OAK', 'WALNUT', etc.)

    Returns:
        tuple: Couleur RGBA (4 floats) ou OAK par défaut
    """
    wood_data = WOOD_COLORS.get(wood_type, WOOD_COLORS['OAK'])
    return wood_data['color']


def get_wood_properties(wood_type):
    """Obtient toutes les propriétés d'une essence de bois

    Args:
        wood_type (str): Type de bois

    Returns:
        dict: Propriétés (color, roughness, name, description)
    """
    return WOOD_COLORS.get(wood_type, WOOD_COLORS['OAK'])


# ============================================================
# COULEURS CARRELAGE
# ============================================================

TILE_COLORS = {
    'WHITE': {
        'name': "Blanc",
        'color': (0.95, 0.95, 0.95, 1.0),  # Blanc brillant
        'roughness': 0.1,
        'description': "Blanc brillant"
    },
    'BEIGE': {
        'name': "Beige",
        'color': (0.85, 0.78, 0.70, 1.0),  # Beige neutre
        'roughness': 0.15,
        'description': "Beige neutre"
    },
    'GREY': {
        'name': "Gris",
        'color': (0.60, 0.60, 0.62, 1.0),  # Gris moderne
        'roughness': 0.12,
        'description': "Gris moderne"
    },
    'BLACK': {
        'name': "Noir",
        'color': (0.15, 0.15, 0.15, 1.0),  # Noir élégant
        'roughness': 0.08,
        'description': "Noir élégant"
    },
    'TERRACOTTA': {
        'name': "Terre cuite",
        'color': (0.75, 0.45, 0.35, 1.0),  # Orange/brun terre cuite
        'roughness': 0.25,
        'description': "Orange/brun méditerranéen"
    },
}


def get_tile_color(tile_color_preset):
    """Obtient la couleur RGBA pour un preset de carrelage

    Args:
        tile_color_preset (str): Preset ('WHITE', 'BEIGE', etc.)

    Returns:
        tuple: Couleur RGBA (4 floats) ou BEIGE par défaut
    """
    tile_data = TILE_COLORS.get(tile_color_preset, TILE_COLORS['BEIGE'])
    return tile_data['color']


def get_tile_properties(tile_color_preset):
    """Obtient toutes les propriétés d'un preset de carrelage

    Args:
        tile_color_preset (str): Preset de couleur

    Returns:
        dict: Propriétés (color, roughness, name, description)
    """
    return TILE_COLORS.get(tile_color_preset, TILE_COLORS['BEIGE'])
