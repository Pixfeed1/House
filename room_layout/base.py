# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Classes de base pour la représentation des pièces et leur géométrie.

Ce module définit les structures de données fondamentales utilisées
par le solver et le générateur de géométrie.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set
from enum import Enum, auto
import math

from .room_types import RoomTypeDefinition, ROOM_TYPES, get_room_type


class WallSide(Enum):
    """Côtés possibles d'une pièce rectangulaire."""
    NORTH = auto()  # Y positif (haut)
    SOUTH = auto()  # Y négatif (bas)
    EAST = auto()   # X positif (droite)
    WEST = auto()   # X négatif (gauche)


@dataclass
class Rectangle:
    """
    Rectangle 2D positionné dans l'espace.

    Utilise le système de coordonnées Blender :
    - X : largeur (ouest → est)
    - Y : profondeur (sud → nord)
    - L'origine (0, 0) est le coin sud-ouest de la maison
    """

    x: float          # Position X du coin sud-ouest
    y: float          # Position Y du coin sud-ouest
    width: float      # Dimension en X
    depth: float      # Dimension en Y

    @property
    def x_min(self) -> float:
        return self.x

    @property
    def x_max(self) -> float:
        return self.x + self.width

    @property
    def y_min(self) -> float:
        return self.y

    @property
    def y_max(self) -> float:
        return self.y + self.depth

    @property
    def area(self) -> float:
        return self.width * self.depth

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.depth / 2)

    @property
    def aspect_ratio(self) -> float:
        """Ratio longueur/largeur (toujours >= 1)."""
        if self.width == 0 or self.depth == 0:
            return float('inf')
        return max(self.width, self.depth) / min(self.width, self.depth)

    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.depth)

    def contains_point(self, px: float, py: float, margin: float = 0.0) -> bool:
        """Vérifie si un point est dans le rectangle (avec marge optionnelle)."""
        return (self.x_min - margin <= px <= self.x_max + margin and
                self.y_min - margin <= py <= self.y_max + margin)

    def intersects(self, other: 'Rectangle', margin: float = 0.0) -> bool:
        """Vérifie si deux rectangles se chevauchent."""
        return not (
            self.x_max + margin < other.x_min - margin or
            self.x_min - margin > other.x_max + margin or
            self.y_max + margin < other.y_min - margin or
            self.y_min - margin > other.y_max + margin
        )

    def intersection(self, other: 'Rectangle') -> Optional['Rectangle']:
        """Retourne l'intersection de deux rectangles, ou None si pas d'intersection."""
        x_min = max(self.x_min, other.x_min)
        x_max = min(self.x_max, other.x_max)
        y_min = max(self.y_min, other.y_min)
        y_max = min(self.y_max, other.y_max)

        if x_min < x_max and y_min < y_max:
            return Rectangle(x_min, y_min, x_max - x_min, y_max - y_min)
        return None

    def touches(self, other: 'Rectangle', tolerance: float = 0.01) -> bool:
        """Vérifie si deux rectangles sont adjacents (se touchent sans se chevaucher)."""
        # Vérifie si les rectangles partagent un bord
        if abs(self.x_max - other.x_min) < tolerance or abs(self.x_min - other.x_max) < tolerance:
            # Adjacent horizontalement
            return (self.y_min < other.y_max and self.y_max > other.y_min)
        if abs(self.y_max - other.y_min) < tolerance or abs(self.y_min - other.y_max) < tolerance:
            # Adjacent verticalement
            return (self.x_min < other.x_max and self.x_max > other.x_min)
        return False

    def get_shared_edge(self, other: 'Rectangle', tolerance: float = 0.01) -> Optional[Tuple[WallSide, float, float, float]]:
        """
        Retourne le bord partagé avec un autre rectangle.

        Returns:
            Tuple (side, position, start, end) ou None
            - side: côté de self qui touche other
            - position: coordonnée X ou Y du bord
            - start, end: étendue du bord partagé
        """
        # Bord EST de self = Bord OUEST de other
        if abs(self.x_max - other.x_min) < tolerance:
            y_start = max(self.y_min, other.y_min)
            y_end = min(self.y_max, other.y_max)
            if y_start < y_end:
                return (WallSide.EAST, self.x_max, y_start, y_end)

        # Bord OUEST de self = Bord EST de other
        if abs(self.x_min - other.x_max) < tolerance:
            y_start = max(self.y_min, other.y_min)
            y_end = min(self.y_max, other.y_max)
            if y_start < y_end:
                return (WallSide.WEST, self.x_min, y_start, y_end)

        # Bord NORD de self = Bord SUD de other
        if abs(self.y_max - other.y_min) < tolerance:
            x_start = max(self.x_min, other.x_min)
            x_end = min(self.x_max, other.x_max)
            if x_start < x_end:
                return (WallSide.NORTH, self.y_max, x_start, x_end)

        # Bord SUD de self = Bord NORD de other
        if abs(self.y_min - other.y_max) < tolerance:
            x_start = max(self.x_min, other.x_min)
            x_end = min(self.x_max, other.x_max)
            if x_start < x_end:
                return (WallSide.SOUTH, self.y_min, x_start, x_end)

        return None

    def get_exterior_walls(self, building_bounds: 'Rectangle', tolerance: float = 0.01, wall_thickness: float = 0.20) -> List[WallSide]:
        """Retourne la liste des côtés qui sont sur l'extérieur du bâtiment."""
        exterior = []
        # Prendre en compte l'épaisseur du mur extérieur
        inner_margin = wall_thickness + tolerance

        if self.x_min <= building_bounds.x_min + inner_margin:
            exterior.append(WallSide.WEST)
        if self.x_max >= building_bounds.x_max - inner_margin:
            exterior.append(WallSide.EAST)
        if self.y_min <= building_bounds.y_min + inner_margin:
            exterior.append(WallSide.SOUTH)
        if self.y_max >= building_bounds.y_max - inner_margin:
            exterior.append(WallSide.NORTH)
        return exterior

    def subdivide_horizontal(self, ratio: float) -> Tuple['Rectangle', 'Rectangle']:
        """Divise le rectangle horizontalement (en Y)."""
        split_y = self.y + self.depth * ratio
        return (
            Rectangle(self.x, self.y, self.width, self.depth * ratio),
            Rectangle(self.x, split_y, self.width, self.depth * (1 - ratio))
        )

    def subdivide_vertical(self, ratio: float) -> Tuple['Rectangle', 'Rectangle']:
        """Divise le rectangle verticalement (en X)."""
        split_x = self.x + self.width * ratio
        return (
            Rectangle(self.x, self.y, self.width * ratio, self.depth),
            Rectangle(split_x, self.y, self.width * (1 - ratio), self.depth)
        )

    def shrink(self, margin: float) -> 'Rectangle':
        """Retourne un rectangle réduit de la marge spécifiée."""
        return Rectangle(
            self.x + margin,
            self.y + margin,
            max(0, self.width - 2 * margin),
            max(0, self.depth - 2 * margin)
        )

    def expand(self, margin: float) -> 'Rectangle':
        """Retourne un rectangle agrandi de la marge spécifiée."""
        return Rectangle(
            self.x - margin,
            self.y - margin,
            self.width + 2 * margin,
            self.depth + 2 * margin
        )

    def copy(self) -> 'Rectangle':
        """Retourne une copie du rectangle."""
        return Rectangle(self.x, self.y, self.width, self.depth)

    def __repr__(self) -> str:
        return f"Rectangle({self.x:.2f}, {self.y:.2f}, {self.width:.2f}×{self.depth:.2f})"


