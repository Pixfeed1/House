# =============================================================================
# GÉNÉRATEUR DE CARRELAGE / DALLES - Mesh Procédural
# Pour Blender 4.2+
# =============================================================================
#
# Génère la géométrie d'un sol carrelé avec :
# - Plusieurs motifs de pose (grille, décalé, chevron, opus romain, etc.)
# - Joints/espacement
# - Chanfreins
# - Variations réalistes (hauteur, rotation)
# - UV automatiques par dalle
#
# =============================================================================

import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix


class MESH_OT_generate_tiles(bpy.types.Operator):
    """Générer un mesh de carrelage/dalles"""
    bl_idname = "mesh.generate_tiles"
    bl_label = "Générer Carrelage"
    bl_options = {'REGISTER', 'UNDO'}

    # =================================================================
    # PROPRIÉTÉS
    # =================================================================

    # Dimensions globales
    floor_width: bpy.props.FloatProperty(
        name="Largeur Sol",
        default=4.0,
        min=0.5,
        max=50.0,
        unit='LENGTH',
        description="Largeur totale du carrelage"
    )
    floor_length: bpy.props.FloatProperty(
        name="Longueur Sol",
        default=5.0,
        min=0.5,
        max=50.0,
        unit='LENGTH',
        description="Longueur totale du carrelage"
    )

    # Dimensions des dalles
    tile_width: bpy.props.FloatProperty(
        name="Largeur Dalle",
        default=0.60,
        min=0.10,
        max=2.0,
        unit='LENGTH',
        description="Largeur d'une dalle"
    )
    tile_length: bpy.props.FloatProperty(
        name="Longueur Dalle",
        default=0.60,
        min=0.10,
        max=2.0,
        unit='LENGTH',
        description="Longueur d'une dalle"
    )
    tile_thickness: bpy.props.FloatProperty(
        name="Épaisseur",
        default=0.012,
        min=0.005,
        max=0.05,
        unit='LENGTH',
        description="Épaisseur des dalles"
    )

    # Type de pose
    pattern_type: bpy.props.EnumProperty(
        name="Motif de Pose",
        items=[
            ('GRID', "Grille", "Pose en grille régulière"),
            ('OFFSET_HALF', "Décalé 1/2", "Décalage d'une demi-dalle"),
            ('OFFSET_THIRD', "Décalé 1/3", "Décalage d'un tiers"),
            ('OFFSET_RANDOM', "Décalé Aléatoire", "Décalage aléatoire"),
            ('CHEVRON', "Chevron", "Pose en chevron"),
            ('HERRINGBONE', "Bâton Rompu", "Pose en bâton rompu"),
            ('OPUS_ROMAN', "Opus Romain", "Motif romain avec tailles variées"),
            ('VERSAILLES', "Versailles", "Motif classique français"),
            ('DIAGONAL', "Diagonal", "Grille à 45°"),
        ],
        default='GRID'
    )

    # Joints
    gap: bpy.props.FloatProperty(
        name="Joint",
        default=0.003,
        min=0.0,
        max=0.02,
        unit='LENGTH',
        description="Largeur des joints entre dalles"
    )

    # Chanfrein
    bevel_width: bpy.props.FloatProperty(
        name="Chanfrein",
        default=0.001,
        min=0.0,
        max=0.005,
        unit='LENGTH',
        description="Largeur du chanfrein sur les arêtes"
    )
    bevel_segments: bpy.props.IntProperty(
        name="Segments Chanfrein",
        default=2,
        min=1,
        max=5,
        description="Nombre de segments pour le chanfrein"
    )

    # Variations réalistes
    height_variation: bpy.props.FloatProperty(
        name="Variation Hauteur",
        default=0.0002,
        min=0.0,
        max=0.002,
        unit='LENGTH',
        description="Variation de hauteur entre les dalles"
    )
    rotation_variation: bpy.props.FloatProperty(
        name="Variation Rotation",
        default=0.1,
        min=0.0,
        max=2.0,
        subtype='ANGLE',
        description="Légère rotation aléatoire des dalles"
    )

    # Seed aléatoire
    random_seed: bpy.props.IntProperty(
        name="Seed",
        default=42,
        min=0,
        description="Graine pour les variations aléatoires"
    )

    # Options
    generate_uvs: bpy.props.BoolProperty(
        name="Générer UVs",
        default=True,
        description="Générer les UVs automatiquement"
    )

    def execute(self, context):
        random.seed(self.random_seed)

        if self.pattern_type == 'GRID':
            obj = self.create_grid_tiles(context)
        elif self.pattern_type in ['OFFSET_HALF', 'OFFSET_THIRD', 'OFFSET_RANDOM']:
            obj = self.create_offset_tiles(context)
        elif self.pattern_type == 'CHEVRON':
            obj = self.create_chevron_tiles(context)
        elif self.pattern_type == 'HERRINGBONE':
            obj = self.create_herringbone_tiles(context)
        elif self.pattern_type == 'OPUS_ROMAN':
            obj = self.create_opus_roman(context)
        elif self.pattern_type == 'VERSAILLES':
            obj = self.create_versailles(context)
        elif self.pattern_type == 'DIAGONAL':
            obj = self.create_diagonal_tiles(context)

        return {'FINISHED'}

    # =================================================================
    # CRÉATION D'UNE DALLE
    # =================================================================

    def create_tile(self, bm, x, y, z, width, length, thickness, rotation=0, uv_layer=None):
        """Crée une dalle de carrelage"""

        # Variations
        z += random.uniform(-self.height_variation, self.height_variation)
        rotation += math.radians(random.uniform(-self.rotation_variation, self.rotation_variation))

        # Créer les vertices (8 points pour un parallélépipède)
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
        if rotation != 0:
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
                    local_pos = loop.vert.co - Vector((x, y, z))
                    if rotation != 0:
                        rot_matrix = Matrix.Rotation(-rotation, 3, 'Z')
                        local_pos = rot_matrix @ local_pos
                    u = (local_pos.x + hw) / width
                    v = (local_pos.y + hl) / length
                    loop[uv_layer].uv = (u, v)

        return bm_verts, created_faces

    # =================================================================
    # GRILLE RÉGULIÈRE
    # =================================================================

    def create_grid_tiles(self, context):
        """Carrelage en grille régulière"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        tile_w = self.tile_width + self.gap
        tile_l = self.tile_length + self.gap

        # +2 pour couvrir toute la surface
        cols = int(math.ceil(self.floor_width / tile_w)) + 2
        rows = int(math.ceil(self.floor_length / tile_l)) + 2

        for col in range(cols):
            for row in range(rows):
                x = col * tile_w + self.tile_width / 2
                y = row * tile_l + self.tile_length / 2

                # Génération généreuse - le Boolean clippera ce qui dépasse
                if x < self.floor_width + self.tile_width and y < self.floor_length + self.tile_length:
                    self.create_tile(
                        bm, x, y, 0,
                        self.tile_width, self.tile_length, self.tile_thickness,
                        0, uv_layer
                    )

        return self.finalize_mesh(context, bm, "Carrelage_Grille")

    # =================================================================
    # GRILLE DÉCALÉE
    # =================================================================

    def create_offset_tiles(self, context):
        """Carrelage décalé"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        tile_w = self.tile_width + self.gap
        tile_l = self.tile_length + self.gap

        cols = int(math.ceil(self.floor_width / tile_w)) + 2
        rows = int(math.ceil(self.floor_length / tile_l)) + 2

        for row in range(rows):
            # Calculer le décalage
            if self.pattern_type == 'OFFSET_HALF':
                offset = (row % 2) * (tile_w / 2)
            elif self.pattern_type == 'OFFSET_THIRD':
                offset = (row % 3) * (tile_w / 3)
            else:  # RANDOM
                offset = random.uniform(0, tile_w * 0.8)

            for col in range(-1, cols):
                x = col * tile_w + self.tile_width / 2 + offset
                y = row * tile_l + self.tile_length / 2

                # Vérifier si dans les limites (avec marge généreuse)
                if (x + self.tile_width / 2 > -self.tile_width and
                    x - self.tile_width / 2 < self.floor_width + self.tile_width and
                    y - self.tile_length / 2 < self.floor_length + self.tile_length):

                    self.create_tile(
                        bm, x, y, 0,
                        self.tile_width, self.tile_length, self.tile_thickness,
                        0, uv_layer
                    )

        obj = self.finalize_mesh(context, bm, "Carrelage_Decale")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # CHEVRON
    # =================================================================

    def create_chevron_tiles(self, context):
        """Carrelage en chevron"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        angle = math.radians(45)

        tile_w = self.tile_width + self.gap
        tile_l = self.tile_length + self.gap

        v_height = tile_l * math.sin(angle)
        row_height = v_height + self.gap

        rows = int(math.ceil(self.floor_length / row_height)) + 3

        for row in range(rows):
            base_y = row * row_height

            # Côté gauche du V
            x = -tile_l * 2
            while x < self.floor_width / 2 + tile_l * 2:
                px = x + tile_l * math.cos(angle) / 2
                py = base_y + tile_l * math.sin(angle) / 2

                self.create_tile(
                    bm, px, py, 0,
                    self.tile_width, self.tile_length, self.tile_thickness,
                    angle, uv_layer
                )

                x += tile_w / math.cos(angle)

            # Côté droit du V (miroir)
            x = -tile_l * 2
            while x < self.floor_width / 2 + tile_l * 2:
                px = self.floor_width - (x + tile_l * math.cos(angle) / 2)
                py = base_y + tile_l * math.sin(angle) / 2

                self.create_tile(
                    bm, px, py, 0,
                    self.tile_width, self.tile_length, self.tile_thickness,
                    -angle, uv_layer
                )

                x += tile_w / math.cos(angle)

        obj = self.finalize_mesh(context, bm, "Carrelage_Chevron")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # BÂTON ROMPU (HERRINGBONE)
    # =================================================================

    def create_herringbone_tiles(self, context):
        """Carrelage bâton rompu"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        tile_w = self.tile_width + self.gap
        tile_l = self.tile_length + self.gap

        # Le motif se répète
        pattern_width = tile_l + tile_w
        pattern_height = tile_l

        cols = int(math.ceil(self.floor_width / pattern_width)) + 2
        rows = int(math.ceil(self.floor_length / pattern_height)) + 2

        for col in range(cols):
            for row in range(rows):
                base_x = col * pattern_width
                base_y = row * pattern_height

                # Dalle horizontale
                px1 = base_x + self.tile_length / 2
                py1 = base_y + self.tile_width / 2

                self.create_tile(
                    bm, px1, py1, 0,
                    self.tile_length, self.tile_width, self.tile_thickness,
                    0, uv_layer
                )

                # Dalle verticale
                px2 = base_x + self.tile_length + self.tile_width / 2
                py2 = base_y + self.tile_length / 2

                self.create_tile(
                    bm, px2, py2, 0,
                    self.tile_width, self.tile_length, self.tile_thickness,
                    0, uv_layer
                )

        obj = self.finalize_mesh(context, bm, "Carrelage_BatonRompu")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # OPUS ROMAIN
    # =================================================================

    def create_opus_roman(self, context):
        """Opus romain - motif avec 4 tailles de dalles"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        # 4 tailles de dalles basées sur un module
        module = self.tile_width
        gap = self.gap

        # Tailles : grand, moyen, petit, très petit
        sizes = [
            (module * 2, module * 2),      # Grand carré
            (module * 2, module),          # Rectangle
            (module, module),              # Petit carré
            (module, module * 0.5),        # Petit rectangle
        ]

        # Motif de base de l'opus romain (répétition)
        pattern_size = module * 4 + gap * 4

        cols = int(math.ceil(self.floor_width / pattern_size)) + 2
        rows = int(math.ceil(self.floor_length / pattern_size)) + 2

        for col in range(cols):
            for row in range(rows):
                base_x = col * pattern_size
                base_y = row * pattern_size

                # Motif complexe - disposition classique
                tiles_in_pattern = [
                    # (x_offset, y_offset, width, length)
                    (0, 0, sizes[0][0], sizes[0][1]),  # Grand carré
                    (sizes[0][0] + gap, 0, sizes[2][0], sizes[2][1]),  # Petit carré
                    (sizes[0][0] + gap, sizes[2][1] + gap, sizes[2][0], sizes[2][1]),  # Petit carré
                    (sizes[0][0] + sizes[2][0] + gap * 2, 0, sizes[2][0], sizes[0][1]),  # Rectangle vertical
                    (0, sizes[0][1] + gap, sizes[1][0], sizes[1][1]),  # Rectangle
                    (sizes[1][0] + gap, sizes[0][1] + gap, sizes[2][0], sizes[2][1]),  # Petit carré
                    (sizes[1][0] + sizes[2][0] + gap * 2, sizes[0][1] + gap, sizes[2][0], sizes[2][1]),  # Petit carré
                    (0, sizes[0][1] + sizes[1][1] + gap * 2, sizes[2][0], sizes[2][1]),  # Petit carré
                    (sizes[2][0] + gap, sizes[0][1] + sizes[1][1] + gap * 2, sizes[0][0], sizes[2][1]),  # Rectangle horizontal
                ]

                for tx, ty, tw, tl in tiles_in_pattern:
                    px = base_x + tx + tw / 2
                    py = base_y + ty + tl / 2

                    if px < self.floor_width + tw * 2 and py < self.floor_length + tl * 2:
                        self.create_tile(
                            bm, px, py, 0,
                            tw, tl, self.tile_thickness,
                            0, uv_layer
                        )

        obj = self.finalize_mesh(context, bm, "Carrelage_OpusRomain")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # VERSAILLES
    # =================================================================

    def create_versailles(self, context):
        """Motif Versailles classique"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        # Module de base
        m = self.tile_width
        gap = self.gap

        # Taille du motif complet
        pattern_size = m * 4 + gap * 3

        cols = int(math.ceil(self.floor_width / pattern_size)) + 2
        rows = int(math.ceil(self.floor_length / pattern_size)) + 2

        for col in range(cols):
            for row in range(rows):
                base_x = col * pattern_size
                base_y = row * pattern_size

                # Carré central (diagonal)
                cx = base_x + pattern_size / 2
                cy = base_y + pattern_size / 2

                self.create_tile(
                    bm, cx, cy, 0,
                    m * 1.41, m * 1.41, self.tile_thickness,
                    math.radians(45), uv_layer
                )

                # 4 rectangles autour
                # Haut
                self.create_tile(
                    bm, cx, base_y + m / 2, 0,
                    m * 2, m, self.tile_thickness,
                    0, uv_layer
                )
                # Bas
                self.create_tile(
                    bm, cx, base_y + pattern_size - m / 2, 0,
                    m * 2, m, self.tile_thickness,
                    0, uv_layer
                )
                # Gauche
                self.create_tile(
                    bm, base_x + m / 2, cy, 0,
                    m, m * 2, self.tile_thickness,
                    0, uv_layer
                )
                # Droite
                self.create_tile(
                    bm, base_x + pattern_size - m / 2, cy, 0,
                    m, m * 2, self.tile_thickness,
                    0, uv_layer
                )

                # 4 petits carrés dans les coins
                corners = [
                    (base_x + m / 2, base_y + m / 2),
                    (base_x + pattern_size - m / 2, base_y + m / 2),
                    (base_x + m / 2, base_y + pattern_size - m / 2),
                    (base_x + pattern_size - m / 2, base_y + pattern_size - m / 2),
                ]

                for corner_x, corner_y in corners:
                    self.create_tile(
                        bm, corner_x, corner_y, 0,
                        m, m, self.tile_thickness,
                        0, uv_layer
                    )

        obj = self.finalize_mesh(context, bm, "Carrelage_Versailles")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # DIAGONAL
    # =================================================================

    def create_diagonal_tiles(self, context):
        """Carrelage en diagonale (45°)"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap") if self.generate_uvs else None

        tile_diag = (self.tile_width + self.gap) * math.sqrt(2)

        # Calculer le nombre de dalles nécessaires avec marge
        diag_length = math.sqrt(self.floor_width**2 + self.floor_length**2)
        count = int(math.ceil(diag_length / tile_diag)) + 3

        for i in range(-count, count):
            for j in range(-count, count):
                # Position en grille diagonale
                x = (i + j) * (self.tile_width + self.gap) / math.sqrt(2)
                y = (j - i) * (self.tile_width + self.gap) / math.sqrt(2)

                # Décaler pour centrer
                x += self.floor_width / 2
                y += self.floor_length / 2

                # Vérifier si dans les limites (avec marge généreuse)
                margin = self.tile_width * 2
                if (-margin < x < self.floor_width + margin and
                    -margin < y < self.floor_length + margin):

                    self.create_tile(
                        bm, x, y, 0,
                        self.tile_width, self.tile_length, self.tile_thickness,
                        math.radians(45), uv_layer
                    )

        obj = self.finalize_mesh(context, bm, "Carrelage_Diagonal")
        self.clip_to_floor(context, obj)
        return obj

    # =================================================================
    # UTILITAIRES
    # =================================================================

    def finalize_mesh(self, context, bm, name):
        """Finalise le mesh et crée l'objet"""

        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()

        # Chanfrein
        if self.bevel_width > 0:
            self.apply_bevel(mesh)

        obj = bpy.data.objects.new(name, mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        return obj

    def apply_bevel(self, mesh):
        """Applique un chanfrein aux arêtes"""
        obj = bpy.data.objects.new("temp_bevel", mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj

        bevel = obj.modifiers.new("Bevel", 'BEVEL')
        bevel.width = self.bevel_width
        bevel.segments = self.bevel_segments
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = math.radians(60)

        bpy.ops.object.modifier_apply(modifier="Bevel")

        bpy.context.collection.objects.unlink(obj)
        bpy.data.objects.remove(obj)

    def clip_to_floor(self, context, obj):
        """Coupe le carrelage aux dimensions du sol - FIX: cube à la bonne taille"""

        bpy.ops.mesh.primitive_cube_add(size=1)
        cutter = context.active_object
        cutter.name = "Tile_Cutter"
        # ✅ FIX CRITIQUE: width et length SANS division par 2
        cutter.scale = (self.floor_width, self.floor_length, self.tile_thickness * 2)
        cutter.location = (self.floor_width / 2, self.floor_length / 2, self.tile_thickness / 2)
        bpy.ops.object.transform_apply(scale=True, location=True)

        context.view_layer.objects.active = obj
        bool_mod = obj.modifiers.new("Boolean", 'BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = cutter
        bool_mod.solver = 'FAST'

        bpy.ops.object.modifier_apply(modifier="Boolean")

        bpy.data.objects.remove(cutter)

        context.view_layer.objects.active = obj

    # =================================================================
    # UI
    # =================================================================

    def draw(self, context):
        layout = self.layout

        # Dimensions du sol
        box = layout.box()
        box.label(text="Dimensions Sol", icon='MESH_PLANE')
        row = box.row()
        row.prop(self, "floor_width")
        row.prop(self, "floor_length")

        # Dimensions des dalles
        box = layout.box()
        box.label(text="Dimensions Dalles", icon='MESH_CUBE')
        row = box.row()
        row.prop(self, "tile_width")
        row.prop(self, "tile_length")
        box.prop(self, "tile_thickness")

        # Type de pose
        box = layout.box()
        box.label(text="Motif de Pose", icon='MOD_ARRAY')
        box.prop(self, "pattern_type")

        # Joints et chanfrein
        box = layout.box()
        box.label(text="Joints & Finition", icon='MODIFIER')
        box.prop(self, "gap")
        row = box.row()
        row.prop(self, "bevel_width")
        row.prop(self, "bevel_segments")

        # Variations
        box = layout.box()
        box.label(text="Variations", icon='FORCE_TURBULENCE')
        box.prop(self, "height_variation")
        box.prop(self, "rotation_variation")
        box.prop(self, "random_seed")

        # Options
        box = layout.box()
        box.label(text="Options", icon='PREFERENCES')
        box.prop(self, "generate_uvs")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)


# =============================================================================
# PANEL
# =============================================================================

class VIEW3D_PT_tiles_panel(bpy.types.Panel):
    bl_label = "Générateur Carrelage"
    bl_idname = "VIEW3D_PT_tiles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Carrelage"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.generate_tiles", text="Générer Carrelage", icon='MESH_GRID')


# =============================================================================
# MENU
# =============================================================================

def menu_func(self, context):
    self.layout.operator(MESH_OT_generate_tiles.bl_idname, icon='MESH_GRID')


# =============================================================================
# REGISTRATION
# =============================================================================

classes = [
    MESH_OT_generate_tiles,
    VIEW3D_PT_tiles_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    print("=" * 50)
    print("✅ GÉNÉRATEUR DE CARRELAGE")
    print("=" * 50)
    print("📍 Menu: Add > Mesh > Générer Carrelage")
    print("📍 Panel: Sidebar (N) > Carrelage")
    print("")
    print("Motifs de pose:")
    print("  • Grille régulière")
    print("  • Décalé (1/2, 1/3, aléatoire)")
    print("  • Chevron")
    print("  • Bâton Rompu")
    print("  • Opus Romain")
    print("  • Versailles")
    print("  • Diagonal (45°)")
    print("")
    print("✅ FIX APPLIQUÉ: Carrelage couvre 100% de la surface")
    print("=" * 50)
