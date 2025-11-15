"""
FLOOR TYPES - Classe de base pour tous les types de sols
==========================================================
Architecture modulaire pour le système de sols.
Chaque type de sol hérite de FloorTypeBase.
"""

import bpy
import bmesh
from mathutils import Vector

# ============================================================
# CONSTANTES GLOBALES
# ============================================================

# Qualité des mesh (nombre de subdivisions, détails géométriques)
QUALITY_LOW = 1
QUALITY_MEDIUM = 2
QUALITY_HIGH = 3
QUALITY_ULTRA = 4

# Dimensions standards (en mètres)
DEFAULT_FLOOR_THICKNESS = 0.02  # 2cm d'épaisseur standard

# Dimensions de planches/dalles selon le type
HARDWOOD_PLANK_WIDTH = 0.15     # 15cm largeur planche parquet
HARDWOOD_PLANK_LENGTH = 1.2     # 1.2m longueur planche
CERAMIC_TILE_SIZE = 0.3         # 30cm×30cm carrelage standard
LARGE_TILE_SIZE = 0.6           # 60cm×60cm grandes dalles
MARBLE_TILE_SIZE = 0.5          # 50cm×50cm dalles marbre

# Espacements et joints
TILE_GROUT_WIDTH = 0.003        # 3mm largeur joint carrelage
PLANK_GAP_WIDTH = 0.001         # 1mm espace entre planches


# ============================================================
# CLASSE DE BASE
# ============================================================

