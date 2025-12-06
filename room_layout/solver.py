# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Algorithme de placement des pièces par contraintes.

Ce module implémente un système de placement intelligent qui :
1. Place d'abord les pièces nécessitant une fenêtre (salon, chambres)
2. Distribue l'espace restant aux pièces secondaires
3. Optimise les adjacences selon les scores définis
4. Génère les cloisons et portes nécessaires
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Set, Callable
from enum import Enum, auto
import math
import random

from .base import (
    Rectangle, Room, FloorPlan, HousePlan, 
    WallSide, DoorOpening, WindowOpening
)
from .room_types import (
    ROOM_TYPES, HOUSING_PRESETS, RoomTypeDefinition,
    RoomCategory, CorridorSettings, StaircaseSettings,
    get_room_type, calculate_adjacency_score
)


# =============================================================================
# CONFIGURATION DU SOLVER
# =============================================================================

@dataclass
class SolverConfig:
    """Configuration du solver de placement."""
    
    # Marges et tolérances
    wall_thickness: float = 0.10          # Épaisseur cloisons intérieures
    exterior_wall_thickness: float = 0.20 # Épaisseur murs extérieurs
    min_gap: float = 0.05                 # Gap minimum entre éléments
    
    # Fenêtres
    window_margin: float = 0.30           # Marge min entre fenêtre et coin
    window_width_default: float = 1.20    # Largeur fenêtre par défaut
    window_height_default: float = 1.20   # Hauteur fenêtre par défaut
    window_sill_height: float = 0.90      # Hauteur d'allège
    
    # Portes
    door_width: float = 0.83              # Largeur porte standard
    door_height: float = 2.04             # Hauteur porte standard
    door_margin: float = 0.15             # Marge min entre porte et coin
    
    # Couloir
    corridor_width_min: float = 0.90      # Largeur min couloir
    corridor_width_default: float = 1.00  # Largeur couloir par défaut
    corridor_width_max: float = 1.20      # Largeur max couloir
    
    # Algorithme
    max_iterations: int = 1000            # Iterations max pour optimisation
    min_improvement: float = 0.01         # Amélioration min pour continuer
    random_seed: Optional[int] = None     # Seed pour reproductibilité
    
    # Réduction de surface
    area_reduction_step: float = 0.05     # Réduction par étape (5%)
    area_reduction_max: float = 0.20      # Réduction max totale (20%)


class PlacementStrategy(Enum):
    """Stratégies de placement disponibles."""
    GREEDY = auto()           # Placement glouton (rapide)
    CONSTRAINT_BASED = auto() # Basé sur contraintes (équilibré)
    OPTIMIZED = auto()        # Avec optimisation (lent mais meilleur)


# =============================================================================
# HELPERS POUR LE PLACEMENT
# =============================================================================

@dataclass
class PlacementCandidate:
    """Un candidat de placement pour une pièce."""
    
    bounds: Rectangle
    score: float
    exterior_walls: List[WallSide]
    adjacent_rooms: List[str]      # IDs des pièces adjacentes
    warnings: List[str] = field(default_factory=list)
    
    def __lt__(self, other):
        return self.score > other.score  # Tri descendant par score


@dataclass
class PlacementResult:
    """Résultat du placement."""
    
    success: bool
    floor_plan: Optional[FloorPlan]
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    score: float = 0.0


# =============================================================================
# SOLVER PRINCIPAL
# =============================================================================