@dataclass
class WindowOpening:
    """Représente une ouverture (fenêtre ou porte-fenêtre) sur un mur extérieur."""

    wall_side: WallSide     # Côté du mur
    position: float         # Position le long du mur (depuis le début)
    width: float            # Largeur de l'ouverture
    height: float           # Hauteur de l'ouverture
    sill_height: float      # Hauteur d'allège
    is_door: bool = False   # True si c'est une porte-fenêtre

    @property
    def center_position(self) -> float:
        """Position du centre de l'ouverture."""
        return self.position + self.width / 2


@dataclass
class DoorOpening:
    """Représente une porte entre deux pièces."""

    room1_id: str           # ID de la première pièce
    room2_id: str           # ID de la deuxième pièce
    wall_side: WallSide     # Côté du mur (du point de vue room1)
    position: float         # Position le long du mur partagé
    width: float = 0.83     # Largeur standard
    height: float = 2.04    # Hauteur standard

    def connects(self, room_id: str) -> bool:
        """Vérifie si cette porte connecte la pièce spécifiée."""
        return room_id in (self.room1_id, self.room2_id)

    def get_other_room(self, room_id: str) -> Optional[str]:
        """Retourne l'ID de l'autre pièce connectée."""
        if room_id == self.room1_id:
            return self.room2_id
        if room_id == self.room2_id:
            return self.room1_id
        return None


