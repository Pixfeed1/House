"""
PARQUET - Types de sols en bois
=================================
- Parquet massif (HARDWOOD_SOLID)
- Parquet contrecollé (HARDWOOD_ENGINEERED)
- Stratifié (LAMINATE)
"""

import bpy
from .base import FloorTypeBase, HARDWOOD_PLANK_WIDTH, HARDWOOD_PLANK_LENGTH


class ParquetMassif(FloorTypeBase):
    """Parquet en bois massif - Chaleureux et authentique"""

    FLOOR_NAME = "Parquet Massif"
    CATEGORY = "warm"
    THICKNESS = 0.018  # 18mm
    PATTERN = "straight"

    # Dimensions planches
    PLANK_WIDTH = 0.15   # 15cm
    PLANK_LENGTH = 1.2   # 1.2m

    def _generate_mesh(self, width, length, height):
        """Génère un sol en planches de parquet massif"""
        return self._create_plank_floor(
            width, length, height,
            self.PLANK_WIDTH,
            self.PLANK_LENGTH
        )

    def _apply_material(self, obj):
        """Matériau bois chêne naturel PBR"""
        mat = bpy.data.materials.new(name="Material_Parquet_Massif")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur bois chêne clair
            bsdf.inputs["Base Color"].default_value = (0.54, 0.42, 0.27, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.3
            bsdf.inputs["Specular"].default_value = 0.2

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat


class ParquetContrecolle(FloorTypeBase):
    """Parquet contrecollé - Stable et polyvalent"""

    FLOOR_NAME = "Parquet Contrecollé"
    CATEGORY = "warm"
    THICKNESS = 0.014  # 14mm
    PATTERN = "straight"

    PLANK_WIDTH = 0.18   # 18cm (plus large)
    PLANK_LENGTH = 1.5   # 1.5m (plus long)

    def _generate_mesh(self, width, length, height):
        """Génère un sol en planches de parquet contrecollé"""
        return self._create_plank_floor(
            width, length, height,
            self.PLANK_WIDTH,
            self.PLANK_LENGTH
        )

    def _apply_material(self, obj):
        """Matériau bois noyer foncé PBR"""
        mat = bpy.data.materials.new(name="Material_Parquet_Contrecolle")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur bois noyer foncé
            bsdf.inputs["Base Color"].default_value = (0.35, 0.25, 0.18, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.25
            bsdf.inputs["Specular"].default_value = 0.3

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat


class Stratifie(FloorTypeBase):
    """Stratifié - Économique et résistant"""

    FLOOR_NAME = "Stratifié"
    CATEGORY = "warm"
    THICKNESS = 0.008  # 8mm
    PATTERN = "straight"

    PLANK_WIDTH = 0.19   # 19cm
    PLANK_LENGTH = 1.3   # 1.3m

    def _generate_mesh(self, width, length, height):
        """Génère un sol en lames de stratifié"""
        return self._create_plank_floor(
            width, length, height,
            self.PLANK_WIDTH,
            self.PLANK_LENGTH
        )

    def _apply_material(self, obj):
        """Matériau imitation bois pin PBR"""
        mat = bpy.data.materials.new(name="Material_Stratifie")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur bois pin clair (imitation)
            bsdf.inputs["Base Color"].default_value = (0.72, 0.58, 0.42, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.4
            bsdf.inputs["Specular"].default_value = 0.15

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
