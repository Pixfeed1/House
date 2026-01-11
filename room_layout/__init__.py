# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Room Layout - Système de distribution automatique des pièces.

Ce module Blender permet de:
- Définir les pièces d'un logement (type, surface)
- Générer automatiquement un plan de distribution optimal
- Créer les cloisons 3D avec portes complètes
- Gérer les adjacences et la circulation

Nouveautés v2.0:
- Portes complètes avec vantail, poignées des deux côtés, charnières
- Sens d'ouverture intelligent (règles par type de pièce)
- Porte d'entrée principale automatique
- Interface de configuration des portes
"""

bl_info = {
    "name": "Room Layout",
    "author": "mvaertan",
    "version": (2, 0, 0),
    "blender": (3, 6, 0),
    "location": "View3D > Sidebar > House",
    "description": "Distribution automatique des pièces avec portes complètes",
    "category": "Architecture",
}


# =============================================================================
# IMPORTS
# =============================================================================

# Imports standards
from typing import Optional, List, Dict, Any

# Imports internes (structures de données)
from .base import (
    # Géométrie
    Rectangle,
    WallSide,
    
    # Ouvertures
    WindowOpening,
    
    # Portes (nouveau système complet)
    DoorOpening,
    DoorType,
    DoorSwingDirection,
    DoorHingeSide,
    DoorStyle,
    DoorHandleType,
    
    # Pièces et plans
    Room,
    FloorPlan,
    HousePlan,
)

from .room_types import (
    RoomTypeDefinition,
    RoomCategory,
    DoorRequirements,
    ROOM_TYPES,
    HOUSING_PRESETS,
    DOOR_REQUIREMENTS,
    get_room_type,
    get_door_requirements,
    calculate_adjacency_score,
)

from .door_placement import (
    DoorPlacementConfig,
    DoorPlacementEngine,
    generate_doors_for_floor_plan,
    update_floor_plan_doors,
)

from .door_geometry import (
    DoorGeometryConfig,
    DoorGeometryBuilder,
    generate_door_geometry,
)

from .geometry import (
    GeometryConfig,
    WallOpening,
    WallSegment,
    WallGeometryGenerator,
    generate_interior_walls,
    get_partition_data_for_floor_plan,
)

from .solver import (
    SolverConfig,
    PlacementStrategy,
    PlacementResult,
    RoomPlacementSolver,
    SimpleGridSolver,
    generate_floor_plan,
)


# =============================================================================
# API PUBLIQUE SIMPLIFIÉE
# =============================================================================

class RoomLayoutManager:
    """
    Interface de haut niveau pour utiliser le système.
    
    Exemple d'utilisation:
    
        manager = RoomLayoutManager()
        
        # Configurer
        manager.set_building_dimensions(10.0, 8.0)
        manager.set_preset('T3')
        
        # Générer
        success = manager.generate()
        
        if success:
            manager.build_geometry()
    """
    
    def __init__(self):
        self.floor_plan: Optional[FloorPlan] = None
        self.solver_config = SolverConfig()
        self.geometry_config = GeometryConfig()
        self.door_config = DoorPlacementConfig()
        self.door_geometry_config = DoorGeometryConfig()
        
        # Dimensions par défaut
        self._width = 10.0
        self._depth = 8.0
        self._height = 2.50
        
        # Pièces à placer
        self._rooms_to_place: List[tuple] = []
    
    def set_building_dimensions(
        self, 
        width: float, 
        depth: float, 
        height: float = 2.50
    ) -> 'RoomLayoutManager':
        """Définit les dimensions du bâtiment."""
        self._width = width
        self._depth = depth
        self._height = height
        self.geometry_config.wall_height = height
        return self
    
    def set_preset(self, preset_id: str) -> 'RoomLayoutManager':
        """Charge un preset de logement (T1 à T6)."""
        if preset_id not in HOUSING_PRESETS:
            raise ValueError(f"Preset inconnu: {preset_id}")
        
        preset = HOUSING_PRESETS[preset_id]
        self._rooms_to_place = preset.get_rooms_list()
        return self
    
    def set_rooms(
        self, 
        rooms: List[tuple]
    ) -> 'RoomLayoutManager':
        """Définit les pièces manuellement. Format: [(type, surface), ...]"""
        self._rooms_to_place = rooms
        return self
    
    def add_room(
        self, 
        room_type: str, 
        area: float
    ) -> 'RoomLayoutManager':
        """Ajoute une pièce à la liste."""
        self._rooms_to_place.append((room_type, area))
        return self
    
    def clear_rooms(self) -> 'RoomLayoutManager':
        """Vide la liste des pièces."""
        self._rooms_to_place.clear()
        return self
    
    def set_door_options(
        self,
        default_width: float = 0.83,
        default_height: float = 2.04,
        generate_panels: bool = True,
        generate_handles: bool = True,
        generate_hinges: bool = True,
        show_open: bool = False,
        pmr_mode: bool = False
    ) -> 'RoomLayoutManager':
        """Configure les options de portes."""
        self.door_config.default_width = default_width
        self.door_config.default_height = default_height
        self.door_config.pmr_mode = pmr_mode
        
        self.door_geometry_config.generate_panel = generate_panels
        self.door_geometry_config.generate_handles = generate_handles
        self.door_geometry_config.generate_hinges = generate_hinges
        
        if show_open:
            self.door_geometry_config.preview_open_angle = 30.0
        else:
            self.door_geometry_config.preview_open_angle = 0.0
        
        return self
    
    def generate(self, floor: int = 0) -> bool:
        """
        Génère le plan de distribution.
        
        Returns:
            True si réussi, False sinon
        """
        if not self._rooms_to_place:
            return False
        
        # Configurer le solver avec les options de portes
        self.solver_config.door_config = self.door_config
        
        result = generate_floor_plan(
            width=self._width,
            depth=self._depth,
            preset_id='CUSTOM',
            custom_rooms=self._rooms_to_place,
            floor=floor,
            config=self.solver_config
        )
        
        if result.success:
            self.floor_plan = result.floor_plan
        
        return result.success
    
    def build_geometry(
        self, 
        collection_name: str = "Room_Layout",
        floor_z: float = 0.0
    ) -> Dict[str, Any]:
        """
        Construit la géométrie 3D dans Blender.
        
        Returns:
            Dict avec les objets créés et statistiques
        """
        if not self.floor_plan:
            raise RuntimeError("Aucun plan généré. Appelez generate() d'abord.")
        
        # Appliquer la config de géométrie des portes
        self.geometry_config.door_geometry_config = self.door_geometry_config
        
        result = generate_interior_walls(
            floor_plan=self.floor_plan,
            collection_name=collection_name,
            floor_z=floor_z,
            config=self.geometry_config
        )
        
        return result
    
    def get_rooms(self) -> List[Room]:
        """Retourne les pièces placées."""
        if not self.floor_plan:
            return []
        return self.floor_plan.placed_rooms
    
    def get_doors(self) -> List[DoorOpening]:
        """Retourne les portes générées."""
        if not self.floor_plan:
            return []
        return self.floor_plan.doors
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le plan."""
        if not self.floor_plan:
            return {}
        
        return {
            'total_rooms': len(self.floor_plan.rooms),
            'placed_rooms': len(self.floor_plan.placed_rooms),
            'total_doors': len(self.floor_plan.doors),
            'interior_doors': len(self.floor_plan.interior_doors),
            'exterior_doors': len(self.floor_plan.exterior_doors),
            'total_area': self.floor_plan.usable_area,
            'adjacency_score': self.floor_plan.calculate_total_adjacency_score()
        }


