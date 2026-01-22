"""
FLOOR TYPES - Système modulaire de sols
=========================================
Architecture modulaire: un fichier par type de matériau.

Types disponibles:
- Parquets: ParquetMassif, ParquetContrecolle, Stratifie
- Carrelages: CarrelageCeramique, GresCerame
- Élégants: Marbre, PierreNaturelle, BetonCire
- Résistants: Vinyle, Linoleum
- Confort: Moquette, Liege

Utilisation:
    from floor_types import FlooringGenerator

    generator = FlooringGenerator(quality=QUALITY_HIGH)
    floor = generator.generate_floor('HARDWOOD_SOLID', width=5.0, length=4.0)
"""

# Importer toutes les classes de matériaux
from .base import (
    FloorTypeBase,
    QUALITY_LOW,
    QUALITY_MEDIUM,
    QUALITY_HIGH,
    QUALITY_ULTRA,
    DEFAULT_FLOOR_THICKNESS
)

from .parquet import ParquetMassif, ParquetContrecolle, Stratifie
from .carrelage import CarrelageCeramique, GresCerame
from .marbre import Marbre
from .pierre import PierreNaturelle
from .beton import BetonCire
from .vinyle import Vinyle
from .lino import Linoleum
from .moquette import Moquette
from .liege import Liege


# ============================================================
# MAPPING TYPE STRING → CLASSE
# ============================================================

FLOOR_TYPES = {
    # Parquets
    'HARDWOOD_SOLID': ParquetMassif,
    'HARDWOOD_ENGINEERED': ParquetContrecolle,
    'LAMINATE': Stratifie,

    # Carrelages
    'CERAMIC_TILE': CarrelageCeramique,
    'PORCELAIN_TILE': GresCerame,

    # Élégants
    'MARBLE': Marbre,
    'NATURAL_STONE': PierreNaturelle,
    'POLISHED_CONCRETE': BetonCire,

    # Résistants
    'VINYL': Vinyle,
    'LINOLEUM': Linoleum,

    # Confort
    'CARPET': Moquette,
    'CORK': Liege,
}


# ============================================================
# CLASSE WRAPPER POUR COMPATIBILITÉ AVEC L'ANCIEN CODE
# ============================================================

class FlooringGenerator:
    """
    Générateur de sols - Wrapper pour compatibilité avec l'ancien système.

    Utilise l'architecture modulaire en interne, mais expose la même API
    que l'ancien flooring.py monolithique.

    Architecture:
    - Chaque type de sol est une classe séparée
    - FlooringGenerator est juste un factory pattern
    - Code maintainable et extensible
    """

    def __init__(self, quality=QUALITY_HIGH):
        """
        Initialise le générateur.

        Args:
            quality: Niveau de qualité (QUALITY_LOW à QUALITY_ULTRA)
        """
        # ✅ SÉCURITÉ: Validation du niveau de qualité
        if quality not in [QUALITY_LOW, QUALITY_MEDIUM, QUALITY_HIGH, QUALITY_ULTRA]:
            print(f"[Flooring] ⚠️ Qualité invalide ({quality}), utilisation de QUALITY_HIGH par défaut")
            quality = QUALITY_HIGH

        self.quality = quality
        print(f"[FlooringGenerator] Initialisé (architecture modulaire, qualité: {quality})")

    def generate_floor(self, floor_type, width, length, room_name="Room", height=0.0, **custom_options):
        """
        Génère un sol du type spécifié.

        Args:
            floor_type: Type de sol (clé de FLOOR_TYPES)
            width: Largeur de la pièce (m)
            length: Longueur de la pièce (m)
            room_name: Nom de la pièce (pour identification)
            height: Hauteur Z du sol (par défaut 0.0)
            **custom_options: Options personnalisées (wood_type, tile_color, tile_size, etc.)

        Custom options disponibles:
            - wood_type: Essence de bois pour parquets ('OAK', 'WALNUT', 'MAPLE', 'CHERRY', 'ASH')
            - tile_color: Couleur pour carrelage ('WHITE', 'BEIGE', 'GREY', 'BLACK', 'TERRACOTTA')
            - tile_size: Taille des carreaux (float, en mètres)

        Returns:
            Object Blender du sol généré, ou None si erreur
        """
        # ✅ SÉCURITÉ: Validation du type de sol
        if floor_type not in FLOOR_TYPES:
            print(f"[FlooringGenerator] ❌ ERREUR: Type de sol '{floor_type}' inconnu")
            print(f"[FlooringGenerator] Types valides: {', '.join(FLOOR_TYPES.keys())}")
            return None

        # Récupérer la classe correspondante
        FloorClass = FLOOR_TYPES[floor_type]

        print(f"[FlooringGenerator] Génération {FloorClass.FLOOR_NAME} pour '{room_name}'")
        if custom_options:
            print(f"[FlooringGenerator] Options custom: {custom_options}")

        # Instancier avec options custom
        floor_instance = FloorClass(quality=self.quality, **custom_options)
        floor_obj = floor_instance.generate(width, length, room_name, height)

        return floor_obj

    @staticmethod
    def get_available_types():
        """
        Retourne la liste des types de sols disponibles.

        Returns:
            dict: {type_key: class_name}
        """
        return {key: cls.FLOOR_NAME for key, cls in FLOOR_TYPES.items()}

    @staticmethod
    def get_type_info(floor_type):
        """
        Retourne les informations sur un type de sol.

        Args:
            floor_type: Clé du type de sol

        Returns:
            dict: Informations sur le type (nom, catégorie, épaisseur, etc.)
        """
        if floor_type not in FLOOR_TYPES:
            return None

        FloorClass = FLOOR_TYPES[floor_type]

        return {
            'name': FloorClass.FLOOR_NAME,
            'category': FloorClass.CATEGORY,
            'thickness': FloorClass.THICKNESS,
            'pattern': FloorClass.PATTERN,
        }


# ============================================================
# EXPORTS PUBLICS
# ============================================================

__all__ = [
    # Constantes
    'QUALITY_LOW',
    'QUALITY_MEDIUM',
    'QUALITY_HIGH',
    'QUALITY_ULTRA',
    'DEFAULT_FLOOR_THICKNESS',

    # Classe principale
    'FlooringGenerator',

    # Mapping types
    'FLOOR_TYPES',

    # Classes individuelles (pour usage avancé)
    'FloorTypeBase',
    'ParquetMassif',
    'ParquetContrecolle',
    'Stratifie',
    'CarrelageCeramique',
    'GresCerame',
    'Marbre',
    'PierreNaturelle',
    'BetonCire',
    'Vinyle',
    'Linoleum',
    'Moquette',
    'Liege',
]
