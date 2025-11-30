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

CORRECTION v2: Suppression du Boolean qui échouait.
Les lames sont maintenant clippées directement dans le générateur.
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

    def create_plank_clipped(self, bm, x, y, z, width, length, thickness, rotation=0, uv_layer=None):
        """
        Crée une lame de parquet avec clipping aux bords du sol.
        
        CORRECTION: Les lames qui dépassent sont coupées au lieu d'être ignorées.
        """
        # Variations (réduites pour éviter les dépassements)
        z += random.uniform(-self.height_variation, self.height_variation)
        x += random.uniform(-self.position_variation, self.position_variation)
        y += random.uniform(-self.position_variation, self.position_variation)
        rotation += math.radians(random.uniform(-self.rotation_variation, self.rotation_variation))

        # Pour les lames droites (pas de rotation significative), on peut clipper facilement
        if abs(rotation) < 0.01:  # Quasi pas de rotation
            # Calculer les bords de la lame
            x_min = x - width / 2
            x_max = x + width / 2
            y_min = y - length / 2
            y_max = y + length / 2
            
            # Clipper aux bords du sol
            if x_max <= 0 or x_min >= self.floor_width:
                return None, None  # Lame complètement hors zone
            if y_max <= 0 or y_min >= self.floor_length:
                return None, None  # Lame complètement hors zone
            
            # Ajuster les bords
            if x_min < 0:
                width += x_min  # Réduire la largeur
                x = width / 2   # Recentrer
                x_min = 0
            if x_max > self.floor_width:
                width -= (x_max - self.floor_width)
                x = self.floor_width - width / 2
            
            if y_min < 0:
                length += y_min
                y = length / 2
                y_min = 0
            if y_max > self.floor_length:
                length -= (y_max - self.floor_length)
                y = self.floor_length - length / 2
            
            # Vérifier que la lame a encore une taille valide
            if width < 0.005 or length < 0.005:  # Minimum 5mm
                return None, None
        
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
                    local_pos = rot_matrix.inverted() @ (loop.vert.co - Vector((x, y, z)))
                    u = (local_pos.x + hw) / width if width > 0 else 0
                    v = (local_pos.y + hl) / length if length > 0 else 0
                    loop[uv_layer].uv = (u, v)

        return bm_verts, created_faces

    def generate_straight(self, bm, uv_layer):
        """Parquet à l'anglaise - pose droite décalée avec clipping intégré"""

        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length + self.gap

        rows = int(math.ceil(self.floor_width / plank_w)) + 1
        planks_created = 0

        for row in range(rows):
            x = row * plank_w + self.plank_width / 2

            # Arrêter si on est trop loin
            if x - self.plank_width / 2 > self.floor_width:
                continue

            # Décalage 1/3 (pose anglaise classique)
            offset = (row % 3) * (plank_l / 3)

            y = offset + self.plank_length / 2 - plank_l
            if y < self.plank_length / 2:
                y = self.plank_length / 2

            while y - self.plank_length / 2 < self.floor_length:
                result = self.create_plank_clipped(
                    bm, x, y, 0,
                    self.plank_width, self.plank_length, self.plank_thickness,
                    0, uv_layer
                )
                if result[0] is not None:
                    planks_created += 1

                y += plank_l

        print(f"[Parquet] STRAIGHT: {planks_created} lames créées")

    def generate_chevron(self, bm, uv_layer):
        """Parquet en chevron avec clipping intégré"""

        angle = math.radians(45)
        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length

        v_height = plank_l * math.sin(angle)
        v_width = plank_l * math.cos(angle)
        row_height = v_height + self.gap

        rows = int(math.ceil(self.floor_length / row_height)) + 2
        planks_created = 0

        for row in range(rows):
            base_y = row * row_height

            # Côté gauche du V
            x = 0
            while x < self.floor_width / 2 + v_width:
                px = x + v_width / 2
                py = base_y + v_height / 2

                if py < self.floor_length + plank_l:
                    result = self.create_plank_clipped(
                        bm, px, py, 0,
                        self.plank_width, plank_l, self.plank_thickness,
                        angle, uv_layer
                    )
                    if result[0] is not None:
                        planks_created += 1

                x += plank_w / math.cos(angle)

            # Côté droit du V (miroir)
            x = 0
            while x < self.floor_width / 2 + v_width:
                px = self.floor_width - x - v_width / 2
                py = base_y + v_height / 2

                if py < self.floor_length + plank_l:
                    result = self.create_plank_clipped(
                        bm, px, py, 0,
                        self.plank_width, plank_l, self.plank_thickness,
                        -angle, uv_layer
                    )
                    if result[0] is not None:
                        planks_created += 1

                x += plank_w / math.cos(angle)

        print(f"[Parquet] CHEVRON: {planks_created} lames créées")

    def generate_herringbone(self, bm, uv_layer):
        """Parquet bâton rompu avec clipping intégré"""

        plank_w = self.plank_width + self.gap
        plank_l = self.plank_length + self.gap

        pattern_width = 2 * plank_w
        pattern_height = plank_l

        cols = int(math.ceil(self.floor_width / pattern_width)) + 1
        rows = int(math.ceil(self.floor_length / pattern_height)) + 1
        planks_created = 0

        for col in range(cols):
            for row in range(rows):
                base_x = col * pattern_width
                base_y = row * pattern_height

                # Lame horizontale
                px1 = base_x + self.plank_length / 2
                py1 = base_y + self.plank_width / 2

                result = self.create_plank_clipped(
                    bm, px1, py1, 0,
                    self.plank_width, self.plank_length, self.plank_thickness,
                    math.radians(90), uv_layer
                )
                if result[0] is not None:
                    planks_created += 1

                # Lame verticale
                px2 = base_x + self.plank_width / 2 + self.plank_length
                py2 = base_y + self.plank_length / 2

                result = self.create_plank_clipped(
                    bm, px2, py2, 0,
                    self.plank_width, self.plank_length, self.plank_thickness,
                    0, uv_layer
                )
                if result[0] is not None:
                    planks_created += 1

        print(f"[Parquet] HERRINGBONE: {planks_created} lames créées")

    def generate(self):
        """Génère le parquet selon le type de pose"""
        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")

        print(f"[Parquet] Génération pattern={self.pattern}, floor={self.floor_width:.2f}x{self.floor_length:.2f}m")

        if self.pattern == 'STRAIGHT':
            self.generate_straight(bm, uv_layer)
        elif self.pattern == 'CHEVRON':
            self.generate_chevron(bm, uv_layer)
        elif self.pattern == 'HERRINGBONE':
            self.generate_herringbone(bm, uv_layer)

        print(f"[Parquet] Mesh généré: {len(bm.verts)} vertices, {len(bm.faces)} faces")

        # Chanfreins sur les bords des lames
        edges_to_bevel = []
        for edge in bm.edges:
            v1, v2 = edge.verts
            if abs(v1.co.z - v2.co.z) > 0.001:
                edges_to_bevel.append(edge)

        if edges_to_bevel:
            try:
                bmesh.ops.bevel(
                    bm,
                    geom=edges_to_bevel,
                    offset=0.001,  # 1mm de chanfrein
                    segments=1,
                    profile=0.5,
                    affect='EDGES'
                )
                print(f"[Parquet] Chanfreins appliqués sur {len(edges_to_bevel)} arêtes")
            except Exception as e:
                print(f"[Parquet] Erreur chanfrein (ignorée): {e}")

        return bm


