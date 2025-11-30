# =============================================================================
# GÉNÉRATEUR DE PORTES - 4 Styles avec Matériaux Intégrés
# Pour Blender 4.2+ - Intégré au système House
# =============================================================================
#
# 4 STYLES DE PORTES :
# 1. PORTE PLEINE BOIS (SOLID_WOOD) - Bois foncé traditionnel
# 2. PORTE PVC BLANC (PVC_WHITE) - Moderne, économique
# 3. PORTE BOIS VITRAGE CENTRAL (WOOD_CENTER_GLASS) - Classique/familial
# 4. PORTE ALU GRAND VITRAGE (ALU_LARGE_GLASS) - Aluminium moderne
#
# =============================================================================

import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix


class DoorGenerator:
    """Générateur de portes avec 4 styles et matériaux intégrés"""

    def __init__(self,
                 door_style='SOLID_WOOD',
                 door_width=0.90,
                 door_height=2.15,
                 door_thickness=0.04,
                 add_frame=True,
                 frame_width=0.07,
                 frame_depth=0.08,
                 add_handle=True,
                 handle_height=1.05,
                 wood_color='DARK_OAK',
                 alu_color='GRIS_ANTHRACITE',
                 alu_finish='SATINE',
                 glass_type='CLEAR',
                 hinge_side='LEFT',
                 add_hinges=True,
                 hinge_count=3,
                 opening_angle=0.0,
                 random_seed=42):
        """
        Initialise le générateur de porte.

        Args:
            door_style: Style de porte (SOLID_WOOD, PVC_WHITE, WOOD_CENTER_GLASS, ALU_LARGE_GLASS)
            door_width: Largeur de la porte
            door_height: Hauteur de la porte
            door_thickness: Épaisseur de la porte
            add_frame: Ajouter un cadre/dormant
            frame_width: Largeur du cadre
            frame_depth: Profondeur du cadre
            add_handle: Ajouter une poignée
            handle_height: Hauteur de la poignée
            wood_color: Teinte du bois
            alu_color: Couleur de l'aluminium
            alu_finish: Finition de l'aluminium
            glass_type: Type de vitrage
            hinge_side: Côté des charnières (LEFT, RIGHT)
            add_hinges: Ajouter des charnières
            hinge_count: Nombre de charnières
            opening_angle: Angle d'ouverture en degrés (0=fermée, 90=ouverte)
            random_seed: Seed aléatoire
        """
        self.door_style = door_style
        self.door_width = door_width
        self.door_height = door_height
        self.door_thickness = door_thickness
        self.add_frame = add_frame
        self.frame_width = frame_width
        self.frame_depth = frame_depth
        self.add_handle = add_handle
        self.handle_height = handle_height
        self.wood_color = wood_color
        self.alu_color = alu_color
        self.alu_finish = alu_finish
        self.glass_type = glass_type
        self.hinge_side = hinge_side
        self.add_hinges = add_hinges
        self.hinge_count = hinge_count
        self.opening_angle = max(0.0, min(90.0, opening_angle))
        self.random_seed = random_seed

        random.seed(random_seed)

    def generate(self, collection, location=(0, 0, 0), rotation=0):
        """
        Génère la porte complète avec animation d'ouverture.

        Args:
            collection: Collection Blender où créer les objets
            location: Position (x, y, z)
            rotation: Rotation en radians autour de Z

        Returns:
            Liste des objets créés
        """
        objects = []
        moving_parts = []  # Parties qui bougent avec la porte

        # Créer la porte selon le style
        if self.door_style == 'SOLID_WOOD':
            door_obj = self.create_solid_wood_door(collection)
        elif self.door_style == 'PVC_WHITE':
            door_obj = self.create_pvc_door(collection)
        elif self.door_style == 'WOOD_CENTER_GLASS':
            door_obj = self.create_wood_center_glass_door(collection)
        elif self.door_style == 'ALU_LARGE_GLASS':
            door_obj = self.create_alu_large_glass_door(collection)
        else:
            door_obj = self.create_solid_wood_door(collection)

        if door_obj:
            objects.append(door_obj)
            moving_parts.append(door_obj)

        # Ajouter le cadre (partie FIXE - ne bouge pas)
        if self.add_frame:
            frame_parts = self.create_frame(collection)
            objects.extend(frame_parts)

        # Ajouter les charnières
        if self.add_hinges:
            hinge_parts = self.create_hinges(collection)
            objects.extend(hinge_parts)
            # Les parties mobiles des charnières bougent avec la porte
            for hp in hinge_parts:
                if hp and 'Mobile' in hp.name:
                    moving_parts.append(hp)

        # Ajouter la poignée (bouge avec la porte)
        if self.add_handle:
            handle_parts = self.create_handle(collection)
            objects.extend(handle_parts)
            moving_parts.extend(handle_parts)

        # Ajouter les panneaux décoratifs (bougent avec la porte)
        for obj in collection.objects:
            if obj and 'Panel' in obj.name and obj not in moving_parts:
                moving_parts.append(obj)

        # ============================================================
        # ANIMATION : Rotation autour du pivot (charnières)
        # ============================================================
        if self.opening_angle > 0:
            # Déterminer le point pivot (côté charnières)
            if self.hinge_side == 'LEFT':
                pivot_x = 0.0
                angle_sign = 1  # Ouvre vers l'intérieur (sens anti-horaire vu de dessus)
            else:
                pivot_x = self.door_width
                angle_sign = -1  # Ouvre vers l'intérieur (sens horaire vu de dessus)

            pivot_y = 0.0
            angle_rad = math.radians(self.opening_angle) * angle_sign

            # Créer un Empty comme pivot
            pivot_empty = bpy.data.objects.new("Door_Pivot", None)
            pivot_empty.empty_display_type = 'ARROWS'
            pivot_empty.empty_display_size = 0.1
            pivot_empty.location = (pivot_x, pivot_y, 0)
            collection.objects.link(pivot_empty)
            pivot_empty["house_part"] = "door_pivot"
            objects.append(pivot_empty)

            # Parenter les parties mobiles au pivot
            for part in moving_parts:
                if part and part.type == 'MESH':
                    # Décaler la position relative au pivot
                    part.location.x -= pivot_x
                    part.location.y -= pivot_y
                    part.parent = pivot_empty
                    part.matrix_parent_inverse = pivot_empty.matrix_world.inverted()

            # Appliquer la rotation au pivot
            pivot_empty.rotation_euler.z = angle_rad

            # Appliquer position et rotation globale au pivot
            pivot_empty.location.x += location[0] + pivot_x
            pivot_empty.location.y += location[1]
            pivot_empty.location.z += location[2]
            if rotation != 0:
                pivot_empty.rotation_euler.z += rotation

            # Appliquer position et rotation aux parties fixes (cadre, charnières fixes)
            for obj in objects:
                if obj and obj.type == 'MESH' and obj not in moving_parts:
                    obj.location.x += location[0]
                    obj.location.y += location[1]
                    obj.location.z += location[2]
                    if rotation != 0:
                        obj.rotation_euler.z += rotation

        else:
            # Pas d'ouverture - appliquer position et rotation normalement
            for obj in objects:
                if obj and obj.type == 'MESH':
                    obj.location.x += location[0]
                    obj.location.y += location[1]
                    obj.location.z += location[2]
                    if rotation != 0:
                        obj.rotation_euler.z += rotation

        return objects

    # =================================================================
    # 1. PORTE PLEINE BOIS
    # =================================================================

    def create_solid_wood_door(self, collection):
        """Crée une porte pleine en bois traditionnel"""

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.door_width, self.door_thickness, self.door_height), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(self.door_width/2, 0, self.door_height/2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Door_Solid_Wood")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Door_Solid_Wood", mesh)
        collection.objects.link(obj)

        # Ajouter panneaux décoratifs
        self._add_wood_panels(collection, obj)

        # Matériau bois
        mat = self._create_wood_material("Bois_Porte_Pleine")
        obj.data.materials.append(mat)

        for poly in mesh.polygons:
            poly.use_smooth = True

        obj["house_part"] = "door"
        return obj

    def _add_wood_panels(self, collection, door_obj):
        """Ajoute des panneaux moulurés à la porte bois"""

        panel_margin_x = 0.08
        panel_margin_z = 0.10
        panel_width = self.door_width - 2 * panel_margin_x
        panel_height = (self.door_height - 3 * panel_margin_z) / 2
        panel_depth = 0.012

        door_front = self.door_thickness / 2
        mat = door_obj.data.materials[0] if door_obj.data.materials else self._create_wood_material("Bois_Panel")

        # Panneau bas
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(panel_width, panel_depth, panel_height), verts=bm.verts)
        bmesh.ops.translate(
            bm,
            vec=(self.door_width / 2, door_front + panel_depth / 2, panel_margin_z + panel_height / 2),
            verts=bm.verts
        )

        mesh = bpy.data.meshes.new("Panel_Bottom")
        bm.to_mesh(mesh)
        bm.free()

        panel_bottom = bpy.data.objects.new("Door_Panel_Bottom", mesh)
        collection.objects.link(panel_bottom)
        panel_bottom.data.materials.append(mat)
        panel_bottom["house_part"] = "door"

        bevel = panel_bottom.modifiers.new("Bevel", 'BEVEL')
        bevel.width = 0.004
        bevel.segments = 2

        for poly in mesh.polygons:
            poly.use_smooth = True

        # Panneau haut
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(panel_width, panel_depth, panel_height), verts=bm.verts)
        bmesh.ops.translate(
            bm,
            vec=(self.door_width / 2, door_front + panel_depth / 2, panel_margin_z * 2 + panel_height * 1.5),
            verts=bm.verts
        )

        mesh = bpy.data.meshes.new("Panel_Top")
        bm.to_mesh(mesh)
        bm.free()

        panel_top = bpy.data.objects.new("Door_Panel_Top", mesh)
        collection.objects.link(panel_top)
        panel_top.data.materials.append(mat)
        panel_top["house_part"] = "door"

        bevel = panel_top.modifiers.new("Bevel", 'BEVEL')
        bevel.width = 0.004
        bevel.segments = 2

        for poly in mesh.polygons:
            poly.use_smooth = True

    # =================================================================
    # 2. PORTE PVC BLANC
    # =================================================================

    def create_pvc_door(self, collection):
        """Crée une porte PVC blanche moderne"""

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.door_width, self.door_thickness, self.door_height), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(self.door_width/2, 0, self.door_height/2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Door_PVC_White")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Door_PVC_White", mesh)
        collection.objects.link(obj)

        bevel = obj.modifiers.new("Bevel", 'BEVEL')
        bevel.width = 0.002
        bevel.segments = 2

        mat = self._create_pvc_material()
        obj.data.materials.append(mat)

        for poly in mesh.polygons:
            poly.use_smooth = True

        obj["house_part"] = "door"
        return obj

    # =================================================================
    # 3. PORTE BOIS VITRAGE CENTRAL
    # =================================================================

    def create_wood_center_glass_door(self, collection):
        """Crée une porte bois avec vitrage central"""

        glass_width = 0.28
        glass_height = 0.40
        glass_center_z = 1.40

        # Panneau principal
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.door_width, self.door_thickness, self.door_height), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(self.door_width / 2, 0, self.door_height / 2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Door_Wood_CenterGlass")
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new("Door_Wood_CenterGlass", mesh)
        collection.objects.link(obj)

        # Boolean pour le trou du vitrage
        bm_hole = bmesh.new()
        bmesh.ops.create_cube(bm_hole, size=1.0)
        bmesh.ops.scale(bm_hole, vec=(glass_width, self.door_thickness + 0.02, glass_height), verts=bm_hole.verts)
        bmesh.ops.translate(bm_hole, vec=(self.door_width / 2, 0, glass_center_z), verts=bm_hole.verts)

        hole_mesh = bpy.data.meshes.new("GlassHole")
        bm_hole.to_mesh(hole_mesh)
        bm_hole.free()

        hole_obj = bpy.data.objects.new("GlassHole", hole_mesh)
        collection.objects.link(hole_obj)

        bool_mod = obj.modifiers.new("Boolean", 'BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = hole_obj

        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier="Boolean")
        except:
            pass

        bpy.data.objects.remove(hole_obj)
        bpy.data.meshes.remove(hole_mesh)

        # Vitrage
        self._create_glass_panel(
            collection,
            glass_width - 0.015, glass_height - 0.015, 0.008,
            self.door_width / 2, 0, glass_center_z,
            "Vitrage_Central"
        )

        mat = self._create_wood_material("Bois_Porte_Vitree", medium=True)
        obj.data.materials.append(mat)

        for poly in obj.data.polygons:
            poly.use_smooth = True

        obj["house_part"] = "door"
        return obj

    # =================================================================
    # 4. PORTE ALU GRAND VITRAGE
    # =================================================================

    def create_alu_large_glass_door(self, collection):
        """Crée une porte aluminium avec grand vitrage"""

        frame_profile = 0.055
        soubassement_height = 0.40

        glass_width = self.door_width - 2 * frame_profile
        glass_height = self.door_height - frame_profile - soubassement_height - frame_profile
        glass_bottom_z = soubassement_height + frame_profile

        mat = self._create_advanced_alu_material()
        alu_parts = []

        # Montant gauche
        alu_parts.append(self._create_alu_profile(
            collection,
            frame_profile, self.door_thickness, self.door_height,
            frame_profile / 2, 0, self.door_height / 2,
            "Montant_Gauche", mat
        ))

        # Montant droit
        alu_parts.append(self._create_alu_profile(
            collection,
            frame_profile, self.door_thickness, self.door_height,
            self.door_width - frame_profile / 2, 0, self.door_height / 2,
            "Montant_Droit", mat
        ))

        # Traverse haute
        alu_parts.append(self._create_alu_profile(
            collection,
            glass_width, self.door_thickness, frame_profile,
            self.door_width / 2, 0, self.door_height - frame_profile / 2,
            "Traverse_Haute", mat
        ))

        # Traverse basse
        alu_parts.append(self._create_alu_profile(
            collection,
            glass_width, self.door_thickness, frame_profile,
            self.door_width / 2, 0, frame_profile / 2,
            "Traverse_Basse", mat
        ))

        # Traverse intermédiaire
        alu_parts.append(self._create_alu_profile(
            collection,
            glass_width, self.door_thickness, frame_profile,
            self.door_width / 2, 0, soubassement_height + frame_profile / 2,
            "Traverse_Inter", mat
        ))

        # Soubassement
        self._create_alu_profile(
            collection,
            glass_width - 0.01, self.door_thickness * 0.6, soubassement_height - frame_profile - 0.01,
            self.door_width / 2, 0, frame_profile + (soubassement_height - frame_profile) / 2,
            "Soubassement", mat
        )

        # Grand vitrage
        self._create_glass_panel(
            collection,
            glass_width - 0.02, glass_height - 0.02, 0.012,
            self.door_width / 2, 0, glass_bottom_z + glass_height / 2,
            "Vitrage_Grand"
        )

        return alu_parts[0] if alu_parts else None

    def _create_alu_profile(self, collection, width, depth, height, x, y, z, name, mat):
        """Crée un profil aluminium"""

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(width, depth, height), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts)

        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Door_{name}", mesh)
        collection.objects.link(obj)
        obj.data.materials.append(mat)
        obj["house_part"] = "door"

        bevel = obj.modifiers.new("Bevel", 'BEVEL')
        bevel.width = 0.002
        bevel.segments = 2

        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    # =================================================================
    # CADRE / DORMANT
    # =================================================================

    def create_frame(self, collection):
        """Crée le cadre/dormant de la porte"""

        frame_parts = []

        if self.door_style in ['SOLID_WOOD', 'WOOD_CENTER_GLASS']:
            frame_mat = self._create_wood_material("Bois_Cadre", medium=True)
        elif self.door_style == 'PVC_WHITE':
            frame_mat = self._create_pvc_material()
        else:
            frame_mat = self._create_advanced_alu_material()

        frame_y = -self.frame_depth / 2

        # Montant gauche
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.frame_width, self.frame_depth, self.door_height + self.frame_width), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(-self.frame_width / 2, frame_y, (self.door_height + self.frame_width) / 2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Frame_Left")
        bm.to_mesh(mesh)
        bm.free()

        frame_left = bpy.data.objects.new("Door_Frame_Left", mesh)
        collection.objects.link(frame_left)
        frame_left.data.materials.append(frame_mat)
        frame_left["house_part"] = "door_frame"
        frame_parts.append(frame_left)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # Montant droit
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.frame_width, self.frame_depth, self.door_height + self.frame_width), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(self.door_width + self.frame_width / 2, frame_y, (self.door_height + self.frame_width) / 2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Frame_Right")
        bm.to_mesh(mesh)
        bm.free()

        frame_right = bpy.data.objects.new("Door_Frame_Right", mesh)
        collection.objects.link(frame_right)
        frame_right.data.materials.append(frame_mat)
        frame_right["house_part"] = "door_frame"
        frame_parts.append(frame_right)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # Traverse haute
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(self.door_width + 2 * self.frame_width, self.frame_depth, self.frame_width), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(self.door_width / 2, frame_y, self.door_height + self.frame_width / 2), verts=bm.verts)

        mesh = bpy.data.meshes.new("Frame_Top")
        bm.to_mesh(mesh)
        bm.free()

        frame_top = bpy.data.objects.new("Door_Frame_Top", mesh)
        collection.objects.link(frame_top)
        frame_top.data.materials.append(frame_mat)
        frame_top["house_part"] = "door_frame"
        frame_parts.append(frame_top)

        for poly in mesh.polygons:
            poly.use_smooth = True

        return frame_parts

    # =================================================================
    # CHARNIÈRES
    # =================================================================

    def create_hinges(self, collection):
        """Crée les charnières de la porte"""

        hinge_parts = []

        if self.hinge_side == 'LEFT':
            hinge_x = 0.015
        else:
            hinge_x = self.door_width - 0.015

        margin_bottom = 0.20
        margin_top = 0.15
        usable_height = self.door_height - margin_bottom - margin_top

        mat = self._create_hinge_material()

        for i in range(self.hinge_count):
            if self.hinge_count == 2:
                z_positions = [margin_bottom, self.door_height - margin_top]
                hinge_z = z_positions[i]
            else:
                t = i / (self.hinge_count - 1)
                hinge_z = margin_bottom + t * usable_height

            parts = self._create_single_hinge(collection, hinge_x, hinge_z, mat, i)
            hinge_parts.extend(parts)

        return hinge_parts

    def _create_single_hinge(self, collection, x, z, mat, index):
        """Crée une charnière individuelle"""

        parts = []
        door_back = -self.door_thickness / 2

        # Partie fixe
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.025, 0.003, 0.080), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x, door_back - 0.010, z), verts=bm.verts)

        mesh = bpy.data.meshes.new(f"Hinge_Fixed_{index}")
        bm.to_mesh(mesh)
        bm.free()

        fixed_plate = bpy.data.objects.new(f"Door_Hinge_Fixed_{index}", mesh)
        collection.objects.link(fixed_plate)
        fixed_plate.data.materials.append(mat)
        fixed_plate["house_part"] = "door_hinge"
        parts.append(fixed_plate)

        for poly in mesh.polygons:
            poly.use_smooth = True

        # Partie mobile
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.025, 0.003, 0.080), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x, door_back + 0.005, z), verts=bm.verts)

        mesh = bpy.data.meshes.new(f"Hinge_Mobile_{index}")
        bm.to_mesh(mesh)
        bm.free()

        mobile_plate = bpy.data.objects.new(f"Door_Hinge_Mobile_{index}", mesh)
        collection.objects.link(mobile_plate)
        mobile_plate.data.materials.append(mat)
        mobile_plate["house_part"] = "door_hinge"
        parts.append(mobile_plate)

        for poly in mesh.polygons:
            poly.use_smooth = True

        return parts

    # =================================================================
    # POIGNÉE
    # =================================================================

    def create_handle(self, collection):
        """Crée une poignée de porte"""

        handle_parts = []

        if self.hinge_side == 'LEFT':
            handle_x = self.door_width - 0.060
            grip_direction = -1
        else:
            handle_x = 0.060
            grip_direction = 1

        handle_z = self.handle_height
        door_front = self.door_thickness / 2

        # Matériau selon style
        if self.door_style in ['SOLID_WOOD', 'WOOD_CENTER_GLASS']:
            mat = self._create_brass_material()
        elif self.door_style == 'PVC_WHITE':
            mat = self._create_chrome_material()
        else:
            mat = self._create_inox_material()

        # Platine
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(0.040, 0.008, 0.160), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(handle_x, door_front + 0.004, handle_z), verts=bm.verts)

        mesh = bpy.data.meshes.new("Handle_Plate")
        bm.to_mesh(mesh)
        bm.free()

        plate = bpy.data.objects.new("Door_Handle_Plate", mesh)
        collection.objects.link(plate)
        plate.data.materials.append(mat)
        plate["house_part"] = "door_handle"
        handle_parts.append(plate)

        bevel = plate.modifiers.new("Bevel", 'BEVEL')
        bevel.width = 0.006
        bevel.segments = 3

        for poly in mesh.polygons:
            poly.use_smooth = True

        # Rosace
        rosace = self._create_cylinder(
            collection,
            radius=0.020, depth=0.008,
            location=(handle_x, door_front + 0.012, handle_z + 0.035),
            axis='Y', name="Door_Rosace"
        )
        rosace.data.materials.append(mat)
        rosace["house_part"] = "door_handle"
        handle_parts.append(rosace)

        # Tige
        tige = self._create_cylinder(
            collection,
            radius=0.009, depth=0.035,
            location=(handle_x, door_front + 0.035, handle_z + 0.035),
            axis='Y', name="Door_Handle_Stem"
        )
        tige.data.materials.append(mat)
        tige["house_part"] = "door_handle"
        handle_parts.append(tige)

        # Partie à saisir
        grip_x = handle_x + grip_direction * 0.050
        grip = self._create_cylinder(
            collection,
            radius=0.010, depth=0.100,
            location=(grip_x, door_front + 0.052, handle_z + 0.035),
            axis='X', name="Door_Handle_Grip"
        )
        grip.data.materials.append(mat)
        grip["house_part"] = "door_handle"
        handle_parts.append(grip)

        # Entrée de serrure
        serrure = self._create_cylinder(
            collection,
            radius=0.014, depth=0.006,
            location=(handle_x, door_front + 0.011, handle_z - 0.040),
            axis='Y', name="Door_Keyhole"
        )
        serrure.data.materials.append(mat)
        serrure["house_part"] = "door_handle"
        handle_parts.append(serrure)

        return handle_parts

    # =================================================================
    # VITRAGE
    # =================================================================

    def _create_glass_panel(self, collection, width, height, thickness, x, y, z, name):
        """Crée un panneau vitré"""

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(width, thickness, height), verts=bm.verts)
        bmesh.ops.translate(bm, vec=(x, y, z), verts=bm.verts)

        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(f"Door_{name}", mesh)
        collection.objects.link(obj)

        mat = self._create_glass_material()
        obj.data.materials.append(mat)
        obj["house_part"] = "door_glass"

        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    # =================================================================
    # UTILITAIRES GÉOMÉTRIE
    # =================================================================

    def _create_cylinder(self, collection, radius, depth, location, axis, name):
        """Crée un cylindre"""

        bm = bmesh.new()
        bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=False,
            segments=24, radius1=radius, radius2=radius, depth=depth
        )

        if axis == 'Y':
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                           matrix=Matrix.Rotation(math.radians(90), 3, 'X'))
        elif axis == 'X':
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                           matrix=Matrix.Rotation(math.radians(90), 3, 'Y'))

        bmesh.ops.translate(bm, vec=location, verts=bm.verts)

        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()

        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)

        for poly in mesh.polygons:
            poly.use_smooth = True

        return obj

    # =================================================================
    # MATÉRIAUX
    # =================================================================

    def _create_wood_material(self, name, medium=False):
        """Crée un matériau bois réaliste"""

        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()

        wood_colors = {
            'DARK_OAK': ((0.15, 0.08, 0.04), (0.08, 0.04, 0.02)),
            'MEDIUM_OAK': ((0.30, 0.18, 0.08), (0.18, 0.10, 0.05)),
            'LIGHT_OAK': ((0.50, 0.35, 0.18), (0.35, 0.22, 0.10)),
            'WALNUT': ((0.18, 0.10, 0.06), (0.10, 0.05, 0.03)),
            'MAHOGANY': ((0.28, 0.10, 0.06), (0.15, 0.05, 0.03)),
            'WHITE_WASH': ((0.75, 0.72, 0.68), (0.60, 0.55, 0.50)),
        }

        if medium:
            base_color, dark_color = wood_colors['MEDIUM_OAK']
        else:
            base_color, dark_color = wood_colors.get(self.wood_color, wood_colors['DARK_OAK'])

        x = -800
        y = 300

        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (400, 0)

        principled = nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = (100, 0)
        principled.inputs['Roughness'].default_value = 0.35
        principled.inputs['IOR'].default_value = 1.5

        links.new(principled.outputs['BSDF'], output.inputs['Surface'])

        tex_coord = nodes.new('ShaderNodeTexCoord')
        tex_coord.location = (x, y)

        mapping = nodes.new('ShaderNodeMapping')
        mapping.location = (x + 200, y)
        mapping.inputs['Scale'].default_value = (1, 20, 1)

        links.new(tex_coord.outputs['Object'], mapping.inputs['Vector'])

        wave = nodes.new('ShaderNodeTexWave')
        wave.location = (x + 400, y)
        wave.wave_type = 'BANDS'
        wave.bands_direction = 'Z'
        wave.wave_profile = 'SAW'
        wave.inputs['Scale'].default_value = 3.0
        wave.inputs['Distortion'].default_value = 5.0
        wave.inputs['Detail'].default_value = 3.0

        links.new(mapping.outputs['Vector'], wave.inputs['Vector'])

        noise = nodes.new('ShaderNodeTexNoise')
        noise.location = (x + 400, y - 200)
        noise.inputs['Scale'].default_value = 10.0
        noise.inputs['Detail'].default_value = 6.0

        links.new(mapping.outputs['Vector'], noise.inputs['Vector'])

        mix_tex = nodes.new('ShaderNodeMix')
        mix_tex.location = (x + 600, y - 100)
        mix_tex.data_type = 'FLOAT'
        mix_tex.inputs['Factor'].default_value = 0.5

        links.new(wave.outputs['Fac'], mix_tex.inputs['A'])
        links.new(noise.outputs['Fac'], mix_tex.inputs['B'])

        base_col = nodes.new('ShaderNodeRGB')
        base_col.location = (x + 600, y + 150)
        base_col.outputs[0].default_value = (*base_color, 1.0)

        dark_col = nodes.new('ShaderNodeRGB')
        dark_col.location = (x + 600, y)
        dark_col.outputs[0].default_value = (*dark_color, 1.0)

        color_mix = nodes.new('ShaderNodeMix')
        color_mix.location = (x + 800, y + 50)
        color_mix.data_type = 'RGBA'

        links.new(mix_tex.outputs['Result'], color_mix.inputs['Factor'])
        links.new(base_col.outputs[0], color_mix.inputs['A'])
        links.new(dark_col.outputs[0], color_mix.inputs['B'])

        links.new(color_mix.outputs['Result'], principled.inputs['Base Color'])

        bump = nodes.new('ShaderNodeBump')
        bump.location = (x + 800, y - 150)
        bump.inputs['Strength'].default_value = 0.2

        links.new(mix_tex.outputs['Result'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], principled.inputs['Normal'])

        return mat

    def _create_pvc_material(self):
        """Crée un matériau PVC blanc"""

        mat = bpy.data.materials.new(name="PVC_Blanc")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['Base Color'].default_value = (0.92, 0.91, 0.89, 1.0)
        principled.inputs['Roughness'].default_value = 0.35
        principled.inputs['IOR'].default_value = 1.46

        return mat

    def _create_advanced_alu_material(self):
        """Crée un matériau aluminium avancé"""

        mat = bpy.data.materials.new(name=f"Alu_{self.alu_color}_{self.alu_finish}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        alu_colors = {
            'GRIS_ALU': (0.65, 0.65, 0.67),
            'GRIS_ANTHRACITE': (0.18, 0.18, 0.20),
            'NOIR': (0.02, 0.02, 0.02),
            'BLANC': (0.92, 0.91, 0.89),
            'BRONZE': (0.35, 0.25, 0.18),
        }

        roughness_values = {
            'BROSSE': 0.35,
            'SATINE': 0.25,
            'BRILLANT': 0.08,
            'ANODISE': 0.30,
        }

        base_color = alu_colors.get(self.alu_color, alu_colors['GRIS_ANTHRACITE'])
        roughness = roughness_values.get(self.alu_finish, 0.25)

        principled.inputs['Base Color'].default_value = (*base_color, 1.0)
        principled.inputs['Metallic'].default_value = 1.0
        principled.inputs['Roughness'].default_value = roughness

        return mat

    def _create_glass_material(self):
        """Crée un matériau verre"""

        mat = bpy.data.materials.new(name=f"Verre_{self.glass_type}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['IOR'].default_value = 1.52

        if self.glass_type == 'CLEAR':
            principled.inputs['Base Color'].default_value = (0.95, 0.97, 1.0, 1.0)
            principled.inputs['Transmission Weight'].default_value = 0.95
            principled.inputs['Roughness'].default_value = 0.0
        elif self.glass_type == 'FROSTED':
            principled.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
            principled.inputs['Transmission Weight'].default_value = 0.85
            principled.inputs['Roughness'].default_value = 0.4
        else:  # TINTED
            principled.inputs['Base Color'].default_value = (0.70, 0.75, 0.80, 1.0)
            principled.inputs['Transmission Weight'].default_value = 0.90
            principled.inputs['Roughness'].default_value = 0.02

        return mat

    def _create_brass_material(self):
        """Matériau laiton"""
        mat = bpy.data.materials.new(name="Laiton")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['Base Color'].default_value = (0.70, 0.55, 0.25, 1.0)
        principled.inputs['Metallic'].default_value = 1.0
        principled.inputs['Roughness'].default_value = 0.25

        return mat

    def _create_chrome_material(self):
        """Matériau chrome"""
        mat = bpy.data.materials.new(name="Chrome")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['Base Color'].default_value = (0.85, 0.85, 0.88, 1.0)
        principled.inputs['Metallic'].default_value = 1.0
        principled.inputs['Roughness'].default_value = 0.05

        return mat

    def _create_inox_material(self):
        """Matériau inox brossé"""
        mat = bpy.data.materials.new(name="Inox")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['Base Color'].default_value = (0.65, 0.65, 0.68, 1.0)
        principled.inputs['Metallic'].default_value = 1.0
        principled.inputs['Roughness'].default_value = 0.30

        return mat

    def _create_hinge_material(self):
        """Matériau métal satiné pour charnières"""
        mat = bpy.data.materials.new(name="Hinge_Metal")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        principled = nodes.get('Principled BSDF')

        principled.inputs['Base Color'].default_value = (0.55, 0.53, 0.50, 1.0)
        principled.inputs['Metallic'].default_value = 1.0
        principled.inputs['Roughness'].default_value = 0.35

        return mat


# =============================================================================
# FONCTION UTILITAIRE POUR INTÉGRATION HOUSE
# =============================================================================

def generate_door_for_house(collection, props, location, rotation=0):
    """
    Génère une porte pour l'intégration avec le générateur House.

    Args:
        collection: Collection Blender
        props: Propriétés du générateur House
        location: Position (x, y, z)
        rotation: Rotation en radians

    Returns:
        Liste des objets créés
    """
    # Récupérer les propriétés de porte si disponibles
    door_style = getattr(props, 'door_style', 'SOLID_WOOD')
    door_width = getattr(props, 'front_door_width', 0.90)
    door_height = getattr(props, 'door_height', 2.15)
    wood_color = getattr(props, 'door_wood_color', 'DARK_OAK')
    alu_color = getattr(props, 'door_alu_color', 'GRIS_ANTHRACITE')
    alu_finish = getattr(props, 'door_alu_finish', 'SATINE')
    glass_type = getattr(props, 'door_glass_type', 'CLEAR')
    opening_angle = getattr(props, 'door_opening_angle', 0.0)

    # Convertir radians en degrés si nécessaire (Blender stocke en radians avec subtype='ANGLE')
    if opening_angle > 2.0:  # Probablement déjà en degrés
        opening_degrees = opening_angle
    else:
        opening_degrees = math.degrees(opening_angle)

    generator = DoorGenerator(
        door_style=door_style,
        door_width=door_width,
        door_height=door_height,
        wood_color=wood_color,
        alu_color=alu_color,
        alu_finish=alu_finish,
        glass_type=glass_type,
        add_frame=True,
        add_handle=True,
        add_hinges=True,
        opening_angle=opening_degrees
    )

    return generator.generate(collection, location, rotation)
