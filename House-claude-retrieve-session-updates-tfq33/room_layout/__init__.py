# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Room Layout - Système de distribution automatique des pièces.

Ce module Blender permet de:
- Définir les pièces d'un logement (type, surface)
- Générer automatiquement un plan de distribution optimal via BSP
- Créer les cloisons 3D avec portes complètes
- Gérer les adjacences et la circulation

Version 3.1 - Window Placement:
- Algorithme BSP (Binary Space Partitioning) pour un placement intelligent
- Pièces proportionnelles aux surfaces demandées
- Contraintes de fenêtres respectées automatiquement
- Optimisation des adjacences (cuisine/salon, SDB/chambres)
- ✅ NOUVEAU: Placement des fenêtres basé sur les segments libres
"""

bl_info = {
    "name": "Room Layout",
    "author": "mvaertan",
    "version": (3, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > House",
    "description": "Distribution automatique des pièces avec BSP Solver",
    "category": "Architecture",
}


# =============================================================================
# IMPORTS
# =============================================================================

from typing import Optional, List, Dict, Any

# Imports internes - Structures de données de base
from .base import (
    # Géométrie
    Rectangle,
    WallSide,
    
    # Ouvertures
    WindowOpening,
    
    # Portes
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

# Imports - Types de pièces et presets
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

# Imports - Placement des portes
from .door_placement import (
    DoorPlacementConfig,
    DoorPlacementEngine,
    generate_doors_for_floor_plan,
    update_floor_plan_doors,
)

# Imports - Géométrie des portes
from .door_geometry import (
    DoorGeometryConfig,
    DoorGeometryBuilder,
    generate_door_geometry,
)

# Imports - Géométrie des murs
from .geometry import (
    GeometryConfig,
    WallOpening,
    WallSegment,
    WallGeometryGenerator,
    generate_interior_walls,
    get_partition_data_for_floor_plan,
)

# Imports - BSP Solver (nouveau système)
from .solver import (
    BSPConfig,
    BSPSolver,
    BSPResult,
    BSPNode,
    SplitDirection,
    generate_floor_plan,
    # Alias rétrocompatibilité
    SolverConfig,
    PlacementResult,
    RoomPlacementSolver,
    SimpleGridSolver,
)

# ✅ NOUVEAU: Imports - Window Placement (système de placement des fenêtres)
try:
    from .window_placement import (
        ExteriorWall,
        FreeSegment,
        WindowPosition,
        WindowPlacementConfig,
        FreeSegmentCalculator,
        WindowPlacementEngine,
        calculate_window_positions,
        convert_to_blender_format,
        print_placement_summary,
    )
    HAS_WINDOW_PLACEMENT = True
except ImportError:
    HAS_WINDOW_PLACEMENT = False
    print("[RoomLayout] ⚠️ Module window_placement non disponible")


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
        self.solver_config = BSPConfig()
        self.geometry_config = GeometryConfig()
        self.door_config = DoorPlacementConfig()
        self.door_geometry_config = DoorGeometryConfig()
        
        # ✅ NOUVEAU: Config window placement
        self.window_config = WindowPlacementConfig() if HAS_WINDOW_PLACEMENT else None
        
        # Dimensions par défaut
        self._width = 10.0
        self._depth = 8.0
        self._height = 2.50
        
        # Pièces à placer
        self._rooms_to_place: List[tuple] = []
        
        # Résultat du solver
        self._last_result: Optional[BSPResult] = None
        
        # ✅ NOUVEAU: Positions des fenêtres calculées
        self._window_positions: List = []
        self._free_segments: Dict = {}
    
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
        Génère le plan de distribution avec le BSP Solver.
        
        Returns:
            True si réussi, False sinon
        """
        if not self._rooms_to_place:
            return False
        
        # Utiliser le BSP Solver
        result = generate_floor_plan(
            width=self._width,
            depth=self._depth,
            preset_id='CUSTOM',
            custom_rooms=self._rooms_to_place,
            floor=floor,
            config=self.solver_config
        )
        
        self._last_result = result
        
        if result.success:
            self.floor_plan = result.floor_plan
            
            # ✅ NOUVEAU: Calculer les positions des fenêtres
            if HAS_WINDOW_PLACEMENT and self.floor_plan:
                self._calculate_window_positions()
        
        return result.success
    
    def _calculate_window_positions(self) -> None:
        """✅ NOUVEAU: Calcule les positions optimales des fenêtres."""
        if not HAS_WINDOW_PLACEMENT or not self.floor_plan:
            return
        
        try:
            self._window_positions, self._free_segments = calculate_window_positions(
                floor_plan=self.floor_plan,
                house_width=self._width,
                house_length=self._depth,
                wall_thickness=self.solver_config.exterior_wall_thickness,
                config=self.window_config
            )
            
            print_placement_summary(self._window_positions, self._free_segments)
            
        except Exception as e:
            print(f"[RoomLayout] ⚠️ Erreur calcul fenêtres: {e}")
            self._window_positions = []
            self._free_segments = {}
    
    def get_window_positions(self) -> List:
        """✅ NOUVEAU: Retourne les positions des fenêtres calculées."""
        return self._window_positions
    
    def get_window_positions_blender_format(self) -> Dict[str, List[dict]]:
        """✅ NOUVEAU: Retourne les positions au format Blender (pour operators_auto.py)."""
        if not HAS_WINDOW_PLACEMENT or not self._window_positions:
            return {'front': [], 'back': [], 'left': [], 'right': []}
        
        return convert_to_blender_format(
            self._window_positions, 
            self.solver_config.exterior_wall_thickness
        )
    
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
        
        stats = {
            'total_rooms': len(self.floor_plan.rooms),
            'placed_rooms': len(self.floor_plan.placed_rooms),
            'total_doors': len(self.floor_plan.doors),
            'interior_doors': len(self.floor_plan.interior_doors),
            'exterior_doors': len(self.floor_plan.exterior_doors),
            'total_area': self.floor_plan.usable_area,
            'adjacency_score': self.floor_plan.calculate_total_adjacency_score(),
            'solver_score': self._last_result.score if self._last_result else 0.0
        }
        
        # ✅ NOUVEAU: Stats fenêtres
        if self._window_positions:
            stats['total_windows'] = len(self._window_positions)
        
        return stats
    
    def get_partition_data(self, floor_plan: Optional[FloorPlan] = None) -> List[Dict]:
        """
        Retourne les données des cloisons pour l'intégration avec operators_auto.py
        """
        fp = floor_plan or self.floor_plan
        if not fp:
            return []
        return get_partition_data_for_floor_plan(fp)
    
    def validate_configuration(
        self,
        width: float,
        depth: float,
        preset_id: str
    ) -> tuple:
        """
        Valide une configuration avant génération.
        
        Returns:
            Tuple (is_valid, list_of_messages)
        """
        messages = []
        is_valid = True
        
        # Vérifier le preset
        if preset_id != 'CUSTOM' and preset_id not in HOUSING_PRESETS:
            messages.append(f"Preset inconnu: {preset_id}")
            is_valid = False
            return (is_valid, messages)
        
        # Récupérer les pièces
        if preset_id == 'CUSTOM':
            rooms = self._rooms_to_place
        else:
            rooms = HOUSING_PRESETS[preset_id].get_rooms_list()
        
        if not rooms:
            messages.append("Aucune pièce définie")
            is_valid = False
            return (is_valid, messages)
        
        # Calculer les surfaces
        total_area_needed = sum(area for _, area in rooms)
        wall_thickness = self.solver_config.exterior_wall_thickness
        available_area = (width - 2 * wall_thickness) * (depth - 2 * wall_thickness)
        
        if total_area_needed > available_area:
            messages.append(
                f"Surface insuffisante: {total_area_needed:.1f}m² demandés, "
                f"{available_area:.1f}m² disponibles"
            )
            is_valid = False
        elif total_area_needed > available_area * 0.9:
            messages.append(
                f"Attention: surface serrée ({total_area_needed:.1f}m² / {available_area:.1f}m²)"
            )
        
        # Compter les pièces nécessitant fenêtre
        window_rooms = [r for r, _ in rooms if get_room_type(r) and get_room_type(r).requires_window]
        
        # Estimation grossière du périmètre extérieur disponible
        perimeter = 2 * (width + depth) - 4 * wall_thickness
        estimated_window_space = len(window_rooms) * 3.0  # ~3m par pièce avec fenêtre
        
        if estimated_window_space > perimeter:
            messages.append(
                f"Trop de pièces nécessitant fenêtre ({len(window_rooms)}) "
                f"pour le périmètre disponible"
            )
        
        return (is_valid, messages)
    
    def generate_layout(
        self,
        width: float,
        depth: float,
        preset_id: str,
        floor: int = 0
    ) -> BSPResult:
        """
        Méthode complète pour générer un layout.
        Combine set_building_dimensions, set_preset et generate.
        """
        self.set_building_dimensions(width, depth)
        
        if preset_id != 'CUSTOM':
            self.set_preset(preset_id)
        
        result = generate_floor_plan(
            width=width,
            depth=depth,
            preset_id=preset_id,
            custom_rooms=self._rooms_to_place if preset_id == 'CUSTOM' else None,
            floor=floor,
            config=self.solver_config
        )
        
        self._last_result = result
        if result.success:
            self.floor_plan = result.floor_plan
            
            # ✅ NOUVEAU: Calculer les fenêtres
            if HAS_WINDOW_PLACEMENT and self.floor_plan:
                self._calculate_window_positions()
        
        return result


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
    try:
        from . import bl_properties
        from . import bl_ui
        
        bl_properties.register()
        bl_ui.register()
    except ImportError:
        # Modules UI optionnels
        pass


def unregister():
    """Désenregistre l'addon de Blender."""
    try:
        from . import bl_ui
        from . import bl_properties
        
        bl_ui.unregister()
        bl_properties.unregister()
    except ImportError:
        pass


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
    
    # BSP Solver (nouveau)
    'BSPConfig',
    'BSPSolver',
    'BSPResult',
    'BSPNode',
    'SplitDirection',
    
    # Alias rétrocompatibilité
    'SolverConfig',
    'PlacementResult',
    'RoomPlacementSolver',
    'SimpleGridSolver',
    
    # Fonctions utilitaires
    'generate_floor_plan',
    'generate_interior_walls',
    'generate_doors_for_floor_plan',
    'generate_door_geometry',
    'get_partition_data_for_floor_plan',
    
    # ✅ NOUVEAU: Window Placement
    'ExteriorWall',
    'FreeSegment',
    'WindowPosition',
    'WindowPlacementConfig',
    'FreeSegmentCalculator',
    'WindowPlacementEngine',
    'calculate_window_positions',
    'convert_to_blender_format',
    'print_placement_summary',
    'HAS_WINDOW_PLACEMENT',
    
    # Manager
    'RoomLayoutManager',
    'RoomLayoutGenerator',  # Alias rétrocompatibilité
]
