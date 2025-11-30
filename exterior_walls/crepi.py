"""
CRÉPI / ENDUIT EXTÉRIEUR
=========================
Générateur de finitions extérieures en crépi/enduit pour les façades.

Adapté du script universel pour l'intégration dans l'extension House.
Compatible avec murs simples et briques 3D.
Gère automatiquement les ouvertures (portes et fenêtres).

Blender 4.2+
"""

import bpy
import bmesh
import math
import random
from mathutils import Vector, noise, Matrix


# =================================================================
# PRESETS COULEUR CRÉPI
# =================================================================

CREPI_COLOR_PRESETS = {
    'BLANC': (0.92, 0.91, 0.89),
    'BLANC_CASSE': (0.90, 0.87, 0.82),
    'IVOIRE': (0.88, 0.85, 0.78),
    'SABLE': (0.82, 0.76, 0.65),
    'BEIGE': (0.78, 0.72, 0.62),
    'OCRE': (0.80, 0.68, 0.45),
    'TERRE': (0.60, 0.48, 0.38),
    'ROSE': (0.85, 0.75, 0.72),
    'PECHE': (0.88, 0.78, 0.68),
    'TERRACOTTA': (0.72, 0.48, 0.35),
    'GRIS_CLAIR': (0.75, 0.74, 0.72),
    'GRIS': (0.55, 0.54, 0.52),
    'GRIS_ANTHRACITE': (0.25, 0.25, 0.26),
    'TAUPE': (0.48, 0.44, 0.40),
}


# =================================================================
# CLASSE PRINCIPALE
# =================================================================

