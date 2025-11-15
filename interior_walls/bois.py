"""
BOIS (Bardage intérieur, panneaux, tasseaux)
=============================================
Chaleureux, isolant.

Types:
- BARDAGE: Planches horizontales ou verticales
- PANNEAUX: Grands panneaux lisses
- TASSEAUX: Lattes espacées (claustra)

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase, WOOD_PANEL_THICKNESS, DEFAULT_WOOD_COLOR

WOOD_TYPES = {
    'BARDAGE_VERTICAL': {'name': "Bardage vertical", 'plank_width': 0.12, 'orientation': 'vertical'},
    'BARDAGE_HORIZONTAL': {'name': "Bardage horizontal", 'plank_width': 0.15, 'orientation': 'horizontal'},
    'PANNEAUX': {'name': "Panneaux bois", 'plank_width': 0.6, 'orientation': 'vertical'},
    'TASSEAUX': {'name': "Tasseaux (claustra)", 'plank_width': 0.04, 'orientation': 'vertical'}
}

class WallBois(WallFinishBase):
    """Finition bois (bardage, panneaux, tasseaux)."""

    def __init__(self, width, height, wood_type='BARDAGE_VERTICAL',
                 color=DEFAULT_WOOD_COLOR, name="WallBois"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type bois
        if wood_type not in WOOD_TYPES:
            print(f"[WallBois] ⚠️ Type invalide '{wood_type}', utilisation BARDAGE_VERTICAL")
            wood_type = 'BARDAGE_VERTICAL'

        self.wood_type = wood_type
        self.color = color

        print(f"[WallBois] Type: {WOOD_TYPES[wood_type]['name']}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            config = WOOD_TYPES[self.wood_type]

            # Créer planches de bois
            self._create_wood_planks(
                bm, 0, 0, 0,
                self.width, self.height,
                plank_width=config['plank_width'],
                orientation=config['orientation']
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallBois] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "BOIS"
            obj["wood_type"] = self.wood_type
            obj["color"] = self.color

            print(f"[WallBois] ✅ Bois {WOOD_TYPES[self.wood_type]['name']} généré")
            return obj

        finally:
            bm.free()
