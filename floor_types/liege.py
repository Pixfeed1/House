"""
LIÈGE - Sol en liège
=====================
Matériau écologique et isolant.
"""

import bpy
from .base import FloorTypeBase


class Liege(FloorTypeBase):
    """Liège - Écologique et confortable"""

    FLOOR_NAME = "Liège"
    CATEGORY = "comfort"
    THICKNESS = 0.006  # 6mm
    PATTERN = "grid"

    TILE_SIZE = 0.3  # 30cm × 30cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol en dalles de liège"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau liège naturel brun PBR"""
        mat = bpy.data.materials.new(name="Material_Liege")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Liège brun naturel
            bsdf.inputs["Base Color"].default_value = (0.65, 0.52, 0.38, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.7  # Texture poreuse
            bsdf.inputs["Specular"].default_value = 0.1  # Peu réfléchissant

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
