# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Window Placement - Placement intelligent des fenêtres basé sur le FloorPlan.

Ce module calcule les SEGMENTS LIBRES sur chaque mur extérieur
et place les fenêtres de manière architecturalement correcte.

Basé sur les principes de:
- Squarified Treemaps (Marson & Musse, 2010)
- Building Tools addon (ranjian0)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Set
from enum import Enum


# =============================================================================
# STRUCTURES DE DONNÉES
# =============================================================================

class ExteriorWall(Enum):
    """Murs extérieurs de la maison."""
    SOUTH = 'south'   # Façade (Y = 0)
    NORTH = 'north'   # Arrière (Y = length)
    WEST = 'west'     # Gauche (X = 0)
    EAST = 'east'     # Droite (X = width)


@dataclass
class FreeSegment:
    """
    Segment libre sur un mur extérieur où une fenêtre peut être placée.
    
    Exemple: Sur le mur SOUTH entre X=2.0 et X=5.5, segment de 3.5m libre.
    """
    wall: ExteriorWall
    start: float          # Position de début (X pour SOUTH/NORTH, Y pour WEST/EAST)
    end: float            # Position de fin
    room_id: Optional[str] = None   # Pièce associée
    room_type: Optional[str] = None # Type de pièce
    
    @property
    def length(self) -> float:
        """Longueur du segment."""
        return self.end - self.start
    
    @property
    def center(self) -> float:
        """Position centrale du segment."""
        return (self.start + self.end) / 2
    
    def can_fit_window(self, window_width: float, margin: float = 0.30) -> bool:
        """Vérifie si une fenêtre peut rentrer dans ce segment."""
        return self.length >= window_width + 2 * margin
    
    def __repr__(self) -> str:
        return f"FreeSegment({self.wall.value}: {self.start:.2f}-{self.end:.2f}, {self.length:.2f}m, room={self.room_type})"


@dataclass
class WindowPosition:
    """
    Position calculée pour une fenêtre.
    """
    wall: ExteriorWall
    position: float       # Position centrale sur le mur
    width: float          # Largeur de la fenêtre
    height: float         # Hauteur de la fenêtre
    sill_height: float    # Hauteur d'allège
    room_id: Optional[str] = None
    room_type: Optional[str] = None
    is_french_door: bool = False  # Porte-fenêtre
    
    def __repr__(self) -> str:
        return f"Window({self.wall.value}: pos={self.position:.2f}, {self.width}x{self.height}m)"


@dataclass
class WindowPlacementConfig:
    """Configuration pour le placement des fenêtres."""
    
    # Dimensions par défaut
    window_width: float = 1.20
    window_height: float = 1.20
    sill_height: float = 0.90      # Hauteur d'allège (90cm standard)
    
    # Marges
    corner_margin: float = 0.50    # Distance minimale aux coins
    partition_margin: float = 0.25 # Distance minimale aux cloisons
    door_margin: float = 0.40      # Distance minimale aux portes
    
    # Limites
    min_segment_for_window: float = 1.50  # Segment minimum pour placer une fenêtre
    max_windows_per_room: int = 2         # Maximum de fenêtres par pièce
    
    # Règles par type de pièce
    window_rules: Dict[str, dict] = field(default_factory=lambda: {
        'SALON': {'required': True, 'prefer_south': True, 'min_count': 1},
        'CHAMBRE': {'required': True, 'prefer_south': False, 'min_count': 1},
        'CHAMBRE_PARENTALE': {'required': True, 'prefer_south': True, 'min_count': 1},
        'CUISINE': {'required': True, 'prefer_south': False, 'min_count': 1},
        'SDB': {'required': False, 'prefer_south': False, 'min_count': 0},
        'WC': {'required': False, 'prefer_south': False, 'min_count': 0},
        'ENTREE': {'required': False, 'prefer_south': False, 'min_count': 0},
        'COULOIR': {'required': False, 'prefer_south': False, 'min_count': 0},
    })


# =============================================================================
# CALCULATEUR DE SEGMENTS LIBRES
# =============================================================================

