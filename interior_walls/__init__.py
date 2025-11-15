"""
INTERIOR WALLS FINISHES - Module principal
===========================================
Système de finitions murales intérieures HAUTE QUALITÉ.

6 types de finitions:
- Peinture (4 variantes)
- Papier peint (avec validation image)
- Enduit décoratif (3 types)
- Bois (4 types)
- Pierre naturelle (4 types)
- Brique apparente (style brut)

Architecture modulaire "CODE BÉTON".
"""

# Import classe de base
from .base import WallFinishBase

# Import tous les types de finitions
from .peinture import WallPeinture, PAINT_TYPES
from .papier_peint import WallPapierPeint, WALLPAPER_TYPES
from .enduit import WallEnduit, PLASTER_TYPES
from .bois import WallBois, WOOD_TYPES
from .pierre import WallPierre, STONE_TYPES
from .brique_apparente import WallBriqueApparente

# ============================================================
# TYPES DE FINITIONS DISPONIBLES
# ============================================================

FINISH_TYPES = {
    'PEINTURE': {
        'name': "Peinture murale",
        'class': WallPeinture,
        'description': "Mat, satinée, brillante, velours. Lessivable selon type.",
        'subtypes': PAINT_TYPES
    },
    'PAPIER_PEINT': {
        'name': "Papier peint",
        'class': WallPapierPeint,
        'description': "Lisse, texturé, vinyle, intissé. Support texture image.",
        'subtypes': WALLPAPER_TYPES
    },
    'ENDUIT': {
        'name': "Enduit décoratif",
        'class': WallEnduit,
        'description': "Taloché, ciré, lissé. Donne relief ou effet matière.",
        'subtypes': PLASTER_TYPES
    },
    'BOIS': {
        'name': "Bois (bardage/panneaux/tasseaux)",
        'class': WallBois,
        'description': "Bardage, panneaux, tasseaux. Chaleureux, isolant.",
        'subtypes': WOOD_TYPES
    },
    'PIERRE': {
        'name': "Pierre naturelle",
        'class': WallPierre,
        'description': "Travertin, ardoise, granit, calcaire. Aspect naturel.",
        'subtypes': STONE_TYPES
    },
    'BRIQUE_APPARENTE': {
        'name': "Brique apparente (non finie)",
        'class': WallBriqueApparente,
        'description': "Briques visibles sans finition. Style industriel/loft.",
        'subtypes': None
    }
}

# ============================================================
# MANAGER CENTRAL
# ============================================================

class InteriorWallFinishManager:
    """
    Manager central pour finitions murales intérieures.

    Facilite création et gestion des différents types.
    """

    @staticmethod
    def create_finish(finish_type, width, height, **kwargs):
        """
        Crée une finition murale du type spécifié.

        Args:
            finish_type: Type de finition (clé de FINISH_TYPES)
            width: Largeur du mur (m)
            height: Hauteur du mur (m)
            **kwargs: Paramètres spécifiques au type

        Returns:
            Instance de finition, ou None si type invalide
        """
        # ✅ SÉCURITÉ: Validation du type
        if finish_type not in FINISH_TYPES:
            print(f"[InteriorWallFinishManager] ❌ Type '{finish_type}' invalide")
            print(f"[InteriorWallFinishManager] Types valides: {', '.join(FINISH_TYPES.keys())}")
            return None

        # Récupérer la classe
        finish_class = FINISH_TYPES[finish_type]['class']

        # Créer l'instance
        try:
            finish = finish_class(width, height, **kwargs)
            return finish
        except Exception as e:
            print(f"[InteriorWallFinishManager] ❌ Erreur création finition: {e}")
            return None

    @staticmethod
    def generate_finish_geometry(finish_type, width, height, **kwargs):
        """
        Crée une finition et génère sa géométrie directement.

        Args:
            finish_type: Type de finition
            width: Largeur (m)
            height: Hauteur (m)
            **kwargs: Paramètres spécifiques

        Returns:
            Object Blender, ou None si erreur
        """
        finish = InteriorWallFinishManager.create_finish(finish_type, width, height, **kwargs)

        if finish is None:
            return None

        return finish.generate_finish()

    @staticmethod
    def list_finish_types():
        """
        Retourne la liste des types de finitions disponibles.

        Returns:
            Dict avec infos sur chaque type
        """
        return FINISH_TYPES

    @staticmethod
    def get_finish_info(finish_type):
        """
        Retourne les informations d'un type de finition.

        Args:
            finish_type: Type de finition

        Returns:
            Dict d'infos, ou None si invalide
        """
        return FINISH_TYPES.get(finish_type)

    @staticmethod
    def list_subtypes(finish_type):
        """
        Liste les sous-types d'une finition (ex: types de peinture).

        Args:
            finish_type: Type de finition principale

        Returns:
            Dict de sous-types, ou None si n'existe pas
        """
        if finish_type not in FINISH_TYPES:
            return None

        return FINISH_TYPES[finish_type].get('subtypes')

    @staticmethod
    def validate_wallpaper_image(image_path):
        """
        Valide une image de papier peint (utilitaire public).

        Args:
            image_path: Chemin vers l'image

        Returns:
            Tuple (bool, width, height, message)
        """
        # Créer instance temporaire pour validation
        temp = WallPapierPeint(3.0, 2.7, image_path=None)
        return temp._validate_image_resolution(image_path)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Classe de base
    'WallFinishBase',

    # Types de finitions
    'WallPeinture',
    'WallPapierPeint',
    'WallEnduit',
    'WallBois',
    'WallPierre',
    'WallBriqueApparente',

    # Manager
    'InteriorWallFinishManager',

    # Constantes
    'FINISH_TYPES',
    'PAINT_TYPES',
    'WALLPAPER_TYPES',
    'PLASTER_TYPES',
    'WOOD_TYPES',
    'STONE_TYPES',
]
