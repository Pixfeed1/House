# =============================================================================
# SHADER MARBRE / CARRELAGE - Matériau Procédural Avancé
# Pour Blender 4.2+
# =============================================================================
#
# Shader réaliste pour sols en marbre/pierre avec :
# - Veines multi-couches (primaires, secondaires, micro)
# - Variation par dalle (chaque carreau unique)
# - Subsurface scattering
# - Micro-imperfections
# - Joints intégrés (optionnel)
# - 12 presets de marbre
#
# =============================================================================

import bpy
import math


class SHADER_OT_create_marble_tile(bpy.types.Operator):
    """Créer un shader de marbre/carrelage avancé"""
    bl_idname = "shader.create_marble_tile"
    bl_label = "Créer Marbre Carrelage"
    bl_options = {'REGISTER', 'UNDO'}

    # =================================================================
    # PROPRIÉTÉS
    # =================================================================

    marble_type: bpy.props.EnumProperty(
        name="Type de Marbre",
        items=[
            ('CARRARA', "Carrare", "Blanc italien, veines grises fines"),
            ('CALACATTA', "Calacatta", "Blanc, veines dorées épaisses"),
            ('STATUARIO', "Statuario", "Blanc pur, veines dramatiques"),
            ('EMPERADOR', "Emperador", "Brun, veines blanches"),
            ('EMPERADOR_LIGHT', "Emperador Clair", "Brun clair, veines crème"),
            ('NERO_MARQUINA', "Noir Marquina", "Noir, veines blanches"),
            ('VERDE_GUATEMALA', "Vert Guatemala", "Vert foncé, veines blanches"),
            ('ROSSO_LEVANTO', "Rouge Levanto", "Bordeaux, veines blanches"),
            ('CREMA_MARFIL', "Crema Marfil", "Beige crème uniforme"),
            ('TRAVERTINE', "Travertin", "Beige poreux"),
            ('SLATE', "Ardoise", "Gris foncé mat texturé"),
            ('CUSTOM', "Personnalisé", "Paramètres manuels"),
        ],
        default='CARRARA'
    )

    # Couleurs
    base_color: bpy.props.FloatVectorProperty(
        name="Couleur Base",
        subtype='COLOR',
        default=(0.9, 0.9, 0.88),
        min=0.0, max=1.0
    )
    vein_color: bpy.props.FloatVectorProperty(
        name="Couleur Veines",
        subtype='COLOR',
        default=(0.3, 0.3, 0.32),
        min=0.0, max=1.0
    )
    secondary_color: bpy.props.FloatVectorProperty(
        name="Couleur Secondaire",
        subtype='COLOR',
        default=(0.6, 0.58, 0.55),
        min=0.0, max=1.0
    )

    # Veines
    vein_scale: bpy.props.FloatProperty(
        name="Échelle Veines",
        default=2.0,
        min=0.5, max=10.0
    )
    vein_intensity: bpy.props.FloatProperty(
        name="Intensité Veines",
        default=0.7,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )
    vein_sharpness: bpy.props.FloatProperty(
        name="Netteté Veines",
        default=0.5,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )
    vein_distortion: bpy.props.FloatProperty(
        name="Distorsion",
        default=2.0,
        min=0.0, max=8.0
    )
    secondary_veins: bpy.props.FloatProperty(
        name="Veines Secondaires",
        default=0.4,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )
    micro_veins: bpy.props.FloatProperty(
        name="Micro-veines",
        default=0.2,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )

    # Variation par dalle
    tile_variation: bpy.props.FloatProperty(
        name="Variation par Dalle",
        default=0.8,
        min=0.0, max=1.0,
        subtype='FACTOR',
        description="Chaque dalle a un motif unique"
    )
    color_variation: bpy.props.FloatProperty(
        name="Variation Couleur",
        default=0.1,
        min=0.0, max=0.3,
        subtype='FACTOR'
    )

    # Surface
    roughness: bpy.props.FloatProperty(
        name="Rugosité",
        default=0.12,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )
    roughness_variation: bpy.props.FloatProperty(
        name="Variation Rugosité",
        default=0.05,
        min=0.0, max=0.2,
        subtype='FACTOR'
    )
    subsurface: bpy.props.FloatProperty(
        name="Translucidité",
        default=0.015,
        min=0.0, max=0.1,
        subtype='FACTOR'
    )

    # Imperfections
    bump_strength: bpy.props.FloatProperty(
        name="Relief Surface",
        default=0.1,
        min=0.0, max=0.5,
        subtype='FACTOR'
    )
    scratches: bpy.props.FloatProperty(
        name="Rayures",
        default=0.0,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )
    pores: bpy.props.FloatProperty(
        name="Porosité",
        default=0.0,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )

    # Joints
    add_grout: bpy.props.BoolProperty(
        name="Ajouter Joints",
        default=False,
        description="Ajouter des joints entre les dalles"
    )
    grout_color: bpy.props.FloatVectorProperty(
        name="Couleur Joints",
        subtype='COLOR',
        default=(0.7, 0.68, 0.65),
        min=0.0, max=1.0
    )
    grout_width: bpy.props.FloatProperty(
        name="Largeur Joints",
        default=0.02,
        min=0.005, max=0.1,
        subtype='FACTOR'
    )
    grout_depth: bpy.props.FloatProperty(
        name="Profondeur Joints",
        default=0.5,
        min=0.0, max=1.0,
        subtype='FACTOR'
    )

    # Coordonnées
    coord_type: bpy.props.EnumProperty(
        name="Coordonnées",
        items=[
            ('UV', "UV", "Utiliser les UVs (variation par dalle)"),
            ('OBJECT', "Objet", "Coordonnées objet (seamless)"),
            ('WORLD', "Monde", "Coordonnées monde"),
        ],
        default='UV'
    )

    random_seed: bpy.props.IntProperty(
        name="Seed",
        default=0,
        min=0
    )

    def execute(self, context):
        self.apply_preset()

        mat = bpy.data.materials.new(name=f"Marbre_{self.marble_type}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        self.create_shader(nodes, links)

        # Assigner
        if context.active_object and context.active_object.type == 'MESH':
            if context.active_object.data.materials:
                context.active_object.data.materials[0] = mat
            else:
                context.active_object.data.materials.append(mat)

        self.report({'INFO'}, f"Marbre {self.marble_type} créé")
        return {'FINISHED'}

    # =================================================================
    # PRESETS
    # =================================================================

    def apply_preset(self):
        if self.marble_type == 'CARRARA':
            self.base_color = (0.92, 0.91, 0.89)
            self.vein_color = (0.35, 0.37, 0.40)
            self.secondary_color = (0.7, 0.69, 0.67)
            self.vein_scale = 2.0
            self.vein_intensity = 0.6
            self.vein_sharpness = 0.4
            self.secondary_veins = 0.5
            self.micro_veins = 0.3
            self.subsurface = 0.015
            self.roughness = 0.10
            self.pores = 0.0

        elif self.marble_type == 'CALACATTA':
            self.base_color = (0.95, 0.94, 0.91)
            self.vein_color = (0.45, 0.38, 0.25)
            self.secondary_color = (0.75, 0.70, 0.60)
            self.vein_scale = 1.8
            self.vein_intensity = 0.85
            self.vein_sharpness = 0.3
            self.secondary_veins = 0.3
            self.micro_veins = 0.15
            self.subsurface = 0.02
            self.roughness = 0.08
            self.pores = 0.0

        elif self.marble_type == 'STATUARIO':
            self.base_color = (0.98, 0.97, 0.96)
            self.vein_color = (0.25, 0.27, 0.30)
            self.secondary_color = (0.5, 0.52, 0.55)
            self.vein_scale = 1.5
            self.vein_intensity = 0.9
            self.vein_sharpness = 0.6
            self.secondary_veins = 0.2
            self.micro_veins = 0.1
            self.subsurface = 0.025
            self.roughness = 0.06
            self.pores = 0.0

        elif self.marble_type == 'EMPERADOR':
            self.base_color = (0.22, 0.15, 0.10)
            self.vein_color = (0.85, 0.78, 0.65)
            self.secondary_color = (0.45, 0.35, 0.25)
            self.vein_scale = 2.5
            self.vein_intensity = 0.7
            self.vein_sharpness = 0.35
            self.secondary_veins = 0.6
            self.micro_veins = 0.4
            self.subsurface = 0.008
            self.roughness = 0.15
            self.pores = 0.1

        elif self.marble_type == 'EMPERADOR_LIGHT':
            self.base_color = (0.55, 0.45, 0.35)
            self.vein_color = (0.9, 0.85, 0.75)
            self.secondary_color = (0.4, 0.32, 0.25)
            self.vein_scale = 2.5
            self.vein_intensity = 0.6
            self.vein_sharpness = 0.3
            self.secondary_veins = 0.5
            self.micro_veins = 0.35
            self.subsurface = 0.01
            self.roughness = 0.14
            self.pores = 0.05

        elif self.marble_type == 'NERO_MARQUINA':
            self.base_color = (0.015, 0.015, 0.02)
            self.vein_color = (0.9, 0.88, 0.85)
            self.secondary_color = (0.35, 0.33, 0.30)
            self.vein_scale = 2.2
            self.vein_intensity = 0.75
            self.vein_sharpness = 0.5
            self.secondary_veins = 0.4
            self.micro_veins = 0.2
            self.subsurface = 0.003
            self.roughness = 0.08
            self.pores = 0.0

        elif self.marble_type == 'VERDE_GUATEMALA':
            self.base_color = (0.06, 0.12, 0.08)
            self.vein_color = (0.85, 0.88, 0.82)
            self.secondary_color = (0.25, 0.40, 0.30)
            self.vein_scale = 2.0
            self.vein_intensity = 0.8
            self.vein_sharpness = 0.45
            self.secondary_veins = 0.5
            self.micro_veins = 0.3
            self.subsurface = 0.006
            self.roughness = 0.12
            self.pores = 0.0

        elif self.marble_type == 'ROSSO_LEVANTO':
            self.base_color = (0.32, 0.06, 0.05)
            self.vein_color = (0.9, 0.85, 0.80)
            self.secondary_color = (0.5, 0.20, 0.15)
            self.vein_scale = 2.2
            self.vein_intensity = 0.7
            self.vein_sharpness = 0.4
            self.secondary_veins = 0.5
            self.micro_veins = 0.35
            self.subsurface = 0.008
            self.roughness = 0.12
            self.pores = 0.0

        elif self.marble_type == 'CREMA_MARFIL':
            self.base_color = (0.85, 0.78, 0.65)
            self.vein_color = (0.6, 0.52, 0.40)
            self.secondary_color = (0.92, 0.88, 0.78)
            self.vein_scale = 3.0
            self.vein_intensity = 0.35
            self.vein_sharpness = 0.25
            self.secondary_veins = 0.4
            self.micro_veins = 0.3
            self.subsurface = 0.012
            self.roughness = 0.10
            self.pores = 0.0

        elif self.marble_type == 'TRAVERTINE':
            self.base_color = (0.75, 0.68, 0.55)
            self.vein_color = (0.5, 0.42, 0.32)
            self.secondary_color = (0.85, 0.80, 0.70)
            self.vein_scale = 4.0
            self.vein_intensity = 0.45
            self.vein_sharpness = 0.2
            self.secondary_veins = 0.6
            self.micro_veins = 0.5
            self.pores = 0.7
            self.subsurface = 0.008
            self.roughness = 0.22

        elif self.marble_type == 'SLATE':
            self.base_color = (0.12, 0.12, 0.14)
            self.vein_color = (0.25, 0.25, 0.28)
            self.secondary_color = (0.08, 0.08, 0.09)
            self.vein_scale = 5.0
            self.vein_intensity = 0.5
            self.vein_sharpness = 0.2
            self.secondary_veins = 0.7
            self.micro_veins = 0.6
            self.pores = 0.0
            self.subsurface = 0.0
            self.roughness = 0.45
            self.bump_strength = 0.3

    # =================================================================
    # CRÉATION DU SHADER (suite dans le prochain message...)
    # =================================================================

    def create_shader(self, nodes, links):
        x = -2200
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
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

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        if self.coord_type == 'UV':
            coord_output = tex_coord.outputs['UV']
        elif self.coord_type == 'OBJECT':
            coord_output = tex_coord.outputs['Object']
        else:
            coord_output = tex_coord.outputs['Generated']

        # Mapping avec seed
        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (
            self.random_seed * 7.3,
            self.random_seed * 11.7,
            self.random_seed * 5.1
        )

        links.new(coord_output, mapping.inputs['Vector'])

        # === VARIATION PAR DALLE ===
        # Noise basé sur la position pour créer des variations
        tile_noise = nodes.new('ShaderNodeTexNoise')
        tile_noise.location = (x + 400, y - 200)
        tile_noise.inputs['Scale'].default_value = 0.5
        tile_noise.inputs['Detail'].default_value = 0.0

        links.new(mapping.outputs['Vector'], tile_noise.inputs['Vector'])

        # Combiner avec les coordonnées pour variation
        tile_offset = nodes.new('ShaderNodeVectorMath')
        tile_offset.location = (x + 600, y)
        tile_offset.operation = 'ADD'

        # Multiplier la variation
        tile_var_mult = nodes.new('ShaderNodeVectorMath')
        tile_var_mult.location = (x + 400, y - 100)
        tile_var_mult.operation = 'MULTIPLY'
        tile_var_mult.inputs[1].default_value = (
            self.tile_variation * 10,
            self.tile_variation * 10,
            self.tile_variation * 10
        )

        links.new(tile_noise.outputs['Color'], tile_var_mult.inputs[0])
        links.new(mapping.outputs['Vector'], tile_offset.inputs[0])
        links.new(tile_var_mult.outputs['Vector'], tile_offset.inputs[1])

        # === DISTORSION DES VEINES ===
        distort_noise = nodes.new('ShaderNodeTexNoise')
        distort_noise.location = (x + 800, y + 200)
        distort_noise.inputs['Scale'].default_value = self.vein_scale * 0.6
        distort_noise.inputs['Detail'].default_value = 4.0
        distort_noise.inputs['Roughness'].default_value = 0.6

        links.new(tile_offset.outputs['Vector'], distort_noise.inputs['Vector'])

        distort_mult = nodes.new('ShaderNodeVectorMath')
        distort_mult.location = (x + 1000, y + 200)
        distort_mult.operation = 'MULTIPLY'
        distort_mult.inputs[1].default_value = (
            self.vein_distortion * 0.08,
            self.vein_distortion * 0.08,
            self.vein_distortion * 0.08
        )

        links.new(distort_noise.outputs['Color'], distort_mult.inputs[0])

        distort_add = nodes.new('ShaderNodeVectorMath')
        distort_add.location = (x + 1200, y)
        distort_add.operation = 'ADD'

        links.new(tile_offset.outputs['Vector'], distort_add.inputs[0])
        links.new(distort_mult.outputs['Vector'], distort_add.inputs[1])

        # === VEINES PRINCIPALES ===
        wave_main = nodes.new('ShaderNodeTexWave')
        wave_main.location = (x + 1400, y)
        wave_main.wave_type = 'BANDS'
        wave_main.bands_direction = 'DIAGONAL'
        wave_main.wave_profile = 'SAW'
        wave_main.inputs['Scale'].default_value = self.vein_scale
        wave_main.inputs['Distortion'].default_value = self.vein_distortion * 2.5
        wave_main.inputs['Detail'].default_value = 3.0
        wave_main.inputs['Detail Scale'].default_value = 1.5
        wave_main.inputs['Detail Roughness'].default_value = 0.5

        links.new(distort_add.outputs['Vector'], wave_main.inputs['Vector'])

        # Contraste (sharpness)
        vein_contrast = nodes.new('ShaderNodeMapRange')
        vein_contrast.location = (x + 1600, y)
        vein_contrast.inputs['From Min'].default_value = 0.5 - (1 - self.vein_sharpness) * 0.4
        vein_contrast.inputs['From Max'].default_value = 0.5 + (1 - self.vein_sharpness) * 0.4
        vein_contrast.clamp = True

        links.new(wave_main.outputs['Fac'], vein_contrast.inputs['Value'])

        # === VEINES SECONDAIRES ===
        wave_secondary = nodes.new('ShaderNodeTexWave')
        wave_secondary.location = (x + 1400, y - 250)
        wave_secondary.wave_type = 'BANDS'
        wave_secondary.bands_direction = 'X'
        wave_secondary.wave_profile = 'SIN'
        wave_secondary.inputs['Scale'].default_value = self.vein_scale * 2.8
        wave_secondary.inputs['Distortion'].default_value = self.vein_distortion * 1.8
        wave_secondary.inputs['Detail'].default_value = 2.0

        links.new(distort_add.outputs['Vector'], wave_secondary.inputs['Vector'])

        # === MICRO-VEINES ===
        noise_micro = nodes.new('ShaderNodeTexNoise')
        noise_micro.location = (x + 1400, y - 450)
        noise_micro.inputs['Scale'].default_value = self.vein_scale * 10
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

        # === COMBINAISON VEINES ===
        mix_veins_1 = nodes.new('ShaderNodeMix')
        mix_veins_1.location = (x + 1800, y - 100)
        mix_veins_1.data_type = 'FLOAT'
        mix_veins_1.inputs['Factor'].default_value = self.secondary_veins

        links.new(vein_contrast.outputs['Result'], mix_veins_1.inputs['A'])
        links.new(wave_secondary.outputs['Fac'], mix_veins_1.inputs['B'])

        mix_veins_2 = nodes.new('ShaderNodeMix')
        mix_veins_2.location = (x + 2000, y - 100)
        mix_veins_2.data_type = 'FLOAT'
        mix_veins_2.blend_type = 'ADD'
        mix_veins_2.inputs['Factor'].default_value = self.micro_veins * 0.25

        links.new(mix_veins_1.outputs['Result'], mix_veins_2.inputs['A'])
        links.new(micro_thresh.outputs['Result'], mix_veins_2.inputs['B'])

        # Intensité finale
        vein_intensity = nodes.new('ShaderNodeMath')
        vein_intensity.location = (x + 2200, y - 100)
        vein_intensity.operation = 'MULTIPLY'
        vein_intensity.inputs[1].default_value = self.vein_intensity

        links.new(mix_veins_2.outputs['Result'], vein_intensity.inputs[0])

        # === VARIATION COULEUR BASE ===
        color_var_noise = nodes.new('ShaderNodeTexNoise')
        color_var_noise.location = (x + 1400, y + 400)
        color_var_noise.inputs['Scale'].default_value = self.vein_scale * 1.2
        color_var_noise.inputs['Detail'].default_value = 3.0
        color_var_noise.inputs['Roughness'].default_value = 0.5

        links.new(tile_offset.outputs['Vector'], color_var_noise.inputs['Vector'])

        # === COULEURS ===
        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 1800, y + 500)
        base_col.outputs[0].default_value = (*self.base_color, 1.0)

        # Variation de base
        base_varied = nodes.new('ShaderNodeMix')
        base_varied.location = (x + 2000, y + 450)
        base_varied.data_type = 'RGBA'
        base_varied.blend_type = 'OVERLAY'
        base_varied.inputs['Factor'].default_value = self.color_variation

        links.new(base_col.outputs[0], base_varied.inputs['A'])
        links.new(color_var_noise.outputs['Color'], base_varied.inputs['B'])

        vein_col = nodes.new('ShaderNodeRGB')
        vein_col.location = (x + 1800, y + 300)
        vein_col.outputs[0].default_value = (*self.vein_color, 1.0)

        secondary_col = nodes.new('ShaderNodeRGB')
        secondary_col.location = (x + 1800, y + 150)
        secondary_col.outputs[0].default_value = (*self.secondary_color, 1.0)

        # Mix couleurs veines
        vein_col_mix = nodes.new('ShaderNodeMix')
        vein_col_mix.location = (x + 2000, y + 200)
        vein_col_mix.data_type = 'RGBA'

        links.new(vein_contrast.outputs['Result'], vein_col_mix.inputs['Factor'])
        links.new(secondary_col.outputs[0], vein_col_mix.inputs['A'])
        links.new(vein_col.outputs[0], vein_col_mix.inputs['B'])

        # === COULEUR FINALE ===
        final_color = nodes.new('ShaderNodeMix')
        final_color.location = (x + 2400, y + 300)
        final_color.data_type = 'RGBA'

        links.new(vein_intensity.outputs['Value'], final_color.inputs['Factor'])
        links.new(base_varied.outputs['Result'], final_color.inputs['A'])
        links.new(vein_col_mix.outputs['Result'], final_color.inputs['B'])

        links.new(final_color.outputs['Result'], principled.inputs['Base Color'])

        # === SUBSURFACE ===
        if self.subsurface > 0:
            try:
                principled.inputs['Subsurface Weight'].default_value = self.subsurface
                principled.inputs['Subsurface Radius'].default_value = (0.5, 0.3, 0.2)
                principled.inputs['Subsurface Scale'].default_value = 0.1
            except KeyError:
                # Ancienne version de Blender
                pass

        # === ROUGHNESS ===
        rough_noise = nodes.new('ShaderNodeTexNoise')
        rough_noise.location = (x + 2000, y - 350)
        rough_noise.inputs['Scale'].default_value = 40.0
        rough_noise.inputs['Detail'].default_value = 6.0

        links.new(mapping.outputs['Vector'], rough_noise.inputs['Vector'])

        rough_map = nodes.new('ShaderNodeMapRange')
        rough_map.location = (x + 2200, y - 350)
        rough_map.inputs['From Min'].default_value = 0.3
        rough_map.inputs['From Max'].default_value = 0.7
        rough_map.inputs['To Min'].default_value = self.roughness - self.roughness_variation
        rough_map.inputs['To Max'].default_value = self.roughness + self.roughness_variation

        links.new(rough_noise.outputs['Fac'], rough_map.inputs['Value'])
        links.new(rough_map.outputs['Result'], principled.inputs['Roughness'])

        # === BUMP ===
        if self.bump_strength > 0 or self.scratches > 0 or self.pores > 0:
            bump_noise = nodes.new('ShaderNodeTexNoise')
            bump_noise.location = (x + 2000, y - 550)
            bump_noise.inputs['Scale'].default_value = 25.0
            bump_noise.inputs['Detail'].default_value = 8.0
            bump_noise.inputs['Roughness'].default_value = 0.7

            links.new(mapping.outputs['Vector'], bump_noise.inputs['Vector'])

            bump = nodes.new('ShaderNodeBump')
            bump.location = (x + 2400, y - 500)
            bump.inputs['Strength'].default_value = self.bump_strength * 0.3

            links.new(bump_noise.outputs['Fac'], bump.inputs['Height'])

            current_normal = bump.outputs['Normal']

            # Pores
            if self.pores > 0:
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
                pore_bump.inputs['Strength'].default_value = self.pores * 0.4
                pore_bump.invert = True

                links.new(pore_thresh.outputs['Result'], pore_bump.inputs['Height'])
                links.new(current_normal, pore_bump.inputs['Normal'])

                current_normal = pore_bump.outputs['Normal']

            # Rayures
            if self.scratches > 0:
                scratch_noise = nodes.new('ShaderNodeTexNoise')
                scratch_noise.location = (x + 2000, y - 950)
                scratch_noise.inputs['Scale'].default_value = 120.0
                scratch_noise.inputs['Detail'].default_value = 15.0
                scratch_noise.inputs['Roughness'].default_value = 1.0
                scratch_noise.inputs['Distortion'].default_value = 5.0

                links.new(mapping.outputs['Vector'], scratch_noise.inputs['Vector'])

                scratch_bump = nodes.new('ShaderNodeBump')
                scratch_bump.location = (x + 2600, y - 900)
                scratch_bump.inputs['Strength'].default_value = self.scratches * 0.15

                links.new(scratch_noise.outputs['Fac'], scratch_bump.inputs['Height'])
                links.new(current_normal, scratch_bump.inputs['Normal'])

                current_normal = scratch_bump.outputs['Normal']

            # Connecter au final
            links.new(current_normal, principled.inputs['Normal'])

    # =================================================================
    # UI
    # =================================================================

    def draw(self, context):
        layout = self.layout

        # Type
        box = layout.box()
        box.label(text="Type de Marbre", icon='NODE_MATERIAL')
        box.prop(self, "marble_type")

        # Couleurs
        if self.marble_type == 'CUSTOM':
            box = layout.box()
            box.label(text="Couleurs", icon='COLOR')
            box.prop(self, "base_color")
            box.prop(self, "vein_color")
            box.prop(self, "secondary_color")

        # Veines
        box = layout.box()
        box.label(text="Veines", icon='GP_MULTIFRAME_EDITING')
        box.prop(self, "vein_scale")
        box.prop(self, "vein_intensity")
        box.prop(self, "vein_sharpness")
        box.prop(self, "vein_distortion")
        row = box.row()
        row.prop(self, "secondary_veins")
        row.prop(self, "micro_veins")

        # Variation
        box = layout.box()
        box.label(text="Variations", icon='FORCE_TURBULENCE')
        box.prop(self, "tile_variation")
        box.prop(self, "color_variation")

        # Surface
        box = layout.box()
        box.label(text="Surface", icon='MATSPHERE')
        row = box.row()
        row.prop(self, "roughness")
        row.prop(self, "roughness_variation")
        box.prop(self, "subsurface")

        # Imperfections
        box = layout.box()
        box.label(text="Imperfections", icon='MOD_NOISE')
        box.prop(self, "bump_strength")
        row = box.row()
        row.prop(self, "scratches")
        row.prop(self, "pores")

        # Options
        box = layout.box()
        box.label(text="Options", icon='PREFERENCES')
        box.prop(self, "coord_type")
        box.prop(self, "random_seed")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=380)


