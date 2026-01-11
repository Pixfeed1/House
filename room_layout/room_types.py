# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2024 mvaertan
"""
Définitions des types de pièces pour le système de distribution.

Chaque type de pièce définit :
- Surfaces (min, défaut, max) en m²
- Contrainte de lumière naturelle
- Priorité pour l'attribution des fenêtres
- Score d'adjacence avec les autres pièces
- Exigences pour les portes
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING
from enum import Enum, auto

if TYPE_CHECKING:
    from .base import DoorSwingDirection, DoorType


class RoomCategory(Enum):
    """Catégories de pièces pour le regroupement logique."""
    LIVING = auto()      # Pièces de vie (salon, cuisine)
    SLEEPING = auto()    # Chambres
    SERVICE = auto()     # Pièces de service (SDB, WC, cellier)
    CIRCULATION = auto() # Circulation (entrée, couloir)
    WORK = auto()        # Travail (bureau)


# =============================================================================
# EXIGENCES DE PORTES PAR TYPE DE PIÈCE
# =============================================================================

@dataclass
class DoorRequirements:
    """
    Exigences de porte pour un type de pièce.
    
    Ces règles sont utilisées par le DoorPlacementEngine pour
    déterminer automatiquement les caractéristiques des portes.
    """
    
    # Largeur préférée (None = utiliser défaut global)
    preferred_width: Optional[float] = None
    
    # Sens d'ouverture obligatoire
    # 'PUSH' = vers l'extérieur de la pièce (s'éloigne de room1)
    # 'PULL' = vers l'intérieur de la pièce (vers room1)
    # None = calculer automatiquement
    required_swing: Optional[str] = None
    
    # Serrure obligatoire
    requires_lock: bool = False
    
    # Types de portes autorisés (noms des DoorType)
    allowed_types: List[str] = field(default_factory=lambda: [
        'STANDARD', 'SLIDING', 'POCKET'
    ])
    
    # Nombre minimum de portes (accès)
    min_doors: int = 1
    
    # Porte coupe-feu obligatoire
    requires_fire_rating: bool = False
    
    # Largeur PMR obligatoire (0.90m)
    requires_accessible: bool = False
    
    # Description pour l'UI
    description: str = ""


# Exigences par type de pièce
DOOR_REQUIREMENTS: Dict[str, DoorRequirements] = {
    'WC': DoorRequirements(
        preferred_width=0.70,
        required_swing='PULL',  # S'ouvre vers l'extérieur du WC (sécurité: si qqn tombe)
        requires_lock=True,
        allowed_types=['STANDARD', 'POCKET'],
        description="Porte étroite avec verrou, ouverture vers l'extérieur"
    ),
    'SDB': DoorRequirements(
        preferred_width=0.70,
        requires_lock=True,
        allowed_types=['STANDARD', 'SLIDING', 'POCKET'],
        description="Porte avec verrou pour intimité"
    ),
    'CHAMBRE': DoorRequirements(
        preferred_width=0.83,
        required_swing='PUSH',  # S'ouvre vers l'intérieur de la chambre (intimité)
        requires_lock=True,
        description="Porte standard avec serrure pour intimité"
    ),
    'CHAMBRE_PARENTALE': DoorRequirements(
        preferred_width=0.83,
        required_swing='PUSH',
        requires_lock=True,
        description="Porte standard avec serrure"
    ),
    'DRESSING': DoorRequirements(
        preferred_width=0.73,
        requires_lock=False,
        allowed_types=['STANDARD', 'SLIDING', 'POCKET'],
        description="Porte coulissante idéale pour gagner de l'espace"
    ),
    'CELLIER': DoorRequirements(
        preferred_width=0.73,
        requires_lock=False,
        description="Porte simple"
    ),
    'BUANDERIE': DoorRequirements(
        preferred_width=0.73,
        requires_lock=False,
        description="Porte simple"
    ),
    'BUREAU': DoorRequirements(
        preferred_width=0.83,
        requires_lock=True,
        description="Porte avec serrure optionnelle pour concentration"
    ),
    'SALON': DoorRequirements(
        preferred_width=0.83,
        requires_lock=False,
        allowed_types=['STANDARD', 'DOUBLE', 'SLIDING'],
        description="Porte large ou double possible"
    ),
    'CUISINE': DoorRequirements(
        preferred_width=0.83,
        requires_lock=False,
        allowed_types=['STANDARD', 'SLIDING', 'POCKET'],
        description="Porte standard ou coulissante"
    ),
    'SALLE_A_MANGER': DoorRequirements(
        preferred_width=0.83,
        requires_lock=False,
        allowed_types=['STANDARD', 'DOUBLE'],
        description="Porte standard ou double"
    ),
    'ENTREE': DoorRequirements(
        preferred_width=0.90,
        min_doors=1,  # Au moins la porte d'entrée
        requires_lock=True,
        requires_accessible=True,
        description="Porte d'entrée PMR avec serrure"
    ),
    'COULOIR': DoorRequirements(
        preferred_width=0.83,
        requires_lock=False,
        min_doors=0,  # Un couloir peut ne pas avoir de porte propre
        description="Portes de distribution"
    ),
    'GARAGE': DoorRequirements(
        preferred_width=0.83,
        requires_lock=True,
        requires_fire_rating=True,  # Porte coupe-feu garage -> maison
        description="Porte coupe-feu vers l'habitation"
    ),
}


def get_door_requirements(room_type_id: str) -> DoorRequirements:
    """Retourne les exigences de porte pour un type de pièce."""
    return DOOR_REQUIREMENTS.get(room_type_id, DoorRequirements())


# =============================================================================
# DÉFINITION DES TYPES DE PIÈCES
# =============================================================================

@dataclass
class RoomTypeDefinition:
    """Définition complète d'un type de pièce."""

    # Identification
    id: str                          # Identifiant unique (ex: 'SALON', 'CHAMBRE')
    name: str                        # Nom affiché (ex: 'Salon', 'Chambre')
    name_plural: str                 # Nom pluriel (ex: 'Salons', 'Chambres')
    icon: str                        # Icône Blender (ex: 'HOME', 'CON_FLOOR')
    category: RoomCategory

    # Surfaces en m² (standards français RT2012 / logement décent)
    area_min: float                  # Surface minimum viable
    area_default: float              # Surface standard recommandée
    area_max: float                  # Surface maximum raisonnable

    # Contraintes de lumière
    requires_window: bool            # DOIT avoir une fenêtre (pièces de vie)
    prefers_window: bool             # Préfère avoir une fenêtre
    window_priority: int             # 1 = priorité max, 10 = priorité min

    # Contraintes de forme
    min_width: float = 2.0           # Largeur minimum en m
    max_aspect_ratio: float = 3.0    # Ratio longueur/largeur max

    # Adjacences (scores: +3 très souhaité, +1 souhaité, -2 éviter, -10 interdit)
    adjacency_scores: Dict[str, int] = field(default_factory=dict)

    # Étage préféré (None = tous, 0 = RDC, 1+ = étages)
    preferred_floors: Optional[List[int]] = None

    # Peut être fusionné avec une autre pièce (ex: cuisine ouverte)
    can_merge_with: List[str] = field(default_factory=list)

    def get_adjacency_score(self, other_room_id: str) -> int:
        """Retourne le score d'adjacence avec un autre type de pièce."""
        return self.adjacency_scores.get(other_room_id, 0)

    def validate_area(self, area: float) -> tuple[bool, str]:
        """Valide une surface proposée. Retourne (ok, message)."""
        if area < self.area_min * 0.8:
            return False, f"Surface trop petite (min: {self.area_min}m²)"
        if area < self.area_min:
            return True, f"Surface en dessous du standard (recommandé: {self.area_min}m²)"
        if area > self.area_max:
            return True, f"Surface très grande (max habituel: {self.area_max}m²)"
        return True, ""
    
    @property
    def door_requirements(self) -> DoorRequirements:
        """Retourne les exigences de porte pour ce type de pièce."""
        return get_door_requirements(self.id)


