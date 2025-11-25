"""
PARQUET - Générateur procédural de géométrie réaliste
======================================================
- Parquet massif (HARDWOOD_SOLID)
- Parquet contrecollé (HARDWOOD_ENGINEERED)
- Stratifié (LAMINATE)

Types de pose:
- À l'Anglaise (straight)
- Chevron
- Bâton Rompu (herringbone)
- Point de Hongrie (hungarian)
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix
from .base import FloorTypeBase, PLANK_GAP_WIDTH
from .floor_colors import get_wood_properties


# =================================================================
# GÉNÉRATEUR PROCÉDURAL DE LAMES
# =================================================================

class ParquetProceduralGenerator:
    """Génère la géométrie procédurale des lames de parquet"""

    def __init__(self, floor_width, floor_length, plank_width, plank_length,
                 plank_thickness, pattern='STRAIGHT', gap=0.001, random_seed=42):
        self.floor_width = floor_width
        self.floor_length = floor_length
        self.plank_width = plank_width
        self.plank_length = plank_length
        self.plank_thickness = plank_thickness
        self.pattern = pattern
        self.gap = gap
        self.random_seed = random_seed

        # Variations réalistes
        self.height_variation = 0.0003
        self.rotation_variation = 0.2
        self.position_variation = 0.0005
        self.length_variation = 0.05

        random.seed(self.random_seed)

    def create_plank(self, bm, x, y, z, width, length, thickness, rotation=0, uv_layer=None):
        """Crée une lame de parquet avec variations réalistes"""

        # Variations
        z += random.uniform(-self.height_variation, self.height_variation)
        x += random.uniform(-self.position_variation, self.position_variation)
        y += random.uniform(-self.position_variation, self.position_variation)
        rotation += math.radians(random.uniform(-self.rotation_variation, self.rotation_variation))

        # Variation de longueur
        if self.length_variation > 0:
            length *= (1 + random.uniform(-self.length_variation, self.length_variation))

        # Créer les vertices de la lame (8 points pour un parallélépipède)
        hw = width / 2
        hl = length / 2

        verts = [
            Vector((-hw, -hl, 0)),
            Vector((hw, -hl, 0)),
            Vector((hw, hl, 0)),
            Vector((-hw, hl, 0)),
            Vector((-hw, -hl, thickness)),
            Vector((hw, -hl, thickness)),
            Vector((hw, hl, thickness)),
            Vector((-hw, hl, thickness)),
        ]

        # Appliquer rotation
        rot_matrix = Matrix.Rotation(rotation, 3, 'Z')
        verts = [rot_matrix @ v for v in verts]

        # Appliquer translation
        verts = [v + Vector((x, y, z)) for v in verts]

        # Créer les vertices dans bmesh
        bm_verts = [bm.verts.new(v) for v in verts]
        bm.verts.ensure_lookup_table()

        # Créer les faces
        faces = [
            (0, 1, 2, 3),  # Bottom
            (4, 7, 6, 5),  # Top
            (0, 4, 5, 1),  # Front
            (2, 6, 7, 3),  # Back
            (0, 3, 7, 4),  # Left
            (1, 5, 6, 2),  # Right
        ]

        created_faces = []
        for face_indices in faces:
            try:
                f = bm.faces.new([bm_verts[i] for i in face_indices])
                created_faces.append(f)
            except:
                pass

        # UVs
        if uv_layer and created_faces:
            for face in created_faces:
                for loop in face.loops:
                    # UV basé sur la position locale de la lame
                    local_pos = rot_matrix.inverted() @ (loop.vert.co - Vector((x, y, z)))
                    # Normaliser les UVs pour chaque lame
                    u = (local_pos.x + hw) / width
                    v = (local_pos.y + hl) / length
                    loop[uv_layer].uv = (u, v)

        return bm_verts, created_faces

    def generate_straight(self, bm, uv_layer):
        """Parquet à l'anglaise - pose droite décalée"""

        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length + self.gap

        # +2 pour marge de sécurité - le Boolean clippera ce qui dépasse
        rows = int(math.ceil(self.floor_width / plank_w)) + 2

        for row in range(rows):
            x = row * plank_w + self.plank_width / 2

            # Permettre aux lames de dépasser légèrement (Boolean les clippera)
            if x - self.plank_width / 2 > self.floor_width + self.plank_width:
                continue

            # Décalage 1/3 (pose anglaise classique)
            offset = (row % 3) * (plank_l / 3)

            y = offset + self.plank_length / 2

            while y - self.plank_length / 2 < self.floor_length:
                # Calculer la longueur réelle (couper si dépasse)
                actual_length = self.plank_length

                # Couper au début
                start_y = y - actual_length / 2
                if start_y < 0:
                    actual_length += start_y
                    y = actual_length / 2

                # Couper à la fin
                end_y = y + actual_length / 2
                if end_y > self.floor_length:
                    actual_length -= (end_y - self.floor_length)
                    y = self.floor_length - actual_length / 2

                if actual_length > 0.05:  # Minimum 5cm
                    self.create_plank(
                        bm, x, y, 0,
                        self.plank_width, actual_length, self.plank_thickness,
                        0, uv_layer
                    )

                y += plank_l

    def generate_chevron(self, bm, uv_layer):
        """Parquet en chevron (pointe de flèche)"""

        angle = math.radians(45)  # Angle fixe 45° pour chevron classique

        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length

        # Calcul de l'espacement en V
        v_height = plank_l * math.sin(angle)
        v_width = plank_l * math.cos(angle)

        row_height = v_height + self.gap

        rows = int(math.ceil(self.floor_length / row_height)) + 1

        for row in range(rows):
            base_y = row * row_height

            # Côté gauche du V
            x = 0
            while x < self.floor_width / 2 + v_width:
                px = x + v_width / 2
                py = base_y + v_height / 2

                if px < self.floor_width / 2 + plank_l and py < self.floor_length + plank_l:
                    self.create_plank(
                        bm, px, py, 0,
                        self.plank_width, plank_l, self.plank_thickness,
                        angle, uv_layer
                    )

                x += plank_w / math.cos(angle)

            # Côté droit du V (miroir)
            x = 0
            while x < self.floor_width / 2 + v_width:
                px = self.floor_width - x - v_width / 2
                py = base_y + v_height / 2

                if px > -plank_l and py < self.floor_length + plank_l:
                    self.create_plank(
                        bm, px, py, 0,
                        self.plank_width, plank_l, self.plank_thickness,
                        -angle, uv_layer
                    )

                x += plank_w / math.cos(angle)

    def generate_herringbone(self, bm, uv_layer):
        """Parquet bâton rompu"""

        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length + self.gap

        pattern_width = 2 * plank_w
        pattern_height = plank_l

        cols = int(math.ceil(self.floor_width / pattern_width)) + 1
        rows = int(math.ceil(self.floor_length / pattern_height)) + 1

        for col in range(cols):
            for row in range(rows):
                base_x = col * pattern_width
                base_y = row * pattern_height

                # Lame horizontale
                px1 = base_x + self.plank_length / 2
                py1 = base_y + self.plank_width / 2

                if px1 < self.floor_width + plank_l and py1 < self.floor_length + plank_w:
                    self.create_plank(
                        bm, px1, py1, 0,
                        self.plank_width, self.plank_length, self.plank_thickness,
                        math.radians(90), uv_layer
                    )

                # Lame verticale
                px2 = base_x + self.plank_width / 2 + self.plank_length
                py2 = base_y + self.plank_length / 2

                if px2 < self.floor_width + plank_w and py2 < self.floor_length + plank_l:
                    self.create_plank(
                        bm, px2, py2, 0,
                        self.plank_width, self.plank_length, self.plank_thickness,
                        0, uv_layer
                    )

    def generate(self):
        """Génère le parquet selon le type de pose"""
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")

        if self.pattern == 'STRAIGHT':
            self.generate_straight(bm, uv_layer)
        elif self.pattern == 'CHEVRON':
            self.generate_chevron(bm, uv_layer)
        elif self.pattern == 'HERRINGBONE':
            self.generate_herringbone(bm, uv_layer)

        return bm


