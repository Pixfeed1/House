"""
MARBRE - Sol en marbre
=======================
Matériau élégant et luxueux avec shader procédural avancé.
"""

import bpy
from .base import FloorTypeBase, MARBLE_TILE_SIZE


# =================================================================
# PRESETS DE MARBRE
# =================================================================

MARBLE_PRESETS = {
    'CARRARA': {
        'name': 'Carrare',
        'base_color': (0.92, 0.91, 0.89),
        'vein_color': (0.35, 0.37, 0.40),
        'secondary_color': (0.7, 0.69, 0.67),
        'vein_scale': 2.0,
        'vein_intensity': 0.6,
        'vein_sharpness': 0.4,
        'secondary_veins': 0.5,
        'micro_veins': 0.3,
        'subsurface': 0.015,
        'roughness': 0.10,
        'pores': 0.0,
    },
    'CALACATTA': {
        'name': 'Calacatta',
        'base_color': (0.95, 0.94, 0.91),
        'vein_color': (0.45, 0.38, 0.25),
        'secondary_color': (0.75, 0.70, 0.60),
        'vein_scale': 1.8,
        'vein_intensity': 0.85,
        'vein_sharpness': 0.3,
        'secondary_veins': 0.3,
        'micro_veins': 0.15,
        'subsurface': 0.02,
        'roughness': 0.08,
        'pores': 0.0,
    },
    'STATUARIO': {
        'name': 'Statuario',
        'base_color': (0.98, 0.97, 0.96),
        'vein_color': (0.25, 0.27, 0.30),
        'secondary_color': (0.5, 0.52, 0.55),
        'vein_scale': 1.5,
        'vein_intensity': 0.9,
        'vein_sharpness': 0.6,
        'secondary_veins': 0.2,
        'micro_veins': 0.1,
        'subsurface': 0.025,
        'roughness': 0.06,
        'pores': 0.0,
    },
}


