# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Automatic Generation Operators Module (BLENDER 4.2+ COMPATIBLE)
#  Copyright (C) 2025 mvaertan
#  ULTIMATE EDITION - Système complet de matériaux briques
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from bpy.types import Operator
from mathutils import Vector, Matrix
import math
import random

# Import du module de fenêtres
from .windows import WindowGenerator

# Import du système de sols avancé
from .flooring import FlooringGenerator, QUALITY_LOW, QUALITY_MEDIUM, QUALITY_HIGH, QUALITY_ULTRA

# ============================================================
# MODE DEBUG (activer pour logs détaillés)
# ============================================================
# NOTE BUG #10: DEBUG_MODE est actuellement hardcodé
# TODO: Considérer de le déplacer vers les préférences (properties.py) pour permettre
# un toggle via l'interface Blender sans éditer le code source
DEBUG_MODE = False  # Mettre à True pour debug détaillé

# ============================================================
# Constantes - Dimensions et épaisseurs
# ============================================================
WALL_THICKNESS = 0.25
FLOOR_THICKNESS = 0.2
FOUNDATION_THICKNESS = 0.3
ROOF_THICKNESS_FLAT = 0.3
ROOF_THICKNESS_PITCHED = 0.15

# Constantes - Ouvertures
OPENING_OFFSET = 0.02
DOOR_HEIGHT = 2.1
DOOR_DEPTH_EXTRA = 0.1
WINDOW_WIDTH = 1.2
WINDOW_DEPTH_EXTRA = 0.1
WINDOW_SPACING_INTERVAL = 3.0

# Constantes - Proportions
FLOOR_INSET = 0.95
WINDOW_HEIGHT_DEFAULT = 0.4

# Constantes - Garage
GARAGE_WIDTH_SINGLE = 3.0
GARAGE_WIDTH_DOUBLE = 6.0
GARAGE_LENGTH = 5.0
GARAGE_HEIGHT = 2.5
GARAGE_OFFSET = 1.0
GARAGE_ROOF_OVERHANG = 0.3
GARAGE_DOOR_WIDTH_RATIO = 0.9
GARAGE_DOOR_HEIGHT_RATIO = 0.8

# Constantes - Terrasse
TERRACE_WIDTH_RATIO = 0.8
TERRACE_LENGTH = 3.0
TERRACE_HEIGHT = 0.2
TERRACE_OFFSET = 0.5

# Constantes - Balcon et Rambarde
BALCONY_WIDTH_RATIO = 0.6
BALCONY_DEPTH = 1.5
BALCONY_HEIGHT = 0.15
BALCONY_RAILING_HEIGHT = 1.0
BALCONY_RAILING_THICKNESS = 0.05
BALCONY_POST_SIZE = 0.08
BALCONY_POST_SPACING = 0.5

# Constantes - Matériaux
MATERIAL_ROUGHNESS = 0.7
BMESH_MERGE_DISTANCE = 0.001

# Couleurs par défaut
DEFAULT_WALL_COLOR = (0.9, 0.9, 0.85)
DEFAULT_ROOF_COLOR = (0.3, 0.2, 0.15)
DEFAULT_FLOOR_COLOR = (0.7, 0.6, 0.5)