# =================================================================
# CLASSES PARQUET
# =================================================================

class ParquetMassif(FloorTypeBase):
    """Parquet en bois massif - Chaleureux et authentique"""

    FLOOR_NAME = "Parquet Massif"
    CATEGORY = "warm"
    THICKNESS = 0.018  # 18mm
    PATTERN = "straight"

    # Dimensions planches
    PLANK_WIDTH = 0.09   # 9cm (lame standard)
    PLANK_LENGTH = 0.60  # 60cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol avec vraie géométrie de lames"""

        # Récupérer le type de pose depuis custom_options
        pattern = self.custom_options.get('pattern', 'STRAIGHT')

        # Créer le générateur
        generator = ParquetProceduralGenerator(
            floor_width=width,
            floor_length=length,
            plank_width=self.PLANK_WIDTH,
            plank_length=self.PLANK_LENGTH,
            plank_thickness=self.THICKNESS,
            pattern=pattern,
            gap=PLANK_GAP_WIDTH,
            random_seed=42
        )

        # Générer le bmesh
        bm = generator.generate()

        # Créer le mesh
        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        # Créer l'objet
        obj = bpy.data.objects.new(self.FLOOR_NAME, mesh)
        obj.location = Vector((0, 0, height))

        # Couper aux dimensions exactes du sol avec Boolean
        self._clip_to_floor(obj, width, length, height)

        return obj

    def _clip_to_floor(self, obj, width, length, height):
        """Coupe le parquet aux dimensions exactes du sol"""

        # Créer un cube de clipping
        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter = bpy.context.active_object
        cutter.name = "Parquet_Cutter_Temp"
        cutter.scale = (width, length, self.THICKNESS * 2)
        cutter.location = (width / 2, length / 2, height + self.THICKNESS / 2)
        bpy.ops.object.transform_apply(scale=True, location=True)

        # Lier l'objet parquet à la scène pour appliquer le Boolean
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj

        # Appliquer Boolean
        bool_mod = obj.modifiers.new("Boolean", 'BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = cutter
        bool_mod.solver = 'FAST'

        # Appliquer le modificateur
        bpy.context.view_layer.update()
        bpy.ops.object.modifier_apply(modifier="Boolean")

        # Supprimer le cutter
        bpy.data.objects.remove(cutter)

        # Retirer de la scène (sera réajouté par le système principal)
        bpy.context.collection.objects.unlink(obj)

    def _apply_material(self, obj):
        """Matériau bois selon l'essence choisie (OAK, WALNUT, MAPLE, CHERRY, ASH)"""
        # Récupérer l'essence de bois depuis les custom_options
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Parquet_Massif_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Utiliser la couleur de l'essence choisie
            bsdf.inputs["Base Color"].default_value = wood_props['color']
            bsdf.inputs["Roughness"].default_value = wood_props['roughness']

            # FIX Blender 4.2: "Specular" n'existe plus
            try:
                bsdf.inputs["Specular"].default_value = 0.2
            except KeyError:
                pass

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

    PLANK_WIDTH = 0.12   # 12cm
    PLANK_LENGTH = 1.20  # 1.2m

    def _generate_mesh(self, width, length, height):
        """Génère un sol avec vraie géométrie de lames"""

        pattern = self.custom_options.get('pattern', 'STRAIGHT')

        generator = ParquetProceduralGenerator(
            floor_width=width,
            floor_length=length,
            plank_width=self.PLANK_WIDTH,
            plank_length=self.PLANK_LENGTH,
            plank_thickness=self.THICKNESS,
            pattern=pattern,
            gap=PLANK_GAP_WIDTH,
            random_seed=42
        )

        bm = generator.generate()

        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(self.FLOOR_NAME, mesh)
        obj.location = Vector((0, 0, height))

        self._clip_to_floor(obj, width, length, height)

        return obj

    def _clip_to_floor(self, obj, width, length, height):
        """Coupe le parquet aux dimensions exactes du sol"""

        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter = bpy.context.active_object
        cutter.name = "Parquet_Cutter_Temp"
        cutter.scale = (width, length, self.THICKNESS * 2)
        cutter.location = (width / 2, length / 2, height + self.THICKNESS / 2)
        bpy.ops.object.transform_apply(scale=True, location=True)

        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj

        bool_mod = obj.modifiers.new("Boolean", 'BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = cutter
        bool_mod.solver = 'FAST'

        bpy.context.view_layer.update()
        bpy.ops.object.modifier_apply(modifier="Boolean")

        bpy.data.objects.remove(cutter)
        bpy.context.collection.objects.unlink(obj)

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

            # FIX Blender 4.2: "Specular" n'existe plus
            try:
                bsdf.inputs["Specular"].default_value = 0.3
            except KeyError:
                pass

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Parquet Contrecollé] Matériau: {wood_props['name']}")


class Stratifie(FloorTypeBase):
    """Stratifié - Imitation bois économique"""

    FLOOR_NAME = "Stratifié"
    CATEGORY = "warm"
    THICKNESS = 0.008  # 8mm
    PATTERN = "straight"

    PLANK_WIDTH = 0.19   # 19cm (plus large)
    PLANK_LENGTH = 1.38  # 1.38m (plus long)

    def _generate_mesh(self, width, length, height):
        """Génère un sol avec vraie géométrie de lames"""

        pattern = self.custom_options.get('pattern', 'STRAIGHT')

        generator = ParquetProceduralGenerator(
            floor_width=width,
            floor_length=length,
            plank_width=self.PLANK_WIDTH,
            plank_length=self.PLANK_LENGTH,
            plank_thickness=self.THICKNESS,
            pattern=pattern,
            gap=PLANK_GAP_WIDTH * 0.5,  # Gap plus petit pour stratifié
            random_seed=42
        )

        # Moins de variations pour stratifié (plus uniforme)
        generator.height_variation = 0.0001
        generator.rotation_variation = 0.1
        generator.position_variation = 0.0002
        generator.length_variation = 0.0

        bm = generator.generate()

        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(self.FLOOR_NAME, mesh)
        obj.location = Vector((0, 0, height))

        self._clip_to_floor(obj, width, length, height)

        return obj

    def _clip_to_floor(self, obj, width, length, height):
        """Coupe le parquet aux dimensions exactes du sol"""

        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter = bpy.context.active_object
        cutter.name = "Parquet_Cutter_Temp"
        cutter.scale = (width, length, self.THICKNESS * 2)
        cutter.location = (width / 2, length / 2, height + self.THICKNESS / 2)
        bpy.ops.object.transform_apply(scale=True, location=True)

        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj

        bool_mod = obj.modifiers.new("Boolean", 'BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = cutter
        bool_mod.solver = 'FAST'

        bpy.context.view_layer.update()
        bpy.ops.object.modifier_apply(modifier="Boolean")

        bpy.data.objects.remove(cutter)
        bpy.context.collection.objects.unlink(obj)

    def _apply_material(self, obj):
        """Matériau stratifié - imitation bois"""
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

            # FIX Blender 4.2: "Specular" n'existe plus
            try:
                bsdf.inputs["Specular"].default_value = 0.15
            except KeyError:
                pass

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Stratifié] Matériau imitation {wood_props['name']}")
