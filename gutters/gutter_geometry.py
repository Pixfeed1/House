# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Gutter Geometry Module
#  Copyright (C) 2025 mvaertan
#
#  Système de génération de gouttières (rain gutters) pour maisons
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from mathutils import Vector
import math


# ============================================================
# CONSTANTES GOUTTIÈRES
# ============================================================

# Dimensions standards des gouttières (en mètres)
GUTTER_WIDTH = 0.15  # 15cm de largeur
GUTTER_DEPTH = 0.12  # 12cm de profondeur
GUTTER_THICKNESS = 0.003  # 3mm d'épaisseur de matériau
GUTTER_OVERHANG = 0.02  # 2cm de débord par rapport au bord du toit

# Dimensions tuyaux de descente (downspouts)
DOWNSPOUT_WIDTH = 0.08  # 8cm
DOWNSPOUT_DEPTH = 0.08  # 8cm
DOWNSPOUT_THICKNESS = 0.002  # 2mm


# ============================================================
# GÉNÉRATION GÉOMÉTRIE GOUTTIÈRE (SECTION PROFILE)
# ============================================================

def create_gutter_profile(style='HALF_ROUND'):
    """Crée le profil 2D d'une gouttière

    Args:
        style: Type de profil ('HALF_ROUND', 'K_STYLE', 'BOX', 'EUROPEAN')

    Returns:
        list: Liste de points 2D [(x, y), ...] formant le profil
    """

    if style == 'HALF_ROUND':
        # Gouttière demi-ronde (classique européen)
        points = []
        num_segments = 16
        for i in range(num_segments + 1):
            angle = math.pi * i / num_segments  # De 0 à π
            x = GUTTER_WIDTH / 2 * math.cos(angle)
            y = GUTTER_DEPTH * (1 - math.sin(angle) / 2)  # Ajusté pour la profondeur
            points.append((x, y))
        return points

    elif style == 'K_STYLE':
        # Gouttière en K (style américain moderne)
        w = GUTTER_WIDTH / 2
        d = GUTTER_DEPTH
        points = [
            (-w, d),  # Coin supérieur gauche
            (-w * 0.7, d * 0.7),  # Courbe
            (-w * 0.5, d * 0.3),
            (0, 0),  # Fond
            (w * 0.5, d * 0.3),
            (w * 0.7, d * 0.7),  # Courbe
            (w, d),  # Coin supérieur droit
        ]
        return points

    elif style == 'BOX':
        # Gouttière rectangulaire (moderne/commercial)
        w = GUTTER_WIDTH / 2
        d = GUTTER_DEPTH
        points = [
            (-w, d),  # Coin supérieur gauche
            (-w, 0),  # Coin inférieur gauche
            (w, 0),  # Coin inférieur droit
            (w, d),  # Coin supérieur droit
        ]
        return points

    elif style == 'EUROPEAN':
        # Gouttière européenne trapézoïdale
        w = GUTTER_WIDTH / 2
        d = GUTTER_DEPTH
        points = [
            (-w, d),  # Coin supérieur gauche
            (-w * 0.6, d * 0.3),  # Pente gauche
            (-w * 0.4, 0),  # Fond gauche
            (w * 0.4, 0),  # Fond droit
            (w * 0.6, d * 0.3),  # Pente droite
            (w, d),  # Coin supérieur droit
        ]
        return points

    else:
        # Par défaut: half-round
        return create_gutter_profile('HALF_ROUND')


