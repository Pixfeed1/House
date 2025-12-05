# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Panneaux d'interface utilisateur pour le système room_layout.

Ce fichier définit les panneaux UI pour :
- Sélection du type de logement (preset)
- Configuration personnalisée des pièces
- Options de génération
- Aperçu et validation
"""

import bpy
from bpy.types import Panel, Menu

from .room_types import ROOM_TYPES, HOUSING_PRESETS, RoomCategory


# =============================================================================
# MENUS
# =============================================================================

class ROOM_MT_add_menu(Menu):
    """Menu pour ajouter une pièce par catégorie."""
    bl_idname = "ROOM_MT_add_menu"
    bl_label = "Ajouter une pièce"

    def draw(self, context):
        layout = self.layout

        # Grouper par catégorie
        categories = {}
        for room_id, room_def in ROOM_TYPES.items():
            cat = room_def.category
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((room_id, room_def))

        # Ordre des catégories
        cat_order = [
            (RoomCategory.LIVING, "Pièces de vie"),
            (RoomCategory.SLEEPING, "Chambres"),
            (RoomCategory.SERVICE, "Service"),
            (RoomCategory.CIRCULATION, "Circulation"),
            (RoomCategory.WORK, "Travail"),
        ]

        for cat, cat_name in cat_order:
            if cat in categories:
                layout.label(text=cat_name)
                for room_id, room_def in categories[cat]:
                    op = layout.operator(
                        "room.add",
                        text=f"{room_def.name} ({room_def.area_default}m²)",
                        icon=room_def.icon
                    )
                    op.room_type = room_id
                layout.separator()


class ROOM_MT_preset_menu(Menu):
    """Menu pour sélectionner un preset."""
    bl_idname = "ROOM_MT_preset_menu"
    bl_label = "Presets"

    def draw(self, context):
        layout = self.layout

        for preset_id, preset in HOUSING_PRESETS.items():
            op = layout.operator(
                "room.apply_preset",
                text=preset.name,
                icon='HOME'
            )
            op.preset_id = preset_id

        layout.separator()
        op = layout.operator(
            "room.apply_preset",
            text="Personnalisé",
            icon='MODIFIER'
        )
        op.preset_id = 'CUSTOM'


# =============================================================================
# OPÉRATEUR PRESET
# =============================================================================

class ROOM_OT_apply_preset(bpy.types.Operator):
    """Applique un preset de logement"""
    bl_idname = "room.apply_preset"
    bl_label = "Appliquer le preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_id: bpy.props.StringProperty()

    def execute(self, context):
        props = context.scene.room_layout

        if self.preset_id == 'CUSTOM':
            props.housing_preset = 'CUSTOM'
            self.report({'INFO'}, "Mode personnalisé activé")
        elif props.apply_preset(self.preset_id):
            self.report({'INFO'}, f"Preset {self.preset_id} appliqué")
        else:
            self.report({'WARNING'}, f"Preset {self.preset_id} inconnu")
            return {'CANCELLED'}

        return {'FINISHED'}


# =============================================================================
# PANNEAU PRINCIPAL
# =============================================================================

class ROOM_PT_layout_main(Panel):
    """Panneau principal de configuration du layout."""
    bl_idname = "ROOM_PT_layout_main"
    bl_label = "Distribution des pièces"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_order = 30

    def draw_header(self, context):
        layout = self.layout
        layout.label(text="", icon='MOD_BUILD')

    def draw(self, context):
        layout = self.layout
        props = context.scene.room_layout

        # =====================================================================
        # SECTION PRESET
        # =====================================================================

        box = layout.box()
        row = box.row()
        row.label(text="Type de logement", icon='HOME')

        row = box.row(align=True)
        row.prop(props, "housing_preset", text="")
        row.menu("ROOM_MT_preset_menu", text="", icon='DOWNARROW_HLT')

        # Afficher les infos du preset
        if props.housing_preset != 'CUSTOM':
            preset = HOUSING_PRESETS.get(props.housing_preset)
            if preset:
                col = box.column(align=True)
                col.scale_y = 0.8
                col.label(text=preset.description, icon='INFO')
                col.label(text=f"Surface recommandée : {preset.area_recommended}m²")

        # =====================================================================
        # SECTION LISTE DES PIÈCES
        # =====================================================================

        box = layout.box()
        row = box.row()
        row.label(text="Pièces", icon='MESH_CUBE')
        row.label(text=f"({len(props.rooms)} pièces, {props.get_total_requested_area():.0f}m²)")

        # Liste avec UIList
        row = box.row()
        row.template_list(
            "ROOM_UL_list", "",
            props, "rooms",
            props, "rooms_index",
            rows=4
        )

        # Boutons de contrôle
        col = row.column(align=True)
        col.menu("ROOM_MT_add_menu", text="", icon='ADD')
        col.operator("room.remove", text="", icon='REMOVE')
        col.separator()
        col.operator("room.move", text="", icon='TRIA_UP').direction = 'UP'
        col.operator("room.move", text="", icon='TRIA_DOWN').direction = 'DOWN'
        col.separator()
        col.operator("room.duplicate", text="", icon='DUPLICATE')

        # Détails de la pièce sélectionnée
        if props.rooms_index >= 0 and props.rooms_index < len(props.rooms):
            room = props.rooms[props.rooms_index]
            room_def = ROOM_TYPES.get(room.room_type)

            col = box.column(align=True)
            col.separator()

            row = col.row(align=True)
            row.prop(room, "room_type", text="Type")

            row = col.row(align=True)
            row.prop(room, "target_area", text="Surface")

            if room_def:
                sub = col.row(align=True)
                sub.scale_y = 0.7
                sub.enabled = False
                sub.label(text=f"Min: {room_def.area_min}m²")
                sub.label(text=f"Défaut: {room_def.area_default}m²")
                sub.label(text=f"Max: {room_def.area_max}m²")

                if room.target_area < room_def.area_min:
                    col.label(text="⚠ Surface en dessous du minimum", icon='ERROR')

            if room.has_warning:
                col.label(text=room.warning_message, icon='ERROR')


class ROOM_PT_layout_options(Panel):
    """Sous-panneau pour les options de génération."""
    bl_idname = "ROOM_PT_layout_options"
    bl_label = "Options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "ROOM_PT_layout_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.room_layout

        # Couloir
        box = layout.box()
        row = box.row()
        row.prop(props, "auto_corridor", text="Couloir automatique")

        if props.auto_corridor:
            row = box.row()
            row.prop(props, "corridor_width", text="Largeur")

        # Escalier
        box = layout.box()
        row = box.row()
        row.prop(props, "has_staircase", text="Réserver escalier")

        if props.has_staircase:
            col = box.column(align=True)
            col.prop(props, "staircase_type", text="Type")
            col.prop(props, "staircase_position", text="Position")

        # Cloisons
        box = layout.box()
        box.label(text="Cloisons", icon='MOD_SOLIDIFY')

        col = box.column(align=True)
        col.prop(props, "wall_thickness", text="Épaisseur")
        col.prop(props, "wall_height", text="Hauteur")

        # Portes
        box = layout.box()
        box.label(text="Portes", icon='MESH_PLANE')

        col = box.column(align=True)
        col.prop(props, "door_width", text="Largeur")
        col.prop(props, "door_height", text="Hauteur")
        row = col.row()
        row.prop(props, "generate_door_frames", text="Générer les cadres")


class ROOM_PT_layout_advanced(Panel):
    """Sous-panneau pour les options avancées."""
    bl_idname = "ROOM_PT_layout_advanced"
    bl_label = "Avancé"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "ROOM_PT_layout_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.room_layout

        col = layout.column(align=True)
        col.prop(props, "optimization_level", text="Optimisation")
        col.prop(props, "random_seed", text="Graine aléatoire")

        if props.last_generation_message:
            box = layout.box()
            box.label(text="Dernière génération", icon='INFO')

            if props.last_generation_success:
                box.label(text="✓ Succès", icon='CHECKMARK')
                box.label(text=f"Score: {props.last_generation_score:.1f}")
            else:
                box.label(text="✗ Échec", icon='ERROR')

            for line in props.last_generation_message.split('\n'):
                if line.strip():
                    box.label(text=line)


class ROOM_PT_layout_generate(Panel):
    """Sous-panneau avec le bouton de génération."""
    bl_idname = "ROOM_PT_layout_generate"
    bl_label = "Génération"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "ROOM_PT_layout_main"

    def draw(self, context):
        layout = self.layout
        props = context.scene.room_layout
        house_props = getattr(context.scene, 'house_properties', None)

        can_generate = True
        warnings = []

        if len(props.rooms) == 0:
            can_generate = False
            warnings.append("Aucune pièce définie")

        if house_props:
            width = house_props.house_width
            depth = house_props.house_depth
            area = width * depth
            requested = props.get_total_requested_area()

            if requested > area * 0.95:
                warnings.append(f"Surface demandée ({requested:.0f}m²) > disponible ({area:.0f}m²)")

        if warnings:
            box = layout.box()
            for warn in warnings:
                box.label(text=warn, icon='ERROR')

        row = layout.row(align=True)
        row.scale_y = 1.5
        row.enabled = can_generate
        row.operator("room.generate_layout", text="Générer le plan", icon='MOD_BUILD')

        row = layout.row(align=True)
        row.operator("room.preview_layout", text="Aperçu 2D", icon='OUTLINER_OB_GREASEPENCIL')


# =============================================================================
# OPÉRATEURS DE GÉNÉRATION
# =============================================================================

class ROOM_OT_generate_layout(bpy.types.Operator):
    """Génère la distribution des pièces"""
    bl_idname = "room.generate_layout"
    bl_label = "Générer le plan"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        props = context.scene.room_layout
        return len(props.rooms) > 0

    def execute(self, context):
        from . import RoomLayoutManager, SolverConfig, GeometryConfig, PlacementStrategy

        props = context.scene.room_layout
        house_props = getattr(context.scene, 'house_properties', None)

        if house_props:
            width = house_props.house_width
            depth = house_props.house_depth
        else:
            width = 10.0
            depth = 12.0

        solver_config = SolverConfig(
            wall_thickness=props.wall_thickness,
            door_width=props.door_width,
            door_height=props.door_height,
            random_seed=props.random_seed if props.random_seed > 0 else None,
        )

        geometry_config = GeometryConfig(
            wall_thickness=props.wall_thickness,
            wall_height=props.wall_height,
            door_width=props.door_width,
            door_height=props.door_height,
            generate_door_frames=props.generate_door_frames,
        )

        manager = RoomLayoutManager(
            solver_config=solver_config,
            geometry_config=geometry_config
        )

        stair_pos = None
        if props.has_staircase:
            stair_pos = props.staircase_position.replace('CORNER_', '').replace('SIDE_', '')

        result = manager.generate_layout(
            width=width,
            depth=depth,
            preset_id='CUSTOM',
            custom_rooms=props.get_rooms_list(),
            staircase_position=stair_pos
        )

        props.last_generation_success = result.success
        props.last_generation_score = result.score

        if result.messages:
            props.last_generation_message = '\n'.join(result.messages)
        elif result.warnings:
            props.last_generation_message = '\n'.join(result.warnings)
        else:
            props.last_generation_message = ""

        if result.floor_plan:
            for room_prop in props.rooms:
                room_obj = result.floor_plan.get_room_by_id(room_prop.room_type)
                if room_obj:
                    room_prop.is_placed = room_obj.is_placed
                    valid, warnings = room_obj.validate_placement(result.floor_plan.bounds)
                    room_prop.has_warning = len(warnings) > 0
                    room_prop.warning_message = warnings[0] if warnings else ""

        if result.success:
            try:
                manager.build_geometry(
                    result.floor_plan,
                    collection_name="Interior_Walls",
                    floor_z=0.0
                )
                self.report({'INFO'}, f"Plan généré avec succès (score: {result.score:.1f})")
            except Exception as e:
                self.report({'WARNING'}, f"Plan généré mais erreur géométrie: {str(e)}")
        else:
            self.report({'ERROR'}, f"Échec: {result.messages[0] if result.messages else 'Erreur inconnue'}")
            return {'CANCELLED'}

        return {'FINISHED'}


class ROOM_OT_preview_layout(bpy.types.Operator):
    """Affiche un aperçu 2D du plan"""
    bl_idname = "room.preview_layout"
    bl_label = "Aperçu du plan"
    bl_options = {'REGISTER'}

    def execute(self, context):
        from . import RoomLayoutManager, SolverConfig
        from .geometry import RoomMarkerBuilder

        props = context.scene.room_layout
        house_props = getattr(context.scene, 'house_properties', None)

        if house_props:
            width = house_props.house_width
            depth = house_props.house_depth
        else:
            width = 10.0
            depth = 12.0

        solver_config = SolverConfig(wall_thickness=props.wall_thickness)
        manager = RoomLayoutManager(solver_config=solver_config)

        result = manager.generate_layout(
            width=width,
            depth=depth,
            preset_id='CUSTOM',
            custom_rooms=props.get_rooms_list()
        )

        if result.success and result.floor_plan:
            coll_name = "RoomLayout_Preview"
            if coll_name in bpy.data.collections:
                coll = bpy.data.collections[coll_name]
                for obj in list(coll.objects):
                    bpy.data.objects.remove(obj, do_unlink=True)
            else:
                coll = bpy.data.collections.new(coll_name)
                context.scene.collection.children.link(coll)

            RoomMarkerBuilder.create_floor_plan_outline(result.floor_plan, coll)
            RoomMarkerBuilder.create_room_markers(result.floor_plan, coll)

            self.report({'INFO'}, "Aperçu généré")
        else:
            self.report({'WARNING'}, "Impossible de générer l'aperçu")

        return {'FINISHED'}


# =============================================================================
# ENREGISTREMENT
# =============================================================================

classes = [
    ROOM_MT_add_menu,
    ROOM_MT_preset_menu,
    ROOM_OT_apply_preset,
    ROOM_OT_generate_layout,
    ROOM_OT_preview_layout,
    ROOM_PT_layout_main,
    ROOM_PT_layout_options,
    ROOM_PT_layout_advanced,
    ROOM_PT_layout_generate,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
