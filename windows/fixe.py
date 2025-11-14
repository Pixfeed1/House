"""
FENÊTRE FIXE
=============
Ne s'ouvre pas.
Apporte beaucoup de lumière, idéale pour grandes baies.

Géométrie:
- Cadre dormant uniquement (pas d'ouvrant)
- Vitrage fixe
- Très simple, excellente isolation
- Idéal pour baies vitrées, verrières

Code HAUTE QUALITÉ avec calculs géométriques précis.
"""

import bpy
import bmesh
from .base import WindowBase

# ============================================================
# CLASSE FENÊTRE FIXE
# ============================================================

class WindowFixe(WindowBase):
    """
    Fenêtre fixe (non ouvrante).

    Caractéristiques:
    - Aucun mécanisme d'ouverture
    - Vitrage scellé dans le cadre
    - Maximum de surface vitrée
    - Isolation optimale (pas de joints mobiles)
    - Idéal pour grandes baies, puits de lumière
    """

    def __init__(self, width, height, name="WindowFixe"):
        """
        Initialise une fenêtre fixe.

        Args:
            width: Largeur de la fenêtre (m)
            height: Hauteur de la fenêtre (m)
            name: Nom de la fenêtre
        """
        super().__init__(width, height, name)
        print(f"[WindowFixe] Fenêtre fixe {width:.2f}m × {height:.2f}m")

    def generate_geometry(self):
        """
        Génère la géométrie de la fenêtre fixe.

        Returns:
            Object Blender de la fenêtre
        """
        bm = bmesh.new()

        try:
            # 1. Cadre dormant uniquement
            self._generate_frame(bm)

            # 2. Vitrage fixe
            self._generate_glass(bm)

            # Créer l'objet Blender
            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            # ✅ SÉCURITÉ: Valider la géométrie
            if not self.validate_geometry(obj):
                print(f"[WindowFixe] ❌ Échec validation géométrie")
                return None

            # Métadonnées
            obj["window_type"] = "FIXE"
            obj["openable"] = False

            print(f"[WindowFixe] ✅ Fenêtre fixe générée avec succès")
            return obj

        finally:
            bm.free()

    def _generate_frame(self, bm):
        """Génère le cadre dormant."""
        self._create_frame_box(
            bm,
            x=0,
            y=0,
            z=0,
            width=self.width,
            height=self.height,
            depth=self.frame_depth
        )

    def _generate_glass(self, bm):
        """Génère le vitrage fixe."""
        self._create_glass_pane(
            bm,
            x=self.frame_thickness,
            y=0,
            z=self.frame_thickness,
            width=self.inner_width,
            height=self.inner_height
        )