def create_gutter_mesh_section(length, style='HALF_ROUND', quality='MEDIUM'):
    """Crée une section de gouttière avec géométrie 3D

    Args:
        length: Longueur de la section en mètres
        style: Type de gouttière
        quality: Niveau de détail ('LOW', 'MEDIUM', 'HIGH')

    Returns:
        bpy.types.Object: Objet mesh de la gouttière
    """

    # Obtenir le profil 2D
    profile_points = create_gutter_profile(style)

    # Créer bmesh
    bm = bmesh.new()

    # Extruder le profil le long de la longueur
    # Créer les vertices pour le début et la fin
    start_verts = []
    end_verts = []

    for x, y in profile_points:
        # Début de la gouttière (z=0)
        v_start = bm.verts.new((x, 0, y))
        start_verts.append(v_start)

        # Fin de la gouttière (z=length)
        v_end = bm.verts.new((x, length, y))
        end_verts.append(v_end)

    bm.verts.ensure_lookup_table()

    # Créer les faces entre début et fin
    num_points = len(profile_points)
    for i in range(num_points - 1):
        v1 = start_verts[i]
        v2 = start_verts[i + 1]
        v3 = end_verts[i + 1]
        v4 = end_verts[i]

        # Créer quad face
        bm.faces.new([v1, v2, v3, v4])

    # Créer les caps (début et fin) si style box
    if style == 'BOX':
        bm.faces.new(start_verts)
        bm.faces.new(reversed(end_verts))

    # Convertir en mesh
    mesh = bpy.data.meshes.new("Gutter_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    # Créer objet
    obj = bpy.data.objects.new("Gutter", mesh)

    # Calculer normales
    mesh.calc_normals()

    return obj


# ============================================================
# TUYAUX DE DESCENTE (DOWNSPOUTS)
# ============================================================

def create_downspout_mesh(height, style='ROUND', quality='MEDIUM'):
    """Crée un tuyau de descente (downspout)

    Args:
        height: Hauteur du tuyau (du toit au sol)
        style: Type ('ROUND', 'SQUARE', 'RECTANGULAR')
        quality: Niveau de détail

    Returns:
        bpy.types.Object: Objet mesh du tuyau
    """

    bm = bmesh.new()

    if style == 'ROUND':
        # Tuyau rond
        segments = 16 if quality == 'HIGH' else 8
        radius = DOWNSPOUT_WIDTH / 2

        # Créer cercle bas
        bottom_verts = []
        top_verts = []

        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)

            v_bottom = bm.verts.new((x, 0, z))
            bottom_verts.append(v_bottom)

            v_top = bm.verts.new((x, -height, z))
            top_verts.append(v_top)

        bm.verts.ensure_lookup_table()

        # Créer faces latérales
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = bottom_verts[i]
            v2 = bottom_verts[next_i]
            v3 = top_verts[next_i]
            v4 = top_verts[i]
            bm.faces.new([v1, v2, v3, v4])

    elif style == 'SQUARE' or style == 'RECTANGULAR':
        # Tuyau carré/rectangulaire
        w = DOWNSPOUT_WIDTH / 2
        d = DOWNSPOUT_DEPTH / 2 if style == 'RECTANGULAR' else w

        # 8 vertices (4 en bas, 4 en haut)
        bottom_verts = [
            bm.verts.new((-w, 0, -d)),
            bm.verts.new((w, 0, -d)),
            bm.verts.new((w, 0, d)),
            bm.verts.new((-w, 0, d)),
        ]

        top_verts = [
            bm.verts.new((-w, -height, -d)),
            bm.verts.new((w, -height, -d)),
            bm.verts.new((w, -height, d)),
            bm.verts.new((-w, -height, d)),
        ]

        bm.verts.ensure_lookup_table()

        # Créer 4 faces latérales
        for i in range(4):
            next_i = (i + 1) % 4
            v1 = bottom_verts[i]
            v2 = bottom_verts[next_i]
            v3 = top_verts[next_i]
            v4 = top_verts[i]
            bm.faces.new([v1, v2, v3, v4])

    # Convertir en mesh
    mesh = bpy.data.meshes.new("Downspout_Mesh")
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new("Downspout", mesh)
    mesh.calc_normals()

    return obj


# ============================================================
# GÉNÉRATION COMPLÈTE SYSTÈME GOUTTIÈRES
# ============================================================