class FreeSegmentCalculator:
    """
    Calcule les segments libres sur chaque mur extérieur.
    
    Algorithme:
    1. Pour chaque mur extérieur, identifier les pièces qui le touchent
    2. Pour chaque pièce, calculer le segment qu'elle occupe
    3. Identifier les points de cloison (intersections entre pièces)
    4. Les segments libres sont les portions de mur entre les cloisons
    """
    
    def __init__(
        self,
        house_width: float,
        house_length: float,
        wall_thickness: float = 0.20,
        config: Optional[WindowPlacementConfig] = None
    ):
        self.house_width = house_width
        self.house_length = house_length
        self.wall_thickness = wall_thickness
        self.config = config or WindowPlacementConfig()
        
        # Espace intérieur (hors murs extérieurs)
        self.inner_x_min = wall_thickness
        self.inner_x_max = house_width - wall_thickness
        self.inner_y_min = wall_thickness
        self.inner_y_max = house_length - wall_thickness
    
    def calculate_free_segments(self, floor_plan) -> Dict[ExteriorWall, List[FreeSegment]]:
        """
        Calcule tous les segments libres pour un plan d'étage.
        
        Args:
            floor_plan: FloorPlan avec les pièces placées
            
        Returns:
            Dict mapping chaque mur aux segments libres
        """
        result = {
            ExteriorWall.SOUTH: [],
            ExteriorWall.NORTH: [],
            ExteriorWall.WEST: [],
            ExteriorWall.EAST: [],
        }
        
        placed_rooms = [r for r in floor_plan.rooms if r.is_placed and r.bounds]
        
        if not placed_rooms:
            return result
        
        # Calculer pour chaque mur
        result[ExteriorWall.SOUTH] = self._calculate_segments_for_wall(
            placed_rooms, ExteriorWall.SOUTH
        )
        result[ExteriorWall.NORTH] = self._calculate_segments_for_wall(
            placed_rooms, ExteriorWall.NORTH
        )
        result[ExteriorWall.WEST] = self._calculate_segments_for_wall(
            placed_rooms, ExteriorWall.WEST
        )
        result[ExteriorWall.EAST] = self._calculate_segments_for_wall(
            placed_rooms, ExteriorWall.EAST
        )
        
        return result
    
    def _calculate_segments_for_wall(
        self, 
        rooms: List, 
        wall: ExteriorWall
    ) -> List[FreeSegment]:
        """
        Calcule les segments libres pour un mur spécifique.
        """
        margin = self.wall_thickness + 0.05
        tolerance = 0.05
        
        # Trouver les pièces qui touchent ce mur
        rooms_on_wall = []
        
        for room in rooms:
            b = room.bounds
            touches = False
            
            if wall == ExteriorWall.SOUTH:
                # Pièce touche le mur sud si y_min ≈ wall_thickness
                if b.y_min < margin:
                    touches = True
            elif wall == ExteriorWall.NORTH:
                # Pièce touche le mur nord si y_max ≈ length - wall_thickness
                if b.y_max > self.house_length - margin:
                    touches = True
            elif wall == ExteriorWall.WEST:
                # Pièce touche le mur ouest si x_min ≈ wall_thickness
                if b.x_min < margin:
                    touches = True
            elif wall == ExteriorWall.EAST:
                # Pièce touche le mur est si x_max ≈ width - wall_thickness
                if b.x_max > self.house_width - margin:
                    touches = True
            
            if touches:
                rooms_on_wall.append(room)
        
        if not rooms_on_wall:
            return []
        
        # Créer les segments pour chaque pièce
        segments = []
        
        for room in rooms_on_wall:
            b = room.bounds
            
            # Calculer le segment occupé par cette pièce sur le mur
            if wall in [ExteriorWall.SOUTH, ExteriorWall.NORTH]:
                # Segment en X
                start = max(b.x_min, self.inner_x_min)
                end = min(b.x_max, self.inner_x_max)
            else:
                # Segment en Y
                start = max(b.y_min, self.inner_y_min)
                end = min(b.y_max, self.inner_y_max)
            
            if end > start:
                # Appliquer les marges aux coins et cloisons
                segment_start = start + self.config.corner_margin
                segment_end = end - self.config.corner_margin
                
                # Vérifier si c'est une cloison intérieure (pas un coin de maison)
                if wall in [ExteriorWall.SOUTH, ExteriorWall.NORTH]:
                    if b.x_min > self.inner_x_min + tolerance:
                        segment_start = start + self.config.partition_margin
                    if b.x_max < self.inner_x_max - tolerance:
                        segment_end = end - self.config.partition_margin
                else:
                    if b.y_min > self.inner_y_min + tolerance:
                        segment_start = start + self.config.partition_margin
                    if b.y_max < self.inner_y_max - tolerance:
                        segment_end = end - self.config.partition_margin
                
                if segment_end > segment_start:
                    segments.append(FreeSegment(
                        wall=wall,
                        start=segment_start,
                        end=segment_end,
                        room_id=room.id,
                        room_type=room.room_type_id
                    ))
        
        return segments


