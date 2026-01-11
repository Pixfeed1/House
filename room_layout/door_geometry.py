# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Génération de la géométrie 3D des portes pour Blender.

Génère:
- Le cadre (huisserie)
- Le vantail (panneau de porte)
- Les charnières
- Les poignées (des deux côtés!)
- Le seuil (optionnel)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Any
import math

try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix, Euler
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Stubs pour tests sans Blender
    class Vector:
        def __init__(self, *args): pass
    class Matrix:
        pass

from .base import (
    DoorOpening, DoorType, DoorSwingDirection, DoorHingeSide,
    DoorStyle, DoorHandleType, WallSide
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class DoorGeometryConfig:
    """Configuration pour la génération de géométrie des portes."""
    
    # Cadre (huisserie)
    frame_width: float = 0.07          # Largeur visible du cadre
    frame_depth: float = 0.035         # Profondeur du cadre (saillie)
    frame_rebate: float = 0.015        # Feuillure (où repose la porte)
    
    # Vantail
    panel_thickness: float = 0.04      # Épaisseur du panneau de porte
    panel_inset: float = 0.003         # Jeu entre panneau et cadre
    panel_bottom_gap: float = 0.005    # Jeu en bas de la porte
    
    # Charnières
    hinge_count: int = 3               # Nombre de charnières
    hinge_radius: float = 0.007        # Rayon du cylindre
    hinge_height: float = 0.10         # Hauteur d'une charnière
    hinge_positions: List[float] = field(default_factory=lambda: [0.20, 0.50, 0.80])
    
    # Poignées
    handle_height: float = 1.05        # Hauteur depuis le sol
    handle_offset: float = 0.06        # Distance depuis le bord
    handle_length: float = 0.12        # Longueur de la poignée
    handle_diameter: float = 0.018     # Diamètre du tube
    rosette_radius: float = 0.025      # Rayon de la rosace
    rosette_depth: float = 0.008       # Épaisseur de la rosace
    
    # Seuil
    generate_threshold: bool = False   # Générer un seuil
    threshold_height: float = 0.015
    threshold_depth: float = 0.05
    
    # Options de génération
    generate_frame: bool = True
    generate_panel: bool = True
    generate_hinges: bool = True
    generate_handles: bool = True
    
    # Prévisualisation
    preview_open_angle: float = 30.0   # Angle pour porte ouverte (degrés)
    
    # Matériaux
    frame_material: str = "Door_Frame"
    panel_material: str = "Door_Panel"
    handle_material: str = "Door_Handle"
    hinge_material: str = "Door_Hinge"
    glass_material: str = "Door_Glass"
    
    # Couleurs par défaut (R, G, B, A)
    frame_color: Tuple[float, ...] = (0.55, 0.40, 0.25, 1.0)   # Bois moyen
    panel_color: Tuple[float, ...] = (0.95, 0.95, 0.93, 1.0)   # Blanc cassé
    handle_color: Tuple[float, ...] = (0.75, 0.75, 0.75, 1.0)  # Inox
    hinge_color: Tuple[float, ...] = (0.65, 0.65, 0.65, 1.0)   # Métal mat


# =============================================================================
# GÉNÉRATEUR DE GÉOMÉTRIE
# =============================================================================

if HAS_BLENDER:

    class DoorGeometryBuilder:
        """
        Construit la géométrie 3D complète d'une porte.
        
        Crée tous les éléments: cadre, vantail, charnières, poignées.
        """
        
        def __init__(self, config: Optional[DoorGeometryConfig] = None):
            self.config = config or DoorGeometryConfig()
        
        def build_door(
            self,
            door: DoorOpening,
            wall_thickness: float,
            wall_start: Tuple[float, float],
            wall_direction: Tuple[float, float],
            collection: bpy.types.Collection,
            floor_z: float = 0.0,
            show_open: bool = False
        ) -> Dict[str, bpy.types.Object]:
            """
            Construit tous les éléments d'une porte.
            
            Args:
                door: Configuration de la porte
                wall_thickness: Épaisseur du mur
                wall_start: Point de départ du mur (x, y)
                wall_direction: Direction normalisée du mur (dx, dy)
                collection: Collection Blender pour les objets
                floor_z: Hauteur du sol
                show_open: Afficher la porte ouverte
                
            Returns:
                Dict avec tous les objets créés
            """
            objects = {}
            
            # Calculer la transformation de base
            transform = self._calculate_transform(
                door, wall_thickness, wall_start, wall_direction, floor_z
            )
            
            # 1. Créer le cadre
            if self.config.generate_frame:
                frame_obj = self._create_frame(door, transform)
                if frame_obj:
                    collection.objects.link(frame_obj)
                    objects['frame'] = frame_obj
                    self._apply_material(
                        frame_obj, 
                        self.config.frame_material,
                        self.config.frame_color
                    )
            
            # 2. Créer le vantail
            if self.config.generate_panel:
                panel_obj = self._create_panel(door, transform, show_open)
                if panel_obj:
                    collection.objects.link(panel_obj)
                    objects['panel'] = panel_obj
                    self._apply_material(
                        panel_obj,
                        self.config.panel_material,
                        self.config.panel_color
                    )
            
            # 3. Créer les charnières
            if self.config.generate_hinges and not door.is_sliding:
                hinges = self._create_hinges(door, transform)
                for i, hinge in enumerate(hinges):
                    collection.objects.link(hinge)
                    objects[f'hinge_{i}'] = hinge
                    self._apply_material(
                        hinge,
                        self.config.hinge_material,
                        self.config.hinge_color
                    )
            
            # 4. Créer les poignées (DES DEUX CÔTÉS!)
            if self.config.generate_handles:
                handles = self._create_handles(door, transform, show_open)
                for side, handle in handles.items():
                    collection.objects.link(handle)
                    objects[f'handle_{side}'] = handle
                    self._apply_material(
                        handle,
                        self.config.handle_material,
                        self.config.handle_color
                    )
            
            # 5. Créer le seuil (optionnel)
            if self.config.generate_threshold and not door.is_exterior:
                threshold = self._create_threshold(door, transform)
                if threshold:
                    collection.objects.link(threshold)
                    objects['threshold'] = threshold
            
            # Créer un parent vide pour grouper tous les objets
            parent_name = f"Door_{door.id}"
            parent = bpy.data.objects.new(parent_name, None)
            parent.empty_display_type = 'ARROWS'
            parent.empty_display_size = 0.15
            parent.location = transform['position']
            parent.rotation_euler.z = transform['rotation']
            collection.objects.link(parent)
            
            # Parenter tous les objets
            for obj in objects.values():
                obj.parent = parent
                # Convertir en coordonnées locales
                obj.location = obj.location - transform['position']
                obj.rotation_euler.z = obj.rotation_euler.z - transform['rotation']
            
            objects['parent'] = parent
            
            return objects
        
        # ---------------------------------------------------------------------
        # CALCUL DE TRANSFORMATION
        # ---------------------------------------------------------------------
        
        def _calculate_transform(
            self,
            door: DoorOpening,
            wall_thickness: float,
            wall_start: Tuple[float, float],
            wall_direction: Tuple[float, float],
            floor_z: float
        ) -> Dict:
            """Calcule la position et rotation de base de la porte."""
            
            dx, dy = wall_direction
            
            # Position du centre de la porte le long du mur
            pos_along_wall = door.position + door.width / 2
            
            # Position dans le monde
            base_x = wall_start[0] + dx * pos_along_wall
            base_y = wall_start[1] + dy * pos_along_wall
            base_z = floor_z
            
            # Rotation (angle du mur par rapport à l'axe X)
            angle = math.atan2(dy, dx)
            
            # Normale au mur (perpendiculaire)
            nx, ny = -dy, dx
            
            return {
                'position': Vector((base_x, base_y, base_z)),
                'rotation': angle,
                'direction': (dx, dy),
                'normal': (nx, ny),
                'wall_thickness': wall_thickness
            }
        
        # ---------------------------------------------------------------------
        # CRÉATION DU CADRE
        # ---------------------------------------------------------------------
        
        def _create_frame(
            self,
            door: DoorOpening,
            transform: Dict
        ) -> Optional[bpy.types.Object]:
            """
            Crée le cadre de la porte (huisserie).
            
            Le cadre a une forme en "U" inversé:
            - Deux montants verticaux (gauche et droite)
            - Une traverse haute
            """
            
            mesh_name = f"Frame_{door.id}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                w = door.width
                h = door.height
                fw = self.config.frame_width
                fd = self.config.frame_depth
                wt = transform['wall_thickness']
                
                # Profondeur totale du cadre (traverse l'épaisseur du mur + saillies)
                total_depth = wt + 2 * fd
                
                # Montant gauche
                self._add_box(
                    bm,
                    x_min=-w/2 - fw,
                    x_max=-w/2,
                    y_min=-total_depth/2,
                    y_max=total_depth/2,
                    z_min=0,
                    z_max=h + fw
                )
                
                # Montant droit
                self._add_box(
                    bm,
                    x_min=w/2,
                    x_max=w/2 + fw,
                    y_min=-total_depth/2,
                    y_max=total_depth/2,
                    z_min=0,
                    z_max=h + fw
                )
                
                # Traverse haute
                self._add_box(
                    bm,
                    x_min=-w/2,
                    x_max=w/2,
                    y_min=-total_depth/2,
                    y_max=total_depth/2,
                    z_min=h,
                    z_max=h + fw
                )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            obj.location = transform['position']
            obj.rotation_euler.z = transform['rotation']
            
            return obj
        
        # ---------------------------------------------------------------------
        # CRÉATION DU VANTAIL
        # ---------------------------------------------------------------------
        
        def _create_panel(
            self,
            door: DoorOpening,
            transform: Dict,
            show_open: bool
        ) -> Optional[bpy.types.Object]:
            """
            Crée le vantail (panneau de porte).
            
            Le panneau est positionné selon le côté des charnières
            et peut être pivoté si show_open=True.
            """
            
            if door.is_sliding:
                return self._create_sliding_panel(door, transform, show_open)
            
            mesh_name = f"Panel_{door.id}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                w = door.width - 2 * self.config.panel_inset
                h = door.height - self.config.panel_inset - self.config.panel_bottom_gap
                t = self.config.panel_thickness
                
                # Position X selon le côté des charnières
                if door.hinge_side == DoorHingeSide.LEFT:
                    # Charnières à gauche = panneau part de la gauche
                    x_min = -door.width/2 + self.config.panel_inset
                    x_max = x_min + w
                else:
                    # Charnières à droite = panneau part de la droite
                    x_max = door.width/2 - self.config.panel_inset
                    x_min = x_max - w
                
                # Le panneau est centré dans l'épaisseur du mur
                y_min = -t/2
                y_max = t/2
                
                # Hauteur
                z_min = self.config.panel_bottom_gap
                z_max = z_min + h
                
                self._add_box(bm, x_min, x_max, y_min, y_max, z_min, z_max)
                
                # Ajouter détails selon le style
                if door.style == DoorStyle.PANELED:
                    self._add_panel_details(bm, x_min, x_max, z_min, z_max, t)
                elif door.style == DoorStyle.GLAZED:
                    # TODO: Ajouter vitrage
                    pass
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            obj.location = transform['position'].copy()
            obj.rotation_euler.z = transform['rotation']
            
            # Si la porte doit être montrée ouverte
            if show_open and not door.is_sliding:
                self._apply_door_opening(obj, door, transform)
            
            return obj
        
        def _create_sliding_panel(
            self,
            door: DoorOpening,
            transform: Dict,
            show_open: bool
        ) -> Optional[bpy.types.Object]:
            """Crée le panneau d'une porte coulissante."""
            
            mesh_name = f"Panel_{door.id}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                w = door.width - 2 * self.config.panel_inset
                h = door.height - self.config.panel_inset - self.config.panel_bottom_gap
                t = self.config.panel_thickness
                
                # Position de base
                x_offset = 0
                if show_open:
                    # Décaler le panneau sur le côté
                    x_offset = door.width * 0.8
                    if door.hinge_side == DoorHingeSide.LEFT:
                        x_offset = -x_offset
                
                x_min = -w/2 + x_offset
                x_max = w/2 + x_offset
                y_min = -t/2
                y_max = t/2
                z_min = self.config.panel_bottom_gap
                z_max = z_min + h
                
                self._add_box(bm, x_min, x_max, y_min, y_max, z_min, z_max)
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            obj.location = transform['position']
            obj.rotation_euler.z = transform['rotation']
            
            return obj
        
        def _add_panel_details(
            self,
            bm: bmesh.types.BMesh,
            x_min: float,
            x_max: float,
            z_min: float,
            z_max: float,
            thickness: float
        ) -> None:
            """Ajoute des détails de moulures sur un panneau."""
            
            # Créer deux panneaux en relief (style classique)
            panel_margin = 0.08
            panel_depth = 0.008
            
            pw = (x_max - x_min) - 2 * panel_margin
            ph = (z_max - z_min) / 2 - 1.5 * panel_margin
            
            # Panneau du bas
            self._add_box(
                bm,
                x_min + panel_margin,
                x_min + panel_margin + pw,
                thickness/2,
                thickness/2 + panel_depth,
                z_min + panel_margin,
                z_min + panel_margin + ph
            )
            
            # Panneau du haut
            self._add_box(
                bm,
                x_min + panel_margin,
                x_min + panel_margin + pw,
                thickness/2,
                thickness/2 + panel_depth,
                z_max - panel_margin - ph,
                z_max - panel_margin
            )
        
        def _apply_door_opening(
            self,
            obj: bpy.types.Object,
            door: DoorOpening,
            transform: Dict
        ) -> None:
            """Applique la rotation d'ouverture à une porte battante."""
            
            angle = math.radians(self.config.preview_open_angle)
            
            # Ajuster selon le sens d'ouverture
            if door.swing_direction == DoorSwingDirection.PUSH:
                angle = -angle
            
            # Ajuster selon le côté des charnières
            if door.hinge_side == DoorHingeSide.RIGHT:
                angle = -angle
            
            # Le pivot est sur les charnières
            # Créer une rotation autour du bord avec charnières
            pivot_x = -door.width/2 if door.hinge_side == DoorHingeSide.LEFT else door.width/2
            
            # Appliquer la rotation
            # Note: Ceci est simplifié - idéalement utiliser un rig avec empties
            obj.rotation_euler.z += angle
        
        # ---------------------------------------------------------------------
        # CRÉATION DES CHARNIÈRES
        # ---------------------------------------------------------------------
        
        def _create_hinges(
            self,
            door: DoorOpening,
            transform: Dict
        ) -> List[bpy.types.Object]:
            """Crée les charnières de la porte."""
            
            hinges = []
            
            # Positions verticales des charnières (ratios de la hauteur)
            if len(self.config.hinge_positions) >= self.config.hinge_count:
                positions_ratio = self.config.hinge_positions[:self.config.hinge_count]
            else:
                # Générer des positions uniformes
                positions_ratio = [
                    (i + 1) / (self.config.hinge_count + 1)
                    for i in range(self.config.hinge_count)
                ]
            
            positions_z = [door.height * r for r in positions_ratio]
            
            # Position X selon le côté des charnières
            if door.hinge_side == DoorHingeSide.LEFT:
                x_pos = -door.width / 2
            else:
                x_pos = door.width / 2
            
            for i, z in enumerate(positions_z):
                hinge = self._create_single_hinge(door, x_pos, z, i, transform)
                hinges.append(hinge)
            
            return hinges
        
        def _create_single_hinge(
            self,
            door: DoorOpening,
            x: float,
            z: float,
            index: int,
            transform: Dict
        ) -> bpy.types.Object:
            """Crée une charnière individuelle (cylindre)."""
            
            mesh_name = f"Hinge_{door.id}_{index}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                # Créer un cylindre vertical
                r = self.config.hinge_radius
                h = self.config.hinge_height
                segments = 12
                
                # Vertices du cylindre
                verts_bottom = []
                verts_top = []
                
                for i in range(segments):
                    angle = 2 * math.pi * i / segments
                    vx = r * math.cos(angle)
                    vy = r * math.sin(angle)
                    
                    verts_bottom.append(bm.verts.new((vx, vy, -h/2)))
                    verts_top.append(bm.verts.new((vx, vy, h/2)))
                
                # Face du bas
                bm.faces.new(verts_bottom[::-1])
                
                # Face du haut
                bm.faces.new(verts_top)
                
                # Faces latérales
                for i in range(segments):
                    next_i = (i + 1) % segments
                    bm.faces.new([
                        verts_bottom[i],
                        verts_bottom[next_i],
                        verts_top[next_i],
                        verts_top[i]
                    ])
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            
            # Position
            pos = transform['position'].copy()
            pos.x += x * math.cos(transform['rotation']) 
            pos.y += x * math.sin(transform['rotation'])
            pos.z += z
            obj.location = pos
            obj.rotation_euler.z = transform['rotation']
            
            return obj
        
        # ---------------------------------------------------------------------
        # CRÉATION DES POIGNÉES (DES DEUX CÔTÉS!)
        # ---------------------------------------------------------------------
        
        def _create_handles(
            self,
            door: DoorOpening,
            transform: Dict,
            show_open: bool
        ) -> Dict[str, bpy.types.Object]:
            """
            Crée les poignées DES DEUX CÔTÉS de la porte.
            
            C'est le point crucial qui manquait dans l'ancienne version!
            """
            
            handles = {}
            
            # Position X (côté opposé aux charnières)
            if door.hinge_side == DoorHingeSide.LEFT:
                x_pos = door.width / 2 - self.config.handle_offset
            else:
                x_pos = -door.width / 2 + self.config.handle_offset
            
            z_pos = self.config.handle_height
            
            # Épaisseur du panneau pour positionner les poignées
            panel_t = self.config.panel_thickness
            
            # Poignée côté AVANT (face positive Y en local)
            handle_front = self._create_single_handle(
                door,
                x_pos,
                panel_t/2 + 0.005,  # Légèrement devant le panneau
                z_pos,
                transform,
                "front",
                facing_positive_y=True
            )
            if handle_front:
                handles['front'] = handle_front
            
            # Poignée côté ARRIÈRE (face négative Y en local)
            handle_back = self._create_single_handle(
                door,
                x_pos,
                -panel_t/2 - 0.005,  # Légèrement derrière le panneau
                z_pos,
                transform,
                "back",
                facing_positive_y=False
            )
            if handle_back:
                handles['back'] = handle_back
            
            return handles
        
        def _create_single_handle(
            self,
            door: DoorOpening,
            x: float,
            y: float,
            z: float,
            transform: Dict,
            side: str,
            facing_positive_y: bool
        ) -> Optional[bpy.types.Object]:
            """Crée une poignée individuelle."""
            
            if door.handle_type == DoorHandleType.NONE:
                return None
            
            if door.handle_type == DoorHandleType.LEVER:
                return self._create_lever_handle(
                    door, x, y, z, transform, side, facing_positive_y
                )
            elif door.handle_type == DoorHandleType.KNOB:
                return self._create_knob_handle(
                    door, x, y, z, transform, side, facing_positive_y
                )
            elif door.handle_type == DoorHandleType.PULL_BAR:
                return self._create_pull_bar(
                    door, x, y, z, transform, side, facing_positive_y
                )
            elif door.handle_type == DoorHandleType.RECESSED:
                return self._create_recessed_handle(
                    door, x, y, z, transform, side, facing_positive_y
                )
            
            return None
        
        def _create_lever_handle(
            self,
            door: DoorOpening,
            x: float,
            y: float,
            z: float,
            transform: Dict,
            side: str,
            facing_positive_y: bool
        ) -> bpy.types.Object:
            """Crée une poignée de type bec-de-cane (levier)."""
            
            mesh_name = f"Handle_{door.id}_{side}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                rr = self.config.rosette_radius
                rd = self.config.rosette_depth
                hr = self.config.handle_diameter / 2
                hl = self.config.handle_length
                
                # Direction Y selon le côté
                y_dir = 1 if facing_positive_y else -1
                
                # 1. Rosace (disque plat)
                self._add_cylinder(
                    bm,
                    radius=rr,
                    height=rd,
                    segments=16,
                    offset_y=y_dir * rd / 2
                )
                
                # 2. Tige sortante (petite section entre rosace et levier)
                stem_length = 0.025
                self._add_cylinder(
                    bm,
                    radius=hr * 1.2,
                    height=stem_length,
                    segments=8,
                    offset_y=y_dir * (rd + stem_length/2)
                )
                
                # 3. Levier horizontal
                # Le levier part vers l'extérieur de la porte
                lever_direction = 1 if door.hinge_side == DoorHingeSide.RIGHT else -1
                
                lever_offset_y = y_dir * (rd + stem_length)
                
                # Créer le levier comme un cylindre horizontal
                self._add_horizontal_cylinder(
                    bm,
                    radius=hr,
                    length=hl,
                    segments=8,
                    offset_x=lever_direction * hl / 2,
                    offset_y=lever_offset_y,
                    offset_z=0
                )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            
            # Position dans le monde
            angle = transform['rotation']
            pos = transform['position'].copy()
            
            # Transformer les coordonnées locales en monde
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            
            pos.x += x * cos_a - y * sin_a
            pos.y += x * sin_a + y * cos_a
            pos.z += z
            
            obj.location = pos
            obj.rotation_euler.z = angle
            
            return obj
        
        def _create_knob_handle(
            self,
            door: DoorOpening,
            x: float,
            y: float,
            z: float,
            transform: Dict,
            side: str,
            facing_positive_y: bool
        ) -> bpy.types.Object:
            """Crée une poignée bouton rond."""
            
            mesh_name = f"Handle_{door.id}_{side}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                knob_radius = 0.022
                knob_depth = 0.025
                y_dir = 1 if facing_positive_y else -1
                
                # Rosace
                self._add_cylinder(
                    bm,
                    radius=self.config.rosette_radius,
                    height=self.config.rosette_depth,
                    segments=16,
                    offset_y=y_dir * self.config.rosette_depth / 2
                )
                
                # Bouton (sphère aplatie approximée par un cylindre avec bords)
                self._add_cylinder(
                    bm,
                    radius=knob_radius,
                    height=knob_depth,
                    segments=16,
                    offset_y=y_dir * (self.config.rosette_depth + knob_depth/2)
                )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            
            angle = transform['rotation']
            pos = transform['position'].copy()
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            pos.x += x * cos_a - y * sin_a
            pos.y += x * sin_a + y * cos_a
            pos.z += z
            
            obj.location = pos
            obj.rotation_euler.z = angle
            
            return obj
        
        def _create_pull_bar(
            self,
            door: DoorOpening,
            x: float,
            y: float,
            z: float,
            transform: Dict,
            side: str,
            facing_positive_y: bool
        ) -> bpy.types.Object:
            """Crée une barre de tirage (pour portes coulissantes)."""
            
            mesh_name = f"Handle_{door.id}_{side}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                bar_height = 0.15
                bar_radius = 0.01
                bar_offset = 0.03
                y_dir = 1 if facing_positive_y else -1
                
                # Barre verticale
                self._add_cylinder(
                    bm,
                    radius=bar_radius,
                    height=bar_height,
                    segments=8,
                    offset_y=y_dir * bar_offset,
                    horizontal=False
                )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            
            angle = transform['rotation']
            pos = transform['position'].copy()
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            pos.x += x * cos_a - y * sin_a
            pos.y += x * sin_a + y * cos_a
            pos.z += z
            
            obj.location = pos
            obj.rotation_euler.z = angle
            
            return obj
        
        def _create_recessed_handle(
            self,
            door: DoorOpening,
            x: float,
            y: float,
            z: float,
            transform: Dict,
            side: str,
            facing_positive_y: bool
        ) -> bpy.types.Object:
            """Crée une poignée encastrée (pour galandage)."""
            
            # Similaire à pull_bar mais plus subtile
            return self._create_pull_bar(door, x, y, z, transform, side, facing_positive_y)
        
        # ---------------------------------------------------------------------
        # CRÉATION DU SEUIL
        # ---------------------------------------------------------------------
        
        def _create_threshold(
            self,
            door: DoorOpening,
            transform: Dict
        ) -> Optional[bpy.types.Object]:
            """Crée le seuil de porte."""
            
            mesh_name = f"Threshold_{door.id}"
            mesh = bpy.data.meshes.new(mesh_name)
            bm = bmesh.new()
            
            try:
                w = door.width
                h = self.config.threshold_height
                d = self.config.threshold_depth
                
                self._add_box(
                    bm,
                    -w/2, w/2,
                    -d/2, d/2,
                    0, h
                )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            obj = bpy.data.objects.new(mesh_name, mesh)
            obj.location = transform['position']
            obj.rotation_euler.z = transform['rotation']
            
            return obj
        
        # ---------------------------------------------------------------------
        # UTILITAIRES GÉOMÉTRIQUES
        # ---------------------------------------------------------------------
        
        def _add_box(
            self,
            bm: bmesh.types.BMesh,
            x_min: float, x_max: float,
            y_min: float, y_max: float,
            z_min: float, z_max: float
        ) -> None:
            """Ajoute un parallélépipède au BMesh."""
            
            verts = [
                bm.verts.new((x_min, y_min, z_min)),  # 0
                bm.verts.new((x_max, y_min, z_min)),  # 1
                bm.verts.new((x_max, y_max, z_min)),  # 2
                bm.verts.new((x_min, y_max, z_min)),  # 3
                bm.verts.new((x_min, y_min, z_max)),  # 4
                bm.verts.new((x_max, y_min, z_max)),  # 5
                bm.verts.new((x_max, y_max, z_max)),  # 6
                bm.verts.new((x_min, y_max, z_max)),  # 7
            ]
            
            # 6 faces
            bm.faces.new([verts[0], verts[3], verts[2], verts[1]])  # Bas
            bm.faces.new([verts[4], verts[5], verts[6], verts[7]])  # Haut
            bm.faces.new([verts[0], verts[1], verts[5], verts[4]])  # Avant
            bm.faces.new([verts[2], verts[3], verts[7], verts[6]])  # Arrière
            bm.faces.new([verts[0], verts[4], verts[7], verts[3]])  # Gauche
            bm.faces.new([verts[1], verts[2], verts[6], verts[5]])  # Droite
        
        def _add_cylinder(
            self,
            bm: bmesh.types.BMesh,
            radius: float,
            height: float,
            segments: int = 12,
            offset_x: float = 0,
            offset_y: float = 0,
            offset_z: float = 0,
            horizontal: bool = False
        ) -> None:
            """Ajoute un cylindre au BMesh."""
            
            verts_bottom = []
            verts_top = []
            
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                
                if horizontal:
                    # Cylindre horizontal (axe X)
                    vx = offset_x - height/2
                    vy = offset_y + radius * math.cos(angle)
                    vz = offset_z + radius * math.sin(angle)
                    verts_bottom.append(bm.verts.new((vx, vy, vz)))
                    
                    vx = offset_x + height/2
                    verts_top.append(bm.verts.new((vx, vy, vz)))
                else:
                    # Cylindre vertical (axe Z)
                    vx = offset_x + radius * math.cos(angle)
                    vy = offset_y + radius * math.sin(angle)
                    
                    verts_bottom.append(bm.verts.new((vx, vy, offset_z - height/2)))
                    verts_top.append(bm.verts.new((vx, vy, offset_z + height/2)))
            
            # Faces
            bm.faces.new(verts_bottom[::-1])  # Bas
            bm.faces.new(verts_top)            # Haut
            
            for i in range(segments):
                next_i = (i + 1) % segments
                bm.faces.new([
                    verts_bottom[i],
                    verts_bottom[next_i],
                    verts_top[next_i],
                    verts_top[i]
                ])
        
        def _add_horizontal_cylinder(
            self,
            bm: bmesh.types.BMesh,
            radius: float,
            length: float,
            segments: int = 8,
            offset_x: float = 0,
            offset_y: float = 0,
            offset_z: float = 0
        ) -> None:
            """Ajoute un cylindre horizontal (axe X) au BMesh."""
            
            verts_left = []
            verts_right = []
            
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                vy = offset_y + radius * math.cos(angle)
                vz = offset_z + radius * math.sin(angle)
                
                verts_left.append(bm.verts.new((offset_x - length/2, vy, vz)))
                verts_right.append(bm.verts.new((offset_x + length/2, vy, vz)))
            
            # Faces
            bm.faces.new(verts_left[::-1])
            bm.faces.new(verts_right)
            
            for i in range(segments):
                next_i = (i + 1) % segments
                bm.faces.new([
                    verts_left[i],
                    verts_left[next_i],
                    verts_right[next_i],
                    verts_right[i]
                ])
        
        # ---------------------------------------------------------------------
        # MATÉRIAUX
        # ---------------------------------------------------------------------
        
        def _apply_material(
            self,
            obj: bpy.types.Object,
            material_name: str,
            color: Tuple[float, ...]
        ) -> None:
            """Applique un matériau à un objet."""
            
            mat = bpy.data.materials.get(material_name)
            
            if mat is None:
                mat = bpy.data.materials.new(name=material_name)
                mat.use_nodes = True
                
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = color
                    
                    # Ajuster selon le type
                    if "Handle" in material_name or "Hinge" in material_name:
                        bsdf.inputs["Metallic"].default_value = 1.0
                        bsdf.inputs["Roughness"].default_value = 0.2
                    elif "Frame" in material_name:
                        bsdf.inputs["Roughness"].default_value = 0.4
                    elif "Panel" in material_name:
                        bsdf.inputs["Roughness"].default_value = 0.3
            
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)


