"""
MARBRE - Sol en marbre
=======================
Matériau élégant et luxueux.
"""

import bpy
from .base import FloorTypeBase, MARBLE_TILE_SIZE


class Marbre(FloorTypeBase):
    """Marbre - Élégance et luxe"""

    FLOOR_NAME = "Marbre"
    CATEGORY = "elegant"
    THICKNESS = 0.020  # 20mm
    PATTERN = "grid"

    TILE_SIZE = 0.5  # 50cm × 50cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol en dalles de marbre"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau marbre blanc de Carrare PBR"""
        mat = bpy.data.materials.new(name="Material_Marbre")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Marbre blanc avec légères veines grises
            bsdf.inputs["Base Color"].default_value = (0.95, 0.94, 0.92, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.05  # Très lisse
            bsdf.inputs["Specular"].default_value = 0.9   # Très réfléchissant
            bsdf.inputs["Sheen"].default_value = 0.3
            # Légère subsurface pour translucidité
            bsdf.inputs["Subsurface"].default_value = 0.02
            bsdf.inputs["Subsurface Color"].default_value = (0.98, 0.97, 0.95, 1.0)

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
