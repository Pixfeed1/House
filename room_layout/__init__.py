# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Module room_layout - Distribution intelligente des pièces.

Ce module fournit un système complet de génération de plans d'étage :
- Définitions des types de pièces (surfaces, contraintes, adjacences)
- Presets de logements (T1 à T6)
- Algorithme de placement par contraintes
- Génération de géométrie pour Blender

Usage basique:
    from room_layout import RoomLayoutManager, HOUSING_PRESETS

    manager = RoomLayoutManager()
    result = manager.generate_layout(
        width=10.0,
        depth=12.0,
        preset_id='T3'
    )

    if result.success:
        manager.build_geometry(result.floor_plan)

Usage avancé:
    from room_layout import (
        RoomPlacementSolver,
        SolverConfig,
        ROOM_TYPES,
        generate_floor_plan
    )

    config = SolverConfig(wall_thickness=0.12)
    result = generate_floor_plan(10.0, 12.0, 'T4', config=config)
"""

# Imports des sous-modules
from .room_types import (
    # Classes
    RoomTypeDefinition,
    RoomCategory,
    HousingPreset,
    CorridorSettings,
    StaircaseSettings,

    # Dictionnaires
    ROOM_TYPES,
    HOUSING_PRESETS,

    # Fonctions utilitaires
    get_room_type,
    get_rooms_requiring_windows,
    get_rooms_by_category,
    calculate_adjacency_score,
    get_enum_items_for_blender,
    get_preset_enum_items_for_blender,
)

from .base import (
    # Classes géométriques
    Rectangle,
    WallSide,

    # Classes de données
    Room,
    FloorPlan,
    HousePlan,
    WindowOpening,
    DoorOpening,
)

from .solver import (
    # Classes
    SolverConfig,
    PlacementStrategy,
    PlacementResult,
    RoomPlacementSolver,

    # Fonctions
    generate_floor_plan,
)

from .geometry import (
    # Classes
    GeometryConfig,
    WallSegment,
    WallGeometryGenerator,

    # Fonctions
    get_partition_data_for_floor_plan,
)

# Import conditionnel pour Blender
try:
    import bpy
    from .geometry import (
        BlenderWallBuilder,
        RoomMarkerBuilder,
        generate_interior_walls,
    )
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False


# =============================================================================
# MANAGER PRINCIPAL
# =============================================================================

class RoomLayoutManager:
    """
    Interface principale pour la génération de plans d'étage.

    Cette classe encapsule toute la logique et fournit une API simple
    pour l'intégration avec le reste de l'addon.
    """

    def __init__(
        self,
        solver_config: SolverConfig = None,
        geometry_config: GeometryConfig = None
    ):
        """
        Initialise le manager.

        Args:
            solver_config: Configuration du solver (optionnel)
            geometry_config: Configuration de géométrie (optionnel)
        """
        self.solver_config = solver_config or SolverConfig()
        self.geometry_config = geometry_config or GeometryConfig()
        self._last_result: PlacementResult = None

    # -------------------------------------------------------------------------
    # GÉNÉRATION DE PLANS
    # -------------------------------------------------------------------------

    def generate_layout(
        self,
        width: float,
        depth: float,
        preset_id: str = 'T3',
        custom_rooms: list = None,
        floor: int = 0,
        staircase_position: str = None  # 'NONE', 'CORNER', 'SIDE'
    ) -> PlacementResult:
        """
        Génère un plan d'étage.

        Args:
            width: Largeur du bâtiment (m)
            depth: Profondeur du bâtiment (m)
            preset_id: ID du preset ('T1'-'T6' ou 'CUSTOM')
            custom_rooms: Liste de (room_type_id, target_area) si preset_id='CUSTOM'
            floor: Numéro d'étage (0 = RDC)
            staircase_position: Position de l'escalier (pour étages > 0)

        Returns:
            PlacementResult avec le plan généré ou les erreurs
        """
        # Déterminer les pièces à placer
        if preset_id == 'CUSTOM':
            if not custom_rooms:
                return PlacementResult(
                    success=False,
                    floor_plan=None,
                    messages=["Mode personnalisé sans liste de pièces"]
                )
            rooms_to_place = custom_rooms
        elif preset_id in HOUSING_PRESETS:
            preset = HOUSING_PRESETS[preset_id]
            rooms_to_place = preset.get_rooms_list()
        else:
            return PlacementResult(
                success=False,
                floor_plan=None,
                messages=[f"Preset inconnu: {preset_id}"]
            )

        # Créer les bounds
        bounds = Rectangle(0, 0, width, depth)

        # Calculer la zone d'escalier si nécessaire
        staircase_bounds = None
        if floor > 0 or staircase_position:
            staircase_bounds = self._calculate_staircase_bounds(
                bounds, staircase_position or 'CORNER'
            )

        # Lancer le solver
        solver = RoomPlacementSolver(self.solver_config)
        result = solver.solve(
            building_bounds=bounds,
            rooms_to_place=rooms_to_place,
            floor=floor,
            staircase_bounds=staircase_bounds
        )

        self._last_result = result
        return result

    def generate_multi_floor(
        self,
        width: float,
        depth: float,
        floors_config: list,  # Liste de (preset_id, custom_rooms)
        floor_height: float = 2.50
    ) -> HousePlan:
        """
        Génère un plan multi-étages.

        Args:
            width: Largeur du bâtiment
            depth: Profondeur du bâtiment
            floors_config: Configuration par étage
            floor_height: Hauteur sous plafond

        Returns:
            HousePlan complet
        """
        house = HousePlan(
            width=width,
            depth=depth,
            floor_height=floor_height
        )

        for floor_num, (preset_id, custom_rooms) in enumerate(floors_config):
            result = self.generate_layout(
                width=width,
                depth=depth,
                preset_id=preset_id,
                custom_rooms=custom_rooms,
                floor=floor_num,
                staircase_position='CORNER' if floor_num > 0 else None
            )

            if result.success and result.floor_plan:
                house.floors.append(result.floor_plan)

        return house

    # -------------------------------------------------------------------------
    # GÉNÉRATION DE GÉOMÉTRIE BLENDER
    # -------------------------------------------------------------------------

    def build_geometry(
        self,
        floor_plan: FloorPlan,
        collection_name: str = "Interior_Walls",
        floor_z: float = 0.0,
        create_markers: bool = False
    ) -> dict:
        """
        Construit la géométrie Blender pour un plan.

        Args:
            floor_plan: Plan d'étage à construire
            collection_name: Nom de la collection Blender
            floor_z: Hauteur Z du plancher
            create_markers: Créer des marqueurs de pièces (debug)

        Returns:
            Dict avec les objets créés
        """
        if not HAS_BLENDER:
            raise RuntimeError("Blender n'est pas disponible")

        return generate_interior_walls(
            floor_plan=floor_plan,
            collection_name=collection_name,
            floor_z=floor_z,
            config=self.geometry_config
        )

    def get_partition_data(self, floor_plan: FloorPlan = None) -> list:
        """
        Retourne les données des cloisons pour l'intégration avec l'ancien système.

        Args:
            floor_plan: Plan à utiliser (ou dernier plan généré)

        Returns:
            Liste de dicts compatibles avec operators_auto.py
        """
        plan = floor_plan or (self._last_result.floor_plan if self._last_result else None)

        if not plan:
            return []

        return get_partition_data_for_floor_plan(plan)

    # -------------------------------------------------------------------------
    # UTILITAIRES
    # -------------------------------------------------------------------------

    def _calculate_staircase_bounds(
        self,
        building: Rectangle,
        position: str
    ) -> Rectangle:
        """Calcule la zone de réservation pour l'escalier."""

        stair_w = StaircaseSettings.TURNING_WIDTH
        stair_d = StaircaseSettings.TURNING_LENGTH
        margin = self.solver_config.exterior_wall_thickness

        if position == 'CORNER':
            # Coin sud-ouest par défaut
            return Rectangle(
                margin + 0.2,
                margin + 0.2,
                stair_w,
                stair_d
            )
        elif position == 'SIDE':
            # Centré sur le mur ouest
            return Rectangle(
                margin + 0.2,
                (building.depth - stair_d) / 2,
                stair_w,
                stair_d
            )
        else:
            # Centré
            return Rectangle(
                (building.width - stair_w) / 2,
                (building.depth - stair_d) / 2,
                stair_w,
                stair_d
            )

    @staticmethod
    def get_available_presets() -> list:
        """Retourne la liste des presets disponibles."""
        return list(HOUSING_PRESETS.keys())

    @staticmethod
    def get_preset_info(preset_id: str) -> dict:
        """Retourne les informations sur un preset."""
        if preset_id not in HOUSING_PRESETS:
            return None

        preset = HOUSING_PRESETS[preset_id]
        return {
            'id': preset.id,
            'name': preset.name,
            'description': preset.description,
            'area_recommended': preset.area_recommended,
            'area_min': preset.area_min,
            'rooms': [
                {
                    'type': room_id,
                    'count': count,
                    'area': area or ROOM_TYPES[room_id].area_default
                }
                for room_id, count, area in preset.rooms
            ]
        }

    @staticmethod
    def get_room_type_info(room_type_id: str) -> dict:
        """Retourne les informations sur un type de pièce."""
        room_type = get_room_type(room_type_id)
        if not room_type:
            return None

        return {
            'id': room_type.id,
            'name': room_type.name,
            'area_min': room_type.area_min,
            'area_default': room_type.area_default,
            'area_max': room_type.area_max,
            'requires_window': room_type.requires_window,
            'category': room_type.category.name
        }

    @staticmethod
    def validate_configuration(
        width: float,
        depth: float,
        preset_id: str = None,
        custom_rooms: list = None
    ) -> tuple:
        """
        Valide une configuration avant génération.

        Returns:
            Tuple (is_valid, list_of_messages)
        """
        messages = []

        # Vérifier les dimensions
        if width < 4.0 or depth < 4.0:
            messages.append("Dimensions trop petites (minimum 4m × 4m)")
            return False, messages

        total_area = width * depth

        # Vérifier le preset
        if preset_id and preset_id != 'CUSTOM':
            if preset_id not in HOUSING_PRESETS:
                messages.append(f"Preset inconnu: {preset_id}")
                return False, messages

            preset = HOUSING_PRESETS[preset_id]
            if total_area < preset.area_min:
                messages.append(
                    f"Surface insuffisante pour {preset.name} "
                    f"(min: {preset.area_min}m², disponible: {total_area:.1f}m²)"
                )
                return False, messages

            if total_area < preset.area_recommended:
                messages.append(
                    f"Surface en dessous de la recommandation pour {preset.name} "
                    f"(recommandé: {preset.area_recommended}m²)"
                )

        # Vérifier les pièces personnalisées
        if custom_rooms:
            total_requested = sum(area for _, area in custom_rooms)
            if total_requested > total_area * 0.9:
                messages.append(
                    f"Surface demandée ({total_requested:.1f}m²) proche de "
                    f"la surface disponible ({total_area:.1f}m²)"
                )

            for room_type_id, area in custom_rooms:
                if room_type_id not in ROOM_TYPES:
                    messages.append(f"Type de pièce inconnu: {room_type_id}")
                    return False, messages

                room_type = ROOM_TYPES[room_type_id]
                if area < room_type.area_min:
                    messages.append(
                        f"{room_type.name}: surface demandée ({area}m²) "
                        f"inférieure au minimum ({room_type.area_min}m²)"
                    )

        is_valid = not any("insuffisante" in m or "inconnu" in m for m in messages)
        return is_valid, messages


