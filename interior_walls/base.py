"""
INTERIOR WALLS FINISHES - Classe de base HAUTE QUALITÉ
========================================================
Système de finitions murales intérieures professionnelles.

Classe de base WallFinishBase avec:
- Validations dimensionnelles strictes
- Calculs géométriques précis pour mesh muraux
- Gestion UV mapping (papier peint, textures)
- Support relief/matière (enduits)
- Code béton (ZÉRO bug toléré)

Types de finitions supportés:
- Peinture (mat, satinée, brillante, velours)
- Enduit décoratif (taloché, ciré, lissé)
- Papier peint (avec texture image)
- Bois (bardage, panneaux, tasseaux)
- Pierre naturelle
- Brique apparente (non finie)
"""

import bpy
import bmesh
import os
from mathutils import Vector
from abc import ABC, abstractmethod

# ============================================================
# CONSTANTES FINITIONS MURALES
# ============================================================

# Dimensions limites
MIN_WALL_WIDTH = 0.5         # 50cm largeur minimum
MAX_WALL_WIDTH = 15.0        # 15m largeur maximum
MIN_WALL_HEIGHT = 2.0        # 2m hauteur minimum
MAX_WALL_HEIGHT = 4.0        # 4m hauteur maximum

# Épaisseurs finitions (ajoutées au mur de base)
PAINT_THICKNESS = 0.0002     # 0.2mm peinture (négligeable)
PLASTER_THICKNESS = 0.003    # 3mm enduit
WALLPAPER_THICKNESS = 0.0005 # 0.5mm papier peint
WOOD_PANEL_THICKNESS = 0.015 # 15mm panneau bois
STONE_THICKNESS = 0.020      # 20mm pierre naturelle

# Papier peint - résolutions minimales (pixels)
MIN_WALLPAPER_RES_WIDTH = 1024   # 1024px largeur min
MIN_WALLPAPER_RES_HEIGHT = 1024  # 1024px hauteur min
RECOMMENDED_WALLPAPER_RES = 2048 # 2048px recommandé (qualité)

# Couleurs par défaut
DEFAULT_PAINT_COLOR = (0.95, 0.95, 0.95, 1.0)  # Blanc cassé
DEFAULT_WOOD_COLOR = (0.6, 0.4, 0.2, 1.0)       # Bois naturel
DEFAULT_STONE_COLOR = (0.7, 0.7, 0.65, 1.0)     # Pierre grise

# ============================================================
# CLASSE DE BASE - FINITION MURALE
# ============================================================

