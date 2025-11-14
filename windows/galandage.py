"""
FENÊTRE COULISSANTE À GALANDAGE
================================
Les vantaux disparaissent dans le mur.
Effet moderne et ouverture totale.

Géométrie:
- Rails horizontaux encastrés dans mur
- Vantaux coulissent et disparaissent dans cloison
- Ouverture 100% (pas d'obstruction)
- Design moderne, baies vitrées

Code HAUTE QUALITÉ avec calculs géométriques précis.
"""

import bpy
import bmesh
from .base import WindowBase

# ============================================================
# CONSTANTES SPÉCIFIQUES GALANDAGE
# ============================================================

WALL_POCKET_DEPTH = 0.15     # 15cm profondeur dans mur

# ============================================================
# CLASSE FENÊTRE À GALANDAGE
# ============================================================

class WindowGalandage(WindowBase):
    """
    Fenêtre coulissante à galandage (encastrée).

    Caractéristiques:
    - Vantaux disparaissent complètement dans le mur
    - Ouverture totale de la baie (100%)
    - Nécessite cloison épaisse
    - Design très épuré
    """

    def __init__(self, width, height, slide_position=0.0, name="WindowGalandage"):
        """
        Initialise une fenêtre à galandage.

        Args:
            width: Largeur de la fenêtre (m)
            height: Hauteur de la fenêtre (m)
            slide_position: Position (0.0=fermé, 1.0=dans mur)
            name: Nom de la fenêtre
        """
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider position
        self.slide_position = max(0.0, min(1.0, slide_position))

        print(f"[WindowGalandage] Position: {self.slide_position * 100:.0f}%")

    def generate_geometry(self):
        """
        Génère la géométrie de la fenêtre à galandage.

        Returns:
            Object Blender de la fenêtre
        """
        bm = bmesh.new()

        try:
            # 1. Cadre dormant minimal (rails)
            self._generate_frame_with_rails(bm)

            # 2. Vantaux (position selon slide_position)
            self._generate_sliding_sashes(bm)

            # 3. Vitrages
            self._generate_glass_panes(bm)

            # Créer l'objet Blender
            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            # ✅ SÉCURITÉ: Valider la géométrie
            if not self.validate_geometry(obj):
                print(f"[WindowGalandage] ❌ Échec validation géométrie")
                return None

            # Métadonnées
            obj["window_type"] = "GALANDAGE"
            obj["slide_position"] = self.slide_position

            print(f"[WindowGalandage] ✅ Fenêtre à galandage générée avec succès")
            return obj

        finally:
            bm.free()

    def _generate_frame_with_rails(self, bm):
        """Génère le cadre minimal avec rails."""
        # Cadre très fin (juste rails)
        self._create_frame_box(
            bm,
            x=0,
            y=0,
            z=0,
            width=self.width,
            height=self.height,
            depth=self.frame_depth * 0.5  # Cadre plus fin
        )

    def _generate_sliding_sashes(self, bm):
        """Génère les vantaux coulissants."""
        # 1 ou 2 vantaux selon largeur
        num_sashes = 2 if self.width > 1.2 else 1

        sash_width = self.width / num_sashes
        sash_height = self.inner_height

        # Calcul position selon slide_position
        # Position 1.0 = vantail complètement dans le mur (décalé de sa largeur)
        slide_offset = self.slide_position * sash_width

        z_offset = self.frame_thickness

        if num_sashes == 1:
            # Vantail unique
            self._create_frame_box(
                bm,
                x=self.frame_thickness - slide_offset,
                y=self.frame_depth * 0.3,
                z=z_offset,
                width=sash_width,
                height=sash_height,
                depth=self.sash_thickness
            )
        else:
            # Deux vantaux
            for i in range(2):
                self._create_frame_box(
                    bm,
                    x=self.frame_thickness + i * sash_width - slide_offset,
                    y=self.frame_depth * 0.3,
                    z=z_offset,
                    width=sash_width,
                    height=sash_height,
                    depth=self.sash_thickness
                )

    def _generate_glass_panes(self, bm):
        """Génère les vitrages."""
        num_sashes = 2 if self.width > 1.2 else 1
        sash_width = self.width / num_sashes
        z_offset = self.frame_thickness
        slide_offset = self.slide_position * sash_width

        if num_sashes == 1:
            self._create_glass_pane(
                bm,
                x=self.frame_thickness - slide_offset,
                y=0,
                z=z_offset,
                width=sash_width - 2 * self.frame_thickness,
                height=self.inner_height
            )
        else:
            for i in range(2):
                self._create_glass_pane(
                    bm,
                    x=self.frame_thickness + i * sash_width - slide_offset,
                    y=0,
                    z=z_offset,
                    width=sash_width - 2 * self.frame_thickness,
                    height=self.inner_height
                )
