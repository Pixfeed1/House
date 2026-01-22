# =============================================================================
# GÉNÉRATEUR BÉTON CIRÉ - Mesh + Shader Intégré
# Pour Blender 4.2+
# =============================================================================
#
# Génère un sol en béton ciré réaliste avec :
#
# MESH :
# - Surface avec micro-relief
# - Joints de dilatation optionnels
# - Variations de hauteur subtiles
#
# SHADER :
# - Aspect nuageux caractéristique
# - Variations de teinte
# - Micro-fissures
# - Traces d'application
# - Usure réaliste
# - Plusieurs finitions (mat, satiné, ciré)
#
# =============================================================================

import bpy
import bmesh
import math
import random
from mathutils import Vector, noise


class MESH_OT_generate_concrete(bpy.types.Operator):
    """Générer un sol en béton ciré avec matériau"""
    bl_idname = "mesh.generate_concrete"
    bl_label = "Générer Béton Ciré"
    bl_options = {'REGISTER', 'UNDO'}

    # =================================================================
    # PROPRIÉTÉS - DIMENSIONS
    # =================================================================

    floor_width: bpy.props.FloatProperty(
        name="Largeur",
        default=5.0,
        min=1.0,
        max=50.0,
        unit='LENGTH'
    )
    floor_length: bpy.props.FloatProperty(
        name="Longueur",
        default=6.0,
        min=1.0,
        max=50.0,
        unit='LENGTH'
    )
    floor_thickness: bpy.props.FloatProperty(
        name="Épaisseur",
        default=0.08,
        min=0.02,
        max=0.20,
        unit='LENGTH'
    )

    # =================================================================
    # PROPRIÉTÉS - JOINTS
    # =================================================================

    add_joints: bpy.props.BoolProperty(
        name="Joints de Dilatation",
        default=True,
        description="Ajouter des joints de dilatation"
    )
    joint_spacing_x: bpy.props.FloatProperty(
        name="Espacement X",
        default=3.0,
        min=1.0,
        max=10.0,
        unit='LENGTH'
    )
    joint_spacing_y: bpy.props.FloatProperty(
        name="Espacement Y",
        default=3.0,
        min=1.0,
        max=10.0,
        unit='LENGTH'
    )
    joint_width: bpy.props.FloatProperty(
        name="Largeur Joint",
        default=0.005,
        min=0.002,
        max=0.02,
        unit='LENGTH'
    )
    joint_depth: bpy.props.FloatProperty(
        name="Profondeur Joint",
        default=0.003,
        min=0.001,
        max=0.01,
        unit='LENGTH'
    )

    # =================================================================
    # PROPRIÉTÉS - MESH
    # =================================================================

    subdivisions: bpy.props.IntProperty(
        name="Subdivisions",
        default=64,
        min=16,
        max=256,
        description="Détail du mesh"
    )
    surface_variation: bpy.props.FloatProperty(
        name="Ondulation Surface",
        default=0.001,
        min=0.0,
        max=0.005,
        unit='LENGTH',
        description="Légères ondulations de la surface"
    )

    # =================================================================
    # PROPRIÉTÉS - COULEUR
    # =================================================================

    color_preset: bpy.props.EnumProperty(
        name="Couleur",
        items=[
            ('GRIS_NATUREL', "Gris Naturel", "Gris béton classique"),
            ('GRIS_CLAIR', "Gris Clair", "Gris perle lumineux"),
            ('GRIS_ANTHRACITE', "Gris Anthracite", "Gris foncé élégant"),
            ('BLANC_CASSE', "Blanc Cassé", "Blanc chaud"),
            ('BEIGE', "Beige", "Ton sable chaleureux"),
            ('TAUPE', "Taupe", "Brun-gris sophistiqué"),
            ('GREIGE', "Greige", "Mélange gris-beige tendance"),
            ('NOIR', "Noir", "Noir profond"),
            ('TERRACOTTA', "Terracotta", "Ton terre cuite"),
            ('CUSTOM', "Personnalisé", "Couleur personnalisée"),
        ],
        default='GRIS_NATUREL'
    )

    custom_color: bpy.props.FloatVectorProperty(
        name="Couleur Custom",
        subtype='COLOR',
        default=(0.35, 0.33, 0.30),
        min=0.0,
        max=1.0
    )

    # =================================================================
    # PROPRIÉTÉS - FINITION
    # =================================================================

    finish_type: bpy.props.EnumProperty(
        name="Finition",
        items=[
            ('MAT', "Mat", "Finition mate naturelle"),
            ('SATINE', "Satiné", "Légèrement brillant"),
            ('CIRE', "Ciré", "Aspect ciré lustré"),
            ('HUILE', "Huilé", "Finition huilée profonde"),
        ],
        default='SATINE'
    )

    # =================================================================
    # PROPRIÉTÉS - ASPECT
    # =================================================================

    cloud_intensity: bpy.props.FloatProperty(
        name="Effet Nuageux",
        default=0.4,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        description="Variations nuageuses caractéristiques"
    )
    cloud_scale: bpy.props.FloatProperty(
        name="Échelle Nuages",
        default=2.0,
        min=0.5,
        max=8.0
    )
    color_variation: bpy.props.FloatProperty(
        name="Variation Teinte",
        default=0.15,
        min=0.0,
        max=0.4,
        subtype='FACTOR'
    )

    # =================================================================
    # PROPRIÉTÉS - IMPERFECTIONS
    # =================================================================

    micro_cracks: bpy.props.FloatProperty(
        name="Micro-fissures",
        default=0.1,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    trowel_marks: bpy.props.FloatProperty(
        name="Traces Taloche",
        default=0.3,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        description="Traces d'application à la taloche"
    )
    pitting: bpy.props.FloatProperty(
        name="Bullage",
        default=0.1,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        description="Petits trous de surface"
    )
    wear: bpy.props.FloatProperty(
        name="Usure",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        description="Usure générale (zones de passage)"
    )
    edge_wear: bpy.props.FloatProperty(
        name="Usure Bords",
        default=0.2,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        description="Usure sur les arêtes des joints"
    )

    # =================================================================
    # PROPRIÉTÉS - OPTIONS
    # =================================================================

    random_seed: bpy.props.IntProperty(
        name="Seed",
        default=42,
        min=0
    )

    def execute(self, context):
        random.seed(self.random_seed)

        # Créer le mesh
        obj = self.create_concrete_mesh(context)

        # Créer et assigner le matériau
        mat = self.create_concrete_material()
        obj.data.materials.append(mat)

        self.report({'INFO'}, "Béton ciré créé avec succès")
        return {'FINISHED'}

    # =================================================================
    # CRÉATION DU MESH
    # =================================================================

    def create_concrete_mesh(self, context):
        """Crée le mesh du sol en béton ciré"""

        bm = bmesh.new()

        # Calculer les subdivisions
        sub_x = int(self.subdivisions * (self.floor_width / max(self.floor_width, self.floor_length)))
        sub_y = int(self.subdivisions * (self.floor_length / max(self.floor_width, self.floor_length)))

        # Créer la grille de base
        bmesh.ops.create_grid(
            bm,
            x_segments=sub_x,
            y_segments=sub_y,
            size=1.0
        )

        # Redimensionner
        bmesh.ops.scale(
            bm,
            vec=(self.floor_width / 2, self.floor_length / 2, 1),
            verts=bm.verts
        )

        # Déplacer pour coin à l'origine
        bmesh.ops.translate(
            bm,
            vec=(self.floor_width / 2, self.floor_length / 2, 0),
            verts=bm.verts
        )

        # Ajouter du relief subtil
        if self.surface_variation > 0:
            for v in bm.verts:
                # Noise multi-octave pour variation naturelle
                n1 = noise.noise(Vector((v.co.x * 2, v.co.y * 2, self.random_seed)))
                n2 = noise.noise(Vector((v.co.x * 8, v.co.y * 8, self.random_seed + 100))) * 0.3
                v.co.z += (n1 + n2) * self.surface_variation

        # Joints de dilatation
        if self.add_joints:
            self.add_expansion_joints(bm)

        # Extruder pour donner l'épaisseur
        top_faces = list(bm.faces)
        result = bmesh.ops.extrude_face_region(bm, geom=top_faces)
        extruded_verts = [v for v in result['geom'] if isinstance(v, bmesh.types.BMVert)]

        bmesh.ops.translate(
            bm,
            vec=(0, 0, -self.floor_thickness),
            verts=extruded_verts
        )

        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        # Créer le mesh
        mesh = bpy.data.meshes.new("Beton_Cire")
        bm.to_mesh(mesh)
        bm.free()

        # Smooth shading
        for poly in mesh.polygons:
            poly.use_smooth = True

        # UVs automatiques
        obj = bpy.data.objects.new("Beton_Cire", mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        # Smart UV Project
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=0.785398, island_margin=0.001)
        bpy.ops.object.mode_set(mode='OBJECT')

        return obj

    def add_expansion_joints(self, bm):
        """Ajoute les joints de dilatation"""

        # Calculer les positions des joints
        joints_x = []
        x = self.joint_spacing_x
        while x < self.floor_width - 0.5:
            joints_x.append(x)
            x += self.joint_spacing_x

        joints_y = []
        y = self.joint_spacing_y
        while y < self.floor_length - 0.5:
            joints_y.append(y)
            y += self.joint_spacing_y

        # Appliquer les joints (creuser les vertices proches)
        half_width = self.joint_width / 2

        for v in bm.verts:
            # Joints en X
            for jx in joints_x:
                if abs(v.co.x - jx) < half_width:
                    dist = abs(v.co.x - jx) / half_width
                    depth = (1 - dist) * self.joint_depth
                    v.co.z -= depth

            # Joints en Y
            for jy in joints_y:
                if abs(v.co.y - jy) < half_width:
                    dist = abs(v.co.y - jy) / half_width
                    depth = (1 - dist) * self.joint_depth
                    v.co.z -= depth

    # =================================================================
    # CRÉATION DU MATÉRIAU
    # =================================================================

    def create_concrete_material(self):
        """Crée le shader de béton ciré"""

        mat = bpy.data.materials.new(name=f"Beton_Cire_{self.color_preset}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Obtenir la couleur
        base_color = self.get_base_color()
        roughness = self.get_roughness()

        x = -2000
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (300, 0)
        principled.inputs['IOR'].default_value = 1.5

        # Blender 4.2+ compatibility
        try:
            principled.inputs['Specular IOR Level'].default_value = 0.4
        except KeyError:
            try:
                principled.inputs['Specular'].default_value = 0.4
            except KeyError:
                pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (
            self.random_seed * 5.7,
            self.random_seed * 8.3,
            self.random_seed * 3.1
        )

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # === EFFET NUAGEUX (caractéristique du béton ciré) ===
        cloud_noise_1 = nodes.new('ShaderNodeTexNoise')
        cloud_noise_1.location = (x + 400, y)
        cloud_noise_1.inputs['Scale'].default_value = self.cloud_scale
        cloud_noise_1.inputs['Detail'].default_value = 6.0
        cloud_noise_1.inputs['Roughness'].default_value = 0.65
        cloud_noise_1.inputs['Distortion'].default_value = 0.8

        links.new(mapping.outputs['Vector'], cloud_noise_1.inputs['Vector'])

        cloud_noise_2 = nodes.new('ShaderNodeTexNoise')
        cloud_noise_2.location = (x + 400, y - 200)
        cloud_noise_2.inputs['Scale'].default_value = self.cloud_scale * 3
        cloud_noise_2.inputs['Detail'].default_value = 4.0
        cloud_noise_2.inputs['Roughness'].default_value = 0.5

        links.new(mapping.outputs['Vector'], cloud_noise_2.inputs['Vector'])

        # Combiner les nuages
        cloud_mix = nodes.new('ShaderNodeMix')
        cloud_mix.location = (x + 600, y - 100)
        cloud_mix.data_type = 'FLOAT'
        cloud_mix.inputs['Factor'].default_value = 0.4

        links.new(cloud_noise_1.outputs['Fac'], cloud_mix.inputs['A'])
        links.new(cloud_noise_2.outputs['Fac'], cloud_mix.inputs['B'])

        # === TRACES DE TALOCHE ===
        trowel_wave = nodes.new('ShaderNodeTexWave')
        trowel_wave.location = (x + 400, y - 400)
        trowel_wave.wave_type = 'BANDS'
        trowel_wave.bands_direction = 'DIAGONAL'
        trowel_wave.wave_profile = 'SIN'
        trowel_wave.inputs['Scale'].default_value = 15.0
        trowel_wave.inputs['Distortion'].default_value = 8.0
        trowel_wave.inputs['Detail'].default_value = 2.0
        trowel_wave.inputs['Detail Scale'].default_value = 1.0

        links.new(mapping.outputs['Vector'], trowel_wave.inputs['Vector'])

        # === MICRO-FISSURES ===
        crack_voronoi = nodes.new('ShaderNodeTexVoronoi')
        crack_voronoi.location = (x + 400, y - 600)
        crack_voronoi.voronoi_dimensions = '3D'
        crack_voronoi.feature = 'DISTANCE_TO_EDGE'
        crack_voronoi.inputs['Scale'].default_value = 8.0
        crack_voronoi.inputs['Randomness'].default_value = 1.0

        links.new(mapping.outputs['Vector'], crack_voronoi.inputs['Vector'])

        # Seuiller les fissures
        crack_ramp = nodes.new('ShaderNodeMapRange')
        crack_ramp.location = (x + 600, y - 600)
        crack_ramp.inputs['From Min'].default_value = 0.0
        crack_ramp.inputs['From Max'].default_value = 0.03
        crack_ramp.inputs['To Min'].default_value = 0.0
        crack_ramp.inputs['To Max'].default_value = 1.0
        crack_ramp.clamp = True

        links.new(crack_voronoi.outputs['Distance'], crack_ramp.inputs['Value'])

        # Inverser (fissures = sombre)
        crack_invert = nodes.new('ShaderNodeMath')
        crack_invert.location = (x + 800, y - 600)
        crack_invert.operation = 'SUBTRACT'
        crack_invert.inputs[0].default_value = 1.0

        links.new(crack_ramp.outputs['Result'], crack_invert.inputs[1])

        # === BULLAGE (petits trous) ===
        pit_voronoi = nodes.new('ShaderNodeTexVoronoi')
        pit_voronoi.location = (x + 400, y - 800)
        pit_voronoi.voronoi_dimensions = '3D'
        pit_voronoi.feature = 'F1'
        pit_voronoi.inputs['Scale'].default_value = 80.0
        pit_voronoi.inputs['Randomness'].default_value = 1.0

        links.new(mapping.outputs['Vector'], pit_voronoi.inputs['Vector'])

        pit_thresh = nodes.new('ShaderNodeMapRange')
        pit_thresh.location = (x + 600, y - 800)
        pit_thresh.inputs['From Min'].default_value = 0.0
        pit_thresh.inputs['From Max'].default_value = 0.08
        pit_thresh.clamp = True

        links.new(pit_voronoi.outputs['Distance'], pit_thresh.inputs['Value'])

        # === COULEUR DE BASE ===
        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 800, y + 300)
        base_col.outputs[0].default_value = (*base_color, 1.0)

        # Couleur plus claire pour les nuages
        light_col = nodes.new('ShaderNodeRGB')
        light_col.location = (x + 800, y + 150)
        light_color = tuple(min(1.0, c * 1.15) for c in base_color)
        light_col.outputs[0].default_value = (*light_color, 1.0)

        # Couleur plus foncée pour les creux
        dark_col = nodes.new('ShaderNodeRGB')
        dark_col.location = (x + 800, y)
        dark_color = tuple(c * 0.85 for c in base_color)
        dark_col.outputs[0].default_value = (*dark_color, 1.0)

        # === MIX COULEURS AVEC NUAGES ===
        # Intensité des nuages
        cloud_intensity_mult = nodes.new('ShaderNodeMath')
        cloud_intensity_mult.location = (x + 800, y - 100)
        cloud_intensity_mult.operation = 'MULTIPLY'
        cloud_intensity_mult.inputs[1].default_value = self.cloud_intensity

        links.new(cloud_mix.outputs['Result'], cloud_intensity_mult.inputs[0])

        # Mix base avec light (nuages clairs)
        color_mix_1 = nodes.new('ShaderNodeMix')
        color_mix_1.location = (x + 1000, y + 200)
        color_mix_1.data_type = 'RGBA'

        links.new(cloud_intensity_mult.outputs['Value'], color_mix_1.inputs['Factor'])
        links.new(base_col.outputs[0], color_mix_1.inputs['A'])
        links.new(light_col.outputs[0], color_mix_1.inputs['B'])

        # Ajouter variation de teinte
        color_var_noise = nodes.new('ShaderNodeTexNoise')
        color_var_noise.location = (x + 800, y + 500)
        color_var_noise.inputs['Scale'].default_value = 1.5
        color_var_noise.inputs['Detail'].default_value = 3.0

        links.new(mapping.outputs['Vector'], color_var_noise.inputs['Vector'])

        color_var_mix = nodes.new('ShaderNodeMix')
        color_var_mix.location = (x + 1200, y + 300)
        color_var_mix.data_type = 'RGBA'
        color_var_mix.blend_type = 'OVERLAY'
        color_var_mix.inputs['Factor'].default_value = self.color_variation

        links.new(color_mix_1.outputs['Result'], color_var_mix.inputs['A'])
        links.new(color_var_noise.outputs['Color'], color_var_mix.inputs['B'])

        # === ASSOMBRIR AVEC FISSURES ===
        crack_darken = nodes.new('ShaderNodeMath')
        crack_darken.location = (x + 1000, y - 600)
        crack_darken.operation = 'MULTIPLY'
        crack_darken.inputs[1].default_value = self.micro_cracks * 0.3

        links.new(crack_invert.outputs['Value'], crack_darken.inputs[0])

        color_with_cracks = nodes.new('ShaderNodeMix')
        color_with_cracks.location = (x + 1400, y + 200)
        color_with_cracks.data_type = 'RGBA'

        links.new(crack_darken.outputs['Value'], color_with_cracks.inputs['Factor'])
        links.new(color_var_mix.outputs['Result'], color_with_cracks.inputs['A'])
        links.new(dark_col.outputs[0], color_with_cracks.inputs['B'])

        links.new(color_with_cracks.outputs['Result'], principled.inputs['Base Color'])

        # === ROUGHNESS ===
        # Base roughness
        rough_noise = nodes.new('ShaderNodeTexNoise')
        rough_noise.location = (x + 1000, y - 300)
        rough_noise.inputs['Scale'].default_value = 30.0
        rough_noise.inputs['Detail'].default_value = 6.0

        links.new(mapping.outputs['Vector'], rough_noise.inputs['Vector'])

        # Variation de roughness
        rough_var = 0.08
        rough_map = nodes.new('ShaderNodeMapRange')
        rough_map.location = (x + 1200, y - 300)
        rough_map.inputs['From Min'].default_value = 0.3
        rough_map.inputs['From Max'].default_value = 0.7
        rough_map.inputs['To Min'].default_value = roughness - rough_var
        rough_map.inputs['To Max'].default_value = roughness + rough_var

        links.new(rough_noise.outputs['Fac'], rough_map.inputs['Value'])

        # Ajouter roughness des traces de taloche
        trowel_rough = nodes.new('ShaderNodeMath')
        trowel_rough.location = (x + 1200, y - 450)
        trowel_rough.operation = 'MULTIPLY'
        trowel_rough.inputs[1].default_value = self.trowel_marks * 0.1

        links.new(trowel_wave.outputs['Fac'], trowel_rough.inputs[0])

        rough_add = nodes.new('ShaderNodeMath')
        rough_add.location = (x + 1400, y - 350)
        rough_add.operation = 'ADD'
        rough_add.use_clamp = True

        links.new(rough_map.outputs['Result'], rough_add.inputs[0])
        links.new(trowel_rough.outputs['Value'], rough_add.inputs[1])

        links.new(rough_add.outputs['Value'], principled.inputs['Roughness'])

        # === BUMP / NORMAL ===
        # Bump principal (nuages + taloche)
        bump_mix = nodes.new('ShaderNodeMath')
        bump_mix.location = (x + 1000, y - 150)
        bump_mix.operation = 'ADD'

        # Nuages
        cloud_bump_mult = nodes.new('ShaderNodeMath')
        cloud_bump_mult.location = (x + 800, y - 50)
        cloud_bump_mult.operation = 'MULTIPLY'
        cloud_bump_mult.inputs[1].default_value = self.cloud_intensity * 0.5

        links.new(cloud_mix.outputs['Result'], cloud_bump_mult.inputs[0])

        # Taloche
        trowel_bump_mult = nodes.new('ShaderNodeMath')
        trowel_bump_mult.location = (x + 800, y - 150)
        trowel_bump_mult.operation = 'MULTIPLY'
        trowel_bump_mult.inputs[1].default_value = self.trowel_marks * 0.3

        links.new(trowel_wave.outputs['Fac'], trowel_bump_mult.inputs[0])

        links.new(cloud_bump_mult.outputs['Value'], bump_mix.inputs[0])
        links.new(trowel_bump_mult.outputs['Value'], bump_mix.inputs[1])

        bump_main = nodes.new('ShaderNodeBump')
        bump_main.location = (x + 1200, y - 100)
        bump_main.inputs['Strength'].default_value = 0.15

        links.new(bump_mix.outputs['Value'], bump_main.inputs['Height'])

        # Bump fissures
        if self.micro_cracks > 0:
            crack_bump = nodes.new('ShaderNodeBump')
            crack_bump.location = (x + 1400, y - 100)
            crack_bump.inputs['Strength'].default_value = self.micro_cracks * 0.2
            crack_bump.invert = True

            links.new(crack_invert.outputs['Value'], crack_bump.inputs['Height'])
            links.new(bump_main.outputs['Normal'], crack_bump.inputs['Normal'])

            current_normal = crack_bump.outputs['Normal']
        else:
            current_normal = bump_main.outputs['Normal']

        # Bump bullage
        if self.pitting > 0:
            pit_bump = nodes.new('ShaderNodeBump')
            pit_bump.location = (x + 1600, y - 100)
            pit_bump.inputs['Strength'].default_value = self.pitting * 0.3
            pit_bump.invert = True

            links.new(pit_thresh.outputs['Result'], pit_bump.inputs['Height'])
            links.new(current_normal, pit_bump.inputs['Normal'])

            current_normal = pit_bump.outputs['Normal']

        links.new(current_normal, principled.inputs['Normal'])

        return mat

    # =================================================================
    # UTILITAIRES
    # =================================================================

    def get_base_color(self):
        """Retourne la couleur de base selon le preset"""

        colors = {
            'GRIS_NATUREL': (0.35, 0.33, 0.30),
            'GRIS_CLAIR': (0.55, 0.53, 0.50),
            'GRIS_ANTHRACITE': (0.15, 0.14, 0.13),
            'BLANC_CASSE': (0.75, 0.72, 0.68),
            'BEIGE': (0.55, 0.48, 0.38),
            'TAUPE': (0.35, 0.30, 0.25),
            'GREIGE': (0.45, 0.42, 0.38),
            'NOIR': (0.05, 0.05, 0.05),
            'TERRACOTTA': (0.50, 0.32, 0.22),
            'CUSTOM': self.custom_color[:],
        }

        return colors.get(self.color_preset, (0.35, 0.33, 0.30))

    def get_roughness(self):
        """Retourne la roughness selon la finition"""

        roughness_values = {
            'MAT': 0.55,
            'SATINE': 0.35,
            'CIRE': 0.20,
            'HUILE': 0.28,
        }

        return roughness_values.get(self.finish_type, 0.35)

    # =================================================================
    # UI
    # =================================================================

    def draw(self, context):
        layout = self.layout

        # Dimensions
        box = layout.box()
        box.label(text="Dimensions", icon='MESH_PLANE')
        row = box.row()
        row.prop(self, "floor_width")
        row.prop(self, "floor_length")
        box.prop(self, "floor_thickness")
        box.prop(self, "subdivisions")
        box.prop(self, "surface_variation")

        # Joints
        box = layout.box()
        box.label(text="Joints de Dilatation", icon='MESH_GRID')
        box.prop(self, "add_joints")
        if self.add_joints:
            row = box.row()
            row.prop(self, "joint_spacing_x")
            row.prop(self, "joint_spacing_y")
            row = box.row()
            row.prop(self, "joint_width")
            row.prop(self, "joint_depth")

        # Couleur
        box = layout.box()
        box.label(text="Couleur", icon='COLOR')
        box.prop(self, "color_preset")
        if self.color_preset == 'CUSTOM':
            box.prop(self, "custom_color")

        # Finition
        box = layout.box()
        box.label(text="Finition", icon='MATSPHERE')
        box.prop(self, "finish_type")

        # Aspect
        box = layout.box()
        box.label(text="Aspect", icon='NODE_TEXTURE')
        box.prop(self, "cloud_intensity")
        box.prop(self, "cloud_scale")
        box.prop(self, "color_variation")

        # Imperfections
        box = layout.box()
        box.label(text="Imperfections", icon='MOD_NOISE')
        box.prop(self, "trowel_marks")
        box.prop(self, "micro_cracks")
        box.prop(self, "pitting")
        row = box.row()
        row.prop(self, "wear")
        row.prop(self, "edge_wear")

        # Options
        box = layout.box()
        box.label(text="Options", icon='PREFERENCES')
        box.prop(self, "random_seed")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380)


