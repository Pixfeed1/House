"""
WINDOW GEOMETRY NODES - Système de génération procédurale
==========================================================
Crée des fenêtres via geometry nodes pour performance et flexibilité.

Avantages :
- Performance GPU
- Paramétrique (modifiable en temps réel)
- Non-destructif
- Éditable dans l'interface Blender
"""

import bpy
from mathutils import Vector


# =================================================================
# CONSTANTES
# =================================================================

FRAME_DEPTH = 0.07  # 70mm - Profondeur du dormant
GLASS_THICKNESS = 0.02  # 20mm - Double vitrage


# =================================================================
# CRÉATION DES NODE GROUPS
# =================================================================

def create_window_frame_nodegroup():
    """Crée le node group pour générer un cadre de fenêtre rectangulaire

    Inputs:
        - Width (Float)
        - Height (Float)
        - Frame Width (Float)
        - Frame Depth (Float)

    Output:
        - Geometry (cadre complet)
    """

    # Vérifier si le node group existe déjà
    group_name = "Window_Frame_Generator"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    # Créer le node group
    node_group = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')

    # Créer les sockets d'entrée/sortie
    group_inputs = node_group.interface.new_socket(
        name='Width',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    group_inputs.default_value = 1.2
    group_inputs.min_value = 0.1
    group_inputs.max_value = 5.0

    group_inputs = node_group.interface.new_socket(
        name='Height',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    group_inputs.default_value = 1.4
    group_inputs.min_value = 0.1
    group_inputs.max_value = 5.0

    group_inputs = node_group.interface.new_socket(
        name='Frame Width',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    group_inputs.default_value = 0.05
    group_inputs.min_value = 0.01
    group_inputs.max_value = 0.2

    group_inputs = node_group.interface.new_socket(
        name='Frame Depth',
        in_out='INPUT',
        socket_type='NodeSocketFloat'
    )
    group_inputs.default_value = FRAME_DEPTH

    group_outputs = node_group.interface.new_socket(
        name='Geometry',
        in_out='OUTPUT',
        socket_type='NodeSocketGeometry'
    )

    # Créer les nodes
    nodes = node_group.nodes
    links = node_group.links

    # Input/Output nodes
    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-1400, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (1200, 0)

    x_start = -1200
    y_offset = 0

    # === CADRE HAUT ===
    cube_top = nodes.new('GeometryNodeMeshCube')
    cube_top.location = (x_start, y_offset)

    # Calculer la taille : (Width, Depth, Frame_Width)
    combine_top_size = nodes.new('ShaderNodeCombineXYZ')
    combine_top_size.location = (x_start - 200, y_offset - 150)

    links.new(input_node.outputs['Width'], combine_top_size.inputs['X'])
    links.new(input_node.outputs['Frame Depth'], combine_top_size.inputs['Y'])
    links.new(input_node.outputs['Frame Width'], combine_top_size.inputs['Z'])
    links.new(combine_top_size.outputs['Vector'], cube_top.inputs['Size'])

    # Position haut : (0, 0, Height/2 - FrameWidth/2)
    transform_top = nodes.new('GeometryNodeTransform')
    transform_top.location = (x_start + 200, y_offset)

    # Calculer Z = Height/2 - FrameWidth/2
    height_half = nodes.new('ShaderNodeMath')
    height_half.location = (x_start - 400, y_offset + 200)
    height_half.operation = 'DIVIDE'
    height_half.inputs[1].default_value = 2.0
    links.new(input_node.outputs['Height'], height_half.inputs[0])

    frame_half = nodes.new('ShaderNodeMath')
    frame_half.location = (x_start - 400, y_offset + 50)
    frame_half.operation = 'DIVIDE'
    frame_half.inputs[1].default_value = 2.0
    links.new(input_node.outputs['Frame Width'], frame_half.inputs[0])

    top_z = nodes.new('ShaderNodeMath')
    top_z.location = (x_start - 200, y_offset + 125)
    top_z.operation = 'SUBTRACT'
    links.new(height_half.outputs['Value'], top_z.inputs[0])
    links.new(frame_half.outputs['Value'], top_z.inputs[1])

    combine_top_pos = nodes.new('ShaderNodeCombineXYZ')
    combine_top_pos.location = (x_start, y_offset + 125)
    combine_top_pos.inputs['X'].default_value = 0.0
    combine_top_pos.inputs['Y'].default_value = FRAME_DEPTH / 2
    links.new(top_z.outputs['Value'], combine_top_pos.inputs['Z'])

    links.new(cube_top.outputs['Mesh'], transform_top.inputs['Geometry'])
    links.new(combine_top_pos.outputs['Vector'], transform_top.inputs['Translation'])

    # === CADRE BAS (miroir du haut) ===
    cube_bottom = nodes.new('GeometryNodeMeshCube')
    cube_bottom.location = (x_start, y_offset - 300)
    links.new(combine_top_size.outputs['Vector'], cube_bottom.inputs['Size'])

    transform_bottom = nodes.new('GeometryNodeTransform')
    transform_bottom.location = (x_start + 200, y_offset - 300)

    # Position bas : Z = -Height/2 + FrameWidth/2
    bottom_z = nodes.new('ShaderNodeMath')
    bottom_z.location = (x_start - 200, y_offset - 175)
    bottom_z.operation = 'SUBTRACT'
    bottom_z.inputs[1].default_value = 0.0
    links.new(top_z.outputs['Value'], bottom_z.inputs[0])

    negate_bottom = nodes.new('ShaderNodeMath')
    negate_bottom.location = (x_start, y_offset - 175)
    negate_bottom.operation = 'MULTIPLY'
    negate_bottom.inputs[1].default_value = -1.0
    links.new(bottom_z.outputs['Value'], negate_bottom.inputs[0])

    combine_bottom_pos = nodes.new('ShaderNodeCombineXYZ')
    combine_bottom_pos.location = (x_start, y_offset - 275)
    combine_bottom_pos.inputs['X'].default_value = 0.0
    combine_bottom_pos.inputs['Y'].default_value = FRAME_DEPTH / 2
    links.new(negate_bottom.outputs['Value'], combine_bottom_pos.inputs['Z'])

    links.new(cube_bottom.outputs['Mesh'], transform_bottom.inputs['Geometry'])
    links.new(combine_bottom_pos.outputs['Vector'], transform_bottom.inputs['Translation'])

    # === CADRE GAUCHE ===
    cube_left = nodes.new('GeometryNodeMeshCube')
    cube_left.location = (x_start, y_offset - 600)

    # Taille : (Frame_Width, Depth, Height)
    combine_left_size = nodes.new('ShaderNodeCombineXYZ')
    combine_left_size.location = (x_start - 200, y_offset - 750)
    links.new(input_node.outputs['Frame Width'], combine_left_size.inputs['X'])
    links.new(input_node.outputs['Frame Depth'], combine_left_size.inputs['Y'])
    links.new(input_node.outputs['Height'], combine_left_size.inputs['Z'])
    links.new(combine_left_size.outputs['Vector'], cube_left.inputs['Size'])

    transform_left = nodes.new('GeometryNodeTransform')
    transform_left.location = (x_start + 200, y_offset - 600)

    # Position gauche : X = -Width/2 + FrameWidth/2
    width_half = nodes.new('ShaderNodeMath')
    width_half.location = (x_start - 400, y_offset - 500)
    width_half.operation = 'DIVIDE'
    width_half.inputs[1].default_value = 2.0
    links.new(input_node.outputs['Width'], width_half.inputs[0])

    left_x = nodes.new('ShaderNodeMath')
    left_x.location = (x_start - 200, y_offset - 500)
    left_x.operation = 'SUBTRACT'
    links.new(frame_half.outputs['Value'], left_x.inputs[0])
    links.new(width_half.outputs['Value'], left_x.inputs[1])

    combine_left_pos = nodes.new('ShaderNodeCombineXYZ')
    combine_left_pos.location = (x_start, y_offset - 675)
    links.new(left_x.outputs['Value'], combine_left_pos.inputs['X'])
    combine_left_pos.inputs['Y'].default_value = FRAME_DEPTH / 2
    combine_left_pos.inputs['Z'].default_value = 0.0

    links.new(cube_left.outputs['Mesh'], transform_left.inputs['Geometry'])
    links.new(combine_left_pos.outputs['Vector'], transform_left.inputs['Translation'])

    # === CADRE DROIT (miroir du gauche) ===
    cube_right = nodes.new('GeometryNodeMeshCube')
    cube_right.location = (x_start, y_offset - 900)
    links.new(combine_left_size.outputs['Vector'], cube_right.inputs['Size'])

    transform_right = nodes.new('GeometryNodeTransform')
    transform_right.location = (x_start + 200, y_offset - 900)

    # Position droite : X = Width/2 - FrameWidth/2
    right_x = nodes.new('ShaderNodeMath')
    right_x.location = (x_start - 200, y_offset - 800)
    right_x.operation = 'SUBTRACT'
    links.new(width_half.outputs['Value'], right_x.inputs[0])
    links.new(frame_half.outputs['Value'], right_x.inputs[1])

    combine_right_pos = nodes.new('ShaderNodeCombineXYZ')
    combine_right_pos.location = (x_start, y_offset - 975)
    links.new(right_x.outputs['Value'], combine_right_pos.inputs['X'])
    combine_right_pos.inputs['Y'].default_value = FRAME_DEPTH / 2
    combine_right_pos.inputs['Z'].default_value = 0.0

    links.new(cube_right.outputs['Mesh'], transform_right.inputs['Geometry'])
    links.new(combine_right_pos.outputs['Vector'], transform_right.inputs['Translation'])

    # === JOINDRE TOUT ===
    join_1 = nodes.new('GeometryNodeJoinGeometry')
    join_1.location = (x_start + 500, y_offset - 150)
    links.new(transform_top.outputs['Geometry'], join_1.inputs['Geometry'])
    links.new(transform_bottom.outputs['Geometry'], join_1.inputs['Geometry'])

    join_2 = nodes.new('GeometryNodeJoinGeometry')
    join_2.location = (x_start + 700, y_offset - 450)
    links.new(join_1.outputs['Geometry'], join_2.inputs['Geometry'])
    links.new(transform_left.outputs['Geometry'], join_2.inputs['Geometry'])

    join_final = nodes.new('GeometryNodeJoinGeometry')
    join_final.location = (x_start + 900, y_offset - 600)
    links.new(join_2.outputs['Geometry'], join_final.inputs['Geometry'])
    links.new(transform_right.outputs['Geometry'], join_final.inputs['Geometry'])

    # Connecter au output
    links.new(join_final.outputs['Geometry'], output_node.inputs['Geometry'])

    print(f"[GeoNodes] Node group créé: {group_name}")
    return node_group


def create_window_glass_nodegroup():
    """Crée le node group pour générer le vitrage

    Inputs:
        - Width (Float)
        - Height (Float)
        - Frame Width (Float)
        - Glass Thickness (Float)

    Output:
        - Geometry (vitrage)
    """

    group_name = "Window_Glass_Generator"
    if group_name in bpy.data.node_groups:
        return bpy.data.node_groups[group_name]

    node_group = bpy.data.node_groups.new(name=group_name, type='GeometryNodeTree')

    # Sockets
    node_group.interface.new_socket(name='Width', in_out='INPUT', socket_type='NodeSocketFloat').default_value = 1.2
    node_group.interface.new_socket(name='Height', in_out='INPUT', socket_type='NodeSocketFloat').default_value = 1.4
    node_group.interface.new_socket(name='Frame Width', in_out='INPUT', socket_type='NodeSocketFloat').default_value = 0.05
    node_group.interface.new_socket(name='Glass Thickness', in_out='INPUT', socket_type='NodeSocketFloat').default_value = GLASS_THICKNESS
    node_group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

    nodes = node_group.nodes
    links = node_group.links

    input_node = nodes.new('NodeGroupInput')
    input_node.location = (-800, 0)

    output_node = nodes.new('NodeGroupOutput')
    output_node.location = (600, 0)

    # Créer un cube pour le verre
    cube_glass = nodes.new('GeometryNodeMeshCube')
    cube_glass.location = (-400, 0)

    # Calculer la taille du verre : (Width - 2*FrameWidth*1.6, Height - 2*FrameWidth*1.6, GlassThickness)
    frame_reduction = nodes.new('ShaderNodeMath')
    frame_reduction.location = (-600, -200)
    frame_reduction.operation = 'MULTIPLY'
    frame_reduction.inputs[1].default_value = 3.2  # 2 * 1.6
    links.new(input_node.outputs['Frame Width'], frame_reduction.inputs[0])

    glass_width = nodes.new('ShaderNodeMath')
    glass_width.location = (-600, -100)
    glass_width.operation = 'SUBTRACT'
    links.new(input_node.outputs['Width'], glass_width.inputs[0])
    links.new(frame_reduction.outputs['Value'], glass_width.inputs[1])

    glass_height = nodes.new('ShaderNodeMath')
    glass_height.location = (-600, -300)
    glass_height.operation = 'SUBTRACT'
    links.new(input_node.outputs['Height'], glass_height.inputs[0])
    links.new(frame_reduction.outputs['Value'], glass_height.inputs[1])

    combine_size = nodes.new('ShaderNodeCombineXYZ')
    combine_size.location = (-400, -200)
    links.new(glass_width.outputs['Value'], combine_size.inputs['X'])
    links.new(input_node.outputs['Glass Thickness'], combine_size.inputs['Y'])
    links.new(glass_height.outputs['Value'], combine_size.inputs['Z'])
    links.new(combine_size.outputs['Vector'], cube_glass.inputs['Size'])

    # Positionner légèrement en avant (Y=0.02)
    transform_glass = nodes.new('GeometryNodeTransform')
    transform_glass.location = (-100, 0)

    position = nodes.new('ShaderNodeCombineXYZ')
    position.location = (-300, -100)
    position.inputs['X'].default_value = 0.0
    position.inputs['Y'].default_value = 0.02
    position.inputs['Z'].default_value = 0.0

    links.new(cube_glass.outputs['Mesh'], transform_glass.inputs['Geometry'])
    links.new(position.outputs['Vector'], transform_glass.inputs['Translation'])

    # Smooth shading pour le verre
    shade_smooth = nodes.new('GeometryNodeSetShadeSmooth')
    shade_smooth.location = (200, 0)
    links.new(transform_glass.outputs['Geometry'], shade_smooth.inputs['Geometry'])

    links.new(shade_smooth.outputs['Geometry'], output_node.inputs['Geometry'])

    print(f"[GeoNodes] Node group créé: {group_name}")
    return node_group


# =================================================================
# APPLICATION DES GEOMETRY NODES
# =================================================================

def create_window_with_geonodes(window_type, width, height, location, orientation, collection):
    """Crée une fenêtre complète en utilisant geometry nodes

    Args:
        window_type: Type de fenêtre (utilisé pour le nom)
        width: Largeur
        height: Hauteur
        location: Position (Vector)
        orientation: Orientation ('front', 'back', 'left', 'right')
        collection: Collection Blender

    Returns:
        Liste des objets créés [frame_obj, glass_obj]
    """

    # Créer les node groups s'ils n'existent pas
    frame_nodegroup = create_window_frame_nodegroup()
    glass_nodegroup = create_window_glass_nodegroup()

    objects_created = []

    # === CRÉER LE CADRE ===
    # Créer un mesh vide
    frame_mesh = bpy.data.meshes.new(f"Window_Frame_{window_type}")
    frame_obj = bpy.data.objects.new(f"Window_Frame_{window_type}", frame_mesh)

    # Ajouter le modifier Geometry Nodes
    geomod_frame = frame_obj.modifiers.new(name="GeometryNodes", type='NODES')
    geomod_frame.node_group = frame_nodegroup

    # Définir les paramètres
    geomod_frame["Input_2"] = width  # Width
    geomod_frame["Input_3"] = height  # Height
    geomod_frame["Input_4"] = 0.05  # Frame Width
    geomod_frame["Input_5"] = FRAME_DEPTH  # Frame Depth

    # Positionner et orienter
    frame_obj.location = location

    # Rotation selon orientation
    if orientation == 'front':
        pass  # Pas de rotation
    elif orientation == 'back':
        frame_obj.rotation_euler[2] = 3.14159  # 180°
    elif orientation == 'left':
        frame_obj.rotation_euler[2] = 1.5708  # 90°
    elif orientation == 'right':
        frame_obj.rotation_euler[2] = -1.5708  # -90°

    collection.objects.link(frame_obj)
    frame_obj["house_part"] = "wall"
    objects_created.append(frame_obj)

    # === CRÉER LE VERRE ===
    glass_mesh = bpy.data.meshes.new(f"Window_Glass_{window_type}")
    glass_obj = bpy.data.objects.new(f"Window_Glass_{window_type}", glass_mesh)

    geomod_glass = glass_obj.modifiers.new(name="GeometryNodes", type='NODES')
    geomod_glass.node_group = glass_nodegroup

    geomod_glass["Input_2"] = width
    geomod_glass["Input_3"] = height
    geomod_glass["Input_4"] = 0.05
    geomod_glass["Input_5"] = GLASS_THICKNESS

    glass_obj.location = location
    glass_obj.rotation_euler = frame_obj.rotation_euler.copy()

    collection.objects.link(glass_obj)
    glass_obj["house_part"] = "glass"
    objects_created.append(glass_obj)

    print(f"[GeoNodes] Fenêtre créée: {window_type} à {location}")

    return objects_created


# =================================================================
# MATÉRIAUX
# =================================================================

def apply_frame_material_geonodes(obj):
    """Applique un matériau au cadre (simplifié pour geometry nodes)"""
    mat_name = "Window_Frame_Material_GeoNodes"
    mat = bpy.data.materials.get(mat_name)

    if not mat:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (0, 0)
        principled.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        principled.inputs['Roughness'].default_value = 0.3

        try:
            principled.inputs['Specular IOR Level'].default_value = 0.5
        except KeyError:
            try:
                principled.inputs['Specular'].default_value = 0.5
            except KeyError:
                pass

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def apply_glass_material_geonodes(obj):
    """Applique un matériau verre (simplifié pour geometry nodes)"""
    mat_name = "Window_Glass_Material_GeoNodes"
    mat = bpy.data.materials.get(mat_name)

    if not mat:
        mat = bpy.data.materials.new(mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (600, 0)

        glass = nodes.new('ShaderNodeBsdfGlass')
        glass.location = (0, 100)
        glass.inputs['IOR'].default_value = 1.52
        glass.inputs['Color'].default_value = (0.85, 0.92, 0.95, 1.0)

        glossy = nodes.new('ShaderNodeBsdfGlossy')
        glossy.location = (0, -100)
        glossy.inputs['Roughness'].default_value = 0.05

        fresnel = nodes.new('ShaderNodeFresnel')
        fresnel.location = (-200, 0)
        fresnel.inputs['IOR'].default_value = 1.52

        mix = nodes.new('ShaderNodeMixShader')
        mix.location = (300, 0)

        links.new(fresnel.outputs['Fac'], mix.inputs['Fac'])
        links.new(glass.outputs['BSDF'], mix.inputs[1])
        links.new(glossy.outputs['BSDF'], mix.inputs[2])
        links.new(mix.outputs['Shader'], output.inputs['Surface'])

        mat.blend_method = 'HASHED'
        mat.shadow_method = 'HASHED'
        mat.use_screen_refraction = True
        mat.refraction_depth = 0.1

    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)


def register():
    """Enregistrement du module"""
    print("[House] Module Window Geometry Nodes chargé")


def unregister():
    """Désenregistrement du module"""
    print("[House] Module Window Geometry Nodes déchargé")
