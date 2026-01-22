# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Logique de placement intelligent des portes.

Ce module détermine:
- Où placer les portes entre pièces adjacentes
- Le sens d'ouverture optimal
- Le côté des charnières
- Le type de porte approprié
- La porte d'entrée principale
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set
import math

from .base import (
    Rectangle, Room, FloorPlan, WallSide,
    DoorOpening, DoorType, DoorSwingDirection, DoorHingeSide,
    DoorStyle, DoorHandleType
)
from .room_types import (
    ROOM_TYPES, get_door_requirements, DoorRequirements,
    calculate_adjacency_score
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class DoorPlacementConfig:
    """Configuration pour le placement des portes."""
    
    # Dimensions par défaut
    default_width: float = 0.83
    default_height: float = 2.04
    entry_door_width: float = 0.90
    entry_door_height: float = 2.15
    
    # Marges
    min_corner_distance: float = 0.20    # Distance min depuis un coin
    min_door_spacing: float = 0.30       # Espacement min entre portes
    min_edge_for_door: float = 0.50      # Marge totale min pour placer une porte
    
    # Préférences
    prefer_centered: bool = True         # Centrer les portes quand possible
    avoid_furniture_zones: bool = True   # Éviter zones meubles (coins)
    
    # PMR
    pmr_mode: bool = False               # Forcer largeurs PMR (0.90m)
    pmr_min_width: float = 0.90          # Largeur min PMR
    
    # Porte d'entrée
    generate_entry_door: bool = True     # Générer la porte d'entrée
    entry_preferred_side: WallSide = WallSide.SOUTH  # Façade préférée
    
    # Style par défaut
    default_style: DoorStyle = DoorStyle.PLAIN
    default_handle: DoorHandleType = DoorHandleType.LEVER
    entry_style: DoorStyle = DoorStyle.PANELED


# =============================================================================
# MOTEUR DE PLACEMENT
# =============================================================================

class DoorPlacementEngine:
    """
    Moteur de placement des portes.
    
    Génère automatiquement toutes les portes d'un plan d'étage
    en respectant les règles architecturales et les exigences
    de chaque type de pièce.
    """
    
    def __init__(self, config: Optional[DoorPlacementConfig] = None):
        self.config = config or DoorPlacementConfig()
        self._door_counter = 0
    
    def generate_doors(self, floor_plan: FloorPlan) -> List[DoorOpening]:
        """
        Génère toutes les portes pour un plan d'étage.
        
        Args:
            floor_plan: Plan avec pièces placées
            
        Returns:
            Liste de DoorOpening configurées
        """
        self._door_counter = 0
        doors: List[DoorOpening] = []
        processed_pairs: Set[Tuple[str, str]] = set()
        
        # Phase 1: Portes intérieures entre pièces adjacentes
        for room in floor_plan.placed_rooms:
            if not room.bounds:
                continue
            
            for other in floor_plan.get_adjacent_rooms(room):
                if not other.bounds:
                    continue
                
                # Éviter les doublons (A-B = B-A)
                pair = tuple(sorted([room.id, other.id]))
                if pair in processed_pairs:
                    continue
                processed_pairs.add(pair)
                
                # Créer la porte
                door = self._create_door_between_rooms(
                    room, other, floor_plan
                )
                if door:
                    doors.append(door)
                    # Enregistrer dans les pièces
                    room.door_ids.append(door.id)
                    other.door_ids.append(door.id)
        
        # Phase 2: Porte d'entrée principale
        if self.config.generate_entry_door:
            entry_door = self._create_entry_door(floor_plan)
            if entry_door:
                doors.append(entry_door)
                # Enregistrer dans la pièce d'entrée
                entry_room = floor_plan.get_room_by_id(entry_door.room1_id)
                if entry_room:
                    entry_room.door_ids.append(entry_door.id)
        
        # Phase 3: Validation et ajustements
        doors = self._validate_and_adjust(doors, floor_plan)
        
        return doors
    
    # -------------------------------------------------------------------------
    # CRÉATION DE PORTE ENTRE DEUX PIÈCES
    # -------------------------------------------------------------------------
    
    def _create_door_between_rooms(
        self,
        room1: Room,
        room2: Room,
        floor_plan: FloorPlan
    ) -> Optional[DoorOpening]:
        """Crée une porte entre deux pièces adjacentes."""
        
        # Obtenir le bord partagé
        shared = room1.bounds.get_shared_edge(room2.bounds)
        if not shared:
            return None
        
        side, position, start, end = shared
        edge_length = end - start
        
        # Déterminer la largeur de porte appropriée
        width = self._determine_door_width(room1, room2)
        
        # Vérifier qu'on peut placer la porte
        min_edge = width + self.config.min_edge_for_door
        if edge_length < min_edge:
            # Mur trop court - impossible de placer une porte
            return None
        
        # Calculer la position optimale
        door_position = self._calculate_optimal_position(
            start, end, width, room1, room2, side, floor_plan
        )
        
        # Déterminer le sens d'ouverture et les charnières
        swing_dir = self._determine_swing_direction(room1, room2, floor_plan)
        hinge_side = self._determine_hinge_side(
            room1, room2, side, door_position, width, floor_plan
        )
        
        # Déterminer le type de porte
        door_type = self._determine_door_type(room1, room2)
        
        # Déterminer le style
        style = self._determine_style(room1, room2, door_type)
        handle = self._determine_handle_type(room1, room2, door_type)
        
        # Créer l'ID unique
        door_id = self._generate_door_id()
        
        # Construire la porte
        door = DoorOpening(
            id=door_id,
            room1_id=room1.id,
            room2_id=room2.id,
            wall_side=side,
            position=door_position,
            width=width,
            height=self.config.default_height,
            door_type=door_type,
            swing_direction=swing_dir,
            hinge_side=hinge_side,
            style=style,
            handle_type=handle,
            has_lock=self._needs_lock(room1, room2),
            is_accessible=self.config.pmr_mode or width >= self.config.pmr_min_width,
            auto_generated=True
        )
        
        return door
    
    def _determine_door_width(self, room1: Room, room2: Room) -> float:
        """Détermine la largeur de porte appropriée."""
        
        # Mode PMR forcé
        if self.config.pmr_mode:
            return self.config.pmr_min_width
        
        # Chercher les exigences des deux pièces
        req1 = get_door_requirements(room1.room_type_id)
        req2 = get_door_requirements(room2.room_type_id)
        
        # Prendre la largeur la plus grande demandée
        width1 = req1.preferred_width or self.config.default_width
        width2 = req2.preferred_width or self.config.default_width
        
        result = max(width1, width2)
        
        # Vérifier PMR obligatoire
        if req1.requires_accessible or req2.requires_accessible:
            result = max(result, self.config.pmr_min_width)
        
        return result
    
    def _calculate_optimal_position(
        self,
        start: float,
        end: float,
        width: float,
        room1: Room,
        room2: Room,
        wall_side: WallSide,
        floor_plan: FloorPlan
    ) -> float:
        """Calcule la position optimale de la porte."""
        
        available_length = end - start
        margin = self.config.min_corner_distance
        
        # Position minimum et maximum
        pos_min = start + margin
        pos_max = end - width - margin
        
        if pos_min > pos_max:
            # Pas assez de place, centrer quand même
            return start + (available_length - width) / 2
        
        if self.config.prefer_centered:
            # Position centrée (par défaut)
            return start + (available_length - width) / 2
        
        # Position qui maximise l'espace de débattement
        # Analyser l'espace dans chaque pièce
        swing_room_id = None
        if self._determine_swing_direction(room1, room2, floor_plan) == DoorSwingDirection.PUSH:
            swing_room_id = room2.id
        else:
            swing_room_id = room1.id
        
        swing_room = floor_plan.get_room_by_id(swing_room_id) if swing_room_id else None
        
        if swing_room and swing_room.bounds:
            # Éviter les coins de la pièce de débattement
            center = swing_room.bounds.center
            
            # Calculer la position qui s'éloigne le plus du centre
            # (pour laisser l'espace central libre)
            mid_pos = start + (available_length - width) / 2
            
            if wall_side in [WallSide.NORTH, WallSide.SOUTH]:
                if center[0] > mid_pos + width/2:
                    return pos_min  # Porte à gauche
                else:
                    return pos_max  # Porte à droite
            else:
                if center[1] > mid_pos + width/2:
                    return pos_min
                else:
                    return pos_max
        
        return start + (available_length - width) / 2
    
    def _determine_swing_direction(
        self,
        room1: Room,
        room2: Room,
        floor_plan: FloorPlan
    ) -> DoorSwingDirection:
        """
        Détermine le sens d'ouverture optimal.
        
        Règles (par priorité):
        1. Exigence explicite du type de pièce (WC, etc.)
        2. Couloir → vers la pièce (dégager la circulation)
        3. Entrée → vers l'intérieur
        4. Par défaut → vers la plus grande pièce
        """
        
        # Exigences des pièces
        req1 = get_door_requirements(room1.room_type_id)
        req2 = get_door_requirements(room2.room_type_id)
        
        # Règle 1: Exigence explicite de room1
        if req1.required_swing:
            if req1.required_swing == 'PUSH':
                return DoorSwingDirection.PUSH
            elif req1.required_swing == 'PULL':
                return DoorSwingDirection.PULL
        
        # Règle 1bis: Exigence explicite de room2 (inverser)
        if req2.required_swing:
            if req2.required_swing == 'PUSH':
                # room2 veut PUSH = s'éloigner de room2 = PULL depuis room1
                return DoorSwingDirection.PULL
            elif req2.required_swing == 'PULL':
                return DoorSwingDirection.PUSH
        
        # Règle 2: Couloir → vers la pièce (pas vers le couloir)
        if room1.room_type_id == 'COULOIR':
            return DoorSwingDirection.PUSH  # Vers room2
        if room2.room_type_id == 'COULOIR':
            return DoorSwingDirection.PULL  # Vers room1 (pas vers couloir)
        
        # Règle 3: Entrée → généralement vers l'intérieur des pièces
        if room1.room_type_id == 'ENTREE':
            return DoorSwingDirection.PUSH
        if room2.room_type_id == 'ENTREE':
            return DoorSwingDirection.PULL
        
        # Règle 4: Vers la plus grande pièce (plus de place pour débattement)
        area1 = room1.bounds.area if room1.bounds else 0
        area2 = room2.bounds.area if room2.bounds else 0
        
        if area2 > area1 * 1.2:  # room2 significativement plus grande
            return DoorSwingDirection.PUSH
        elif area1 > area2 * 1.2:
            return DoorSwingDirection.PULL
        
        # Par défaut: PUSH (vers room2)
        return DoorSwingDirection.PUSH
    
    def _determine_hinge_side(
        self,
        room1: Room,
        room2: Room,
        wall_side: WallSide,
        door_position: float,
        door_width: float,
        floor_plan: FloorPlan
    ) -> DoorHingeSide:
        """
        Détermine le côté des charnières.
        
        Règles:
        1. Éviter que la porte ouverte bloque une autre porte
        2. Charnières du côté du mur le plus proche (pour cacher les charnières)
        3. Éviter de bloquer la circulation principale
        """
        
        if not room1.bounds:
            return DoorHingeSide.LEFT
        
        # Calculer le centre de la porte
        door_center = door_position + door_width / 2
        
        # Comparer avec le centre de la pièce
        room_center = room1.bounds.center
        
        if wall_side in [WallSide.NORTH, WallSide.SOUTH]:
            # Mur horizontal - comparer X
            # Charnières du côté le plus proche du coin
            if door_center < room_center[0]:
                return DoorHingeSide.LEFT
            else:
                return DoorHingeSide.RIGHT
        else:
            # Mur vertical - comparer Y
            if door_center < room_center[1]:
                return DoorHingeSide.LEFT
            else:
                return DoorHingeSide.RIGHT
    
    def _determine_door_type(
        self,
        room1: Room,
        room2: Room
    ) -> DoorType:
        """Détermine le type de porte approprié."""
        
        req1 = get_door_requirements(room1.room_type_id)
        req2 = get_door_requirements(room2.room_type_id)
        
        # Trouver les types autorisés communs
        allowed1 = set(req1.allowed_types)
        allowed2 = set(req2.allowed_types)
        allowed = allowed1 & allowed2
        
        if not allowed:
            # Pas de type commun, utiliser STANDARD
            return DoorType.STANDARD
        
        # Préférer STANDARD si disponible
        if 'STANDARD' in allowed:
            return DoorType.STANDARD
        
        # Sinon prendre le premier disponible
        type_name = list(allowed)[0]
        return DoorType[type_name]
    
    def _determine_style(
        self,
        room1: Room,
        room2: Room,
        door_type: DoorType
    ) -> DoorStyle:
        """Détermine le style visuel de la porte."""
        
        # Porte d'entrée
        if door_type == DoorType.ENTRY:
            return self.config.entry_style
        
        # Porte coulissante → style moderne
        if door_type in [DoorType.SLIDING, DoorType.POCKET]:
            return DoorStyle.FLUSH
        
        # Double porte → panneaux
        if door_type == DoorType.DOUBLE:
            return DoorStyle.PANELED
        
        # Porte-fenêtre → vitrée
        if door_type == DoorType.FRENCH:
            return DoorStyle.GLAZED
        
        # Par défaut
        return self.config.default_style
    
    def _determine_handle_type(
        self,
        room1: Room,
        room2: Room,
        door_type: DoorType
    ) -> DoorHandleType:
        """Détermine le type de poignée."""
        
        # Porte coulissante → barre ou encastrée
        if door_type == DoorType.SLIDING:
            return DoorHandleType.PULL_BAR
        
        if door_type == DoorType.POCKET:
            return DoorHandleType.RECESSED
        
        # Par défaut: levier (bec-de-cane)
        return self.config.default_handle
    
    def _needs_lock(self, room1: Room, room2: Room) -> bool:
        """Détermine si la porte nécessite une serrure."""
        req1 = get_door_requirements(room1.room_type_id)
        req2 = get_door_requirements(room2.room_type_id)
        return req1.requires_lock or req2.requires_lock
    
    # -------------------------------------------------------------------------
    # PORTE D'ENTRÉE PRINCIPALE
    # -------------------------------------------------------------------------
    
    def _create_entry_door(
        self,
        floor_plan: FloorPlan
    ) -> Optional[DoorOpening]:
        """
        Crée la porte d'entrée principale.
        
        Cherche la pièce d'entrée ou le salon et place une porte
        sur un mur extérieur.
        """
        
        # Trouver la pièce d'entrée
        entry_rooms = [
            r for r in floor_plan.placed_rooms
            if r.room_type_id == 'ENTREE'
        ]
        
        if not entry_rooms:
            # Pas d'entrée définie - utiliser le salon
            entry_rooms = [
                r for r in floor_plan.placed_rooms
                if r.room_type_id == 'SALON'
            ]
        
        if not entry_rooms:
            # Toujours rien - prendre la première pièce avec mur extérieur
            for room in floor_plan.placed_rooms:
                if room.bounds:
                    ext_walls = room.bounds.get_exterior_walls(
                        floor_plan.bounds,
                        wall_thickness=floor_plan.exterior_wall_thickness
                    )
                    if ext_walls:
                        entry_rooms = [room]
                        break
        
        if not entry_rooms:
            return None
        
        entry_room = entry_rooms[0]
        
        if not entry_room.bounds:
            return None
        
        # Trouver un mur extérieur approprié
        exterior_walls = entry_room.bounds.get_exterior_walls(
            floor_plan.bounds,
            wall_thickness=floor_plan.exterior_wall_thickness
        )
        
        if not exterior_walls:
            return None
        
        # Préférer le mur selon l'ordre de préférence
        preferred_order = [
            self.config.entry_preferred_side,
            WallSide.SOUTH,
            WallSide.EAST,
            WallSide.WEST,
            WallSide.NORTH
        ]
        
        chosen_wall = None
        for wall in preferred_order:
            if wall in exterior_walls:
                chosen_wall = wall
                break
        
        if not chosen_wall:
            chosen_wall = exterior_walls[0]
        
        # Calculer la position sur le mur
        wall_start, wall_end = self._get_wall_extent(
            entry_room.bounds, chosen_wall
        )
        
        wall_length = wall_end - wall_start
        door_width = self.config.entry_door_width
        
        # Vérifier qu'on peut placer la porte
        if wall_length < door_width + 2 * self.config.min_corner_distance:
            return None
        
        # Centrer la porte
        door_position = wall_start + (wall_length - door_width) / 2
        
        # Créer la porte d'entrée
        door_id = self._generate_door_id()
        
        return DoorOpening(
            id=door_id,
            room1_id=entry_room.id,
            room2_id=None,  # Extérieur
            wall_side=chosen_wall,
            position=door_position,
            width=door_width,
            height=self.config.entry_door_height,
            door_type=DoorType.ENTRY,
            swing_direction=DoorSwingDirection.PULL,  # S'ouvre vers l'intérieur
            hinge_side=DoorHingeSide.LEFT,
            style=self.config.entry_style,
            handle_type=DoorHandleType.LEVER,
            has_lock=True,
            is_fire_rated=False,
            is_accessible=True,
            auto_generated=True
        )
    
    def _get_wall_extent(
        self,
        bounds: Rectangle,
        wall_side: WallSide
    ) -> Tuple[float, float]:
        """Retourne (start, end) pour un mur donné."""
        
        if wall_side == WallSide.SOUTH:
            return (bounds.x_min, bounds.x_max)
        elif wall_side == WallSide.NORTH:
            return (bounds.x_min, bounds.x_max)
        elif wall_side == WallSide.WEST:
            return (bounds.y_min, bounds.y_max)
        else:  # EAST
            return (bounds.y_min, bounds.y_max)
    
    # -------------------------------------------------------------------------
    # VALIDATION ET AJUSTEMENTS
    # -------------------------------------------------------------------------
    
    def _validate_and_adjust(
        self,
        doors: List[DoorOpening],
        floor_plan: FloorPlan
    ) -> List[DoorOpening]:
        """
        Valide et ajuste les portes si nécessaire.
        
        - Vérifie les conflits de débattement
        - Ajuste les positions si chevauchement
        - Corrige les erreurs de configuration
        """
        
        valid_doors = []
        
        for door in doors:
            # Valider la porte
            is_valid, warnings = door.validate()
            
            if not is_valid:
                # Essayer de corriger
                door = self._try_fix_door(door)
            
            valid_doors.append(door)
        
        # Vérifier les conflits entre portes sur le même mur
        valid_doors = self._check_door_conflicts(valid_doors)
        
        return valid_doors
    
    def _try_fix_door(self, door: DoorOpening) -> DoorOpening:
        """Essaie de corriger une porte invalide."""
        
        # Si largeur PMR insuffisante mais marquée accessible
        if door.is_accessible and door.width < self.config.pmr_min_width:
            door.width = self.config.pmr_min_width
        
        # Si poignée inadaptée pour coulissante
        if door.is_sliding and door.handle_type == DoorHandleType.LEVER:
            door.handle_type = DoorHandleType.PULL_BAR
        
        return door
    
    def _check_door_conflicts(
        self,
        doors: List[DoorOpening]
    ) -> List[DoorOpening]:
        """
        Vérifie et corrige les conflits entre portes.
        
        Détecte les portes qui se chevauchent sur le même mur et les décale.
        """
        if len(doors) <= 1:
            return doors
        
        # Grouper les portes par segment de mur approximatif
        # Clé = (wall_side, position_mur_arrondie)
        wall_groups: Dict[tuple, List[DoorOpening]] = {}
        
        for door in doors:
            # Utiliser wall_side + une approximation de la position du mur
            # Pour les murs horizontaux (NORTH/SOUTH), la position Y est constante
            # Pour les murs verticaux (EAST/WEST), la position X est constante
            # On utilise room1_id comme proxy pour identifier le segment
            key = (door.wall_side, door.room1_id, door.room2_id)
            
            if key not in wall_groups:
                wall_groups[key] = []
            wall_groups[key].append(door)
        
        # Pour chaque groupe, vérifier les chevauchements
        adjusted_doors = []
        
        for key, group in wall_groups.items():
            if len(group) == 1:
                adjusted_doors.extend(group)
                continue
            
            # Trier par position
            group.sort(key=lambda d: d.position)
            
            # Vérifier et corriger les chevauchements
            for i, door in enumerate(group):
                if i == 0:
                    adjusted_doors.append(door)
                    continue
                
                prev_door = group[i - 1]
                prev_end = prev_door.position + prev_door.width
                
                # Minimum d'espacement entre portes
                min_gap = self.config.min_door_spacing
                
                if door.position < prev_end + min_gap:
                    # Chevauchement détecté - décaler cette porte
                    new_position = prev_end + min_gap
                    print(f"[DoorPlacement] ⚠️ Conflit détecté: {door.id} décalé de {door.position:.2f} à {new_position:.2f}")
                    door.position = new_position
                
                adjusted_doors.append(door)
        
        return adjusted_doors
    
    # -------------------------------------------------------------------------
    # UTILITAIRES
    # -------------------------------------------------------------------------
    
    def _generate_door_id(self) -> str:
        """Génère un ID unique pour une porte."""
        self._door_counter += 1
        return f"door_{self._door_counter:03d}"


# =============================================================================
# FONCTION UTILITAIRE PRINCIPALE
# =============================================================================

def generate_doors_for_floor_plan(
    floor_plan: FloorPlan,
    config: Optional[DoorPlacementConfig] = None
) -> List[DoorOpening]:
    """
    Génère toutes les portes pour un plan d'étage.
    
    Args:
        floor_plan: Plan avec pièces placées
        config: Configuration optionnelle
        
    Returns:
        Liste de DoorOpening
    """
    engine = DoorPlacementEngine(config)
    doors = engine.generate_doors(floor_plan)
    
    # Mettre à jour le floor_plan
    floor_plan.doors = doors
    
    return doors


def update_floor_plan_doors(
    floor_plan: FloorPlan,
    config: Optional[DoorPlacementConfig] = None
) -> None:
    """
    Met à jour les portes d'un floor_plan en place.
    
    Nettoie les anciennes portes et en génère de nouvelles.
    """
    # Nettoyer les références de portes dans les pièces
    for room in floor_plan.rooms:
        room.door_ids.clear()
    
    # Générer les nouvelles portes
    generate_doors_for_floor_plan(floor_plan, config)