class FloorTypeBase:
    """
    Classe de base pour tous les types de sols.

    Chaque type de sol (parquet, carrelage, marbre, etc.) hérite de cette classe
    et implémente sa propre logique de génération de mesh et de matériaux.

    Architecture:
    - Validations et sécurités robustes
    - Gestion des matériaux PBR
    - Génération de mesh optimisée
    - Code "béton" (aucun bug toléré)
    """

    # Propriétés par défaut (à surcharger dans les classes enfants)
    FLOOR_NAME = "Sol Générique"
    CATEGORY = "generic"  # warm, resistant, elegant, comfort
    THICKNESS = DEFAULT_FLOOR_THICKNESS
    PATTERN = "seamless"  # seamless, straight, grid, random

    def __init__(self, quality=QUALITY_HIGH, **kwargs):
        """
        Initialise le type de sol.

        Args:
            quality: Niveau de qualité (QUALITY_LOW à QUALITY_ULTRA)
            **kwargs: Options custom (ignorées dans la classe de base, utilisées par les classes enfants)
        """
        # ✅ SÉCURITÉ: Validation du niveau de qualité
        if quality not in [QUALITY_LOW, QUALITY_MEDIUM, QUALITY_HIGH, QUALITY_ULTRA]:
            print(f"[FloorType] ⚠️ Qualité invalide ({quality}), utilisation de QUALITY_HIGH par défaut")
            quality = QUALITY_HIGH

        self.quality = quality

        # Stocker les kwargs pour les classes enfants
        self.custom_options = kwargs

        if kwargs:
            print(f"[FloorType] {self.FLOOR_NAME} initialisé (qualité: {quality}, options: {list(kwargs.keys())})")
        else:
            print(f"[FloorType] {self.FLOOR_NAME} initialisé (qualité: {quality})")

    def generate(self, width, length, room_name="Room", height=0.0):
        """
        Génère le sol dans Blender.

        Args:
            width: Largeur de la pièce (m)
            length: Longueur de la pièce (m)
            room_name: Nom de la pièce (pour identification)
            height: Hauteur Z du sol (par défaut 0.0)

        Returns:
            Object Blender du sol généré, ou None si erreur
        """
        # ✅ SÉCURITÉ: Validation des dimensions
        if width <= 0 or length <= 0:
            print(f"[FloorType] ❌ ERREUR: Dimensions invalides ({width}m × {length}m)")
            return None

        if width > 100 or length > 100:
            print(f"[FloorType] ⚠️ WARNING: Dimensions très grandes ({width}m × {length}m)")

        print(f"[FloorType] Génération {self.FLOOR_NAME} pour '{room_name}': {width}m × {length}m")

        # Générer le mesh (méthode à implémenter dans les classes enfants)
        mesh_obj = self._generate_mesh(width, length, height)

        if mesh_obj is None:
            print(f"[FloorType] ❌ ERREUR: Échec génération mesh")
            return None

        # Nommer l'objet
        mesh_obj.name = f"Floor_{self.FLOOR_NAME.replace(' ', '_')}_{room_name}"
        mesh_obj["house_part"] = "floor"
        mesh_obj["floor_type"] = self.__class__.__name__
        mesh_obj["room_name"] = room_name

        # Appliquer le matériau
        self._apply_material(mesh_obj)

        print(f"[FloorType] ✅ {self.FLOOR_NAME} généré avec succès")
        return mesh_obj

    def _generate_mesh(self, width, length, height):
        """
        Génère le mesh du sol.

        DOIT être implémentée dans les classes enfants.

        Args:
            width: Largeur (m)
            length: Longueur (m)
            height: Hauteur Z (m)

        Returns:
            Object Blender du mesh généré
        """
        raise NotImplementedError(f"_generate_mesh() doit être implémentée dans {self.__class__.__name__}")

    def _apply_material(self, obj):
        """
        Applique le matériau PBR au sol.

        PEUT être surchargée dans les classes enfants pour des matériaux spécifiques.

        Args:
            obj: Object Blender à matérialiser
        """
        # Par défaut: matériau basique gris
        mat = bpy.data.materials.new(name=f"Material_{self.FLOOR_NAME.replace(' ', '_')}")
        mat.use_nodes = True

        # Récupérer le shader principal
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            # Couleur de base grise
            bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.5

        # Appliquer le matériau
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat

    def _create_seamless_floor(self, width, length, height):
        """
        Crée un sol seamless (dalle continue sans joints).

        Utilisé par: Béton ciré, moquette, etc.

        Args:
            width, length, height: Dimensions

        Returns:
            Object Blender
        """
        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm = bmesh.new()

        try:
            # Créer 4 vertices pour le rectangle
            v1 = bm.verts.new((0, 0, 0))
            v2 = bm.verts.new((width, 0, 0))
            v3 = bm.verts.new((width, length, 0))
            v4 = bm.verts.new((0, length, 0))

            bm.verts.ensure_lookup_table()

            # Créer la face
            face = bm.faces.new([v1, v2, v3, v4])

            # Extruder pour donner de l'épaisseur
            ret = bmesh.ops.extrude_face_region(bm, geom=[face])
            extruded_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=extruded_verts, vec=(0, 0, -self.THICKNESS))

            # Finaliser
            bm.to_mesh(mesh)
            mesh.update()

        finally:
            bm.free()

        # Créer l'objet
        obj = bpy.data.objects.new(f"{self.FLOOR_NAME}_Obj", mesh)
        obj.location.z = height

        return obj

    def _create_plank_floor(self, width, length, height, plank_width, plank_length):
        """
        Crée un sol en planches (parquet, stratifié, vinyle).

        Args:
            width, length, height: Dimensions pièce
            plank_width: Largeur d'une planche
            plank_length: Longueur d'une planche

        Returns:
            Object Blender
        """
        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm = bmesh.new()

        try:
            # Calculer le nombre de planches
            num_planks_width = int(length / plank_width) + 1
            num_planks_length = int(width / plank_length) + 1

            gap = PLANK_GAP_WIDTH

            # Générer les planches en lignes parallèles
            for row in range(num_planks_width):
                y_start = row * plank_width

                # Décalage aléatoire pour effet réaliste (brickwork pattern)
                x_offset = (row % 2) * (plank_length / 3)

                for col in range(num_planks_length + 1):
                    x_start = col * plank_length + x_offset

                    # Ne pas dépasser la largeur
                    if x_start >= width:
                        continue

                    # Ajuster la dernière planche
                    actual_length = min(plank_length - gap, width - x_start)
                    actual_width = min(plank_width - gap, length - y_start)

                    if actual_length <= 0 or actual_width <= 0:
                        continue

                    # Créer une planche
                    self._add_plank(bm, x_start, y_start, actual_length, actual_width)

            # Extruder pour donner de l'épaisseur
            all_faces = list(bm.faces)
            if all_faces:
                ret = bmesh.ops.extrude_face_region(bm, geom=all_faces)
                extruded_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=extruded_verts, vec=(0, 0, -self.THICKNESS))

            # Finaliser
            bm.to_mesh(mesh)
            mesh.update()

        finally:
            bm.free()

        obj = bpy.data.objects.new(f"{self.FLOOR_NAME}_Obj", mesh)
        obj.location.z = height

        return obj

    def _add_plank(self, bm, x, y, length, width):
        """Ajoute une planche au bmesh"""
        v1 = bm.verts.new((x, y, 0))
        v2 = bm.verts.new((x + length, y, 0))
        v3 = bm.verts.new((x + length, y + width, 0))
        v4 = bm.verts.new((x, y + width, 0))

        bm.verts.ensure_lookup_table()
        bm.faces.new([v1, v2, v3, v4])

    def _create_tile_floor(self, width, length, height, tile_size):
        """
        Crée un sol en dalles/carreaux (carrelage, marbre, liège).

        Args:
            width, length, height: Dimensions pièce
            tile_size: Taille d'une dalle (carré)

        Returns:
            Object Blender
        """
        mesh = bpy.data.meshes.new(f"{self.FLOOR_NAME}_Mesh")
        bm = bmesh.new()

        try:
            # Calculer le nombre de dalles
            num_tiles_x = int(width / tile_size) + 1
            num_tiles_y = int(length / tile_size) + 1

            gap = TILE_GROUT_WIDTH

            # Générer les dalles en grille
            for row in range(num_tiles_y):
                y_start = row * tile_size

                for col in range(num_tiles_x):
                    x_start = col * tile_size

                    # Ajuster la dernière dalle
                    actual_size_x = min(tile_size - gap, width - x_start)
                    actual_size_y = min(tile_size - gap, length - y_start)

                    if actual_size_x <= 0 or actual_size_y <= 0:
                        continue

                    # Créer une dalle
                    self._add_tile(bm, x_start, y_start, actual_size_x, actual_size_y)

            # Extruder pour donner de l'épaisseur
            all_faces = list(bm.faces)
            if all_faces:
                ret = bmesh.ops.extrude_face_region(bm, geom=all_faces)
                extruded_verts = [v for v in ret["geom"] if isinstance(v, bmesh.types.BMVert)]
                bmesh.ops.translate(bm, verts=extruded_verts, vec=(0, 0, -self.THICKNESS))

            # Finaliser
            bm.to_mesh(mesh)
            mesh.update()

        finally:
            bm.free()

        obj = bpy.data.objects.new(f"{self.FLOOR_NAME}_Obj", mesh)
        obj.location.z = height

        return obj

    def _add_tile(self, bm, x, y, size_x, size_y):
        """Ajoute une dalle au bmesh"""
        v1 = bm.verts.new((x, y, 0))
        v2 = bm.verts.new((x + size_x, y, 0))
        v3 = bm.verts.new((x + size_x, y + size_y, 0))
        v4 = bm.verts.new((x, y + size_y, 0))

        bm.verts.ensure_lookup_table()
        bm.faces.new([v1, v2, v3, v4])