# =============================================================================
# PANEL
# =============================================================================

class VIEW3D_PT_concrete_panel(bpy.types.Panel):
    bl_label = "Béton Ciré"
    bl_idname = "VIEW3D_PT_concrete"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Béton"

    def draw(self, context):
        layout = self.layout
        layout.operator("mesh.generate_concrete", text="Générer Béton Ciré", icon='MESH_PLANE')


# =============================================================================
# MENU
# =============================================================================

def menu_func(self, context):
    self.layout.operator(MESH_OT_generate_concrete.bl_idname, icon='MESH_PLANE')


# =============================================================================
# REGISTRATION
# =============================================================================

classes = [
    MESH_OT_generate_concrete,
    VIEW3D_PT_concrete_panel,
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
    print("=" * 60)
    print("✅ GÉNÉRATEUR BÉTON CIRÉ (MESH + MATÉRIAU)")
    print("=" * 60)
    print("📍 Menu: Add > Mesh > Générer Béton Ciré")
    print("📍 Panel: Sidebar (N) > Béton")
    print("")
    print("MESH :")
    print("  • Surface avec micro-relief")
    print("  • Joints de dilatation optionnels")
    print("  • UVs automatiques")
    print("")
    print("COULEURS :")
    print("  • Gris Naturel, Clair, Anthracite")
    print("  • Blanc Cassé, Beige, Taupe, Greige")
    print("  • Noir, Terracotta")
    print("  • Personnalisé")
    print("")
    print("FINITIONS :")
    print("  • Mat, Satiné, Ciré, Huilé")
    print("")
    print("CARACTÉRISTIQUES :")
    print("  • Effet nuageux réaliste")
    print("  • Traces de taloche")
    print("  • Micro-fissures")
    print("  • Bullage (petits trous)")
    print("=" * 60)
