# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Bardage Bois Extérieur (BLENDER 4.2+ COMPATIBLE)
#  Copyright (C) 2025 mvaertan
#
#  Bardage bois avec 3 shaders : Naturel, Peint, Shou Sugi Ban
#  Types de pose : Horizontal, Vertical, Claire-voie, Clin
#
#  ✅ FIX: Correction axes Y/Z pour orientation verticale correcte
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
import math
import random
from mathutils import Vector


# Presets couleur peinture
PAINT_COLOR_PRESETS = {
    'BLANC': (0.90, 0.89, 0.87),
    'BLANC_CASSE': (0.88, 0.85, 0.80),
    'GRIS_CLAIR': (0.72, 0.71, 0.69),
    'GRIS_BLEU': (0.55, 0.58, 0.62),
    'GRIS_ANTHRACITE': (0.18, 0.18, 0.19),
    'NOIR': (0.03, 0.03, 0.03),
    'BLEU_MARINE': (0.10, 0.12, 0.22),
    'BLEU_GRIS': (0.40, 0.48, 0.55),
    'VERT_SAUGE': (0.45, 0.50, 0.42),
    'VERT_FORET': (0.15, 0.22, 0.15),
    'ROUGE_SUEDOIS': (0.55, 0.18, 0.12),
    'JAUNE_OCRE': (0.72, 0.58, 0.32),
}