def generate_gutters_for_house(
    house_width,
    house_length,
    roof_height,
    roof_type='GABLE',
    roof_overhang=0.5,
    gutter_style='HALF_ROUND',
    downspout_style='ROUND',
    quality='MEDIUM',
    collection=None
):
    """Génère le système complet de gouttières pour une maison

    Args:
        house_width: Largeur de la maison
        house_length: Longueur de la maison
        roof_height: Hauteur du toit
        roof_type: Type de toit ('GABLE', 'HIP', 'FLAT')
        roof_overhang: Débord du toit
        gutter_style: Style de gouttière
        downspout_style: Style de tuyaux de descente
        quality: Niveau de détail
        collection: Collection où ajouter les objets

    Returns:
        list: Liste des objets créés
    """

    objects = []

    # Déterminer les positions des gouttières selon le type de toit
    if roof_type == 'GABLE':
        # Toit à pignon: gouttières sur les 2 côtés longs (front et back)

        # Gouttière avant
        gutter_front = create_gutter_mesh_section(
            house_width + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_front.name = "Gutter_Front"
        gutter_front.location = (
            -roof_overhang,
            -roof_overhang,
            roof_height
        )
        gutter_front.rotation_euler = (0, 0, 0)
        objects.append(gutter_front)

        # Gouttière arrière
        gutter_back = create_gutter_mesh_section(
            house_width + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_back.name = "Gutter_Back"
        gutter_back.location = (
            -roof_overhang,
            house_length + roof_overhang,
            roof_height
        )
        gutter_back.rotation_euler = (0, 0, 0)
        objects.append(gutter_back)

        # Tuyaux de descente (4 coins)
        downspout_positions = [
            (-roof_overhang, -roof_overhang, roof_height),  # Coin avant-gauche
            (house_width + roof_overhang, -roof_overhang, roof_height),  # Coin avant-droit
            (-roof_overhang, house_length + roof_overhang, roof_height),  # Coin arrière-gauche
            (house_width + roof_overhang, house_length + roof_overhang, roof_height),  # Coin arrière-droit
        ]

        for idx, (x, y, z) in enumerate(downspout_positions):
            downspout = create_downspout_mesh(
                height=roof_height,
                style=downspout_style,
                quality=quality
            )
            downspout.name = f"Downspout_{idx+1}"
            downspout.location = (x, y, z)
            objects.append(downspout)

    elif roof_type == 'HIP':
        # Toit à 4 pentes: gouttières sur les 4 côtés

        # Gouttière avant
        gutter_front = create_gutter_mesh_section(
            house_width + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_front.name = "Gutter_Front"
        gutter_front.location = (-roof_overhang, -roof_overhang, roof_height)
        objects.append(gutter_front)

        # Gouttière arrière
        gutter_back = create_gutter_mesh_section(
            house_width + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_back.name = "Gutter_Back"
        gutter_back.location = (-roof_overhang, house_length + roof_overhang, roof_height)
        objects.append(gutter_back)

        # Gouttière gauche (rotation 90°)
        gutter_left = create_gutter_mesh_section(
            house_length + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_left.name = "Gutter_Left"
        gutter_left.location = (-roof_overhang, -roof_overhang, roof_height)
        gutter_left.rotation_euler = (0, 0, math.radians(90))
        objects.append(gutter_left)

        # Gouttière droite (rotation 90°)
        gutter_right = create_gutter_mesh_section(
            house_length + roof_overhang * 2,
            style=gutter_style,
            quality=quality
        )
        gutter_right.name = "Gutter_Right"
        gutter_right.location = (house_width + roof_overhang, -roof_overhang, roof_height)
        gutter_right.rotation_euler = (0, 0, math.radians(90))
        objects.append(gutter_right)

        # 4 downspouts aux coins
        downspout_positions = [
            (-roof_overhang, -roof_overhang, roof_height),
            (house_width + roof_overhang, -roof_overhang, roof_height),
            (-roof_overhang, house_length + roof_overhang, roof_height),
            (house_width + roof_overhang, house_length + roof_overhang, roof_height),
        ]

        for idx, (x, y, z) in enumerate(downspout_positions):
            downspout = create_downspout_mesh(roof_height, downspout_style, quality)
            downspout.name = f"Downspout_{idx+1}"
            downspout.location = (x, y, z)
            objects.append(downspout)

    elif roof_type == 'FLAT':
        # Toit plat: gouttières sur les 4 côtés
        # (similaire à HIP mais sans pente)

        # Code similaire à HIP
        # (implémentation simplifiée pour l'exemple)
        pass

    # Ajouter les objets à la collection
    if collection:
        for obj in objects:
            if obj not in collection.objects:
                collection.objects.link(obj)
    else:
        # Ajouter à la scène
        for obj in objects:
            bpy.context.collection.objects.link(obj)

    return objects


# ============================================================
# FONCTIONS UTILITAIRES
# ============================================================

def get_gutter_style_from_architectural_style(arch_style):
    """Détermine le style de gouttière selon le style architectural

    Args:
        arch_style: Style architectural ('MODERN', 'TRADITIONAL', etc.)

    Returns:
        tuple: (gutter_style, downspout_style)
    """

    style_mapping = {
        'MODERN': ('BOX', 'SQUARE'),
        'CONTEMPORARY': ('BOX', 'SQUARE'),
        'TRADITIONAL': ('HALF_ROUND', 'ROUND'),
        'MEDITERRANEAN': ('EUROPEAN', 'ROUND'),
        'ASIAN': ('BOX', 'SQUARE'),
    }

    return style_mapping.get(arch_style, ('HALF_ROUND', 'ROUND'))
