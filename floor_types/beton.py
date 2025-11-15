"""
BÉTON - Sol en béton ciré
===========================
Matériau moderne et minimaliste.
"""

import bpy
from .base import FloorTypeBase


class BetonCire(FloorTypeBase):
    """Béton ciré - Modernité et minimalisme"""

    FLOOR_NAME = "Béton Ciré"
    CATEGORY = "elegant"
    THICKNESS = 0.050  # 50mm (dalle épaisse)
    PATTERN = "seamless"  # Dalle continue sans joints

    def _generate_mesh(self, width, length, height):
        """Génère un sol en béton ciré continu"""
        return self._create_seamless_floor(width, length, height)

    def _apply_material(self, obj):
        """Matériau béton gris ciré PBR"""
        mat = bpy.data.materials.new(name="Material_Beton_Cire")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Béton gris moyen, légèrement poli
            bsdf.inputs["Base Color"].default_value = (0.52, 0.52, 0.52, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.25  # Poli
            bsdf.inputs["Specular"].default_value = 0.4
            bsdf.inputs["Metallic"].default_value = 0.02

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