# =============================================================================
# PLACEMENT DES FENÊTRES
# =============================================================================

class WindowPlacementEngine:
    """
    Moteur de placement des fenêtres.
    
    Utilise les segments libres pour placer les fenêtres de manière optimale.
    """
    
    def __init__(self, config: Optional[WindowPlacementConfig] = None):
        self.config = config or WindowPlacementConfig()
    
    def place_windows(
        self,
        free_segments: Dict[ExteriorWall, List[FreeSegment]],
        door_positions: Optional[Dict[ExteriorWall, List[float]]] = None
    ) -> List[WindowPosition]:
        """
        Place les fenêtres dans les segments libres.
        
        Args:
            free_segments: Segments libres calculés par FreeSegmentCalculator
            door_positions: Positions des portes à éviter (optionnel)
            
        Returns:
            Liste des positions de fenêtres
        """
        door_positions = door_positions or {}
        windows = []
        
        # Compteur de fenêtres par pièce
        windows_per_room: Dict[str, int] = {}
        
        # Traiter chaque mur
        for wall, segments in free_segments.items():
            for segment in segments:
                # Vérifier si on peut placer une fenêtre
                if not self._should_place_window(segment, windows_per_room):
                    continue
                
                # Vérifier si le segment est assez grand
                if not segment.can_fit_window(
                    self.config.window_width, 
                    self.config.partition_margin
                ):
                    continue
                
                # Vérifier les conflits avec les portes
                door_list = door_positions.get(wall, [])
                window_pos = segment.center
                
                if self._conflicts_with_door(window_pos, door_list):
                    continue
                
                # Créer la fenêtre
                window = WindowPosition(
                    wall=wall,
                    position=window_pos,
                    width=self.config.window_width,
                    height=self.config.window_height,
                    sill_height=self.config.sill_height,
                    room_id=segment.room_id,
                    room_type=segment.room_type
                )
                
                windows.append(window)
                
                # Incrémenter le compteur
                room_id = segment.room_id or 'unknown'
                windows_per_room[room_id] = windows_per_room.get(room_id, 0) + 1
        
        return windows
    
    def _should_place_window(
        self, 
        segment: FreeSegment,
        windows_per_room: Dict[str, int]
    ) -> bool:
        """Vérifie si on doit placer une fenêtre pour ce segment."""
        room_type = segment.room_type or 'UNKNOWN'
        rules = self.config.window_rules.get(room_type, {})
        
        # Vérifier le maximum par pièce
        room_id = segment.room_id or 'unknown'
        current_count = windows_per_room.get(room_id, 0)
        if current_count >= self.config.max_windows_per_room:
            return False
        
        # Les pièces de service n'ont pas besoin de fenêtre
        if room_type in ['SDB', 'WC', 'COULOIR']:
            return False
        
        return True
    
    def _conflicts_with_door(
        self, 
        window_pos: float, 
        door_positions: List[float]
    ) -> bool:
        """Vérifie si la fenêtre entre en conflit avec une porte."""
        half_width = self.config.window_width / 2
        margin = self.config.door_margin
        
        for door_pos in door_positions:
            if abs(window_pos - door_pos) < half_width + margin:
                return True
        
        return False


# =============================================================================
# FONCTION PRINCIPALE
# =============================================================================

def calculate_window_positions(
    floor_plan,
    house_width: float,
    house_length: float,
    wall_thickness: float = 0.20,
    door_positions: Optional[Dict[str, List[float]]] = None,
    config: Optional[WindowPlacementConfig] = None
) -> Tuple[List[WindowPosition], Dict[ExteriorWall, List[FreeSegment]]]:
    """
    Calcule les positions optimales des fenêtres pour un plan.
    
    Args:
        floor_plan: FloorPlan avec les pièces placées
        house_width: Largeur de la maison
        house_length: Longueur de la maison
        wall_thickness: Épaisseur des murs extérieurs
        door_positions: Dict {wall_name: [positions]} des portes
        config: Configuration du placement
        
    Returns:
        Tuple (liste de WindowPosition, dict des segments libres)
    """
    config = config or WindowPlacementConfig()
    
    # 1. Calculer les segments libres
    calculator = FreeSegmentCalculator(
        house_width=house_width,
        house_length=house_length,
        wall_thickness=wall_thickness,
        config=config
    )
    
    free_segments = calculator.calculate_free_segments(floor_plan)
    
    # 2. Convertir les positions de portes
    door_pos_converted = {}
    if door_positions:
        wall_map = {
            'front': ExteriorWall.SOUTH,
            'back': ExteriorWall.NORTH,
            'left': ExteriorWall.WEST,
            'right': ExteriorWall.EAST,
            'south': ExteriorWall.SOUTH,
            'north': ExteriorWall.NORTH,
            'west': ExteriorWall.WEST,
            'east': ExteriorWall.EAST,
        }
        for wall_name, positions in door_positions.items():
            wall = wall_map.get(wall_name.lower())
            if wall:
                door_pos_converted[wall] = positions
    
    # 3. Placer les fenêtres
    engine = WindowPlacementEngine(config)
    windows = engine.place_windows(free_segments, door_pos_converted)
    
    return windows, free_segments


