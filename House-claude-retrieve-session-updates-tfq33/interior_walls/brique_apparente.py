"""
BRIQUE APPARENTE (Non finie)
=============================
Laisser les briques apparentes des deux côtés.
Style construction inachevée, industriel, loft.

Option pour:
- Maison en cours de construction
- Style industriel/loft
- Aspect brut authentique

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase

class WallBriqueApparente(WallFinishBase):
    """
    Finition briques apparentes (non finies).

    IMPORTANT: Cette classe génère une surface minimale.
    Les vraies briques 3D sont gérées par le système brick_geometry
    du module principal. Cette finition indique simplement qu'il
    faut laisser les briques visibles sans finition.
    """

    def __init__(self, width, height, name="WallBriqueApparente"):
        super().__init__(width, height, name)
        print(f"[WallBriqueApparente] Briques apparentes (style brut/industriel)")

    def generate_finish(self):
        """
        Génère une surface minimale pour briques apparentes.

        Note: La vraie géométrie de briques est gérée ailleurs.
        Cette méthode crée juste un placeholder/indicateur.
        """
        bm = bmesh.new()

        try:
            # Surface plane très fine (juste marqueur visuel)
            self._create_flat_wall_surface(
                bm, 0, 0, 0,
                self.width, self.height,
                thickness=0.001,  # 1mm (placeholder)
                subdivisions=0
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallBriqueApparente] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "BRIQUE_APPARENTE"
            obj["industrial_style"] = True
            obj["needs_brick_geometry"] = True  # Indique qu'il faut garder briques 3D

            print(f"[WallBriqueApparente] ✅ Briques apparentes (placeholder) généré")
            return obj

        finally:
            bm.free()
