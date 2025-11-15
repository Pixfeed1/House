# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Gutter Materials Module
#  Copyright (C) 2025 mvaertan
#
#  Système de matériaux pour gouttières selon style architectural
#
# ##### END GPL LICENSE BLOCK #####

import bpy


# ============================================================
# MATÉRIAUX GOUTTIÈRES PAR STYLE
# ============================================================

def create_gutter_material(material_type='ALUMINUM', style='MODERN', quality='MEDIUM'):
    """Crée un matériau pour gouttière

    Args:
        material_type: Type de matériau ('ALUMINUM', 'COPPER', 'ZINC', 'PVC', 'STEEL')
        style: Style architectural (affecte la finition)
        quality: Niveau de détail du shader

    Returns:
        bpy.types.Material: Matériau créé
    """

    mat_name = f"Gutter_{material_type}_{style}"

    # Vérifier si le matériau existe déjà
    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    # Créer nouveau matériau
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Nettoyer nodes par défaut
    nodes.clear()

    # Créer nodes de base
    node_output = nodes.new('ShaderNodeOutputMaterial')
    node_output.location = (400, 0)

    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.location = (0, 0)

    # Connecter BSDF -> Output
    links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

    # Configurer selon le type de matériau
    if material_type == 'ALUMINUM':
        # Aluminium: gris métallique, peut être peint
        if style in ['MODERN', 'CONTEMPORARY']:
            # Aluminium blanc/gris clair moderne
            node_bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.85, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.9
            node_bsdf.inputs['Roughness'].default_value = 0.3
        else:
            # Aluminium naturel
            node_bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.75, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.95
            node_bsdf.inputs['Roughness'].default_value = 0.2

    elif material_type == 'COPPER':
        # Cuivre: aspect cuivré qui peut patiner
        if style == 'TRADITIONAL':
            # Cuivre patiné (vert-de-gris)
            node_bsdf.inputs['Base Color'].default_value = (0.3, 0.5, 0.4, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.6
            node_bsdf.inputs['Roughness'].default_value = 0.5
        else:
            # Cuivre neuf/brillant
            node_bsdf.inputs['Base Color'].default_value = (0.95, 0.64, 0.54, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 1.0
            node_bsdf.inputs['Roughness'].default_value = 0.1

    elif material_type == 'ZINC':
        # Zinc: gris bleuté mat
        node_bsdf.inputs['Base Color'].default_value = (0.65, 0.67, 0.70, 1.0)
        node_bsdf.inputs['Metallic'].default_value = 0.85
        node_bsdf.inputs['Roughness'].default_value = 0.4

    elif material_type == 'PVC':
        # PVC: plastique blanc ou gris
        if style in ['MODERN', 'CONTEMPORARY']:
            # PVC blanc brillant
            node_bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.0
            node_bsdf.inputs['Roughness'].default_value = 0.15
            node_bsdf.inputs['Specular'].default_value = 0.5
        else:
            # PVC gris/beige
            node_bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.68, 1.0)
            node_bsdf.inputs['Metallic'].default_value = 0.0
            node_bsdf.inputs['Roughness'].default_value = 0.3

    elif material_type == 'STEEL':
        # Acier galvanisé
        node_bsdf.inputs['Base Color'].default_value = (0.75, 0.75, 0.77, 1.0)
        node_bsdf.inputs['Metallic'].default_value = 0.95
        node_bsdf.inputs['Roughness'].default_value = 0.25

    # Ajouter variation si qualité HIGH
    if quality == 'HIGH':
        # Ajouter noise pour variation de surface
        node_noise = nodes.new('ShaderNodeTexNoise')
        node_noise.location = (-400, -200)
        node_noise.inputs['Scale'].default_value = 50.0

        node_colorramp = nodes.new('ShaderNodeValToRGB')
        node_colorramp.location = (-200, -200)
        node_colorramp.color_ramp.elements[0].position = 0.45
        node_colorramp.color_ramp.elements[1].position = 0.55

        links.new(node_noise.outputs['Fac'], node_colorramp.inputs['Fac'])
        links.new(node_colorramp.outputs['Fac'], node_bsdf.inputs['Roughness'])

    return mat


def create_downspout_material(material_type='ALUMINUM', style='MODERN', quality='MEDIUM'):
    """Crée un matériau pour tuyau de descente (downspout)

    Généralement identique au matériau de gouttière
    """
    return create_gutter_material(material_type, style, quality)


# ============================================================
# MAPPING STYLE ARCHITECTURAL -> MATÉRIAU GOUTTIÈRE
# ============================================================

def get_gutter_material_for_style(architectural_style, quality='MEDIUM'):
    """Détermine le matériau de gouttière selon le style architectural

    Args:
        architectural_style: Style architectural de la maison
        quality: Niveau de détail du shader

    Returns:
        bpy.types.Material: Matériau approprié
    """

    style_material_mapping = {
        'MODERN': ('ALUMINUM', 'MODERN'),
        'CONTEMPORARY': ('ALUMINUM', 'CONTEMPORARY'),
        'TRADITIONAL': ('COPPER', 'TRADITIONAL'),
        'MEDITERRANEAN': ('COPPER', 'TRADITIONAL'),
        'ASIAN': ('ZINC', 'MODERN'),
    }

    material_type, material_style = style_material_mapping.get(
        architectural_style,
        ('ALUMINUM', 'MODERN')  # Par défaut
    )

    return create_gutter_material(material_type, material_style, quality)


def apply_gutter_materials(gutter_objects, architectural_style='MODERN', quality='MEDIUM'):
    """Applique les matériaux appropriés aux objets gouttières

    Args:
        gutter_objects: Liste d'objets gouttières
        architectural_style: Style architectural
        quality: Niveau de détail

    Returns:
        int: Nombre d'objets modifiés
    """

    material = get_gutter_material_for_style(architectural_style, quality)

    count = 0
    for obj in gutter_objects:
        if obj.type == 'MESH':
            # Nettoyer matériaux existants
            obj.data.materials.clear()

            # Appliquer nouveau matériau
            obj.data.materials.append(material)
            count += 1

    return count


# ============================================================
# VARIANTES DE COULEURS (pour PVC peint)
# ============================================================

def create_painted_gutter_material(color=(1.0, 1.0, 1.0, 1.0), style='MODERN'):
    """Crée un matériau de gouttière peinte (PVC ou aluminium laqué)

    Args:
        color: Couleur RGBA
        style: Style architectural

    Returns:
        bpy.types.Material: Matériau créé
    """

    mat_name = f"Gutter_Painted_{int(color[0]*255)}_{int(color[1]*255)}_{int(color[2]*255)}"

    if mat_name in bpy.data.materials:
        return bpy.data.materials[mat_name]

    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    node_output = nodes.new('ShaderNodeOutputMaterial')
    node_output.location = (400, 0)

    node_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    node_bsdf.location = (0, 0)

    # Appliquer la couleur
    node_bsdf.inputs['Base Color'].default_value = color

    # Finition selon style
    if style in ['MODERN', 'CONTEMPORARY']:
        # Finition brillante
        node_bsdf.inputs['Metallic'].default_value = 0.0
        node_bsdf.inputs['Roughness'].default_value = 0.15
        node_bsdf.inputs['Specular'].default_value = 0.6
    else:
        # Finition mate
        node_bsdf.inputs['Metallic'].default_value = 0.0
        node_bsdf.inputs['Roughness'].default_value = 0.4
        node_bsdf.inputs['Specular'].default_value = 0.3

    links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

    return mat


# ============================================================
# PRESETS COULEURS POPULAIRES POUR GOUTTIÈRES
# ============================================================

GUTTER_COLOR_PRESETS = {
    'WHITE': (0.95, 0.95, 0.95, 1.0),
    'BLACK': (0.1, 0.1, 0.1, 1.0),
    'BROWN': (0.35, 0.25, 0.2, 1.0),
    'BEIGE': (0.85, 0.8, 0.7, 1.0),
    'GREY': (0.5, 0.5, 0.5, 1.0),
    'DARK_GREY': (0.3, 0.3, 0.3, 1.0),
    'COPPER': (0.95, 0.64, 0.54, 1.0),
    'GREEN': (0.2, 0.4, 0.25, 1.0),  # Patine cuivre
}


def get_preset_gutter_material(preset_name='WHITE', style='MODERN'):
    """Obtient un matériau de gouttière depuis un preset

    Args:
        preset_name: Nom du preset ('WHITE', 'BLACK', etc.)
        style: Style architectural

    Returns:
        bpy.types.Material: Matériau créé
    """

    color = GUTTER_COLOR_PRESETS.get(preset_name, GUTTER_COLOR_PRESETS['WHITE'])
    return create_painted_gutter_material(color, style)
