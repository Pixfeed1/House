# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
ARCHITECTURAL SOLVER V2 - Générateur de plans réalistes.

Améliorations v2 :
- Couloir de distribution si > 3 chambres
- Évitement des fenêtres pour toutes les subdivisions
- Connexions logiques (entrée → couloir → pièces)
- SDB/WC toujours intérieurs (pas de gaspillage fenêtre)
- Portes uniquement entre pièces qui doivent communiquer
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Set
from enum import Enum, auto
import math

from .base import (
    Rectangle, Room, FloorPlan, WallSide,
    DoorOpening, DoorType, DoorSwingDirection, DoorHingeSide
)
from .room_types import (
    ROOM_TYPES, HOUSING_PRESETS,
    get_room_type, calculate_adjacency_score,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class SolverConfig:
    """Configuration du solver architectural."""
    
    exterior_wall_thickness: float = 0.20
    interior_wall_thickness: float = 0.10
    min_room_width: float = 1.50  # ✅ Réduit pour WC/SDB
    min_room_depth: float = 1.50  # ✅ Réduit aussi
    
    door_width_default: float = 0.83
    door_height_default: float = 2.04
    door_width_wc: float = 0.70
    door_width_entry: float = 0.90
    door_margin: float = 0.15
    
    window_width: float = 1.20
    window_margin: float = 0.60  # Marge pour éviter cloisons sur fenêtres
    
    corridor_width: float = 1.10  # Largeur couloir
    corridor_threshold: int = 3   # Couloir si >= 3 chambres
    
    random_seed: Optional[int] = None


BSPConfig = SolverConfig


# =============================================================================
# RÉSULTAT
# =============================================================================

@dataclass
class PlacementResult:
    success: bool
    floor_plan: Optional[FloorPlan]
    score: float = 0.0
    message: str = ""
    warnings: List[str] = field(default_factory=list)


BSPResult = PlacementResult


# =============================================================================
# SOLVER ARCHITECTURAL V2
# =============================================================================

class ArchitecturalSolver:
    """
    Solver avec logique architecturale réaliste.
    
    Layout généré :
    
    NORD (calme)
    ┌─────────┬─────────┬───────┬─────┐
    │ CHAMBRE │ CHAMBRE │  SDB  │ WC  │
    │ PARENT. │    2    │       │     │
    ├─────────┴─────────┴───────┴─────┤  ← Couloir si >= 3 chambres
    │            COULOIR              │
    ├─────────────────┬───────────────┤
    │                 │               │
    │     SALON       │   CUISINE     │
    │                 │               │
    └────────┬────────┴───────────────┘
             │ ENTRÉE │
    SUD (façade principale)
    """
    
    def __init__(self, config: Optional[SolverConfig] = None):
        self.config = config or SolverConfig()
    
    def solve(
        self,
        building_bounds: Rectangle,
        rooms_to_place: List[Tuple[str, float]],
        floor: int = 0
    ) -> PlacementResult:
        """Résout le placement."""
        
        warnings = []
        
        print(f"[Solver] Début: {len(rooms_to_place)} pièces à placer dans {building_bounds.width}x{building_bounds.depth}m")
        
        floor_plan = FloorPlan(
            floor=floor,
            bounds=building_bounds,
            exterior_wall_thickness=self.config.exterior_wall_thickness,
            interior_wall_thickness=self.config.interior_wall_thickness
        )
        
        rooms = self._create_rooms(rooms_to_place, floor)
        if not rooms:
            return PlacementResult(True, floor_plan, 0, "Aucune pièce")
        
        # Espace intérieur
        wall = self.config.exterior_wall_thickness
        inner = Rectangle(
            wall, wall,
            building_bounds.width - 2 * wall,
            building_bounds.depth - 2 * wall
        )
        
        print(f"[Solver] Espace intérieur: {inner.width:.2f}x{inner.depth:.2f}m")
        
        # Classifier les pièces
        day_rooms, night_rooms, service_rooms = self._classify_rooms(rooms)
        
        print(f"[Solver] Classification: {len(day_rooms)} jour, {len(night_rooms)} nuit, {len(service_rooms)} service")
        
        # Compter les chambres pour décider du couloir
        num_bedrooms = len([r for r in night_rooms if 'CHAMBRE' in r.room_type_id])
        use_corridor = num_bedrooms >= self.config.corridor_threshold
        
        # Calculer les zones
        zones = self._calculate_zones(inner, day_rooms, night_rooms, service_rooms, use_corridor)
        
        print(f"[Solver] Zones: day={zones.get('day')}, night={zones.get('night')}")
        
        # Placer les pièces
        self._place_day_zone(zones.get('day'), day_rooms, building_bounds)
        
        if use_corridor:
            self._place_corridor(zones.get('corridor'), service_rooms)
        
        self._place_night_zone(zones.get('night'), night_rooms, service_rooms, building_bounds, use_corridor)
        
        # Collecter toutes les pièces
        all_rooms = day_rooms + night_rooms + service_rooms
        floor_plan.rooms = all_rooms
        
        # Générer les portes intelligemment
        doors = self._generate_smart_doors(floor_plan, use_corridor)
        floor_plan.doors = doors
        
        # Stats
        placed = [r for r in all_rooms if r.is_placed]
        unplaced = [r for r in all_rooms if not r.is_placed]
        
        print(f"[Solver] Résultat: {len(placed)}/{len(all_rooms)} pièces placées")
        
        if unplaced:
            warnings.append(f"Non placées: {[r.room_type_id for r in unplaced]}")
            print(f"[Solver] ⚠️ Non placées: {[r.room_type_id for r in unplaced]}")
        
        for r in placed:
            print(f"[Solver]   ✓ {r.room_type_id}: {r.bounds}")
        
        score = floor_plan.calculate_total_adjacency_score()
        
        # ✅ Considérer comme succès si au moins 50% des pièces sont placées
        success = len(placed) >= len(all_rooms) * 0.5
        
        return PlacementResult(
            success=success,
            floor_plan=floor_plan,
            score=score,
            message=f"{len(placed)}/{len(all_rooms)} pièces",
            warnings=warnings
        )
    
    # =========================================================================
    # CRÉATION ET CLASSIFICATION
    # =========================================================================
    
    def _create_rooms(self, rooms_to_place: List[Tuple[str, float]], floor: int) -> List[Room]:
        rooms = []
        counters: Dict[str, int] = {}
        
        for room_type_id, target_area in rooms_to_place:
            count = counters.get(room_type_id, 0) + 1
            counters[room_type_id] = count
            room_id = f"{room_type_id}_{count}" if count > 1 else room_type_id
            
            rooms.append(Room(
                id=room_id,
                room_type_id=room_type_id,
                floor=floor,
                target_area=target_area,
                is_placed=False
            ))
        
        return rooms
    
    def _classify_rooms(self, rooms: List[Room]) -> Tuple[List[Room], List[Room], List[Room]]:
        """Classe en jour/nuit/service."""
        day = []
        night = []
        service = []
        
        for room in rooms:
            rt = room.room_type_id
            if rt in ['SALON', 'CUISINE', 'SALLE_A_MANGER', 'SEJOUR', 'ENTREE']:
                day.append(room)
            elif rt in ['CHAMBRE', 'CHAMBRE_PARENTALE', 'BUREAU']:
                night.append(room)
            else:
                service.append(room)
        
        # Trier par surface décroissante
        day.sort(key=lambda r: -(r.target_area or 0))
        night.sort(key=lambda r: -(r.target_area or 0))
        service.sort(key=lambda r: -(r.target_area or 0))
        
        return day, night, service
    
    # =========================================================================
    # CALCUL DES ZONES
    # =========================================================================
    
    def _calculate_zones(
        self,
        inner: Rectangle,
        day_rooms: List[Room],
        night_rooms: List[Room],
        service_rooms: List[Room],
        use_corridor: bool
    ) -> Dict[str, Rectangle]:
        """
        Divise l'espace en zones.
        
        IMPORTANT : Pas de zone entry séparée !
        L'entrée est DANS la zone jour pour assurer la contiguïté.
        """
        
        zones = {}
        
        # Surface totale demandée
        day_area = sum(r.target_area or 15 for r in day_rooms)
        night_area = sum(r.target_area or 10 for r in night_rooms)
        service_area = sum(r.target_area or 4 for r in service_rooms)
        
        # Couloir si nécessaire
        corridor_depth = self.config.corridor_width if use_corridor else 0
        
        usable_depth = inner.depth - corridor_depth
        
        # Ratio jour/nuit (services répartis)
        night_total = night_area + service_area * 0.7
        day_total = day_area + service_area * 0.3
        total = day_total + night_total
        
        if total > 0:
            day_ratio = day_total / total
            day_ratio = max(0.40, min(0.55, day_ratio))
        else:
            day_ratio = 0.5
        
        day_depth = usable_depth * day_ratio
        night_depth = usable_depth - day_depth
        
        # Minimums
        day_depth = max(3.0, day_depth)
        night_depth = max(3.0, night_depth)
        
        # Créer les zones (sud → nord)
        # Zone jour inclut l'entrée
        zones['day'] = Rectangle(inner.x, inner.y, inner.width, day_depth)
        
        current_y = inner.y + day_depth
        
        if use_corridor:
            zones['corridor'] = Rectangle(inner.x, current_y, inner.width, corridor_depth)
            current_y += corridor_depth
        
        zones['night'] = Rectangle(inner.x, current_y, inner.width, night_depth)
        
        return zones
    
    # =========================================================================
    # PLACEMENT ZONE JOUR
    # =========================================================================
    
    def _place_day_zone(self, zone: Optional[Rectangle], day_rooms: List[Room], building_bounds: Rectangle):
        """
        Place les pièces jour avec entrée intégrée.
        """
        if not zone:
            print("[Solver] ⚠️ Pas de zone jour!")
            return
        
        print(f"[Solver] Zone jour: {zone.width:.2f}x{zone.depth:.2f}m à ({zone.x:.2f}, {zone.y:.2f})")
        
        entree = next((r for r in day_rooms if r.room_type_id == 'ENTREE'), None)
        salon = next((r for r in day_rooms if r.room_type_id == 'SALON'), None)
        cuisine = next((r for r in day_rooms if r.room_type_id == 'CUISINE'), None)
        autres = [r for r in day_rooms if r.room_type_id not in ['SALON', 'CUISINE', 'ENTREE']]
        
        # Calculer la bande d'entrée si nécessaire
        entry_depth = 0
        if entree:
            entry_depth = min(2.2, max(1.5, zone.depth * 0.15))
        
        # Zone principale (au-dessus de l'entrée)
        main_zone = Rectangle(
            zone.x,
            zone.y + entry_depth,
            zone.width,
            zone.depth - entry_depth
        )
        
        print(f"[Solver] Zone principale jour: {main_zone.width:.2f}x{main_zone.depth:.2f}m")
        
        if salon and cuisine:
            # Répartir selon surfaces
            salon_area = salon.target_area or 20
            cuisine_area = cuisine.target_area or 10
            total = salon_area + cuisine_area
            
            salon_ratio = salon_area / total
            salon_ratio = max(0.50, min(0.65, salon_ratio))
            
            salon_width = main_zone.width * salon_ratio
            cuisine_width = main_zone.width - salon_width
            
            # SALON à gauche
            salon.bounds = Rectangle(main_zone.x, main_zone.y, salon_width, main_zone.depth)
            salon.is_placed = True
            print(f"[Solver]   SALON placé: {salon.bounds}")
            
            # CUISINE à droite
            cuisine.bounds = Rectangle(main_zone.x + salon_width, main_zone.y, cuisine_width, main_zone.depth)
            cuisine.is_placed = True
            print(f"[Solver]   CUISINE placée: {cuisine.bounds}")
            
            # ENTRÉE sous le salon (contiguë au salon)
            if entree:
                entry_width = min(salon_width * 0.6, 3.5)
                entry_x = salon.bounds.x + (salon_width - entry_width) / 2
                
                entree.bounds = Rectangle(entry_x, zone.y, entry_width, entry_depth)
                entree.is_placed = True
                print(f"[Solver]   ENTREE placée: {entree.bounds}")
                
        elif salon:
            salon.bounds = main_zone
            salon.is_placed = True
            print(f"[Solver]   SALON (seul) placé: {salon.bounds}")
            
            if entree:
                entry_width = min(salon.bounds.width * 0.4, 3.5)
                entry_x = salon.bounds.x + (salon.bounds.width - entry_width) / 2
                entree.bounds = Rectangle(entry_x, zone.y, entry_width, entry_depth)
                entree.is_placed = True
                print(f"[Solver]   ENTREE placée: {entree.bounds}")
                
        elif cuisine:
            cuisine.bounds = main_zone
            cuisine.is_placed = True
            print(f"[Solver]   CUISINE (seule) placée: {cuisine.bounds}")
        else:
            # Aucun salon ni cuisine - placer les autres pièces
            print("[Solver] ⚠️ Pas de salon ni cuisine dans zone jour")
            if day_rooms:
                # Prendre la première pièce et lui donner toute la zone
                first_room = day_rooms[0]
                first_room.bounds = main_zone
                first_room.is_placed = True
                print(f"[Solver]   {first_room.room_type_id} placé: {first_room.bounds}")
        
        # Autres pièces jour
        for room in autres:
            if not room.is_placed:
                # Essayer de subdiviser le salon
                if salon and salon.is_placed and salon.bounds and salon.bounds.width > 5:
                    room_width = min(salon.bounds.width * 0.35, 4)
                    room.bounds = Rectangle(
                        salon.bounds.x + salon.bounds.width - room_width,
                        salon.bounds.y,
                        room_width,
                        salon.bounds.depth
                    )
                    salon.bounds = Rectangle(
                        salon.bounds.x,
                        salon.bounds.y,
                        salon.bounds.width - room_width,
                        salon.bounds.depth
                    )
                    room.is_placed = True
                    print(f"[Solver]   {room.room_type_id} subdivisé depuis salon: {room.bounds}")
    
    # =========================================================================
    # PLACEMENT COULOIR
    # =========================================================================
    
    def _place_corridor(self, zone: Optional[Rectangle], service_rooms: List[Room]) -> Optional[Room]:
        """Crée et place le couloir."""
        if not zone:
            return None
        
        # Chercher si couloir existe déjà
        couloir = next((r for r in service_rooms if r.room_type_id == 'COULOIR'), None)
        
        if not couloir:
            # Créer le couloir
            couloir = Room(
                id='COULOIR',
                room_type_id='COULOIR',
                floor=0,
                target_area=zone.area,
                is_placed=False
            )
            service_rooms.append(couloir)
        
        couloir.bounds = zone
        couloir.is_placed = True
        couloir._has_exterior_wall = False
        
        return couloir
    
    # =========================================================================
    # PLACEMENT ZONE NUIT
    # =========================================================================
    
    def _place_night_zone(
        self,
        zone: Optional[Rectangle],
        night_rooms: List[Room],
        service_rooms: List[Room],
        building_bounds: Rectangle,
        use_corridor: bool
    ):
        if not zone:
            print("[Solver] ⚠️ Pas de zone nuit!")
            return
        
        print(f"[Solver] Zone nuit: {zone.width:.2f}x{zone.depth:.2f}m à ({zone.x:.2f}, {zone.y:.2f})")
        
        # Collecter SDB et WC non placés
        sdb_wc = [r for r in service_rooms if r.room_type_id in ['SDB', 'WC'] and not r.is_placed]
        
        # Chambres
        chambres = [r for r in night_rooms if 'CHAMBRE' in r.room_type_id]
        
        # Ordonner : chambre parentale en premier
        ch_parent = next((r for r in chambres if r.room_type_id == 'CHAMBRE_PARENTALE'), None)
        if ch_parent:
            chambres_ordered = [ch_parent] + [r for r in chambres if r != ch_parent]
        else:
            chambres_ordered = chambres
        
        # Toutes les pièces
        all_rooms = chambres_ordered + sdb_wc
        
        if not all_rooms:
            print("[Solver] ⚠️ Aucune pièce à placer en zone nuit")
            return
        
        print(f"[Solver] {len(all_rooms)} pièces en zone nuit: {[r.room_type_id for r in all_rooms]}")
        
        # Définir des largeurs minimales (en mètres)
        min_widths = {
            'WC': 1.10,
            'SDB': 1.60,
            'CHAMBRE': 2.50,
            'CHAMBRE_PARENTALE': 2.80
        }
        
        def get_min_width(room_type):
            for key, val in min_widths.items():
                if key in room_type:
                    return val
            return 2.0
        
        # Calculer largeur totale minimale requise
        total_min = sum(get_min_width(r.room_type_id) for r in all_rooms)
        
        if total_min > zone.width:
            # Réduire proportionnellement les minimums
            factor = zone.width / total_min
            print(f"[Solver] Ajustement minimums: {total_min:.2f}m → {zone.width:.2f}m (×{factor:.2f})")
            for key in min_widths:
                min_widths[key] *= factor
        
        # Calculer les largeurs basées sur la surface, avec minimum garanti
        total_area = sum(r.target_area or 8 for r in all_rooms)
        widths = []
        
        for room in all_rooms:
            room_area = room.target_area or 8
            proportional_width = zone.width * (room_area / total_area)
            min_w = get_min_width(room.room_type_id)
            width = max(min_w, proportional_width)
            widths.append(width)
        
        # Normaliser pour que le total = zone.width
        total_width = sum(widths)
        if total_width > zone.width:
            factor = zone.width / total_width
            widths = [w * factor for w in widths]
        
        print(f"[Solver] Largeurs: {[f'{w:.2f}' for w in widths]} = {sum(widths):.2f}m")
        
        # Placer les pièces
        current_x = zone.x
        
        for i, room in enumerate(all_rooms):
            room_width = widths[i]
            
            # Dernière pièce prend exactement ce qui reste
            if i == len(all_rooms) - 1:
                room_width = zone.x + zone.width - current_x
            
            if room_width > 0.8:  # Au moins 80cm
                room.bounds = Rectangle(current_x, zone.y, room_width, zone.depth)
                room.is_placed = True
                print(f"[Solver]   {room.room_type_id}: {room_width:.2f}m")
                current_x += room_width
            else:
                print(f"[Solver] ⚠️ {room.room_type_id}: trop étroit ({room_width:.2f}m)")
    
    # =========================================================================
    # GÉNÉRATION DES PORTES INTELLIGENTE
    # =========================================================================
    
    def _generate_smart_doors(self, floor_plan: FloorPlan, use_corridor: bool) -> List[DoorOpening]:
        """
        Génère les portes avec logique :
        - Entrée → Salon (ou Couloir si existe)
        - Couloir → Toutes les chambres, SDB, WC
        - Salon ↔ Cuisine (passage ou porte)
        - Pas de porte directe Chambre ↔ Chambre
        """
        doors: List[DoorOpening] = []
        door_id = 0
        
        # Identifier les pièces clés
        entree = next((r for r in floor_plan.placed_rooms if r.room_type_id == 'ENTREE'), None)
        salon = next((r for r in floor_plan.placed_rooms if r.room_type_id == 'SALON'), None)
        cuisine = next((r for r in floor_plan.placed_rooms if r.room_type_id == 'CUISINE'), None)
        couloir = next((r for r in floor_plan.placed_rooms if r.room_type_id == 'COULOIR'), None)
        
        chambres = [r for r in floor_plan.placed_rooms if 'CHAMBRE' in r.room_type_id]
        services = [r for r in floor_plan.placed_rooms if r.room_type_id in ['SDB', 'WC', 'CELLIER', 'BUANDERIE']]
        
        created_pairs: Set[Tuple[str, str]] = set()
        
        def add_door(room1: Room, room2: Room, door_type: DoorType = DoorType.STANDARD):
            nonlocal door_id
            
            if not room1.bounds or not room2.bounds:
                return
            
            pair = tuple(sorted([room1.id, room2.id]))
            if pair in created_pairs:
                return
            
            # Vérifier adjacence
            if not room1.bounds.touches(room2.bounds, tolerance=0.1):
                return
            
            shared = room1.bounds.get_shared_edge(room2.bounds, tolerance=0.1)
            if not shared:
                return
            
            created_pairs.add(pair)
            side, pos, start, end = shared
            
            edge_len = end - start
            
            # Largeur porte selon type
            if room1.room_type_id == 'WC' or room2.room_type_id == 'WC':
                door_w = self.config.door_width_wc
            elif door_type == DoorType.ENTRY:
                door_w = self.config.door_width_entry
            else:
                door_w = self.config.door_width_default
            
            # Vérifier qu'il y a assez de place
            if edge_len < door_w + 0.20:
                print(f"[Solver] ⚠️ Bord trop court pour porte: {edge_len:.2f}m < {door_w + 0.20:.2f}m")
                return
            
            # Position centrée - ABSOLUE (start + offset relatif)
            relative_pos = (edge_len - door_w) / 2
            door_pos = start + max(0.10, relative_pos)
            
            door_id += 1
            doors.append(DoorOpening(
                id=f"door_{door_id}",
                room1_id=room1.id,
                room2_id=room2.id,
                wall_side=side,
                position=door_pos,
                width=door_w,
                height=self.config.door_height_default,
                door_type=door_type,
                swing_direction=DoorSwingDirection.PUSH,
                hinge_side=DoorHingeSide.LEFT
            ))
        
        # 1. Porte d'entrée (extérieur)
        if entree and entree.bounds:
            door_id += 1
            # Position ABSOLUE: x_min de l'entrée + offset centré
            entry_door_pos = entree.bounds.x_min + (entree.bounds.width - self.config.door_width_entry) / 2
            doors.append(DoorOpening(
                id=f"door_entry_{door_id}",
                room1_id=entree.id,
                room2_id=None,
                wall_side=WallSide.SOUTH,
                position=entry_door_pos,
                width=self.config.door_width_entry,
                height=2.15,
                door_type=DoorType.ENTRY,
                swing_direction=DoorSwingDirection.PUSH,
                hinge_side=DoorHingeSide.LEFT
            ))
        
        # 2. Entrée → Salon (ou Couloir)
        if entree:
            if couloir:
                add_door(entree, couloir)
            elif salon:
                add_door(entree, salon)
        
        # 3. Salon ↔ Cuisine
        if salon and cuisine:
            add_door(salon, cuisine)
        
        # 4. Si couloir : couloir → toutes les pièces de nuit et services
        if couloir:
            for room in chambres + services:
                add_door(couloir, room)
            
            # Aussi salon → couloir si adjacent
            if salon:
                add_door(salon, couloir)
        else:
            # Pas de couloir : salon → chambres adjacentes
            if salon:
                for ch in chambres:
                    add_door(salon, ch)
                for svc in services:
                    add_door(salon, svc)
        
        # 5. Portes entre chambres adjacentes et leurs services (ex: suite parentale → SDB)
        for ch in chambres:
            for svc in services:
                if ch.bounds and svc.bounds and ch.bounds.touches(svc.bounds, tolerance=0.1):
                    # Seulement si chambre parentale ou si pas de couloir
                    if 'PARENTALE' in ch.room_type_id or not couloir:
                        add_door(ch, svc)
        
        return doors


# =============================================================================
# FONCTION UTILITAIRE
# =============================================================================

def generate_floor_plan(
    width: float,
    depth: float,
    preset_id: str = 'T3',
    custom_rooms: Optional[List[Tuple[str, float]]] = None,
    floor: int = 0,
    config: Optional[SolverConfig] = None
) -> PlacementResult:
    """Génère un plan d'étage."""
    
    bounds = Rectangle(0, 0, width, depth)
    
    if preset_id == 'CUSTOM' and custom_rooms:
        rooms_to_place = custom_rooms
    elif preset_id in HOUSING_PRESETS:
        rooms_to_place = HOUSING_PRESETS[preset_id].get_rooms_list()
    else:
        return PlacementResult(False, None, 0, f"Preset inconnu: {preset_id}")
    
    solver = ArchitecturalSolver(config)
    return solver.solve(bounds, rooms_to_place, floor)


# =============================================================================
# RÉTROCOMPATIBILITÉ
# =============================================================================

class RoomPlacementSolver:
    def __init__(self, config=None):
        self.solver = ArchitecturalSolver(config)
    
    def solve(self, bounds, rooms, floor=0, **kw):
        return self.solver.solve(bounds, rooms, floor)
    
    def solve_simple_grid(self, bounds, rooms, floor=0, **kw):
        return self.solver.solve(bounds, rooms, floor)


class SimpleGridSolver:
    def __init__(self, config=None, door_engine=None):
        self.solver = ArchitecturalSolver(config)
    
    def solve(self, bounds, rooms, floor=0, **kw):
        return self.solver.solve(bounds, rooms, floor)


# Classe factice pour rétrocompatibilité avec imports existants
class BSPNode:
    """Classe factice - le nouveau solver n'utilise plus BSP."""
    def __init__(self, bounds=None):
        self.bounds = bounds
        self.left = None
        self.right = None
        self.room = None


# Enum factice pour rétrocompatibilité
class SplitDirection:
    """Enum factice - le nouveau solver n'utilise plus BSP."""
    HORIZONTAL = 'HORIZONTAL'
    VERTICAL = 'VERTICAL'


BSPSolver = ArchitecturalSolver

__all__ = [
    'SolverConfig', 'BSPConfig', 'PlacementResult', 'BSPResult',
    'ArchitecturalSolver', 'BSPSolver', 'generate_floor_plan',
    'RoomPlacementSolver', 'SimpleGridSolver',
    'BSPNode', 'SplitDirection',  # Rétrocompatibilité
]
