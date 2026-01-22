"""
BÉTON - Sol en béton ciré
===========================
Matériau moderne et minimaliste avec shader procédural avancé.
"""

import bpy
from .base import FloorTypeBase


# =================================================================
# PRESETS DE BÉTON CIRÉ
# =================================================================

CONCRETE_PRESETS = {
    'GRIS_NATUREL': {
        'name': 'Gris Naturel',
        'color': (0.35, 0.33, 0.30),
        'finish': 'SATINE',  # Mat, Satiné, Ciré, Huilé
        'cloud_intensity': 0.4,
        'cloud_scale': 2.0,
        'trowel_marks': 0.3,
        'micro_cracks': 0.1,
        'pitting': 0.1,
    },
    'GRIS_CLAIR': {
        'name': 'Gris Clair',
        'color': (0.55, 0.53, 0.50),
        'finish': 'CIRE',
        'cloud_intensity': 0.3,
        'cloud_scale': 2.5,
        'trowel_marks': 0.2,
        'micro_cracks': 0.05,
        'pitting': 0.05,
    },
    'GRIS_ANTHRACITE': {
        'name': 'Gris Anthracite',
        'color': (0.15, 0.14, 0.13),
        'finish': 'SATINE',
        'cloud_intensity': 0.45,
        'cloud_scale': 1.8,
        'trowel_marks': 0.35,
        'micro_cracks': 0.12,
        'pitting': 0.08,
    },
}


# =================================================================
# ROUGHNESS PAR FINITION
# =================================================================

FINISH_ROUGHNESS = {
    'MAT': 0.55,
    'SATINE': 0.35,
    'CIRE': 0.20,
    'HUILE': 0.28,
}


