"""
FENÊTRE BASCULANTE
==================
Le vantail pivote autour d'un axe central horizontal.
Souvent utilisée pour les toits (velux pivotant).

Géométrie:
- Rotation autour axe horizontal central
- S'ouvre vers l'intérieur ET l'extérieur
- Ventilation optimale
- Idéal toitures, ateliers, grandes hauteurs

Code HAUTE QUALITÉ avec calculs géométriques précis.
"""

import bpy
import bmesh
import math
from .base import WindowBase

# ============================================================
# CONSTANTES SPÉCIFIQUES BASCULANTE
# ============================================================

MAX_PIVOT_ANGLE = 90.0       # 90° rotation max

# ============================================================
# CLASSE FENÊTRE BASCULANTE
# ============================================================

class WindowBasculante(WindowBase):
    """
    Fenêtre basculante (pivot axe horizontal central).

    Caractéristiques:
    - Rotation autour axe horizontal au milieu
    - Haut bascule vers intérieur, bas vers extérieur
    - Ventilation sans perte d'espace
    - Populaire pour velux, toits, ateliers
    """

    def __init__(self, width, height, pivot_angle=45.0, name="WindowBasculante"):
        """
        Initialise une fenêtre basculante.

        Args:
            width: Largeur de la fenêtre (m)
            height: Hauteur de la fenêtre (m)
            pivot_angle: Angle de rotation (degrés, 0-90)
            name: Nom de la fenêtre
        """
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Limiter angle
        self.pivot_angle = max(0.0, min(MAX_PIVOT_ANGLE, pivot_angle))

        print(f"[WindowBasculante] Angle pivot: {self.pivot_angle}°")

    def generate_geometry(self):
        """
        Génère la géométrie de la fenêtre basculante.

        Returns:
            Object Blender de la fenêtre
        """
        bm = bmesh.new()

        try:
            # 1. Cadre dormant
            self._generate_frame(bm)

            # 2. Ouvrant pivotant
            self._generate_pivoting_sash(bm)

            # 3. Vitrage
            self._generate_glass(bm)

            # Créer l'objet Blender
            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            # ✅ SÉCURITÉ: Valider la géométrie
            if not self.validate_geometry(obj):
                print(f"[WindowBasculante] ❌ Échec validation géométrie")
                return None

            # Métadonnées
            obj["window_type"] = "BASCULANTE"
            obj["pivot_angle"] = self.pivot_angle

            print(f"[WindowBasculante] ✅ Fenêtre basculante générée avec succès")
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

    def _generate_pivoting_sash(self, bm):
        """Génère l'ouvrant pivotant."""
        x_offset = self.frame_thickness
        z_offset = self.frame_thickness
        y_offset = self.frame_depth * 0.3

        # Position standard (fermé)
        # TODO: Implémenter rotation réelle autour axe central horizontal
        # pour positions ouvertes

        self._create_frame_box(
            bm,
            x=x_offset,
            y=y_offset,
            z=z_offset,
            width=self.inner_width,
            height=self.inner_height,
            depth=self.sash_thickness
        )

    def _generate_glass(self, bm):
        """Génère le vitrage."""
        self._create_glass_pane(
            bm,
            x=self.frame_thickness,
            y=0,
            z=self.frame_thickness,
            width=self.inner_width,
            height=self.inner_height
        )
