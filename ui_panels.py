# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - UI Panels Module
#  Copyright (C) 2025 mvaertan
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Panel


class HOUSE_PT_main_panel(Panel):
    """Panneau principal du générateur de maison"""
    bl_label = "House Generator"
    bl_idname = "HOUSE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        box = layout.box()
        box.label(text="Mode de génération", icon='SETTINGS')
        box.prop(props, "generation_mode", expand=True)
        
        if props.generation_mode == 'AUTO':
            self.draw_auto_mode(context, layout, props)
        else:
            self.draw_manual_mode(context, layout, props)
    
    def draw_auto_mode(self, context, layout, props):
        """Interface pour le mode automatique"""
        
        box = layout.box()
        box.label(text="Dimensions", icon='EMPTY_ARROWS')
        col = box.column(align=True)
        col.prop(props, "house_width")
        col.prop(props, "house_length")
        col.separator()
        col.prop(props, "num_floors")
        col.prop(props, "floor_height")
        
        box = layout.box()
        box.label(text="Style architectural", icon='HOME')
        box.prop(props, "architectural_style", text="")
        
        layout.separator()
        row = layout.row()
        row.scale_y = 2.0
        row.operator("house.generate_auto", text="Générer la maison", icon='HOME')
        
        layout.separator()
        row = layout.row()
        row.prop(context.scene, "house_auto_update", text="Mise à jour auto")
    
    def draw_manual_mode(self, context, layout, props):
        """Interface pour le mode manuel"""
        
        box = layout.box()
        box.label(text="Plan 2D", icon='IMAGE_DATA')
        box.prop(props, "plan_image_path", text="")
        box.prop(props, "plan_scale")
        box.prop(props, "plan_opacity")
        
        layout.separator()
        layout.operator("house.import_plan", text="Importer le plan", icon='IMPORT')
        layout.operator("house.generate_from_plan", text="Générer depuis le plan", icon='HOME')


class HOUSE_PT_roof_panel(Panel):
    """Panneau pour les paramètres du toit"""
    bl_label = "Toit"
    bl_idname = "HOUSE_PT_roof_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(props, "roof_type", text="Type")
        col.prop(props, "roof_pitch", text="Pente")
        col.prop(props, "roof_overhang", text="Débord")


class HOUSE_PT_windows_panel(Panel):
    """Panneau pour les paramètres des fenêtres"""
    bl_label = "Fenêtres"
    bl_idname = "HOUSE_PT_windows_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(props, "window_type", text="Type")
        col.prop(props, "window_quality", text="Qualité")
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(props, "window_width", text="Largeur")
        col.prop(props, "window_height", text="Hauteur")
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(props, "num_windows_front", text="Façade")
        col.prop(props, "num_windows_side", text="Côtés")


class HOUSE_PT_doors_panel(Panel):
    """Panneau pour les paramètres des portes"""
    bl_label = "Portes"
    bl_idname = "HOUSE_PT_doors_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(props, "front_door_width", text="Largeur porte")
        col.prop(props, "include_back_door", text="Porte arrière")


class HOUSE_PT_walls_panel(Panel):
    """Panneau pour les paramètres des murs"""
    bl_label = "Murs"
    bl_idname = "HOUSE_PT_walls_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        box = layout.box()
        box.label(text="Type de construction", icon='MESH_CUBE')
        box.prop(props, "wall_construction_type", text="")
        
        if props.wall_construction_type == 'BRICK_3D':
            box.separator()
            box.label(text="Qualité géométrie 3D:", icon='MESH_GRID')
            box.prop(props, "brick_3d_quality", text="")
            
            total_height = props.num_floors * props.floor_height
            brick_count_approx = int((props.house_width * 2 + props.house_length * 2) * total_height / 0.014)
            
            box.separator()
            info_box = box.box()
            info_box.label(text=f"Briques: {brick_count_approx:,}", icon='INFO')
            
            if props.brick_3d_quality == 'HIGH':
                info_box.label(text="Calcul intensif", icon='ERROR')
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(props, "wall_thickness", text="Épaisseur")


