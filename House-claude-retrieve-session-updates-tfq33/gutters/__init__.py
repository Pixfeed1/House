# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Gutters System Module
#  Copyright (C) 2025 mvaertan
#
#  Système modulaire de gouttières (rain gutters) pour maisons
#  - Géométrie dans gutter_geometry.py
#  - Matériaux dans gutter_materials.py
#
# ##### END GPL LICENSE BLOCK #####

"""
Système de gouttières pour House Generator

Ce module fournit un système complet de génération de gouttières
adapté au style architectural de la maison.

Usage:
    from gutters import GuttersGenerator

    gen = GuttersGenerator(quality='HIGH')
    gutter_objects = gen.generate(
        house_width=10.0,
        house_length=12.0,
        roof_height=5.5,
        architectural_style='TRADITIONAL'
    )
"""

from .gutter_geometry import (
    create_gutter_profile,
    create_gutter_mesh_section,
    create_downspout_mesh,
    generate_gutters_for_house,
    get_gutter_style_from_architectural_style,
    GUTTER_WIDTH,
    GUTTER_DEPTH,
    DOWNSPOUT_WIDTH,
)

from .gutter_materials import (
    create_gutter_material,
    create_downspout_material,
    get_gutter_material_for_style,
    apply_gutter_materials,
    create_painted_gutter_material,
    get_preset_gutter_material,
    GUTTER_COLOR_PRESETS,
)


# ============================================================
# CLASSE PRINCIPALE POUR GÉNÉRATION GOUTTIÈRES
# ============================================================

class GuttersGenerator:
    """Générateur de gouttières pour maisons

    Gère la génération complète du système de gouttières incluant:
    - Gouttières horizontales le long des bords du toit
    - Tuyaux de descente (downspouts) aux coins
    - Matériaux adaptés au style architectural

    Attributes:
        quality (str): Niveau de détail ('LOW', 'MEDIUM', 'HIGH', 'ULTRA')
    """

    def __init__(self, quality='MEDIUM'):
        """Initialise le générateur

        Args:
            quality: Niveau de détail de la géométrie et des matériaux
        """
        self.quality = quality

    def generate(
        self,
        house_width,
        house_length,
        roof_height,
        architectural_style='TRADITIONAL',
        roof_type='GABLE',
        roof_overhang=0.5,
        collection=None,
        material_type='AUTO'
    ):
        """Génère le système complet de gouttières

        Args:
            house_width: Largeur de la maison en mètres
            house_length: Longueur de la maison en mètres
            roof_height: Hauteur du point bas du toit
            architectural_style: Style architectural ('MODERN', 'TRADITIONAL', etc.)
            roof_type: Type de toit ('GABLE', 'HIP', 'FLAT')
            roof_overhang: Débord du toit en mètres
            collection: Collection Blender où ajouter les objets
            material_type: Type de matériau ('AUTO', 'ALUMINUM', 'COPPER', etc.)

        Returns:
            list: Liste des objets gouttières créés
        """

        # Déterminer le style de gouttière selon l'architecture
        gutter_style, downspout_style = get_gutter_style_from_architectural_style(
            architectural_style
        )

        # Générer la géométrie
        gutter_objects = generate_gutters_for_house(
            house_width=house_width,
            house_length=house_length,
            roof_height=roof_height,
            roof_type=roof_type,
            roof_overhang=roof_overhang,
            gutter_style=gutter_style,
            downspout_style=downspout_style,
            quality=self.quality,
            collection=collection
        )

        # Appliquer les matériaux
        if material_type == 'AUTO':
            # Matériau automatique selon le style
            apply_gutter_materials(
                gutter_objects,
                architectural_style=architectural_style,
                quality=self.quality
            )
        else:
            # Matériau spécifique
            material = create_gutter_material(
                material_type=material_type,
                style=architectural_style,
                quality=self.quality
            )
            for obj in gutter_objects:
                if obj.type == 'MESH':
                    obj.data.materials.clear()
                    obj.data.materials.append(material)

        return gutter_objects

    def generate_custom_color(
        self,
        house_width,
        house_length,
        roof_height,
        color=(1.0, 1.0, 1.0, 1.0),
        architectural_style='MODERN',
        roof_type='GABLE',
        roof_overhang=0.5,
        collection=None
    ):
        """Génère des gouttières avec une couleur personnalisée

        Utile pour des gouttières peintes (PVC ou aluminium laqué)

        Args:
            house_width, house_length, roof_height: Dimensions
            color: Couleur RGBA (tuple de 4 floats)
            architectural_style, roof_type, roof_overhang: Paramètres style
            collection: Collection Blender

        Returns:
            list: Liste des objets créés
        """

        # Déterminer le style de gouttière
        gutter_style, downspout_style = get_gutter_style_from_architectural_style(
            architectural_style
        )

        # Générer géométrie
        gutter_objects = generate_gutters_for_house(
            house_width=house_width,
            house_length=house_length,
            roof_height=roof_height,
            roof_type=roof_type,
            roof_overhang=roof_overhang,
            gutter_style=gutter_style,
            downspout_style=downspout_style,
            quality=self.quality,
            collection=collection
        )

        # Créer et appliquer matériau couleur
        material = create_painted_gutter_material(color, architectural_style)

        for obj in gutter_objects:
            if obj.type == 'MESH':
                obj.data.materials.clear()
                obj.data.materials.append(material)

        return gutter_objects


# ============================================================
# EXPORTS PUBLICS
# ============================================================

__all__ = [
    # Classe principale
    'GuttersGenerator',

    # Fonctions géométrie
    'create_gutter_profile',
    'create_gutter_mesh_section',
    'create_downspout_mesh',
    'generate_gutters_for_house',
    'get_gutter_style_from_architectural_style',

    # Fonctions matériaux
    'create_gutter_material',
    'create_downspout_material',
    'get_gutter_material_for_style',
    'apply_gutter_materials',
    'create_painted_gutter_material',
    'get_preset_gutter_material',

    # Constantes
    'GUTTER_WIDTH',
    'GUTTER_DEPTH',
    'DOWNSPOUT_WIDTH',
    'GUTTER_COLOR_PRESETS',
]


print("[Gutters] Module gouttières chargé")
print("  ✓ 4 styles géométriques: HALF_ROUND, K_STYLE, BOX, EUROPEAN")
print("  ✓ 5 matériaux: ALUMINUM, COPPER, ZINC, PVC, STEEL")
print("  ✓ Mapping automatique selon style architectural")
