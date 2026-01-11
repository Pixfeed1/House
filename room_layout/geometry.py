# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Génération de la géométrie des cloisons et portes pour Blender.

Ce module crée les meshes 3D pour:
- Cloisons intérieures avec ouvertures pour les portes
- Cadres et vantaux de portes (via door_geometry.py)
- Marqueurs de pièces pour le debug
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set, Any
import math

try:
    import bpy
    import bmesh
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False

from .base import (
    Rectangle, Room, FloorPlan, WallSide,
    DoorOpening, DoorType
)
from .door_geometry import (
    DoorGeometryBuilder, DoorGeometryConfig, generate_door_geometry
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class GeometryConfig:
    """Configuration pour la génération de géométrie."""
    
    # Murs
    wall_thickness: float = 0.10         # Épaisseur cloisons intérieures
    wall_height: float = 2.50            # Hauteur sous plafond
    
    # Portes (dimensions par défaut, peuvent être override par DoorOpening)
    door_width: float = 0.83
    door_height: float = 2.04
    
    # Options de génération
    generate_door_frames: bool = True    # Générer les cadres
    generate_door_panels: bool = True    # Générer les vantaux
    generate_door_handles: bool = True   # Générer les poignées
    generate_door_hinges: bool = True    # Générer les charnières
    show_doors_open: bool = False        # Montrer les portes ouvertes
    
    # Fusion des murs
    merge_coplanar_walls: bool = True
    
    # Matériaux
    wall_material_name: str = "Wall_Interior"
    
    # Configuration détaillée des portes
    door_geometry_config: Optional[DoorGeometryConfig] = None
    
    def get_door_config(self) -> DoorGeometryConfig:
        """Retourne la config de géométrie des portes."""
        if self.door_geometry_config:
            return self.door_geometry_config
        
        # Créer une config par défaut basée sur nos options
        return DoorGeometryConfig(
            generate_frame=self.generate_door_frames,
            generate_panel=self.generate_door_panels,
            generate_handles=self.generate_door_handles,
            generate_hinges=self.generate_door_hinges,
            preview_open_angle=30.0 if self.show_doors_open else 0.0
        )


# =============================================================================
# OUVERTURE DANS UN MUR
# =============================================================================

@dataclass
class WallOpening:
    """
    Représente une ouverture dans un mur (porte ou fenêtre).
    """
    position: float          # Position relative depuis le début du mur
    width: float
    height: float
    base_height: float = 0.0 # Hauteur depuis le sol (0 pour portes)
    
    # Référence à la porte source
    door_id: Optional[str] = None
    door: Optional[DoorOpening] = None
    
    # Type d'ouverture
    opening_type: str = "door"  # "door", "window", "pass_through"


# =============================================================================
# SEGMENT DE MUR
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
    
    # Ouvertures
    openings: List[WallOpening] = field(default_factory=list)
    
    # Métadonnées des pièces adjacentes
    room1_id: Optional[str] = None
    room2_id: Optional[str] = None
    
    # Flags
    is_exterior: bool = False
    
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
    
    @property
    def start_point(self) -> Tuple[float, float]:
        """Point de départ."""
        return (self.start_x, self.start_y)
    
    @property
    def end_point(self) -> Tuple[float, float]:
        """Point de fin."""
        return (self.end_x, self.end_y)
    
    def add_door_opening(self, door: DoorOpening, relative_position: float) -> None:
        """Ajoute une ouverture de porte avec toutes les infos."""
        opening = WallOpening(
            position=relative_position,
            width=door.width,
            height=door.height,
            base_height=0.0,
            door_id=door.id,
            door=door,
            opening_type="door"
        )
        self.openings.append(opening)
    
    def get_doors(self) -> List[WallOpening]:
        """Retourne uniquement les ouvertures de type porte."""
        return [o for o in self.openings if o.opening_type == "door"]
    
    def get_solid_segments(self) -> List[Tuple[float, float]]:
        """
        Retourne les segments solides (sans ouvertures).
        
        Returns:
            Liste de (start_pos, end_pos) le long du mur
        """
        if not self.openings:
            return [(0, self.length)]
        
        # Trier les ouvertures par position
        sorted_openings = sorted(self.openings, key=lambda o: o.position)
        
        segments = []
        current_pos = 0
        
        for opening in sorted_openings:
            if opening.position > current_pos:
                segments.append((current_pos, opening.position))
            current_pos = opening.position + opening.width
        
        if current_pos < self.length:
            segments.append((current_pos, self.length))
        
        return segments
    
    def validate_openings(self) -> Tuple[bool, List[str]]:
        """Vérifie qu'il n'y a pas de chevauchement d'ouvertures."""
        warnings = []
        sorted_openings = sorted(self.openings, key=lambda o: o.position)
        
        for i in range(len(sorted_openings) - 1):
            current = sorted_openings[i]
            next_op = sorted_openings[i + 1]
            
            current_end = current.position + current.width
            gap = next_op.position - current_end
            
            if gap < 0:
                warnings.append(
                    f"Chevauchement d'ouvertures: {current.door_id} et {next_op.door_id}"
                )
            elif gap < 0.10:
                warnings.append(
                    f"Ouvertures trop proches ({gap:.2f}m)"
                )
        
        return len(warnings) == 0, warnings


# =============================================================================
# GÉNÉRATEUR DE SEGMENTS DE MURS
# =============================================================================

class WallGeometryGenerator:
    """
    Analyse un FloorPlan et génère les segments de murs nécessaires.
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
        processed_edges: Set[Tuple[str, str]] = set()
        
        # Pour chaque paire de pièces adjacentes
        for room in floor_plan.placed_rooms:
            if not room.bounds:
                continue
            
            for other in floor_plan.get_adjacent_rooms(room):
                if not other.bounds:
                    continue
                
                # Éviter les doublons - clé basée sur les IDs des pièces triés
                pair = tuple(sorted([room.id, other.id]))
                if pair in processed_edges:
                    continue
                processed_edges.add(pair)
                
                # Obtenir le bord partagé
                shared = room.bounds.get_shared_edge(other.bounds)
                if not shared:
                    continue
                
                side, position, start, end = shared
                
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
                        segment.add_door_opening(door, door_pos_rel)
                
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
                # Calculer l'offset pour les ouvertures du segment suivant
                if is_horizontal:
                    offset = next_seg.start_x - current.start_x
                else:
                    offset = next_seg.start_y - current.start_y
                
                # Fusionner les ouvertures avec positions ajustées
                new_openings = list(current.openings)
                for op in next_seg.openings:
                    new_op = WallOpening(
                        position=op.position + offset,
                        width=op.width,
                        height=op.height,
                        base_height=op.base_height,
                        door_id=op.door_id,
                        door=op.door,
                        opening_type=op.opening_type
                    )
                    new_openings.append(new_op)
                
                # Créer le segment fusionné
                if is_horizontal:
                    current = WallSegment(
                        start_x=current.start_x,
                        start_y=current.start_y,
                        end_x=next_seg.end_x,
                        end_y=current.end_y,
                        thickness=current.thickness,
                        height=current.height,
                        openings=new_openings,
                        room1_id=current.room1_id,
                        room2_id=current.room2_id
                    )
                else:
                    current = WallSegment(
                        start_x=current.start_x,
                        start_y=current.start_y,
                        end_x=current.end_x,
                        end_y=next_seg.end_y,
                        thickness=current.thickness,
                        height=current.height,
                        openings=new_openings,
                        room1_id=current.room1_id,
                        room2_id=current.room2_id
                    )
            else:
                merged.append(current)
                current = next_seg
        
        merged.append(current)
        return merged


# =============================================================================
# CONSTRUCTEUR DE MESHES BLENDER
# =============================================================================

if HAS_BLENDER:

    class BlenderWallBuilder:
        """
        Construit les meshes Blender pour les segments de murs.
        """
        
        def __init__(self, config: Optional[GeometryConfig] = None):
            self.config = config or GeometryConfig()
            self.door_builder = DoorGeometryBuilder(self.config.get_door_config())
        
        def build_walls(
            self,
            segments: List[WallSegment],
            collection: bpy.types.Collection,
            floor_z: float = 0.0
        ) -> List[bpy.types.Object]:
            """
            Construit tous les murs et portes.
            
            Returns:
                Liste des objets créés
            """
            objects = []
            
            for i, segment in enumerate(segments):
                # Créer le mesh du mur (avec trous pour les portes)
                wall_obj = self._create_wall_mesh(segment, floor_z, f"Wall_{i:03d}")
                if wall_obj:
                    collection.objects.link(wall_obj)
                    objects.append(wall_obj)
                    self._apply_material(wall_obj, self.config.wall_material_name)
                
                # Créer les portes
                for opening in segment.get_doors():
                    if opening.door:
                        door_objects = self._create_door(
                            opening.door,
                            segment,
                            collection,
                            floor_z
                        )
                        objects.extend(door_objects.values())
            
            return objects
        
        def _create_wall_mesh(
            self,
            segment: WallSegment,
            floor_z: float,
            name: str
        ) -> Optional[bpy.types.Object]:
            """Crée le mesh d'un segment de mur avec ouvertures."""
            
            mesh = bpy.data.meshes.new(name)
            bm = bmesh.new()
            
            try:
                # Direction et normale du mur
                dx, dy = segment.direction
                nx, ny = segment.normal
                
                half_thick = segment.thickness / 2
                
                # Obtenir les parties solides du mur
                solid_parts = segment.get_solid_segments()
                
                for start_pos, end_pos in solid_parts:
                    # Calculer les positions 3D
                    s_x = segment.start_x + dx * start_pos
                    s_y = segment.start_y + dy * start_pos
                    e_x = segment.start_x + dx * end_pos
                    e_y = segment.start_y + dy * end_pos
                    
                    # Les 8 coins du bloc de mur
                    v = [
                        bm.verts.new((s_x - nx * half_thick, s_y - ny * half_thick, floor_z)),
                        bm.verts.new((e_x - nx * half_thick, e_y - ny * half_thick, floor_z)),
                        bm.verts.new((e_x + nx * half_thick, e_y + ny * half_thick, floor_z)),
                        bm.verts.new((s_x + nx * half_thick, s_y + ny * half_thick, floor_z)),
                        bm.verts.new((s_x - nx * half_thick, s_y - ny * half_thick, floor_z + segment.height)),
                        bm.verts.new((e_x - nx * half_thick, e_y - ny * half_thick, floor_z + segment.height)),
                        bm.verts.new((e_x + nx * half_thick, e_y + ny * half_thick, floor_z + segment.height)),
                        bm.verts.new((s_x + nx * half_thick, s_y + ny * half_thick, floor_z + segment.height)),
                    ]
                    
                    # Créer les 6 faces
                    bm.faces.new([v[0], v[1], v[5], v[4]])  # Face avant
                    bm.faces.new([v[2], v[3], v[7], v[6]])  # Face arrière
                    bm.faces.new([v[3], v[0], v[4], v[7]])  # Face gauche
                    bm.faces.new([v[1], v[2], v[6], v[5]])  # Face droite
                    bm.faces.new([v[4], v[5], v[6], v[7]])  # Dessus
                    bm.faces.new([v[3], v[2], v[1], v[0]])  # Dessous
                
                # Créer les parties au-dessus des portes
                for opening in segment.openings:
                    if opening.height < segment.height:
                        self._add_wall_above_opening(
                            bm, segment, opening, floor_z
                        )
                
                bm.to_mesh(mesh)
                
            finally:
                bm.free()
            
            return bpy.data.objects.new(name, mesh)
        
        def _add_wall_above_opening(
            self,
            bm: bmesh.types.BMesh,
            segment: WallSegment,
            opening: WallOpening,
            floor_z: float
        ) -> None:
            """Ajoute la partie de mur au-dessus d'une ouverture."""
            
            dx, dy = segment.direction
            nx, ny = segment.normal
            half_thick = segment.thickness / 2
            
            # Position de l'ouverture
            start_pos = opening.position
            end_pos = opening.position + opening.width
            
            s_x = segment.start_x + dx * start_pos
            s_y = segment.start_y + dy * start_pos
            e_x = segment.start_x + dx * end_pos
            e_y = segment.start_y + dy * end_pos
            
            z_bottom = floor_z + opening.base_height + opening.height
            z_top = floor_z + segment.height
            
            if z_bottom >= z_top:
                return
            
            # Les 8 coins
            v = [
                bm.verts.new((s_x - nx * half_thick, s_y - ny * half_thick, z_bottom)),
                bm.verts.new((e_x - nx * half_thick, e_y - ny * half_thick, z_bottom)),
                bm.verts.new((e_x + nx * half_thick, e_y + ny * half_thick, z_bottom)),
                bm.verts.new((s_x + nx * half_thick, s_y + ny * half_thick, z_bottom)),
                bm.verts.new((s_x - nx * half_thick, s_y - ny * half_thick, z_top)),
                bm.verts.new((e_x - nx * half_thick, e_y - ny * half_thick, z_top)),
                bm.verts.new((e_x + nx * half_thick, e_y + ny * half_thick, z_top)),
                bm.verts.new((s_x + nx * half_thick, s_y + ny * half_thick, z_top)),
            ]
            
            # Faces
            bm.faces.new([v[0], v[1], v[5], v[4]])
            bm.faces.new([v[2], v[3], v[7], v[6]])
            bm.faces.new([v[3], v[0], v[4], v[7]])
            bm.faces.new([v[1], v[2], v[6], v[5]])
            bm.faces.new([v[4], v[5], v[6], v[7]])
            bm.faces.new([v[3], v[2], v[1], v[0]])
        
        def _create_door(
            self,
            door: DoorOpening,
            segment: WallSegment,
            collection: bpy.types.Collection,
            floor_z: float
        ) -> Dict[str, bpy.types.Object]:
            """Crée tous les éléments d'une porte."""
            
            return self.door_builder.build_door(
                door=door,
                wall_thickness=segment.thickness,
                wall_start=segment.start_point,
                wall_direction=segment.direction,
                collection=collection,
                floor_z=floor_z,
                show_open=self.config.show_doors_open
            )
        
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
                
                bsdf = mat.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = (0.9, 0.9, 0.88, 1)
                    bsdf.inputs["Roughness"].default_value = 0.5
            
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)


    # =========================================================================
    # MARQUEURS DE PIÈCES (DEBUG)
    # =========================================================================

    class RoomMarkerBuilder:
        """Crée des marqueurs visuels pour identifier les pièces."""
        
        @staticmethod
        def create_room_markers(
            floor_plan: FloorPlan,
            collection: bpy.types.Collection,
            floor_z: float = 0.0,
            text_size: float = 0.3
        ) -> List[bpy.types.Object]:
            """Crée des textes pour identifier chaque pièce."""
            
            markers = []
            
            for room in floor_plan.placed_rooms:
                if not room.bounds:
                    continue
                
                # Créer un empty avec le nom de la pièce
                center_x, center_y = room.bounds.center
                
                empty = bpy.data.objects.new(f"Marker_{room.id}", None)
                empty.empty_display_type = 'PLAIN_AXES'
                empty.empty_display_size = 0.5
                empty.location = (center_x, center_y, floor_z + 0.1)
                
                # Ajouter une propriété custom pour le nom
                empty["room_name"] = room.name
                empty["room_area"] = f"{room.area:.1f}m²"
                
                collection.objects.link(empty)
                markers.append(empty)
            
            return markers


