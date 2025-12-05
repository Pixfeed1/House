# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Génération de la géométrie des cloisons et portes pour Blender.

Ce module transforme le plan logique (FloorPlan) en objets Blender :
- Cloisons intérieures avec ouvertures pour les portes
- Marqueurs de pièces (pour debug/visualisation)
- Intégration avec le système de finitions existant
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Set, TYPE_CHECKING
from enum import Enum
import math

# Import Blender - sera disponible uniquement dans Blender
try:
    import bpy
    import bmesh
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

from .base import (
    Rectangle, Room, FloorPlan, HousePlan,
    WallSide, DoorOpening, WindowOpening
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class GeometryConfig:
    """Configuration pour la génération de géométrie."""

    # Dimensions des cloisons
    wall_thickness: float = 0.10         # Épaisseur cloisons intérieures
    wall_height: float = 2.50            # Hauteur sous plafond

    # Portes
    door_width: float = 0.83
    door_height: float = 2.04
    door_frame_width: float = 0.05       # Largeur du cadre
    door_frame_depth: float = 0.03       # Profondeur du cadre

    # Plinthes
    baseboard_height: float = 0.08
    baseboard_depth: float = 0.01

    # Matériaux par défaut
    wall_material_name: str = "Wall_Interior"
    door_frame_material_name: str = "Door_Frame"

    # Options de génération
    generate_door_frames: bool = True
    generate_baseboards: bool = False    # Peut être ajouté plus tard
    merge_coplanar_walls: bool = True    # Fusionner les murs alignés


# =============================================================================
# REPRÉSENTATION DES SEGMENTS DE MUR
# =============================================================================

@dataclass
class WallSegment:
    """
    Représente un segment de cloison intérieure.

    Un mur est défini par deux points (start, end) et peut avoir
    des ouvertures (portes).
    """

    # Position (coordonnées 2D au sol)
    start_x: float
    start_y: float
    end_x: float
    end_y: float

    # Dimensions
    thickness: float
    height: float

    # Ouvertures (position relative depuis start, largeur, hauteur, hauteur_base)
    openings: List[Tuple[float, float, float, float]] = field(default_factory=list)

    # Métadonnées
    room1_id: Optional[str] = None   # Pièce d'un côté
    room2_id: Optional[str] = None   # Pièce de l'autre côté
    is_exterior: bool = False         # Mur extérieur (pour référence)

    @property
    def length(self) -> float:
        """Longueur du segment."""
        dx = self.end_x - self.start_x
        dy = self.end_y - self.start_y
        return math.sqrt(dx * dx + dy * dy)

    @property
    def direction(self) -> Tuple[float, float]:
        """Direction normalisée du segment."""
        length = self.length
        if length < 0.001:
            return (1.0, 0.0)
        return (
            (self.end_x - self.start_x) / length,
            (self.end_y - self.start_y) / length
        )

    @property
    def normal(self) -> Tuple[float, float]:
        """Normale au segment (perpendiculaire, sens horaire)."""
        dx, dy = self.direction
        return (-dy, dx)

    @property
    def is_horizontal(self) -> bool:
        """Le segment est-il horizontal?"""
        return abs(self.end_y - self.start_y) < 0.01

    @property
    def is_vertical(self) -> bool:
        """Le segment est-il vertical?"""
        return abs(self.end_x - self.start_x) < 0.01

    def add_door_opening(
        self,
        position: float,
        width: float,
        height: float,
        base_height: float = 0.0
    ) -> None:
        """Ajoute une ouverture de porte."""
        self.openings.append((position, width, height, base_height))

    def get_solid_segments(self) -> List[Tuple[float, float]]:
        """
        Retourne les segments solides (sans ouvertures).

        Returns:
            Liste de (start_pos, end_pos) le long du mur
        """
        if not self.openings:
            return [(0, self.length)]

        # Trier les ouvertures par position
        sorted_openings = sorted(self.openings, key=lambda o: o[0])

        segments = []
        current_pos = 0

        for pos, width, height, base in sorted_openings:
            if pos > current_pos:
                segments.append((current_pos, pos))
            current_pos = pos + width

        if current_pos < self.length:
            segments.append((current_pos, self.length))

        return segments


# =============================================================================
# GÉNÉRATEUR DE MURS
# =============================================================================

class WallGeometryGenerator:
    """
    Génère la géométrie des cloisons intérieures.
    """

    def __init__(self, config: Optional[GeometryConfig] = None):
        self.config = config or GeometryConfig()

    def generate_wall_segments(self, floor_plan: FloorPlan) -> List[WallSegment]:
        """
        Analyse le plan et génère les segments de murs nécessaires.

        Returns:
            Liste de WallSegment représentant toutes les cloisons
        """
        segments: List[WallSegment] = []
        processed_edges: Set[Tuple[float, float, float, float]] = set()

        # Pour chaque paire de pièces adjacentes
        for room in floor_plan.placed_rooms:
            if not room.bounds:
                continue

            for other in floor_plan.get_adjacent_rooms(room):
                if not other.bounds:
                    continue

                # Obtenir le bord partagé
                shared = room.bounds.get_shared_edge(other.bounds)
                if not shared:
                    continue

                side, position, start, end = shared

                # Éviter les doublons
                edge_key = tuple(sorted([
                    (start, end, position, side.value),
                    (start, end, position, side.value)
                ])[0])

                if edge_key in processed_edges:
                    continue
                processed_edges.add(edge_key)

                # Créer le segment de mur
                segment = self._create_wall_segment(
                    side, position, start, end,
                    room.id, other.id
                )

                # Ajouter les ouvertures de portes
                for door in floor_plan.doors:
                    if door.connects(room.id) and door.connects(other.id):
                        # Calculer la position relative de la porte
                        door_pos_rel = door.position - start
                        segment.add_door_opening(
                            door_pos_rel,
                            door.width,
                            door.height,
                            0.0  # Portes au sol
                        )

                segments.append(segment)

        # Fusionner les murs coplanaires si configuré
        if self.config.merge_coplanar_walls:
            segments = self._merge_coplanar_segments(segments)

        return segments

    def _create_wall_segment(
        self,
        side: WallSide,
        position: float,
        start: float,
        end: float,
        room1_id: str,
        room2_id: str
    ) -> WallSegment:
        """Crée un segment de mur à partir d'un bord partagé."""

        half_thick = self.config.wall_thickness / 2

        if side in [WallSide.NORTH, WallSide.SOUTH]:
            # Mur horizontal (Y constant)
            return WallSegment(
                start_x=start,
                start_y=position,
                end_x=end,
                end_y=position,
                thickness=self.config.wall_thickness,
                height=self.config.wall_height,
                room1_id=room1_id,
                room2_id=room2_id
            )
        else:
            # Mur vertical (X constant)
            return WallSegment(
                start_x=position,
                start_y=start,
                end_x=position,
                end_y=end,
                thickness=self.config.wall_thickness,
                height=self.config.wall_height,
                room1_id=room1_id,
                room2_id=room2_id
            )

    def _merge_coplanar_segments(
        self,
        segments: List[WallSegment]
    ) -> List[WallSegment]:
        """Fusionne les segments de murs alignés."""

        # Grouper par orientation et position
        horizontal: Dict[float, List[WallSegment]] = {}
        vertical: Dict[float, List[WallSegment]] = {}

        for seg in segments:
            if seg.is_horizontal:
                key = round(seg.start_y, 3)
                horizontal.setdefault(key, []).append(seg)
            elif seg.is_vertical:
                key = round(seg.start_x, 3)
                vertical.setdefault(key, []).append(seg)

        merged = []

        # Fusionner les horizontaux
        for y, segs in horizontal.items():
            merged.extend(self._merge_aligned_segments(segs, is_horizontal=True))

        # Fusionner les verticaux
        for x, segs in vertical.items():
            merged.extend(self._merge_aligned_segments(segs, is_horizontal=False))

        return merged

    def _merge_aligned_segments(
        self,
        segments: List[WallSegment],
        is_horizontal: bool
    ) -> List[WallSegment]:
        """Fusionne des segments alignés sur une même ligne."""

        if len(segments) <= 1:
            return segments

        # Trier par position de départ
        if is_horizontal:
            segments.sort(key=lambda s: s.start_x)
        else:
            segments.sort(key=lambda s: s.start_y)

        merged = []
        current = segments[0]

        for next_seg in segments[1:]:
            # Vérifier si les segments se touchent
            if is_horizontal:
                gap = next_seg.start_x - current.end_x
            else:
                gap = next_seg.start_y - current.end_y

            if gap < 0.01:  # Segments contigus
                # Fusionner
                if is_horizontal:
                    current = WallSegment(
                        start_x=current.start_x,
                        start_y=current.start_y,
                        end_x=next_seg.end_x,
                        end_y=current.end_y,
                        thickness=current.thickness,
                        height=current.height,
                        openings=current.openings + [
                            (o[0] + (next_seg.start_x - current.start_x), o[1], o[2], o[3])
                            for o in next_seg.openings
                        ]
                    )
                else:
                    current = WallSegment(
                        start_x=current.start_x,
                        start_y=current.start_y,
                        end_x=current.end_x,
                        end_y=next_seg.end_y,
                        thickness=current.thickness,
                        height=current.height,
                        openings=current.openings + [
                            (o[0] + (next_seg.start_y - current.start_y), o[1], o[2], o[3])
                            for o in next_seg.openings
                        ]
                    )
            else:
                merged.append(current)
                current = next_seg

        merged.append(current)
        return merged


# =============================================================================
# GÉNÉRATION BLENDER
# =============================================================================

if HAS_BLENDER:

    class BlenderWallBuilder:
        """
        Construit les objets Blender pour les cloisons.
        """

        def __init__(self, config: Optional[GeometryConfig] = None):
            self.config = config or GeometryConfig()

        def build_walls(
            self,
            segments: List[WallSegment],
            collection: bpy.types.Collection,
            floor_z: float = 0.0
        ) -> List[bpy.types.Object]:
            """
            Construit les meshes de murs dans Blender.

            Args:
                segments: Liste des segments de murs
                collection: Collection Blender où ajouter les objets
                floor_z: Hauteur Z du plancher

            Returns:
                Liste des objets créés
            """
            objects = []

            for i, segment in enumerate(segments):
                obj = self._create_wall_mesh(segment, floor_z, f"Wall_{i:03d}")

                if obj:
                    collection.objects.link(obj)
                    objects.append(obj)

                    # Appliquer le matériau
                    self._apply_material(obj, self.config.wall_material_name)

                    # Générer le cadre de porte si demandé
                    if self.config.generate_door_frames:
                        for opening in segment.openings:
                            frame = self._create_door_frame(
                                segment, opening, floor_z, f"DoorFrame_{i:03d}"
                            )
                            if frame:
                                collection.objects.link(frame)
                                objects.append(frame)

            return objects

        def _create_wall_mesh(
            self,
            segment: WallSegment,
            floor_z: float,
            name: str
        ) -> Optional[bpy.types.Object]:
            """Crée le mesh d'un segment de mur."""

            mesh = bpy.data.meshes.new(name)
            bm = bmesh.new()

            try:
                dx, dy = segment.direction
                nx, ny = segment.normal

                half_thick = segment.thickness / 2

                # Pour chaque segment solide
                solid_segments = segment.get_solid_segments()

                for seg_start, seg_end in solid_segments:
                    # Calculer les 4 coins au sol
                    p1_x = segment.start_x + dx * seg_start - nx * half_thick
                    p1_y = segment.start_y + dy * seg_start - ny * half_thick

                    p2_x = segment.start_x + dx * seg_end - nx * half_thick
                    p2_y = segment.start_y + dy * seg_end - ny * half_thick

                    p3_x = segment.start_x + dx * seg_end + nx * half_thick
                    p3_y = segment.start_y + dy * seg_end + ny * half_thick

                    p4_x = segment.start_x + dx * seg_start + nx * half_thick
                    p4_y = segment.start_y + dy * seg_start + ny * half_thick

                    # Créer les 8 vertices (4 en bas, 4 en haut)
                    v1 = bm.verts.new((p1_x, p1_y, floor_z))
                    v2 = bm.verts.new((p2_x, p2_y, floor_z))
                    v3 = bm.verts.new((p3_x, p3_y, floor_z))
                    v4 = bm.verts.new((p4_x, p4_y, floor_z))

                    v5 = bm.verts.new((p1_x, p1_y, floor_z + segment.height))
                    v6 = bm.verts.new((p2_x, p2_y, floor_z + segment.height))
                    v7 = bm.verts.new((p3_x, p3_y, floor_z + segment.height))
                    v8 = bm.verts.new((p4_x, p4_y, floor_z + segment.height))

                    # Créer les faces
                    # Face avant
                    bm.faces.new([v1, v2, v6, v5])
                    # Face arrière
                    bm.faces.new([v3, v4, v8, v7])
                    # Face gauche
                    bm.faces.new([v4, v1, v5, v8])
                    # Face droite
                    bm.faces.new([v2, v3, v7, v6])
                    # Face dessus
                    bm.faces.new([v5, v6, v7, v8])
                    # Face dessous (optionnel)
                    bm.faces.new([v4, v3, v2, v1])

                # Créer les parties au-dessus des portes
                for pos, width, height, base in segment.openings:
                    if height < segment.height:
                        self._add_wall_above_opening(
                            bm, segment, pos, width,
                            floor_z + height,
                            segment.height - height,
                            half_thick
                        )

                bm.to_mesh(mesh)

            finally:
                bm.free()

            obj = bpy.data.objects.new(name, mesh)
            return obj

        def _add_wall_above_opening(
            self,
            bm: bmesh.types.BMesh,
            segment: WallSegment,
            pos: float,
            width: float,
            z_start: float,
            height: float,
            half_thick: float
        ) -> None:
            """Ajoute la partie de mur au-dessus d'une ouverture."""

            dx, dy = segment.direction
            nx, ny = segment.normal

            seg_start = pos
            seg_end = pos + width

            # Coins du rectangle au-dessus de l'ouverture
            p1_x = segment.start_x + dx * seg_start - nx * half_thick
            p1_y = segment.start_y + dy * seg_start - ny * half_thick

            p2_x = segment.start_x + dx * seg_end - nx * half_thick
            p2_y = segment.start_y + dy * seg_end - ny * half_thick

            p3_x = segment.start_x + dx * seg_end + nx * half_thick
            p3_y = segment.start_y + dy * seg_end + ny * half_thick

            p4_x = segment.start_x + dx * seg_start + nx * half_thick
            p4_y = segment.start_y + dy * seg_start + ny * half_thick

            v1 = bm.verts.new((p1_x, p1_y, z_start))
            v2 = bm.verts.new((p2_x, p2_y, z_start))
            v3 = bm.verts.new((p3_x, p3_y, z_start))
            v4 = bm.verts.new((p4_x, p4_y, z_start))

            v5 = bm.verts.new((p1_x, p1_y, z_start + height))
            v6 = bm.verts.new((p2_x, p2_y, z_start + height))
            v7 = bm.verts.new((p3_x, p3_y, z_start + height))
            v8 = bm.verts.new((p4_x, p4_y, z_start + height))

            # Faces
            bm.faces.new([v1, v2, v6, v5])
            bm.faces.new([v3, v4, v8, v7])
            bm.faces.new([v4, v1, v5, v8])
            bm.faces.new([v2, v3, v7, v6])
            bm.faces.new([v5, v6, v7, v8])
            bm.faces.new([v4, v3, v2, v1])

        def _create_door_frame(
            self,
            segment: WallSegment,
            opening: Tuple[float, float, float, float],
            floor_z: float,
            name: str
        ) -> Optional[bpy.types.Object]:
            """Crée le cadre d'une porte."""

            pos, width, height, base = opening

            mesh = bpy.data.meshes.new(name)
            bm = bmesh.new()

            try:
                dx, dy = segment.direction
                nx, ny = segment.normal

                frame_w = self.config.door_frame_width
                frame_d = self.config.door_frame_depth
                half_thick = segment.thickness / 2

                # Montant gauche
                self._add_frame_piece(
                    bm, segment,
                    pos - frame_w, pos,
                    floor_z + base, height,
                    frame_d, half_thick
                )

                # Montant droit
                self._add_frame_piece(
                    bm, segment,
                    pos + width, pos + width + frame_w,
                    floor_z + base, height,
                    frame_d, half_thick
                )

                # Traverse haute
                self._add_frame_piece(
                    bm, segment,
                    pos, pos + width,
                    floor_z + base + height - frame_w, frame_w,
                    frame_d, half_thick
                )

                bm.to_mesh(mesh)

            finally:
                bm.free()

            obj = bpy.data.objects.new(name, mesh)
            self._apply_material(obj, self.config.door_frame_material_name)

            return obj

        def _add_frame_piece(
            self,
            bm: bmesh.types.BMesh,
            segment: WallSegment,
            start_pos: float,
            end_pos: float,
            z_start: float,
            height: float,
            depth: float,
            half_thick: float
        ) -> None:
            """Ajoute un élément de cadre de porte."""

            dx, dy = segment.direction
            nx, ny = segment.normal

            # Décaler vers l'extérieur du mur
            offset = half_thick + depth / 2

            for sign in [-1, 1]:  # Des deux côtés du mur
                p1_x = segment.start_x + dx * start_pos + nx * sign * offset - nx * depth/2
                p1_y = segment.start_y + dy * start_pos + ny * sign * offset - ny * depth/2

                p2_x = segment.start_x + dx * end_pos + nx * sign * offset - nx * depth/2
                p2_y = segment.start_y + dy * end_pos + ny * sign * offset - ny * depth/2

                p3_x = segment.start_x + dx * end_pos + nx * sign * offset + nx * depth/2
                p3_y = segment.start_y + dy * end_pos + ny * sign * offset + ny * depth/2

                p4_x = segment.start_x + dx * start_pos + nx * sign * offset + nx * depth/2
                p4_y = segment.start_y + dy * start_pos + ny * sign * offset + ny * depth/2

                v1 = bm.verts.new((p1_x, p1_y, z_start))
                v2 = bm.verts.new((p2_x, p2_y, z_start))
                v3 = bm.verts.new((p3_x, p3_y, z_start))
                v4 = bm.verts.new((p4_x, p4_y, z_start))

                v5 = bm.verts.new((p1_x, p1_y, z_start + height))
                v6 = bm.verts.new((p2_x, p2_y, z_start + height))
                v7 = bm.verts.new((p3_x, p3_y, z_start + height))
                v8 = bm.verts.new((p4_x, p4_y, z_start + height))

                bm.faces.new([v1, v2, v6, v5])
                bm.faces.new([v3, v4, v8, v7])
                bm.faces.new([v4, v1, v5, v8])
                bm.faces.new([v2, v3, v7, v6])
                bm.faces.new([v5, v6, v7, v8])

        def _apply_material(
            self,
            obj: bpy.types.Object,
            material_name: str
        ) -> None:
            """Applique un matériau à un objet."""

            mat = bpy.data.materials.get(material_name)

            if mat is None:
                mat = bpy.data.materials.new(name=material_name)
                mat.use_nodes = True

                # Configuration basique
                if mat.node_tree:
                    bsdf = mat.node_tree.nodes.get("Principled BSDF")
                    if bsdf:
                        if "Wall" in material_name:
                            bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.88, 1)
                        elif "Door" in material_name:
                            bsdf.inputs["Base Color"].default_value = (0.4, 0.25, 0.15, 1)

            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)


    class RoomMarkerBuilder:
        """
        Crée des marqueurs visuels pour les pièces (debug).
        """

        @staticmethod
        def create_room_markers(
            floor_plan: FloorPlan,
            collection: bpy.types.Collection,
            floor_z: float = 0.0
        ) -> List[bpy.types.Object]:
            """Crée des empties avec le nom des pièces au centre."""

            markers = []

            for room in floor_plan.placed_rooms:
                if not room.bounds:
                    continue

                cx, cy = room.bounds.center

                empty = bpy.data.objects.new(f"Room_{room.id}", None)
                empty.empty_display_type = 'PLAIN_AXES'
                empty.empty_display_size = 0.5
                empty.location = (cx, cy, floor_z + 0.1)

                # Ajouter une propriété custom avec les infos
                empty["room_type"] = room.room_type_id
                empty["room_area"] = room.area
                empty["room_name"] = room.name

                collection.objects.link(empty)
                markers.append(empty)

            return markers

        @staticmethod
        def create_floor_plan_outline(
            floor_plan: FloorPlan,
            collection: bpy.types.Collection,
            floor_z: float = 0.01
        ) -> Optional[bpy.types.Object]:
            """Crée un outline 2D du plan au sol (pour visualisation)."""

            mesh = bpy.data.meshes.new("FloorPlan_Outline")
            bm = bmesh.new()

            try:
                for room in floor_plan.placed_rooms:
                    if not room.bounds:
                        continue

                    b = room.bounds

                    # Créer les 4 vertices du rectangle
                    v1 = bm.verts.new((b.x_min, b.y_min, floor_z))
                    v2 = bm.verts.new((b.x_max, b.y_min, floor_z))
                    v3 = bm.verts.new((b.x_max, b.y_max, floor_z))
                    v4 = bm.verts.new((b.x_min, b.y_max, floor_z))

                    # Créer les edges (pas de face)
                    bm.edges.new([v1, v2])
                    bm.edges.new([v2, v3])
                    bm.edges.new([v3, v4])
                    bm.edges.new([v4, v1])

                bm.to_mesh(mesh)

            finally:
                bm.free()

            obj = bpy.data.objects.new("FloorPlan_Outline", mesh)
            collection.objects.link(obj)

            return obj


