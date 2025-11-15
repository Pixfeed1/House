"""
ENDUIT DÉCORATIF
=================
Enduit taloché, enduit ciré, enduit lissé.
Donne du relief ou un effet matière.

Types:
- TALOCHE: Relief prononcé, aspect rustique
- CIRE: Lisse et brillant, aspect ciré
- LISSE: Parfaitement plat, moderne

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase, PLASTER_THICKNESS

PLASTER_TYPES = {
    'TALOCHE': {'name': "Taloché", 'relief': 0.003, 'roughness': 0.9},
    'CIRE': {'name': "Ciré", 'relief': 0.001, 'roughness': 0.3},
    'LISSE': {'name': "Lissé", 'relief': 0.0005, 'roughness': 0.5}
}

class WallEnduit(WallFinishBase):
    """Finition enduit décoratif."""

    def __init__(self, width, height, plaster_type='LISSE',
                 color=(0.92, 0.90, 0.85, 1.0), name="WallEnduit"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type enduit
        if plaster_type not in PLASTER_TYPES:
            print(f"[WallEnduit] ⚠️ Type invalide '{plaster_type}', utilisation LISSE")
            plaster_type = 'LISSE'

        self.plaster_type = plaster_type
        self.color = color

        print(f"[WallEnduit] Type: {PLASTER_TYPES[plaster_type]['name']}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            relief_depth = PLASTER_TYPES[self.plaster_type]['relief']

            # Surface avec relief selon type
            self._create_relief_surface(
                bm, 0, 0, 0,
                self.width, self.height,
                relief_depth=relief_depth,
                pattern="random"
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallEnduit] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "ENDUIT"
            obj["plaster_type"] = self.plaster_type
            obj["color"] = self.color
            obj["relief_depth"] = relief_depth

            print(f"[WallEnduit] ✅ Enduit {PLASTER_TYPES[self.plaster_type]['name']} généré")
            return obj

        finally:
            bm.free()