class ExteriorBardage:
    """Générateur de bardage bois pour façades extérieures"""

    def __init__(self,
                 wall_width=6.0,
                 wall_height=2.7,
                 pose_type='HORIZONTAL',
                 material_type='NATUREL',
                 plank_width=0.15,
                 plank_thickness=0.020,
                 gap=0.008,
                 bevel_width=0.001,
                 # Bois naturel
                 wood_species='DOUGLAS',
                 weathering=0.3,
                 # Bois peint
                 paint_color_preset='GRIS_BLEU',
                 paint_custom_color=None,
                 paint_wear=0.15,
                 # Shou Sugi Ban
                 burn_intensity=0.7,
                 # Variations
                 plank_variation=0.5,
                 height_variation=0.001,
                 random_seed=42):
        """
        Initialise le générateur de bardage.

        Args:
            wall_width: Largeur du mur
            wall_height: Hauteur du mur
            pose_type: Type de pose (HORIZONTAL, VERTICAL, CLAIRE_VOIE, CLIN)
            material_type: Type de matériau (NATUREL, PEINT, BRULE)
            plank_width: Largeur des lames
            plank_thickness: Épaisseur des lames
            gap: Espacement entre lames
            bevel_width: Largeur du chanfrein
            wood_species: Essence de bois pour naturel
            weathering: Grisaillement naturel
            paint_color_preset: Preset de couleur peinture
            paint_custom_color: Couleur custom si preset CUSTOM
            paint_wear: Usure de la peinture
            burn_intensity: Intensité du brûlage
            plank_variation: Variation entre lames
            height_variation: Variation de hauteur
            random_seed: Seed aléatoire
        """
        self.wall_width = wall_width
        self.wall_height = wall_height
        self.pose_type = pose_type
        self.material_type = material_type
        self.plank_width = plank_width
        self.plank_thickness = plank_thickness
        self.gap = gap
        self.bevel_width = bevel_width
        self.wood_species = wood_species
        self.weathering = weathering
        self.paint_color_preset = paint_color_preset
        self.paint_custom_color = paint_custom_color
        self.paint_wear = paint_wear
        self.burn_intensity = burn_intensity
        self.plank_variation = plank_variation
        self.height_variation = height_variation
        self.random_seed = random_seed

        print(f"[ExteriorBardage] Type: {pose_type}, Matériau: {material_type}")

    def generate_for_wall(self, wall_obj, collection):
        """
        Génère le bardage pour un mur existant ou crée un nouveau mur.

        Args:
            wall_obj: Objet mur existant (ou None pour créer nouveau)
            collection: Collection Blender où créer les objets

        Returns:
            Objet Blender avec le bardage appliqué
        """
        random.seed(self.random_seed)

        # Si le mur existe (briques 3D ou mur simple), on applique juste le matériau
        if wall_obj and wall_obj.data:
            print(f"[ExteriorBardage] Application sur mur existant")
            mat = self.create_material()

            # Remplacer le matériau
            if len(wall_obj.data.materials) > 0:
                wall_obj.data.materials[0] = mat
            else:
                wall_obj.data.materials.append(mat)

            return wall_obj

        # Sinon, créer le mesh de bardage
        print(f"[ExteriorBardage] Création mesh bardage")
        obj = self.create_cladding_mesh(collection)

        mat = self.create_material()
        obj.data.materials.append(mat)

        return obj

    def create_cladding_mesh(self, collection):
        """Crée le mesh du bardage"""

        bm = bmesh.new()
        uv_layer = bm.loops.layers.uv.new("UVMap")

        if self.pose_type == 'CLAIRE_VOIE':
            # Espacement plus large pour claire-voie
            actual_gap = max(self.gap, self.plank_width * 0.3)
        else:
            actual_gap = self.gap

        plank_step = self.plank_width + actual_gap

        if self.pose_type in ['HORIZONTAL', 'CLIN']:
            self._create_horizontal_planks(bm, uv_layer, plank_step)
        elif self.pose_type in ['VERTICAL', 'CLAIRE_VOIE']:
            self._create_vertical_planks(bm, uv_layer, plank_step)

        # Créer le mesh
        mesh_name = f"Bardage_{self.material_type}_{self.pose_type}"
        mesh = bpy.data.meshes.new(mesh_name)
        bm.to_mesh(mesh)
        bm.free()

        # Chanfrein
        if self.bevel_width > 0:
            self._apply_bevel(mesh)

        # Créer l'objet
        obj = bpy.data.objects.new(mesh_name, mesh)
        collection.objects.link(obj)

        # Smooth shading
        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    def _create_horizontal_planks(self, bm, uv_layer, plank_step):
        """Crée les lames horizontales"""

        num_planks = int(math.ceil(self.wall_height / plank_step))

        for i in range(num_planks):
            z_pos = i * plank_step + self.plank_width / 2  # ✅ Position en Z (hauteur)

            if z_pos + self.plank_width / 2 > self.wall_height:
                continue

            # Variation de profondeur pour le clin
            y_offset = 0
            if self.pose_type == 'CLIN':
                y_offset = (i % 2) * self.plank_thickness * 0.3

            # Variation hauteur
            y_var = random.uniform(-self.height_variation, self.height_variation)

            self._create_plank(
                bm, uv_layer,
                0, y_offset + y_var, z_pos,  # ✅ y=profondeur, z=hauteur
                self.wall_width, self.plank_width, self.plank_thickness,
                horizontal=True,
                plank_index=i
            )

    def _create_vertical_planks(self, bm, uv_layer, plank_step):
        """Crée les lames verticales"""

        num_planks = int(math.ceil(self.wall_width / plank_step))

        for i in range(num_planks):
            x_pos = i * plank_step + self.plank_width / 2

            if x_pos + self.plank_width / 2 > self.wall_width:
                continue

            y_var = random.uniform(-self.height_variation, self.height_variation)

            self._create_plank(
                bm, uv_layer,
                x_pos, y_var, 0,  # ✅ y=profondeur, z=base
                self.plank_width, self.wall_height, self.plank_thickness,
                horizontal=False,
                plank_index=i
            )

    def _create_plank(self, bm, uv_layer, x, y, z, width, height, thickness, horizontal=True, plank_index=0):
        """
        Crée une lame individuelle.
        
        ✅ FIX: Axes corrigés pour Blender
        - X = largeur (gauche/droite)
        - Y = profondeur (avant/arrière) 
        - Z = hauteur (haut/bas)
        
        Args:
            x: Position X de la lame
            y: Profondeur (offset Y)
            z: Position Z (hauteur pour horizontal, base pour vertical)
            width: Largeur de la lame
            height: Hauteur de la lame
            thickness: Épaisseur (profondeur Y)
        """

        if horizontal:
            # Lame horizontale : s'étend en X, Z est la position verticale
            verts = [
                Vector((0, y, z - height/2)),
                Vector((width, y, z - height/2)),
                Vector((width, y, z + height/2)),
                Vector((0, y, z + height/2)),
                Vector((0, y + thickness, z - height/2)),
                Vector((width, y + thickness, z - height/2)),
                Vector((width, y + thickness, z + height/2)),
                Vector((0, y + thickness, z + height/2)),
            ]
        else:
            # Lame verticale : s'étend en Z, X est la position horizontale
            verts = [
                Vector((x - width/2, y, 0)),
                Vector((x + width/2, y, 0)),
                Vector((x + width/2, y, height)),
                Vector((x - width/2, y, height)),
                Vector((x - width/2, y + thickness, 0)),
                Vector((x + width/2, y + thickness, 0)),
                Vector((x + width/2, y + thickness, height)),
                Vector((x - width/2, y + thickness, height)),
            ]

        bm_verts = [bm.verts.new(v) for v in verts]
        bm.verts.ensure_lookup_table()

        faces = [
            (0, 1, 2, 3),  # Back
            (4, 7, 6, 5),  # Front
            (0, 4, 5, 1),  # Bottom
            (2, 6, 7, 3),  # Top
            (0, 3, 7, 4),  # Left
            (1, 5, 6, 2),  # Right
        ]

        for face_indices in faces:
            try:
                f = bm.faces.new([bm_verts[i] for i in face_indices])

                # UVs - ✅ Corrigés pour les nouveaux axes
                if uv_layer:
                    for loop in f.loops:
                        if horizontal:
                            u = (loop.vert.co.x) / self.wall_width
                            v = (loop.vert.co.z - z + height/2) / height  # ✅ Z au lieu de Y
                        else:
                            u = (loop.vert.co.x - x + width/2) / width
                            v = (loop.vert.co.z) / self.wall_height

                        # Ajouter offset par lame pour variation
                        u += plank_index * 0.1
                        loop[uv_layer].uv = (u, v)
            except:
                pass

    def _apply_bevel(self, mesh):
        """Applique chanfrein sur le mesh"""
        # Cette méthode nécessite un objet actif, sera appliquée différemment
        pass

    def create_material(self):
        """Crée le matériau selon le type sélectionné"""
        if self.material_type == 'NATUREL':
            return self._create_natural_wood_material()
        elif self.material_type == 'PEINT':
            return self._create_painted_wood_material()
        else:  # BRULE
            return self._create_burnt_wood_material()

    # =================================================================
    # SHADER 1 : BOIS NATUREL
    # =================================================================

    def _create_natural_wood_material(self):
        """Crée le shader de bois naturel avec grisaillement"""

        mat = bpy.data.materials.new(name=f"Bardage_Naturel_{self.wood_species}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        x = -2000
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Roughness'].default_value = 0.65

        try:
            principled.inputs['IOR'].default_value = 1.5
        except KeyError:
            pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Scale'].default_value = (1, 15, 1)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # === COULEUR BOIS DE BASE ===
        wood_colors = {
            'DOUGLAS': (0.55, 0.35, 0.20),
            'MELEZE': (0.60, 0.40, 0.25),
            'CEDRE': (0.65, 0.45, 0.28),
            'PIN': (0.70, 0.50, 0.30),
            'CHENE': (0.50, 0.32, 0.18),
        }
        base_color = wood_colors.get(self.wood_species, (0.55, 0.35, 0.20))

        wood_base = nodes.new('ShaderNodeRGB')
        wood_base.location = (x + 400, y + 200)
        wood_base.outputs[0].default_value = (*base_color, 1.0)

        # Couleur grisée
        gray_color = (0.45, 0.43, 0.40)
        wood_gray = nodes.new('ShaderNodeRGB')
        wood_gray.location = (x + 400, y + 50)
        wood_gray.outputs[0].default_value = (*gray_color, 1.0)

        # === GRAIN DU BOIS ===
        wave_tex = nodes.new('ShaderNodeTexWave')
        wave_tex.location = (x + 400, y - 150)
        wave_tex.wave_type = 'BANDS'
        wave_tex.bands_direction = 'Y'
        wave_tex.wave_profile = 'SAW'
        wave_tex.inputs['Scale'].default_value = 3.0
        wave_tex.inputs['Distortion'].default_value = 4.0
        wave_tex.inputs['Detail'].default_value = 3.0

        links.new(mapping.outputs['Vector'], wave_tex.inputs['Vector'])

        # === NOISE POUR VARIATION ===
        noise_tex = nodes.new('ShaderNodeTexNoise')
        noise_tex.location = (x + 400, y - 350)
        noise_tex.inputs['Scale'].default_value = 8.0
        noise_tex.inputs['Detail'].default_value = 6.0
        noise_tex.inputs['Roughness'].default_value = 0.6

        links.new(mapping.outputs['Vector'], noise_tex.inputs['Vector'])

        # === MIX GRAIN + NOISE ===
        grain_mix = nodes.new('ShaderNodeMix')
        grain_mix.location = (x + 700, y - 200)
        grain_mix.data_type = 'RGBA'
        grain_mix.inputs['Factor'].default_value = 0.3

        links.new(wave_tex.outputs['Color'], grain_mix.inputs[6])
        links.new(noise_tex.outputs['Color'], grain_mix.inputs[7])

        # === GRISAILLEMENT ===
        weather_noise = nodes.new('ShaderNodeTexNoise')
        weather_noise.location = (x + 400, y - 550)
        weather_noise.inputs['Scale'].default_value = 2.0
        weather_noise.inputs['Detail'].default_value = 4.0

        links.new(mapping.outputs['Vector'], weather_noise.inputs['Vector'])

        weather_ramp = nodes.new('ShaderNodeMapRange')
        weather_ramp.location = (x + 600, y - 550)
        weather_ramp.inputs['From Min'].default_value = 0.3
        weather_ramp.inputs['From Max'].default_value = 0.7

        links.new(weather_noise.outputs['Fac'], weather_ramp.inputs['Value'])

        weather_factor = nodes.new('ShaderNodeMath')
        weather_factor.location = (x + 800, y - 550)
        weather_factor.operation = 'MULTIPLY'
        weather_factor.inputs[1].default_value = self.weathering

        links.new(weather_ramp.outputs['Result'], weather_factor.inputs[0])

        # === MIX COULEUR BOIS/GRIS ===
        color_mix = nodes.new('ShaderNodeMix')
        color_mix.location = (x + 1000, y + 100)
        color_mix.data_type = 'RGBA'

        links.new(weather_factor.outputs['Value'], color_mix.inputs['Factor'])
        links.new(wood_base.outputs[0], color_mix.inputs[6])
        links.new(wood_gray.outputs[0], color_mix.inputs[7])

        # === VARIATION PAR GRAIN ===
        final_color = nodes.new('ShaderNodeMix')
        final_color.location = (x + 1200, y)
        final_color.data_type = 'RGBA'
        final_color.blend_type = 'OVERLAY'
        final_color.inputs['Factor'].default_value = 0.15

        links.new(color_mix.outputs[2], final_color.inputs[6])
        links.new(grain_mix.outputs[2], final_color.inputs[7])

        links.new(final_color.outputs[2], principled.inputs['Base Color'])

        # === BUMP ===
        bump = nodes.new('ShaderNodeBump')
        bump.location = (x + 1200, y - 400)
        bump.inputs['Strength'].default_value = 0.2

        links.new(wave_tex.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])

        return mat

    # =================================================================
    # SHADER 2 : BOIS PEINT
    # =================================================================

    def _create_painted_wood_material(self):
        """Crée le shader de bois peint avec usure"""

        # Récupérer couleur
        if self.paint_color_preset == 'CUSTOM' and self.paint_custom_color:
            paint_color = self.paint_custom_color[:3]
        else:
            paint_color = PAINT_COLOR_PRESETS.get(self.paint_color_preset, (0.55, 0.58, 0.62))

        mat = bpy.data.materials.new(name=f"Bardage_Peint_{self.paint_color_preset}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        x = -2000
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Roughness'].default_value = 0.55

        try:
            principled.inputs['IOR'].default_value = 1.5
        except KeyError:
            pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Scale'].default_value = (1, 15, 1)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # === COULEUR PEINTURE ===
        paint_col = nodes.new('ShaderNodeRGB')
        paint_col.location = (x + 400, y + 400)
        paint_col.outputs[0].default_value = (*paint_color, 1.0)
        paint_col.label = "Couleur Peinture"

        # === GRAIN DU BOIS ===
        wave_grain = nodes.new('ShaderNodeTexWave')
        wave_grain.location = (x + 400, y)
        wave_grain.wave_type = 'BANDS'
        wave_grain.bands_direction = 'Y'
        wave_grain.wave_profile = 'SAW'
        wave_grain.inputs['Scale'].default_value = 4.0
        wave_grain.inputs['Distortion'].default_value = 3.0
        wave_grain.inputs['Detail'].default_value = 2.0

        links.new(mapping.outputs['Vector'], wave_grain.inputs['Vector'])

        # Le grain influence légèrement
        grain_influence = nodes.new('ShaderNodeMix')
        grain_influence.location = (x + 800, y + 300)
        grain_influence.data_type = 'RGBA'
        grain_influence.blend_type = 'OVERLAY'
        grain_influence.inputs['Factor'].default_value = 0.08

        links.new(paint_col.outputs[0], grain_influence.inputs[6])
        links.new(wave_grain.outputs['Color'], grain_influence.inputs[7])

        # === USURE ===
        wear_noise = nodes.new('ShaderNodeTexNoise')
        wear_noise.location = (x + 400, y - 200)
        wear_noise.inputs['Scale'].default_value = 15.0
        wear_noise.inputs['Detail'].default_value = 8.0
        wear_noise.inputs['Roughness'].default_value = 0.7

        links.new(mapping.outputs['Vector'], wear_noise.inputs['Vector'])

        wear_thresh = nodes.new('ShaderNodeMapRange')
        wear_thresh.location = (x + 600, y - 200)
        wear_thresh.inputs['From Min'].default_value = 0.5 - self.paint_wear * 0.3
        wear_thresh.inputs['From Max'].default_value = 0.5 + self.paint_wear * 0.3
        wear_thresh.clamp = True

        links.new(wear_noise.outputs['Fac'], wear_thresh.inputs['Value'])

        # Couleur du bois sous la peinture
        wood_under = nodes.new('ShaderNodeRGB')
        wood_under.location = (x + 600, y - 350)
        wood_under.outputs[0].default_value = (0.35, 0.28, 0.20, 1.0)

        wear_intensity = nodes.new('ShaderNodeMath')
        wear_intensity.location = (x + 800, y - 200)
        wear_intensity.operation = 'MULTIPLY'
        wear_intensity.inputs[1].default_value = self.paint_wear

        links.new(wear_thresh.outputs['Result'], wear_intensity.inputs[0])

        wear_mix = nodes.new('ShaderNodeMix')
        wear_mix.location = (x + 1000, y + 200)
        wear_mix.data_type = 'RGBA'

        links.new(wear_intensity.outputs['Value'], wear_mix.inputs['Factor'])
        links.new(grain_influence.outputs[2], wear_mix.inputs[6])
        links.new(wood_under.outputs[0], wear_mix.inputs[7])

        links.new(wear_mix.outputs[2], principled.inputs['Base Color'])

        # === BUMP ===
        bump = nodes.new('ShaderNodeBump')
        bump.location = (x + 1400, y - 400)
        bump.inputs['Strength'].default_value = 0.15

        links.new(wave_grain.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])

        return mat

    # =================================================================
    # SHADER 3 : SHOU SUGI BAN
    # =================================================================

    def _create_burnt_wood_material(self):
        """Crée le shader de bois brûlé japonais"""

        mat = bpy.data.materials.new(name="Bardage_ShouSugiBan")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        x = -2000
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Roughness'].default_value = 0.75

        try:
            principled.inputs['IOR'].default_value = 1.5
        except KeyError:
            pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Scale'].default_value = (1, 12, 1)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # === COULEURS CARBONISÉES ===
        black_col = nodes.new('ShaderNodeRGB')
        black_col.location = (x + 400, y + 300)
        black_col.outputs[0].default_value = (0.008, 0.008, 0.01, 1.0)

        brown_col = nodes.new('ShaderNodeRGB')
        brown_col.location = (x + 400, y + 150)
        brown_col.outputs[0].default_value = (0.08, 0.05, 0.03, 1.0)

        ash_col = nodes.new('ShaderNodeRGB')
        ash_col.location = (x + 400, y)
        ash_col.outputs[0].default_value = (0.15, 0.14, 0.13, 1.0)

        # === VEINES BRÛLÉES ===
        burn_wave = nodes.new('ShaderNodeTexWave')
        burn_wave.location = (x + 400, y - 400)
        burn_wave.wave_type = 'BANDS'
        burn_wave.bands_direction = 'Y'
        burn_wave.wave_profile = 'SAW'
        burn_wave.inputs['Scale'].default_value = 5.0
        burn_wave.inputs['Distortion'].default_value = 6.0
        burn_wave.inputs['Detail'].default_value = 4.0

        links.new(mapping.outputs['Vector'], burn_wave.inputs['Vector'])

        # === INTENSITÉ BRÛLAGE ===
        burn_noise = nodes.new('ShaderNodeTexNoise')
        burn_noise.location = (x + 400, y - 600)
        burn_noise.inputs['Scale'].default_value = 3.0
        burn_noise.inputs['Detail'].default_value = 5.0

        links.new(mapping.outputs['Vector'], burn_noise.inputs['Vector'])

        burn_mod = nodes.new('ShaderNodeMapRange')
        burn_mod.location = (x + 600, y - 600)
        burn_mod.inputs['From Min'].default_value = 0.0
        burn_mod.inputs['From Max'].default_value = 1.0
        burn_mod.inputs['To Min'].default_value = self.burn_intensity * 0.5
        burn_mod.inputs['To Max'].default_value = 1.0

        links.new(burn_noise.outputs['Fac'], burn_mod.inputs['Value'])

        # === MIX COULEURS ===
        color_mix_1 = nodes.new('ShaderNodeMix')
        color_mix_1.location = (x + 800, y + 200)
        color_mix_1.data_type = 'RGBA'

        links.new(burn_wave.outputs['Fac'], color_mix_1.inputs['Factor'])
        links.new(black_col.outputs[0], color_mix_1.inputs[6])
        links.new(brown_col.outputs[0], color_mix_1.inputs[7])

        # Ajouter cendres
        ash_factor = nodes.new('ShaderNodeMath')
        ash_factor.location = (x + 800, y - 50)
        ash_factor.operation = 'SUBTRACT'
        ash_factor.inputs[0].default_value = 1.0

        links.new(burn_mod.outputs['Result'], ash_factor.inputs[1])

        ash_intensity = nodes.new('ShaderNodeMath')
        ash_intensity.location = (x + 1000, y - 50)
        ash_intensity.operation = 'MULTIPLY'
        ash_intensity.inputs[1].default_value = 0.3

        links.new(ash_factor.outputs['Value'], ash_intensity.inputs[0])

        color_mix_2 = nodes.new('ShaderNodeMix')
        color_mix_2.location = (x + 1000, y + 150)
        color_mix_2.data_type = 'RGBA'

        links.new(ash_intensity.outputs['Value'], color_mix_2.inputs['Factor'])
        links.new(color_mix_1.outputs[2], color_mix_2.inputs[6])
        links.new(ash_col.outputs[0], color_mix_2.inputs[7])

        links.new(color_mix_2.outputs[2], principled.inputs['Base Color'])

        # === BUMP ===
        bump = nodes.new('ShaderNodeBump')
        bump.location = (x + 1000, y - 450)
        bump.inputs['Strength'].default_value = 0.4

        links.new(burn_wave.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])

        return mat
