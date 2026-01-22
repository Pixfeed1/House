"""
WINDOWS SYSTEM - Module principal
==================================
Architecture professionnelle avec 8 types de fenêtres.

Imports et exports de toutes les classes de fenêtres.
Manager central pour faciliter l'utilisation.

Code HAUTE QUALITÉ - Architecture modulaire.
"""

# Import de la classe de base
from .base import WindowBase

# Import de tous les types de fenêtres
from .battants import WindowBattants
from .oscillo_battante import WindowOscilloBattante
from .coulissante import WindowCoulissante
from .galandage import WindowGalandage
from .basculante import WindowBasculante
from .soufflet import WindowSoufflet
from .fixe import WindowFixe
from .guillotine import WindowGuillotine

# ============================================================
# TYPES DE FENÊTRES DISPONIBLES
# ============================================================

WINDOW_TYPES = {
    'BATTANTS': {
        'name': "Fenêtre à battants (française)",
        'class': WindowBattants,
        'description': "S'ouvre vers l'intérieur, 1 ou 2 vantaux"
    },
    'OSCILLO_BATTANTE': {
        'name': "Fenêtre oscillo-battante",
        'class': WindowOscilloBattante,
        'description': "Peut s'ouvrir en soufflet ou en battant"
    },
    'COULISSANTE': {
        'name': "Fenêtre coulissante",
        'class': WindowCoulissante,
        'description': "Vantaux glissent horizontalement"
    },
    'GALANDAGE': {
        'name': "Fenêtre coulissante à galandage",
        'class': WindowGalandage,
        'description': "Vantaux disparaissent dans le mur"
    },
    'BASCULANTE': {
        'name': "Fenêtre basculante",
        'class': WindowBasculante,
        'description': "Pivote autour d'un axe horizontal central"
    },
    'SOUFFLET': {
        'name': "Fenêtre à soufflet",
        'class': WindowSoufflet,
        'description': "S'ouvre par le haut, basculement limité"
    },
    'FIXE': {
        'name': "Fenêtre fixe",
        'class': WindowFixe,
        'description': "Ne s'ouvre pas, vitrage fixe"
    },
    'GUILLOTINE': {
        'name': "Fenêtre à guillotine (américaine)",
        'class': WindowGuillotine,
        'description': "Vantail coulisse verticalement"
    }
}

# ============================================================
# MANAGER CENTRAL
# ============================================================

class WindowManager:
    """
    Manager central pour créer des fenêtres.

    Facilite la création et la gestion des différents types.
    """

    @staticmethod
    def create_window(window_type, width, height, **kwargs):
        """
        Crée une fenêtre du type spécifié.

        Args:
            window_type: Type de fenêtre (clé de WINDOW_TYPES)
            width: Largeur (m)
            height: Hauteur (m)
            **kwargs: Paramètres spécifiques au type

        Returns:
            Instance de fenêtre, ou None si type invalide
        """
        # ✅ SÉCURITÉ: Validation du type
        if window_type not in WINDOW_TYPES:
            print(f"[WindowManager] ❌ Type '{window_type}' invalide")
            print(f"[WindowManager] Types valides: {', '.join(WINDOW_TYPES.keys())}")
            return None

        # Récupérer la classe
        window_class = WINDOW_TYPES[window_type]['class']

        # Créer l'instance
        try:
            window = window_class(width, height, **kwargs)
            return window
        except Exception as e:
            print(f"[WindowManager] ❌ Erreur création fenêtre: {e}")
            return None

    @staticmethod
    def generate_window_geometry(window_type, width, height, **kwargs):
        """
        Crée une fenêtre et génère sa géométrie directement.

        Args:
            window_type: Type de fenêtre
            width: Largeur (m)
            height: Hauteur (m)
            **kwargs: Paramètres spécifiques

        Returns:
            Object Blender, ou None si erreur
        """
        window = WindowManager.create_window(window_type, width, height, **kwargs)

        if window is None:
            return None

        return window.generate_geometry()

    @staticmethod
    def list_window_types():
        """
        Retourne la liste des types de fenêtres disponibles.

        Returns:
            Dict avec infos sur chaque type
        """
        return WINDOW_TYPES

    @staticmethod
    def get_window_info(window_type):
        """
        Retourne les informations d'un type de fenêtre.

        Args:
            window_type: Type de fenêtre

        Returns:
            Dict d'infos, ou None si invalide
        """
        return WINDOW_TYPES.get(window_type)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Classe de base
    'WindowBase',

    # Types de fenêtres
    'WindowBattants',
    'WindowOscilloBattante',
    'WindowCoulissante',
    'WindowGalandage',
    'WindowBasculante',
    'WindowSoufflet',
    'WindowFixe',
    'WindowGuillotine',

    # Manager
    'WindowManager',

    # Constantes
    'WINDOW_TYPES',
]
