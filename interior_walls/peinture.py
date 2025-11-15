"""
PEINTURE MURALE
================
Mat, satinée, brillante, velours.
Lessivable ou non selon la pièce.

Types:
- MAT: Absorption lumière, cache imperfections
- SATINEE: Légère brillance, lessivable
- BRILLANTE: Brillance élevée, très lessivable
- VELOURS: Aspect velouté, élégant

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase, PAINT_THICKNESS

# Types de peinture
PAINT_TYPES = {
    'MAT': {'roughness': 1.0, 'metallic': 0.0, 'name': "Mat"},
    'SATINEE': {'roughness': 0.6, 'metallic': 0.0, 'name': "Satinée"},
    'BRILLANTE': {'roughness': 0.2, 'metallic': 0.0, 'name': "Brillante"},
    'VELOURS': {'roughness': 0.8, 'metallic': 0.0, 'name': "Velours"}
}

class WallPeinture(WallFinishBase):
    """Finition peinture murale."""

    def __init__(self, width, height, paint_type='SATINEE', color=(0.95, 0.95, 0.95, 1.0), name="WallPeinture"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type peinture
        if paint_type not in PAINT_TYPES:
            print(f"[WallPeinture] ⚠️ Type invalide '{paint_type}', utilisation SATINEE")
            paint_type = 'SATINEE'

        self.paint_type = paint_type
        self.color = color

        print(f"[WallPeinture] Type: {PAINT_TYPES[paint_type]['name']}, Couleur: RGBA{color}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            # Surface lisse simple (peinture = finition plane)
            self._create_flat_wall_surface(
                bm, 0, 0, 0,
                self.width, self.height,
                thickness=PAINT_THICKNESS,
                subdivisions=0  # Pas besoin subdivisions pour peinture
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallPeinture] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "PEINTURE"
            obj["paint_type"] = self.paint_type
            obj["color"] = self.color

            print(f"[WallPeinture] ✅ Peinture {PAINT_TYPES[self.paint_type]['name']} générée")
            return obj

        finally:
            bm.free()