@dataclass
class Room:
    """
    Représente une pièce dans le plan.

    Combine la définition du type (depuis room_types.py) avec
    la géométrie effective (rectangle) et les connexions.
    """

    # Identification
    id: str                              # ID unique (ex: 'CHAMBRE_1', 'SALON')
    room_type_id: str                    # Type de pièce (ex: 'CHAMBRE', 'SALON')
    floor: int = 0                       # Étage (0 = RDC)

    # Géométrie
    bounds: Optional[Rectangle] = None   # Rectangle de la pièce

    # Surface demandée (peut différer de bounds.area)
    target_area: Optional[float] = None

    # Fenêtres attribuées
    windows: List[WindowOpening] = field(default_factory=list)

    # Portes (références vers DoorOpening)
    door_ids: List[int] = field(default_factory=list)

    # État du placement
    is_placed: bool = False
    placement_score: float = 0.0         # Score de qualité du placement

    @property
    def room_type(self) -> Optional[RoomTypeDefinition]:
        """Retourne la définition du type de pièce."""
        return get_room_type(self.room_type_id)

    @property
    def area(self) -> float:
        """Surface effective de la pièce."""
        return self.bounds.area if self.bounds else 0.0

    @property
    def has_window(self) -> bool:
        """La pièce a-t-elle au moins une fenêtre?"""
        return len(self.windows) > 0

    @property
    def has_exterior_wall(self) -> bool:
        """La pièce a-t-elle un mur extérieur? (pour validation)"""
        # Cette propriété sera mise à jour par le solver
        return self._has_exterior_wall if hasattr(self, '_has_exterior_wall') else False

    @property
    def name(self) -> str:
        """Nom complet de la pièce."""
        room_def = self.room_type
        base_name = room_def.name if room_def else self.room_type_id

        # Ajouter numéro si ID contient un suffixe
        if '_' in self.id:
            parts = self.id.rsplit('_', 1)
            if parts[-1].isdigit():
                return f"{base_name} {parts[-1]}"
        return base_name

    def validate_placement(self, building_bounds: Rectangle, wall_thickness: float = 0.20) -> Tuple[bool, List[str]]:
        """
        Valide le placement de la pièce.

        Returns:
            Tuple (is_valid, list_of_warnings)
        """
        warnings = []
        room_def = self.room_type

        if not self.bounds:
            return False, ["Pièce non placée"]

        if not room_def:
            warnings.append(f"Type de pièce inconnu: {self.room_type_id}")
            return True, warnings

        # Vérifier la surface
        area_valid, area_msg = room_def.validate_area(self.area)
        if area_msg:
            warnings.append(area_msg)
        if not area_valid:
            return False, warnings

        # Vérifier les dimensions minimales
        if self.bounds.width < room_def.min_width:
            warnings.append(f"Largeur insuffisante ({self.bounds.width:.2f}m < {room_def.min_width}m)")
        if self.bounds.depth < room_def.min_width:
            warnings.append(f"Profondeur insuffisante ({self.bounds.depth:.2f}m < {room_def.min_width}m)")

        # Vérifier le ratio
        if self.bounds.aspect_ratio > room_def.max_aspect_ratio:
            warnings.append(f"Pièce trop allongée (ratio {self.bounds.aspect_ratio:.1f} > {room_def.max_aspect_ratio})")

        # Vérifier la fenêtre obligatoire
        exterior_walls = self.bounds.get_exterior_walls(building_bounds, wall_thickness=wall_thickness)
        has_exterior = len(exterior_walls) > 0

        if room_def.requires_window and not has_exterior:
            return False, [f"{room_def.name} doit avoir un mur extérieur (fenêtre obligatoire)"]

        return True, warnings

    def copy(self) -> 'Room':
        """Retourne une copie de la pièce."""
        new_room = Room(
            id=self.id,
            room_type_id=self.room_type_id,
            floor=self.floor,
            bounds=self.bounds.copy() if self.bounds else None,
            target_area=self.target_area,
            is_placed=self.is_placed,
            placement_score=self.placement_score
        )
        new_room.windows = self.windows.copy()
        new_room.door_ids = self.door_ids.copy()
        return new_room

    def __repr__(self) -> str:
        status = "✓" if self.is_placed else "○"
        area_str = f"{self.area:.1f}m²" if self.bounds else "?"
        return f"Room[{status}] {self.name} ({area_str})"