class HOUSE_PT_materials_panel(Panel):
    """Panneau pour les matériaux"""
    bl_label = "Matériaux"
    bl_idname = "HOUSE_PT_materials_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = False
        
        layout.prop(props, "use_materials", text="Utiliser les matériaux", toggle=True)
        
        if not props.use_materials:
            return
        
        layout.separator()
        
        # ============================================================
        # ✅ NOUVEAU : SYSTÈME DE MATÉRIAUX BRIQUES 3D
        # ============================================================
        
        box = layout.box()
        box.label(text="Murs extérieurs", icon='MATERIAL')
        
        col = box.column(align=True)
        
        # Si briques 3D : afficher le nouveau système
        if props.wall_construction_type == 'BRICK_3D':
            col.label(text="Mode matériau briques 3D:", icon='NODE_MATERIAL')
            col.prop(props, "brick_material_mode", text="")
            
            col.separator()
            
            # MODE COULEUR UNIE
            if props.brick_material_mode == 'COLOR':
                subbox = col.box()
                subbox.label(text="Couleur unie:", icon='COLOR')
                subbox.prop(props, "brick_solid_color", text="")
                
            # MODE PRESET RÉALISTE
            elif props.brick_material_mode == 'PRESET':
                subbox = col.box()
                subbox.label(text="Preset briques:", icon='TEXTURE')
                subbox.prop(props, "brick_preset_type", text="")
                
                # Afficher un aperçu du preset
                preset_colors = {
                    'BRICK_RED': "Rouge traditionnel",
                    'BRICK_RED_DARK': "Rouge foncé",
                    'BRICK_ORANGE': "Orangé/terre cuite",
                    'BRICK_BROWN': "Brun/chocolat",
                    'BRICK_YELLOW': "Jaune (London)",
                    'BRICK_GREY': "Gris moderne"
                }
                if props.brick_preset_type in preset_colors:
                    subbox.label(text=preset_colors[props.brick_preset_type], icon='COLORSET_01_VEC')
            
            # MODE CUSTOM
            elif props.brick_material_mode == 'CUSTOM':
                subbox = col.box()
                subbox.label(text="Matériau personnalisé:", icon='MATERIAL_DATA')
                subbox.prop(props, "brick_custom_material", text="")
                
                if not props.brick_custom_material:
                    warning = subbox.box()
                    warning.label(text="Aucun matériau sélectionné", icon='ERROR')
                    warning.label(text="Preset utilisé par défaut", icon='INFO')
        
        # Si murs simples : afficher l'ancien système (inchangé)
        else:
            col.label(text="Type de briques:", icon='MESH_CUBE')
            col.prop(props, "wall_material_type", text="")
            
            col.separator()
            col.label(text="Qualité matériau shader:", icon='SHADING_RENDERED')
            col.prop(props, "wall_brick_quality", text="")
            
            if props.wall_material_type == 'BRICK_PAINTED':
                col.separator()
                col.label(text="Couleur personnalisée:")
                col.prop(props, "wall_brick_color", text="")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="Toit", icon='MATERIAL')
        col = box.column(align=True)
        col.prop(props, "roof_color", text="Couleur")


