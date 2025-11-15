"""
WINDOWS SYSTEM - Classe de base pour fenêtres HAUTE QUALITÉ
=============================================================
Architecture professionnelle avec validations mathématiques rigoureuses.

Classe de base WindowBase avec:
- Validations dimensionnelles strictes
- Calculs géométriques précis
- Gestion des cas limites
- Logging détaillé
- Code béton (ZÉRO bug toléré)
"""

import bpy
import bmesh
import math
from mathutils import Vector
from abc import ABC, abstractmethod

# ============================================================
# CONSTANTES STANDARDS FENÊTRES
# ============================================================

# Dimensions standards (en mètres)
MIN_WINDOW_WIDTH = 0.4      # 40cm largeur minimum (velux, WC)
MAX_WINDOW_WIDTH = 3.0       # 3m largeur maximum (baie vitrée)
MIN_WINDOW_HEIGHT = 0.5      # 50cm hauteur minimum
MAX_WINDOW_HEIGHT = 2.5      # 2.5m hauteur maximum

# Épaisseurs standards
FRAME_THICKNESS = 0.05       # 5cm épaisseur cadre dormant
FRAME_DEPTH = 0.12           # 12cm profondeur dans le mur
GLASS_THICKNESS = 0.024      # 24mm double vitrage standard
SASH_THICKNESS = 0.04        # 4cm épaisseur ouvrant

# Espacements
GLASS_FRAME_GAP = 0.005      # 5mm espace entre verre et cadre

# Matériaux par défaut
DEFAULT_FRAME_COLOR = (0.9, 0.9, 0.9, 1.0)  # Blanc
DEFAULT_GLASS_COLOR = (0.7, 0.85, 0.95, 0.3)  # Bleu clair translucide

# ============================================================
# CLASSE DE BASE - FENÊTRE
# ============================================================