class HOUSE_OT_generate_auto(Operator):
    """Génère automatiquement une maison selon les paramètres"""
    bl_idname = "house.generate_auto"
    bl_label = "Générer la maison"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.house_generator

        # ✅ VALIDATION : Vérifier les paramètres
        validation_error = self._validate_parameters(props)
        if validation_error:
            self.report({'ERROR'}, validation_error)
            return {'CANCELLED'}

        # Initialiser real_wall_height pour éviter AttributeError
        self.real_wall_height = None

        print("[House] Début de la génération...")
        self.report({'INFO'}, "Génération de la maison en cours...")

        # Mode debug
        if DEBUG_MODE:
            print(f"[DEBUG] Dimensions: {props.house_width}m × {props.house_length}m")
            print(f"[DEBUG] Étages: {props.num_floors}, Hauteur étage: {props.floor_height}m")
            print(f"[DEBUG] Toit: {props.roof_type}, Pente: {props.roof_pitch}°")
            print(f"[DEBUG] Murs: {props.wall_construction_type}, Qualité briques: {props.brick_3d_quality if props.wall_construction_type == 'BRICK_3D' else 'N/A'}")

        if props.random_seed > 0:
            random.seed(props.random_seed)
            print(f"[House] Seed: {props.random_seed}")

        # Initialiser la barre de progression
        wm = context.window_manager
        wm.progress_begin(0, 100)
        progress = 0

        try:
            # Appliquer le style architectural
            style_config = self._apply_architectural_style(props)
            print(f"[House] Style architectural: {props.architectural_style}")
            progress += 5
            wm.progress_update(progress)

            house_collection = self._create_house_collection(context)
            progress += 5
            wm.progress_update(progress)

            print("[House] Fondations...")
            self._generate_foundation(context, props, house_collection)
            progress += 10
            wm.progress_update(progress)

            print("[House] Murs...")
            walls = self._generate_walls(context, props, house_collection)
            progress += 20
            wm.progress_update(progress)

            print("[House] Planchers...")
            self._generate_floors(context, props, house_collection)
            progress += 10
            wm.progress_update(progress)

            print("[House] Toit...")
            self._generate_roof(context, props, house_collection)
            progress += 15
            wm.progress_update(progress)
            
            # Perçage des murs SEULEMENT si MUR SIMPLE
            if props.wall_construction_type != 'BRICK_3D':
                print("[House] Perçage des murs (portes et fenêtres)...")
                self._generate_wall_openings(context, props, house_collection, walls, style_config)
            else:
                print("[House] Murs en briques 3D : ouvertures déjà intégrées")
            progress += 10
            wm.progress_update(progress)

            print(f"[House] Fenêtres complètes 3D (type: {props.window_type}, qualité: {props.window_quality})...")
            self._generate_windows_complete(context, props, house_collection, style_config)
            progress += 10
            wm.progress_update(progress)

            if props.include_garage:
                print("[House] Garage...")
                self._generate_garage(context, props, house_collection)
                progress += 5
                wm.progress_update(progress)

            if props.include_terrace or style_config.get('terrace_enabled', False):
                print("[House] Terrasse...")
                self._generate_terrace(context, props, house_collection)
                progress += 3
                wm.progress_update(progress)

            if (props.include_balcony and props.num_floors > 1) or style_config.get('balcony_enabled', False):
                print("[House] Balcon...")
                self._generate_balcony(context, props, house_collection)
                progress += 3
                wm.progress_update(progress)

            if props.use_materials:
                print("[House] Matériaux...")
                self._apply_materials(context, props, house_collection, style_config)
                progress += 10
                wm.progress_update(progress)

            # Éclairage automatique
            if props.auto_lighting:
                print("[House] Éclairage automatique...")
                self._add_scene_lighting(context, props)
                progress += 4
                wm.progress_update(progress)
            
            # Finaliser la progression
            wm.progress_update(100)

            print(f"[House] Terminé! Style: {props.architectural_style}, Fenêtres: {props.window_type}")
            self.report({'INFO'}, f"Maison générée! Style: {props.architectural_style}, Fenêtres: {props.window_type}")

        except Exception as e:
            wm.progress_end()
            print(f"[House] ERREUR: {str(e)}")
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, f"Erreur: {str(e)}")
            return {'CANCELLED'}

        wm.progress_end()
        self.report({'INFO'}, "Maison générée avec succès!")
        return {'FINISHED'}

    def _validate_parameters(self, props):
        """Valide les paramètres de génération

        Returns:
            str: Message d'erreur si invalide, None si valide
        """
        # Dimensions minimales/maximales
        if props.house_width < 3.0:
            return "Largeur minimale : 3m"
        if props.house_width > 50.0:
            return "Largeur maximale : 50m"
        if props.house_length < 3.0:
            return "Longueur minimale : 3m"
        if props.house_length > 50.0:
            return "Longueur maximale : 50m"

        # Hauteur d'étage réaliste
        if props.floor_height < 2.2:
            return "Hauteur d'étage minimale : 2.2m"
        if props.floor_height > 5.0:
            return "Hauteur d'étage maximale : 5m"

        # Pente de toit
        if props.roof_pitch < 5.0:
            return "Pente de toit minimale : 5°"
        if props.roof_pitch > 75.0:
            return "Pente de toit maximale : 75°"

        # Warning pour GAMBREL avec pente faible
        if props.roof_type == 'GAMBREL' and props.roof_pitch < 20.0:
            # Pas d'erreur, juste un warning (sera affiché dans execute)
            print(f"[House] ⚠️ Toit mansarde : pente faible ({props.roof_pitch}°), résultat peu esthétique (recommandé: 20-45°)")

        # Débord de toit réaliste
        if props.roof_overhang < 0.0:
            return "Débord de toit minimal : 0m"
        if props.roof_overhang > 2.0:
            return "Débord de toit maximal : 2m"

        # Matériau custom pour briques
        if props.wall_construction_type == 'BRICK_3D' and props.brick_material_mode == 'CUSTOM' and not props.brick_custom_material:
            return "Mode matériau custom sélectionné mais aucun matériau défini"

        return None  # Tout est valide

    def _apply_architectural_style(self, props):
        """Applique les variations selon le style architectural"""
        style = props.architectural_style
        
        if style == 'MODERN':
            return self._get_modern_style()
        elif style == 'TRADITIONAL':
            return self._get_traditional_style()
        elif style == 'MEDITERRANEAN':
            return self._get_mediterranean_style()
        elif style == 'CONTEMPORARY':
            return self._get_contemporary_style()
        elif style == 'ASIAN':
            return self._get_asian_style()
        else:
            return self._get_modern_style()
    
    def _get_modern_style(self):
        """Style moderne"""
        return {
            'wall_color': (0.95, 0.95, 0.95),
            'roof_color': (0.2, 0.2, 0.2),
            'floor_color': (0.7, 0.7, 0.7),
            'window_height_ratio': 0.6,
            'balcony_enabled': False,
            'terrace_enabled': True
        }
    
    def _get_traditional_style(self):
        """Style traditionnel"""
        return {
            'wall_color': (0.85, 0.75, 0.65),
            'roof_color': (0.4, 0.25, 0.2),
            'floor_color': (0.6, 0.5, 0.4),
            'window_height_ratio': 0.45,
            'balcony_enabled': False,
            'terrace_enabled': False
        }
    
    def _get_mediterranean_style(self):
        """Style méditerranéen"""
        return {
            'wall_color': (0.95, 0.9, 0.8),
            'roof_color': (0.7, 0.3, 0.2),
            'floor_color': (0.8, 0.6, 0.4),
            'window_height_ratio': 0.5,
            'balcony_enabled': True,
            'terrace_enabled': True
        }
    
    def _get_contemporary_style(self):
        """Style contemporain"""
        return {
            'wall_color': (0.3, 0.3, 0.35),
            'roof_color': (0.15, 0.15, 0.15),
            'floor_color': (0.5, 0.5, 0.5),
            'window_height_ratio': 0.55,
            'balcony_enabled': True,
            'terrace_enabled': True
        }
    
    def _get_asian_style(self):
        """Style asiatique"""
        return {
            'wall_color': (0.9, 0.85, 0.75),
            'roof_color': (0.15, 0.1, 0.08),
            'floor_color': (0.55, 0.45, 0.35),
            'window_height_ratio': 0.5,
            'balcony_enabled': True,
            'terrace_enabled': True
        }
    
    def _colors_are_default(self, user_color, default_color):
        """Vérifie si l'utilisateur a modifié les couleurs par défaut"""
        tolerance = 0.01
        return all(abs(user_color[i] - default_color[i]) < tolerance for i in range(3))
    
    def _create_house_collection(self, context):
        """Crée une collection pour la maison"""
        collection_name = "House"

        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
            for obj in list(collection.objects):
                # Unlink from all collections before removing (Blender 4.2 compatibility)
                for coll in bpy.data.collections:
                    # ✅ FIX BUG #2: Utiliser `obj in coll.objects` au lieu de `obj.name in coll.objects`
                    # bpy_prop_collection supporte les deux mais `in` avec objet est plus robuste
                    if obj in coll.objects:
                        try:
                            coll.objects.unlink(obj)
                        except (RuntimeError, ReferenceError) as e:
                            # Objet déjà unlinked ou invalide, continuer
                            print(f"[House] ⚠️ Impossible de unlink {obj.name}: {e}")
                bpy.data.objects.remove(obj, do_unlink=True)
        else:
            collection = bpy.data.collections.new(collection_name)
            context.scene.collection.children.link(collection)

        return collection
    
    def _create_box_mesh(self, name, location, dimensions):
        """Crée un mesh box aux dimensions exactes"""
        mesh = bpy.data.meshes.new(name)
        bm = bmesh.new()
        
        try:
            bmesh.ops.create_cube(bm, size=1.0)

            scale_matrix = Matrix.Diagonal((*dimensions, 1.0))
            bmesh.ops.transform(bm, matrix=scale_matrix, verts=bm.verts)

            bm.normal_update()

            bm.to_mesh(mesh)
            mesh.update()
            
        finally:
            bm.free()
        
        obj = bpy.data.objects.new(name, mesh)
        obj.location = location
        
        return obj, mesh
    
    def _create_mesh_from_bmesh(self, name, bm):
        """Crée un mesh à partir d'un bmesh"""
        mesh = bpy.data.meshes.new(name)
        
        try:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=BMESH_MERGE_DISTANCE)
            bm.normal_update()

            bm.to_mesh(mesh)
            mesh.update()
            
        except Exception as e:
            print(f"[House] Erreur mesh {name}: {e}")
            raise
        
        obj = bpy.data.objects.new(name, mesh)
        return obj, mesh
    
    def _generate_foundation(self, context, props, collection):
        """Génère les fondations"""
        width = props.house_width
        length = props.house_length
        thickness = FOUNDATION_THICKNESS
        
        location = Vector((width/2, length/2, -thickness/2))
        dimensions = Vector((width, length, thickness))
        
        foundation, mesh = self._create_box_mesh("Foundation", location, dimensions)
        collection.objects.link(foundation)
        foundation["house_part"] = "floor"
        
        return foundation
    
    def _calculate_safe_window_count(self, wall_length, dimension_name="largeur"):
        """✅ FIX BUG #4: Calcule le nombre de fenêtres sans chevauchement

        Sécurité niveau 1: Validation des paramètres d'entrée
        Sécurité niveau 2: Calcul mathématique avec espacement minimum
        Sécurité niveau 3: Vérification du résultat (pas de division par zéro)
        Sécurité niveau 4: Warnings si maison trop petite
        Sécurité niveau 5: Logging pour debug

        Args:
            wall_length: Longueur du mur en mètres
            dimension_name: Nom pour les messages (debug)

        Returns:
            int: Nombre de fenêtres sécuritaire (1 minimum, jamais de chevauchement)
        """
        # === SÉCURITÉ NIVEAU 1: Validation entrées ===
        if wall_length <= 0:
            print(f"[House] ⚠️ Longueur mur invalide: {wall_length}m, utilisation 1 fenêtre par défaut")
            return 1

        # === SÉCURITÉ NIVEAU 2: Calcul avec espacement minimum ===
        window_width = WINDOW_WIDTH  # 1.2m
        min_spacing = 0.5  # Espacement minimum entre fenêtres (sécurité architecturale)
        min_edge_spacing = 0.3  # Espacement minimum depuis les bords

        # Formule: wall_length >= edge_spacing + n*window_width + (n-1)*spacing + edge_spacing
        # Simplification: wall_length >= 2*edge + n*window_width + (n-1)*spacing
        # wall_length - 2*edge >= n*window_width + n*spacing - spacing
        # wall_length - 2*edge + spacing >= n*(window_width + spacing)
        # n <= (wall_length - 2*edge + spacing) / (window_width + spacing)

        try:
            available_space = wall_length - 2 * min_edge_spacing + min_spacing
            max_windows = int(available_space / (window_width + min_spacing))
        except (ZeroDivisionError, ValueError) as e:
            print(f"[House] ⚠️ Erreur calcul fenêtres: {e}, utilisation 1 fenêtre")
            return 1

        # === SÉCURITÉ NIVEAU 3: Validation résultat ===
        # Minimum absolu: 1 fenêtre
        # Maximum raisonnable: basé sur l'ancien système (éviter régression)
        old_system_max = max(2, int(wall_length / WINDOW_SPACING_INTERVAL))
        safe_count = max(1, min(max_windows, old_system_max))

        # === SÉCURITÉ NIVEAU 4: Warnings si maison trop petite ===
        if safe_count < 2 and wall_length >= 3.0:
            print(f"[House] ⚠️ Mur {dimension_name} ({wall_length:.1f}m) trop petit pour 2 fenêtres")
            print(f"[House]    → 1 fenêtre générée pour éviter chevauchement")
            print(f"[House]    → Recommandé: {dimension_name} ≥ {2*min_edge_spacing + 2*window_width + min_spacing:.1f}m pour 2 fenêtres")

        # Vérification espacement réel (double sécurité)
        actual_spacing = wall_length / (safe_count + 1)
        min_required_space_per_window = window_width + min_spacing

        if actual_spacing < min_required_space_per_window and safe_count > 1:
            # Réduction forcée si l'espacement calculé est encore trop petit
            safe_count = max(1, safe_count - 1)
            print(f"[House] ⚠️ Réduction fenêtres à {safe_count} pour garantir espacement minimum")

        # === SÉCURITÉ NIVEAU 5: Logging (mode production) ===
        if DEBUG_MODE:
            print(f"[House] Fenêtres {dimension_name}: {safe_count} pour {wall_length:.1f}m")
            print(f"[House]    - Espacement: {actual_spacing:.2f}m")
            print(f"[House]    - Ancien système: {old_system_max}, Nouveau: {safe_count}")

        return safe_count

    def _generate_walls(self, context, props, collection):
        """Génère les murs extérieurs (SIMPLE ou BRIQUES 3D) - ULTIMATE"""

        # === SI BRIQUES 3D : NOUVEAU SYSTÈME COMPLET ===
        if props.wall_construction_type == 'BRICK_3D':
            print(f"[House] Génération murs en briques 3D (qualité: {props.brick_3d_quality})")
            print(f"[House] Mode matériau: {props.brick_material_mode}")
            
            from .materials import brick_geometry
            
            width = props.house_width
            length = props.house_length
            total_height = props.num_floors * props.floor_height
            
            # Calculer les ouvertures
            openings = self._calculate_openings_for_brick_walls(props)
            print(f"[House] {len(openings)} ouvertures calculées")
            
            # ✅ NOUVEAU : Préparer les paramètres matériau selon le mode
            brick_material_mode = props.brick_material_mode
            brick_color = None
            brick_preset = 'BRICK_RED'
            custom_material = None
            
            if brick_material_mode == 'COLOR':
                # Mode couleur unie
                brick_color = props.brick_solid_color
                print(f"[House] Couleur unie: {brick_color}")
            elif brick_material_mode == 'PRESET':
                # Mode preset
                brick_preset = props.brick_preset_type
                print(f"[House] Preset: {brick_preset}")
            elif brick_material_mode == 'CUSTOM':
                # Mode matériau custom
                custom_material = props.brick_custom_material
                if custom_material:
                    print(f"[House] Matériau custom: {custom_material.name}")
                else:
                    print(f"[House] ATTENTION : Pas de matériau custom défini, utilisation preset par défaut")
                    self.report({'WARNING'}, "Pas de matériau custom défini, utilisation du preset par défaut")
                    brick_material_mode = 'PRESET'
            
            # Générer les murs avec le nouveau système
            # ✅ FIX : Capturer la hauteur réelle des murs pour positionner le toit correctement
            walls, real_wall_height = brick_geometry.generate_house_walls_bricks(
                width,
                length,
                total_height,
                collection,
                props.brick_3d_quality,
                openings,
                brick_material_mode,
                brick_color,
                brick_preset,
                custom_material
            )

            # Stocker la hauteur réelle pour l'utiliser dans _generate_roof
            self.real_wall_height = real_wall_height
            print(f"[House] Hauteur réelle des murs enregistrée: {real_wall_height:.3f}m")

            return walls
        
        # === SINON MUR SIMPLE (inchangé) ===
        width = props.house_width
        length = props.house_length
        wall_thickness = WALL_THICKNESS
        total_height = props.num_floors * props.floor_height

        # ✅ FIX CRITIQUE SHED: Adapter hauteur murs selon type toit
        roof_type = props.roof_type
        roof_pitch = props.roof_pitch

        # Calculer hauteur additionnelle pour toit SHED
        shed_extra_height = 0
        if roof_type == 'SHED':
            pitch_rad = math.radians(roof_pitch)
            shed_extra_height = length * math.tan(pitch_rad)
            # Limiter à 1.5× hauteur murs
            max_extra = total_height * 0.5
            if shed_extra_height > max_extra:
                shed_extra_height = max_extra
            print(f"[House] Toit SHED: mur arrière surélevé de {shed_extra_height:.2f}m")

        # Aligner murs avec le dessus de la fondation
        base_z = 0

        walls = []
        mesh = bpy.data.meshes.new("Walls")
        bm = bmesh.new()

        try:
            h = total_height

            # Vertices du bas (au niveau des fondations)
            outer = [
                bm.verts.new((0, 0, base_z)),
                bm.verts.new((width, 0, base_z)),
                bm.verts.new((width, length, base_z)),
                bm.verts.new((0, length, base_z))
            ]

            inner = [
                bm.verts.new((wall_thickness, wall_thickness, base_z)),
                bm.verts.new((width - wall_thickness, wall_thickness, base_z)),
                bm.verts.new((width - wall_thickness, length - wall_thickness, base_z)),
                bm.verts.new((wall_thickness, length - wall_thickness, base_z))
            ]

            # ✅ FIX CRITIQUE SHED: Vertices du haut avec hauteurs adaptées
            # Pour SHED: murs arrière (indices 2, 3) plus hauts
            outer_top = []
            inner_top = []
            for i, v in enumerate(outer):
                # Indices 2 et 3 = mur arrière (côté Y+)
                extra_h = shed_extra_height if (i >= 2 and roof_type == 'SHED') else 0
                outer_top.append(bm.verts.new(v.co + Vector((0, 0, h + extra_h))))

            for i, v in enumerate(inner):
                extra_h = shed_extra_height if (i >= 2 and roof_type == 'SHED') else 0
                inner_top.append(bm.verts.new(v.co + Vector((0, 0, h + extra_h))))
            
            # Faces verticales extérieures
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new([outer[i], outer[j], outer_top[j], outer_top[i]])
            
            # Faces verticales intérieures
            for i in range(4):
                j = (i + 1) % 4
                bm.faces.new([inner[j], inner[i], inner_top[i], inner_top[j]])
            
            # Sol de la structure murale
            bm.faces.new([outer[0], outer[1], inner[1], inner[0]])
            bm.faces.new([outer[1], outer[2], inner[2], inner[1]])
            bm.faces.new([outer[2], outer[3], inner[3], inner[2]])
            bm.faces.new([outer[3], outer[0], inner[0], inner[3]])
            
            # Plafond de la structure murale
            bm.faces.new([outer_top[0], inner_top[0], inner_top[1], outer_top[1]])
            bm.faces.new([outer_top[1], inner_top[1], inner_top[2], outer_top[2]])
            bm.faces.new([outer_top[2], inner_top[2], inner_top[3], outer_top[3]])
            bm.faces.new([outer_top[3], inner_top[3], inner_top[0], outer_top[0]])
            
            walls_obj, walls_mesh = self._create_mesh_from_bmesh("Walls", bm)
            collection.objects.link(walls_obj)
            walls_obj["house_part"] = "wall"
            walls.append(walls_obj)
            
        finally:
            bm.free()
        
        return walls
    
    def _calculate_openings_for_brick_walls(self, props):
        """Calcule les positions des ouvertures pour les murs en briques"""
        width = props.house_width
        length = props.house_length

        openings = []

        # Récupérer window_height_ratio
        style_config = self._apply_architectural_style(props)
        window_height_ratio = style_config.get('window_height_ratio', props.window_height_ratio)

        # ✅ FIX BUG #4: Calculer nombre de fenêtres avec validation anti-chevauchement
        num_windows_front = self._calculate_safe_window_count(width, "largeur")
        num_windows_side = self._calculate_safe_window_count(length, "longueur")
        
        # PORTE
        door_width = props.front_door_width
        door_height = DOOR_HEIGHT
        door_x = width/2 - door_width/2
        
        openings.append({
            'x': door_x,
            'y': 0,
            'z': 0,
            'width': door_width,
            'height': door_height,
            'depth': WALL_THICKNESS,
            'wall': 'front',
            'type': 'door'
        })
        
        # FENÊTRES
        for floor in range(props.num_floors):
            floor_z = floor * props.floor_height
            window_height = props.floor_height * window_height_ratio
            window_z = floor_z + props.floor_height * WINDOW_HEIGHT_DEFAULT
            window_width = WINDOW_WIDTH
            
            # Mur AVANT
            spacing_front = width / (num_windows_front + 1)
            for i in range(num_windows_front):
                x_pos = spacing_front * (i + 1)
                
                if floor == 0 and abs(x_pos - width/2) < door_width * 1.5:
                    continue
                
                opening_x = x_pos - window_width/2
                
                openings.append({
                    'x': opening_x,
                    'y': 0,
                    'z': window_z,
                    'width': window_width,
                    'height': window_height,
                    'depth': WALL_THICKNESS,
                    'wall': 'front',
                    'type': 'window'
                })
            
            # Mur ARRIÈRE
            for i in range(num_windows_front):
                x_pos = spacing_front * (i + 1)
                opening_x = x_pos - window_width/2
                
                openings.append({
                    'x': opening_x,
                    'y': length,
                    'z': window_z,
                    'width': window_width,
                    'height': window_height,
                    'depth': WALL_THICKNESS,
                    'wall': 'back',
                    'type': 'window'
                })
            
            # Mur GAUCHE
            spacing_side = length / (num_windows_side + 1)
            for i in range(num_windows_side):
                y_pos = spacing_side * (i + 1)
                opening_y = y_pos - window_width/2
                
                openings.append({
                    'x': 0,
                    'y': opening_y,
                    'z': window_z,
                    'width': window_width,
                    'height': window_height,
                    'depth': WALL_THICKNESS,
                    'wall': 'left',
                    'type': 'window'
                })
            
            # Mur DROIT
            for i in range(num_windows_side):
                y_pos = spacing_side * (i + 1)
                opening_y = y_pos - window_width/2
                
                openings.append({
                    'x': width,
                    'y': opening_y,
                    'z': window_z,
                    'width': window_width,
                    'height': window_height,
                    'depth': WALL_THICKNESS,
                    'wall': 'right',
                    'type': 'window'
                })
        
        return openings
    
    def _generate_floors(self, context, props, collection):
        """Génère les planchers (simple ou système avancé)"""
        width = props.house_width
        length = props.house_length
        floor_thickness = FLOOR_THICKNESS

        floors = []

        # ✅ SYSTÈME AVANCÉ: Utiliser flooring.py si activé
        if hasattr(props, 'use_flooring_system') and props.use_flooring_system:
            print("[House] Utilisation du système de sols avancé")

            # Mapper qualité property vers constantes flooring
            quality_map = {
                'LOW': QUALITY_LOW,
                'MEDIUM': QUALITY_MEDIUM,
                'HIGH': QUALITY_HIGH,
                'ULTRA': QUALITY_ULTRA
            }
            quality = quality_map.get(props.flooring_quality, QUALITY_HIGH)

            # Créer le générateur
            flooring_gen = FlooringGenerator(quality=quality)

            # Générer les sols pour chaque étage
            for floor_num in range(props.num_floors):
                if floor_num == 0:
                    z_pos = 0  # Sol rez-de-chaussée au niveau 0
                else:
                    z_pos = floor_num * props.floor_height

                inset_width = width * FLOOR_INSET
                inset_length = length * FLOOR_INSET

                room_name = "RDC" if floor_num == 0 else f"Etage{floor_num}"

                # ✅ Générer le sol avec le système avancé
                floor_obj = flooring_gen.generate_floor(
                    floor_type=props.flooring_type,
                    width=inset_width,
                    length=inset_length,
                    room_name=room_name,
                    height=z_pos
                )

                if floor_obj:
                    # ✅ FIX BUG #5: Position centrée dans la maison avec hauteur correcte
                    floor_obj.location = (width/2 - inset_width/2, length/2 - inset_length/2, z_pos)
                    collection.objects.link(floor_obj)
                    floors.append(floor_obj)

            return floors

        # ✅ SYSTÈME SIMPLE (code original)
        for floor_num in range(props.num_floors):
            if floor_num == 0:
                z_pos = floor_thickness / 2
            else:
                z_pos = floor_num * props.floor_height + floor_thickness / 2

            inset_width = width * FLOOR_INSET
            inset_length = length * FLOOR_INSET

            location = Vector((width/2, length/2, z_pos))
            dimensions = Vector((inset_width, inset_length, floor_thickness))

            floor_name = f"Floor_Ground" if floor_num == 0 else f"Floor_{floor_num}"
            floor, mesh = self._create_box_mesh(floor_name, location, dimensions)
            collection.objects.link(floor)
            floor["house_part"] = "floor"
            floors.append(floor)

        return floors
    
    def _generate_roof(self, context, props, collection):
        """Génère le toit"""
        width = props.house_width
        length = props.house_length

        # ✅ FIX : Utiliser la hauteur RÉELLE des murs en briques si disponible
        # Sinon utiliser la hauteur calculée (murs simples)
        if hasattr(self, 'real_wall_height') and self.real_wall_height:
            total_height = self.real_wall_height
            print(f"[House] Toit positionné à la hauteur réelle des murs: {total_height:.3f}m")
        else:
            total_height = props.num_floors * props.floor_height
            print(f"[House] Toit positionné à la hauteur calculée: {total_height:.3f}m")

        roof_type = props.roof_type
        roof_pitch = props.roof_pitch
        roof_overhang = props.roof_overhang

        # ✅ FIX BUG #1: Suppression du paramètre collection inutilisé dans les appels
        if roof_type == 'FLAT':
            roof = self._create_flat_roof(width, length, total_height, roof_overhang)
        elif roof_type == 'GABLE':
            roof = self._create_gable_roof(width, length, total_height, roof_pitch, roof_overhang)
        elif roof_type == 'HIP':
            roof = self._create_hip_roof(width, length, total_height, roof_pitch, roof_overhang)
        elif roof_type == 'SHED':
            roof = self._create_shed_roof(width, length, total_height, roof_pitch, roof_overhang)
        elif roof_type == 'GAMBREL':
            roof = self._create_gambrel_roof(width, length, total_height, roof_pitch, roof_overhang)
        else:
            # Fallback au toit plat si type inconnu
            print(f"[House] ⚠️ Type de toit '{roof_type}' inconnu, utilisation d'un toit plat")
            roof = self._create_flat_roof(width, length, total_height, roof_overhang)

        roof.name = f"Roof_{roof_type}"
        roof["house_part"] = "roof"
        collection.objects.link(roof)
        
        return roof
    
    def _create_flat_roof(self, width, length, height, overhang):
        """Toit plat"""
        thickness = ROOF_THICKNESS_FLAT
        
        location = Vector((width/2, length/2, height + thickness/2))
        dimensions = Vector((width + overhang*2, length + overhang*2, thickness))
        
        roof, mesh = self._create_box_mesh("Roof_Flat", location, dimensions)
        return roof
    
    def _create_gable_roof(self, width, length, height, pitch, overhang):
        """Toit à 2 pans"""
        pitch_rad = math.radians(pitch)

        # ✅ FIX BUG #8: Validation de pente extrême pour GABLE
        if pitch < 15.0:
            print(f"[House] ⚠️ Pente très faible ({pitch}°) - toit presque plat, considérez un toit FLAT")
        elif pitch > 50.0:
            print(f"[House] ⚠️ Pente très raide ({pitch}°) - toit très incliné, vérifiez le réalisme")

        roof_height = (width/2) * math.tan(pitch_rad)

        # ✅ FIX BUG #2: Limiter la hauteur à 1.5× la hauteur des murs (réalisme)
        max_roof_height = height * 1.5
        if roof_height > max_roof_height:
            print(f"[House] ⚠️ Toit à 2 pans trop haut ({roof_height:.2f}m), limité à {max_roof_height:.2f}m")
            roof_height = max_roof_height

        roof_thickness = ROOF_THICKNESS_PITCHED

        # ✅ FIX BUG #6: Ajouter logging comme SHED/GAMBREL
        print(f"[House] Toit à 2 pans: pente {pitch}°, hauteur {roof_height:.2f}m (largeur {width:.1f}m)")

        bm = bmesh.new()
        
        try:
            h = height
            rh = roof_height
            o = overhang
            
            v1 = bm.verts.new((-o, -o, h))
            v2 = bm.verts.new((width + o, -o, h))
            v3 = bm.verts.new((width + o, length + o, h))
            v4 = bm.verts.new((-o, length + o, h))
            
            v5 = bm.verts.new((width/2, -o, h + rh))
            v6 = bm.verts.new((width/2, length + o, h + rh))
            
            f1 = bm.faces.new([v1, v2, v5])
            f2 = bm.faces.new([v2, v3, v6, v5])
            f3 = bm.faces.new([v3, v4, v6])
            f4 = bm.faces.new([v4, v1, v5, v6])
            
            faces_to_extrude = [f1, f2, f3, f4]
            ret = bmesh.ops.extrude_face_region(bm, geom=faces_to_extrude)
            
            extruded_verts = [v for v in ret['geom'] if isinstance(v, bmesh.types.BMVert)]
            offset_vector = Vector((0, 0, -roof_thickness))
            bmesh.ops.translate(bm, verts=extruded_verts, vec=offset_vector)
            
            roof, mesh = self._create_mesh_from_bmesh("GableRoof", bm)
            
        finally:
            bm.free()
        
        return roof
    
    def _create_hip_roof(self, width, length, height, pitch, overhang):
        """Toit à 4 pans RECTANGULAIRE (vrai toit en croupe)"""
        pitch_rad = math.radians(pitch)

        # ✅ FIX BUG #8: Validation de pente extrême pour HIP
        if pitch < 15.0:
            print(f"[House] ⚠️ Pente très faible ({pitch}°) - toit presque plat, considérez un toit FLAT")
        elif pitch > 50.0:
            print(f"[House] ⚠️ Pente très raide ({pitch}°) - toit très incliné, vérifiez le réalisme")

        # ✅ FIX CRITIQUE: Calcul basé sur la plus petite dimension (standard architectural)
        # Le toit HIP s'élève depuis les bords jusqu'au faîtage central
        min_dim = min(width, length)

        # Hauteur basée sur la moitié de la plus petite dimension
        roof_height = (min_dim / 2) * math.tan(pitch_rad)

        # ✅ FIX BUG #3: Limiter la hauteur à 1.5× la hauteur des murs (réalisme)
        max_roof_height = height * 1.5
        if roof_height > max_roof_height:
            print(f"[House] ⚠️ Toit à 4 pans trop haut ({roof_height:.2f}m), limité à {max_roof_height:.2f}m")
            roof_height = max_roof_height

        print(f"[House] Toit à 4 pans: pente {pitch}°, hauteur {roof_height:.2f}m (dimensions {width:.1f}m × {length:.1f}m)")

        # ✅ SÉCURITÉ: Vérification dimensions valides
        if width <= 0 or length <= 0 or roof_height <= 0:
            print(f"[House] ❌ ERREUR: Dimensions invalides pour toit HIP (w={width}, l={length}, h={roof_height})")
            # Fallback: créer un toit plat minimal
            return self._create_flat_roof(width, length, height, overhang)

        bm = bmesh.new()

        try:
            o = overhang
            h = height
            w = width
            l = length
            rh = roof_height
            roof_thickness = ROOF_THICKNESS_PITCHED

            # ✅ GÉOMÉTRIE MANUELLE RECTANGULAIRE (pas de cone!)
            # Calculer le faîtage selon les proportions
            if width > length:
                # Maison plus large que longue: faîtage horizontal le long de X
                ridge_length = width - length

                # Base (8 vertices du périmètre avec overhang)
                v1 = bm.verts.new((-o, -o, h))                    # Avant-gauche
                v2 = bm.verts.new((w + o, -o, h))                 # Avant-droit
                v3 = bm.verts.new((w + o, l + o, h))              # Arrière-droit
                v4 = bm.verts.new((-o, l + o, h))                 # Arrière-gauche

                # Faîtage (2 vertices au sommet)
                ridge_start_x = (w - ridge_length) / 2
                ridge_end_x = ridge_start_x + ridge_length
                ridge_y = l / 2

                v5 = bm.verts.new((ridge_start_x, ridge_y, h + rh))    # Sommet gauche
                v6 = bm.verts.new((ridge_end_x, ridge_y, h + rh))      # Sommet droit

                # Faces du toit (4 pans)
                bm.faces.new([v1, v2, v6, v5])  # Pan avant (trapèze)
                bm.faces.new([v3, v4, v5, v6])  # Pan arrière (trapèze)
                bm.faces.new([v1, v5, v4])      # Pan gauche (triangle)
                bm.faces.new([v2, v3, v6])      # Pan droit (triangle)

            elif length > width:
                # Maison plus longue que large: faîtage horizontal le long de Y
                ridge_length = length - width

                # Base (périmètre avec overhang)
                v1 = bm.verts.new((-o, -o, h))
                v2 = bm.verts.new((w + o, -o, h))
                v3 = bm.verts.new((w + o, l + o, h))
                v4 = bm.verts.new((-o, l + o, h))

                # Faîtage le long de Y
                ridge_x = w / 2
                ridge_start_y = (l - ridge_length) / 2
                ridge_end_y = ridge_start_y + ridge_length

                v5 = bm.verts.new((ridge_x, ridge_start_y, h + rh))   # Sommet avant
                v6 = bm.verts.new((ridge_x, ridge_end_y, h + rh))     # Sommet arrière

                # Faces du toit (4 pans)
                bm.faces.new([v1, v2, v5])      # Pan avant (triangle)
                bm.faces.new([v3, v4, v6])      # Pan arrière (triangle)
                bm.faces.new([v1, v5, v6, v4])  # Pan gauche (trapèze)
                bm.faces.new([v2, v3, v6, v5])  # Pan droit (trapèze)
            else:
                # Maison carrée: pyramide à 4 pans triangulaires
                v1 = bm.verts.new((-o, -o, h))
                v2 = bm.verts.new((w + o, -o, h))
                v3 = bm.verts.new((w + o, l + o, h))
                v4 = bm.verts.new((-o, l + o, h))

                # Sommet unique au centre
                v5 = bm.verts.new((w / 2, l / 2, h + rh))

                # 4 faces triangulaires
                bm.faces.new([v1, v2, v5])
                bm.faces.new([v2, v3, v5])
                bm.faces.new([v3, v4, v5])
                bm.faces.new([v4, v1, v5])

            roof, mesh = self._create_mesh_from_bmesh("HipRoof", bm)

        finally:
            bm.free()

        # ✅ Position centrée
        roof.location = (0, 0, 0)

        return roof

    def _create_shed_roof(self, width, length, height, pitch, overhang):
        """Toit monopente (monte de l'avant vers l'arrière, axe Y)"""
        pitch_rad = math.radians(pitch)

        # ✅ FIX: Calculer la hauteur basée sur la LONGUEUR (axe Y), pas la largeur
        roof_height = length * math.tan(pitch_rad)

        # ✅ AMÉLIORATION: Limiter la hauteur à 1.5× la hauteur des murs (réalisme)
        max_roof_height = height * 1.5
        if roof_height > max_roof_height:
            print(f"[House] ⚠️ Toit monopente trop haut ({roof_height:.2f}m), limité à {max_roof_height:.2f}m")
            roof_height = max_roof_height

        roof_thickness = ROOF_THICKNESS_PITCHED

        print(f"[House] Toit monopente: pente {pitch}°, hauteur {roof_height:.2f}m (longueur {length:.1f}m)")

        bm = bmesh.new()

        try:
            h = height
            o = overhang

            # ✅ FIX: Sommets corrigés - pente monte sur l'axe Y (avant → arrière)
            # Face supérieure (surface du toit inclinée)
            v1_top = bm.verts.new((-o, -o, h))                          # Avant-gauche BAS
            v2_top = bm.verts.new((width + o, -o, h))                   # Avant-droit BAS
            v3_top = bm.verts.new((width + o, length + o, h + roof_height))  # Arrière-droit HAUT
            v4_top = bm.verts.new((-o, length + o, h + roof_height))    # Arrière-gauche HAUT

            # Face inférieure (plafond sous le toit)
            v1_bot = bm.verts.new((-o, -o, h - roof_thickness))
            v2_bot = bm.verts.new((width + o, -o, h - roof_thickness))
            v3_bot = bm.verts.new((width + o, length + o, h + roof_height - roof_thickness))
            v4_bot = bm.verts.new((-o, length + o, h + roof_height - roof_thickness))

            # Face supérieure (pente du toit)
            bm.faces.new([v1_top, v2_top, v3_top, v4_top])

            # Face inférieure (plafond)
            bm.faces.new([v4_bot, v3_bot, v2_bot, v1_bot])

            # ✅ FIX BUG #9: Clarification des formes géométriques des faces
            # Faces latérales (fermeture du volume - ordre cohérent)
            bm.faces.new([v1_top, v1_bot, v2_bot, v2_top])  # Avant (rectangle bas, Y = -o)
            bm.faces.new([v3_top, v3_bot, v4_bot, v4_top])  # Arrière (rectangle haut, Y = length+o)
            bm.faces.new([v4_top, v4_bot, v1_bot, v1_top])  # Gauche (trapèze incliné, X = -o)
            bm.faces.new([v2_top, v2_bot, v3_bot, v3_top])  # Droite (trapèze incliné, X = width+o)

            roof, mesh = self._create_mesh_from_bmesh("ShedRoof", bm)

        finally:
            bm.free()

        return roof

    def _create_gambrel_roof(self, width, length, height, pitch, overhang):
        """Toit mansarde/gambrel (4 pans brisés)"""
        pitch_rad = math.radians(pitch)

        # ✅ FIX BUG #7: Utiliser width au lieu de min(width, length) pour éviter asymétrie
        # Calcul des hauteurs (pente inférieure plus raide)
        lower_height = (width / 4) * math.tan(pitch_rad * 1.5)  # Pente raide
        upper_height = lower_height * 0.4  # Partie supérieure plus plate

        # Limite réaliste
        max_total_height = height * 1.5
        total_roof_height = lower_height + upper_height
        if total_roof_height > max_total_height:
            scale_factor = max_total_height / total_roof_height
            lower_height *= scale_factor
            upper_height *= scale_factor
            print(f"[House] ⚠️ Toit mansarde trop haut, limité à {max_total_height:.2f}m")

        print(f"[House] Toit mansarde: pente {pitch}°, hauteur {lower_height + upper_height:.2f}m (pente basse {lower_height:.2f}m + haute {upper_height:.2f}m)")

        bm = bmesh.new()

        try:
            h = height
            o = overhang
            break_point = 0.7  # Point de brisure à 70% de la largeur/longueur

            # ========== Base (niveau des murs) ==========
            v1 = bm.verts.new((-o, -o, h))
            v2 = bm.verts.new((width + o, -o, h))
            v3 = bm.verts.new((width + o, length + o, h))
            v4 = bm.verts.new((-o, length + o, h))

            # ========== Points de brisure (pente inférieure) ==========
            bw = width * (1 - break_point) / 2
            bl = length * (1 - break_point) / 2

            v5 = bm.verts.new((bw, bl, h + lower_height))
            v6 = bm.verts.new((width - bw, bl, h + lower_height))
            v7 = bm.verts.new((width - bw, length - bl, h + lower_height))
            v8 = bm.verts.new((bw, length - bl, h + lower_height))

            # ========== Sommet plat (pente supérieure) ==========
            tw = width * 0.25  # Toit plat = 25% de la largeur
            tl = length * 0.25

            v9 = bm.verts.new((width/2 - tw/2, length/2 - tl/2, h + lower_height + upper_height))
            v10 = bm.verts.new((width/2 + tw/2, length/2 - tl/2, h + lower_height + upper_height))
            v11 = bm.verts.new((width/2 + tw/2, length/2 + tl/2, h + lower_height + upper_height))
            v12 = bm.verts.new((width/2 - tw/2, length/2 + tl/2, h + lower_height + upper_height))

            # ========== Faces - Pentes inférieures (raides) ==========
            bm.faces.new([v1, v2, v6, v5])  # Avant
            bm.faces.new([v2, v3, v7, v6])  # Droite
            bm.faces.new([v3, v4, v8, v7])  # Arrière
            bm.faces.new([v4, v1, v5, v8])  # Gauche

            # ========== Faces - Pentes supérieures (douces) ==========
            bm.faces.new([v5, v6, v10, v9])  # Avant
            bm.faces.new([v6, v7, v11, v10])  # Droite
            bm.faces.new([v7, v8, v12, v11])  # Arrière
            bm.faces.new([v8, v5, v9, v12])  # Gauche

            # ========== Toit plat supérieur ==========
            bm.faces.new([v9, v10, v11, v12])

            roof, mesh = self._create_mesh_from_bmesh("GambrelRoof", bm)

        finally:
            bm.free()

        return roof

    def _generate_wall_openings(self, context, props, collection, walls, style_config):
        """Génère les trous dans les murs (Boolean) - pour murs SIMPLES uniquement"""
        width = props.house_width
        length = props.house_length

        window_height_ratio = style_config.get('window_height_ratio', props.window_height_ratio)

        # ✅ FIX BUG #4: Utiliser calcul sécurisé pour éviter chevauchement
        num_windows_front = self._calculate_safe_window_count(width, "largeur")
        num_windows_side = self._calculate_safe_window_count(length, "longueur")
        
        combined_bm = bmesh.new()
        
        try:
            # PORTE
            door_height = DOOR_HEIGHT
            door_width = props.front_door_width
            door_depth = WALL_THICKNESS + DOOR_DEPTH_EXTRA
            
            door_bm = bmesh.new()
            bmesh.ops.create_cube(door_bm, size=1.0)
            
            door_scale = Matrix.Diagonal((door_width, door_depth, door_height, 1.0))
            bmesh.ops.transform(door_bm, matrix=door_scale, verts=door_bm.verts)
            
            door_location = Vector((width/2, WALL_THICKNESS/2, door_height/2))
            bmesh.ops.translate(door_bm, verts=door_bm.verts, vec=door_location)
            
            for v in door_bm.verts:
                combined_bm.verts.new(v.co)
            combined_bm.verts.ensure_lookup_table()
            
            for f in door_bm.faces:
                combined_bm.faces.new([combined_bm.verts[v.index] for v in f.verts])
            
            door_bm.free()
            
            # FENÊTRES
            for floor in range(props.num_floors):
                floor_z = floor * props.floor_height
                window_height = props.floor_height * window_height_ratio
                window_z = floor_z + props.floor_height * WINDOW_HEIGHT_DEFAULT
                window_depth = WALL_THICKNESS + WINDOW_DEPTH_EXTRA
                window_width = WINDOW_WIDTH
                
                spacing_front = width / (num_windows_front + 1)
                for i in range(num_windows_front):
                    x_pos = spacing_front * (i + 1)
                    
                    if floor == 0 and abs(x_pos - width/2) < door_width * 1.5:
                        continue
                    
                    self._add_window_to_combined_mesh(
                        combined_bm, x_pos, WALL_THICKNESS/2, window_z,
                        window_width, window_depth, window_height
                    )
                
                for i in range(num_windows_front):
                    x_pos = spacing_front * (i + 1)
                    self._add_window_to_combined_mesh(
                        combined_bm, x_pos, length - WALL_THICKNESS/2, window_z,
                        window_width, window_depth, window_height
                    )
                
                spacing_side = length / (num_windows_side + 1)
                for i in range(num_windows_side):
                    y_pos = spacing_side * (i + 1)
                    self._add_window_to_combined_mesh(
                        combined_bm, WALL_THICKNESS/2, y_pos, window_z,
                        window_depth, window_width, window_height
                    )
                
                for i in range(num_windows_side):
                    y_pos = spacing_side * (i + 1)
                    self._add_window_to_combined_mesh(
                        combined_bm, width - WALL_THICKNESS/2, y_pos, window_z,
                        window_depth, window_width, window_height
                    )
            
            combined_cutter, combined_mesh = self._create_mesh_from_bmesh("Openings_Cutter", combined_bm)
            collection.objects.link(combined_cutter)
            combined_cutter["house_part"] = "opening"
            if hasattr(combined_cutter, "display_type"):
                combined_cutter.display_type = 'WIRE'
            combined_cutter.hide_render = True
            
            for wall in walls:
                mod = wall.modifiers.new(name="Boolean_Openings", type='BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = combined_cutter
                mod.solver = 'FAST'
            
        finally:
            combined_bm.free()
    
    def _add_window_to_combined_mesh(self, combined_bm, x, y, z, width, depth, height):
        """Ajoute une fenêtre au mesh combiné"""
        window_bm = bmesh.new()
        bmesh.ops.create_cube(window_bm, size=1.0)
        
        window_scale = Matrix.Diagonal((width, depth, height, 1.0))
        bmesh.ops.transform(window_bm, matrix=window_scale, verts=window_bm.verts)
        
        window_location = Vector((x, y, z))
        bmesh.ops.translate(window_bm, verts=window_bm.verts, vec=window_location)
        
        vert_offset = len(combined_bm.verts)
        for v in window_bm.verts:
            combined_bm.verts.new(v.co)
        combined_bm.verts.ensure_lookup_table()
        
        for f in window_bm.faces:
            combined_bm.faces.new([combined_bm.verts[vert_offset + v.index] for v in f.verts])
        
        window_bm.free()
    
    def _generate_windows_complete(self, context, props, collection, style_config):
        """Génère les fenêtres 3D complètes"""
        width = props.house_width
        length = props.house_length

        # ✅ FIX BUG #4: Utiliser calcul sécurisé pour éviter chevauchement
        num_windows_front = self._calculate_safe_window_count(width, "largeur")
        num_windows_side = self._calculate_safe_window_count(length, "longueur")
        
        window_height_ratio = style_config.get('window_height_ratio', props.window_height_ratio)
        window_height = props.floor_height * window_height_ratio
        window_width = WINDOW_WIDTH
        
        window_gen = WindowGenerator(quality=props.window_quality)
        
        for floor in range(props.num_floors):
            floor_z = floor * props.floor_height
            window_z = floor_z + props.floor_height * WINDOW_HEIGHT_DEFAULT
            
            # Mur avant
            spacing_front = width / (num_windows_front + 1)
            for i in range(num_windows_front):
                x_pos = spacing_front * (i + 1)
                
                if floor == 0 and abs(x_pos - width/2) < props.front_door_width * 1.5:
                    continue
                
                window_gen.generate_window(
                    window_type=props.window_type,
                    width=window_width,
                    height=window_height,
                    location=Vector((x_pos, WALL_THICKNESS/2, window_z)),
                    orientation='front',
                    collection=collection
                )
            
            # Mur arrière
            for i in range(num_windows_front):
                x_pos = spacing_front * (i + 1)
                window_gen.generate_window(
                    window_type=props.window_type,
                    width=window_width,
                    height=window_height,
                    location=Vector((x_pos, length - WALL_THICKNESS/2, window_z)),
                    orientation='back',
                    collection=collection
                )
            
            # Mur gauche
            spacing_side = length / (num_windows_side + 1)
            for i in range(num_windows_side):
                y_pos = spacing_side * (i + 1)
                window_gen.generate_window(
                    window_type=props.window_type,
                    width=window_width,
                    height=window_height,
                    location=Vector((WALL_THICKNESS/2, y_pos, window_z)),
                    orientation='left',
                    collection=collection
                )
            
            # Mur droit
            for i in range(num_windows_side):
                y_pos = spacing_side * (i + 1)
                window_gen.generate_window(
                    window_type=props.window_type,
                    width=window_width,
                    height=window_height,
                    location=Vector((width - WALL_THICKNESS/2, y_pos, window_z)),
                    orientation='right',
                    collection=collection
                )
    
    # [... Les autres fonctions garage, terrace, balcony, lighting restent identiques ...]
    
    def _generate_garage(self, context, props, collection):
        """Génère un garage"""
        width = props.house_width
        length = props.house_length

        # Taille du garage selon le type
        if props.garage_size == 'SINGLE':
            garage_width = GARAGE_WIDTH_SINGLE
        else:
            garage_width = GARAGE_WIDTH_DOUBLE

        garage_length = GARAGE_LENGTH
        garage_height = GARAGE_HEIGHT

        # Position sur le côté gauche de la maison
        if props.garage_position == 'LEFT':
            garage_x = -garage_width / 2 - GARAGE_OFFSET
            garage_y = length / 2
        elif props.garage_position == 'RIGHT':
            garage_x = width + garage_width / 2 + GARAGE_OFFSET
            garage_y = length / 2
        else:  # FRONT ou ATTACHED
            garage_x = width / 2
            garage_y = -garage_length / 2 - GARAGE_OFFSET

        location = Vector((garage_x, garage_y, garage_height / 2))
        dimensions = Vector((garage_width, garage_length, garage_height))

        garage, mesh = self._create_box_mesh("Garage", location, dimensions)
        collection.objects.link(garage)
        garage["house_part"] = "garage"

        return garage
    
    def _generate_terrace(self, context, props, collection):
        """Génère une terrasse"""
        width = props.house_width
        length = props.house_length

        terrace_width = width * TERRACE_WIDTH_RATIO
        terrace_length = TERRACE_LENGTH
        terrace_height = TERRACE_HEIGHT

        # Position devant la maison
        terrace_x = width / 2
        terrace_y = -terrace_length / 2 - TERRACE_OFFSET

        location = Vector((terrace_x, terrace_y, terrace_height / 2))
        dimensions = Vector((terrace_width, terrace_length, terrace_height))

        terrace, mesh = self._create_box_mesh("Terrace", location, dimensions)
        collection.objects.link(terrace)
        terrace["house_part"] = "terrace"

        return terrace
    
    def _generate_balcony(self, context, props, collection):
        """Génère un balcon"""
        width = props.house_width
        length = props.house_length

        balcony_width = width * BALCONY_WIDTH_RATIO
        balcony_depth = BALCONY_DEPTH
        balcony_height = BALCONY_HEIGHT

        # Position à l'avant de la maison, au premier étage
        balcony_x = width / 2
        balcony_y = -balcony_depth / 2
        balcony_z = props.floor_height + balcony_height / 2

        location = Vector((balcony_x, balcony_y, balcony_z))
        dimensions = Vector((balcony_width, balcony_depth, balcony_height))

        balcony, mesh = self._create_box_mesh("Balcony", location, dimensions)
        collection.objects.link(balcony)
        balcony["house_part"] = "balcony"

        # Générer la rambarde
        self._generate_balcony_railing(context, props, collection, balcony_width, balcony_depth, balcony_x, balcony_y, balcony_z + balcony_height / 2)

        return balcony

    def _generate_balcony_railing(self, context, props, collection, balcony_width, balcony_depth, x_pos, y_pos, z_pos):
        """Génère la rambarde"""
        bm = bmesh.new()

        try:
            railing_height = BALCONY_RAILING_HEIGHT
            railing_thickness = BALCONY_RAILING_THICKNESS

            # Rail horizontal supérieur (avant)
            self._add_railing_segment(bm, x_pos, y_pos - balcony_depth / 2, z_pos + railing_height, balcony_width, railing_thickness, railing_thickness)

            # Poteaux
            num_posts = int(balcony_width / BALCONY_POST_SPACING) + 1
            for i in range(num_posts):
                post_x = x_pos - balcony_width / 2 + i * BALCONY_POST_SPACING
                self._add_railing_post(bm, post_x, y_pos - balcony_depth / 2, z_pos, BALCONY_POST_SIZE, BALCONY_POST_SIZE, railing_height)

            railing, mesh = self._create_mesh_from_bmesh("Balcony_Railing", bm)
            collection.objects.link(railing)
            railing["house_part"] = "balcony"

        finally:
            bm.free()

        return railing

    def _add_railing_segment(self, bm, x, y, z, width, depth, height):
        """Ajoute un segment de rambarde"""
        half_w = width / 2
        half_d = depth / 2
        half_h = height / 2

        # Créer les 8 sommets d'un cube
        v1 = bm.verts.new((x - half_w, y - half_d, z - half_h))
        v2 = bm.verts.new((x + half_w, y - half_d, z - half_h))
        v3 = bm.verts.new((x + half_w, y + half_d, z - half_h))
        v4 = bm.verts.new((x - half_w, y + half_d, z - half_h))
        v5 = bm.verts.new((x - half_w, y - half_d, z + half_h))
        v6 = bm.verts.new((x + half_w, y - half_d, z + half_h))
        v7 = bm.verts.new((x + half_w, y + half_d, z + half_h))
        v8 = bm.verts.new((x - half_w, y + half_d, z + half_h))

        # Créer les faces
        bm.faces.new([v1, v2, v3, v4])  # Bas
        bm.faces.new([v5, v8, v7, v6])  # Haut
        bm.faces.new([v1, v5, v6, v2])  # Avant
        bm.faces.new([v2, v6, v7, v3])  # Droite
        bm.faces.new([v3, v7, v8, v4])  # Arrière
        bm.faces.new([v4, v8, v5, v1])  # Gauche

    def _add_railing_post(self, bm, x, y, z, width, depth, height):
        """Ajoute un poteau"""
        half_w = width / 2
        half_d = depth / 2

        # Créer les 8 sommets d'un poteau vertical
        v1 = bm.verts.new((x - half_w, y - half_d, z))
        v2 = bm.verts.new((x + half_w, y - half_d, z))
        v3 = bm.verts.new((x + half_w, y + half_d, z))
        v4 = bm.verts.new((x - half_w, y + half_d, z))
        v5 = bm.verts.new((x - half_w, y - half_d, z + height))
        v6 = bm.verts.new((x + half_w, y - half_d, z + height))
        v7 = bm.verts.new((x + half_w, y + half_d, z + height))
        v8 = bm.verts.new((x - half_w, y + half_d, z + height))

        # Créer les faces
        bm.faces.new([v1, v2, v3, v4])  # Bas
        bm.faces.new([v5, v8, v7, v6])  # Haut
        bm.faces.new([v1, v5, v6, v2])  # Avant
        bm.faces.new([v2, v6, v7, v3])  # Droite
        bm.faces.new([v3, v7, v8, v4])  # Arrière
        bm.faces.new([v4, v8, v5, v1])  # Gauche
    
    def _add_scene_lighting(self, context, props):
        """Ajoute l'éclairage"""
        width = props.house_width
        length = props.house_length
        total_height = props.num_floors * props.floor_height

        # Lumière principale (soleil)
        if "Sun" not in bpy.data.lights:
            sun_data = bpy.data.lights.new(name="Sun", type='SUN')
            sun_data.energy = 2.0
            sun_object = bpy.data.objects.new(name="Sun", object_data=sun_data)
            context.scene.collection.objects.link(sun_object)
            sun_object.location = (width / 2, length / 2, total_height + 10)
            sun_object.rotation_euler = (0.785, 0, 0.785)  # 45 degrés

        # Lumière d'appoint (point light)
        if "House_Light" not in bpy.data.lights:
            light_data = bpy.data.lights.new(name="House_Light", type='POINT')
            light_data.energy = 500.0
            light_data.shadow_soft_size = 2.0
            light_object = bpy.data.objects.new(name="House_Light", object_data=light_data)
            context.scene.collection.objects.link(light_object)
            light_object.location = (width / 2, length / 2 - 5, total_height + 5)
    
    def _apply_materials(self, context, props, collection, style_config):
        """Applique les matériaux - Les briques 3D sont déjà gérées"""
        
        # Les briques 3D ont DÉJÀ leur matériau appliqué dans brick_geometry
        # On ne touche PAS aux briques ici
        
        user_changed_wall = not self._colors_are_default(props.wall_material_color, DEFAULT_WALL_COLOR)
        user_changed_roof = not self._colors_are_default(props.roof_material_color, DEFAULT_ROOF_COLOR)
        user_changed_floor = not self._colors_are_default(props.floor_material_color, DEFAULT_FLOOR_COLOR)
        
        wall_color = props.wall_material_color if user_changed_wall else style_config.get('wall_color', props.wall_material_color)
        roof_color = props.roof_material_color if user_changed_roof else style_config.get('roof_color', props.roof_material_color)
        floor_color = props.floor_material_color if user_changed_floor else style_config.get('floor_color', props.floor_material_color)
        
        wall_mat = self._get_or_create_material("House_Wall", wall_color)
        roof_mat = self._get_or_create_material("House_Roof", roof_color)
        floor_mat = self._get_or_create_material("House_Floor", floor_color)
        glass_mat = self._get_or_create_glass_material("House_Glass")
        
        for obj in collection.objects:
            if obj.type != 'MESH' or obj.hide_render:
                continue
            
            part_type = obj.get("house_part", None)
            
            if part_type == "wall":
                # Murs simples uniquement (pas les briques qui ont déjà leur matériau)
                if props.wall_construction_type == 'SIMPLE' and len(obj.data.materials) == 0:
                    obj.data.materials.append(wall_mat)
            elif part_type == "roof":
                obj.data.materials.clear()
                obj.data.materials.append(roof_mat)
            elif part_type == "floor":
                # ✅ FIX BUG #6: Respecter matériaux du système avancé (comme pour les murs)
                # Ne PAS écraser les matériaux si le système de sols avancé est activé
                if hasattr(props, 'use_flooring_system') and props.use_flooring_system:
                    # Système avancé activé: les sols ont déjà leurs matériaux détaillés
                    # Ne rien faire, préserver les matériaux créés par flooring.py
                    pass
                else:
                    # Système simple: appliquer couleur unie seulement si pas de matériau
                    if len(obj.data.materials) == 0:
                        obj.data.materials.append(floor_mat)
            elif part_type == "glass":
                obj.data.materials.clear()
                obj.data.materials.append(glass_mat)
    
    def _get_or_create_material(self, name, color):
        """Crée ou récupère un matériau"""
        if name in bpy.data.materials:
            mat = bpy.data.materials[name]
        else:
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
        
        if not mat.use_nodes:
            mat.use_nodes = True

        nodes = mat.node_tree.nodes
        # Chercher par type au lieu du nom pour compatibilité Blender 4.2
        principled = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)

        if not principled:
            principled = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
            if output:
                mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        principled.inputs["Base Color"].default_value = (*color, 1.0)
        principled.inputs["Roughness"].default_value = MATERIAL_ROUGHNESS
        
        return mat
    
    def _get_or_create_glass_material(self, name):
        """Crée ou récupère le matériau verre"""
        if name in bpy.data.materials:
            return bpy.data.materials[name]
        
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        
        glass_bsdf = nodes.new(type='ShaderNodeBsdfGlass')
        glass_bsdf.location = (0, 0)
        glass_bsdf.inputs["IOR"].default_value = 1.45
        glass_bsdf.inputs["Roughness"].default_value = 0.0
        glass_bsdf.inputs["Color"].default_value = (0.8, 0.9, 1.0, 1.0)
        
        mat.node_tree.links.new(glass_bsdf.outputs["BSDF"], output.inputs["Surface"])

        mat.blend_method = 'HASHED'
        mat.shadow_method = 'HASHED'
        
        return mat


classes = (
    HOUSE_OT_generate_auto,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    print("[House] Module operators_auto ULTIMATE chargé")


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
