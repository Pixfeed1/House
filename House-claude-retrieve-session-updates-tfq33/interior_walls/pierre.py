"""
PIERRE NATURELLE
=================
Aspect naturel, irrégulier.
Travertin, ardoise, granit, etc.

Types:
- TRAVERTIN: Pierre calcaire beige/ivoire
- ARDOISE: Pierre noire/grise, aspect feuilleté
- GRANIT: Pierre dure, aspect granuleux
- CALCAIRE: Pierre claire, aspect lisse

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase, STONE_THICKNESS, DEFAULT_STONE_COLOR

STONE_TYPES = {
    'TRAVERTIN': {'name': "Travertin", 'color': (0.85, 0.80, 0.70, 1.0)},
    'ARDOISE': {'name': "Ardoise", 'color': (0.25, 0.25, 0.28, 1.0)},
    'GRANIT': {'name': "Granit", 'color': (0.50, 0.50, 0.52, 1.0)},
    'CALCAIRE': {'name': "Calcaire", 'color': (0.90, 0.88, 0.85, 1.0)}
}

class WallPierre(WallFinishBase):
    """Finition pierre naturelle."""

    def __init__(self, width, height, stone_type='CALCAIRE',
                 color=None, name="WallPierre"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type pierre
        if stone_type not in STONE_TYPES:
            print(f"[WallPierre] ⚠️ Type invalide '{stone_type}', utilisation CALCAIRE")
            stone_type = 'CALCAIRE'

        self.stone_type = stone_type

        # Utiliser couleur par défaut du type si non fournie
        self.color = color if color else STONE_TYPES[stone_type]['color']

        print(f"[WallPierre] Type: {STONE_TYPES[stone_type]['name']}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            # Surface avec relief léger (pierre irrégulière)
            self._create_relief_surface(
                bm, 0, 0, 0,
                self.width, self.height,
                relief_depth=STONE_THICKNESS,
                pattern="random"
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallPierre] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "PIERRE"
            obj["stone_type"] = self.stone_type
            obj["color"] = self.color

            print(f"[WallPierre] ✅ Pierre {STONE_TYPES[self.stone_type]['name']} générée")
            return obj

        finally:
            bm.free()