class WallFinishBase(ABC):
    """
    Classe de base abstraite pour finitions murales intérieures.

    Fournit:
    - Validations dimensionnelles strictes
    - Méthodes utilitaires communes (UV mapping, relief)
    - Calculs géométriques de base
    - Gestion des erreurs robuste

    Chaque type de finition hérite de cette classe et implémente
    sa propre méthode generate_finish().
    """

    def __init__(self, width, height, name="WallFinish"):
        """
        Initialise une finition murale avec validations strictes.

        Args:
            width: Largeur du mur (m)
            height: Hauteur du mur (m)
            name: Nom de la finition

        Raises:
            ValueError: Si dimensions invalides
        """
        # ✅ SÉCURITÉ: Validation des dimensions
        if not self._validate_dimensions(width, height):
            raise ValueError(
                f"Dimensions mur invalides: {width}m × {height}m. "
                f"Limites: largeur [{MIN_WALL_WIDTH}, {MAX_WALL_WIDTH}], "
                f"hauteur [{MIN_WALL_HEIGHT}, {MAX_WALL_HEIGHT}]"
            )

        self.width = width
        self.height = height
        self.name = name

        print(f"[WallFinish] Finition '{name}' initialisée: {width:.2f}m × {height:.2f}m")

    def _validate_dimensions(self, width, height):
        """
        Valide les dimensions d'un mur selon les standards.

        Returns:
            bool: True si valide, False sinon
        """
        if width < MIN_WALL_WIDTH or width > MAX_WALL_WIDTH:
            print(f"[WallFinish] ❌ Largeur invalide: {width}m (limites: {MIN_WALL_WIDTH}-{MAX_WALL_WIDTH}m)")
            return False

        if height < MIN_WALL_HEIGHT or height > MAX_WALL_HEIGHT:
            print(f"[WallFinish] ❌ Hauteur invalide: {height}m (limites: {MIN_WALL_HEIGHT}-{MAX_WALL_HEIGHT}m)")
            return False

        return True

    @abstractmethod
    def generate_finish(self):
        """
        Génère la géométrie 3D de la finition murale.

        Cette méthode DOIT être implémentée par chaque classe fille.

        Returns:
            Object Blender de la finition générée
        """
        pass

    def _create_flat_wall_surface(self, bm, x, y, z, width, height, thickness=0.001, subdivisions=1):
        """
        Crée une surface murale plane (base pour finitions).

        Args:
            bm: BMesh où ajouter la surface
            x, y, z: Position coin inférieur gauche
            width: Largeur du mur
            height: Hauteur du mur
            thickness: Épaisseur de la finition
            subdivisions: Nombre de subdivisions (pour UV mapping propre)

        Returns:
            Liste des faces créées
        """
        # ✅ SÉCURITÉ: Validation
        if width <= 0 or height <= 0:
            print(f"[WallFinish] ❌ ERREUR: Dimensions surface invalides (w={width}, h={height})")
            return []

        # Vertices du rectangle (face avant)
        v1 = bm.verts.new((x, y, z))
        v2 = bm.verts.new((x + width, y, z))
        v3 = bm.verts.new((x + width, y, z + height))
        v4 = bm.verts.new((x, y, z + height))

        # Face avant
        face_front = bm.faces.new([v1, v2, v3, v4])

        # Vertices face arrière (avec épaisseur)
        v5 = bm.verts.new((x, y + thickness, z))
        v6 = bm.verts.new((x + width, y + thickness, z))
        v7 = bm.verts.new((x + width, y + thickness, z + height))
        v8 = bm.verts.new((x, y + thickness, z + height))

        # Face arrière
        face_back = bm.faces.new([v5, v8, v7, v6])

        # Faces latérales
        faces = [face_front, face_back]
        faces.append(bm.faces.new([v1, v5, v6, v2]))  # Bas
        faces.append(bm.faces.new([v2, v6, v7, v3]))  # Droite
        faces.append(bm.faces.new([v3, v7, v8, v4]))  # Haut
        faces.append(bm.faces.new([v4, v8, v5, v1]))  # Gauche

        # ✅ Subdivisions pour UV mapping propre
        if subdivisions > 0:
            edges_to_subdivide = []
            for face in [face_front, face_back]:
                edges_to_subdivide.extend(face.edges)

            if edges_to_subdivide:
                bmesh.ops.subdivide_edges(bm, edges=edges_to_subdivide, cuts=subdivisions)

        return faces

    def _create_relief_surface(self, bm, x, y, z, width, height, relief_depth=0.005, pattern="random"):
        """
        Crée une surface avec relief (pour enduits décoratifs).

        Args:
            bm: BMesh
            x, y, z: Position
            width, height: Dimensions
            relief_depth: Profondeur du relief (m)
            pattern: Type de pattern ("random", "horizontal", "vertical")

        Returns:
            Liste des faces
        """
        # Créer surface de base avec subdivisions
        faces = self._create_flat_wall_surface(
            bm, x, y, z, width, height,
            thickness=relief_depth,
            subdivisions=4  # Plus de subdivisions pour relief
        )

        # TODO: Ajouter déplacement aléatoire des vertices pour relief
        # (Simplification pour l'instant: surface plane)

        return faces

    def _setup_uv_mapping(self, obj, image_path=None):
        """
        Configure l'UV mapping pour texture/papier peint.

        Args:
            obj: Objet Blender
            image_path: Chemin vers image texture (optionnel)

        Returns:
            bool: True si succès, False sinon
        """
        if obj is None or obj.data is None:
            print(f"[WallFinish] ❌ Objet invalide pour UV mapping")
            return False

        # Créer UV map si n'existe pas
        if not obj.data.uv_layers:
            obj.data.uv_layers.new(name="UVMap")
            print(f"[WallFinish] ✅ UV map créée")

        # TODO: Si image_path fourni, charger et appliquer texture
        # (Nécessite création matériau avec shader nodes)

        return True

    def _validate_image_resolution(self, image_path):
        """
        Valide la résolution d'une image de papier peint.

        Args:
            image_path: Chemin vers l'image

        Returns:
            Tuple (bool, width, height, message)
        """
        # ✅ SÉCURITÉ: Vérifier existence fichier
        if not os.path.exists(image_path):
            return (False, 0, 0, f"Fichier introuvable: {image_path}")

        # ✅ SÉCURITÉ: Vérifier extension
        valid_extensions = ['.png', '.jpg', '.jpeg', '.tga', '.bmp']
        ext = os.path.splitext(image_path)[1].lower()
        if ext not in valid_extensions:
            return (False, 0, 0, f"Format invalide: {ext}. Formats valides: {', '.join(valid_extensions)}")

        # Charger image Blender pour obtenir résolution
        try:
            img = bpy.data.images.load(image_path, check_existing=True)
            width = img.size[0]
            height = img.size[1]

            # ✅ SÉCURITÉ: Vérifier résolution minimale
            if width < MIN_WALLPAPER_RES_WIDTH or height < MIN_WALLPAPER_RES_HEIGHT:
                return (False, width, height,
                        f"Résolution trop faible: {width}×{height}px. "
                        f"Minimum: {MIN_WALLPAPER_RES_WIDTH}×{MIN_WALLPAPER_RES_HEIGHT}px")

            # ✅ Avertissement si pas résolution recommandée
            if width < RECOMMENDED_WALLPAPER_RES or height < RECOMMENDED_WALLPAPER_RES:
                print(f"[WallFinish] ⚠️ Résolution acceptable mais non optimale: {width}×{height}px")
                print(f"[WallFinish] Résolution recommandée: {RECOMMENDED_WALLPAPER_RES}×{RECOMMENDED_WALLPAPER_RES}px pour qualité optimale")

            return (True, width, height, f"Résolution OK: {width}×{height}px")

        except Exception as e:
            return (False, 0, 0, f"Erreur chargement image: {e}")

    def _create_mesh_from_bmesh(self, bmesh_data, obj_name):
        """
        Crée un objet Blender à partir d'un BMesh.

        Args:
            bmesh_data: BMesh contenant la géométrie
            obj_name: Nom de l'objet

        Returns:
            Tuple (objet, mesh)
        """
        # Recalculer normales pour éclairage correct
        bmesh.ops.recalc_face_normals(bmesh_data, faces=bmesh_data.faces)

        # Créer le mesh Blender
        mesh = bpy.data.meshes.new(obj_name)
        bmesh_data.to_mesh(mesh)

        # Créer l'objet
        obj = bpy.data.objects.new(obj_name, mesh)

        return obj, mesh

    def validate_geometry(self, obj):
        """
        Valide la géométrie générée.

        Args:
            obj: Objet Blender à valider

        Returns:
            bool: True si valide, False sinon
        """
        if obj is None:
            print(f"[WallFinish] ❌ Objet généré est None")
            return False

        if obj.data is None:
            print(f"[WallFinish] ❌ Mesh de l'objet est None")
            return False

        # Vérifier qu'il y a des vertices
        if len(obj.data.vertices) == 0:
            print(f"[WallFinish] ❌ Aucun vertex dans le mesh")
            return False

        # Vérifier qu'il y a des faces
        if len(obj.data.polygons) == 0:
            print(f"[WallFinish] ⚠️ Aucune face dans le mesh")

        print(f"[WallFinish] ✅ Géométrie validée: {len(obj.data.vertices)} vertices, {len(obj.data.polygons)} faces")
        return True

    def _create_wood_planks(self, bm, x, y, z, width, height, plank_width=0.15, orientation="vertical"):
        """
        Crée un pattern de planches de bois.

        Args:
            bm: BMesh
            x, y, z: Position
            width, height: Dimensions totales
            plank_width: Largeur d'une planche (m)
            orientation: "vertical" ou "horizontal"

        Returns:
            Liste des faces créées
        """
        # ✅ SÉCURITÉ: Validation
        if width <= 0 or height <= 0 or plank_width <= 0:
            print(f"[WallFinish] ❌ Paramètres planches invalides")
            return []

        thickness = WOOD_PANEL_THICKNESS
        gap = 0.002  # 2mm espace entre planches

        faces = []

        if orientation == "vertical":
            # Planches verticales
            num_planks = int(width / plank_width) + 1

            for i in range(num_planks):
                plank_x = x + i * plank_width
                actual_width = min(plank_width - gap, width - (i * plank_width))

                if actual_width <= 0:
                    continue

                # Vertices planche
                v1 = bm.verts.new((plank_x, y, z))
                v2 = bm.verts.new((plank_x + actual_width, y, z))
                v3 = bm.verts.new((plank_x + actual_width, y, z + height))
                v4 = bm.verts.new((plank_x, y, z + height))

                v5 = bm.verts.new((plank_x, y + thickness, z))
                v6 = bm.verts.new((plank_x + actual_width, y + thickness, z))
                v7 = bm.verts.new((plank_x + actual_width, y + thickness, z + height))
                v8 = bm.verts.new((plank_x, y + thickness, z + height))

                # Faces
                faces.append(bm.faces.new([v1, v2, v3, v4]))  # Face avant
                faces.append(bm.faces.new([v5, v8, v7, v6]))  # Face arrière
                faces.append(bm.faces.new([v1, v5, v6, v2]))  # Bas
                faces.append(bm.faces.new([v3, v7, v8, v4]))  # Haut

        else:  # horizontal
            # Planches horizontales
            num_planks = int(height / plank_width) + 1

            for i in range(num_planks):
                plank_z = z + i * plank_width
                actual_height = min(plank_width - gap, height - (i * plank_width))

                if actual_height <= 0:
                    continue

                # Vertices planche
                v1 = bm.verts.new((x, y, plank_z))
                v2 = bm.verts.new((x + width, y, plank_z))
                v3 = bm.verts.new((x + width, y, plank_z + actual_height))
                v4 = bm.verts.new((x, y, plank_z + actual_height))

                v5 = bm.verts.new((x, y + thickness, plank_z))
                v6 = bm.verts.new((x + width, y + thickness, plank_z))
                v7 = bm.verts.new((x + width, y + thickness, plank_z + actual_height))
                v8 = bm.verts.new((x, y + thickness, plank_z + actual_height))

                # Faces
                faces.append(bm.faces.new([v1, v2, v3, v4]))
                faces.append(bm.faces.new([v5, v8, v7, v6]))
                faces.append(bm.faces.new([v1, v5, v6, v2]))
                faces.append(bm.faces.new([v2, v6, v7, v3]))

        return faces
