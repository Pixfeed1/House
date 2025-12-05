# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Propriétés Blender pour le système de distribution des pièces.

Ce fichier définit les PropertyGroups pour l'interface utilisateur :
- RoomItemProperty : Une pièce dans la liste
- RoomLayoutProperties : Configuration globale du layout

Ces propriétés doivent être intégrées dans le properties.py principal
de l'addon House.
"""

import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    BoolProperty,
    EnumProperty,
    CollectionProperty,
    PointerProperty,
)
from bpy.types import PropertyGroup

from .room_types import (
    ROOM_TYPES,
    HOUSING_PRESETS,
    get_enum_items_for_blender,
    get_preset_enum_items_for_blender,
)


# =============================================================================
# CALLBACKS
# =============================================================================

def _update_preset(self, context):
    """Callback quand le preset change."""
    if self.housing_preset == 'CUSTOM':
        return

    preset = HOUSING_PRESETS.get(self.housing_preset)
    if not preset:
        return

    # Reconstruire la liste des pièces
    self.rooms.clear()

    for room_type_id, count, area_override in preset.rooms:
        room_def = ROOM_TYPES.get(room_type_id)
        if not room_def:
            continue

        for i in range(count):
            item = self.rooms.add()
            item.room_type = room_type_id
            item.target_area = area_override if area_override else room_def.area_default
            item.name = f"{room_def.name} {i+1}" if count > 1 else room_def.name


def _update_room_type(self, context):
    """Callback quand le type de pièce change."""
    room_def = ROOM_TYPES.get(self.room_type)
    if room_def:
        # Mettre à jour les limites
        self.area_min = room_def.area_min
        self.area_max = room_def.area_max

        # Réinitialiser la surface si hors limites
        if self.target_area < room_def.area_min:
            self.target_area = room_def.area_default
        elif self.target_area > room_def.area_max:
            self.target_area = room_def.area_max


def _get_room_type_items(self, context):
    """Génère dynamiquement les items du menu déroulant des types de pièces."""
    return get_enum_items_for_blender()


def _get_preset_items(self, context):
    """Génère dynamiquement les items du menu déroulant des presets."""
    return get_preset_enum_items_for_blender()


# =============================================================================
# PROPERTY GROUPS
# =============================================================================

class RoomItemProperty(PropertyGroup):
    """
    Représente une pièce dans la liste des pièces.

    Permet à l'utilisateur de personnaliser chaque pièce :
    - Type (salon, chambre, etc.)
    - Surface cible
    - Étage (pour multi-étages)
    """

    # Nom affiché dans la liste
    name: StringProperty(
        name="Nom",
        description="Nom de la pièce",
        default="Pièce"
    )

    # Type de pièce
    room_type: EnumProperty(
        name="Type",
        description="Type de pièce",
        items=_get_room_type_items,
        update=_update_room_type
    )

    # Surface cible
    target_area: FloatProperty(
        name="Surface",
        description="Surface cible en m²",
        default=10.0,
        min=1.0,
        max=100.0,
        step=50,  # 0.5m² par clic
        precision=1,
        unit='AREA',
        subtype='NONE'
    )

    # Limites (mises à jour automatiquement)
    area_min: FloatProperty(
        name="Min",
        default=3.0,
        options={'HIDDEN'}
    )

    area_max: FloatProperty(
        name="Max",
        default=50.0,
        options={'HIDDEN'}
    )

    # Étage (pour multi-étages)
    floor: IntProperty(
        name="Étage",
        description="Étage de la pièce (0 = RDC)",
        default=0,
        min=0,
        max=5
    )

    # État (pour feedback)
    is_placed: BoolProperty(
        name="Placée",
        description="La pièce a-t-elle été placée avec succès",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    has_warning: BoolProperty(
        name="Avertissement",
        description="La pièce a un avertissement",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    warning_message: StringProperty(
        name="Message",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'}
    )


class RoomLayoutProperties(PropertyGroup):
    """
    Propriétés globales pour la configuration du layout.

    Contient :
    - Mode (preset ou personnalisé)
    - Liste des pièces
    - Options de génération
    """

    # -------------------------------------------------------------------------
    # MODE ET PRESET
    # -------------------------------------------------------------------------

    housing_preset: EnumProperty(
        name="Type de logement",
        description="Preset de configuration du logement",
        items=_get_preset_items,
        default=2,  # T3 par défaut (index dans la liste)
        update=_update_preset
    )

    # -------------------------------------------------------------------------
    # LISTE DES PIÈCES
    # -------------------------------------------------------------------------

    rooms: CollectionProperty(
        type=RoomItemProperty,
        name="Pièces",
        description="Liste des pièces à générer"
    )

    rooms_index: IntProperty(
        name="Index",
        description="Index de la pièce sélectionnée",
        default=0
    )

    # -------------------------------------------------------------------------
    # OPTIONS DE GÉNÉRATION
    # -------------------------------------------------------------------------

    # Couloir
    corridor_width: FloatProperty(
        name="Largeur couloir",
        description="Largeur du couloir de distribution",
        default=1.0,
        min=0.80,
        max=1.50,
        step=5,
        precision=2,
        unit='LENGTH'
    )

    auto_corridor: BoolProperty(
        name="Couloir automatique",
        description="Générer automatiquement un couloir si nécessaire",
        default=True
    )

    # Escalier
    has_staircase: BoolProperty(
        name="Escalier",
        description="Réserver une zone pour l'escalier",
        default=False
    )

    staircase_position: EnumProperty(
        name="Position escalier",
        description="Position de l'escalier dans le plan",
        items=[
            ('CORNER_SW', "Coin Sud-Ouest", "Escalier dans le coin sud-ouest"),
            ('CORNER_SE', "Coin Sud-Est", "Escalier dans le coin sud-est"),
            ('CORNER_NW', "Coin Nord-Ouest", "Escalier dans le coin nord-ouest"),
            ('CORNER_NE', "Coin Nord-Est", "Escalier dans le coin nord-est"),
            ('SIDE_W', "Côté Ouest", "Escalier centré sur le mur ouest"),
            ('SIDE_E', "Côté Est", "Escalier centré sur le mur est"),
            ('CENTER', "Centre", "Escalier au centre"),
        ],
        default='CORNER_SW'
    )

    staircase_type: EnumProperty(
        name="Type escalier",
        description="Type d'escalier",
        items=[
            ('STRAIGHT', "Droit", "Escalier droit (3.5m × 1m)"),
            ('QUARTER', "Quart tournant", "Escalier quart tournant (2.5m × 2m)"),
            ('HALF', "Demi tournant", "Escalier demi tournant (2m × 2.5m)"),
        ],
        default='QUARTER'
    )

    # Cloisons
    wall_thickness: FloatProperty(
        name="Épaisseur cloisons",
        description="Épaisseur des cloisons intérieures",
        default=0.10,
        min=0.07,
        max=0.20,
        step=1,
        precision=2,
        unit='LENGTH'
    )

    wall_height: FloatProperty(
        name="Hauteur sous plafond",
        description="Hauteur des murs intérieurs",
        default=2.50,
        min=2.20,
        max=4.00,
        step=10,
        precision=2,
        unit='LENGTH'
    )

    # Portes
    door_width: FloatProperty(
        name="Largeur portes",
        description="Largeur des portes intérieures",
        default=0.83,
        min=0.63,
        max=1.20,
        step=1,
        precision=2,
        unit='LENGTH'
    )

    door_height: FloatProperty(
        name="Hauteur portes",
        description="Hauteur des portes intérieures",
        default=2.04,
        min=1.80,
        max=2.50,
        step=1,
        precision=2,
        unit='LENGTH'
    )

    generate_door_frames: BoolProperty(
        name="Cadres de portes",
        description="Générer les cadres de portes",
        default=True
    )

    # -------------------------------------------------------------------------
    # OPTIONS AVANCÉES
    # -------------------------------------------------------------------------

    show_advanced: BoolProperty(
        name="Options avancées",
        description="Afficher les options avancées",
        default=False
    )

    optimization_level: EnumProperty(
        name="Optimisation",
        description="Niveau d'optimisation du placement",
        items=[
            ('FAST', "Rapide", "Placement glouton, rapide mais moins optimal"),
            ('BALANCED', "Équilibré", "Bon compromis vitesse/qualité"),
            ('QUALITY', "Qualité", "Optimisation poussée, plus lent"),
        ],
        default='BALANCED'
    )

    random_seed: IntProperty(
        name="Graine aléatoire",
        description="Graine pour la génération (0 = aléatoire)",
        default=0,
        min=0,
        max=999999
    )

    # -------------------------------------------------------------------------
    # RÉSULTATS (lecture seule)
    # -------------------------------------------------------------------------

    last_generation_success: BoolProperty(
        name="Succès",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    last_generation_message: StringProperty(
        name="Message",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    last_generation_score: FloatProperty(
        name="Score",
        default=0.0,
        options={'HIDDEN', 'SKIP_SAVE'}
    )

    # -------------------------------------------------------------------------
    # MÉTHODES UTILITAIRES
    # -------------------------------------------------------------------------

    def get_rooms_list(self) -> list:
        """
        Retourne la liste des pièces au format attendu par le solver.

        Returns:
            Liste de tuples (room_type_id, target_area)
        """
        return [(room.room_type, room.target_area) for room in self.rooms]

    def get_total_requested_area(self) -> float:
        """Retourne la surface totale demandée."""
        return sum(room.target_area for room in self.rooms)

    def add_room(self, room_type: str, area: float = None) -> RoomItemProperty:
        """
        Ajoute une pièce à la liste.

        Args:
            room_type: ID du type de pièce
            area: Surface cible (optionnel, utilise défaut si None)

        Returns:
            L'item créé
        """
        room_def = ROOM_TYPES.get(room_type)
        if not room_def:
            return None

        item = self.rooms.add()
        item.room_type = room_type
        item.target_area = area if area else room_def.area_default
        item.name = room_def.name

        # Numéroter si plusieurs du même type
        count = sum(1 for r in self.rooms if r.room_type == room_type)
        if count > 1:
            item.name = f"{room_def.name} {count}"

        return item

    def remove_room(self, index: int) -> bool:
        """
        Supprime une pièce de la liste.

        Args:
            index: Index de la pièce à supprimer

        Returns:
            True si supprimé, False sinon
        """
        if 0 <= index < len(self.rooms):
            self.rooms.remove(index)
            if self.rooms_index >= len(self.rooms):
                self.rooms_index = max(0, len(self.rooms) - 1)
            return True
        return False

    def clear_rooms(self) -> None:
        """Supprime toutes les pièces."""
        self.rooms.clear()
        self.rooms_index = 0

    def apply_preset(self, preset_id: str) -> bool:
        """
        Applique un preset.

        Args:
            preset_id: ID du preset à appliquer

        Returns:
            True si appliqué, False sinon
        """
        if preset_id not in HOUSING_PRESETS and preset_id != 'CUSTOM':
            return False

        self.housing_preset = preset_id
        _update_preset(self, None)
        return True


# =============================================================================
# OPÉRATEURS POUR LA LISTE
# =============================================================================

class ROOM_OT_add(bpy.types.Operator):
    """Ajoute une pièce à la liste"""
    bl_idname = "room.add"
    bl_label = "Ajouter une pièce"
    bl_options = {'REGISTER', 'UNDO'}

    room_type: EnumProperty(
        name="Type",
        items=_get_room_type_items
    )

    def execute(self, context):
        props = context.scene.room_layout
        props.add_room(self.room_type)
        props.rooms_index = len(props.rooms) - 1

        # Passer en mode personnalisé
        if props.housing_preset != 'CUSTOM':
            props.housing_preset = 'CUSTOM'

        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class ROOM_OT_remove(bpy.types.Operator):
    """Supprime la pièce sélectionnée"""
    bl_idname = "room.remove"
    bl_label = "Supprimer la pièce"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.room_layout
        return len(props.rooms) > 0

    def execute(self, context):
        props = context.scene.room_layout
        props.remove_room(props.rooms_index)

        # Passer en mode personnalisé
        if props.housing_preset != 'CUSTOM':
            props.housing_preset = 'CUSTOM'

        return {'FINISHED'}


class ROOM_OT_move(bpy.types.Operator):
    """Déplace une pièce dans la liste"""
    bl_idname = "room.move"
    bl_label = "Déplacer la pièce"
    bl_options = {'REGISTER', 'UNDO'}

    direction: EnumProperty(
        items=[
            ('UP', "Haut", ""),
            ('DOWN', "Bas", ""),
        ]
    )

    @classmethod
    def poll(cls, context):
        props = context.scene.room_layout
        return len(props.rooms) > 1

    def execute(self, context):
        props = context.scene.room_layout
        index = props.rooms_index

        if self.direction == 'UP' and index > 0:
            props.rooms.move(index, index - 1)
            props.rooms_index -= 1
        elif self.direction == 'DOWN' and index < len(props.rooms) - 1:
            props.rooms.move(index, index + 1)
            props.rooms_index += 1

        return {'FINISHED'}


class ROOM_OT_duplicate(bpy.types.Operator):
    """Duplique la pièce sélectionnée"""
    bl_idname = "room.duplicate"
    bl_label = "Dupliquer la pièce"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.room_layout
        return len(props.rooms) > 0

    def execute(self, context):
        props = context.scene.room_layout

        if props.rooms_index >= 0 and props.rooms_index < len(props.rooms):
            source = props.rooms[props.rooms_index]
            props.add_room(source.room_type, source.target_area)

            # Passer en mode personnalisé
            if props.housing_preset != 'CUSTOM':
                props.housing_preset = 'CUSTOM'

        return {'FINISHED'}


# =============================================================================
# UI LIST
# =============================================================================

class ROOM_UL_list(bpy.types.UIList):
    """Liste des pièces dans l'interface."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        room_def = ROOM_TYPES.get(item.room_type)
        icon_name = room_def.icon if room_def else 'QUESTION'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            # Icône de statut
            if item.has_warning:
                row.label(text="", icon='ERROR')
            elif item.is_placed:
                row.label(text="", icon='CHECKMARK')
            else:
                row.label(text="", icon='RADIOBUT_OFF')

            # Type de pièce
            row.prop(item, "room_type", text="", icon=icon_name, emboss=False)

            # Surface
            row.prop(item, "target_area", text="", emboss=True)
            row.label(text="m²")

        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon=icon_name)


# =============================================================================
# ENREGISTREMENT
# =============================================================================

classes = [
    RoomItemProperty,
    RoomLayoutProperties,
    ROOM_OT_add,
    ROOM_OT_remove,
    ROOM_OT_move,
    ROOM_OT_duplicate,
    ROOM_UL_list,
]


def register():
    """Enregistre les classes et propriétés."""
    for cls in classes:
        bpy.utils.register_class(cls)

    # Ajouter la propriété à la scène
    bpy.types.Scene.room_layout = PointerProperty(type=RoomLayoutProperties)


def unregister():
    """Désenregistre les classes et propriétés."""
    # Supprimer la propriété
    if hasattr(bpy.types.Scene, 'room_layout'):
        del bpy.types.Scene.room_layout

    # Désenregistrer les classes dans l'ordre inverse
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