# =============================================================================
# DÉFINITIONS DES TYPES DE PIÈCES
# =============================================================================

ROOM_TYPES: Dict[str, RoomTypeDefinition] = {}

def _register_room_type(room_type: RoomTypeDefinition) -> None:
    """Enregistre un type de pièce dans le dictionnaire global."""
    ROOM_TYPES[room_type.id] = room_type


# -----------------------------------------------------------------------------
# PIÈCES DE VIE
# -----------------------------------------------------------------------------

_register_room_type(RoomTypeDefinition(
    id='SALON',
    name='Salon',
    name_plural='Salons',
    icon='HOME',
    category=RoomCategory.LIVING,
    area_min=12.0,
    area_default=20.0,
    area_max=50.0,
    requires_window=True,
    prefers_window=True,
    window_priority=1,
    min_width=3.0,
    adjacency_scores={
        'ENTREE': 3,      # Entrée doit donner sur salon
        'CUISINE': 3,     # Cuisine adjacente ou ouverte
        'TERRASSE': 2,    # Accès terrasse apprécié
        'WC': -2,         # WC pas directement visible
    },
    preferred_floors=[0],  # RDC préféré
    can_merge_with=['CUISINE', 'SALLE_A_MANGER'],
))

_register_room_type(RoomTypeDefinition(
    id='CUISINE',
    name='Cuisine',
    name_plural='Cuisines',
    icon='OUTLINER_OB_LIGHTPROBE',
    category=RoomCategory.LIVING,
    area_min=5.0,
    area_default=10.0,
    area_max=25.0,
    requires_window=False,  # Peut être ouverte sur salon
    prefers_window=True,
    window_priority=3,
    min_width=2.0,
    adjacency_scores={
        'SALON': 3,
        'SALLE_A_MANGER': 3,
        'CELLIER': 2,
        'WC': -2,         # Hygiène
    },
    preferred_floors=[0],
    can_merge_with=['SALON', 'SALLE_A_MANGER'],
))

