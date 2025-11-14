"""
FENÊTRE À GUILLOTINE (à l'américaine)
======================================
Un vantail coulisse verticalement.
Très utilisée dans les maisons modernes et anglo-saxonnes.

Géométrie:
- Cadre dormant avec rails verticaux
- 1 ou 2 panneaux coulissants verticalement
- Panneau inférieur mobile monte/descend
- Style américain traditionnel

Code HAUTE QUALITÉ avec calculs géométriques précis.
"""

import bpy
import bmesh
from .base import WindowBase

# ============================================================
# CONSTANTES SPÉCIFIQUES GUILLOTINE
# ============================================================

COUNTERWEIGHT_SPACE = 0.08   # 8cm espace contrepoids dans mur

# ============================================================
# CLASSE FENÊTRE À GUILLOTINE
# ============================================================

class WindowGuillotine(WindowBase):
    """
    Fenêtre à guillotine (coulissement vertical).

    Caractéristiques:
    - Panneau(x) coulissant verticalement
    - Généralement panneau bas mobile
    - Système de contrepoids (dans mur)
    - Style américain/victorien
    - Ouverture max = 50% hauteur
    """

    def __init__(self, width, height, raise_position=0.0, name="WindowGuillotine"):
        """
        Initialise une fenêtre à guillotine.

        Args:
            width: Largeur de la fenêtre (m)
            height: Hauteur de la fenêtre (m)
            raise_position: Position levée (0.0=fermé, 1.0=ouvert 50%)
            name: Nom de la fenêtre
        """
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider position
        self.raise_position = max(0.0, min(1.0, raise_position))

        print(f"[WindowGuillotine] Position levée: {self.raise_position * 100:.0f}%")

    def generate_geometry(self):
        """
        Génère la géométrie de la fenêtre à guillotine.

        Returns:
            Object Blender de la fenêtre
        """
        bm = bmesh.new()

        try:
            # 1. Cadre dormant avec rails
            self._generate_frame_with_rails(bm)

            # 2. Deux panneaux (haut fixe, bas mobile)
            self._generate_panels(bm)

            # 3. Vitrages
            self._generate_glass_panes(bm)

            # Créer l'objet Blender
            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            # ✅ SÉCURITÉ: Valider la géométrie
            if not self.validate_geometry(obj):
                print(f"[WindowGuillotine] ❌ Échec validation géométrie")
                return None

            # Métadonnées
            obj["window_type"] = "GUILLOTINE"
            obj["raise_position"] = self.raise_position

            print(f"[WindowGuillotine] ✅ Fenêtre à guillotine générée avec succès")
            return obj

        finally:
            bm.free()

    def _generate_frame_with_rails(self, bm):
        """Génère le cadre avec rails verticaux."""
        # Cadre principal
        self._create_frame_box(
            bm,
            x=0,
            y=0,
            z=0,
            width=self.width,
            height=self.height,
            depth=self.frame_depth
        )

        # TODO: Ajouter géométrie rails verticaux

    def _generate_panels(self, bm):
        """Génère les deux panneaux coulissants."""
        # Chaque panneau fait 50% de la hauteur
        panel_width = self.inner_width
        panel_height = self.height / 2

        x_offset = self.frame_thickness
        y_offset = self.frame_depth * 0.3

        # Calcul levée du panneau bas
        raise_offset = self.raise_position * panel_height

        # Panneau haut (fixe, arrière-plan)
        self._create_frame_box(
            bm,
            x=x_offset,
            y=y_offset - 0.01,  # Légèrement en retrait
            z=panel_height,
            width=panel_width,
            height=panel_height,
            depth=self.sash_thickness
        )

        # Panneau bas (mobile, avant-plan)
        self._create_frame_box(
            bm,
            x=x_offset,
            y=y_offset + 0.01,  # Légèrement en avant
            z=self.frame_thickness + raise_offset,
            width=panel_width,
            height=panel_height,
            depth=self.sash_thickness
        )

    def _generate_glass_panes(self, bm):
        """Génère les vitrages des deux panneaux."""
        panel_width = self.inner_width
        panel_height = self.height / 2
        x_offset = self.frame_thickness
        raise_offset = self.raise_position * panel_height

        # Vitrage panneau haut
        self._create_glass_pane(
            bm,
            x=x_offset,
            y=0,
            z=panel_height,
            width=panel_width,
            height=panel_height - self.frame_thickness
        )

        # Vitrage panneau bas
        self._create_glass_pane(
            bm,
            x=x_offset,
            y=0,
            z=self.frame_thickness + raise_offset,
            width=panel_width,
            height=panel_height - self.frame_thickness
        )