else:
    # Stub quand Blender n'est pas disponible
    class DoorGeometryBuilder:
        """Stub pour import sans Blender."""
        def __init__(self, config=None):
            self.config = config or DoorGeometryConfig()
        
        def build_door(self, *args, **kwargs):
            raise RuntimeError("DoorGeometryBuilder nécessite Blender")


# =============================================================================
# FONCTION UTILITAIRE PRINCIPALE
# =============================================================================

def generate_door_geometry(
    door: DoorOpening,
    wall_thickness: float,
    wall_start: Tuple[float, float],
    wall_direction: Tuple[float, float],
    collection,  # bpy.types.Collection
    floor_z: float = 0.0,
    config: Optional[DoorGeometryConfig] = None,
    show_open: bool = False
) -> Dict[str, Any]:
    """
    Génère la géométrie complète d'une porte.
    
    Args:
        door: Configuration de la porte
        wall_thickness: Épaisseur du mur
        wall_start: Point de départ du mur (x, y)
        wall_direction: Direction normalisée du mur (dx, dy)
        collection: Collection Blender
        floor_z: Hauteur du sol
        config: Configuration optionnelle
        show_open: Afficher la porte ouverte
        
    Returns:
        Dict avec les objets créés
    """
    if not HAS_BLENDER:
        raise RuntimeError("Cette fonction nécessite Blender")
    
    builder = DoorGeometryBuilder(config)
    return builder.build_door(
        door, wall_thickness, wall_start, wall_direction,
        collection, floor_z, show_open
    )
