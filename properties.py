# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Properties Module (BLENDER 4.2+ COMPATIBLE)
#  Copyright (C) 2025 mvaertan
#
#  ✅ CORRIGÉ - Lazy loading de pbr_scanner pour éviter l'erreur _RestrictData
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
    EnumProperty,
    StringProperty,
    FloatVectorProperty,
    PointerProperty,
)


def regenerate_house(self, context):
    """Callback pour régénérer la maison quand une propriété change"""
    if hasattr(context.scene, 'house_auto_update') and context.scene.house_auto_update:
        # Déclencher la régénération (sera implémenté plus tard)
        pass


def get_brick_presets_safe(self, context):
    """Wrapper sécurisé pour get_brick_preset_items avec fallback
    
    ✅ CORRECTION: Lazy loading du scanner pour éviter l'import au chargement du module
    """
    # ✅ Importer seulement quand on en a besoin (lazy loading)
    try:
        from .materials import pbr_scanner
        return pbr_scanner.get_brick_preset_items(self, context)
    except Exception as e:
        print(f"[House] ⚠️ Erreur scan PBR: {e}")
    
    # Fallback: presets hardcodés si le scanner ne marche pas
    return [
        ('BRICK_RED', "Briques rouges", "Briques rouges traditionnelles", 'MATERIAL', 0),
        ('BRICK_RED_DARK', "Briques rouges foncées", "Briques rouges sombres", 'MATERIAL', 1),
        ('BRICK_ORANGE', "Briques orangées", "Briques orangées/terre cuite", 'MATERIAL', 2),
        ('BRICK_BROWN', "Briques brunes", "Briques brunes/chocolat", 'MATERIAL', 3),
        ('BRICK_YELLOW', "Briques jaunes (London)", "Briques jaunes type London", 'MATERIAL', 4),
        ('BRICK_GREY', "Briques grises modernes", "Briques grises contemporaines", 'MATERIAL', 5),
    ]