class BetonCire(FloorTypeBase):
    """Béton ciré - Modernité et minimalisme"""

    FLOOR_NAME = "Béton Ciré"
    CATEGORY = "elegant"
    THICKNESS = 0.050  # 50mm (dalle épaisse)
    PATTERN = "seamless"  # Dalle continue sans joints

    def _generate_mesh(self, width, length, height):
        """Génère un sol en béton ciré continu"""
        return self._create_seamless_floor(width, length, height)

    def _apply_material(self, obj):
        """Matériau béton ciré procédural avancé"""

        # Sélectionner le preset (par défaut Gris Naturel)
        concrete_type = self.custom_options.get('concrete_type', 'GRIS_NATUREL')
        if concrete_type not in CONCRETE_PRESETS:
            concrete_type = 'GRIS_NATUREL'

        preset = CONCRETE_PRESETS[concrete_type]

        mat_name = f"Material_Beton_{preset['name'].replace(' ', '_')}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Créer le shader procédural
        self._create_concrete_shader(nodes, links, preset)

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Béton Ciré] Shader procédural: {preset['name']}")

    def _create_concrete_shader(self, nodes, links, preset):
        """Crée le shader de béton ciré procédural avancé"""

        base_color = preset['color']
        roughness = FINISH_ROUGHNESS.get(preset['finish'], 0.35)
        cloud_intensity = preset['cloud_intensity']
        cloud_scale = preset['cloud_scale']
        trowel_marks = preset['trowel_marks']
        micro_cracks = preset['micro_cracks']
        pitting = preset['pitting']
        color_variation = 0.15
        random_seed = 42

        x = -2000
        y = 400

        # OUTPUT
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)

        # PRINCIPLED BSDF
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

        # COORDONNÉES
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (
            random_seed * 5.7,
            random_seed * 8.3,
            random_seed * 3.1
        )

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # EFFET NUAGEUX (caractéristique du béton ciré)
        cloud_noise_1 = nodes.new('ShaderNodeTexNoise')
        cloud_noise_1.location = (x + 400, y)
        cloud_noise_1.inputs['Scale'].default_value = cloud_scale
        cloud_noise_1.inputs['Detail'].default_value = 6.0
        cloud_noise_1.inputs['Roughness'].default_value = 0.65
        cloud_noise_1.inputs['Distortion'].default_value = 0.8

        links.new(mapping.outputs['Vector'], cloud_noise_1.inputs['Vector'])

        cloud_noise_2 = nodes.new('ShaderNodeTexNoise')
        cloud_noise_2.location = (x + 400, y - 200)
        cloud_noise_2.inputs['Scale'].default_value = cloud_scale * 3
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

        # TRACES DE TALOCHE
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

        # MICRO-FISSURES
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

        # BULLAGE (petits trous)
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

        # COULEUR DE BASE
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

        # MIX COULEURS AVEC NUAGES
        # Intensité des nuages
        cloud_intensity_mult = nodes.new('ShaderNodeMath')
        cloud_intensity_mult.location = (x + 800, y - 100)
        cloud_intensity_mult.operation = 'MULTIPLY'
        cloud_intensity_mult.inputs[1].default_value = cloud_intensity

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
        color_var_mix.inputs['Factor'].default_value = color_variation

        links.new(color_mix_1.outputs['Result'], color_var_mix.inputs['A'])
        links.new(color_var_noise.outputs['Color'], color_var_mix.inputs['B'])

        # ASSOMBRIR AVEC FISSURES
        crack_darken = nodes.new('ShaderNodeMath')
        crack_darken.location = (x + 1000, y - 600)
        crack_darken.operation = 'MULTIPLY'
        crack_darken.inputs[1].default_value = micro_cracks * 0.3

        links.new(crack_invert.outputs['Value'], crack_darken.inputs[0])

        color_with_cracks = nodes.new('ShaderNodeMix')
        color_with_cracks.location = (x + 1400, y + 200)
        color_with_cracks.data_type = 'RGBA'

        links.new(crack_darken.outputs['Value'], color_with_cracks.inputs['Factor'])
        links.new(color_var_mix.outputs['Result'], color_with_cracks.inputs['A'])
        links.new(dark_col.outputs[0], color_with_cracks.inputs['B'])

        links.new(color_with_cracks.outputs['Result'], principled.inputs['Base Color'])

        # ROUGHNESS
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
        trowel_rough.inputs[1].default_value = trowel_marks * 0.1

        links.new(trowel_wave.outputs['Fac'], trowel_rough.inputs[0])

        rough_add = nodes.new('ShaderNodeMath')
        rough_add.location = (x + 1400, y - 350)
        rough_add.operation = 'ADD'
        rough_add.use_clamp = True

        links.new(rough_map.outputs['Result'], rough_add.inputs[0])
        links.new(trowel_rough.outputs['Value'], rough_add.inputs[1])

        links.new(rough_add.outputs['Value'], principled.inputs['Roughness'])

        # BUMP / NORMAL
        # Bump principal (nuages + taloche)
        bump_mix = nodes.new('ShaderNodeMath')
        bump_mix.location = (x + 1000, y - 150)
        bump_mix.operation = 'ADD'

        # Nuages
        cloud_bump_mult = nodes.new('ShaderNodeMath')
        cloud_bump_mult.location = (x + 800, y - 50)
        cloud_bump_mult.operation = 'MULTIPLY'
        cloud_bump_mult.inputs[1].default_value = cloud_intensity * 0.5

        links.new(cloud_mix.outputs['Result'], cloud_bump_mult.inputs[0])

        # Taloche
        trowel_bump_mult = nodes.new('ShaderNodeMath')
        trowel_bump_mult.location = (x + 800, y - 150)
        trowel_bump_mult.operation = 'MULTIPLY'
        trowel_bump_mult.inputs[1].default_value = trowel_marks * 0.3

        links.new(trowel_wave.outputs['Fac'], trowel_bump_mult.inputs[0])

        links.new(cloud_bump_mult.outputs['Value'], bump_mix.inputs[0])
        links.new(trowel_bump_mult.outputs['Value'], bump_mix.inputs[1])

        bump_main = nodes.new('ShaderNodeBump')
        bump_main.location = (x + 1200, y - 100)
        bump_main.inputs['Strength'].default_value = 0.15

        links.new(bump_mix.outputs['Value'], bump_main.inputs['Height'])

        # Bump fissures
        if micro_cracks > 0:
            crack_bump = nodes.new('ShaderNodeBump')
            crack_bump.location = (x + 1400, y - 100)
            crack_bump.inputs['Strength'].default_value = micro_cracks * 0.2
            crack_bump.invert = True

            links.new(crack_invert.outputs['Value'], crack_bump.inputs['Height'])
            links.new(bump_main.outputs['Normal'], crack_bump.inputs['Normal'])

            current_normal = crack_bump.outputs['Normal']
        else:
            current_normal = bump_main.outputs['Normal']

        # Bump bullage
        if pitting > 0:
            pit_bump = nodes.new('ShaderNodeBump')
            pit_bump.location = (x + 1600, y - 100)
            pit_bump.inputs['Strength'].default_value = pitting * 0.3
            pit_bump.invert = True

            links.new(pit_thresh.outputs['Result'], pit_bump.inputs['Height'])
            links.new(current_normal, pit_bump.inputs['Normal'])

            current_normal = pit_bump.outputs['Normal']

        links.new(current_normal, principled.inputs['Normal'])

