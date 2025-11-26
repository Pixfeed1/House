# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Pierre de Parement Extérieur (BLENDER 4.2+ COMPATIBLE)
#  Copyright (C) 2025 mvaertan
#
#  Pierre de parement avec mesh détaillé + shader réaliste
#  Types de pose : Assisé régulier, Irrégulier, Opus incertum, Moellons, Pierre sèche
#  Types de pierre : Calcaire, Granit, Grès, Ardoise, Meulière, Pierre de Taille
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, noise


class ExteriorPierreParement:
    """Générateur de pierre de parement pour façades extérieures"""

    def __init__(self,
                 wall_width=5.0,
                 wall_height=2.5,
                 wall_thickness=0.25,
                 layout_type='ASSISE_REGULIER',
                 stone_height=0.15,
                 stone_width_min=0.20,
                 stone_width_max=0.45,
                 stone_depth=0.015,
                 joint_width=0.015,
                 joint_depth=0.008,
                 stone_type='CALCAIRE',
                 custom_color=(0.72, 0.68, 0.60),
                 color_variation=0.35,
                 brightness_variation=0.3,
                 texture_variation=0.4,
                 vein_amount=0.2,
                 weathering=0.2,
                 moss=0.0,
                 dirt=0.1,
                 random_seed=42):
        """
        Initialise le générateur de pierre de parement.

        Args:
            wall_width: Largeur du mur
            wall_height: Hauteur du mur
            wall_thickness: Épaisseur du parement
            layout_type: Type de pose (ASSISE_REGULIER, ASSISE_IRREGULIER, OPUS_INCERTUM, MOELLONS, PIERRE_SECHE)
            stone_height: Hauteur des pierres
            stone_width_min: Largeur minimum des pierres
            stone_width_max: Largeur maximum des pierres
            stone_depth: Relief des pierres
            joint_width: Largeur des joints
            joint_depth: Profondeur des joints
            stone_type: Type de pierre (CALCAIRE, GRANIT, GRES, ARDOISE, etc.)
            custom_color: Couleur custom si CUSTOM
            color_variation: Variation de teinte entre pierres
            brightness_variation: Variation de luminosité entre pierres
            texture_variation: Variation de rugosité entre pierres
            vein_amount: Intensité des veines
            weathering: Patine/vieillissement
            moss: Mousse et lichen
            dirt: Salissures
            random_seed: Seed aléatoire
        """
        self.wall_width = wall_width
        self.wall_height = wall_height
        self.wall_thickness = wall_thickness
        self.layout_type = layout_type
        self.stone_height = stone_height
        self.stone_width_min = stone_width_min
        self.stone_width_max = stone_width_max
        self.stone_depth = stone_depth
        self.joint_width = joint_width
        self.joint_depth = joint_depth
        self.stone_type = stone_type
        self.custom_color = custom_color
        self.color_variation = color_variation
        self.brightness_variation = brightness_variation
        self.texture_variation = texture_variation
        self.vein_amount = vein_amount
        self.weathering = weathering
        self.moss = moss
        self.dirt = dirt
        self.random_seed = random_seed

        print(f"[ExteriorPierreParement] Type: {layout_type}, Pierre: {stone_type}")

    def generate_for_wall(self, wall_obj, collection):
        """
        Génère le parement pierre pour un mur existant ou crée un nouveau mur.

        Args:
            wall_obj: Objet mur existant (ou None pour créer nouveau)
            collection: Collection Blender où créer les objets

        Returns:
            Objet Blender avec le parement appliqué
        """
        random.seed(self.random_seed)

        # Si le mur existe (briques 3D ou mur simple), on applique juste le matériau
        if wall_obj and wall_obj.data:
            print(f"[ExteriorPierreParement] Application sur mur existant")
            mat = self.create_stone_material()

            # Remplacer le matériau
            if len(wall_obj.data.materials) > 0:
                wall_obj.data.materials[0] = mat
            else:
                wall_obj.data.materials.append(mat)

            return wall_obj

        # Sinon, créer le mesh de pierre de parement
        print(f"[ExteriorPierreParement] Création mesh pierre")
        obj = self.create_stone_wall_mesh(collection)

        mat = self.create_stone_material()
        obj.data.materials.append(mat)

        return obj

    # =================================================================
    # CRÉATION DU MESH
    # =================================================================

    def create_stone_wall_mesh(self, collection):
        """Crée le mesh du mur en pierre"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")

        if self.layout_type == 'ASSISE_REGULIER':
            self.create_regular_courses(bm, uv_layer)
        elif self.layout_type == 'ASSISE_IRREGULIER':
            self.create_irregular_courses(bm, uv_layer)
        elif self.layout_type == 'OPUS_INCERTUM':
            self.create_opus_incertum(bm, uv_layer)
        elif self.layout_type == 'MOELLONS':
            self.create_moellons(bm, uv_layer)
        elif self.layout_type == 'PIERRE_SECHE':
            self.create_dry_stone(bm, uv_layer)

        # Créer le mesh
        mesh_name = f"Pierre_{self.stone_type}_{self.layout_type}"
        mesh = bpy.data.meshes.new(mesh_name)
        bm.to_mesh(mesh)
        bm.free()

        # Créer l'objet
        obj = bpy.data.objects.new(mesh_name, mesh)
        collection.objects.link(obj)

        # Smooth shading
        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    def create_regular_courses(self, bm, uv_layer):
        """Assisé régulier - rangées de même hauteur"""

        course_height = self.stone_height + self.joint_width
        num_courses = int(math.ceil(self.wall_height / course_height))

        stone_index = 0

        for course in range(num_courses):
            y = course * course_height

            if y >= self.wall_height:
                break

            actual_height = min(self.stone_height, self.wall_height - y)

            # Décalage alterné
            offset = 0 if course % 2 == 0 else random.uniform(0.1, 0.3) * self.stone_width_max

            x = -offset
            while x < self.wall_width:
                stone_width = random.uniform(self.stone_width_min, self.stone_width_max)

                # Ajuster la dernière pierre
                if x + stone_width > self.wall_width:
                    stone_width = self.wall_width - x

                if stone_width > 0.05 and x + stone_width > 0:
                    start_x = max(0, x)
                    end_x = min(self.wall_width, x + stone_width)
                    actual_width = end_x - start_x

                    if actual_width > 0.05:
                        self.create_stone(
                            bm, uv_layer,
                            start_x, y,
                            actual_width, actual_height,
                            stone_index
                        )
                        stone_index += 1

                x += stone_width + self.joint_width

    def create_irregular_courses(self, bm, uv_layer):
        """Assisé irrégulier - hauteurs variables"""

        stone_index = 0
        y = 0
        course = 0

        while y < self.wall_height:
            # Hauteur variable pour cette rangée
            course_height = self.stone_height * random.uniform(0.7, 1.3)
            actual_height = min(course_height, self.wall_height - y)

            offset = 0 if course % 2 == 0 else random.uniform(0.1, 0.4) * self.stone_width_max

            x = -offset
            while x < self.wall_width:
                stone_width = random.uniform(self.stone_width_min, self.stone_width_max)

                if x + stone_width > self.wall_width:
                    stone_width = self.wall_width - x

                if stone_width > 0.05 and x + stone_width > 0:
                    start_x = max(0, x)
                    end_x = min(self.wall_width, x + stone_width)
                    actual_width = end_x - start_x

                    # Variation de hauteur par pierre
                    h_var = actual_height * random.uniform(0.9, 1.0)

                    if actual_width > 0.05:
                        self.create_stone(
                            bm, uv_layer,
                            start_x, y,
                            actual_width, h_var,
                            stone_index
                        )
                        stone_index += 1

                x += stone_width + self.joint_width

            y += course_height + self.joint_width
            course += 1

    def create_opus_incertum(self, bm, uv_layer):
        """Opus incertum - pierres irrégulières aléatoires"""

        stone_index = 0

        # Grille de base pour placer les pierres
        grid_size = self.stone_height * 0.8
        cols = int(self.wall_width / grid_size) + 2
        rows = int(self.wall_height / grid_size) + 2

        for row in range(rows):
            for col in range(cols):
                # Position de base avec variation
                base_x = col * grid_size + random.uniform(-grid_size * 0.3, grid_size * 0.3)
                base_y = row * grid_size + random.uniform(-grid_size * 0.3, grid_size * 0.3)

                # Taille aléatoire
                width = random.uniform(self.stone_width_min * 0.6, self.stone_width_max * 0.8)
                height = random.uniform(self.stone_height * 0.5, self.stone_height * 1.2)

                # Vérifier les limites
                if (base_x >= -width * 0.5 and base_x <= self.wall_width + width * 0.5 and
                    base_y >= -height * 0.5 and base_y <= self.wall_height + height * 0.5):

                    # Clipper aux bords
                    start_x = max(0, base_x)
                    start_y = max(0, base_y)
                    end_x = min(self.wall_width, base_x + width)
                    end_y = min(self.wall_height, base_y + height)

                    actual_width = end_x - start_x
                    actual_height = end_y - start_y

                    if actual_width > 0.04 and actual_height > 0.04:
                        self.create_stone(
                            bm, uv_layer,
                            start_x, start_y,
                            actual_width, actual_height,
                            stone_index,
                            irregular=True
                        )
                        stone_index += 1

    def create_moellons(self, bm, uv_layer):
        """Moellons - pierres grossièrement équarries"""

        stone_index = 0
        y = 0
        course = 0

        while y < self.wall_height:
            # Hauteur variable
            course_height = self.stone_height * random.uniform(0.8, 1.4)
            actual_height = min(course_height, self.wall_height - y)

            x = 0
            while x < self.wall_width:
                stone_width = random.uniform(self.stone_width_min * 0.8, self.stone_width_max * 1.2)

                if x + stone_width > self.wall_width:
                    stone_width = self.wall_width - x

                if stone_width > 0.05:
                    self.create_stone(
                        bm, uv_layer,
                        x, y,
                        stone_width, actual_height,
                        stone_index,
                        irregular=True,
                        rough=True
                    )
                    stone_index += 1

                x += stone_width + self.joint_width * random.uniform(0.8, 1.5)

            y += course_height + self.joint_width * random.uniform(0.8, 1.5)
            course += 1

    def create_dry_stone(self, bm, uv_layer):
        """Pierre sèche - sans mortier, joints très fins"""

        # Similaire à assisé irrégulier mais joints plus fins
        original_joint = self.joint_width
        self.joint_width = 0.003  # Joints très fins

        self.create_irregular_courses(bm, uv_layer)

        self.joint_width = original_joint

    def create_stone(self, bm, uv_layer, x, y, width, height, index, irregular=False, rough=False):
        """Crée une pierre individuelle"""

        # Relief de la pierre
        z_offset = random.uniform(0, self.stone_depth)

        # Pour les pierres irrégulières, ajouter de la variation aux coins
        if irregular:
            offsets = [
                (random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)),
                (random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)),
                (random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)),
                (random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)),
            ]
        else:
            offsets = [(0, 0), (0, 0), (0, 0), (0, 0)]

        # Épaisseur variable pour rough
        thickness = self.wall_thickness
        if rough:
            thickness *= random.uniform(0.85, 1.15)

        # Vertices de la pierre (face avant)
        verts = [
            # Face avant
            Vector((x + offsets[0][0], z_offset, y + offsets[0][1])),
            Vector((x + width + offsets[1][0], z_offset, y + offsets[1][1])),
            Vector((x + width + offsets[2][0], z_offset, y + height + offsets[2][1])),
            Vector((x + offsets[3][0], z_offset, y + height + offsets[3][1])),
            # Face arrière
            Vector((x, -thickness, y)),
            Vector((x + width, -thickness, y)),
            Vector((x + width, -thickness, y + height)),
            Vector((x, -thickness, y + height)),
        ]

        bm_verts = [bm.verts.new(v) for v in verts]
        bm.verts.ensure_lookup_table()

        faces = [
            (0, 1, 2, 3),  # Front
            (5, 4, 7, 6),  # Back
            (0, 4, 5, 1),  # Bottom
            (2, 6, 7, 3),  # Top
            (0, 3, 7, 4),  # Left
            (1, 5, 6, 2),  # Right
        ]

        for face_indices in faces:
            try:
                f = bm.faces.new([bm_verts[i] for i in face_indices])

                # UVs
                if uv_layer:
                    for loop in f.loops:
                        u = (loop.vert.co.x - x) / max(width, 0.01)
                        v = (loop.vert.co.z - y) / max(height, 0.01)
                        # Offset par pierre pour variation
                        u += (index % 10) * 0.1
                        v += (index // 10) * 0.1
                        loop[uv_layer].uv = (u, v)
            except:
                pass

    # =================================================================
    # CRÉATION DU MATÉRIAU
    # =================================================================

    def create_stone_material(self):
        """Crée le shader de pierre"""

        mat = bpy.data.materials.new(name=f"Pierre_{self.stone_type}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Obtenir les couleurs
        base_color, dark_color, light_color = self.get_stone_colors()

        x = -2200
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Roughness'].default_value = self.get_base_roughness()
        principled.inputs['IOR'].default_value = 1.5
        principled.inputs['Specular IOR Level'].default_value = 0.35

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (
            self.random_seed * 3.7,
            self.random_seed * 5.3,
            self.random_seed * 2.1
        )

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # === COULEUR DE BASE (EXPOSÉE) ===
        color_frame = nodes.new('NodeFrame')
        color_frame.label = "🪨 COULEUR PIERRE (Modifier ici)"
        color_frame.use_custom_color = True
        color_frame.color = (0.6, 0.5, 0.4)
        color_frame.label_size = 20

        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 400, y + 400)
        base_col.outputs[0].default_value = (*base_color, 1.0)
        base_col.label = "COULEUR PIERRE"
        base_col.parent = color_frame

        dark_col = nodes.new('ShaderNodeRGB')
        dark_col.location = (x + 400, y + 250)
        dark_col.outputs[0].default_value = (*dark_color, 1.0)
        dark_col.label = "Ton Foncé"

        light_col = nodes.new('ShaderNodeRGB')
        light_col.location = (x + 400, y + 100)
        light_col.outputs[0].default_value = (*light_color, 1.0)
        light_col.label = "Ton Clair"

        # === TEXTURE DE LA PIERRE ===
        # Bruit principal pour la texture
        stone_noise = nodes.new('ShaderNodeTexNoise')
        stone_noise.location = (x + 400, y - 100)
        stone_noise.inputs['Scale'].default_value = 8.0
        stone_noise.inputs['Detail'].default_value = 8.0
        stone_noise.inputs['Roughness'].default_value = 0.65
        stone_noise.inputs['Distortion'].default_value = 0.5

        links.new(mapping.outputs['Vector'], stone_noise.inputs['Vector'])

        # Voronoi pour texture granuleuse
        stone_voronoi = nodes.new('ShaderNodeTexVoronoi')
        stone_voronoi.location = (x + 400, y - 300)
        stone_voronoi.voronoi_dimensions = '3D'
        stone_voronoi.feature = 'F1'
        stone_voronoi.inputs['Scale'].default_value = 30.0
        stone_voronoi.inputs['Randomness'].default_value = 1.0

        links.new(mapping.outputs['Vector'], stone_voronoi.inputs['Vector'])

        # Combiner les textures
        texture_mix = nodes.new('ShaderNodeMix')
        texture_mix.location = (x + 600, y - 200)
        texture_mix.data_type = 'FLOAT'
        texture_mix.inputs['Factor'].default_value = 0.3

        links.new(stone_noise.outputs['Fac'], texture_mix.inputs['A'])
        links.new(stone_voronoi.outputs['Distance'], texture_mix.inputs['B'])

        # === VARIATION PAR PIERRE ===
        # Noise à basse fréquence pour variation par pierre (ID unique par pierre)
        stone_var_noise = nodes.new('ShaderNodeTexNoise')
        stone_var_noise.location = (x + 400, y - 500)
        stone_var_noise.inputs['Scale'].default_value = 0.5
        stone_var_noise.inputs['Detail'].default_value = 0.0

        links.new(tex_coord.outputs['UV'], stone_var_noise.inputs['Vector'])

        # Deuxième noise pour plus de variation
        stone_var_noise2 = nodes.new('ShaderNodeTexNoise')
        stone_var_noise2.location = (x + 400, y - 650)
        stone_var_noise2.inputs['Scale'].default_value = 0.8
        stone_var_noise2.inputs['Detail'].default_value = 1.0

        links.new(tex_coord.outputs['UV'], stone_var_noise2.inputs['Vector'])

        # Voronoi pour variation cellulaire (chaque pierre = une cellule)
        stone_cell = nodes.new('ShaderNodeTexVoronoi')
        stone_cell.location = (x + 400, y - 800)
        stone_cell.voronoi_dimensions = '2D'
        stone_cell.feature = 'F1'
        stone_cell.inputs['Scale'].default_value = 3.0
        stone_cell.inputs['Randomness'].default_value = 0.5

        links.new(tex_coord.outputs['UV'], stone_cell.inputs['Vector'])

        # === VEINES ET INCLUSIONS ===
        vein_wave = nodes.new('ShaderNodeTexWave')
        vein_wave.location = (x + 600, y - 900)
        vein_wave.wave_type = 'BANDS'
        vein_wave.bands_direction = 'DIAGONAL'
        vein_wave.wave_profile = 'SAW'
        vein_wave.inputs['Scale'].default_value = 5.0
        vein_wave.inputs['Distortion'].default_value = 8.0
        vein_wave.inputs['Detail'].default_value = 3.0

        links.new(mapping.outputs['Vector'], vein_wave.inputs['Vector'])

        # Masque pour que certaines pierres aient des veines, d'autres non
        vein_mask = nodes.new('ShaderNodeMapRange')
        vein_mask.location = (x + 600, y - 700)
        vein_mask.inputs['From Min'].default_value = 0.3
        vein_mask.inputs['From Max'].default_value = 0.7
        vein_mask.clamp = True

        links.new(stone_var_noise2.outputs['Fac'], vein_mask.inputs['Value'])

        # Combiner veines avec masque
        vein_factor = nodes.new('ShaderNodeMath')
        vein_factor.location = (x + 800, y - 850)
        vein_factor.operation = 'MULTIPLY'

        links.new(vein_wave.outputs['Fac'], vein_factor.inputs[0])
        links.new(vein_mask.outputs['Result'], vein_factor.inputs[1])

        vein_intensity = nodes.new('ShaderNodeMath')
        vein_intensity.location = (x + 1000, y - 850)
        vein_intensity.operation = 'MULTIPLY'
        vein_intensity.inputs[1].default_value = self.vein_amount * 0.4

        links.new(vein_factor.outputs['Value'], vein_intensity.inputs[0])

        # Couleur des veines (plus foncée)
        vein_col = nodes.new('ShaderNodeRGB')
        vein_col.location = (x + 800, y - 1000)
        vein_col.outputs[0].default_value = (
            dark_color[0] * 0.7,
            dark_color[1] * 0.7,
            dark_color[2] * 0.7,
            1.0
        )

        # === MIX COULEURS ===
        # Mix base avec texture
        color_tex_mix = nodes.new('ShaderNodeMix')
        color_tex_mix.location = (x + 800, y + 200)
        color_tex_mix.data_type = 'RGBA'

        links.new(texture_mix.outputs['Result'], color_tex_mix.inputs['Factor'])
        links.new(base_col.outputs[0], color_tex_mix.inputs['A'])
        links.new(dark_col.outputs[0], color_tex_mix.inputs['B'])

        # Ajouter tons clairs
        light_mix = nodes.new('ShaderNodeMix')
        light_mix.location = (x + 1000, y + 200)
        light_mix.data_type = 'RGBA'
        light_mix.blend_type = 'OVERLAY'
        light_mix.inputs['Factor'].default_value = 0.15

        links.new(color_tex_mix.outputs['Result'], light_mix.inputs['A'])
        links.new(light_col.outputs[0], light_mix.inputs['B'])

        # === VARIATION TEINTE PAR PIERRE ===
        var_intensity = nodes.new('ShaderNodeMath')
        var_intensity.location = (x + 800, y - 400)
        var_intensity.operation = 'MULTIPLY'
        var_intensity.inputs[1].default_value = self.color_variation

        links.new(stone_var_noise.outputs['Fac'], var_intensity.inputs[0])

        color_var_mix = nodes.new('ShaderNodeMix')
        color_var_mix.location = (x + 1200, y + 150)
        color_var_mix.data_type = 'RGBA'
        color_var_mix.blend_type = 'HUE'

        links.new(var_intensity.outputs['Value'], color_var_mix.inputs['Factor'])
        links.new(light_mix.outputs['Result'], color_var_mix.inputs['A'])
        links.new(stone_var_noise.outputs['Color'], color_var_mix.inputs['B'])

        # === VARIATION LUMINOSITÉ PAR PIERRE ===
        brightness_var = nodes.new('ShaderNodeMix')
        brightness_var.location = (x + 1400, y + 150)
        brightness_var.data_type = 'RGBA'
        brightness_var.blend_type = 'VALUE'

        # Mapper la variation de luminosité
        bright_map = nodes.new('ShaderNodeMapRange')
        bright_map.location = (x + 1200, y - 50)
        bright_map.inputs['From Min'].default_value = 0.0
        bright_map.inputs['From Max'].default_value = 1.0
        bright_map.inputs['To Min'].default_value = 0.5 - self.brightness_variation
        bright_map.inputs['To Max'].default_value = 0.5 + self.brightness_variation

        links.new(stone_var_noise2.outputs['Fac'], bright_map.inputs['Value'])
        links.new(bright_map.outputs['Result'], brightness_var.inputs['Factor'])
        links.new(color_var_mix.outputs['Result'], brightness_var.inputs['A'])

        links.new(stone_var_noise2.outputs['Color'], brightness_var.inputs['B'])

        # === AJOUTER LES VEINES ===
        with_veins = nodes.new('ShaderNodeMix')
        with_veins.location = (x + 1600, y + 150)
        with_veins.data_type = 'RGBA'

        links.new(vein_intensity.outputs['Value'], with_veins.inputs['Factor'])
        links.new(brightness_var.outputs['Result'], with_veins.inputs['A'])
        links.new(vein_col.outputs[0], with_veins.inputs['B'])

        current_color = with_veins.outputs['Result']

        # === PATINE / VIEILLISSEMENT ===
        if self.weathering > 0:
            weather_noise = nodes.new('ShaderNodeTexNoise')
            weather_noise.location = (x + 1000, y - 600)
            weather_noise.inputs['Scale'].default_value = 2.5
            weather_noise.inputs['Detail'].default_value = 4.0

            links.new(mapping.outputs['Vector'], weather_noise.inputs['Vector'])

            # Couleur patinée (plus grise)
            patina_col = nodes.new('ShaderNodeRGB')
            patina_col.location = (x + 1000, y - 750)
            patina_col.outputs[0].default_value = (0.45, 0.44, 0.42, 1.0)

            weather_intensity = nodes.new('ShaderNodeMath')
            weather_intensity.location = (x + 1200, y - 600)
            weather_intensity.operation = 'MULTIPLY'
            weather_intensity.inputs[1].default_value = self.weathering * 0.4

            links.new(weather_noise.outputs['Fac'], weather_intensity.inputs[0])

            weather_mix = nodes.new('ShaderNodeMix')
            weather_mix.location = (x + 1400, y + 100)
            weather_mix.data_type = 'RGBA'

            links.new(weather_intensity.outputs['Value'], weather_mix.inputs['Factor'])
            links.new(current_color, weather_mix.inputs['A'])
            links.new(patina_col.outputs[0], weather_mix.inputs['B'])

            current_color = weather_mix.outputs['Result']

        # === SALISSURES ===
        if self.dirt > 0:
            dirt_noise = nodes.new('ShaderNodeTexNoise')
            dirt_noise.location = (x + 1200, y - 800)
            dirt_noise.inputs['Scale'].default_value = 3.0
            dirt_noise.inputs['Detail'].default_value = 5.0
            dirt_noise.inputs['Roughness'].default_value = 0.8

            links.new(mapping.outputs['Vector'], dirt_noise.inputs['Vector'])

            dirt_col = nodes.new('ShaderNodeRGB')
            dirt_col.location = (x + 1200, y - 950)
            dirt_col.outputs[0].default_value = (0.18, 0.16, 0.12, 1.0)

            dirt_intensity = nodes.new('ShaderNodeMath')
            dirt_intensity.location = (x + 1400, y - 800)
            dirt_intensity.operation = 'MULTIPLY'
            dirt_intensity.inputs[1].default_value = self.dirt * 0.35

            links.new(dirt_noise.outputs['Fac'], dirt_intensity.inputs[0])

            dirt_mix = nodes.new('ShaderNodeMix')
            dirt_mix.location = (x + 1600, y + 50)
            dirt_mix.data_type = 'RGBA'

            links.new(dirt_intensity.outputs['Value'], dirt_mix.inputs['Factor'])
            links.new(current_color, dirt_mix.inputs['A'])
            links.new(dirt_col.outputs[0], dirt_mix.inputs['B'])

            current_color = dirt_mix.outputs['Result']

        # === MOUSSE ===
        if self.moss > 0:
            moss_noise = nodes.new('ShaderNodeTexNoise')
            moss_noise.location = (x + 1400, y - 1000)
            moss_noise.inputs['Scale'].default_value = 6.0
            moss_noise.inputs['Detail'].default_value = 6.0

            links.new(mapping.outputs['Vector'], moss_noise.inputs['Vector'])

            # Gradient vertical (mousse en bas)
            gradient = nodes.new('ShaderNodeTexGradient')
            gradient.location = (x + 1400, y - 1150)
            gradient.gradient_type = 'LINEAR'

            gradient_mapping = nodes.new('ShaderNodeMapping')
            gradient_mapping.location = (x + 1200, y - 1150)
            gradient_mapping.inputs['Rotation'].default_value = (math.radians(90), 0, 0)

            links.new(tex_coord.outputs['Object'], gradient_mapping.inputs['Vector'])
            links.new(gradient_mapping.outputs['Vector'], gradient.inputs['Vector'])

            # Combiner noise + gradient
            moss_factor = nodes.new('ShaderNodeMath')
            moss_factor.location = (x + 1600, y - 1050)
            moss_factor.operation = 'MULTIPLY'

            links.new(moss_noise.outputs['Fac'], moss_factor.inputs[0])
            links.new(gradient.outputs['Fac'], moss_factor.inputs[1])

            moss_col = nodes.new('ShaderNodeRGB')
            moss_col.location = (x + 1600, y - 1200)
            moss_col.outputs[0].default_value = (0.12, 0.18, 0.08, 1.0)

            moss_intensity = nodes.new('ShaderNodeMath')
            moss_intensity.location = (x + 1800, y - 1050)
            moss_intensity.operation = 'MULTIPLY'
            moss_intensity.inputs[1].default_value = self.moss * 0.6

            links.new(moss_factor.outputs['Value'], moss_intensity.inputs[0])

            moss_mix = nodes.new('ShaderNodeMix')
            moss_mix.location = (x + 1800, y)
            moss_mix.data_type = 'RGBA'

            links.new(moss_intensity.outputs['Value'], moss_mix.inputs['Factor'])
            links.new(current_color, moss_mix.inputs['A'])
            links.new(moss_col.outputs[0], moss_mix.inputs['B'])

            current_color = moss_mix.outputs['Result']

        # Connecter couleur finale
        links.new(current_color, principled.inputs['Base Color'])

        # === ROUGHNESS AVEC VARIATION PAR PIERRE ===
        rough_base = self.get_base_roughness()

        # Noise pour variation de surface
        rough_noise = nodes.new('ShaderNodeTexNoise')
        rough_noise.location = (x + 1600, y - 300)
        rough_noise.inputs['Scale'].default_value = 25.0
        rough_noise.inputs['Detail'].default_value = 5.0

        links.new(mapping.outputs['Vector'], rough_noise.inputs['Vector'])

        # Variation de roughness par pierre
        rough_per_stone = nodes.new('ShaderNodeMapRange')
        rough_per_stone.location = (x + 1600, y - 450)
        rough_per_stone.inputs['From Min'].default_value = 0.0
        rough_per_stone.inputs['From Max'].default_value = 1.0
        rough_per_stone.inputs['To Min'].default_value = rough_base - self.texture_variation * 0.2
        rough_per_stone.inputs['To Max'].default_value = rough_base + self.texture_variation * 0.25

        links.new(stone_var_noise2.outputs['Fac'], rough_per_stone.inputs['Value'])

        # Combiner roughness surface + variation par pierre
        rough_combine = nodes.new('ShaderNodeMix')
        rough_combine.location = (x + 1800, y - 350)
        rough_combine.data_type = 'FLOAT'
        rough_combine.inputs['Factor'].default_value = 0.6

        # Map le noise de surface
        rough_surface_map = nodes.new('ShaderNodeMapRange')
        rough_surface_map.location = (x + 1800, y - 200)
        rough_surface_map.inputs['From Min'].default_value = 0.3
        rough_surface_map.inputs['From Max'].default_value = 0.7
        rough_surface_map.inputs['To Min'].default_value = -0.08
        rough_surface_map.inputs['To Max'].default_value = 0.08

        links.new(rough_noise.outputs['Fac'], rough_surface_map.inputs['Value'])

        # Ajouter la variation de surface à la roughness par pierre
        rough_add = nodes.new('ShaderNodeMath')
        rough_add.location = (x + 2000, y - 300)
        rough_add.operation = 'ADD'
        rough_add.use_clamp = True

        links.new(rough_per_stone.outputs['Result'], rough_add.inputs[0])
        links.new(rough_surface_map.outputs['Result'], rough_add.inputs[1])

        links.new(rough_add.outputs['Value'], principled.inputs['Roughness'])

        # === BUMP AVEC VARIATION PAR PIERRE ===
        # Bump principal (texture pierre)
        bump_main = nodes.new('ShaderNodeBump')
        bump_main.location = (x + 1600, y - 550)
        bump_main.inputs['Strength'].default_value = 0.35

        links.new(texture_mix.outputs['Result'], bump_main.inputs['Height'])

        # Bump granuleux avec intensité variable par pierre
        grain_bump_strength = nodes.new('ShaderNodeMapRange')
        grain_bump_strength.location = (x + 1600, y - 700)
        grain_bump_strength.inputs['From Min'].default_value = 0.0
        grain_bump_strength.inputs['From Max'].default_value = 1.0
        grain_bump_strength.inputs['To Min'].default_value = 0.05
        grain_bump_strength.inputs['To Max'].default_value = 0.25 + self.texture_variation * 0.2

        links.new(stone_var_noise.outputs['Fac'], grain_bump_strength.inputs['Value'])

        grain_bump = nodes.new('ShaderNodeBump')
        grain_bump.location = (x + 1800, y - 600)

        links.new(grain_bump_strength.outputs['Result'], grain_bump.inputs['Strength'])
        links.new(stone_voronoi.outputs['Distance'], grain_bump.inputs['Height'])
        links.new(bump_main.outputs['Normal'], grain_bump.inputs['Normal'])

        # Bump des veines
        vein_bump = nodes.new('ShaderNodeBump')
        vein_bump.location = (x + 2000, y - 600)
        vein_bump.inputs['Strength'].default_value = self.vein_amount * 0.15
        vein_bump.invert = True

        links.new(vein_factor.outputs['Value'], vein_bump.inputs['Height'])
        links.new(grain_bump.outputs['Normal'], vein_bump.inputs['Normal'])

        links.new(vein_bump.outputs['Normal'], principled.inputs['Normal'])

        return mat

    def get_stone_colors(self):
        """Retourne les couleurs selon le type de pierre"""

        colors = {
            'CALCAIRE': (
                (0.75, 0.72, 0.65),  # Base
                (0.55, 0.52, 0.45),  # Foncé
                (0.88, 0.85, 0.78),  # Clair
            ),
            'CALCAIRE_DORE': (
                (0.78, 0.68, 0.50),
                (0.58, 0.48, 0.35),
                (0.90, 0.82, 0.65),
            ),
            'GRANIT': (
                (0.45, 0.44, 0.43),
                (0.25, 0.25, 0.26),
                (0.65, 0.64, 0.63),
            ),
            'GRANIT_ROSE': (
                (0.60, 0.50, 0.48),
                (0.40, 0.32, 0.30),
                (0.78, 0.68, 0.65),
            ),
            'GRES': (
                (0.70, 0.58, 0.45),
                (0.50, 0.40, 0.30),
                (0.85, 0.75, 0.62),
            ),
            'ARDOISE': (
                (0.22, 0.24, 0.28),
                (0.12, 0.14, 0.18),
                (0.35, 0.38, 0.42),
            ),
            'MEULIERE': (
                (0.55, 0.45, 0.35),
                (0.35, 0.28, 0.22),
                (0.72, 0.62, 0.50),
            ),
            'PIERRE_TAILLE': (
                (0.82, 0.80, 0.75),
                (0.62, 0.60, 0.55),
                (0.92, 0.90, 0.88),
            ),
            'CUSTOM': (
                self.custom_color[:],
                tuple(c * 0.7 for c in self.custom_color),
                tuple(min(1.0, c * 1.2) for c in self.custom_color),
            ),
        }

        return colors.get(self.stone_type, colors['CALCAIRE'])

    def get_base_roughness(self):
        """Retourne la roughness selon le type"""

        roughness_values = {
            'CALCAIRE': 0.65,
            'CALCAIRE_DORE': 0.60,
            'GRANIT': 0.45,
            'GRANIT_ROSE': 0.45,
            'GRES': 0.70,
            'ARDOISE': 0.55,
            'MEULIERE': 0.75,
            'PIERRE_TAILLE': 0.50,
            'CUSTOM': 0.60,
        }

        return roughness_values.get(self.stone_type, 0.60)