class RoomPlacementSolver:
    """
    Solver de placement des pièces.
    
    Utilise une approche en plusieurs phases :
    1. Analyse de l'espace disponible et des fenêtres existantes
    2. Placement des pièces prioritaires (nécessitant fenêtre)
    3. Placement des pièces secondaires
    4. Génération des portes et optimisation
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)
    
    # -------------------------------------------------------------------------
    # POINT D'ENTRÉE PRINCIPAL
    # -------------------------------------------------------------------------
    
    def solve(
        self,
        building_bounds: Rectangle,
        rooms_to_place: List[Tuple[str, float]],  # (room_type_id, target_area)
        floor: int = 0,
        existing_windows: Optional[List[WindowOpening]] = None,
        staircase_bounds: Optional[Rectangle] = None,
        strategy: PlacementStrategy = PlacementStrategy.CONSTRAINT_BASED
    ) -> PlacementResult:
        """
        Résout le placement des pièces.
        
        Args:
            building_bounds: Contour du bâtiment
            rooms_to_place: Liste de (type_pièce, surface_cible)
            floor: Numéro d'étage
            existing_windows: Fenêtres déjà placées (optionnel)
            staircase_bounds: Zone réservée pour escalier
            strategy: Stratégie de placement
            
        Returns:
            PlacementResult avec le plan ou les erreurs
        """
        # Créer le plan de base
        floor_plan = FloorPlan(
            floor=floor,
            bounds=building_bounds,
            exterior_wall_thickness=self.config.exterior_wall_thickness,
            interior_wall_thickness=self.config.wall_thickness,
            staircase_bounds=staircase_bounds
        )
        
        # Créer les objets Room
        rooms = self._create_rooms(rooms_to_place, floor)
        floor_plan.rooms = rooms
        
        # Vérifier la faisabilité
        feasible, msg = self._check_feasibility(floor_plan, rooms)
        if not feasible:
            return PlacementResult(
                success=False,
                floor_plan=None,
                messages=[msg]
            )
        
        # Analyser les murs extérieurs et fenêtres disponibles
        exterior_segments = self._analyze_exterior_walls(
            building_bounds, 
            existing_windows or [],
            staircase_bounds
        )
        
        # Trier les pièces par priorité de placement
        sorted_rooms = self._sort_rooms_by_priority(rooms)
        
        # Phase 1: Placer les pièces nécessitant une fenêtre
        success = self._place_window_rooms(floor_plan, sorted_rooms, exterior_segments)
        if not success:
            # Essayer de réduire les surfaces
            success = self._retry_with_reduced_areas(
                floor_plan, sorted_rooms, exterior_segments
            )
        
        if not success:
            return PlacementResult(
                success=False,
                floor_plan=floor_plan,
                messages=["Impossible de placer toutes les pièces nécessitant une fenêtre"]
            )
        
        # Phase 2: Placer les pièces secondaires
        success = self._place_remaining_rooms(floor_plan, sorted_rooms)
        
        if not success:
            return PlacementResult(
                success=False,
                floor_plan=floor_plan,
                messages=["Impossible de placer toutes les pièces secondaires"]
            )
        
        # Phase 3: Générer les portes
        self._generate_doors(floor_plan)
        
        # Phase 4: Optimiser si demandé
        if strategy == PlacementStrategy.OPTIMIZED:
            self._optimize_placement(floor_plan)
        
        # Calculer le score final
        score = self._calculate_plan_score(floor_plan)
        
        # Valider
        is_valid, validation_msgs = floor_plan.validate()
        
        return PlacementResult(
            success=is_valid,
            floor_plan=floor_plan,
            messages=validation_msgs if not is_valid else [],
            warnings=validation_msgs if is_valid else [],
            score=score
        )
    
    def solve_simple_grid(
        self,
        building_bounds: Rectangle,
        rooms_to_place: List[Tuple[str, float]],
        floor: int = 0
    ) -> PlacementResult:
        """
        Méthode de placement simplifiée utilisant une grille.
        Plus fiable pour les cas courants.
        """
        grid_solver = SimpleGridSolver(self.config)
        return grid_solver.solve(building_bounds, rooms_to_place, floor)
    
    # -------------------------------------------------------------------------
    # CRÉATION DES PIÈCES
    # -------------------------------------------------------------------------
    
    def _create_rooms(
        self, 
        rooms_to_place: List[Tuple[str, float]], 
        floor: int
    ) -> List[Room]:
        """Crée les objets Room à partir de la liste de pièces demandées."""
        rooms = []
        type_counters: Dict[str, int] = {}
        
        for room_type_id, target_area in rooms_to_place:
            # Générer un ID unique
            count = type_counters.get(room_type_id, 0) + 1
            type_counters[room_type_id] = count
            
            room_id = f"{room_type_id}_{count}" if count > 1 else room_type_id
            
            room = Room(
                id=room_id,
                room_type_id=room_type_id,
                floor=floor,
                target_area=target_area,
                is_placed=False
            )
            rooms.append(room)
        
        return rooms
    
    # -------------------------------------------------------------------------
    # VÉRIFICATION DE FAISABILITÉ
    # -------------------------------------------------------------------------
    
    def _check_feasibility(
        self, 
        floor_plan: FloorPlan, 
        rooms: List[Room]
    ) -> Tuple[bool, str]:
        """Vérifie si le placement est théoriquement possible."""
        
        # Surface disponible
        available_area = floor_plan.usable_area
        
        # Surface demandée (avec murs intérieurs estimés)
        total_requested = sum(r.target_area or 0 for r in rooms)
        wall_estimate = len(rooms) * 2 * self.config.wall_thickness * 3  # Estimation grossière
        total_with_walls = total_requested + wall_estimate
        
        if total_with_walls > available_area * 1.1:  # Marge de 10%
            return False, (
                f"Surface demandée ({total_requested:.1f}m²) trop grande "
                f"pour la surface disponible ({available_area:.1f}m²)"
            )
        
        # Nombre de pièces nécessitant fenêtre vs murs extérieurs
        rooms_needing_window = [
            r for r in rooms 
            if r.room_type and r.room_type.requires_window
        ]
        
        perimeter = floor_plan.bounds.perimeter
        min_window_space = len(rooms_needing_window) * 2.5  # 2.5m par pièce min
        
        if min_window_space > perimeter:
            return False, (
                f"Trop de pièces nécessitant une fenêtre ({len(rooms_needing_window)}) "
                f"pour le périmètre disponible ({perimeter:.1f}m)"
            )
        
        return True, ""
    
    # -------------------------------------------------------------------------
    # ANALYSE DES MURS EXTÉRIEURS
    # -------------------------------------------------------------------------
    
    def _analyze_exterior_walls(
        self,
        bounds: Rectangle,
        existing_windows: List[WindowOpening],
        staircase: Optional[Rectangle]
    ) -> Dict[WallSide, List[Tuple[float, float]]]:
        """
        Analyse les murs extérieurs et retourne les segments disponibles.
        
        Returns:
            Dict mapping WallSide -> liste de (start, end) segments disponibles
        """
        segments = {
            WallSide.SOUTH: [(bounds.x_min, bounds.x_max)],
            WallSide.NORTH: [(bounds.x_min, bounds.x_max)],
            WallSide.WEST: [(bounds.y_min, bounds.y_max)],
            WallSide.EAST: [(bounds.y_min, bounds.y_max)],
        }
        
        # Soustraire les fenêtres existantes
        for window in existing_windows:
            side = window.wall_side
            window_start = window.position
            window_end = window.position + window.width
            
            segments[side] = self._subtract_segment(
                segments[side], 
                window_start, 
                window_end,
                margin=self.config.window_margin
            )
        
        # Soustraire la zone escalier si elle touche un mur
        if staircase:
            for side in WallSide:
                if side == WallSide.SOUTH and abs(staircase.y_min - bounds.y_min) < 0.1:
                    segments[side] = self._subtract_segment(
                        segments[side], staircase.x_min, staircase.x_max, 0.1
                    )
                elif side == WallSide.NORTH and abs(staircase.y_max - bounds.y_max) < 0.1:
                    segments[side] = self._subtract_segment(
                        segments[side], staircase.x_min, staircase.x_max, 0.1
                    )
                elif side == WallSide.WEST and abs(staircase.x_min - bounds.x_min) < 0.1:
                    segments[side] = self._subtract_segment(
                        segments[side], staircase.y_min, staircase.y_max, 0.1
                    )
                elif side == WallSide.EAST and abs(staircase.x_max - bounds.x_max) < 0.1:
                    segments[side] = self._subtract_segment(
                        segments[side], staircase.y_min, staircase.y_max, 0.1
                    )
        
        return segments
    
    def _subtract_segment(
        self, 
        segments: List[Tuple[float, float]], 
        start: float, 
        end: float,
        margin: float = 0
    ) -> List[Tuple[float, float]]:
        """Soustrait un segment d'une liste de segments."""
        result = []
        for seg_start, seg_end in segments:
            if end + margin <= seg_start or start - margin >= seg_end:
                # Pas d'intersection
                result.append((seg_start, seg_end))
            else:
                # Intersection - découper
                if seg_start < start - margin:
                    result.append((seg_start, start - margin))
                if seg_end > end + margin:
                    result.append((end + margin, seg_end))
        return result
    
    # -------------------------------------------------------------------------
    # TRI PAR PRIORITÉ
    # -------------------------------------------------------------------------
    
    def _sort_rooms_by_priority(self, rooms: List[Room]) -> List[Room]:
        """
        Trie les pièces par priorité de placement.
        
        Ordre :
        1. Pièces nécessitant fenêtre, par priorité fenêtre croissante
        2. Pièces préférant fenêtre
        3. Pièces aveugles OK
        """
        def priority_key(room: Room) -> Tuple[int, int, float]:
            room_type = room.room_type
            if not room_type:
                return (3, 10, 0)
            
            # Catégorie principale
            if room_type.requires_window:
                cat = 0
            elif room_type.prefers_window:
                cat = 1
            else:
                cat = 2
            
            # Priorité fenêtre (1 = plus important)
            window_priority = room_type.window_priority
            
            # Surface (plus grande en premier dans chaque catégorie)
            area = -(room.target_area or room_type.area_default)
            
            return (cat, window_priority, area)
        
        return sorted(rooms, key=priority_key)
    
    # -------------------------------------------------------------------------
    # PLACEMENT DES PIÈCES AVEC FENÊTRE
    # -------------------------------------------------------------------------
    
    def _place_window_rooms(
        self,
        floor_plan: FloorPlan,
        sorted_rooms: List[Room],
        exterior_segments: Dict[WallSide, List[Tuple[float, float]]]
    ) -> bool:
        """Place les pièces nécessitant une fenêtre."""
        
        # Séparer les pièces par besoin de fenêtre
        window_rooms = [r for r in sorted_rooms if r.room_type and r.room_type.requires_window]
        
        if not window_rooms:
            return True
        
        # Espace disponible initial
        available_space = self._get_available_space(floor_plan)
        
        for room in window_rooms:
            candidates = self._find_window_room_candidates(
                room, floor_plan, exterior_segments, available_space
            )
            
            if not candidates:
                return False
            
            # Choisir le meilleur candidat
            best = max(candidates, key=lambda c: c.score)
            
            # Appliquer le placement
            room.bounds = best.bounds
            room.is_placed = True
            room.placement_score = best.score
            room._has_exterior_wall = len(best.exterior_walls) > 0
            
            # Mettre à jour l'espace disponible
            available_space = self._subtract_room_from_space(available_space, room.bounds)
            
            # Mettre à jour les segments extérieurs utilisés
            self._update_exterior_segments(exterior_segments, room.bounds, floor_plan.bounds)
        
        return True
    
    def _find_window_room_candidates(
        self,
        room: Room,
        floor_plan: FloorPlan,
        exterior_segments: Dict[WallSide, List[Tuple[float, float]]],
        available_space: List[Rectangle]
    ) -> List[PlacementCandidate]:
        """Trouve les candidats de placement pour une pièce nécessitant une fenêtre."""
        
        candidates = []
        room_type = room.room_type
        target_area = room.target_area or room_type.area_default
        min_width = room_type.min_width if room_type else 2.0
        
        # Pour chaque mur extérieur avec de l'espace
        for side, segments in exterior_segments.items():
            for seg_start, seg_end in segments:
                seg_length = seg_end - seg_start
                
                if seg_length < min_width:
                    continue
                
                # Calculer les dimensions possibles
                for facade_width in self._generate_widths(min_width, seg_length, 0.5):
                    depth = target_area / facade_width
                    
                    if depth < min_width:
                        continue
                    
                    # Vérifier le ratio
                    ratio = max(facade_width, depth) / min(facade_width, depth)
                    if room_type and ratio > room_type.max_aspect_ratio:
                        continue
                    
                    # Générer les positions le long du segment
                    for offset in self._generate_positions(seg_start, seg_end, facade_width, 0.5):
                        bounds = self._create_bounds_for_side(
                            side, floor_plan.bounds, offset, facade_width, depth
                        )
                        
                        if not bounds:
                            continue
                        
                        # Vérifier que ça rentre dans l'espace disponible
                        if not self._fits_in_available_space(bounds, available_space):
                            continue
                        
                        # Vérifier les collisions avec pièces placées
                        if self._collides_with_placed_rooms(bounds, floor_plan):
                            continue
                        
                        # Calculer le score
                        score = self._calculate_candidate_score(
                            room, bounds, floor_plan, [side]
                        )
                        
                        candidates.append(PlacementCandidate(
                            bounds=bounds,
                            score=score,
                            exterior_walls=[side],
                            adjacent_rooms=[]
                        ))
        
        return candidates
    
    def _create_bounds_for_side(
        self,
        side: WallSide,
        building: Rectangle,
        offset: float,
        facade_width: float,
        depth: float
    ) -> Optional[Rectangle]:
        """Crée un rectangle contre un mur extérieur."""
        
        wall_thick = self.config.exterior_wall_thickness
        
        if side == WallSide.SOUTH:
            return Rectangle(
                x=offset,
                y=building.y_min + wall_thick,
                width=facade_width,
                depth=depth
            )
        elif side == WallSide.NORTH:
            return Rectangle(
                x=offset,
                y=building.y_max - wall_thick - depth,
                width=facade_width,
                depth=depth
            )
        elif side == WallSide.WEST:
            return Rectangle(
                x=building.x_min + wall_thick,
                y=offset,
                width=depth,
                depth=facade_width
            )
        elif side == WallSide.EAST:
            return Rectangle(
                x=building.x_max - wall_thick - depth,
                y=offset,
                width=depth,
                depth=facade_width
            )
        
        return None
    
    # -------------------------------------------------------------------------
    # PLACEMENT DES PIÈCES RESTANTES
    # -------------------------------------------------------------------------
    
    def _place_remaining_rooms(
        self,
        floor_plan: FloorPlan,
        sorted_rooms: List[Room]
    ) -> bool:
        """Place les pièces ne nécessitant pas de fenêtre."""
        
        remaining = [r for r in sorted_rooms if not r.is_placed]
        
        if not remaining:
            return True
        
        available_space = self._get_available_space(floor_plan)
        
        for room in remaining:
            candidates = self._find_interior_room_candidates(
                room, floor_plan, available_space
            )
            
            if not candidates:
                # Essayer de subdiviser un espace existant
                candidates = self._try_subdivide_for_room(room, floor_plan, available_space)
            
            if not candidates:
                return False
            
            best = max(candidates, key=lambda c: c.score)
            
            room.bounds = best.bounds
            room.is_placed = True
            room.placement_score = best.score
            room._has_exterior_wall = len(best.exterior_walls) > 0
            
            available_space = self._subtract_room_from_space(available_space, room.bounds)
        
        return True
    
    def _find_interior_room_candidates(
        self,
        room: Room,
        floor_plan: FloorPlan,
        available_space: List[Rectangle]
    ) -> List[PlacementCandidate]:
        """Trouve les candidats de placement pour une pièce intérieure."""
        
        candidates = []
        room_type = room.room_type
        target_area = room.target_area or (room_type.area_default if room_type else 6.0)
        min_width = room_type.min_width if room_type else 1.5
        
        for space in available_space:
            if space.area < target_area * 0.8:
                continue
            
            # Essayer différentes configurations dans cet espace
            for width_ratio in [0.3, 0.4, 0.5, 0.6, 0.7]:
                width = space.width * width_ratio
                if width < min_width:
                    continue
                
                depth = target_area / width
                if depth < min_width or depth > space.depth:
                    continue
                
                # Positions dans l'espace
                for x_offset in [0, space.width - width]:
                    for y_offset in [0, space.depth - depth]:
                        bounds = Rectangle(
                            x=space.x + x_offset,
                            y=space.y + y_offset,
                            width=width,
                            depth=depth
                        )
                        
                        if self._collides_with_placed_rooms(bounds, floor_plan):
                            continue
                        
                        exterior = bounds.get_exterior_walls(
                            floor_plan.bounds, 
                            wall_thickness=self.config.exterior_wall_thickness
                        )
                        score = self._calculate_candidate_score(
                            room, bounds, floor_plan, exterior
                        )
                        
                        candidates.append(PlacementCandidate(
                            bounds=bounds,
                            score=score,
                            exterior_walls=exterior,
                            adjacent_rooms=[]
                        ))
        
        return candidates
    
    def _try_subdivide_for_room(
        self,
        room: Room,
        floor_plan: FloorPlan,
        available_space: List[Rectangle]
    ) -> List[PlacementCandidate]:
        """Essaie de subdiviser un espace pour faire rentrer une pièce."""
        
        candidates = []
        room_type = room.room_type
        target_area = room.target_area or (room_type.area_default if room_type else 6.0)
        min_width = room_type.min_width if room_type else 1.5
        
        # Trouver le plus grand espace disponible
        if not available_space:
            return candidates
        
        largest = max(available_space, key=lambda s: s.area)
        
        if largest.area < target_area:
            return candidates
        
        # Essayer une subdivision simple
        ratio = target_area / largest.area
        
        if largest.width > largest.depth:
            # Subdivision verticale
            new_width = largest.width * ratio
            if new_width >= min_width:
                bounds = Rectangle(
                    x=largest.x,
                    y=largest.y,
                    width=new_width,
                    depth=largest.depth
                )
                exterior = bounds.get_exterior_walls(
                    floor_plan.bounds, 
                    wall_thickness=self.config.exterior_wall_thickness
                )
                score = self._calculate_candidate_score(room, bounds, floor_plan, exterior)
                candidates.append(PlacementCandidate(
                    bounds=bounds, score=score, exterior_walls=exterior, adjacent_rooms=[]
                ))
        else:
            # Subdivision horizontale
            new_depth = largest.depth * ratio
            if new_depth >= min_width:
                bounds = Rectangle(
                    x=largest.x,
                    y=largest.y,
                    width=largest.width,
                    depth=new_depth
                )
                exterior = bounds.get_exterior_walls(
                    floor_plan.bounds, 
                    wall_thickness=self.config.exterior_wall_thickness
                )
                score = self._calculate_candidate_score(room, bounds, floor_plan, exterior)
                candidates.append(PlacementCandidate(
                    bounds=bounds, score=score, exterior_walls=exterior, adjacent_rooms=[]
                ))
        
        return candidates
    
    # -------------------------------------------------------------------------
    # GÉNÉRATION DES PORTES
    # -------------------------------------------------------------------------
    
    def _generate_doors(self, floor_plan: FloorPlan) -> None:
        """Génère les portes entre les pièces adjacentes."""
        
        doors: List[DoorOpening] = []
        door_id = 0
        
        # Pour chaque paire de pièces adjacentes
        for i, room1 in enumerate(floor_plan.placed_rooms):
            for room2 in floor_plan.placed_rooms[i+1:]:
                if not room1.bounds or not room2.bounds:
                    continue
                
                shared = room1.bounds.get_shared_edge(room2.bounds)
                if not shared:
                    continue
                
                side, position, start, end = shared
                edge_length = end - start
                
                # Vérifier qu'on peut placer une porte
                if edge_length < self.config.door_width + 2 * self.config.door_margin:
                    continue
                
                # Position de la porte (centrée sur le bord partagé)
                door_pos = start + (edge_length - self.config.door_width) / 2
                
                door = DoorOpening(
                    room1_id=room1.id,
                    room2_id=room2.id,
                    wall_side=side,
                    position=door_pos,
                    width=self.config.door_width,
                    height=self.config.door_height
                )
                
                doors.append(door)
                room1.door_ids.append(door_id)
                room2.door_ids.append(door_id)
                door_id += 1
        
        floor_plan.doors = doors
        
        # Vérifier l'accessibilité et ajouter des portes vers le couloir si nécessaire
        self._ensure_accessibility(floor_plan)
    
    def _ensure_accessibility(self, floor_plan: FloorPlan) -> None:
        """S'assure que toutes les pièces sont accessibles."""
        
        # Trouver l'entrée ou le couloir principal
        entry_rooms = [r for r in floor_plan.placed_rooms 
                       if r.room_type_id in ['ENTREE', 'COULOIR']]
        
        if not entry_rooms:
            # Pas d'entrée définie - le salon fait office d'entrée
            entry_rooms = [r for r in floor_plan.placed_rooms 
                           if r.room_type_id == 'SALON']
        
        if not entry_rooms:
            return
        
        # BFS pour vérifier l'accessibilité
        accessible = set()
        queue = [r.id for r in entry_rooms]
        
        while queue:
            current_id = queue.pop(0)
            if current_id in accessible:
                continue
            accessible.add(current_id)
            
            # Trouver les pièces connectées par des portes
            for door in floor_plan.doors:
                if door.room1_id == current_id and door.room2_id not in accessible:
                    queue.append(door.room2_id)
                elif door.room2_id == current_id and door.room1_id not in accessible:
                    queue.append(door.room1_id)
        
        # Avertir pour les pièces inaccessibles
        for room in floor_plan.placed_rooms:
            if room.id not in accessible:
                # TODO: Essayer de créer une porte de secours
                pass
    
    # -------------------------------------------------------------------------
    # OPTIMISATION
    # -------------------------------------------------------------------------
    
    def _optimize_placement(self, floor_plan: FloorPlan) -> None:
        """Optimise le placement par petits ajustements."""
        
        initial_score = self._calculate_plan_score(floor_plan)
        best_score = initial_score
        
        for iteration in range(self.config.max_iterations):
            # Choisir une pièce aléatoire à ajuster
            movable = [r for r in floor_plan.placed_rooms 
                       if r.room_type and not r.room_type.requires_window]
            
            if not movable:
                break
            
            room = random.choice(movable)
            
            # Essayer de petits déplacements
            original_bounds = room.bounds.copy()
            
            for dx, dy in [(0.1, 0), (-0.1, 0), (0, 0.1), (0, -0.1)]:
                room.bounds = Rectangle(
                    original_bounds.x + dx,
                    original_bounds.y + dy,
                    original_bounds.width,
                    original_bounds.depth
                )
                
                # Vérifier validité
                if self._collides_with_placed_rooms(room.bounds, floor_plan, exclude=room.id):
                    continue
                
                new_score = self._calculate_plan_score(floor_plan)
                
                if new_score > best_score:
                    best_score = new_score
                    original_bounds = room.bounds.copy()
                else:
                    room.bounds = original_bounds
            
            # Critère d'arrêt
            if best_score - initial_score < self.config.min_improvement:
                if iteration > 100:
                    break
    
    def _retry_with_reduced_areas(
        self,
        floor_plan: FloorPlan,
        sorted_rooms: List[Room],
        exterior_segments: Dict[WallSide, List[Tuple[float, float]]]
    ) -> bool:
        """Réessaie le placement avec des surfaces réduites."""
        
        reduction = self.config.area_reduction_step
        max_reduction = self.config.area_reduction_max
        
        while reduction <= max_reduction:
            # Réinitialiser
            for room in floor_plan.rooms:
                room.is_placed = False
                room.bounds = None
            
            # Réduire les surfaces cibles
            for room in floor_plan.rooms:
                if room.target_area:
                    room_type = room.room_type
                    min_area = room_type.area_min if room_type else 3.0
                    reduced = room.target_area * (1 - reduction)
                    room.target_area = max(reduced, min_area)
            
            # Réessayer
            if self._place_window_rooms(floor_plan, sorted_rooms, exterior_segments):
                return True
            
            reduction += self.config.area_reduction_step
        
        return False
    
    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------
    
    def _get_available_space(self, floor_plan: FloorPlan) -> List[Rectangle]:
        """Retourne les espaces disponibles dans le plan."""
        
        # Commencer avec tout l'espace intérieur
        inner = floor_plan.bounds.shrink(self.config.exterior_wall_thickness)
        available = [inner]
        
        # Soustraire l'escalier
        if floor_plan.staircase_bounds:
            available = self._subtract_rect_from_spaces(
                available, floor_plan.staircase_bounds
            )
        
        # Soustraire les pièces placées
        for room in floor_plan.placed_rooms:
            if room.bounds:
                available = self._subtract_rect_from_spaces(available, room.bounds)
        
        return available
    
    def _subtract_rect_from_spaces(
        self, 
        spaces: List[Rectangle], 
        to_remove: Rectangle
    ) -> List[Rectangle]:
        """Soustrait un rectangle d'une liste d'espaces."""
        result = []
        
        for space in spaces:
            if not space.intersects(to_remove):
                result.append(space)
                continue
            
            # Découper l'espace autour du rectangle à enlever
            # Partie gauche
            if space.x_min < to_remove.x_min:
                result.append(Rectangle(
                    space.x_min, space.y_min,
                    to_remove.x_min - space.x_min, space.depth
                ))
            
            # Partie droite
            if space.x_max > to_remove.x_max:
                result.append(Rectangle(
                    to_remove.x_max, space.y_min,
                    space.x_max - to_remove.x_max, space.depth
                ))
            
            # Partie basse (entre les côtés)
            left_bound = max(space.x_min, to_remove.x_min)
            right_bound = min(space.x_max, to_remove.x_max)
            
            if space.y_min < to_remove.y_min:
                result.append(Rectangle(
                    left_bound, space.y_min,
                    right_bound - left_bound, to_remove.y_min - space.y_min
                ))
            
            # Partie haute
            if space.y_max > to_remove.y_max:
                result.append(Rectangle(
                    left_bound, to_remove.y_max,
                    right_bound - left_bound, space.y_max - to_remove.y_max
                ))
        
        # Filtrer les espaces trop petits
        return [s for s in result if s.area > 1.0]
    
    def _subtract_room_from_space(
        self, 
        spaces: List[Rectangle], 
        room_bounds: Rectangle
    ) -> List[Rectangle]:
        """Soustrait une pièce de l'espace disponible."""
        return self._subtract_rect_from_spaces(spaces, room_bounds)
    
    def _fits_in_available_space(
        self, 
        bounds: Rectangle, 
        available: List[Rectangle]
    ) -> bool:
        """Vérifie si un rectangle rentre dans l'espace disponible."""
        for space in available:
            if (space.x_min <= bounds.x_min and space.x_max >= bounds.x_max and
                space.y_min <= bounds.y_min and space.y_max >= bounds.y_max):
                return True
        return False
    
    def _collides_with_placed_rooms(
        self, 
        bounds: Rectangle, 
        floor_plan: FloorPlan,
        exclude: Optional[str] = None
    ) -> bool:
        """Vérifie si un rectangle chevauche des pièces placées."""
        for room in floor_plan.placed_rooms:
            if exclude and room.id == exclude:
                continue
            if room.bounds and bounds.intersects(room.bounds, margin=-0.01):
                return True
        return False
    
    def _update_exterior_segments(
        self,
        segments: Dict[WallSide, List[Tuple[float, float]]],
        room_bounds: Rectangle,
        building_bounds: Rectangle
    ) -> None:
        """Met à jour les segments extérieurs après placement d'une pièce."""
        
        exterior = room_bounds.get_exterior_walls(
            building_bounds, 
            wall_thickness=self.config.exterior_wall_thickness
        )
        
        for side in exterior:
            if side in [WallSide.SOUTH, WallSide.NORTH]:
                segments[side] = self._subtract_segment(
                    segments[side],
                    room_bounds.x_min,
                    room_bounds.x_max,
                    margin=0.1
                )
            else:
                segments[side] = self._subtract_segment(
                    segments[side],
                    room_bounds.y_min,
                    room_bounds.y_max,
                    margin=0.1
                )
    
    def _generate_widths(
        self, 
        min_w: float, 
        max_w: float, 
        step: float
    ) -> List[float]:
        """Génère une liste de largeurs à tester."""
        widths = []
        w = min_w
        while w <= max_w:
            widths.append(w)
            w += step
        return widths
    
    def _generate_positions(
        self, 
        start: float, 
        end: float, 
        width: float, 
        step: float
    ) -> List[float]:
        """Génère une liste de positions à tester."""
        positions = []
        pos = start
        while pos + width <= end:
            positions.append(pos)
            pos += step
        return positions
    
    def _calculate_candidate_score(
        self,
        room: Room,
        bounds: Rectangle,
        floor_plan: FloorPlan,
        exterior_walls: List[WallSide]
    ) -> float:
        """Calcule le score d'un candidat de placement."""
        
        score = 0.0
        room_type = room.room_type
        
        # Bonus pour mur extérieur si préféré
        if room_type:
            if room_type.requires_window and exterior_walls:
                score += 10.0
            elif room_type.prefers_window and exterior_walls:
                score += 5.0
        
        # Score d'adjacence avec les pièces déjà placées
        for placed in floor_plan.placed_rooms:
            if placed.bounds and bounds.touches(placed.bounds):
                adj_score = calculate_adjacency_score(room.room_type_id, placed.room_type_id)
                score += adj_score
        
        # Pénalité pour surface trop différente de la cible
        target = room.target_area or (room_type.area_default if room_type else 10.0)
        area_diff = abs(bounds.area - target) / target
        score -= area_diff * 5.0
        
        # Bonus pour ratio raisonnable
        if bounds.aspect_ratio < 2.0:
            score += 2.0
        elif bounds.aspect_ratio > 3.0:
            score -= 2.0
        
        return score
    
    def _calculate_plan_score(self, floor_plan: FloorPlan) -> float:
        """Calcule le score global du plan."""
        
        score = 0.0
        
        # Score d'adjacence total
        score += floor_plan.calculate_total_adjacency_score()
        
        # Bonus pour pièces bien placées
        for room in floor_plan.placed_rooms:
            score += room.placement_score
        
        # Pénalité pour pièces non placées
        score -= len(floor_plan.unplaced_rooms) * 20.0
        
        return score