_register_room_type(RoomTypeDefinition(
    id='SALLE_A_MANGER',
    name='Salle à manger',
    name_plural='Salles à manger',
    icon='OUTLINER_OB_LATTICE',
    category=RoomCategory.LIVING,
    area_min=8.0,
    area_default=14.0,
    area_max=30.0,
    requires_window=True,
    prefers_window=True,
    window_priority=2,
    min_width=2.5,
    adjacency_scores={
        'CUISINE': 3,
        'SALON': 2,
        'TERRASSE': 2,
    },
    preferred_floors=[0],
    can_merge_with=['SALON', 'CUISINE'],
))


# -----------------------------------------------------------------------------
# CHAMBRES
# -----------------------------------------------------------------------------

_register_room_type(RoomTypeDefinition(
    id='CHAMBRE',
    name='Chambre',
    name_plural='Chambres',
    icon='CON_FLOOR',
    category=RoomCategory.SLEEPING,
    area_min=9.0,          # Norme logement décent
    area_default=12.0,
    area_max=25.0,
    requires_window=True,  # Obligatoire légalement
    prefers_window=True,
    window_priority=2,
    min_width=2.5,
    adjacency_scores={
        'SDB': 1,
        'DRESSING': 2,
        'COULOIR': 1,
        'ENTREE': -2,      # Pas d'accès direct depuis entrée
        'CUISINE': -1,
    },
    preferred_floors=None,  # Tous étages OK
))

_register_room_type(RoomTypeDefinition(
    id='CHAMBRE_PARENTALE',
    name='Chambre parentale',
    name_plural='Chambres parentales',
    icon='CON_FLOOR',
    category=RoomCategory.SLEEPING,
    area_min=12.0,
    area_default=16.0,
    area_max=35.0,
    requires_window=True,
    prefers_window=True,
    window_priority=2,
    min_width=3.0,
    adjacency_scores={
        'SDB': 2,          # SDB privative appréciée
        'DRESSING': 3,     # Dressing attenant
        'COULOIR': 1,
        'ENTREE': -2,
    },
    preferred_floors=None,
))


# -----------------------------------------------------------------------------
# PIÈCES DE SERVICE
# -----------------------------------------------------------------------------