def print_placement_summary(
    windows: List[WindowPosition],
    segments: Dict[ExteriorWall, List[FreeSegment]]
) -> None:
    """Affiche un résumé du placement."""
    print("\n[WindowPlacement] === RÉSUMÉ ===")
    
    print("\nSegments libres par mur:")
    for wall, segs in segments.items():
        if segs:
            print(f"  {wall.value}: {len(segs)} segment(s)")
            for s in segs:
                print(f"    - {s.start:.2f}-{s.end:.2f} ({s.length:.2f}m) [{s.room_type}]")
    
    print(f"\nFenêtres placées: {len(windows)}")
    for w in windows:
        print(f"  - {w.wall.value}: pos={w.position:.2f}m ({w.room_type})")


# =============================================================================
# INTÉGRATION AVEC OPERATORS_AUTO
# =============================================================================

def convert_to_blender_format(
    windows: List[WindowPosition],
    wall_thickness: float = 0.20
) -> Dict[str, List[dict]]:
    """
    Convertit les positions de fenêtres au format utilisé par operators_auto.py
    
    Returns:
        Dict {wall_name: [{pos, width, height, sill_height, room_id}]}
    """
    result = {
        'front': [],   # SOUTH
        'back': [],    # NORTH
        'left': [],    # WEST
        'right': [],   # EAST
    }
    
    wall_map = {
        ExteriorWall.SOUTH: 'front',
        ExteriorWall.NORTH: 'back',
        ExteriorWall.WEST: 'left',
        ExteriorWall.EAST: 'right',
    }
    
    for w in windows:
        wall_name = wall_map[w.wall]
        result[wall_name].append({
            'position': w.position,
            'width': w.width,
            'height': w.height,
            'sill_height': w.sill_height,
            'room_id': w.room_id,
            'room_type': w.room_type,
            'is_french_door': w.is_french_door,
        })
    
    return result


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Test simple avec un plan fictif
    print("Test du module window_placement.py")
    
    # Simuler un FloorPlan simple
    class MockBounds:
        def __init__(self, x, y, width, depth):
            self.x_min = x
            self.x_max = x + width
            self.y_min = y
            self.y_max = y + depth
    
    class MockRoom:
        def __init__(self, id, room_type, x, y, w, d):
            self.id = id
            self.room_type_id = room_type
            self.bounds = MockBounds(x, y, w, d)
            self.is_placed = True
    
    class MockFloorPlan:
        def __init__(self):
            self.rooms = [
                # Zone jour
                MockRoom('SALON', 'SALON', 0.20, 0.20, 6.0, 4.0),
                MockRoom('CUISINE', 'CUISINE', 6.20, 0.20, 3.6, 4.0),
                # Zone nuit
                MockRoom('CH1', 'CHAMBRE_PARENTALE', 0.20, 6.0, 3.0, 5.8),
                MockRoom('CH2', 'CHAMBRE', 3.20, 6.0, 2.5, 5.8),
                MockRoom('CH3', 'CHAMBRE', 5.70, 6.0, 2.5, 5.8),
                MockRoom('SDB', 'SDB', 8.20, 6.0, 1.6, 5.8),
            ]
    
    floor_plan = MockFloorPlan()
    
    windows, segments = calculate_window_positions(
        floor_plan=floor_plan,
        house_width=10.0,
        house_length=12.0,
        wall_thickness=0.20
    )
    
    print_placement_summary(windows, segments)
    
    # Convertir pour Blender
    blender_format = convert_to_blender_format(windows)
    print("\nFormat Blender:")
    for wall, wins in blender_format.items():
        if wins:
            print(f"  {wall}: {len(wins)} fenêtre(s)")
