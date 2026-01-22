"""
PEINTURE MURALE
================
Mat, satinée, brillante, velours.
Lessivable ou non selon la pièce.

Types:
- MAT: Absorption lumière, cache imperfections
- SATINEE: Légère brillance, lessivable
- BRILLANTE: Brillance élevée, très lessivable
- VELOURS: Aspect velouté, élégant

Code HAUTE QUALITÉ.
"""

import bpy
import bmesh
from .base import WallFinishBase, PAINT_THICKNESS
from .paint_colors import PAINT_COLOR_PRESETS

# Types de peinture
PAINT_TYPES = {
    'MAT': {'roughness': 1.0, 'metallic': 0.0, 'name': "Mat"},
    'SATINEE': {'roughness': 0.6, 'metallic': 0.0, 'name': "Satinée"},
    'BRILLANTE': {'roughness': 0.2, 'metallic': 0.0, 'name': "Brillante"},
    'VELOURS': {'roughness': 0.8, 'metallic': 0.0, 'name': "Velours"}
}

class WallPeinture(WallFinishBase):
    """Finition peinture murale."""

    def __init__(self, width, height, paint_type='SATINEE', color=(0.95, 0.95, 0.95, 1.0), name="WallPeinture"):
        super().__init__(width, height, name)

        # ✅ SÉCURITÉ: Valider type peinture
        if paint_type not in PAINT_TYPES:
            print(f"[WallPeinture] ⚠️ Type invalide '{paint_type}', utilisation SATINEE")
            paint_type = 'SATINEE'

        self.paint_type = paint_type
        self.color = color

        print(f"[WallPeinture] Type: {PAINT_TYPES[paint_type]['name']}, Couleur: RGBA{color}")

    def generate_finish(self):
        bm = bmesh.new()

        try:
            # Surface lisse simple (peinture = finition plane)
            self._create_flat_wall_surface(
                bm, 0, 0, 0,
                self.width, self.height,
                thickness=PAINT_THICKNESS,
                subdivisions=0  # Pas besoin subdivisions pour peinture
            )

            obj, mesh = self._create_mesh_from_bmesh(bm, self.name)

            if not self.validate_geometry(obj):
                print(f"[WallPeinture] ❌ Échec validation")
                return None

            # Métadonnées
            obj["finish_type"] = "PEINTURE"
            obj["paint_type"] = self.paint_type
            obj["color"] = self.color

            # ✅ Appliquer le matériau
            self._apply_material(obj)

            print(f"[WallPeinture] ✅ Peinture {PAINT_TYPES[self.paint_type]['name']} générée")
            return obj

        finally:
            bm.free()

    def _apply_material(self, obj):
        """Applique le shader de peinture murale réaliste (Cycles & Eevee)"""
        mat_name = f"Peinture_Murale_{self.paint_type}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        # =================================================================
        # COORDONNÉES
        # =================================================================

        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (-1800, 0)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (-1600, 0)

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # =================================================================
        # OUTPUT & PRINCIPLED
        # =================================================================

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Metallic'].default_value = 0.0
        principled.inputs['IOR'].default_value = 1.5

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # =================================================================
        # COULEUR PRINCIPALE (utilise la couleur choisie dans le panel)
        # =================================================================

        color_node = nodes.new('ShaderNodeRGB')
        color_node.location = (-1400, 400)
        color_node.outputs[0].default_value = self.color  # ← Couleur du panel House
        color_node.label = "🎨 COULEUR"

        # =================================================================
        # MICRO-VARIATION PIGMENTS
        # =================================================================

        pigment_noise = nodes.new('ShaderNodeTexNoise')
        pigment_noise.location = (-1400, 200)
        pigment_noise.noise_dimensions = '3D'
        pigment_noise.inputs['Scale'].default_value = 200
        pigment_noise.inputs['Detail'].default_value = 4
        pigment_noise.inputs['Roughness'].default_value = 0.5
        pigment_noise.label = "Variation Pigments"

        links.new(mapping.outputs['Vector'], pigment_noise.inputs['Vector'])

        # Variation de teinte subtile
        hsv = nodes.new('ShaderNodeHueSaturation')
        hsv.location = (-1000, 350)
        hsv.inputs['Saturation'].default_value = 1.0
        hsv.inputs['Value'].default_value = 1.0

        hue_map = nodes.new('ShaderNodeMapRange')
        hue_map.location = (-1200, 150)
        hue_map.inputs['From Min'].default_value = 0.0
        hue_map.inputs['From Max'].default_value = 1.0
        hue_map.inputs['To Min'].default_value = 0.495
        hue_map.inputs['To Max'].default_value = 0.505

        links.new(pigment_noise.outputs['Fac'], hue_map.inputs['Value'])
        links.new(hue_map.outputs['Result'], hsv.inputs['Hue'])
        links.new(color_node.outputs['Color'], hsv.inputs['Color'])

        # Variation de luminosité subtile
        value_noise = nodes.new('ShaderNodeTexNoise')
        value_noise.location = (-1400, 0)
        value_noise.noise_dimensions = '3D'
        value_noise.inputs['Scale'].default_value = 80
        value_noise.inputs['Detail'].default_value = 3
        value_noise.inputs['Roughness'].default_value = 0.4
        value_noise.label = "Variation Luminosité"

        links.new(mapping.outputs['Vector'], value_noise.inputs['Vector'])

        value_map = nodes.new('ShaderNodeMapRange')
        value_map.location = (-1200, 0)
        value_map.inputs['From Min'].default_value = 0.0
        value_map.inputs['From Max'].default_value = 1.0
        value_map.inputs['To Min'].default_value = 0.98
        value_map.inputs['To Max'].default_value = 1.02

        links.new(value_noise.outputs['Fac'], value_map.inputs['Value'])

        # Multiplier la couleur par la variation
        color_multiply = nodes.new('ShaderNodeMix')
        color_multiply.location = (-800, 350)
        color_multiply.data_type = 'RGBA'
        color_multiply.blend_type = 'MULTIPLY'
        color_multiply.inputs['Factor'].default_value = 1.0

        value_to_color = nodes.new('ShaderNodeCombineColor')
        value_to_color.location = (-1000, 0)

        links.new(value_map.outputs['Result'], value_to_color.inputs['Red'])
        links.new(value_map.outputs['Result'], value_to_color.inputs['Green'])
        links.new(value_map.outputs['Result'], value_to_color.inputs['Blue'])

        links.new(hsv.outputs['Color'], color_multiply.inputs['A'])
        links.new(value_to_color.outputs['Color'], color_multiply.inputs['B'])

        links.new(color_multiply.outputs['Result'], principled.inputs['Base Color'])

        # =================================================================
        # FINITION (selon type de peinture choisi)
        # =================================================================

        # Mapper les types vers les presets
        finish_presets = {
            'MAT': {'finish': 0.0, 'quality': 0.85, 'roller': 0.006, 'support': 0.01, 'imperf': 0.001},
            'SATINEE': {'finish': 0.5, 'quality': 0.8, 'roller': 0.008, 'support': 0.01, 'imperf': 0.002},
            'BRILLANTE': {'finish': 1.0, 'quality': 0.75, 'roller': 0.012, 'support': 0.015, 'imperf': 0.003},
            'VELOURS': {'finish': 0.3, 'quality': 0.85, 'roller': 0.005, 'support': 0.008, 'imperf': 0.001},
        }

        preset = finish_presets.get(self.paint_type, finish_presets['SATINEE'])

        finish = nodes.new('ShaderNodeValue')
        finish.location = (-1400, -200)
        finish.outputs[0].default_value = preset['finish']
        finish.label = "✨ FINITION"

        rough_map = nodes.new('ShaderNodeMapRange')
        rough_map.location = (-1200, -200)
        rough_map.inputs['From Min'].default_value = 0.0
        rough_map.inputs['From Max'].default_value = 1.0
        rough_map.inputs['To Min'].default_value = 0.60
        rough_map.inputs['To Max'].default_value = 0.15

        links.new(finish.outputs['Value'], rough_map.inputs['Value'])

        # =================================================================
        # QUALITÉ DE PEINTURE
        # =================================================================

        quality = nodes.new('ShaderNodeValue')
        quality.location = (-1400, -350)
        quality.outputs[0].default_value = preset['quality']
        quality.label = "🏷️ QUALITÉ"

        grain_noise = nodes.new('ShaderNodeTexNoise')
        grain_noise.location = (-1200, -400)
        grain_noise.noise_dimensions = '3D'
        grain_noise.inputs['Scale'].default_value = 600
        grain_noise.inputs['Detail'].default_value = 8
        grain_noise.inputs['Roughness'].default_value = 0.6
        grain_noise.label = "Grain Peinture"

        links.new(mapping.outputs['Vector'], grain_noise.inputs['Vector'])

        quality_invert = nodes.new('ShaderNodeMath')
        quality_invert.location = (-1200, -550)
        quality_invert.operation = 'SUBTRACT'
        quality_invert.inputs[0].default_value = 1.0

        links.new(quality.outputs['Value'], quality_invert.inputs[1])

        grain_strength = nodes.new('ShaderNodeMath')
        grain_strength.location = (-1000, -450)
        grain_strength.operation = 'MULTIPLY'
        grain_strength.inputs[1].default_value = 0.06

        links.new(quality_invert.outputs['Value'], grain_strength.inputs[0])

        grain_map = nodes.new('ShaderNodeMapRange')
        grain_map.location = (-800, -400)
        grain_map.inputs['From Min'].default_value = 0.0
        grain_map.inputs['From Max'].default_value = 1.0
        grain_map.inputs['To Min'].default_value = -0.5
        grain_map.inputs['To Max'].default_value = 0.5

        links.new(grain_noise.outputs['Fac'], grain_map.inputs['Value'])

        grain_mult = nodes.new('ShaderNodeMath')
        grain_mult.location = (-600, -400)
        grain_mult.operation = 'MULTIPLY'

        links.new(grain_map.outputs['Result'], grain_mult.inputs[0])
        links.new(grain_strength.outputs['Value'], grain_mult.inputs[1])

        rough_add = nodes.new('ShaderNodeMath')
        rough_add.location = (-400, -250)
        rough_add.operation = 'ADD'

        links.new(rough_map.outputs['Result'], rough_add.inputs[0])
        links.new(grain_mult.outputs['Value'], rough_add.inputs[1])

        rough_clamp = nodes.new('ShaderNodeClamp')
        rough_clamp.location = (-200, -250)
        rough_clamp.inputs['Min'].default_value = 0.08
        rough_clamp.inputs['Max'].default_value = 0.85

        links.new(rough_add.outputs['Value'], rough_clamp.inputs['Value'])
        links.new(rough_clamp.outputs['Result'], principled.inputs['Roughness'])

        # =================================================================
        # TRACES DE ROULEAU
        # =================================================================

        roller = nodes.new('ShaderNodeTexWave')
        roller.location = (-600, -650)
        roller.wave_type = 'BANDS'
        roller.bands_direction = 'Y'
        roller.wave_profile = 'SIN'
        roller.inputs['Scale'].default_value = 120
        roller.inputs['Distortion'].default_value = 2.5
        roller.inputs['Detail'].default_value = 2
        roller.inputs['Detail Scale'].default_value = 0.8
        roller.label = "Traces Rouleau"

        links.new(mapping.outputs['Vector'], roller.inputs['Vector'])

        roller_strength = nodes.new('ShaderNodeValue')
        roller_strength.location = (-600, -800)
        roller_strength.outputs[0].default_value = preset['roller']
        roller_strength.label = "🖌️ TRACES ROULEAU"

        # =================================================================
        # TEXTURE DU SUPPORT
        # =================================================================

        support_noise = nodes.new('ShaderNodeTexNoise')
        support_noise.location = (-600, -950)
        support_noise.noise_dimensions = '3D'
        support_noise.noise_type = 'FBM'
        support_noise.inputs['Scale'].default_value = 50
        support_noise.inputs['Detail'].default_value = 6
        support_noise.inputs['Roughness'].default_value = 0.5
        support_noise.inputs['Lacunarity'].default_value = 2.0
        support_noise.label = "Texture Support"

        links.new(mapping.outputs['Vector'], support_noise.inputs['Vector'])

        support_strength = nodes.new('ShaderNodeValue')
        support_strength.location = (-600, -1100)
        support_strength.outputs[0].default_value = preset['support']
        support_strength.label = "🧱 TEXTURE MUR"

        # =================================================================
        # MICRO-IMPERFECTIONS
        # =================================================================

        imperfections = nodes.new('ShaderNodeTexVoronoi')
        imperfections.location = (-600, -1250)
        imperfections.voronoi_dimensions = '3D'
        imperfections.feature = 'F1'
        imperfections.inputs['Scale'].default_value = 400
        imperfections.inputs['Randomness'].default_value = 1.0
        imperfections.label = "Micro-bulles"

        links.new(mapping.outputs['Vector'], imperfections.inputs['Vector'])

        imperf_strength = nodes.new('ShaderNodeValue')
        imperf_strength.location = (-600, -1400)
        imperf_strength.outputs[0].default_value = preset['imperf']
        imperf_strength.label = "💧 IMPERFECTIONS"

        # =================================================================
        # COMBINAISON DES BUMPS
        # =================================================================

        bump_roller = nodes.new('ShaderNodeBump')
        bump_roller.location = (-200, -650)
        bump_roller.inputs['Distance'].default_value = 0.01

        links.new(roller.outputs['Fac'], bump_roller.inputs['Height'])
        links.new(roller_strength.outputs['Value'], bump_roller.inputs['Strength'])

        bump_support = nodes.new('ShaderNodeBump')
        bump_support.location = (0, -850)
        bump_support.inputs['Distance'].default_value = 0.01

        links.new(support_noise.outputs['Fac'], bump_support.inputs['Height'])
        links.new(support_strength.outputs['Value'], bump_support.inputs['Strength'])
        links.new(bump_roller.outputs['Normal'], bump_support.inputs['Normal'])

        bump_imperf = nodes.new('ShaderNodeBump')
        bump_imperf.location = (200, -1050)
        bump_imperf.inputs['Distance'].default_value = 0.005

        links.new(imperfections.outputs['Distance'], bump_imperf.inputs['Height'])
        links.new(imperf_strength.outputs['Value'], bump_imperf.inputs['Strength'])
        links.new(bump_support.outputs['Normal'], bump_imperf.inputs['Normal'])

        links.new(bump_imperf.outputs['Normal'], principled.inputs['Normal'])

        # Appliquer le matériau
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

        print(f"[WallPeinture] ✅ Shader réaliste appliqué: {PAINT_TYPES[self.paint_type]['name']}, couleur RGBA{self.color}")