class HOUSE_PT_elements_panel(Panel):
    """Panneau pour les éléments additionnels"""
    bl_label = "Éléments additionnels"
    bl_idname = "HOUSE_PT_elements_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        box = layout.box()
        row = box.row()
        row.prop(props, "include_garage", text="Garage", toggle=True)
        if props.include_garage:
            box.prop(props, "garage_size", text="")
        
        box = layout.box()
        box.prop(props, "include_terrace", text="Terrasse", toggle=True)
        
        box = layout.box()
        box.prop(props, "include_balcony", text="Balcon", toggle=True)
        
        box = layout.box()
        box.prop(props, "add_chimney", text="Cheminée", toggle=True)

        box = layout.box()
        box.label(text="Gouttières", icon='MOD_WAVE')
        row = box.row()
        row.prop(props, "add_gutters", text="Ajouter gouttières", toggle=True)

        if props.add_gutters:
            box.separator()
            col = box.column(align=True)
            col.label(text="Style:", icon='MESH_GRID')
            col.prop(props, "gutter_style", text="")

            col.separator()
            col.label(text="Matériau:", icon='MATERIAL')
            col.prop(props, "gutter_material_type", text="")

            # Info selon le style sélectionné
            style_descriptions = {
                'AUTO': "Adapté au style architectural",
                'HALF_ROUND': "Classique européen",
                'K_STYLE': "Moderne américain",
                'BOX': "Moderne/commercial",
                'EUROPEAN': "Trapézoïdale européenne",
            }

            material_descriptions = {
                'AUTO': "Adapté au style architectural",
                'ALUMINUM': "Léger et durable",
                'COPPER': "Élégant, haute gamme",
                'ZINC': "Moderne et durable",
                'PVC': "Économique",
                'STEEL': "Robuste",
            }

            if props.gutter_style in style_descriptions or props.gutter_material_type in material_descriptions:
                info_box = box.box()
                info_box.scale_y = 0.7
                if props.gutter_style in style_descriptions:
                    info_box.label(text=f"Style: {style_descriptions[props.gutter_style]}", icon='INFO')
                if props.gutter_material_type in material_descriptions:
                    info_box.label(text=f"Mat: {material_descriptions[props.gutter_material_type]}", icon='INFO')

            col.separator()
            col.label(text="Qualité:", icon='SHADING_RENDERED')
            col.prop(props, "gutter_quality", text="")

        layout.separator()
        box = layout.box()
        box.label(text="Fondations", icon='MESH_PLANE')
        box.prop(props, "foundation_height", text="Hauteur")


class HOUSE_PT_rooms_panel(Panel):
    """Panneau pour la distribution des pièces"""
    bl_label = "Distribution des pièces"
    bl_idname = "HOUSE_PT_rooms_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(props, "num_rooms", text="Pièces principales")
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(props, "include_kitchen", text="Cuisine")
        col.prop(props, "include_bathroom", text="Salle de bain")
        
        if props.include_bathroom:
            col.prop(props, "num_bathrooms", text="Nombre SDB")


class HOUSE_PT_flooring_panel(Panel):
    """Panneau pour les options de sols"""
    bl_label = "Sols"
    bl_idname = "HOUSE_PT_flooring_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator

        layout.use_property_split = False

        layout.prop(props, "use_flooring_system", text="Activer système sols", toggle=True)

        if not props.use_flooring_system:
            return

        layout.separator()

        box = layout.box()
        box.label(text="Type de revêtement", icon='MATERIAL')
        box.prop(props, "flooring_type", text="")

        layout.separator()

        # ============================================================
        # OPTIONS SELON TYPE DE SOL
        # ============================================================

        floor_type = props.flooring_type

        if floor_type in ['HARDWOOD_SOLID', 'HARDWOOD_ENGINEERED', 'LAMINATE']:
            # Options PARQUET/BOIS
            box = layout.box()
            box.label(text="Options bois", icon='MATERIAL')

            col = box.column(align=True)
            col.label(text="Essence de bois:", icon='COLORSET_05_VEC')
            col.prop(props, "parquet_wood_type", text="")

            # Info selon essence
            wood_info = {
                'OAK': "Chêne - Classique durable",
                'WALNUT': "Noyer - Brun foncé élégant",
                'MAPLE': "Érable - Clair moderne",
                'CHERRY': "Cerisier - Rougeâtre chaleureux",
                'ASH': "Frêne - Beige nervuré",
            }
            if props.parquet_wood_type in wood_info:
                info_box = box.box()
                info_box.scale_y = 0.7
                info_box.label(text=wood_info[props.parquet_wood_type], icon='INFO')

        elif floor_type in ['CERAMIC_TILE', 'PORCELAIN_TILE']:
            # Options CARRELAGE
            box = layout.box()
            box.label(text="Options carrelage", icon='MESH_GRID')

            col = box.column(align=True)
            col.label(text="Couleur:", icon='COLOR')
            col.prop(props, "tile_color_preset", text="")

            box.separator()
            col = box.column(align=True)
            col.label(text="Taille carreaux:", icon='MESH_PLANE')
            col.prop(props, "tile_size", text="")

            # Info
            info_box = box.box()
            info_box.scale_y = 0.7
            if props.tile_size <= 0.20:
                info_box.label(text="Petits carreaux (mosaïque)", icon='INFO')
            elif props.tile_size <= 0.40:
                info_box.label(text="Carreaux standard", icon='INFO')
            else:
                info_box.label(text="Grands carreaux (moderne)", icon='INFO')

        elif floor_type == 'MARBLE':
            # Options MARBRE
            box = layout.box()
            box.label(text="Marbre", icon='MESH_ICOSPHERE')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Élégant, haut de gamme", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        elif floor_type == 'NATURAL_STONE':
            # Options PIERRE
            box = layout.box()
            box.label(text="Pierre naturelle", icon='MESH_CUBE')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Travertin, ardoise, granit", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        elif floor_type == 'POLISHED_CONCRETE':
            # Options BÉTON CIRÉ
            box = layout.box()
            box.label(text="Béton ciré", icon='MESH_PLANE')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Moderne, contemporain", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        elif floor_type in ['VINYL', 'LINOLEUM']:
            # Options VINYLE/LINO
            box = layout.box()
            box.label(text="Vinyle/Linoléum", icon='MATERIAL')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Économique, étanche", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        elif floor_type == 'CARPET':
            # Options MOQUETTE
            box = layout.box()
            box.label(text="Moquette", icon='BRUSHES_ALL')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Confortable, absorbe le son", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        elif floor_type == 'CORK':
            # Options LIÈGE
            box = layout.box()
            box.label(text="Liège", icon='MATERIAL')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Naturel, isolant", icon='INFO')
            info_box.label(text="Options à venir", icon='INFO')

        layout.separator()

        box = layout.box()
        box.label(text="Qualité géométrie", icon='MESH_GRID')
        box.prop(props, "flooring_quality", text="")