_register_room_type(RoomTypeDefinition(
    id='SDB',
    name='Salle de bain',
    name_plural='Salles de bain',
    icon='MATFLUID',
    category=RoomCategory.SERVICE,
    area_min=3.0,
    area_default=6.0,
    area_max=15.0,
    requires_window=False,  # VMC obligatoire si aveugle
    prefers_window=True,
    window_priority=5,
    min_width=1.5,
    max_aspect_ratio=2.5,
    adjacency_scores={
        'CHAMBRE': 1,
        'CHAMBRE_PARENTALE': 2,
        'COULOIR': 1,
    },
    preferred_floors=None,
))

_register_room_type(RoomTypeDefinition(
    id='WC',
    name='WC',
    name_plural='WC',
    icon='EVENT_W',
    category=RoomCategory.SERVICE,
    area_min=1.0,
    area_default=1.5,
    area_max=4.0,
    requires_window=False,
    prefers_window=False,
    window_priority=6,
    min_width=0.9,
    max_aspect_ratio=2.0,
    adjacency_scores={
        'ENTREE': 1,
        'COULOIR': 1,
        'CUISINE': -2,     # Hygiène
        'SALON': -2,       # Pas visible depuis salon
        'SALLE_A_MANGER': -2,
    },
    preferred_floors=None,
))

_register_room_type(RoomTypeDefinition(
    id='CELLIER',
    name='Cellier',
    name_plural='Celliers',
    icon='PACKAGE',
    category=RoomCategory.SERVICE,
    area_min=2.0,
    area_default=4.0,
    area_max=10.0,
    requires_window=False,
    prefers_window=False,
    window_priority=7,
    min_width=1.2,
    adjacency_scores={
        'CUISINE': 2,
        'GARAGE': 1,
    },
    preferred_floors=[0],
))

_register_room_type(RoomTypeDefinition(
    id='BUANDERIE',
    name='Buanderie',
    name_plural='Buanderies',
    icon='MOD_WAVE',
    category=RoomCategory.SERVICE,
    area_min=3.0,
    area_default=5.0,
    area_max=10.0,
    requires_window=False,
    prefers_window=True,
    window_priority=6,
    min_width=1.5,
    adjacency_scores={
        'CUISINE': 1,
        'CELLIER': 1,
        'SDB': 1,
    },
    preferred_floors=[0],
))

_register_room_type(RoomTypeDefinition(
    id='DRESSING',
    name='Dressing',
    name_plural='Dressings',
    icon='ASSET_MANAGER',
    category=RoomCategory.SERVICE,
    area_min=3.0,
    area_default=6.0,
    area_max=15.0,
    requires_window=False,
    prefers_window=False,
    window_priority=8,
    min_width=1.5,
    adjacency_scores={
        'CHAMBRE_PARENTALE': 3,
        'CHAMBRE': 2,
    },
    preferred_floors=None,
))

_register_room_type(RoomTypeDefinition(
    id='GARAGE',
    name='Garage',
    name_plural='Garages',
    icon='AUTO',
    category=RoomCategory.SERVICE,
    area_min=12.0,
    area_default=18.0,
    area_max=50.0,
    requires_window=False,
    prefers_window=False,
    window_priority=10,
    min_width=2.5,
    max_aspect_ratio=4.0,
    adjacency_scores={
        'CELLIER': 1,
        'ENTREE': 1,
    },
    preferred_floors=[0],
))


# -----------------------------------------------------------------------------
# CIRCULATION
# -----------------------------------------------------------------------------

_register_room_type(RoomTypeDefinition(
    id='ENTREE',
    name='Entrée',
    name_plural='Entrées',
    icon='IMPORT',
    category=RoomCategory.CIRCULATION,
    area_min=2.0,
    area_default=5.0,
    area_max=12.0,
    requires_window=False,
    prefers_window=True,
    window_priority=5,
    min_width=1.2,
    adjacency_scores={
        'SALON': 3,
        'COULOIR': 2,
        'WC': 1,
        'GARAGE': 1,
    },
    preferred_floors=[0],
))

_register_room_type(RoomTypeDefinition(
    id='COULOIR',
    name='Couloir',
    name_plural='Couloirs',
    icon='TRACKING_FORWARDS_SINGLE',
    category=RoomCategory.CIRCULATION,
    area_min=2.0,
    area_default=5.0,
    area_max=15.0,
    requires_window=False,
    prefers_window=False,
    window_priority=7,
    min_width=0.9,          # Norme accessibilité PMR
    max_aspect_ratio=10.0,  # Peut être très allongé
    adjacency_scores={
        # Le couloir peut être adjacent à tout
    },
    preferred_floors=None,
))


