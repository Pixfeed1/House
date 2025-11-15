"""
PAPIER PEINT
=============
Lisse, texturé, vinyle, intissé.
Existe en versions résistantes pour cuisine/salle de bain.

IMPORTANT: Système de validation résolution image.
- Résolution MIN: 1024×1024px
- Résolution RECOMMANDÉE: 2048×2048px pour qualité optimale

Code HAUTE QUALITÉ avec vérifications strictes.
"""

import bpy
import bmesh
from .base import (WallFinishBase, WALLPAPER_THICKNESS,
                   MIN_WALLPAPER_RES_WIDTH, MIN_WALLPAPER_RES_HEIGHT,
                   RECOMMENDED_WALLPAPER_RES)

# Types de papier peint
WALLPAPER_TYPES = {
    'LISSE': {'name': "Lisse", 'relief': False},
    'TEXTURE': {'name': "Texturé", 'relief': True},
    'VINYLE': {'name': "Vinyle (résistant)", 'relief': False},
    'INTISSE': {'name': "Intissé", 'relief': False}
}

class WallPapierPeint(WallFinishBase):
    """
    Finition papier peint avec texture image.

    VALIDATIONS STRICTES:
    - Vérification existence fichier image
    - Vérification format (PNG, JPG, TGA, BMP)
    - Vérification résolution minimale (1024×1024px)
    - Avertissement si résolution sous-optimale
    """

    def __init__(self, width, height, wallpaper_type='LISSE',
                 image_path=None, name="WallPapierPeint"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type papier peint
        if wallpaper_type not in WALLPAPER_TYPES:
            print(f"[WallPapierPeint] ⚠️ Type invalide '{wallpaper_type}', utilisation LISSE")
            wallpaper_type = 'LISSE'

        self.wallpaper_type = wallpaper_type
        self.image_path = image_path
        self.image_valid = False
        self.image_width = 0
        self.image_height = 0

        # ✅ SÉCURITÉ: Valider image si fournie
        if image_path:
            valid, w, h, msg = self._validate_image_resolution(image_path)
            self.image_valid = valid
            self.image_width = w
            self.image_height = h

            if valid:
                print(f"[WallPapierPeint] ✅ {msg}")
            else:
                print(f"[WallPapierPeint] ❌ {msg}")
                print(f"[WallPapierPeint] Le papier peint sera créé SANS texture")
        else:
            print(f"[WallPapierPeint] ⚠️ Aucune image fournie, papier peint uni")

        print(f"[WallPapierPeint] Type: {WALLPAPER_TYPES[wallpaper_type]['name']}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            # Surface avec subdivisions pour UV mapping propre
            has_relief = WALLPAPER_TYPES[self.wallpaper_type]['relief']

            if has_relief:
                # Papier texturé: légères subdivisions pour relief
                self._create_flat_wall_surface(
                    bm, 0, 0, 0,
                    self.width, self.height,
                    thickness=WALLPAPER_THICKNESS,
                    subdivisions=2
                )
            else:
                # Papier lisse: subdivisions pour UV mapping
                self._create_flat_wall_surface(
                    bm, 0, 0, 0,
                    self.width, self.height,
                    thickness=WALLPAPER_THICKNESS,
                    subdivisions=1
                )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallPapierPeint] ❌ Échec validation")
                return None

            # ✅ Setup UV mapping (crucial pour papier peint)
            if not self._setup_uv_mapping(obj, self.image_path if self.image_valid else None):
                print(f"[WallPapierPeint] ⚠️ Échec UV mapping")

            # Métadonnées
            obj["finish_type"] = "PAPIER_PEINT"
            obj["wallpaper_type"] = self.wallpaper_type
            obj["has_texture"] = self.image_valid
            if self.image_valid:
                obj["texture_path"] = self.image_path
                obj["texture_resolution"] = f"{self.image_width}×{self.image_height}"

            print(f"[WallPapierPeint] ✅ Papier peint {WALLPAPER_TYPES[self.wallpaper_type]['name']} généré")
            return obj

        finally:
            bm.free()
