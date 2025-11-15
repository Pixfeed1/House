"""
LINOLÉUM - Sol en linoléum
============================
Matériau écologique et durable.
"""

import bpy
from .base import FloorTypeBase


class Linoleum(FloorTypeBase):
    """Linoléum - Écologique et naturel"""

    FLOOR_NAME = "Linoléum"
    CATEGORY = "resistant"
    THICKNESS = 0.003  # 3mm
    PATTERN = "sheet"  # Nappe continue

    TILE_SIZE = 0.5  # 50cm (si en dalles)

    def _generate_mesh(self, width, length, height):
        """Génère un sol en linoléum (seamless ou dalles selon préférence)"""
        # Linoléum peut être en nappe continue ou en dalles
        # Ici on utilise seamless pour effet nappe
        return self._create_seamless_floor(width, length, height)

    def _apply_material(self, obj):
        """Matériau linoléum vert olive naturel PBR"""
        mat = bpy.data.materials.new(name="Material_Linoleum")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Linoléum vert olive naturel
            bsdf.inputs["Base Color"].default_value = (0.62, 0.65, 0.52, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.45
            bsdf.inputs["Specular"].default_value = 0.2

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
