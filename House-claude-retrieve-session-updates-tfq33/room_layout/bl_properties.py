# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Propriétés Blender pour le système de distribution des pièces.

Définit toutes les PropertyGroups utilisées dans l'interface.
"""

import bpy
from bpy.props import (
    StringProperty, FloatProperty, IntProperty, BoolProperty,
    EnumProperty, CollectionProperty, PointerProperty, FloatVectorProperty
)
from bpy.types import PropertyGroup

from .room_types import get_enum_items_for_blender, get_preset_enum_items_for_blender


# =============================================================================
# PROPRIÉTÉS D'UNE PIÈCE
# =============================================================================

class RoomItemProperty(PropertyGroup):
    """Représente une pièce dans la liste des pièces à placer."""
    
    room_type: EnumProperty(
        name="Type",
        description="Type de pièce",
        items=get_enum_items_for_blender,
    )
    
    area: FloatProperty(
        name="Surface",
        description="Surface souhaitée en m²",
        default=12.0,
        min=1.0,
        max=100.0,
        unit='AREA',
        subtype='UNSIGNED'
    )
    
    # Propriétés calculées après placement (lecture seule dans l'UI)
    actual_area: FloatProperty(
        name="Surface réelle",
        description="Surface obtenue après placement",
        default=0.0,
        unit='AREA'
    )
    
    is_placed: BoolProperty(
        name="Placée",
        description="La pièce a-t-elle été placée",
        default=False
    )
    
    has_window: BoolProperty(
        name="Fenêtre",
        description="La pièce a-t-elle une fenêtre",
        default=False
    )


# =============================================================================
# PROPRIÉTÉS D'UNE PORTE
# =============================================================================

class DoorItemProperty(PropertyGroup):
    """Représente une porte dans la liste des portes générées."""
    
    # Identification
    door_id: StringProperty(
        name="ID",
        description="Identifiant unique de la porte"
    )
    
    # Pièces connectées (lecture seule, pour affichage)
    room1_name: StringProperty(
        name="Pièce 1",
        description="Première pièce connectée"
    )
    
    room2_name: StringProperty(
        name="Pièce 2",
        description="Deuxième pièce connectée (vide si extérieur)"
    )
    
    # Type de porte
    door_type: EnumProperty(
        name="Type",
        description="Type de porte",
        items=[
            ('STANDARD', "Battante", "Porte battante classique", 'MESH_PLANE', 0),
            ('SLIDING', "Coulissante", "Porte coulissante", 'ARROW_LEFTRIGHT', 1),
            ('POCKET', "Galandage", "Porte à galandage (dans le mur)", 'FULLSCREEN_EXIT', 2),
            ('DOUBLE', "Double", "Porte double battant", 'MOD_MIRROR', 3),
            ('ENTRY', "Entrée", "Porte d'entrée principale", 'HOME', 4),
        ],
        default='STANDARD'
    )
    
    # Dimensions
    width: FloatProperty(
        name="Largeur",
        description="Largeur de la porte",
        default=0.83,
        min=0.63,
        max=1.80,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    height: FloatProperty(
        name="Hauteur",
        description="Hauteur de la porte",
        default=2.04,
        min=1.80,
        max=2.50,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    # Sens d'ouverture
    swing_direction: EnumProperty(
        name="Sens",
        description="Sens d'ouverture de la porte",
        items=[
            ('PUSH', "Pousser", "S'ouvre en poussant (vers pièce 2)", 'FORWARD', 0),
            ('PULL', "Tirer", "S'ouvre en tirant (vers pièce 1)", 'BACK', 1),
        ],
        default='PUSH'
    )
    
    # Côté charnières
    hinge_side: EnumProperty(
        name="Charnières",
        description="Côté des charnières (vu depuis pièce 1)",
        items=[
            ('LEFT', "Gauche", "Charnières à gauche", 'TRIA_LEFT', 0),
            ('RIGHT', "Droite", "Charnières à droite", 'TRIA_RIGHT', 1),
        ],
        default='LEFT'
    )
    
    # Style visuel
    style: EnumProperty(
        name="Style",
        description="Style visuel de la porte",
        items=[
            ('PLAIN', "Pleine", "Porte pleine sans vitrage", 'MESH_PLANE', 0),
            ('GLAZED', "Vitrée", "Porte avec vitrage central", 'MESH_GRID', 1),
            ('HALF_GLAZED', "Semi-vitrée", "Vitrée en partie haute", 'SEQ_SPLITVIEW', 2),
            ('PANELED', "À panneaux", "Porte avec moulures", 'MESH_CUBE', 3),
            ('FLUSH', "Plane", "Porte moderne sans relief", 'MATPLANE', 4),
        ],
        default='PLAIN'
    )
    
    # Type de poignée
    handle_type: EnumProperty(
        name="Poignée",
        description="Type de poignée",
        items=[
            ('LEVER', "Levier", "Poignée bec-de-cane (levier)", 'ORIENTATION_VIEW', 0),
            ('KNOB', "Bouton", "Poignée bouton rond", 'MESH_UVSPHERE', 1),
            ('PULL_BAR', "Barre", "Barre de tirage", 'GRIP', 2),
            ('RECESSED', "Encastrée", "Poignée encastrée", 'SELECT_SET', 3),
            ('NONE', "Aucune", "Sans poignée visible", 'X', 4),
        ],
        default='LEVER'
    )
    
    # Options
    has_lock: BoolProperty(
        name="Serrure",
        description="La porte a une serrure/verrou",
        default=False
    )
    
    is_accessible: BoolProperty(
        name="PMR",
        description="Conforme accessibilité PMR (≥0.90m)",
        default=False
    )
    
    is_fire_rated: BoolProperty(
        name="Coupe-feu",
        description="Porte coupe-feu",
        default=False
    )
    
    # État pour visualisation
    is_open: BoolProperty(
        name="Ouverte",
        description="Afficher la porte ouverte",
        default=False
    )


# =============================================================================
# PROPRIÉTÉS PRINCIPALES DU LAYOUT
# =============================================================================

class RoomLayoutProperties(PropertyGroup):
    """Propriétés principales du système de distribution des pièces."""
    
    # -------------------------------------------------------------------------
    # DIMENSIONS DU BÂTIMENT
    # -------------------------------------------------------------------------
    
    building_width: FloatProperty(
        name="Largeur",
        description="Largeur du bâtiment (axe X)",
        default=10.0,
        min=4.0,
        max=50.0,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    building_depth: FloatProperty(
        name="Profondeur",
        description="Profondeur du bâtiment (axe Y)",
        default=8.0,
        min=4.0,
        max=50.0,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    floor_height: FloatProperty(
        name="Hauteur sous plafond",
        description="Hauteur des murs intérieurs",
        default=2.50,
        min=2.20,
        max=4.00,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    num_floors: IntProperty(
        name="Nombre d'étages",
        description="Nombre d'étages (1 = RDC seul)",
        default=1,
        min=1,
        max=5
    )
    
    # -------------------------------------------------------------------------
    # MURS
    # -------------------------------------------------------------------------
    
    exterior_wall_thickness: FloatProperty(
        name="Murs extérieurs",
        description="Épaisseur des murs extérieurs",
        default=0.20,
        min=0.15,
        max=0.50,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    interior_wall_thickness: FloatProperty(
        name="Cloisons",
        description="Épaisseur des cloisons intérieures",
        default=0.10,
        min=0.05,
        max=0.20,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    # -------------------------------------------------------------------------
    # PRESET ET PIÈCES
    # -------------------------------------------------------------------------
    
    housing_preset: EnumProperty(
        name="Preset",
        description="Configuration prédéfinie du logement",
        items=get_preset_enum_items_for_blender,
        default='T3'
    )
    
    # Liste des pièces personnalisées
    rooms: CollectionProperty(
        type=RoomItemProperty,
        name="Pièces"
    )
    
    rooms_index: IntProperty(
        name="Index pièce",
        description="Index de la pièce sélectionnée",
        default=0
    )
    
    # -------------------------------------------------------------------------
    # PORTES - OPTIONS GLOBALES
    # -------------------------------------------------------------------------
    
    door_default_width: FloatProperty(
        name="Largeur par défaut",
        description="Largeur par défaut des portes intérieures",
        default=0.83,
        min=0.63,
        max=1.20,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    door_default_height: FloatProperty(
        name="Hauteur par défaut",
        description="Hauteur par défaut des portes",
        default=2.04,
        min=1.80,
        max=2.50,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    door_entry_width: FloatProperty(
        name="Largeur entrée",
        description="Largeur de la porte d'entrée",
        default=0.90,
        min=0.80,
        max=1.20,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    door_generate_frames: BoolProperty(
        name="Cadres",
        description="Générer les cadres de portes (huisseries)",
        default=True
    )
    
    door_generate_panels: BoolProperty(
        name="Vantaux",
        description="Générer les panneaux de porte (vantaux)",
        default=True
    )
    
    door_generate_handles: BoolProperty(
        name="Poignées",
        description="Générer les poignées (des deux côtés)",
        default=True
    )
    
    door_generate_hinges: BoolProperty(
        name="Charnières",
        description="Générer les charnières",
        default=True
    )
    
    door_show_open: BoolProperty(
        name="Portes ouvertes",
        description="Afficher les portes entrouvertes (30°)",
        default=False
    )
    
    door_pmr_mode: BoolProperty(
        name="Mode PMR",
        description="Forcer les largeurs PMR (0.90m minimum)",
        default=False
    )
    
    door_generate_entry: BoolProperty(
        name="Porte d'entrée",
        description="Générer automatiquement la porte d'entrée principale",
        default=True
    )
    
    # Liste des portes générées
    doors: CollectionProperty(
        type=DoorItemProperty,
        name="Portes"
    )
    
    doors_index: IntProperty(
        name="Index porte",
        description="Index de la porte sélectionnée",
        default=0
    )
    
    # -------------------------------------------------------------------------
    # FENÊTRES
    # -------------------------------------------------------------------------
    
    window_width: FloatProperty(
        name="Largeur fenêtres",
        description="Largeur par défaut des fenêtres",
        default=1.20,
        min=0.60,
        max=3.00,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    window_height: FloatProperty(
        name="Hauteur fenêtres",
        description="Hauteur par défaut des fenêtres",
        default=1.20,
        min=0.60,
        max=2.20,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    window_sill_height: FloatProperty(
        name="Allège",
        description="Hauteur d'allège (sous la fenêtre)",
        default=0.90,
        min=0.0,
        max=1.20,
        unit='LENGTH',
        subtype='DISTANCE'
    )
    
    # -------------------------------------------------------------------------
    # OPTIONS DE GÉNÉRATION
    # -------------------------------------------------------------------------
    
    generate_exterior_walls: BoolProperty(
        name="Murs extérieurs",
        description="Générer les murs extérieurs",
        default=True
    )
    
    generate_interior_walls: BoolProperty(
        name="Cloisons",
        description="Générer les cloisons intérieures",
        default=True
    )
    
    generate_floor: BoolProperty(
        name="Sol",
        description="Générer le plancher",
        default=True
    )
    
    generate_ceiling: BoolProperty(
        name="Plafond",
        description="Générer le plafond",
        default=False
    )
    
    generate_room_markers: BoolProperty(
        name="Marqueurs",
        description="Générer des marqueurs pour identifier les pièces",
        default=True
    )
    
    # -------------------------------------------------------------------------
    # COULEURS ET MATÉRIAUX
    # -------------------------------------------------------------------------
    
    wall_color: FloatVectorProperty(
        name="Couleur murs",
        description="Couleur des murs intérieurs",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.9, 0.9, 0.88, 1.0)
    )
    
    door_frame_color: FloatVectorProperty(
        name="Couleur cadres",
        description="Couleur des cadres de portes",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.55, 0.40, 0.25, 1.0)
    )
    
    door_panel_color: FloatVectorProperty(
        name="Couleur portes",
        description="Couleur des panneaux de portes",
        subtype='COLOR',
        size=4,
        min=0.0, max=1.0,
        default=(0.95, 0.95, 0.93, 1.0)
    )
    
    # -------------------------------------------------------------------------
    # ÉTAT
    # -------------------------------------------------------------------------
    
    is_generated: BoolProperty(
        name="Généré",
        description="Un plan a été généré",
        default=False
    )
    
    last_generation_score: FloatProperty(
        name="Score",
        description="Score du dernier plan généré",
        default=0.0
    )
    
    show_advanced: BoolProperty(
        name="Options avancées",
        description="Afficher les options avancées",
        default=False
    )


# =============================================================================
# FONCTIONS DE MISE À JOUR
# =============================================================================

def update_rooms_from_preset(self, context):
    """Met à jour la liste des pièces quand le preset change."""
    from .room_types import HOUSING_PRESETS, ROOM_TYPES
    
    props = context.scene.room_layout
    preset_id = props.housing_preset
    
    if preset_id == 'CUSTOM':
        return
    
    if preset_id not in HOUSING_PRESETS:
        return
    
    preset = HOUSING_PRESETS[preset_id]
    rooms_list = preset.get_rooms_list()
    
    # Vider la liste actuelle
    props.rooms.clear()
    
    # Ajouter les nouvelles pièces
    for room_type_id, area in rooms_list:
        item = props.rooms.add()
        item.room_type = room_type_id
        item.area = area


def sync_doors_from_floor_plan(props, floor_plan):
    """
    Synchronise la liste des portes UI avec le FloorPlan.
    
    Appelé après la génération pour mettre à jour l'interface.
    """
    props.doors.clear()
    
    for door in floor_plan.doors:
        item = props.doors.add()
        item.door_id = door.id
        
        # Noms des pièces
        room1 = floor_plan.get_room_by_id(door.room1_id)
        item.room1_name = room1.name if room1 else door.room1_id
        
        if door.room2_id:
            room2 = floor_plan.get_room_by_id(door.room2_id)
            item.room2_name = room2.name if room2 else door.room2_id
        else:
            item.room2_name = "Extérieur"
        
        # Type
        item.door_type = door.door_type.name
        
        # Dimensions
        item.width = door.width
        item.height = door.height
        
        # Comportement
        item.swing_direction = door.swing_direction.name
        item.hinge_side = door.hinge_side.name
        
        # Style
        item.style = door.style.name
        item.handle_type = door.handle_type.name
        
        # Options
        item.has_lock = door.has_lock
        item.is_accessible = door.is_accessible
        item.is_fire_rated = door.is_fire_rated


# =============================================================================
# ENREGISTREMENT
# =============================================================================

classes = [
    RoomItemProperty,
    DoorItemProperty,
    RoomLayoutProperties,
]


def register():
    """Enregistre les propriétés."""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.room_layout = PointerProperty(type=RoomLayoutProperties)


def unregister():
    """Désenregistre les propriétés."""
    del bpy.types.Scene.room_layout
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