# =============================================================================
# COMPATIBILITÉ AVEC L'ANCIEN SYSTÈME
# =============================================================================

class RoomLayoutGenerator:
    """
    Classe de compatibilité pour l'ancien système.
    Redirige vers RoomLayoutManager.
    """

    def __init__(self):
        self._manager = RoomLayoutManager()

    def generate(
        self,
        house_width: float,
        house_depth: float,
        num_rooms: int = 4,
        floor_height: float = 2.5,
        wall_thickness: float = 0.1,
        **kwargs
    ) -> dict:
        """
        Interface de compatibilité avec l'ancien système.

        Args:
            house_width: Largeur de la maison
            house_depth: Profondeur de la maison
            num_rooms: Nombre de pièces (utilisé pour choisir le preset)
            floor_height: Hauteur sous plafond
            wall_thickness: Épaisseur des cloisons

        Returns:
            Dict avec 'rooms' et 'partitions' pour compatibilité
        """
        # Mapper num_rooms vers un preset
        preset_map = {
            1: 'T1',
            2: 'T1',
            3: 'T2',
            4: 'T3',
            5: 'T3',
            6: 'T4',
            7: 'T4',
            8: 'T5',
            9: 'T5',
            10: 'T6',
        }
        preset_id = preset_map.get(num_rooms, 'T3')

        # Configurer le solver
        from .solver import SolverConfig
        config = SolverConfig(
            wall_thickness=wall_thickness,
        )
        self._manager.solver_config = config

        # Générer le layout
        result = self._manager.generate_layout(
            width=house_width,
            depth=house_depth,
            preset_id=preset_id
        )

        if not result.success or not result.floor_plan:
            return {'rooms': [], 'partitions': []}

        # Convertir vers l'ancien format
        rooms = []
        for room in result.floor_plan.placed_rooms:
            if room.bounds:
                rooms.append({
                    'name': room.name,
                    'type': room.room_type_id,
                    'x': room.bounds.x,
                    'y': room.bounds.y,
                    'width': room.bounds.width,
                    'depth': room.bounds.depth,
                    'area': room.area,
                })

        partitions = self._manager.get_partition_data(result.floor_plan)

        return {
            'rooms': rooms,
            'partitions': partitions,
            'floor_plan': result.floor_plan,  # Nouveau: accès direct au plan
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Compatibilité ancien système
    'RoomLayoutGenerator',

    # Manager principal
    'RoomLayoutManager',

    # Types de pièces
    'ROOM_TYPES',
    'HOUSING_PRESETS',
    'RoomTypeDefinition',
    'RoomCategory',
    'HousingPreset',

    # Géométrie de base
    'Rectangle',
    'WallSide',
    'Room',
    'FloorPlan',
    'HousePlan',

    # Solver
    'RoomPlacementSolver',
    'SolverConfig',
    'PlacementStrategy',
    'PlacementResult',
    'generate_floor_plan',

    # Géométrie Blender
    'GeometryConfig',
    'WallSegment',
    'WallGeometryGenerator',
    'get_partition_data_for_floor_plan',

    # Fonctions utilitaires
    'get_room_type',
    'get_rooms_requiring_windows',
    'calculate_adjacency_score',
    'get_enum_items_for_blender',
    'get_preset_enum_items_for_blender',
]

# Exports conditionnels Blender
if HAS_BLENDER:
    __all__.extend([
        'BlenderWallBuilder',
        'RoomMarkerBuilder',
        'generate_interior_walls',
    ])