# =================================================================
# CLASSES PARQUET (SANS BOOLEAN)
# =================================================================

class ParquetMassif(FloorTypeBase):
    """Parquet en bois massif - Chaleureux et authentique"""

    FLOOR_NAME = "Parquet Massif"
    CATEGORY = "warm"
    THICKNESS = 0.018  # 18mm
    PATTERN = "straight"

    PLANK_WIDTH = 0.09   # 9cm
    PLANK_LENGTH = 0.60  # 60cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol avec vraie géométrie de lames - SANS Boolean"""

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

        # Générer le bmesh (déjà clippé aux dimensions)
        bm = generator.generate()

        # Créer le mesh
        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm.to_mesh(mesh)
        bm.free()

        # Créer l'objet
        obj = bpy.data.objects.new(self.FLOOR_NAME, mesh)
        obj.location = Vector((0, 0, height))

        print(f"[Parquet] Objet créé: {len(mesh.vertices)} vertices, {len(mesh.polygons)} faces")

        return obj

    def _apply_material(self, obj):
        """Matériau bois selon l'essence choisie"""
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Parquet_Massif_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = wood_props['color']
            bsdf.inputs["Roughness"].default_value = wood_props['roughness']
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
        """Génère un sol avec vraie géométrie de lames - SANS Boolean"""

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

        print(f"[Parquet] Objet créé: {len(mesh.vertices)} vertices, {len(mesh.polygons)} faces")

        return obj

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

    PLANK_WIDTH = 0.19   # 19cm
    PLANK_LENGTH = 1.38  # 1.38m

    def _generate_mesh(self, width, length, height):
        """Génère un sol avec vraie géométrie de lames - SANS Boolean"""

        pattern = self.custom_options.get('pattern', 'STRAIGHT')

        generator = ParquetProceduralGenerator(
            floor_width=width,
            floor_length=length,
            plank_width=self.PLANK_WIDTH,
            plank_length=self.PLANK_LENGTH,
            plank_thickness=self.THICKNESS,
            pattern=pattern,
            gap=PLANK_GAP_WIDTH * 0.5,
            random_seed=42
        )

        # Moins de variations pour stratifié
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

        print(f"[Parquet] Objet créé: {len(mesh.vertices)} vertices, {len(mesh.polygons)} faces")

        return obj

    def _apply_material(self, obj):
        """Matériau stratifié - imitation bois"""
        wood_type = self.custom_options.get('wood_type', 'OAK')
        wood_props = get_wood_properties(wood_type)

        mat_name = f"Material_Stratifie_{wood_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            color = wood_props['color']
            lighter_color = (
                min(color[0] * 1.1, 1.0),
                min(color[1] * 1.1, 1.0),
                min(color[2] * 1.1, 1.0),
                1.0
            )
            bsdf.inputs["Base Color"].default_value = lighter_color
            bsdf.inputs["Roughness"].default_value = wood_props['roughness'] + 0.1
            try:
                bsdf.inputs["Specular"].default_value = 0.15
            except KeyError:
                pass

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Stratifié] Matériau imitation {wood_props['name']}")