class Marbre(FloorTypeBase):
    """Marbre - Élégance et luxe"""

    FLOOR_NAME = "Marbre"
    CATEGORY = "elegant"
    THICKNESS = 0.020  # 20mm
    PATTERN = "grid"

    TILE_SIZE = 0.5  # 50cm × 50cm

    def _generate_mesh(self, width, length, height):
        """Génère un sol en dalles de marbre"""
        return self._create_tile_floor(
            width, length, height,
            self.TILE_SIZE
        )

    def _apply_material(self, obj):
        """Matériau marbre procédural avancé avec veines réalistes"""

        # Sélectionner le preset (par défaut Carrare)
        marble_type = self.custom_options.get('marble_type', 'CARRARA')
        if marble_type not in MARBLE_PRESETS:
            marble_type = 'CARRARA'

        preset = MARBLE_PRESETS[marble_type]

        mat_name = f"Material_Marbre_{preset['name']}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # Créer le shader procédural
        self._create_marble_shader(nodes, links, preset)

        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[Marbre] Shader procédural: {preset['name']}")

    def _create_marble_shader(self, nodes, links, preset):
        """Crée le shader de marbre procédural avancé"""

        x = -2200
        y = 400

        # OUTPUT
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # PRINCIPLED BSDF
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['IOR'].default_value = 1.55

        # Blender 4.2+ compatibility
        try:
            principled.inputs['Specular IOR Level'].default_value = 0.5
        except KeyError:
            try:
                principled.inputs['Specular'].default_value = 0.5
            except KeyError:
                pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # COORDONNÉES (UV pour variation par dalle)
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (42 * 7.3, 42 * 11.7, 42 * 5.1)

        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])

        # VARIATION PAR DALLE
        tile_noise = nodes.new('ShaderNodeTexNoise')
        tile_noise.location = (x + 400, y - 200)
        tile_noise.inputs['Scale'].default_value = 0.5
        tile_noise.inputs['Detail'].default_value = 0.0

        links.new(mapping.outputs['Vector'], tile_noise.inputs['Vector'])

        tile_offset = nodes.new('ShaderNodeVectorMath')
        tile_offset.location = (x + 600, y)
        tile_offset.operation = 'ADD'

        tile_var_mult = nodes.new('ShaderNodeVectorMath')
        tile_var_mult.location = (x + 400, y - 100)
        tile_var_mult.operation = 'MULTIPLY'
        tile_var_mult.inputs[1].default_value = (8.0, 8.0, 8.0)

        links.new(tile_noise.outputs['Color'], tile_var_mult.inputs[0])
        links.new(mapping.outputs['Vector'], tile_offset.inputs[0])
        links.new(tile_var_mult.outputs['Vector'], tile_offset.inputs[1])

        # DISTORSION DES VEINES
        vein_distortion = 2.0
        distort_noise = nodes.new('ShaderNodeTexNoise')
        distort_noise.location = (x + 800, y + 200)
        distort_noise.inputs['Scale'].default_value = preset['vein_scale'] * 0.6
        distort_noise.inputs['Detail'].default_value = 4.0
        distort_noise.inputs['Roughness'].default_value = 0.6

        links.new(tile_offset.outputs['Vector'], distort_noise.inputs['Vector'])

        distort_mult = nodes.new('ShaderNodeVectorMath')
        distort_mult.location = (x + 1000, y + 200)
        distort_mult.operation = 'MULTIPLY'
        distort_mult.inputs[1].default_value = (
            vein_distortion * 0.08,
            vein_distortion * 0.08,
            vein_distortion * 0.08
        )

        links.new(distort_noise.outputs['Color'], distort_mult.inputs[0])

        distort_add = nodes.new('ShaderNodeVectorMath')
        distort_add.location = (x + 1200, y)
        distort_add.operation = 'ADD'

        links.new(tile_offset.outputs['Vector'], distort_add.inputs[0])
        links.new(distort_mult.outputs['Vector'], distort_add.inputs[1])

        # VEINES PRINCIPALES
        wave_main = nodes.new('ShaderNodeTexWave')
        wave_main.location = (x + 1400, y)
        wave_main.wave_type = 'BANDS'
        wave_main.bands_direction = 'DIAGONAL'
        wave_main.wave_profile = 'SAW'
        wave_main.inputs['Scale'].default_value = preset['vein_scale']
        wave_main.inputs['Distortion'].default_value = vein_distortion * 2.5
        wave_main.inputs['Detail'].default_value = 3.0
        wave_main.inputs['Detail Scale'].default_value = 1.5
        wave_main.inputs['Detail Roughness'].default_value = 0.5

        links.new(distort_add.outputs['Vector'], wave_main.inputs['Vector'])

        # Contraste (sharpness)
        vein_contrast = nodes.new('ShaderNodeMapRange')
        vein_contrast.location = (x + 1600, y)
        vein_contrast.inputs['From Min'].default_value = 0.5 - (1 - preset['vein_sharpness']) * 0.4
        vein_contrast.inputs['From Max'].default_value = 0.5 + (1 - preset['vein_sharpness']) * 0.4
        vein_contrast.clamp = True

        links.new(wave_main.outputs['Fac'], vein_contrast.inputs['Value'])

        # VEINES SECONDAIRES
        wave_secondary = nodes.new('ShaderNodeTexWave')
        wave_secondary.location = (x + 1400, y - 250)
        wave_secondary.wave_type = 'BANDS'
        wave_secondary.bands_direction = 'X'
        wave_secondary.wave_profile = 'SIN'
        wave_secondary.inputs['Scale'].default_value = preset['vein_scale'] * 2.8
        wave_secondary.inputs['Distortion'].default_value = vein_distortion * 1.8
        wave_secondary.inputs['Detail'].default_value = 2.0

        links.new(distort_add.outputs['Vector'], wave_secondary.inputs['Vector'])

        # MICRO-VEINES
        noise_micro = nodes.new('ShaderNodeTexNoise')
        noise_micro.location = (x + 1400, y - 450)
        noise_micro.inputs['Scale'].default_value = preset['vein_scale'] * 10
        noise_micro.inputs['Detail'].default_value = 10.0
        noise_micro.inputs['Roughness'].default_value = 0.8
        noise_micro.inputs['Distortion'].default_value = 1.5

        links.new(distort_add.outputs['Vector'], noise_micro.inputs['Vector'])

        micro_thresh = nodes.new('ShaderNodeMapRange')
        micro_thresh.location = (x + 1600, y - 450)
        micro_thresh.inputs['From Min'].default_value = 0.42
        micro_thresh.inputs['From Max'].default_value = 0.58
        micro_thresh.clamp = True

        links.new(noise_micro.outputs['Fac'], micro_thresh.inputs['Value'])

        # COMBINAISON VEINES
        mix_veins_1 = nodes.new('ShaderNodeMix')
        mix_veins_1.location = (x + 1800, y - 100)
        mix_veins_1.data_type = 'FLOAT'
        mix_veins_1.inputs['Factor'].default_value = preset['secondary_veins']

        links.new(vein_contrast.outputs['Result'], mix_veins_1.inputs['A'])
        links.new(wave_secondary.outputs['Fac'], mix_veins_1.inputs['B'])

        mix_veins_2 = nodes.new('ShaderNodeMix')
        mix_veins_2.location = (x + 2000, y - 100)
        mix_veins_2.data_type = 'FLOAT'
        mix_veins_2.blend_type = 'ADD'
        mix_veins_2.inputs['Factor'].default_value = preset['micro_veins'] * 0.25

        links.new(mix_veins_1.outputs['Result'], mix_veins_2.inputs['A'])
        links.new(micro_thresh.outputs['Result'], mix_veins_2.inputs['B'])

        # Intensité finale
        vein_intensity = nodes.new('ShaderNodeMath')
        vein_intensity.location = (x + 2200, y - 100)
        vein_intensity.operation = 'MULTIPLY'
        vein_intensity.inputs[1].default_value = preset['vein_intensity']

        links.new(mix_veins_2.outputs['Result'], vein_intensity.inputs[0])

        # VARIATION COULEUR BASE
        color_var_noise = nodes.new('ShaderNodeTexNoise')
        color_var_noise.location = (x + 1400, y + 400)
        color_var_noise.inputs['Scale'].default_value = preset['vein_scale'] * 1.2
        color_var_noise.inputs['Detail'].default_value = 3.0
        color_var_noise.inputs['Roughness'].default_value = 0.5

        links.new(tile_offset.outputs['Vector'], color_var_noise.inputs['Vector'])

        # COULEURS
        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 1800, y + 500)
        base_col.outputs[0].default_value = (*preset['base_color'], 1.0)

        color_variation = 0.1
        base_varied = nodes.new('ShaderNodeMix')
        base_varied.location = (x + 2000, y + 450)
        base_varied.data_type = 'RGBA'
        base_varied.blend_type = 'OVERLAY'
        base_varied.inputs['Factor'].default_value = color_variation

        links.new(base_col.outputs[0], base_varied.inputs['A'])
        links.new(color_var_noise.outputs['Color'], base_varied.inputs['B'])

        vein_col = nodes.new('ShaderNodeRGB')
        vein_col.location = (x + 1800, y + 300)
        vein_col.outputs[0].default_value = (*preset['vein_color'], 1.0)

        secondary_col = nodes.new('ShaderNodeRGB')
        secondary_col.location = (x + 1800, y + 150)
        secondary_col.outputs[0].default_value = (*preset['secondary_color'], 1.0)

        # Mix couleurs veines
        vein_col_mix = nodes.new('ShaderNodeMix')
        vein_col_mix.location = (x + 2000, y + 200)
        vein_col_mix.data_type = 'RGBA'

        links.new(vein_contrast.outputs['Result'], vein_col_mix.inputs['Factor'])
        links.new(secondary_col.outputs[0], vein_col_mix.inputs['A'])
        links.new(vein_col.outputs[0], vein_col_mix.inputs['B'])

        # COULEUR FINALE
        final_color = nodes.new('ShaderNodeMix')
        final_color.location = (x + 2400, y + 300)
        final_color.data_type = 'RGBA'

        links.new(vein_intensity.outputs['Value'], final_color.inputs['Factor'])
        links.new(base_varied.outputs['Result'], final_color.inputs['A'])
        links.new(vein_col_mix.outputs['Result'], final_color.inputs['B'])

        links.new(final_color.outputs['Result'], principled.inputs['Base Color'])

        # SUBSURFACE
        if preset['subsurface'] > 0:
            try:
                principled.inputs['Subsurface Weight'].default_value = preset['subsurface']
                principled.inputs['Subsurface Radius'].default_value = (0.5, 0.3, 0.2)
                principled.inputs['Subsurface Scale'].default_value = 0.1
            except KeyError:
                pass

        # ROUGHNESS
        rough_noise = nodes.new('ShaderNodeTexNoise')
        rough_noise.location = (x + 2000, y - 350)
        rough_noise.inputs['Scale'].default_value = 40.0
        rough_noise.inputs['Detail'].default_value = 6.0

        links.new(mapping.outputs['Vector'], rough_noise.inputs['Vector'])

        roughness_variation = 0.05
        rough_map = nodes.new('ShaderNodeMapRange')
        rough_map.location = (x + 2200, y - 350)
        rough_map.inputs['From Min'].default_value = 0.3
        rough_map.inputs['From Max'].default_value = 0.7
        rough_map.inputs['To Min'].default_value = preset['roughness'] - roughness_variation
        rough_map.inputs['To Max'].default_value = preset['roughness'] + roughness_variation

        links.new(rough_noise.outputs['Fac'], rough_map.inputs['Value'])
        links.new(rough_map.outputs['Result'], principled.inputs['Roughness'])

        # BUMP
        bump_strength = 0.1
        bump_noise = nodes.new('ShaderNodeTexNoise')
        bump_noise.location = (x + 2000, y - 550)
        bump_noise.inputs['Scale'].default_value = 25.0
        bump_noise.inputs['Detail'].default_value = 8.0
        bump_noise.inputs['Roughness'].default_value = 0.7

        links.new(mapping.outputs['Vector'], bump_noise.inputs['Vector'])

        bump = nodes.new('ShaderNodeBump')
        bump.location = (x + 2400, y - 500)
        bump.inputs['Strength'].default_value = bump_strength * 0.3

        links.new(bump_noise.outputs['Fac'], bump.inputs['Height'])

        # Pores pour Travertin
        if preset['pores'] > 0:
            pore_voronoi = nodes.new('ShaderNodeTexVoronoi')
            pore_voronoi.location = (x + 2000, y - 750)
            pore_voronoi.voronoi_dimensions = '3D'
            pore_voronoi.feature = 'F1'
            pore_voronoi.inputs['Scale'].default_value = 60.0
            pore_voronoi.inputs['Randomness'].default_value = 1.0

            links.new(mapping.outputs['Vector'], pore_voronoi.inputs['Vector'])

            pore_thresh = nodes.new('ShaderNodeMapRange')
            pore_thresh.location = (x + 2200, y - 750)
            pore_thresh.inputs['From Min'].default_value = 0.0
            pore_thresh.inputs['From Max'].default_value = 0.12
            pore_thresh.clamp = True

            links.new(pore_voronoi.outputs['Distance'], pore_thresh.inputs['Value'])

            pore_bump = nodes.new('ShaderNodeBump')
            pore_bump.location = (x + 2600, y - 700)
            pore_bump.inputs['Strength'].default_value = preset['pores'] * 0.4
            pore_bump.invert = True

            links.new(pore_thresh.outputs['Result'], pore_bump.inputs['Height'])
            links.new(bump.outputs['Normal'], pore_bump.inputs['Normal'])

            links.new(pore_bump.outputs['Normal'], principled.inputs['Normal'])
        else:
            links.new(bump.outputs['Normal'], principled.inputs['Normal'])