# =============================================================================
# FONCTION UTILITAIRE PRINCIPALE
# =============================================================================

def generate_floor_plan(
    width: float,
    depth: float,
    preset_id: str = 'T3',
    custom_rooms: Optional[List[Tuple[str, float]]] = None,
    floor: int = 0,
    config: Optional[SolverConfig] = None
) -> PlacementResult:
    """
    Fonction utilitaire pour générer un plan d'étage.
    
    Args:
        width: Largeur du bâtiment en m
        depth: Profondeur du bâtiment en m
        preset_id: ID du preset ('T1' à 'T6' ou 'CUSTOM')
        custom_rooms: Liste personnalisée si preset_id == 'CUSTOM'
        floor: Numéro d'étage
        config: Configuration du solver
        
    Returns:
        PlacementResult avec le plan généré
    """
    bounds = Rectangle(0, 0, width, depth)
    
    if preset_id == 'CUSTOM' and custom_rooms:
        rooms_to_place = custom_rooms
    elif preset_id in HOUSING_PRESETS:
        rooms_to_place = HOUSING_PRESETS[preset_id].get_rooms_list()
    else:
        raise ValueError(f"Preset inconnu: {preset_id}")
    
    solver = RoomPlacementSolver(config)
    # Utiliser le placement simple par grille
    return solver.solve_simple_grid(bounds, rooms_to_place, floor=floor)