# =============================================================================
# FONCTIONS UTILITAIRES PRINCIPALES
# =============================================================================

def generate_interior_walls(
    floor_plan: FloorPlan,
    collection_name: str = "Interior_Walls",
    floor_z: float = 0.0,
    config: Optional[GeometryConfig] = None
) -> Dict[str, Any]:
    """
    Génère toutes les cloisons intérieures et portes pour un plan d'étage.
    
    Args:
        floor_plan: Plan d'étage avec pièces et portes
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
    partitions_coll_name = f"{collection_name}_Interior_Partitions"
    
    # Récupérer la collection parent
    parent_collection = None
    if collection_name in bpy.data.collections:
        parent_collection = bpy.data.collections[collection_name]
    
    # Créer ou nettoyer la sous-collection des cloisons
    if partitions_coll_name in bpy.data.collections:
        collection = bpy.data.collections[partitions_coll_name]
        # Nettoyer uniquement les objets de cette sous-collection
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    else:
        collection = bpy.data.collections.new(partitions_coll_name)
        # Lier à la collection parent ou à la scène
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
    
    # Compter les portes
    num_doors = sum(len(s.get_doors()) for s in segments)
    
    return {
        "collection": collection,
        "walls": wall_objects,
        "markers": markers,
        "num_segments": len(segments),
        "num_doors": num_doors
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
                    "position": o.position,
                    "width": o.width,
                    "height": o.height,
                    "base_height": o.base_height,
                    "type": o.opening_type,
                    "door_id": o.door_id
                }
                for o in seg.openings
            ],
            "rooms": [seg.room1_id, seg.room2_id]
        }
        partitions.append(partition)
    
    return partitions
