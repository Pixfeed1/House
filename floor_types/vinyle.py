"""
VINYLE - Sol en vinyle/PVC
============================
Matériau économique et résistant.
"""

import bpy
from .base import FloorTypeBase


class Vinyle(FloorTypeBase):
    """Vinyle/PVC - Économique et résistant à l'eau"""

    FLOOR_NAME = "Vinyle PVC"
    CATEGORY = "resistant"
    THICKNESS = 0.005  # 5mm
    PATTERN = "straight"

    PLANK_WIDTH = 0.18   # 18cm
    PLANK_LENGTH = 1.2   # 1.2m

    def _generate_mesh(self, width, length, height):
        """Génère un sol en lames de vinyle"""
        return self._create_plank_floor(
            width, length, height,
            self.PLANK_WIDTH,
            self.PLANK_LENGTH
        )

    def _apply_material(self, obj):
        """Matériau vinyle imitation bois gris PBR"""
        mat = bpy.data.materials.new(name="Material_Vinyle")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Vinyle gris clair imitation bois
            bsdf.inputs["Base Color"].default_value = (0.68, 0.68, 0.70, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.35
            bsdf.inputs["Specular"].default_value = 0.3

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