# -----------------------------------------------------------------------------
# TRAVAIL
# -----------------------------------------------------------------------------

_register_room_type(RoomTypeDefinition(
    id='BUREAU',
    name='Bureau',
    name_plural='Bureaux',
    icon='DESKTOP',
    category=RoomCategory.WORK,
    area_min=6.0,
    area_default=10.0,
    area_max=20.0,
    requires_window=False,
    prefers_window=True,
    window_priority=4,
    min_width=2.0,
    adjacency_scores={
        'COULOIR': 1,
        'SALON': 0,        # Neutre
        'CHAMBRE': -1,     # Séparation vie/travail
    },
    preferred_floors=None,
))


# =============================================================================
# PRESETS DE LOGEMENTS (T1 à T6+)
# =============================================================================

@dataclass
class HousingPreset:
    """Configuration prédéfinie pour un type de logement."""

    id: str                          # Ex: 'T3'
    name: str                        # Ex: 'T3 - 2 chambres'
    description: str

    # Liste des pièces (room_type_id, quantité, surface_override optionnelle)
    rooms: List[tuple[str, int, Optional[float]]]

    # Surface totale recommandée
    area_recommended: float
    area_min: float

    def get_rooms_list(self) -> List[tuple[str, float]]:
        """Retourne la liste étendue (room_id, surface) pour chaque pièce."""
        result = []
        for room_id, count, area_override in self.rooms:
            room_def = ROOM_TYPES.get(room_id)
            if room_def:
                area = area_override if area_override else room_def.area_default
                for i in range(count):
                    result.append((room_id, area))
        return result


HOUSING_PRESETS: Dict[str, HousingPreset] = {
    'T1': HousingPreset(
        id='T1',
        name='T1 - Studio',
        description='Pièce principale + salle de bain',
        rooms=[
            ('SALON', 1, 25.0),   # Salon/chambre combiné
            ('CUISINE', 1, 6.0),  # Kitchenette
            ('SDB', 1, 4.0),
        ],
        area_recommended=30.0,
        area_min=20.0,
    ),

    'T2': HousingPreset(
        id='T2',
        name='T2 - 1 chambre',
        description='Salon + cuisine + 1 chambre + SDB',
        rooms=[
            ('SALON', 1, 18.0),
            ('CUISINE', 1, 8.0),
            ('CHAMBRE', 1, 10.0),
            ('SDB', 1, 4.0),
        ],
        area_recommended=45.0,
        area_min=35.0,
    ),

    'T3': HousingPreset(
        id='T3',
        name='T3 - 2 chambres',
        description='Salon + cuisine + 2 chambres + SDB',
        rooms=[
            ('SALON', 1, 22.0),
            ('CUISINE', 1, 10.0),
            ('CHAMBRE', 2, 11.0),
            ('SDB', 1, 5.0),
            ('WC', 1, 1.5),
        ],
        area_recommended=70.0,
        area_min=55.0,
    ),

    'T4': HousingPreset(
        id='T4',
        name='T4 - 3 chambres',
        description='Salon + cuisine + 3 chambres + SDB + WC',
        rooms=[
            ('SALON', 1, 25.0),
            ('CUISINE', 1, 12.0),
            ('CHAMBRE_PARENTALE', 1, 14.0),
            ('CHAMBRE', 2, 11.0),
            ('SDB', 1, 6.0),
            ('WC', 1, 1.5),
            ('ENTREE', 1, 4.0),
        ],
        area_recommended=95.0,
        area_min=75.0,
    ),

    'T5': HousingPreset(
        id='T5',
        name='T5 - 4 chambres',
        description='Salon + cuisine + 4 chambres + 2 SDB',
        rooms=[
            ('SALON', 1, 30.0),
            ('CUISINE', 1, 14.0),
            ('CHAMBRE_PARENTALE', 1, 16.0),
            ('CHAMBRE', 3, 11.0),
            ('SDB', 2, 5.0),
            ('WC', 1, 2.0),
            ('ENTREE', 1, 5.0),
            ('COULOIR', 1, 6.0),
        ],
        area_recommended=120.0,
        area_min=100.0,
    ),

    'T6': HousingPreset(
        id='T6',
        name='T6 - 5 chambres',
        description='Salon + cuisine + 5 chambres + 2 SDB + bureau',
        rooms=[
            ('SALON', 1, 35.0),
            ('CUISINE', 1, 16.0),
            ('CHAMBRE_PARENTALE', 1, 18.0),
            ('CHAMBRE', 4, 12.0),
            ('SDB', 2, 6.0),
            ('WC', 2, 1.5),
            ('BUREAU', 1, 10.0),
            ('ENTREE', 1, 6.0),
            ('COULOIR', 1, 8.0),
        ],
        area_recommended=160.0,
        area_min=130.0,
    ),
}


