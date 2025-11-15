"""
PARQUET - Types de sols en bois
=================================
- Parquet massif (HARDWOOD_SOLID)
- Parquet contrecollé (HARDWOOD_ENGINEERED)
- Stratifié (LAMINATE)
"""

import bpy
from .base import FloorTypeBase, HARDWOOD_PLANK_WIDTH, HARDWOOD_PLANK_LENGTH
from .floor_colors import get_wood_properties


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
        """Matériau bois selon l'essence choisie (OAK, WALNUT, MAPLE, CHERRY, ASH)"""
        # ✅ Récupérer l'essence de bois depuis les custom_options
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Parquet_Massif_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # ✅ Utiliser la couleur de l'essence choisie
            bsdf.inputs["Base Color"].default_value = wood_props['color']
            bsdf.inputs["Roughness"].default_value = wood_props['roughness']
            bsdf.inputs["Specular"].default_value = 0.2

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Parquet Massif] Matériau: {wood_props['name']} - {wood_props['description']}")


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
        """Matériau bois selon l'essence choisie"""
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Parquet_Contrecolle_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = wood_props['color']
            bsdf.inputs["Roughness"].default_value = wood_props['roughness']
            bsdf.inputs["Specular"].default_value = 0.3

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Parquet Contrecollé] Matériau: {wood_props['name']}")


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
        """Matériau imitation bois selon l'essence choisie"""
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Stratifie_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Imitation: légèrement plus clair et plus rough que le vrai bois
            color = wood_props['color']
            lighter_color = (
                min(color[0] * 1.1, 1.0),
                min(color[1] * 1.1, 1.0),
                min(color[2] * 1.1, 1.0),
                1.0
            )
            bsdf.inputs["Base Color"].default_value = lighter_color
            bsdf.inputs["Roughness"].default_value = wood_props['roughness'] + 0.1
            bsdf.inputs["Specular"].default_value = 0.15

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Stratifié] Matériau: Imitation {wood_props['name']}")
