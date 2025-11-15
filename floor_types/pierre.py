"""
PIERRE - Sol en pierre naturelle
==================================
Matériau naturel et authentique.
"""

import bpy
from .base import FloorTypeBase


class PierreNaturelle(FloorTypeBase):
    """Pierre naturelle - Authenticité et caractère"""

    FLOOR_NAME = "Pierre Naturelle"
    CATEGORY = "elegant"
    THICKNESS = 0.025  # 25mm
    PATTERN = "random"  # Aspect irrégulier

    TILE_SIZE = 0.4  # 40cm (taille moyenne, aspect varié)

    def _generate_mesh(self, width, length, height):
        """Génère un sol en dalles de pierre naturelle"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau pierre calcaire beige PBR"""
        mat = bpy.data.materials.new(name="Material_Pierre_Naturelle")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Pierre calcaire beige avec texture
            bsdf.inputs["Base Color"].default_value = (0.78, 0.72, 0.65, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.6  # Surface texturée
            bsdf.inputs["Specular"].default_value = 0.25

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
