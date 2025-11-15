"""
CARRELAGE - Types de sols carrelés
===================================
- Carrelage céramique (CERAMIC_TILE)
- Grès cérame (PORCELAIN_TILE)
"""

import bpy
from .base import FloorTypeBase, CERAMIC_TILE_SIZE, LARGE_TILE_SIZE
from .floor_colors import get_tile_properties


class CarrelageCeramique(FloorTypeBase):
    """Carrelage céramique - Classique et facile d'entretien"""

    FLOOR_NAME = "Carrelage Céramique"
    CATEGORY = "resistant"
    THICKNESS = 0.010  # 10mm
    PATTERN = "grid"

    TILE_SIZE = 0.3  # 30cm × 30cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol en carreaux de céramique"""
        # ✅ Récupérer la taille personnalisée si fournie
        tile_size = self.custom_options.get('tile_size', self.TILE_SIZE)
        return self._create_tile_floor(
            width, length, height,
            tile_size
        )

    def _apply_material(self, obj):
        """Matériau céramique selon la couleur choisie (WHITE, BEIGE, GREY, BLACK, TERRACOTTA)"""
        # ✅ Récupérer la couleur depuis les custom_options
        tile_color = self.custom_options.get('tile_color', 'BEIGE')
        tile_props = get_tile_properties(tile_color)

        mat_name = f"Material_Carrelage_Ceramique_{tile_color}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # ✅ Utiliser la couleur du preset choisi
            bsdf.inputs["Base Color"].default_value = tile_props['color']
            bsdf.inputs["Roughness"].default_value = tile_props['roughness']
            bsdf.inputs["Specular"].default_value = 0.6
            # Légère brillance pour effet céramique
            bsdf.inputs["Sheen"].default_value = 0.1

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Carrelage Céramique] Matériau: {tile_props['name']} - {tile_props['description']}")


class GresCerame(FloorTypeBase):
    """Grès cérame - Grande taille, haute résistance"""

    FLOOR_NAME = "Grès Cérame"
    CATEGORY = "resistant"
    THICKNESS = 0.012  # 12mm
    PATTERN = "grid"

    TILE_SIZE = 0.6  # 60cm × 60cm (grandes dalles)

    def _generate_mesh(self, width, length, height):
        """Génère un sol en grandes dalles de grès"""
        # ✅ Récupérer la taille personnalisée si fournie
        tile_size = self.custom_options.get('tile_size', self.TILE_SIZE)
        return self._create_tile_floor(
            width, length, height,
            tile_size
        )

    def _apply_material(self, obj):
        """Matériau grès cérame selon la couleur choisie"""
        # ✅ Récupérer la couleur depuis les custom_options
        tile_color = self.custom_options.get('tile_color', 'GREY')
        tile_props = get_tile_properties(tile_color)

        mat_name = f"Material_Gres_Cerame_{tile_color}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # ✅ Utiliser la couleur du preset choisi
            bsdf.inputs["Base Color"].default_value = tile_props['color']
            bsdf.inputs["Roughness"].default_value = tile_props['roughness']
            bsdf.inputs["Specular"].default_value = 0.7
            bsdf.inputs["Metallic"].default_value = 0.05

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Grès Cérame] Matériau: {tile_props['name']} - {tile_props['description']}")