@dataclass
class FloorPlan:
    """
    Plan complet d'un étage.

    Contient toutes les pièces, les portes, et les métadonnées
    pour un étage donné.
    """

    floor: int                           # Numéro d'étage (0 = RDC)
    bounds: Rectangle                    # Contour de l'étage
    rooms: List[Room] = field(default_factory=list)
    doors: List[DoorOpening] = field(default_factory=list)

    # Réservations spéciales
    staircase_bounds: Optional[Rectangle] = None  # Zone escalier

    # Épaisseur des murs
    exterior_wall_thickness: float = 0.20
    interior_wall_thickness: float = 0.10

    @property
    def usable_area(self) -> float:
        """Surface utile (hors murs extérieurs)."""
        shrunk = self.bounds.shrink(self.exterior_wall_thickness)
        area = shrunk.area
        if self.staircase_bounds:
            area -= self.staircase_bounds.area
        return area

    @property
    def placed_rooms(self) -> List[Room]:
        """Retourne les pièces placées."""
        return [r for r in self.rooms if r.is_placed]

    @property
    def unplaced_rooms(self) -> List[Room]:
        """Retourne les pièces non placées."""
        return [r for r in self.rooms if not r.is_placed]

    def get_room_by_id(self, room_id: str) -> Optional[Room]:
        """Trouve une pièce par son ID."""
        for room in self.rooms:
            if room.id == room_id:
                return room
        return None

    def get_adjacent_rooms(self, room: Room) -> List[Room]:
        """Retourne les pièces adjacentes à une pièce donnée."""
        if not room.bounds:
            return []

        adjacent = []
        for other in self.rooms:
            if other.id != room.id and other.bounds:
                if room.bounds.touches(other.bounds):
                    adjacent.append(other)
        return adjacent

    def get_rooms_on_exterior(self, side: WallSide) -> List[Room]:
        """Retourne les pièces ayant un mur sur le côté extérieur spécifié."""
        result = []
        for room in self.placed_rooms:
            if room.bounds:
                exterior = room.bounds.get_exterior_walls(self.bounds)
                if side in exterior:
                    result.append(room)
        return result

    def calculate_total_adjacency_score(self) -> float:
        """Calcule le score total d'adjacence du plan."""
        from .room_types import calculate_adjacency_score

        total_score = 0.0
        checked_pairs: Set[Tuple[str, str]] = set()

        for room in self.placed_rooms:
            for adjacent in self.get_adjacent_rooms(room):
                # Éviter de compter deux fois
                pair = tuple(sorted([room.id, adjacent.id]))
                if pair not in checked_pairs:
                    checked_pairs.add(pair)
                    score = calculate_adjacency_score(room.room_type_id, adjacent.room_type_id)
                    total_score += score

        return total_score

    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valide le plan complet.

        Returns:
            Tuple (is_valid, list_of_errors_and_warnings)
        """
        messages = []
        is_valid = True

        # Vérifier que toutes les pièces sont placées
        unplaced = self.unplaced_rooms
        if unplaced:
            is_valid = False
            names = [r.name for r in unplaced]
            messages.append(f"Pièces non placées: {', '.join(names)}")

        # Valider chaque pièce
        for room in self.placed_rooms:
            room_valid, room_warnings = room.validate_placement(
                self.bounds,
                wall_thickness=self.exterior_wall_thickness
            )
            if not room_valid:
                is_valid = False
            messages.extend([f"{room.name}: {w}" for w in room_warnings])

        # Vérifier les chevauchements
        for i, room1 in enumerate(self.placed_rooms):
            for room2 in self.placed_rooms[i+1:]:
                if room1.bounds and room2.bounds:
                    if room1.bounds.intersects(room2.bounds, margin=-0.01):
                        is_valid = False
                        messages.append(f"Chevauchement: {room1.name} et {room2.name}")

        # Vérifier l'accessibilité (chaque pièce doit avoir une porte)
        for room in self.placed_rooms:
            if room.room_type_id not in ['ENTREE', 'COULOIR']:
                if not room.door_ids:
                    messages.append(f"{room.name}: pas de porte d'accès")

        return is_valid, messages

    def __repr__(self) -> str:
        floor_name = "RDC" if self.floor == 0 else f"Étage {self.floor}"
        return f"FloorPlan({floor_name}, {len(self.rooms)} pièces, {self.bounds.area:.1f}m²)"


@dataclass
class HousePlan:
    """
    Plan complet de la maison (multi-étages).
    """

    floors: List[FloorPlan] = field(default_factory=list)

    # Dimensions globales
    width: float = 0.0       # Dimension X
    depth: float = 0.0       # Dimension Y
    floor_height: float = 2.50  # Hauteur sous plafond

    @property
    def num_floors(self) -> int:
        return len(self.floors)

    @property
    def total_area(self) -> float:
        return sum(f.usable_area for f in self.floors)

    @property
    def all_rooms(self) -> List[Room]:
        result = []
        for floor in self.floors:
            result.extend(floor.rooms)
        return result

    def get_floor(self, floor_num: int) -> Optional[FloorPlan]:
        for floor in self.floors:
            if floor.floor == floor_num:
                return floor
        return None

    def validate(self) -> Tuple[bool, List[str]]:
        """Valide le plan complet."""
        all_valid = True
        all_messages = []

        for floor in self.floors:
            valid, messages = floor.validate()
            if not valid:
                all_valid = False
            floor_name = "RDC" if floor.floor == 0 else f"Étage {floor.floor}"
            all_messages.extend([f"[{floor_name}] {m}" for m in messages])

        return all_valid, all_messages