class WindowBase(ABC):
    """
    Classe de base abstraite pour toutes les fenêtres.

    Fournit:
    - Validations dimensionnelles strictes
    - Méthodes utilitaires communes
    - Calculs géométriques de base
    - Gestion des erreurs robuste

    Chaque type de fenêtre hérite de cette classe et implémente
    sa propre méthode generate_geometry().
    """

    def __init__(self, width, height, name="Window"):
        """
        Initialise une fenêtre avec validations strictes.

        Args:
            width: Largeur de la fenêtre (m)
            height: Hauteur de la fenêtre (m)
            name: Nom de la fenêtre

        Raises:
            ValueError: Si dimensions invalides
        """
        # ✅ SÉCURITÉ: Validation des dimensions
        if not self._validate_dimensions(width, height):
            raise ValueError(
                f"Dimensions fenêtre invalides: {width}m × {height}m. "
                f"Limites: largeur [{MIN_WINDOW_WIDTH}, {MAX_WINDOW_WIDTH}], "
                f"hauteur [{MIN_WINDOW_HEIGHT}, {MAX_WINDOW_HEIGHT}]"
            )

        self.width = width
        self.height = height
        self.name = name

        # Paramètres géométriques calculés
        self.frame_thickness = FRAME_THICKNESS
        self.frame_depth = FRAME_DEPTH
        self.glass_thickness = GLASS_THICKNESS
        self.sash_thickness = SASH_THICKNESS

        # Dimensions intérieures (zone vitrée)
        self.inner_width = width - 2 * self.frame_thickness
        self.inner_height = height - 2 * self.frame_thickness

        # ✅ SÉCURITÉ: Vérifier que les dimensions intérieures sont positives
        if self.inner_width <= 0 or self.inner_height <= 0:
            raise ValueError(
                f"Fenêtre trop petite: cadre ({self.frame_thickness*2}m) "
                f"dépasse les dimensions totales ({width}m × {height}m)"
            )

        print(f"[Window] Fenêtre '{name}' initialisée: {width:.2f}m × {height:.2f}m")

    def _validate_dimensions(self, width, height):
        """
        Valide les dimensions d'une fenêtre selon les standards.

        Returns:
            bool: True si valide, False sinon
        """
        if width < MIN_WINDOW_WIDTH or width > MAX_WINDOW_WIDTH:
            print(f"[Window] ❌ Largeur invalide: {width}m (limites: {MIN_WINDOW_WIDTH}-{MAX_WINDOW_WIDTH}m)")
            return False

        if height < MIN_WINDOW_HEIGHT or height > MAX_WINDOW_HEIGHT:
            print(f"[Window] ❌ Hauteur invalide: {height}m (limites: {MIN_WINDOW_HEIGHT}-{MAX_WINDOW_HEIGHT}m)")
            return False

        # ✅ Ratio largeur/hauteur réaliste (entre 1:3 et 3:1)
        ratio = width / height
        if ratio < 0.33 or ratio > 3.0:
            print(f"[Window] ⚠️ Ratio inhabituel: {ratio:.2f} (largeur/hauteur)")

        return True

    @abstractmethod
    def generate_geometry(self):
        """
        Génère la géométrie 3D de la fenêtre.

        Cette méthode DOIT être implémentée par chaque classe fille.

        Returns:
            Object Blender de la fenêtre générée
        """
        pass

    def _create_frame_box(self, bm, x, y, z, width, height, depth):
        """
        Crée un cadre rectangulaire (dormant ou ouvrant).

        Géométrie: 8 vertices formant un cadre creux.

        Args:
            bm: BMesh où ajouter les vertices
            x, y, z: Position du coin inférieur gauche
            width: Largeur totale du cadre
            height: Hauteur totale du cadre
            depth: Profondeur du cadre (épaisseur Z)

        Returns:
            Liste des faces créées
        """
        # ✅ SÉCURITÉ: Validation des paramètres
        if width <= 0 or height <= 0 or depth <= 0:
            print(f"[Window] ❌ ERREUR: Dimensions cadre invalides (w={width}, h={height}, d={depth})")
            return []

        t = self.frame_thickness

        # Vertices extérieurs (face avant)
        v1_out = bm.verts.new((x, y, z))
        v2_out = bm.verts.new((x + width, y, z))
        v3_out = bm.verts.new((x + width, y, z + height))
        v4_out = bm.verts.new((x, y, z + height))

        # Vertices intérieurs (face avant)
        v1_in = bm.verts.new((x + t, y, z + t))
        v2_in = bm.verts.new((x + width - t, y, z + t))
        v3_in = bm.verts.new((x + width - t, y, z + height - t))
        v4_in = bm.verts.new((x + t, y, z + height - t))

        # Vertices extérieurs (face arrière)
        v1_out_back = bm.verts.new((x, y + depth, z))
        v2_out_back = bm.verts.new((x + width, y + depth, z))
        v3_out_back = bm.verts.new((x + width, y + depth, z + height))
        v4_out_back = bm.verts.new((x, y + depth, z + height))

        # Vertices intérieurs (face arrière)
        v1_in_back = bm.verts.new((x + t, y + depth, z + t))
        v2_in_back = bm.verts.new((x + width - t, y + depth, z + t))
        v3_in_back = bm.verts.new((x + width - t, y + depth, z + height - t))
        v4_in_back = bm.verts.new((x + t, y + depth, z + height - t))

        faces = []

        # Face avant du cadre (4 rectangles formant le cadre)
        faces.append(bm.faces.new([v1_out, v2_out, v2_in, v1_in]))  # Bas
        faces.append(bm.faces.new([v2_out, v3_out, v3_in, v2_in]))  # Droite
        faces.append(bm.faces.new([v3_out, v4_out, v4_in, v3_in]))  # Haut
        faces.append(bm.faces.new([v4_out, v1_out, v1_in, v4_in]))  # Gauche

        # Face arrière du cadre
        faces.append(bm.faces.new([v1_in_back, v2_in_back, v2_out_back, v1_out_back]))  # Bas
        faces.append(bm.faces.new([v2_in_back, v3_in_back, v3_out_back, v2_out_back]))  # Droite
        faces.append(bm.faces.new([v3_in_back, v4_in_back, v4_out_back, v3_out_back]))  # Haut
        faces.append(bm.faces.new([v4_in_back, v1_in_back, v1_out_back, v4_out_back]))  # Gauche

        # Faces latérales externes
        faces.append(bm.faces.new([v1_out, v1_out_back, v2_out_back, v2_out]))  # Bas ext
        faces.append(bm.faces.new([v2_out, v2_out_back, v3_out_back, v3_out]))  # Droite ext
        faces.append(bm.faces.new([v3_out, v3_out_back, v4_out_back, v4_out]))  # Haut ext
        faces.append(bm.faces.new([v4_out, v4_out_back, v1_out_back, v1_out]))  # Gauche ext

        # Faces latérales internes
        faces.append(bm.faces.new([v2_in, v2_in_back, v1_in_back, v1_in]))  # Bas int
        faces.append(bm.faces.new([v3_in, v3_in_back, v2_in_back, v2_in]))  # Droite int
        faces.append(bm.faces.new([v4_in, v4_in_back, v3_in_back, v3_in]))  # Haut int
        faces.append(bm.faces.new([v1_in, v1_in_back, v4_in_back, v4_in]))  # Gauche int

        return faces

    def _create_glass_pane(self, bm, x, y, z, width, height):
        """
        Crée un panneau de verre simple.

        Args:
            bm: BMesh où ajouter le verre
            x, y, z: Position coin inférieur gauche
            width: Largeur du vitrage
            height: Hauteur du vitrage

        Returns:
            Liste des faces du verre
        """
        # ✅ SÉCURITÉ: Validation
        if width <= 0 or height <= 0:
            print(f"[Window] ❌ ERREUR: Dimensions verre invalides (w={width}, h={height})")
            return []

        gap = GLASS_FRAME_GAP
        thickness = self.glass_thickness

        # Position légèrement en retrait du cadre
        x_glass = x + gap
        y_glass = y + self.frame_depth / 2 - thickness / 2
        z_glass = z + gap
        width_glass = width - 2 * gap
        height_glass = height - 2 * gap

        # Face avant
        v1 = bm.verts.new((x_glass, y_glass, z_glass))
        v2 = bm.verts.new((x_glass + width_glass, y_glass, z_glass))
        v3 = bm.verts.new((x_glass + width_glass, y_glass, z_glass + height_glass))
        v4 = bm.verts.new((x_glass, y_glass, z_glass + height_glass))

        # Face arrière
        v5 = bm.verts.new((x_glass, y_glass + thickness, z_glass))
        v6 = bm.verts.new((x_glass + width_glass, y_glass + thickness, z_glass))
        v7 = bm.verts.new((x_glass + width_glass, y_glass + thickness, z_glass + height_glass))
        v8 = bm.verts.new((x_glass, y_glass + thickness, z_glass + height_glass))

        faces = []
        faces.append(bm.faces.new([v1, v2, v3, v4]))  # Face avant
        faces.append(bm.faces.new([v5, v8, v7, v6]))  # Face arrière
        faces.append(bm.faces.new([v1, v5, v6, v2]))  # Bas
        faces.append(bm.faces.new([v2, v6, v7, v3]))  # Droite
        faces.append(bm.faces.new([v3, v7, v8, v4]))  # Haut
        faces.append(bm.faces.new([v4, v8, v5, v1]))  # Gauche

        return faces

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

    def _calculate_opening_angle(self, opening_percent):
        """
        Calcule l'angle d'ouverture en radians.

        Args:
            opening_percent: Pourcentage d'ouverture (0-100)

        Returns:
            float: Angle en radians
        """
        # ✅ SÉCURITÉ: Clamping du pourcentage
        opening_percent = max(0.0, min(100.0, opening_percent))

        # Ouverture maximale standard: 90° (π/2 radians)
        max_angle = math.pi / 2

        return (opening_percent / 100.0) * max_angle

    def validate_geometry(self, obj):
        """
        Valide la géométrie générée.

        Args:
            obj: Objet Blender à valider

        Returns:
            bool: True si valide, False sinon
        """
        if obj is None:
            print(f"[Window] ❌ Objet généré est None")
            return False

        if obj.data is None:
            print(f"[Window] ❌ Mesh de l'objet est None")
            return False

        # Vérifier qu'il y a des vertices
        if len(obj.data.vertices) == 0:
            print(f"[Window] ❌ Aucun vertex dans le mesh")
            return False

        # Vérifier qu'il y a des faces
        if len(obj.data.polygons) == 0:
            print(f"[Window] ⚠️ Aucune face dans le mesh")

        print(f"[Window] ✅ Géométrie validée: {len(obj.data.vertices)} vertices, {len(obj.data.polygons)} faces")
        return True