class HouseGeneratorProperties(PropertyGroup):
    """Propriétés pour le générateur de maison"""
    
    # ============================================================
    # MODE DE GÉNÉRATION
    # ============================================================
    
    generation_mode: EnumProperty(
        name="Mode",
        description="Mode de génération de la maison",
        items=[
            ('AUTO', "Automatique", "Génération automatique selon des critères", 'AUTO', 0),
            ('MANUAL', "Plan Manuel", "Construction à partir d'un plan 2D", 'GREASEPENCIL', 1),
        ],
        default='AUTO'
    )
    
    # ============================================================
    # DIMENSIONS GÉNÉRALES
    # ============================================================
    
    house_width: FloatProperty(
        name="Largeur",
        description="Largeur de la maison (axe X)",
        default=10.0,
        min=3.0,
        max=50.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    house_length: FloatProperty(
        name="Longueur",
        description="Longueur de la maison (axe Y)",
        default=12.0,
        min=3.0,
        max=50.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    num_floors: IntProperty(
        name="Nombre d'étages",
        description="Nombre d'étages de la maison",
        default=1,
        min=1,
        max=4,
        update=regenerate_house
    )
    
    floor_height: FloatProperty(
        name="Hauteur d'étage",
        description="Hauteur d'un étage",
        default=2.7,
        min=2.0,
        max=4.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    wall_thickness: FloatProperty(
        name="Épaisseur murs",
        description="Épaisseur des murs extérieurs",
        default=0.3,
        min=0.1,
        max=0.6,
        unit='LENGTH',
        update=regenerate_house
    )
    
    # ============================================================
    # STYLE ARCHITECTURAL
    # ============================================================
    
    architectural_style: EnumProperty(
        name="Style",
        description="Style architectural de la maison",
        items=[
            ('MODERN', "Moderne", "Architecture contemporaine minimaliste"),
            ('TRADITIONAL', "Traditionnel", "Style classique européen"),
            ('MEDITERRANEAN', "Méditerranéen", "Style villa du sud"),
            ('CONTEMPORARY', "Contemporain", "Style moderne mixte"),
            ('ASIAN', "Asiatique", "Style japonais/chinois"),
        ],
        default='TRADITIONAL',
        update=regenerate_house
    )
    
    # ============================================================
    # TOIT
    # ============================================================
    
    roof_type: EnumProperty(
        name="Type de toit",
        description="Forme du toit",
        items=[
            ('GABLE', "Pignon", "Toit à deux pentes (standard)"),
            ('HIP', "Croupe", "Toit à quatre pentes"),
            ('FLAT', "Plat", "Toit-terrasse"),
            ('GAMBREL', "Mansarde", "Toit à combles"),
            ('SHED', "Monopente", "Toit à une seule pente"),
        ],
        default='GABLE',
        update=regenerate_house
    )
    
    roof_pitch: FloatProperty(
        name="Pente du toit",
        description="Angle de pente du toit en degrés",
        default=35.0,
        min=5.0,
        max=60.0,
        subtype='ANGLE',
        update=regenerate_house
    )
    
    roof_overhang: FloatProperty(
        name="Débord de toit",
        description="Longueur du débord du toit",
        default=0.5,
        min=0.0,
        max=2.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    # ============================================================
    # FONDATIONS
    # ============================================================
    
    foundation_height: FloatProperty(
        name="Hauteur fondations",
        description="Hauteur visible des fondations",
        default=0.5,
        min=0.0,
        max=2.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    # ============================================================
    # FENÊTRES
    # ============================================================
    
    window_width: FloatProperty(
        name="Largeur fenêtre",
        description="Largeur standard des fenêtres",
        default=1.2,
        min=0.6,
        max=3.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    window_height: FloatProperty(
        name="Hauteur fenêtre",
        description="Hauteur standard des fenêtres",
        default=1.4,
        min=0.8,
        max=2.5,
        unit='LENGTH',
        update=regenerate_house
    )
    
    window_height_ratio: FloatProperty(
        name="Ratio hauteur fenêtre",
        description="Ratio de hauteur par rapport à la hauteur de l'étage (0.4 = 40%)",
        default=0.4,
        min=0.2,
        max=0.8,
        update=regenerate_house
    )
    
    window_type: EnumProperty(
        name="Type fenêtre",
        description="Type de fenêtre par défaut",
        items=[
            ('CASEMENT', "Battant", "Fenêtre à battant (standard européen)"),
            ('SLIDING', "Coulissante", "Fenêtre coulissante horizontale"),
            ('FIXED', "Fixe", "Fenêtre fixe (ne s'ouvre pas)"),
            ('DOUBLE_HUNG', "Guillotine", "Fenêtre à guillotine (style américain)"),
            ('ARCHED', "Cintrée", "Fenêtre avec arc en haut"),
            ('PICTURE', "Panoramique", "Grande baie vitrée"),
        ],
        default='CASEMENT',
        update=regenerate_house
    )
    
    window_quality: EnumProperty(
        name="Qualité fenêtres",
        description="Niveau de détail des fenêtres",
        items=[
            ('LOW', "Basse", "Peu de détails, rapide (pour grandes scènes)", 0),
            ('MEDIUM', "Moyenne", "Bon équilibre détails/performance", 1),
            ('HIGH', "Haute", "Maximum de détails (pour rendus finaux)", 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )
    
    num_windows_front: IntProperty(
        name="Fenêtres façade",
        description="Nombre de fenêtres sur la façade avant",
        default=3,
        min=0,
        max=10,
        update=regenerate_house
    )
    
    num_windows_side: IntProperty(
        name="Fenêtres côtés",
        description="Nombre de fenêtres sur les côtés",
        default=2,
        min=0,
        max=10,
        update=regenerate_house
    )
    
    num_windows_back: IntProperty(
        name="Fenêtres arrière",
        description="Nombre de fenêtres sur la façade arrière",
        default=2,
        min=0,
        max=10,
        update=regenerate_house
    )
    
    window_spacing: FloatProperty(
        name="Espacement fenêtres",
        description="Espacement entre les fenêtres",
        default=2.0,
        min=0.5,
        max=5.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    # ============================================================
    # PORTES
    # ============================================================
    
    front_door_width: FloatProperty(
        name="Largeur porte entrée",
        description="Largeur de la porte d'entrée principale",
        default=1.0,
        min=0.8,
        max=2.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    door_height: FloatProperty(
        name="Hauteur porte",
        description="Hauteur de la porte d'entrée",
        default=2.1,
        min=1.8,
        max=2.5,
        unit='LENGTH',
        update=regenerate_house
    )
    
    door_type: EnumProperty(
        name="Type porte",
        description="Type de porte d'entrée",
        items=[
            ('SINGLE', "Simple", "Porte simple battant"),
            ('DOUBLE', "Double", "Porte double battant"),
            ('SLIDING', "Coulissante", "Porte coulissante"),
            ('FRENCH', "Française", "Porte-fenêtre vitrée"),
        ],
        default='SINGLE',
        update=regenerate_house
    )

    door_quality: EnumProperty(
        name="Qualité portes",
        description="Niveau de détail des portes",
        items=[
            ('LOW', "Basse", "Peu de détails", 0),
            ('MEDIUM', "Moyenne", "Bon équilibre", 1),
            ('HIGH', "Haute", "Maximum de détails", 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )

    include_back_door: BoolProperty(
        name="Porte arrière",
        description="Ajouter une porte à l'arrière de la maison",
        default=False,
        update=regenerate_house
    )
    
    # ============================================================
    # GARAGE
    # ============================================================
    
    include_garage: BoolProperty(
        name="Inclure garage",
        description="Ajouter un garage à la maison",
        default=False,
        update=regenerate_house
    )
    
    garage_width: FloatProperty(
        name="Largeur garage",
        description="Largeur du garage",
        default=3.0,
        min=2.5,
        max=6.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    garage_depth: FloatProperty(
        name="Profondeur garage",
        description="Profondeur du garage",
        default=5.0,
        min=4.0,
        max=8.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    garage_position: EnumProperty(
        name="Position garage",
        description="Position du garage par rapport à la maison",
        items=[
            ('LEFT', "Gauche", "Garage sur le côté gauche"),
            ('RIGHT', "Droite", "Garage sur le côté droit"),
            ('FRONT', "Avant", "Garage en façade"),
            ('ATTACHED', "Attaché", "Garage intégré à la maison"),
        ],
        default='LEFT',
        update=regenerate_house
    )

    garage_size: EnumProperty(
        name="Taille garage",
        description="Taille du garage",
        items=[
            ('SINGLE', "Simple (1 voiture)", "Garage pour 1 voiture"),
            ('DOUBLE', "Double (2 voitures)", "Garage pour 2 voitures"),
        ],
        default='SINGLE',
        update=regenerate_house
    )
    
    # ============================================================
    # BALCONS / TERRASSES
    # ============================================================
    
    include_balcony: BoolProperty(
        name="Ajouter balcon",
        description="Ajouter un balcon aux étages supérieurs",
        default=False,
        update=regenerate_house
    )
    
    include_terrace: BoolProperty(
        name="Ajouter terrasse",
        description="Ajouter une terrasse au rez-de-chaussée",
        default=False,
        update=regenerate_house
    )
    
    balcony_width: FloatProperty(
        name="Largeur balcon",
        description="Largeur du balcon",
        default=2.0,
        min=1.0,
        max=4.0,
        unit='LENGTH',
        update=regenerate_house
    )
    
    balcony_depth: FloatProperty(
        name="Profondeur balcon",
        description="Profondeur du balcon",
        default=1.2,
        min=0.8,
        max=2.0,
        unit='LENGTH',
        update=regenerate_house
    )

    # ============================================================
    # CHEMINÉE
    # ============================================================

    add_chimney: BoolProperty(
        name="Ajouter cheminée",
        description="Ajouter une cheminée sur le toit",
        default=False,
        update=regenerate_house
    )

    # ============================================================
    # GOUTTIÈRES (RAIN GUTTERS)
    # ============================================================

    add_gutters: BoolProperty(
        name="Ajouter gouttières",
        description="Ajouter un système de gouttières le long du toit",
        default=True,
        update=regenerate_house
    )

    gutter_style: EnumProperty(
        name="Style gouttière",
        description="Style de gouttière (adapté automatiquement au style architectural)",
        items=[
            ('AUTO', "Automatique", "Style adapté à l'architecture", 'AUTO', 0),
            ('HALF_ROUND', "Demi-ronde", "Gouttière classique européenne", 'SPHERE', 1),
            ('K_STYLE', "Style K", "Gouttière américaine moderne", 'MESH_UVSPHERE', 2),
            ('BOX', "Rectangulaire", "Gouttière moderne/commerciale", 'MESH_CUBE', 3),
            ('EUROPEAN', "Trapézoïdale", "Gouttière trapézoïdale européenne", 'MESH_GRID', 4),
        ],
        default='AUTO',
        update=regenerate_house
    )

    gutter_material_type: EnumProperty(
        name="Matériau gouttières",
        description="Type de matériau pour les gouttières",
        items=[
            ('AUTO', "Automatique", "Matériau adapté au style architectural", 'AUTO', 0),
            ('ALUMINUM', "Aluminium", "Gouttières en aluminium (léger, durable)", 'MATERIAL', 1),
            ('COPPER', "Cuivre", "Gouttières en cuivre (élégant, haute gamme)", 'MATERIAL', 2),
            ('ZINC', "Zinc", "Gouttières en zinc (moderne, durable)", 'MATERIAL', 3),
            ('PVC', "PVC", "Gouttières en plastique (économique)", 'MATERIAL', 4),
            ('STEEL', "Acier galvanisé", "Gouttières en acier (robuste)", 'MATERIAL', 5),
        ],
        default='AUTO',
        update=regenerate_house
    )

    gutter_quality: EnumProperty(
        name="Qualité gouttières",
        description="Niveau de détail géométrique des gouttières",
        items=[
            ('LOW', "Basse", "Minimal, rapide", 0),
            ('MEDIUM', "Moyenne", "Bon équilibre", 1),
            ('HIGH', "Haute", "Très détaillé", 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )

    # ============================================================
    # DISTRIBUTION DES PIÈCES
    # ============================================================

    num_rooms: IntProperty(
        name="Nombre de pièces",
        description="Nombre de pièces principales",
        default=3,
        min=1,
        max=10,
        update=regenerate_house
    )

    include_kitchen: BoolProperty(
        name="Inclure cuisine",
        description="Inclure une cuisine dans le plan",
        default=True,
        update=regenerate_house
    )

    include_bathroom: BoolProperty(
        name="Inclure salle de bain",
        description="Inclure une ou plusieurs salles de bain",
        default=True,
        update=regenerate_house
    )

    num_bathrooms: IntProperty(
        name="Nombre de salles de bain",
        description="Nombre de salles de bain",
        default=1,
        min=0,
        max=5,
        update=regenerate_house
    )

    # ============================================================
    # QUALITÉ GLOBALE
    # ============================================================
    
    global_quality: EnumProperty(
        name="Qualité globale",
        description="Niveau de détail général de la maison",
        items=[
            ('LOW', "Basse (rapide)", "Peu de détails, optimisé pour l'édition", 'PREFERENCES', 0),
            ('MEDIUM', "Moyenne", "Bon équilibre entre qualité et performance", 'PREFERENCES', 1),
            ('HIGH', "Haute (lent)", "Maximum de détails pour rendus finaux", 'PREFERENCES', 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )
    
    # ============================================================
    # MATÉRIAUX ET TEXTURES
    # ============================================================
    
    use_materials: BoolProperty(
        name="Utiliser matériaux",
        description="Appliquer automatiquement des matériaux",
        default=True
    )
    
    # ============================================================
    # PROPRIÉTÉS AJOUTÉES : CONSTRUCTION MURS BRIQUES 3D
    # ============================================================
    
    wall_construction_type: EnumProperty(
        name="Type de construction murs",
        description="Méthode de construction des murs",
        items=[
            ('SIMPLE', "Mur simple", "Mur simple avec matériau shader", 'SHADING_TEXTURE', 0),
            ('BRICK_3D', "Briques 3D", "Mur avec vraies briques 3D géométriques", 'MESH_CUBE', 1),
        ],
        default='SIMPLE',
        update=regenerate_house
    )
    
    brick_3d_quality: EnumProperty(
        name="Qualité briques 3D",
        description="Niveau de détail des briques 3D",
        items=[
            ('LOW', "Basse", "Instancing simple (rapide)", 0),
            ('MEDIUM', "Moyenne", "Instancing avec briques détaillées", 1),
            ('HIGH', "Haute", "Géométrie complète (lourd!)", 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )
    
    brick_material_mode: EnumProperty(
        name="Mode matériau briques 3D",
        description="Comment appliquer le matériau aux briques",
        items=[
            ('COLOR', "Couleur unie", "Utiliser une couleur unie", 0),
            ('PRESET', "Preset", "Utiliser un preset de matériau", 1),
            ('CUSTOM', "Personnalisé", "Utiliser matériau custom", 2),
        ],
        default='PRESET',
        update=regenerate_house
    )
    
    brick_preset_type: EnumProperty(
        name="Preset briques",
        description="Type de briques à utiliser",
        items=get_brick_presets_safe,
        update=regenerate_house
    )
    
    brick_solid_color: FloatVectorProperty(
        name="Couleur briques 3D",
        description="Couleur pour les briques 3D",
        subtype='COLOR',
        size=4,
        default=(0.65, 0.25, 0.15, 1.0),
        update=regenerate_house
    )
    
    brick_custom_material: PointerProperty(
        name="Matériau custom",
        description="Matériau personnalisé pour briques 3D",
        type=bpy.types.Material
    )
    
    wall_material_type: EnumProperty(
        name="Matériau murs",
        description="Type de matériau pour les murs extérieurs",
        items=[
            ('BRICK_RED', "Briques rouges", "Briques traditionnelles rouges", 'MATERIAL', 0),
            ('BRICK_RED_DARK', "Briques rouges foncées", "Briques rouge foncé", 'MATERIAL', 1),
            ('BRICK_ORANGE', "Briques orangées", "Briques orange terre cuite", 'MATERIAL', 2),
            ('BRICK_BROWN', "Briques brunes", "Briques marron", 'MATERIAL', 3),
            ('BRICK_YELLOW', "Briques jaunes", "Briques jaunes (style London)", 'MATERIAL', 4),
            ('BRICK_GREY', "Briques grises", "Briques grises modernes", 'MATERIAL', 5),
            ('BRICK_WHITE', "Briques blanches", "Briques peintes en blanc", 'MATERIAL', 6),
            ('BRICK_PAINTED', "Briques peintes", "Briques avec couleur personnalisée", 'COLOR', 7),
        ],
        default='BRICK_RED',
        update=regenerate_house
    )
    
    wall_brick_quality: EnumProperty(
        name="Qualité matériau briques",
        description="Niveau de détail du matériau shader des briques (pour mur simple)",
        items=[
            ('LOW', "Basse", "Peu de détails shader (grandes scènes)", 'PREFERENCES', 0),
            ('MEDIUM', "Moyenne", "Bon équilibre", 'PREFERENCES', 1),
            ('HIGH', "Haute", "Maximum de détails shader", 'PREFERENCES', 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )
    
    wall_brick_color: FloatVectorProperty(
        name="Couleur briques",
        description="Couleur personnalisée pour les briques peintes",
        subtype='COLOR',
        size=4,
        min=0.0,
        max=1.0,
        default=(0.8, 0.7, 0.5, 1.0),
        update=regenerate_house
    )
    
    # ============================================================
    # PROPRIÉTÉ AJOUTÉE : CHOIX BRIQUES 3D OU SIMPLE MATÉRIAU
    # ============================================================
    
    use_geometry_bricks: BoolProperty(
        name="Utiliser briques 3D",
        description="Utiliser de vraies briques 3D géométriques au lieu d'un simple matériau shader",
        default=False,
        update=regenerate_house
    )
    
    geometry_brick_quality: EnumProperty(
        name="Qualité briques 3D",
        description="Niveau de détail de la géométrie des briques 3D",
        items=[
            ('LOW', "Basse (Instancing)", "Utilise l'instancing pour optimiser (grandes scènes)", 'MESH_CUBE', 0),
            ('MEDIUM', "Moyenne (Instancing HQ)", "Instancing avec briques haute qualité", 'MESH_UVSPHERE', 1),
            ('HIGH', "Haute (Géométrie complète)", "Chaque brique est unique (lourd!)", 'MESH_ICOSPHERE', 2),
        ],
        default='MEDIUM',
        update=regenerate_house
    )
    
    wall_material_color: FloatVectorProperty(
        name="Couleur murs (legacy)",
        description="Couleur des murs (ancienne propriété, conservée pour compatibilité)",
        subtype='COLOR',
        default=(0.9, 0.9, 0.85),
        min=0.0,
        max=1.0,
        size=3
    )
    
    roof_color: FloatVectorProperty(
        name="Couleur toit",
        description="Couleur du toit",
        subtype='COLOR',
        default=(0.4, 0.2, 0.1),
        min=0.0,
        max=1.0,
        size=3,
        update=regenerate_house
    )
    
    roof_material_color: FloatVectorProperty(
        name="Couleur toit",
        description="Couleur du toit",
        subtype='COLOR',
        default=(0.3, 0.2, 0.15),
        min=0.0,
        max=1.0,
        size=3
    )
    
    floor_material_color: FloatVectorProperty(
        name="Couleur sol",
        description="Couleur du sol",
        subtype='COLOR',
        default=(0.7, 0.6, 0.5),
        min=0.0,
        max=1.0,
        size=3
    )

    # ============================================================
    # SOLS / FLOORING (SYSTÈME AVANCÉ)
    # ============================================================

    use_flooring_system: BoolProperty(
        name="Utiliser système de sols",
        description="Activer le système avancé de sols avec mesh détaillés",
        default=False,
        update=regenerate_house
    )

    flooring_type: EnumProperty(
        name="Type de sol",
        description="Type de revêtement de sol",
        items=[
            # Chaleureux et confortables
            ('HARDWOOD_SOLID', "Parquet Massif", "Bois véritable, très durable, élégant", 'MATERIAL', 0),
            ('HARDWOOD_ENGINEERED', "Parquet Contrecollé", "Plus stable et facile à poser", 'MATERIAL', 1),
            ('LAMINATE', "Stratifié", "Imitation bois, bon rapport qualité/prix", 'MATERIAL', 2),

            # Résistants et faciles d'entretien
            ('CERAMIC_TILE', "Carrelage Céramique", "Très résistant, idéal cuisine/salle de bain", 'MATERIAL', 3),
            ('PORCELAIN_TILE', "Grès Cérame", "Plus robuste, imite bois/pierre/béton", 'MATERIAL', 4),
            ('VINYL', "Vinyle/PVC", "Économique, étanche, en dalles ou lames", 'MATERIAL', 5),
            ('LINOLEUM', "Linoléum", "Naturel, solide, antibactérien", 'MATERIAL', 6),

            # Élégants et haut de gamme
            ('MARBLE', "Marbre", "Très esthétique, coûteux", 'MATERIAL', 7),
            ('NATURAL_STONE', "Pierre Naturelle", "Travertin, ardoise, granit", 'MATERIAL', 8),
            ('POLISHED_CONCRETE', "Béton Ciré", "Moderne, style contemporain", 'MATERIAL', 9),

            # Confort thermique/acoustique
            ('CARPET', "Moquette", "Absorbe le son, confortable", 'MATERIAL', 10),
            ('CORK', "Liège", "Naturel, isolant, résistant à l'humidité", 'MATERIAL', 11),
        ],
        default='HARDWOOD_SOLID',
        update=regenerate_house
    )

    flooring_quality: EnumProperty(
        name="Qualité mesh sols",
        description="Niveau de détail géométrique des sols",
        items=[
            ('LOW', "Basse", "Minimal, rapide", 0),
            ('MEDIUM', "Moyenne", "Bon équilibre", 1),
            ('HIGH', "Haute", "Très détaillé", 2),
            ('ULTRA', "Ultra", "Maximum de détails (lourd)", 3),
        ],
        default='HIGH',
        update=regenerate_house
    )

    # ============================================================
    # MURS INTÉRIEURS (SYSTÈME AVANCÉ)
    # ============================================================

    use_interior_walls_system: BoolProperty(
        name="Utiliser système murs intérieurs",
        description="Activer le système avancé de finitions murales intérieures",
        default=False,
        update=regenerate_house
    )

    interior_wall_finish: EnumProperty(
        name="Finition murs intérieurs",
        description="Type de finition pour les murs intérieurs",
        items=[
            ('PAINT', "Peinture", "Mur peint (nombreuses couleurs disponibles)", 'COLOR', 0),
            ('WALLPAPER', "Papier peint", "Papier peint avec motifs", 'TEXTURE', 1),
            ('WOOD_PANELING', "Lambris bois", "Panneaux de bois (chêne, pin, etc.)", 'MATERIAL', 2),
            ('EXPOSED_BRICK', "Brique apparente", "Mur en briques apparentes", 'MATERIAL', 3),
            ('NATURAL_STONE', "Pierre naturelle", "Pierre apparente", 'MATERIAL', 4),
            ('PLASTER', "Enduit", "Enduit décoratif (lisse, grain, etc.)", 'MATERIAL', 5),
        ],
        default='PAINT',
        update=regenerate_house
    )

    interior_wall_quality: EnumProperty(
        name="Qualité mesh murs intérieurs",
        description="Niveau de détail géométrique des murs intérieurs",
        items=[
            ('LOW', "Basse", "Minimal, rapide", 0),
            ('MEDIUM', "Moyenne", "Bon équilibre", 1),
            ('HIGH', "Haute", "Très détaillé", 2),
            ('ULTRA', "Ultra", "Maximum de détails (lourd)", 3),
        ],
        default='MEDIUM',
        update=regenerate_house
    )

    # ============================================================
    # MODE MANUEL
    # ============================================================
    
    exterior_wall_thickness: FloatProperty(
        name="Mur extérieur",
        description="Épaisseur des murs extérieurs",
        default=0.25,
        min=0.15,
        max=0.60,
        unit='LENGTH',
        precision=3
    )
    
    interior_wall_thickness: FloatProperty(
        name="Mur intérieur",
        description="Épaisseur des murs intérieurs",
        default=0.10,
        min=0.05,
        max=0.25,
        unit='LENGTH',
        precision=3
    )
    
    manual_floor_height: FloatProperty(
        name="Hauteur étage",
        description="Hauteur d'un étage en mode manuel",
        default=2.7,
        min=2.0,
        max=4.0,
        unit='LENGTH',
        precision=2
    )
    
    manual_door_height: FloatProperty(
        name="Hauteur porte",
        description="Hauteur standard des portes",
        default=2.1,
        min=1.8,
        max=2.5,
        unit='LENGTH',
        precision=2
    )
    
    manual_window_height: FloatProperty(
        name="Hauteur fenêtre",
        description="Hauteur standard des fenêtres",
        default=1.2,
        min=0.5,
        max=2.0,
        unit='LENGTH',
        precision=2
    )
    
    manual_window_sill_height: FloatProperty(
        name="Hauteur allège",
        description="Hauteur du bas de fenêtre par rapport au sol",
        default=0.9,
        min=0.3,
        max=1.5,
        unit='LENGTH',
        precision=2
    )
    
    plan_image_path: StringProperty(
        name="Chemin du plan",
        description="Chemin vers l'image du plan 2D",
        default="",
        subtype='FILE_PATH'
    )
    
    plan_scale: FloatProperty(
        name="Échelle du plan",
        description="Échelle du plan importé (mètres par pixel)",
        default=0.01,
        min=0.001,
        max=1.0,
        precision=4
    )
    
    plan_opacity: FloatProperty(
        name="Opacité du plan",
        description="Opacité de l'image de référence",
        default=0.5,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    # ============================================================
    # OPTIONS AVANCÉES
    # ============================================================
    
    auto_lighting: BoolProperty(
        name="Éclairage automatique",
        description="Ajouter des lumières à la scène",
        default=True
    )
    
    collection_name: StringProperty(
        name="Nom collection",
        description="Nom de la collection où créer la maison",
        default="House"
    )
    
    show_dimensions: BoolProperty(
        name="Afficher dimensions",
        description="Afficher les dimensions sur la maison",
        default=False
    )
    
    show_grid: BoolProperty(
        name="Afficher grille",
        description="Afficher une grille de référence",
        default=True
    )
    
    random_seed: IntProperty(
        name="Seed aléatoire",
        description="Seed pour la génération procédurale (0 = aléatoire)",
        default=0,
        min=0,
        max=999999
    )
    
    advanced_mode: BoolProperty(
        name="Mode avancé",
        description="Afficher les options avancées et le scripting Python",
        default=False
    )
    
    python_script: StringProperty(
        name="Script Python",
        description="Script Python personnalisé pour générer la maison",
        default=""
    )


# Classes à enregistrer
classes = (
    HouseGeneratorProperties,
)


def register():
    """Enregistrement des propriétés"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.house_generator = bpy.props.PointerProperty(type=HouseGeneratorProperties)
    bpy.types.Scene.house_auto_update = bpy.props.BoolProperty(
        name="Mise à jour auto",
        description="Régénérer automatiquement la maison quand les paramètres changent",
        default=False
    )
    
    print("[House] Propriétés enregistrées")
    print("  ✓ Système matériaux briques 3 modes (COLOR/PRESET/CUSTOM)")
    print("  ✓ Scan automatique textures PBR activé (lazy loading)")


def unregister():
    """Désenregistrement des propriétés"""
    del bpy.types.Scene.house_generator
    del bpy.types.Scene.house_auto_update
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("[House] Propriétés désenregistrées")