# =============================================================================
# CONSTANTES DE CIRCULATION
# =============================================================================

class CorridorSettings:
    """Paramètres pour les couloirs."""

    WIDTH_MIN = 0.90       # Norme accessibilité PMR
    WIDTH_DEFAULT = 1.00   # Confort standard
    WIDTH_MAX = 1.20       # Au-delà = gaspillage

    # Seuils de surface pour déterminer la nécessité d'un couloir
    THRESHOLD_NO_CORRIDOR = 50.0      # Pas de couloir en dessous
    THRESHOLD_SIMPLE_CORRIDOR = 100.0 # Couloir simple
    THRESHOLD_COMPLEX_CORRIDOR = 150.0 # Couloir en T ou L possible


class StaircaseSettings:
    """Paramètres pour les escaliers (réservation d'espace)."""

    # Escalier droit
    STRAIGHT_LENGTH = 3.5   # Longueur en m
    STRAIGHT_WIDTH = 1.0    # Largeur en m

    # Escalier tournant (quart ou demi)
    TURNING_LENGTH = 2.5
    TURNING_WIDTH = 2.0

    # Trémie (trou dans le plancher)
    HOLE_MARGIN = 0.10      # Marge autour de l'escalier

    # Position préférée
    NEAR_ENTRANCE = True
    AGAINST_WALL = True


# =============================================================================
# UTILITAIRES
# =============================================================================

def get_room_type(room_id: str) -> Optional[RoomTypeDefinition]:
    """Récupère la définition d'un type de pièce."""
    return ROOM_TYPES.get(room_id)


def get_rooms_requiring_windows() -> List[str]:
    """Retourne la liste des IDs des pièces nécessitant une fenêtre."""
    return [room_id for room_id, room_def in ROOM_TYPES.items()
            if room_def.requires_window]


def get_rooms_by_category(category: RoomCategory) -> List[RoomTypeDefinition]:
    """Retourne les types de pièces d'une catégorie."""
    return [room_def for room_def in ROOM_TYPES.values()
            if room_def.category == category]


def calculate_adjacency_score(room1_id: str, room2_id: str) -> int:
    """Calcule le score d'adjacence entre deux pièces (bidirectionnel)."""
    room1 = ROOM_TYPES.get(room1_id)
    room2 = ROOM_TYPES.get(room2_id)

    if not room1 or not room2:
        return 0

    # Score combiné des deux directions
    score1 = room1.get_adjacency_score(room2_id)
    score2 = room2.get_adjacency_score(room1_id)

    return score1 + score2


def get_enum_items_for_blender() -> list:
    """Génère les items pour un EnumProperty Blender."""
    items = []
    for room_id, room_def in ROOM_TYPES.items():
        items.append((
            room_id,
            room_def.name,
            f"{room_def.name} ({room_def.area_default}m² par défaut)",
            room_def.icon,
            len(items)
        ))
    return items


def get_preset_enum_items_for_blender() -> list:
    """Génère les items de presets pour un EnumProperty Blender."""
    items = [('CUSTOM', 'Personnalisé', 'Configuration manuelle des pièces', 'MODIFIER', 0)]
    for i, (preset_id, preset) in enumerate(HOUSING_PRESETS.items(), start=1):
        items.append((
            preset_id,
            preset.name,
            preset.description,
            'HOME',
            i
        ))
    return items