# =============================================================================
# FONCTIONS UTILITAIRES PRINCIPALES
# =============================================================================

def generate_interior_walls(
    floor_plan: FloorPlan,
    collection_name: str = "Interior_Walls",
    floor_z: float = 0.0,
    config: Optional[GeometryConfig] = None
) -> Dict[str, any]:
    """
    Génère toutes les cloisons intérieures pour un plan d'étage.

    Args:
        floor_plan: Plan d'étage avec pièces placées
        collection_name: Nom de la collection Blender
        floor_z: Hauteur Z du plancher
        config: Configuration de géométrie

    Returns:
        Dict avec les objets créés et les statistiques
    """
    if not HAS_BLENDER:
        raise RuntimeError("Cette fonction nécessite Blender")

    cfg = config or GeometryConfig()

    # Créer une sous-collection dédiée aux cloisons intérieures
    # pour éviter de supprimer les murs extérieurs
    partitions_collection_name = f"{collection_name}_Interior_Partitions"

    # Récupérer la collection parent si elle existe
    parent_collection = None
    if collection_name in bpy.data.collections:
        parent_collection = bpy.data.collections[collection_name]

    # Créer ou récupérer la sous-collection des cloisons
    if partitions_collection_name in bpy.data.collections:
        collection = bpy.data.collections[partitions_collection_name]
        # Nettoyer seulement les anciennes cloisons
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        collection = bpy.data.collections.new(partitions_collection_name)
        # Lier à la collection parent si elle existe, sinon à la scène
        if parent_collection:
            parent_collection.children.link(collection)
        else:
            bpy.context.scene.collection.children.link(collection)

    # Générer les segments de murs
    wall_gen = WallGeometryGenerator(cfg)
    segments = wall_gen.generate_wall_segments(floor_plan)

    # Construire les meshes
    builder = BlenderWallBuilder(cfg)
    wall_objects = builder.build_walls(segments, collection, floor_z)

    # Créer les marqueurs de pièces (debug)
    markers = RoomMarkerBuilder.create_room_markers(floor_plan, collection, floor_z)

    return {
        "collection": collection,
        "walls": wall_objects,
        "markers": markers,
        "num_segments": len(segments),
        "num_doors": sum(len(s.openings) for s in segments)
    }


def get_partition_data_for_floor_plan(floor_plan: FloorPlan) -> List[Dict]:
    """
    Retourne les données des cloisons dans un format compatible avec l'ancien système.

    Utile pour l'intégration avec operators_auto.py

    Returns:
        Liste de dicts avec les infos de chaque cloison
    """
    wall_gen = WallGeometryGenerator()
    segments = wall_gen.generate_wall_segments(floor_plan)

    partitions = []

    for i, seg in enumerate(segments):
        partition = {
            "index": i,
            "start": (seg.start_x, seg.start_y),
            "end": (seg.end_x, seg.end_y),
            "thickness": seg.thickness,
            "height": seg.height,
            "is_horizontal": seg.is_horizontal,
            "openings": [
                {
                    "position": o[0],
                    "width": o[1],
                    "height": o[2],
                    "base_height": o[3],
                    "type": "door"
                }
                for o in seg.openings
            ],
            "rooms": [seg.room1_id, seg.room2_id]
        }
        partitions.append(partition)

    return partitions