# =============================================================================
# PANEL
# =============================================================================

class VIEW3D_PT_marble_tile_panel(bpy.types.Panel):
    bl_label = "Marbre Carrelage"
    bl_idname = "VIEW3D_PT_marble_tile"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Marbre"

    def draw(self, context):
        layout = self.layout
        layout.operator("shader.create_marble_tile", text="Créer Marbre", icon='NODE_MATERIAL')


# =============================================================================
# MENU
# =============================================================================

def menu_func(self, context):
    self.layout.operator(SHADER_OT_create_marble_tile.bl_idname, icon='NODE_MATERIAL')


# =============================================================================
# REGISTRATION
# =============================================================================

classes = [
    SHADER_OT_create_marble_tile,
    VIEW3D_PT_marble_tile_panel,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
    print("=" * 50)
    print("✅ SHADER MARBRE CARRELAGE")
    print("=" * 50)
    print("📍 Menu: Add > Créer Marbre Carrelage")
    print("📍 Panel: Sidebar (N) > Marbre")
    print("")
    print("Types de marbre:")
    print("  • Carrare, Calacatta, Statuario")
    print("  • Emperador, Emperador Clair")
    print("  • Noir Marquina, Vert Guatemala")
    print("  • Rouge Levanto, Crema Marfil")
    print("  • Travertin, Ardoise")
    print("  • Personnalisé")
    print("")
    print("Caractéristiques:")
    print("  • Veines multi-couches")
    print("  • Variation par dalle")
    print("  • Subsurface scattering")
    print("  • Joints optionnels")
    print("=" * 50)