class HOUSE_PT_interior_walls_panel(Panel):
    """Panneau pour les finitions des murs intérieurs"""
    bl_label = "Murs intérieurs"
    bl_idname = "HOUSE_PT_interior_walls_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator

        layout.use_property_split = False

        layout.prop(props, "use_interior_walls_system", text="Activer finitions intérieures", toggle=True)

        if not props.use_interior_walls_system:
            return

        layout.separator()

        box = layout.box()
        box.label(text="Finition murale", icon='MATERIAL')
        box.prop(props, "interior_wall_finish", text="")

        layout.separator()

        # ============================================================
        # OPTIONS SELON TYPE DE FINITION
        # ============================================================

        if props.interior_wall_finish == 'PAINT':
            # Options PEINTURE
            box = layout.box()
            box.label(text="Peinture", icon='COLOR')

            col = box.column(align=True)
            col.label(text="Couleur:", icon='COLORSET_01_VEC')
            col.prop(props, "paint_color_preset", text="")

            # Si couleur custom, afficher le color picker
            if props.paint_color_preset == 'CUSTOM':
                box.separator()
                col = box.column(align=True)
                col.label(text="Couleur personnalisée:", icon='BRUSH_DATA')
                col.prop(props, "paint_color_custom", text="")

            box.separator()
            col = box.column(align=True)
            col.label(text="Type de finition:", icon='SHADING_RENDERED')
            col.prop(props, "paint_type", text="")

            # Info sur le type de peinture
            paint_type_info = {
                'MAT': "Cache les imperfections",
                'SATINEE': "Lessivable, polyvalent",
                'BRILLANTE': "Très lessivable, reflets",
                'VELOURS': "Aspect doux, élégant",
            }
            if props.paint_type in paint_type_info:
                info_box = box.box()
                info_box.scale_y = 0.7
                info_box.label(text=paint_type_info[props.paint_type], icon='INFO')

        elif props.interior_wall_finish == 'WALLPAPER':
            # Options PAPIER PEINT
            box = layout.box()
            box.label(text="Papier peint", icon='TEXTURE')

            col = box.column(align=True)
            col.label(text="Image du motif:", icon='IMAGE_DATA')
            col.prop(props, "wallpaper_image_path", text="")

            # Info résolution recommandée
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Format: PNG/JPG", icon='INFO')
            info_box.label(text="Min: 1024×1024px", icon='INFO')
            info_box.label(text="Recommandé: 2048×2048px", icon='INFO')

            box.separator()
            col = box.column(align=True)
            col.label(text="Type de papier:", icon='MESH_GRID')
            col.prop(props, "wallpaper_type", text="")

        elif props.interior_wall_finish == 'WOOD_PANELING':
            # Options LAMBRIS BOIS
            box = layout.box()
            box.label(text="Lambris bois", icon='MATERIAL')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Types: Chêne, Pin, etc.", icon='INFO')
            info_box.label(text="À venir dans prochaine version", icon='INFO')

        elif props.interior_wall_finish == 'EXPOSED_BRICK':
            # Options BRIQUE APPARENTE
            box = layout.box()
            box.label(text="Brique apparente", icon='MESH_CUBE')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Style industriel/loft", icon='INFO')
            info_box.label(text="À venir dans prochaine version", icon='INFO')

        elif props.interior_wall_finish == 'NATURAL_STONE':
            # Options PIERRE NATURELLE
            box = layout.box()
            box.label(text="Pierre naturelle", icon='MESH_ICOSPHERE')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Ardoise, granit, etc.", icon='INFO')
            info_box.label(text="À venir dans prochaine version", icon='INFO')

        elif props.interior_wall_finish == 'PLASTER':
            # Options ENDUIT
            box = layout.box()
            box.label(text="Enduit décoratif", icon='BRUSHES_ALL')
            info_box = box.box()
            info_box.scale_y = 0.7
            info_box.label(text="Lisse, grain, etc.", icon='INFO')
            info_box.label(text="À venir dans prochaine version", icon='INFO')

        layout.separator()

        box = layout.box()
        box.label(text="Qualité géométrie", icon='MESH_GRID')
        box.prop(props, "interior_wall_quality", text="")