# =============================================================================
# PLACEMENT SIMPLE PAR GRILLE
# =============================================================================

class SimpleGridSolver:
    """
    Solver simplifié utilisant une approche par grille.
    Plus fiable que l'approche par contraintes pour les cas simples.
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
    
    def solve(
        self,
        building_bounds: Rectangle,
        rooms_to_place: List[Tuple[str, float]],
        floor: int = 0
    ) -> PlacementResult:
        """
        Place les pièces en utilisant une grille simple.
        """
        wall_ext = self.config.exterior_wall_thickness
        wall_int = self.config.wall_thickness
        
        # Espace intérieur disponible
        inner_x = wall_ext
        inner_y = wall_ext
        inner_width = building_bounds.width - 2 * wall_ext
        inner_depth = building_bounds.depth - 2 * wall_ext
        
        # Créer le floor plan
        floor_plan = FloorPlan(
            floor=floor,
            bounds=building_bounds,
            exterior_wall_thickness=wall_ext,
            interior_wall_thickness=wall_int,
        )
        
        # Créer les objets Room
        rooms = []
        type_counters: Dict[str, int] = {}
        
        for room_type_id, target_area in rooms_to_place:
            count = type_counters.get(room_type_id, 0) + 1
            type_counters[room_type_id] = count
            room_id = f"{room_type_id}_{count}" if count > 1 else room_type_id
            
            room = Room(
                id=room_id,
                room_type_id=room_type_id,
                floor=floor,
                target_area=target_area,
                is_placed=False
            )
            rooms.append(room)
        
        floor_plan.rooms = rooms
        
        num_rooms = len(rooms)
        if num_rooms == 0:
            return PlacementResult(success=True, floor_plan=floor_plan, score=0)
        
        # Calculer la grille optimale
        # Pour N pièces, essayer différentes configurations cols x rows
        best_cols, best_rows = self._find_best_grid(num_rooms, inner_width, inner_depth)
        
        # Calculer les dimensions des cellules
        cell_width = inner_width / best_cols
        cell_height = inner_depth / best_rows
        
        # Trier les pièces : d'abord celles qui ont besoin de fenêtres
        sorted_rooms = sorted(rooms, key=lambda r: (
            0 if r.room_type and r.room_type.requires_window else 1,
            -(r.target_area or 0)
        ))
        
        # Créer les positions de cellules (prioriser les bords pour les pièces avec fenêtres)
        cell_positions = self._generate_cell_positions(best_cols, best_rows)
        
        # Placer chaque pièce dans une cellule
        for i, room in enumerate(sorted_rooms):
            if i >= len(cell_positions):
                break
            
            col, row = cell_positions[i]
            
            # Position de base de la cellule
            x = inner_x + col * cell_width
            y = inner_y + row * cell_height
            
            # Les pièces se touchent exactement (pas de gap)
            # Le mur sera dessiné sur la ligne de frontière
            w = cell_width
            h = cell_height
            
            room.bounds = Rectangle(x, y, w, h)
            room.is_placed = True
            room._has_exterior_wall = (col == 0 or col == best_cols - 1 or 
                                        row == 0 or row == best_rows - 1)
        
        # Générer les portes
        self._generate_doors(floor_plan)
        
        # Calculer le score
        score = floor_plan.calculate_total_adjacency_score()
        
        return PlacementResult(
            success=True,
            floor_plan=floor_plan,
            score=score
        )
    
    def _find_best_grid(self, num_rooms: int, width: float, depth: float) -> Tuple[int, int]:
        """Trouve la meilleure configuration de grille."""
        aspect = width / depth
        
        best_cols = 1
        best_rows = num_rooms
        best_diff = float('inf')
        
        for cols in range(1, num_rooms + 1):
            rows = math.ceil(num_rooms / cols)
            if cols * rows >= num_rooms:
                cell_aspect = (width / cols) / (depth / rows)
                # On veut des cellules aussi carrées que possible
                diff = abs(cell_aspect - 1.0)
                if diff < best_diff:
                    best_diff = diff
                    best_cols = cols
                    best_rows = rows
        
        return best_cols, best_rows
    
    def _generate_cell_positions(self, cols: int, rows: int) -> List[Tuple[int, int]]:
        """
        Génère les positions des cellules en priorisant les bords.
        Les pièces nécessitant des fenêtres seront placées en premier (sur les bords).
        """
        positions = []
        
        # D'abord les coins
        corners = [(0, 0), (cols-1, 0), (0, rows-1), (cols-1, rows-1)]
        for pos in corners:
            if pos not in positions and 0 <= pos[0] < cols and 0 <= pos[1] < rows:
                positions.append(pos)
        
        # Puis les bords (haut et bas)
        for c in range(1, cols - 1):
            if (c, 0) not in positions:
                positions.append((c, 0))
            if (c, rows - 1) not in positions:
                positions.append((c, rows - 1))
        
        # Puis les bords (gauche et droite)
        for r in range(1, rows - 1):
            if (0, r) not in positions:
                positions.append((0, r))
            if (cols - 1, r) not in positions:
                positions.append((cols - 1, r))
        
        # Enfin l'intérieur
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                if (c, r) not in positions:
                    positions.append((c, r))
        
        return positions
    
    def _generate_doors(self, floor_plan: FloorPlan) -> None:
        """Génère les portes entre pièces adjacentes."""
        doors: List[DoorOpening] = []
        door_id = 0
        processed_pairs: Set[Tuple[str, str]] = set()
        
        for room in floor_plan.placed_rooms:
            if not room.bounds:
                continue
            
            for other in floor_plan.get_adjacent_rooms(room):
                if not other.bounds:
                    continue
                
                # Éviter les doublons
                pair = tuple(sorted([room.id, other.id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                shared = room.bounds.get_shared_edge(other.bounds)
                if not shared:
                    continue
                
                side, position, start, end = shared
                edge_length = end - start
                
                if edge_length < self.config.door_width + 0.3:
                    continue
                
                door_pos = start + (edge_length - self.config.door_width) / 2
                
                door = DoorOpening(
                    room1_id=room.id,
                    room2_id=other.id,
                    wall_side=side,
                    position=door_pos,
                    width=self.config.door_width,
                    height=self.config.door_height
                )
                
                doors.append(door)
                room.door_ids.append(door_id)
                other.door_ids.append(door_id)
                door_id += 1
        
        floor_plan.doors = doors
