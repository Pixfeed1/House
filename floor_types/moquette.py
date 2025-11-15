"""
MOQUETTE - Sol en moquette/tapis
==================================
Matériau confortable et isolant.
"""

import bpy
from .base import FloorTypeBase


class Moquette(FloorTypeBase):
    """Moquette - Confort et isolation acoustique"""

    FLOOR_NAME = "Moquette"
    CATEGORY = "comfort"
    THICKNESS = 0.010  # 10mm
    PATTERN = "seamless"  # Surface continue

    def _generate_mesh(self, width, length, height):
        """Génère un sol en moquette continue"""
        return self._create_seamless_floor(width, length, height)

    def _apply_material(self, obj):
        """Matériau moquette beige douce PBR"""
        mat = bpy.data.materials.new(name="Material_Moquette")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Moquette beige chaud
            bsdf.inputs["Base Color"].default_value = (0.82, 0.75, 0.68, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.9  # Très mate
            bsdf.inputs["Specular"].default_value = 0.05  # Presque pas de reflet
            # Ajout de velours/duvet
            bsdf.inputs["Sheen"].default_value = 0.5
            bsdf.inputs["Sheen Tint"].default_value = 0.3

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