class ExteriorCrepi:
    """Générateur de crépi/enduit pour façades extérieures"""

    def __init__(self,
                 plaster_type='GRATTE',
                 color_preset='BLANC_CASSE',
                 custom_color=None,
                 grain_size=0.5,
                 grain_intensity=0.5,
                 color_variation=0.08,
                 dirt=0.1,
                 water_stains=0.05,
                 moss=0.0,
                 cracks=0.05,
                 aging=0.1,
                 random_seed=42):
        """
        Initialise le générateur de crépi.

        Args:
            plaster_type: Type de crépi (GRATTE, TALOCHE, RIBBE, ECRASE, PROJETE, LISSE)
            color_preset: Preset de couleur ou 'CUSTOM'
            custom_color: Couleur RGB personnalisée si color_preset='CUSTOM'
            grain_size: Taille du grain (0.1 - 1.0)
            grain_intensity: Intensité du relief (0.0 - 1.0)
            color_variation: Variation de teinte (0.0 - 0.3)
            dirt: Niveau de salissures (0.0 - 1.0)
            water_stains: Traces d'eau (0.0 - 1.0)
            moss: Mousse/algues (0.0 - 1.0)
            cracks: Fissures (0.0 - 1.0)
            aging: Vieillissement (0.0 - 1.0)
            random_seed: Seed pour variation aléatoire
        """
        self.plaster_type = plaster_type
        self.color_preset = color_preset
        self.custom_color = custom_color
        self.grain_size = grain_size
        self.grain_intensity = grain_intensity
        self.color_variation = color_variation
        self.dirt = dirt
        self.water_stains = water_stains
        self.moss = moss
        self.cracks = cracks
        self.aging = aging
        self.random_seed = random_seed

        # Déterminer la couleur finale
        if color_preset == 'CUSTOM' and custom_color:
            self.base_color = custom_color
        else:
            self.base_color = CREPI_COLOR_PRESETS.get(color_preset, CREPI_COLOR_PRESETS['BLANC_CASSE'])

        print(f"[ExteriorCrepi] Type: {plaster_type}, Couleur: {color_preset}")

    def generate_for_wall(self, wall_obj, wall_width, wall_height, wall_thickness, orientation='front'):
        """
        Génère le crépi pour un mur existant.

        Args:
            wall_obj: Objet mur existant (ou None pour créer nouveau)
            wall_width: Largeur du mur
            wall_height: Hauteur du mur
            wall_thickness: Épaisseur du mur
            orientation: Orientation ('front', 'back', 'left', 'right')

        Returns:
            Objet Blender avec le crépi appliqué
        """
        random.seed(self.random_seed)

        # Si le mur existe déjà (briques 3D), on applique juste le matériau
        if wall_obj and wall_obj.data:
            print(f"[ExteriorCrepi] Application sur mur existant ({orientation})")
            mat = self.create_plaster_material(f"Crepi_{orientation}")

            # Remplacer ou ajouter le matériau
            if len(wall_obj.data.materials) > 0:
                wall_obj.data.materials[0] = mat
            else:
                wall_obj.data.materials.append(mat)

            return wall_obj

        # Sinon, créer un plan de crépi (pour murs simples)
        print(f"[ExteriorCrepi] Création nouveau plan de crépi ({orientation})")
        obj = self.create_crepi_plane(wall_width, wall_height, wall_thickness, orientation)

        mat = self.create_plaster_material(f"Crepi_{orientation}")
        obj.data.materials.append(mat)

        return obj

    def create_crepi_plane(self, width, height, thickness, orientation):
        """Crée un plan de crépi avec relief pour murs simples"""

        bm = bmesh.new()

        # ✅ FIX: Protection division par zéro si dimensions nulles
        max_dim = max(width, height)
        if max_dim < 0.01:  # Dimensions trop petites
            print(f"[ExteriorCrepi] ⚠️ Dimensions invalides: width={width:.3f}, height={height:.3f}")
            max_dim = 1.0  # Valeur par défaut pour éviter division par zéro

        # Subdivisions adaptées
        sub_x = max(8, int(32 * (width / max_dim)))
        sub_y = max(8, int(32 * (height / max_dim)))

        # Créer grille
        bmesh.ops.create_grid(bm, x_segments=sub_x, y_segments=sub_y, size=1.0)

        # Redimensionner
        bmesh.ops.scale(bm, vec=(width/2, height/2, 1), verts=bm.verts)

        # Rotation verticale (face en Y)
        angle_x = math.radians(90)
        rot_matrix = Matrix.Rotation(angle_x, 3, 'X')
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0,0,0), matrix=rot_matrix)

        # Déplacer pour avoir base au sol et centré
        bmesh.ops.translate(bm, vec=(width/2, thickness/2, height/2), verts=bm.verts)

        # Appliquer relief
        self.apply_plaster_displacement(bm, width, height)

        # Calculer normales
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])

        # Créer mesh
        mesh = bpy.data.meshes.new(f"Crepi_Plane_{orientation}")
        bm.to_mesh(mesh)
        bm.free()

        # Smooth shading
        for poly in mesh.polygons:
            poly.use_smooth = True

        # Créer objet
        obj = bpy.data.objects.new(f"Crepi_{orientation}", mesh)

        return obj

    def apply_plaster_displacement(self, bm, width, height):
        """Applique le relief du crépi au mesh"""

        intensity = self.grain_intensity * 0.003
        scale = 50.0 / self.grain_size

        for v in bm.verts:
            # Position pour le noise
            pos = Vector((v.co.x * scale, v.co.z * scale, self.random_seed))

            if self.plaster_type == 'GRATTE':
                # Gratté : noise + stries horizontales
                n = noise.noise(pos) * 0.7
                n += noise.noise(Vector((v.co.x * 200, v.co.z * 20, self.random_seed))) * 0.3

            elif self.plaster_type == 'TALOCHE':
                # Taloché : noise lisse
                n = noise.noise(Vector((pos.x * 0.5, pos.y * 0.5, pos.z)))

            elif self.plaster_type == 'RIBBE':
                # Ribbé : stries verticales
                n = math.sin(v.co.x * scale * 0.8) * 0.5
                n += noise.noise(pos) * 0.5

            elif self.plaster_type == 'ECRASE':
                # Écrasé : motif aplati irrégulier
                n = noise.noise(pos) * 0.6
                n += noise.noise(Vector((pos.x * 0.3, pos.y * 0.3, pos.z))) * 0.4

            elif self.plaster_type == 'PROJETE':
                # Projeté : très rugueux
                n = noise.noise(pos)
                n += noise.noise(Vector((pos.x * 2, pos.y * 2, pos.z))) * 0.5
                intensity *= 1.5

            else:  # LISSE
                # Lisse : très peu de relief
                n = noise.noise(Vector((pos.x * 0.3, pos.y * 0.3, pos.z)))
                intensity *= 0.3

            # Appliquer le déplacement en Y (normal du mur)
            v.co.y += n * intensity

    def create_plaster_material(self, mat_name):
        """Crée le shader de crépi universel"""

        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        x = -2200
        y = 400

        # === OUTPUT ===
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (800, 0)

        # === PRINCIPLED BSDF ===
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (500, 0)
        principled.inputs['Roughness'].default_value = self.get_base_roughness()
        principled.inputs['IOR'].default_value = 1.45

        # Blender 4.2 compatible
        try:
            principled.inputs['Specular IOR Level'].default_value = 0.3
        except KeyError:
            try:
                principled.inputs['Specular'].default_value = 0.3
            except KeyError:
                pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        # === COORDONNÉES ===
        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Location'].default_value = (
            self.random_seed * 4.7,
            self.random_seed * 7.3,
            self.random_seed * 2.9
        )

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        # === COULEUR DE BASE (EXPOSÉE) ===
        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 400, y + 400)
        base_col.outputs[0].default_value = (*self.base_color, 1.0)
        base_col.label = "🎨 COULEUR CRÉPI"

        # === TEXTURE DU GRAIN ===
        grain_scale = 60.0 / self.grain_size

        grain_noise = nodes.new('ShaderNodeTexNoise')
        grain_noise.location = (x + 400, y)
        grain_noise.inputs['Scale'].default_value = grain_scale
        grain_noise.inputs['Detail'].default_value = 8.0
        grain_noise.inputs['Roughness'].default_value = 0.7
        grain_noise.inputs['Distortion'].default_value = 0.3

        links.new(mapping.outputs['Vector'], grain_noise.inputs['Vector'])

        # Texture spécifique selon le type
        grain_output, type_texture = self.create_type_texture(nodes, links, mapping, grain_noise, x, y, grain_scale)

        # === VARIATION DE COULEUR ===
        color_var_noise = nodes.new('ShaderNodeTexNoise')
        color_var_noise.location = (x + 400, y + 200)
        color_var_noise.inputs['Scale'].default_value = 3.0
        color_var_noise.inputs['Detail'].default_value = 4.0
        color_var_noise.inputs['Roughness'].default_value = 0.5

        links.new(mapping.outputs['Vector'], color_var_noise.inputs['Vector'])

        color_var_mix = nodes.new('ShaderNodeMix')
        color_var_mix.location = (x + 800, y + 350)
        color_var_mix.data_type = 'RGBA'
        color_var_mix.blend_type = 'OVERLAY'
        color_var_mix.inputs['Factor'].default_value = self.color_variation

        links.new(base_col.outputs[0], color_var_mix.inputs['A'])
        links.new(color_var_noise.outputs['Color'], color_var_mix.inputs['B'])

        current_color = color_var_mix.outputs['Result']

        # === IMPERFECTIONS ===
        current_color = self.add_imperfections(nodes, links, mapping, current_color, x, y)

        # Connecter couleur finale
        links.new(current_color, principled.inputs['Base Color'])

        # === ROUGHNESS ===
        self.add_roughness_variation(nodes, links, mapping, principled, x, y)

        # === BUMP ===
        self.add_bump(nodes, links, mapping, grain_output, principled, x, y)

        return mat

    def create_type_texture(self, nodes, links, mapping, grain_noise, x, y, grain_scale):
        """Crée la texture spécifique au type de crépi"""

        if self.plaster_type == 'GRATTE':
            # Stries horizontales
            wave = nodes.new('ShaderNodeTexWave')
            wave.location = (x + 400, y - 200)
            wave.wave_type = 'BANDS'
            wave.bands_direction = 'X'
            wave.wave_profile = 'SAW'
            wave.inputs['Scale'].default_value = grain_scale * 0.3
            wave.inputs['Distortion'].default_value = 5.0
            wave.inputs['Detail'].default_value = 2.0

            links.new(mapping.outputs['Vector'], wave.inputs['Vector'])

            grain_mix = nodes.new('ShaderNodeMix')
            grain_mix.location = (x + 600, y - 100)
            grain_mix.data_type = 'FLOAT'
            grain_mix.inputs['Factor'].default_value = 0.5

            links.new(grain_noise.outputs['Fac'], grain_mix.inputs['A'])
            links.new(wave.outputs['Fac'], grain_mix.inputs['B'])

            return grain_mix.outputs['Result'], wave

        elif self.plaster_type == 'RIBBE':
            # Stries verticales
            wave = nodes.new('ShaderNodeTexWave')
            wave.location = (x + 400, y - 200)
            wave.wave_type = 'BANDS'
            wave.bands_direction = 'Z'
            wave.wave_profile = 'SIN'
            wave.inputs['Scale'].default_value = grain_scale * 0.4
            wave.inputs['Distortion'].default_value = 2.0

            links.new(mapping.outputs['Vector'], wave.inputs['Vector'])

            grain_mix = nodes.new('ShaderNodeMix')
            grain_mix.location = (x + 600, y - 100)
            grain_mix.data_type = 'FLOAT'
            grain_mix.inputs['Factor'].default_value = 0.5

            links.new(grain_noise.outputs['Fac'], grain_mix.inputs['A'])
            links.new(wave.outputs['Fac'], grain_mix.inputs['B'])

            return grain_mix.outputs['Result'], wave

        elif self.plaster_type == 'PROJETE':
            # Voronoi projeté
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.location = (x + 400, y - 200)
            voronoi.voronoi_dimensions = '3D'
            voronoi.feature = 'F1'
            voronoi.inputs['Scale'].default_value = grain_scale * 1.5
            voronoi.inputs['Randomness'].default_value = 1.0

            links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])

            grain_mix = nodes.new('ShaderNodeMix')
            grain_mix.location = (x + 600, y - 100)
            grain_mix.data_type = 'FLOAT'
            grain_mix.inputs['Factor'].default_value = 0.6

            links.new(grain_noise.outputs['Fac'], grain_mix.inputs['A'])
            links.new(voronoi.outputs['Distance'], grain_mix.inputs['B'])

            return grain_mix.outputs['Result'], voronoi

        elif self.plaster_type == 'ECRASE':
            # Voronoi écrasé
            voronoi = nodes.new('ShaderNodeTexVoronoi')
            voronoi.location = (x + 400, y - 200)
            voronoi.voronoi_dimensions = '3D'
            voronoi.feature = 'SMOOTH_F1'
            voronoi.inputs['Scale'].default_value = grain_scale * 0.8
            voronoi.inputs['Smoothness'].default_value = 0.5

            links.new(mapping.outputs['Vector'], voronoi.inputs['Vector'])

            grain_mix = nodes.new('ShaderNodeMix')
            grain_mix.location = (x + 600, y - 100)
            grain_mix.data_type = 'FLOAT'
            grain_mix.inputs['Factor'].default_value = 0.5

            links.new(grain_noise.outputs['Fac'], grain_mix.inputs['A'])
            links.new(voronoi.outputs['Distance'], grain_mix.inputs['B'])

            return grain_mix.outputs['Result'], voronoi

        else:  # TALOCHE ou LISSE
            return grain_noise.outputs['Fac'], grain_noise

    def add_imperfections(self, nodes, links, mapping, current_color, x, y):
        """Ajoute les imperfections (salissures, eau, mousse, vieillissement)"""

        # Salissures
        if self.dirt > 0:
            dirt_noise = nodes.new('ShaderNodeTexNoise')
            dirt_noise.location = (x + 600, y - 400)
            dirt_noise.inputs['Scale'].default_value = 2.0
            dirt_noise.inputs['Detail'].default_value = 6.0
            dirt_noise.inputs['Roughness'].default_value = 0.8

            links.new(mapping.outputs['Vector'], dirt_noise.inputs['Vector'])

            dirt_color = nodes.new('ShaderNodeRGB')
            dirt_color.location = (x + 800, y - 400)
            dirt_color.outputs[0].default_value = (0.15, 0.14, 0.12, 1.0)

            dirt_mix = nodes.new('ShaderNodeMix')
            dirt_mix.location = (x + 1000, y + 300)
            dirt_mix.data_type = 'RGBA'

            dirt_intensity = nodes.new('ShaderNodeMath')
            dirt_intensity.location = (x + 800, y - 300)
            dirt_intensity.operation = 'MULTIPLY'
            dirt_intensity.inputs[1].default_value = self.dirt * 0.4

            links.new(dirt_noise.outputs['Fac'], dirt_intensity.inputs[0])
            links.new(dirt_intensity.outputs['Value'], dirt_mix.inputs['Factor'])
            links.new(current_color, dirt_mix.inputs['A'])
            links.new(dirt_color.outputs[0], dirt_mix.inputs['B'])

            current_color = dirt_mix.outputs['Result']

        # Traces d'eau
        if self.water_stains > 0:
            water_noise = nodes.new('ShaderNodeTexNoise')
            water_noise.location = (x + 600, y - 600)
            water_noise.inputs['Scale'].default_value = 5.0
            water_noise.inputs['Detail'].default_value = 3.0
            water_noise.inputs['Distortion'].default_value = 3.0

            links.new(mapping.outputs['Vector'], water_noise.inputs['Vector'])

            gradient = nodes.new('ShaderNodeTexGradient')
            gradient.location = (x + 600, y - 750)
            gradient.gradient_type = 'LINEAR'

            gradient_mapping = nodes.new('ShaderNodeMapping')
            gradient_mapping.location = (x + 400, y - 750)
            gradient_mapping.inputs['Rotation'].default_value = (0, 0, math.radians(90))

            links.new(mapping.outputs['Vector'], gradient_mapping.inputs['Vector'])
            links.new(gradient_mapping.outputs['Vector'], gradient.inputs['Vector'])

            water_combine = nodes.new('ShaderNodeMath')
            water_combine.location = (x + 800, y - 650)
            water_combine.operation = 'MULTIPLY'

            links.new(water_noise.outputs['Fac'], water_combine.inputs[0])
            links.new(gradient.outputs['Fac'], water_combine.inputs[1])

            water_color = nodes.new('ShaderNodeRGB')
            water_color.location = (x + 800, y - 800)
            water_color.outputs[0].default_value = (0.25, 0.23, 0.20, 1.0)

            water_mix = nodes.new('ShaderNodeMix')
            water_mix.location = (x + 1200, y + 250)
            water_mix.data_type = 'RGBA'

            water_intensity = nodes.new('ShaderNodeMath')
            water_intensity.location = (x + 1000, y - 650)
            water_intensity.operation = 'MULTIPLY'
            water_intensity.inputs[1].default_value = self.water_stains * 0.5

            links.new(water_combine.outputs['Value'], water_intensity.inputs[0])
            links.new(water_intensity.outputs['Value'], water_mix.inputs['Factor'])
            links.new(current_color, water_mix.inputs['A'])
            links.new(water_color.outputs[0], water_mix.inputs['B'])

            current_color = water_mix.outputs['Result']

        # Mousse
        if self.moss > 0:
            moss_noise = nodes.new('ShaderNodeTexNoise')
            moss_noise.location = (x + 600, y - 900)
            moss_noise.inputs['Scale'].default_value = 8.0
            moss_noise.inputs['Detail'].default_value = 5.0

            links.new(mapping.outputs['Vector'], moss_noise.inputs['Vector'])

            moss_color = nodes.new('ShaderNodeRGB')
            moss_color.location = (x + 800, y - 950)
            moss_color.outputs[0].default_value = (0.15, 0.22, 0.10, 1.0)

            moss_mix = nodes.new('ShaderNodeMix')
            moss_mix.location = (x + 1400, y + 200)
            moss_mix.data_type = 'RGBA'

            moss_intensity = nodes.new('ShaderNodeMath')
            moss_intensity.location = (x + 1000, y - 900)
            moss_intensity.operation = 'MULTIPLY'
            moss_intensity.inputs[1].default_value = self.moss * 0.6

            links.new(moss_noise.outputs['Fac'], moss_intensity.inputs[0])
            links.new(moss_intensity.outputs['Value'], moss_mix.inputs['Factor'])
            links.new(current_color, moss_mix.inputs['A'])
            links.new(moss_color.outputs[0], moss_mix.inputs['B'])

            current_color = moss_mix.outputs['Result']

        # Vieillissement
        if self.aging > 0:
            age_darken = nodes.new('ShaderNodeMix')
            age_darken.location = (x + 1600, y + 150)
            age_darken.data_type = 'RGBA'
            age_darken.blend_type = 'MULTIPLY'
            age_darken.inputs['Factor'].default_value = self.aging * 0.3

            age_color = nodes.new('ShaderNodeRGB')
            age_color.location = (x + 1400, y + 50)
            age_color.outputs[0].default_value = (0.8, 0.78, 0.75, 1.0)

            links.new(current_color, age_darken.inputs['A'])
            links.new(age_color.outputs[0], age_darken.inputs['B'])

            current_color = age_darken.outputs['Result']

        return current_color

    def add_roughness_variation(self, nodes, links, mapping, principled, x, y):
        """Ajoute variation de roughness"""

        rough_base = self.get_base_roughness()

        rough_noise = nodes.new('ShaderNodeTexNoise')
        rough_noise.location = (x + 1000, y - 200)
        rough_noise.inputs['Scale'].default_value = 40.0
        rough_noise.inputs['Detail'].default_value = 5.0

        links.new(mapping.outputs['Vector'], rough_noise.inputs['Vector'])

        rough_map = nodes.new('ShaderNodeMapRange')
        rough_map.location = (x + 1200, y - 200)
        rough_map.inputs['From Min'].default_value = 0.3
        rough_map.inputs['From Max'].default_value = 0.7
        rough_map.inputs['To Min'].default_value = rough_base - 0.1
        rough_map.inputs['To Max'].default_value = rough_base + 0.15

        links.new(rough_noise.outputs['Fac'], rough_map.inputs['Value'])
        links.new(rough_map.outputs['Result'], principled.inputs['Roughness'])

    def add_bump(self, nodes, links, mapping, grain_output, principled, x, y):
        """Ajoute bump mapping (grain + fissures)"""

        bump_main = nodes.new('ShaderNodeBump')
        bump_main.location = (x + 1200, y - 50)
        bump_main.inputs['Strength'].default_value = self.grain_intensity * 0.4

        links.new(grain_output, bump_main.inputs['Height'])

        current_normal = bump_main.outputs['Normal']

        # Fissures
        if self.cracks > 0:
            crack_voronoi = nodes.new('ShaderNodeTexVoronoi')
            crack_voronoi.location = (x + 800, y - 1100)
            crack_voronoi.voronoi_dimensions = '3D'
            crack_voronoi.feature = 'DISTANCE_TO_EDGE'
            crack_voronoi.inputs['Scale'].default_value = 4.0
            crack_voronoi.inputs['Randomness'].default_value = 1.0

            links.new(mapping.outputs['Vector'], crack_voronoi.inputs['Vector'])

            crack_thresh = nodes.new('ShaderNodeMapRange')
            crack_thresh.location = (x + 1000, y - 1100)
            crack_thresh.inputs['From Min'].default_value = 0.0
            crack_thresh.inputs['From Max'].default_value = 0.02
            crack_thresh.clamp = True

            links.new(crack_voronoi.outputs['Distance'], crack_thresh.inputs['Value'])

            crack_bump = nodes.new('ShaderNodeBump')
            crack_bump.location = (x + 1400, y - 50)
            crack_bump.inputs['Strength'].default_value = self.cracks * 0.3
            crack_bump.invert = True

            links.new(crack_thresh.outputs['Result'], crack_bump.inputs['Height'])
            links.new(current_normal, crack_bump.inputs['Normal'])

            current_normal = crack_bump.outputs['Normal']

        links.new(current_normal, principled.inputs['Normal'])

    def get_base_roughness(self):
        """Retourne la roughness de base selon le type"""
        roughness_values = {
            'GRATTE': 0.75,
            'TALOCHE': 0.55,
            'RIBBE': 0.70,
            'ECRASE': 0.65,
            'PROJETE': 0.85,
            'LISSE': 0.40,
        }
        return roughness_values.get(self.plaster_type, 0.65)
