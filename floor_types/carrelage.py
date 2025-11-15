"""
CARRELAGE - Types de sols carrelés
===================================
- Carrelage céramique (CERAMIC_TILE)
- Grès cérame (PORCELAIN_TILE)
"""

import bpy
from .base import FloorTypeBase, CERAMIC_TILE_SIZE, LARGE_TILE_SIZE


class CarrelageCeramique(FloorTypeBase):
    """Carrelage céramique - Classique et facile d'entretien"""

    FLOOR_NAME = "Carrelage Céramique"
    CATEGORY = "resistant"
    THICKNESS = 0.010  # 10mm
    PATTERN = "grid"

    TILE_SIZE = 0.3  # 30cm × 30cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol en carreaux de céramique"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau céramique beige clair PBR"""
        mat = bpy.data.materials.new(name="Material_Carrelage_Ceramique")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur beige clair classique
            bsdf.inputs["Base Color"].default_value = (0.88, 0.85, 0.78, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.15
            bsdf.inputs["Specular"].default_value = 0.6
            # Légère brillance
            bsdf.inputs["Sheen"].default_value = 0.1

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat


class GresCerame(FloorTypeBase):
    """Grès cérame - Grande taille, haute résistance"""

    FLOOR_NAME = "Grès Cérame"
    CATEGORY = "resistant"
    THICKNESS = 0.012  # 12mm
    PATTERN = "grid"

    TILE_SIZE = 0.6  # 60cm × 60cm (grandes dalles)

    def _generate_mesh(self, width, length, height):
        """Génère un sol en grandes dalles de grès"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau grès gris anthracite PBR"""
        mat = bpy.data.materials.new(name="Material_Gres_Cerame")
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur gris anthracite moderne
            bsdf.inputs["Base Color"].default_value = (0.35, 0.35, 0.38, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.12
            bsdf.inputs["Specular"].default_value = 0.7
            bsdf.inputs["Metallic"].default_value = 0.05

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