class HOUSE_PT_advanced_panel(Panel):
    """Panneau pour les options avancées"""
    bl_label = "Options avancées"
    bl_idname = "HOUSE_PT_advanced_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_parent_id = "HOUSE_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        layout.use_property_split = True
        layout.use_property_decorate = False
        
        col = layout.column(align=True)
        col.prop(props, "auto_lighting", text="Éclairage auto")
        col.prop(props, "show_dimensions", text="Afficher dimensions")
        col.prop(props, "show_grid", text="Afficher grille")
        
        layout.separator()
        
        col = layout.column(align=True)
        col.prop(props, "collection_name", text="Collection")
        col.prop(props, "random_seed", text="Seed aléatoire")


class HOUSE_PT_info_panel(Panel):
    """Panneau d'informations"""
    bl_label = "Informations"
    bl_idname = "HOUSE_PT_info_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'House'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.house_generator
        
        total_height = props.num_floors * props.floor_height
        total_area = props.house_width * props.house_length
        wall_perimeter = 2 * (props.house_width + props.house_length)
        
        box = layout.box()
        box.label(text="Statistiques", icon='INFO')
        
        col = box.column(align=True)
        col.label(text=f"Surface: {total_area:.1f} m²")
        col.label(text=f"Hauteur totale: {total_height:.1f} m")
        col.label(text=f"Périmètre: {wall_perimeter:.1f} m")
        
        if props.wall_construction_type == 'BRICK_3D':
            brick_count = int(wall_perimeter * total_height / 0.014)
            col.separator()
            col.label(text=f"Briques: {brick_count:,}")
        
        layout.separator()
        
        box = layout.box()
        box.label(text="À propos", icon='QUESTION')
        col = box.column(align=True)
        col.label(text="House Generator v1.0")
        col.label(text="© 2025 mvaertan")
        
        layout.separator()
        layout.operator("wm.url_open", text="Documentation", icon='URL').url = "https://github.com/mvaertan/house-generator"


classes = (
    HOUSE_PT_main_panel,
    HOUSE_PT_roof_panel,
    HOUSE_PT_windows_panel,
    HOUSE_PT_doors_panel,
    HOUSE_PT_walls_panel,
    HOUSE_PT_flooring_panel,
    HOUSE_PT_interior_walls_panel,
    HOUSE_PT_materials_panel,
    HOUSE_PT_elements_panel,
    HOUSE_PT_rooms_panel,
    HOUSE_PT_advanced_panel,
    HOUSE_PT_info_panel,
)


def register():
    """Enregistrement des panneaux UI"""
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[House] Panneaux UI enregistrés")
    print("  ✓ Interface système matériaux briques (COLOR/PRESET/CUSTOM)")


def unregister():
    """Désenregistrement des panneaux UI"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("[House] Panneaux UI désenregistrés")