# =============================================================================
# ALIAS RÉTROCOMPATIBILITÉ
# =============================================================================

# Ancien nom -> nouveau nom (utilisé par operators_auto.py)
RoomLayoutGenerator = RoomLayoutManager


# =============================================================================
# ENREGISTREMENT BLENDER
# =============================================================================

def register():
    """Enregistre l'addon dans Blender."""
    from . import bl_properties
    from . import bl_ui
    
    bl_properties.register()
    bl_ui.register()


def unregister():
    """Désenregistre l'addon de Blender."""
    from . import bl_ui
    from . import bl_properties
    
    bl_ui.unregister()
    bl_properties.unregister()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Classes principales
    'Rectangle',
    'Room',
    'FloorPlan',
    'HousePlan',
    
    # Portes
    'DoorOpening',
    'DoorType',
    'DoorSwingDirection',
    'DoorHingeSide',
    'DoorStyle',
    'DoorHandleType',
    'DoorPlacementConfig',
    'DoorPlacementEngine',
    'DoorGeometryConfig',
    'DoorGeometryBuilder',
    
    # Types de pièces
    'RoomTypeDefinition',
    'RoomCategory',
    'DoorRequirements',
    'ROOM_TYPES',
    'HOUSING_PRESETS',
    
    # Géométrie
    'GeometryConfig',
    'WallSegment',
    'WallOpening',
    
    # Solver
    'SolverConfig',
    'PlacementResult',
    'RoomPlacementSolver',
    
    # Fonctions utilitaires
    'generate_floor_plan',
    'generate_interior_walls',
    'generate_doors_for_floor_plan',
    'generate_door_geometry',
    
    # Manager
    'RoomLayoutManager',
    'RoomLayoutGenerator',  # Alias rétrocompatibilité
]
