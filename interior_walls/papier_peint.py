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

            # ✅ Appliquer le matériau avec texture
            self._apply_material(obj)

            print(f"[WallPapierPeint] ✅ Papier peint {WALLPAPER_TYPES[self.wallpaper_type]['name']} généré")
            return obj

        finally:
            bm.free()

    def _apply_material(self, obj):
        """Applique le matériau de papier peint avec texture image si disponible"""
        mat_name = f"Material_Wallpaper_{self.wallpaper_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")

        if bsdf:
            # Si image valide, créer texture node
            if self.image_valid and self.image_path:
                # Charger l'image
                try:
                    img = bpy.data.images.load(self.image_path, check_existing=True)

                    # Créer Image Texture node
                    tex_node = nodes.new(type='ShaderNodeTexImage')
                    tex_node.image = img
                    tex_node.location = (-300, 300)

                    # Connecter Image Texture à Base Color
                    links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

                    print(f"[WallPapierPeint] Texture chargée: {self.image_path}")
                except Exception as e:
                    print(f"[WallPapierPeint] ❌ Erreur chargement texture: {e}")
                    # Fallback: couleur unie beige
                    bsdf.inputs["Base Color"].default_value = (0.95, 0.93, 0.88, 1.0)
            else:
                # Pas d'image: couleur unie beige clair
                bsdf.inputs["Base Color"].default_value = (0.95, 0.93, 0.88, 1.0)

            # Propriétés communes
            bsdf.inputs["Roughness"].default_value = 0.7
            bsdf.inputs["Specular"].default_value = 0.1

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
