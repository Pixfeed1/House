# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Système de Distribution des Pièces COMPLET (BLENDER 4.2+)
#  Copyright (C) 2025
#
#  Génération automatique et manuelle de cloisons/murs intérieurs
#  Multi-étages + Portes + Distribution architecturale intelligente
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from mathutils import Vector
import math


# =============================================================================
# PRINCIPES ARCHITECTURAUX
# =============================================================================

# Largeurs standard des portes (en mètres)
DOOR_WIDTH_STANDARD = 0.80  # Porte intérieure standard
DOOR_WIDTH_BATHROOM = 0.70  # Porte SDB (plus étroite)
DOOR_WIDTH_LARGE = 0.90     # Porte principale / salon
DOOR_HEIGHT = 2.04          # Hauteur standard

# Distances minimales
MIN_CORRIDOR_WIDTH = 0.90   # Largeur minimum couloir
MIN_ROOM_WIDTH = 2.50       # Largeur minimum pièce viable
MIN_ROOM_LENGTH = 2.50      # Longueur minimum pièce viable

# Types de pièces
ROOM_TYPES = {
    'LIVING': {'name': 'Salon', 'min_area': 12.0, 'door_width': DOOR_WIDTH_LARGE},
    'KITCHEN': {'name': 'Cuisine', 'min_area': 6.0, 'door_width': DOOR_WIDTH_LARGE},
    'BEDROOM': {'name': 'Chambre', 'min_area': 9.0, 'door_width': DOOR_WIDTH_STANDARD},
    'BATHROOM': {'name': 'Salle de bain', 'min_area': 3.0, 'door_width': DOOR_WIDTH_BATHROOM},
    'OFFICE': {'name': 'Bureau', 'min_area': 6.0, 'door_width': DOOR_WIDTH_STANDARD},
    'STORAGE': {'name': 'Débarras', 'min_area': 2.0, 'door_width': DOOR_WIDTH_BATHROOM},
    'WC': {'name': 'WC', 'min_area': 1.5, 'door_width': DOOR_WIDTH_BATHROOM},
}


class RoomLayoutGenerator:
    """Générateur de distribution de pièces avec cloisons et portes"""

    def __init__(self, width, length, num_floors=1, wall_thickness=0.10, window_positions=None):
        """
        Initialise le générateur de distribution.

        Args:
            width: Largeur totale de la maison
            length: Longueur totale de la maison
            num_floors: Nombre d'étages
            wall_thickness: Épaisseur des cloisons (10cm par défaut)
            window_positions: Dict avec positions des fenêtres {'window_x': [...], 'window_y': [...]}
        """
        self.width = width
        self.length = length
        self.num_floors = num_floors
        self.wall_thickness = wall_thickness
        self.window_positions = window_positions or {'window_x': [], 'window_y': [], 'door_x': 0, 'door_width': 1.0}
        self.partitions_per_floor = {}  # {floor_num: [partitions]}
        self.doors_per_floor = {}        # {floor_num: [doors]}
        self.rooms_per_floor = {}        # {floor_num: [room_specs]}

        # Marge de sécurité autour des fenêtres (60cm de chaque côté)
        self.window_clearance = 0.60

        print(f"[RoomLayout] Initialisation avec {len(self.window_positions.get('window_x', []))} fenêtres X, {len(self.window_positions.get('window_y', []))} fenêtres Y")

    def _check_partition_collision(self, partition_type, position):
        """
        Vérifie si une cloison entre en collision avec une fenêtre.

        Args:
            partition_type: 'vertical' (position X) ou 'horizontal' (position Y)
            position: Position de la cloison (X pour vertical, Y pour horizontal)

        Returns:
            True si collision, False sinon
        """
        if partition_type == 'vertical':
            # Cloison verticale (va dans direction Y) → vérifier fenêtres sur murs avant/arrière (position X)
            for window_x in self.window_positions.get('window_x', []):
                if abs(position - window_x) < self.window_clearance:
                    print(f"[RoomLayout]   ⚠️  Collision détectée: cloison verticale à X={position:.2f}m proche fenêtre à X={window_x:.2f}m")
                    return True

            # Vérifier aussi la porte d'entrée
            door_x = self.window_positions.get('door_x', 0)
            door_width = self.window_positions.get('door_width', 1.0)
            if abs(position - door_x) < (door_width / 2 + self.window_clearance):
                print(f"[RoomLayout]   ⚠️  Collision détectée: cloison verticale à X={position:.2f}m proche porte à X={door_x:.2f}m")
                return True

        elif partition_type == 'horizontal':
            # Cloison horizontale (va dans direction X) → vérifier fenêtres sur murs gauche/droit (position Y)
            for window_y in self.window_positions.get('window_y', []):
                if abs(position - window_y) < self.window_clearance:
                    print(f"[RoomLayout]   ⚠️  Collision détectée: cloison horizontale à Y={position:.2f}m proche fenêtre à Y={window_y:.2f}m")
                    return True

        return False

    def _adjust_partition_position(self, partition_type, original_position, min_offset=0.80):
        """
        Ajuste la position d'une cloison pour éviter les fenêtres.

        Args:
            partition_type: 'vertical' ou 'horizontal'
            original_position: Position originale souhaitée
            min_offset: Distance minimum à déplacer si collision (80cm par défaut)

        Returns:
            Nouvelle position ajustée, ou None si impossible de placer
        """
        if not self._check_partition_collision(partition_type, original_position):
            return original_position

        # Essayer de décaler vers la gauche/bas
        adjusted = original_position - min_offset
        if adjusted > 0.5 and not self._check_partition_collision(partition_type, adjusted):
            print(f"[RoomLayout]   ✅ Cloison ajustée: {original_position:.2f}m → {adjusted:.2f}m")
            return adjusted

        # Essayer de décaler vers la droite/haut
        adjusted = original_position + min_offset
        max_pos = self.width if partition_type == 'vertical' else self.length
        if adjusted < (max_pos - 0.5) and not self._check_partition_collision(partition_type, adjusted):
            print(f"[RoomLayout]   ✅ Cloison ajustée: {original_position:.2f}m → {adjusted:.2f}m")
            return adjusted

        # Impossible de placer cette cloison
        print(f"[RoomLayout]   ❌ Impossible de placer cloison à {original_position:.2f}m (trop de fenêtres)")
        return None

    def generate_auto_layout(self, num_rooms, include_kitchen=True, include_bathroom=True, num_bathrooms=1):
        """
        Génère une distribution automatique intelligente des pièces sur TOUS les étages.

        Args:
            num_rooms: Nombre de pièces principales TOTAL (réparties sur tous les étages)
            include_kitchen: Inclure une cuisine
            include_bathroom: Inclure salle(s) de bain
            num_bathrooms: Nombre de salles de bain TOTAL

        Returns:
            Dict {floor_num: {'partitions': [...], 'doors': [...]}}
        """
        print(f"[RoomLayout] Génération AUTO multi-étages: {num_rooms} pièces sur {self.num_floors} étage(s)")

        # Réinitialiser
        self.partitions_per_floor = {}
        self.doors_per_floor = {}
        self.rooms_per_floor = {}

        # Répartir les pièces par étage selon principes architecturaux
        rooms_distribution = self._distribute_rooms_by_floor(
            num_rooms, include_kitchen, include_bathroom, num_bathrooms
        )

        # Générer la distribution pour chaque étage
        for floor_num in range(self.num_floors):
            if floor_num not in rooms_distribution:
                continue

            floor_rooms = rooms_distribution[floor_num]
            print(f"[RoomLayout] Étage {floor_num}: {len(floor_rooms)} pièces - {[r['type'] for r in floor_rooms]}")

            # Générer layout pour cet étage
            partitions, doors = self._generate_floor_layout(floor_num, floor_rooms)

            self.partitions_per_floor[floor_num] = partitions
            self.doors_per_floor[floor_num] = doors
            self.rooms_per_floor[floor_num] = floor_rooms

        total_partitions = sum(len(p) for p in self.partitions_per_floor.values())
        total_doors = sum(len(d) for d in self.doors_per_floor.values())
        print(f"[RoomLayout] Total: {total_partitions} cloisons, {total_doors} portes")

        return {
            'partitions': self.partitions_per_floor,
            'doors': self.doors_per_floor,
            'rooms': self.rooms_per_floor
        }

    def _distribute_rooms_by_floor(self, num_rooms, include_kitchen, include_bathroom, num_bathrooms):
        """
        Répartit intelligemment les pièces par étage selon principes architecturaux.

        PRINCIPES:
        - RDC (étage 0): Pièces de vie (salon, cuisine, 1 SDB/WC)
        - Étages supérieurs: Chambres, bureaux, SDB

        Returns:
            Dict {floor_num: [room_specs]}
        """
        distribution = {}

        if self.num_floors == 1:
            # Maison plain-pied : tout au RDC
            rooms = []
            if include_kitchen:
                rooms.append({'type': 'KITCHEN'})

            # Chambres/salon
            if num_rooms == 1:
                rooms.append({'type': 'LIVING'})
            else:
                rooms.append({'type': 'LIVING'})
                for i in range(num_rooms - 1):
                    rooms.append({'type': 'BEDROOM', 'number': i + 1})

            # SDB
            for i in range(num_bathrooms):
                rooms.append({'type': 'BATHROOM', 'number': i + 1})

            distribution[0] = rooms

        else:
            # Multi-étages : répartition intelligente

            # RDC: Salon + Cuisine + 1 SDB/WC
            rdc_rooms = []
            rdc_rooms.append({'type': 'LIVING'})

            if include_kitchen:
                rdc_rooms.append({'type': 'KITCHEN'})

            if include_bathroom:
                rdc_rooms.append({'type': 'WC'})  # WC au RDC

            distribution[0] = rdc_rooms

            # Étages supérieurs: Chambres + SDB
            bedrooms_to_place = num_rooms - 1  # Moins le salon
            bathrooms_to_place = num_bathrooms - (1 if include_bathroom else 0)

            upper_floors = self.num_floors - 1
            bedrooms_per_floor = math.ceil(bedrooms_to_place / upper_floors)

            for floor_num in range(1, self.num_floors):
                floor_rooms = []

                # Chambres
                start_bedroom = (floor_num - 1) * bedrooms_per_floor
                end_bedroom = min(start_bedroom + bedrooms_per_floor, bedrooms_to_place)

                for i in range(start_bedroom, end_bedroom):
                    floor_rooms.append({'type': 'BEDROOM', 'number': i + 1})

                # SDB (1 par étage si multi-étages)
                if bathrooms_to_place > 0:
                    floor_rooms.append({'type': 'BATHROOM', 'number': floor_num})
                    bathrooms_to_place -= 1

                distribution[floor_num] = floor_rooms

        return distribution

    def _generate_floor_layout(self, floor_num, rooms):
        """
        Génère le layout pour un étage spécifique.

        Args:
            floor_num: Numéro de l'étage
            rooms: Liste des specs de pièces pour cet étage

        Returns:
            (partitions, doors) : Listes des cloisons et portes
        """
        partitions = []
        doors = []

        # Stratégie selon le nombre de pièces
        num_rooms = len(rooms)

        if num_rooms == 1:
            # Une seule pièce : pas de cloison
            return partitions, doors

        elif num_rooms == 2:
            # 2 pièces : division simple
            partitions, doors = self._layout_2_rooms(floor_num, rooms)

        elif num_rooms == 3:
            # 3 pièces : disposition en L ou T
            partitions, doors = self._layout_3_rooms(floor_num, rooms)

        elif num_rooms >= 4:
            # 4+ pièces : grille avec couloir
            partitions, doors = self._layout_multi_rooms(floor_num, rooms)

        return partitions, doors

    def _layout_2_rooms(self, floor_num, rooms):
        """Layout pour 2 pièces avec évitement fenêtres"""
        partitions = []
        doors = []

        # Division verticale au milieu
        mid_x = self.width / 2

        # ✅ Vérifier et ajuster position cloison
        adjusted_x = self._adjust_partition_position('vertical', mid_x)

        if adjusted_x is not None:
            # Cloison centrale
            partitions.append({
                'type': 'vertical',
                'x': adjusted_x,
                'y_start': 0,
                'y_end': self.length,
                'height': 2.5,
                'floor': floor_num
            })

            # Porte au milieu de la cloison
            door_y = self.length / 2
            doors.append({
                'partition_index': len(partitions) - 1,
                'position_along': door_y,
                'width': DOOR_WIDTH_STANDARD,
                'type': 'center',
                'floor': floor_num
            })
        else:
            print(f"[RoomLayout] ⚠️  Impossible de créer layout 2 pièces (conflit fenêtres)")

        return partitions, doors

    def _layout_3_rooms(self, floor_num, rooms):
        """Layout pour 3 pièces avec évitement fenêtres"""
        partitions = []
        doors = []

        # Vérifier si une pièce est une SDB (plus petite)
        has_bathroom = any(r['type'] in ['BATHROOM', 'WC'] for r in rooms)

        if has_bathroom:
            # Layout: Grande zone gauche (60%) + 2 pièces droite empilées
            mid_x = self.width * 0.6
            mid_y = self.length / 2

            # ✅ Vérifier et ajuster cloison verticale
            adjusted_x = self._adjust_partition_position('vertical', mid_x)

            if adjusted_x is not None:
                # Cloison verticale principale
                partitions.append({
                    'type': 'vertical',
                    'x': adjusted_x,
                    'y_start': 0,
                    'y_end': self.length,
                    'height': 2.5,
                    'floor': floor_num
                })

                # Porte dans cloison verticale (vers le haut)
                doors.append({
                    'partition_index': len(partitions) - 1,
                    'position_along': self.length * 0.75,
                    'width': DOOR_WIDTH_STANDARD,
                    'type': 'corridor',
                    'floor': floor_num
                })

            # ✅ Vérifier et ajuster cloison horizontale
            adjusted_y = self._adjust_partition_position('horizontal', mid_y)

            if adjusted_y is not None and adjusted_x is not None:
                # Cloison horizontale (divise zone droite en 2)
                partitions.append({
                    'type': 'horizontal',
                    'x_start': adjusted_x,
                    'x_end': self.width,
                    'y': adjusted_y,
                    'height': 2.5,
                    'floor': floor_num
                })

                # Porte dans SDB (pièce du haut généralement)
                doors.append({
                    'partition_index': len(partitions) - 1,
                    'position_along': adjusted_x + (self.width - adjusted_x) * 0.5,
                    'width': DOOR_WIDTH_BATHROOM,
                    'type': 'bathroom',
                    'floor': floor_num
                })

        else:
            # Layout symétrique : 3 pièces équilibrées
            third_x = self.width / 3
            two_thirds_x = 2 * self.width / 3

            # ✅ Vérifier et ajuster les 2 cloisons verticales
            adjusted_x1 = self._adjust_partition_position('vertical', third_x)
            adjusted_x2 = self._adjust_partition_position('vertical', two_thirds_x)

            partition_indices = []

            if adjusted_x1 is not None:
                partitions.append({
                    'type': 'vertical',
                    'x': adjusted_x1,
                    'y_start': 0,
                    'y_end': self.length,
                    'height': 2.5,
                    'floor': floor_num
                })
                partition_indices.append(len(partitions) - 1)

            if adjusted_x2 is not None:
                partitions.append({
                    'type': 'vertical',
                    'x': adjusted_x2,
                    'y_start': 0,
                    'y_end': self.length,
                    'height': 2.5,
                    'floor': floor_num
                })
                partition_indices.append(len(partitions) - 1)

            # Portes
            door_y = self.length / 2
            for idx in partition_indices:
                doors.append({
                    'partition_index': idx,
                    'position_along': door_y,
                    'width': DOOR_WIDTH_STANDARD,
                    'type': 'center',
                    'floor': floor_num
                })

        return partitions, doors

    def _layout_multi_rooms(self, floor_num, rooms):
        """Layout pour 4+ pièces avec couloir central et évitement fenêtres"""
        partitions = []
        doors = []

        num_rooms = len(rooms)

        # Couloir central horizontal (20% de la longueur)
        corridor_width = max(MIN_CORRIDOR_WIDTH, self.length * 0.2)
        corridor_y_start = (self.length - corridor_width) / 2
        corridor_y_end = corridor_y_start + corridor_width

        # ✅ Vérifier et ajuster positions cloisons horizontales du couloir
        adjusted_y_start = self._adjust_partition_position('horizontal', corridor_y_start)
        adjusted_y_end = self._adjust_partition_position('horizontal', corridor_y_end)

        # Si impossible de placer le couloir, fallback sur layout plus simple
        if adjusted_y_start is None or adjusted_y_end is None:
            print(f"[RoomLayout] ⚠️  Impossible de créer couloir (conflit fenêtres), fallback layout simple")
            # Fallback: division verticale simple
            mid_x = self.width / 2
            adjusted_x = self._adjust_partition_position('vertical', mid_x)
            if adjusted_x is not None:
                partitions.append({
                    'type': 'vertical',
                    'x': adjusted_x,
                    'y_start': 0,
                    'y_end': self.length,
                    'height': 2.5,
                    'floor': floor_num
                })
                doors.append({
                    'partition_index': 0,
                    'position_along': self.length / 2,
                    'width': DOOR_WIDTH_STANDARD,
                    'type': 'center',
                    'floor': floor_num
                })
            return partitions, doors

        # Diviser en zones : haut / couloir / bas
        # Chaque zone peut avoir 2 pièces (gauche/droite)

        # Cloisons horizontales du couloir
        partitions.append({
            'type': 'horizontal',
            'x_start': 0,
            'x_end': self.width,
            'y': adjusted_y_start,
            'height': 2.5,
            'floor': floor_num
        })

        partitions.append({
            'type': 'horizontal',
            'x_start': 0,
            'x_end': self.width,
            'y': adjusted_y_end,
            'height': 2.5,
            'floor': floor_num
        })

        # Portes vers le couloir (haut)
        doors.append({
            'partition_index': 0,
            'position_along': self.width * 0.25,
            'width': DOOR_WIDTH_STANDARD,
            'type': 'corridor',
            'floor': floor_num
        })

        doors.append({
            'partition_index': 0,
            'position_along': self.width * 0.75,
            'width': DOOR_WIDTH_STANDARD,
            'type': 'corridor',
            'floor': floor_num
        })

        # Portes vers le couloir (bas)
        doors.append({
            'partition_index': 1,
            'position_along': self.width * 0.25,
            'width': DOOR_WIDTH_STANDARD,
            'type': 'corridor',
            'floor': floor_num
        })

        doors.append({
            'partition_index': 1,
            'position_along': self.width * 0.75,
            'width': DOOR_WIDTH_STANDARD,
            'type': 'corridor',
            'floor': floor_num
        })

        # Cloisons verticales pour diviser haut et bas en 2 pièces chacun
        mid_x = self.width / 2

        # ✅ Vérifier et ajuster cloison verticale
        adjusted_x = self._adjust_partition_position('vertical', mid_x)

        if adjusted_x is not None:
            # Zone haute
            partitions.append({
                'type': 'vertical',
                'x': adjusted_x,
                'y_start': adjusted_y_end,
                'y_end': self.length,
                'height': 2.5,
                'floor': floor_num
            })

            # Zone basse
            partitions.append({
                'type': 'vertical',
                'x': adjusted_x,
                'y_start': 0,
                'y_end': adjusted_y_start,
                'height': 2.5,
                'floor': floor_num
            })
        else:
            print(f"[RoomLayout] ⚠️  Impossible de créer cloison verticale (conflit fenêtres)")

        return partitions, doors

    def create_partition_meshes(self, collection, floor_height=2.5):
        """
        Crée les mesh 3D des cloisons AVEC portes pour tous les étages.

        Args:
            collection: Collection Blender où ajouter les objets
            floor_height: Hauteur par défaut des pièces

        Returns:
            Liste des objets créés
        """
        all_objects = []

        for floor_num, partitions in self.partitions_per_floor.items():
            z_base = floor_num * floor_height
            doors = self.doors_per_floor.get(floor_num, [])

            for i, partition in enumerate(partitions):
                partition_type = partition['type']
                height = partition.get('height', floor_height)

                # Créer cloison avec porte si nécessaire
                partition_obj = self._create_partition_with_door(
                    partition, i, doors, z_base, height, collection
                )

                if partition_obj:
                    all_objects.append(partition_obj)

        print(f"[RoomLayout] {len(all_objects)} cloisons créées avec portes")
        return all_objects

    def _create_partition_with_door(self, partition, partition_idx, doors, z_base, height, collection):
        """Crée une cloison avec découpe de porte si nécessaire"""

        # Trouver les portes pour cette cloison
        partition_doors = [d for d in doors if d.get('partition_index') == partition_idx]

        bm = bmesh.new()

        try:
            partition_type = partition['type']

            if partition_type == 'vertical':
                x = partition['x']
                y_start = partition['y_start']
                y_end = partition['y_end']

                # Créer segments entre les portes
                segments = self._calculate_wall_segments(
                    y_start, y_end, partition_doors, is_vertical=True
                )

                for seg_start, seg_end in segments:
                    # Créer morceau de cloison
                    verts = [
                        bm.verts.new(Vector((x - self.wall_thickness/2, seg_start, z_base))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, seg_start, z_base))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, seg_end, z_base))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, seg_end, z_base))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, seg_start, z_base + height))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, seg_start, z_base + height))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, seg_end, z_base + height))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, seg_end, z_base + height))),
                    ]
                    self._create_box_faces(bm, verts)

            elif partition_type == 'horizontal':
                y = partition['y']
                x_start = partition['x_start']
                x_end = partition['x_end']

                # Créer segments entre les portes
                segments = self._calculate_wall_segments(
                    x_start, x_end, partition_doors, is_vertical=False
                )

                for seg_start, seg_end in segments:
                    # Créer morceau de cloison
                    verts = [
                        bm.verts.new(Vector((seg_start, y - self.wall_thickness/2, z_base))),
                        bm.verts.new(Vector((seg_end, y - self.wall_thickness/2, z_base))),
                        bm.verts.new(Vector((seg_end, y + self.wall_thickness/2, z_base))),
                        bm.verts.new(Vector((seg_start, y + self.wall_thickness/2, z_base))),
                        bm.verts.new(Vector((seg_start, y - self.wall_thickness/2, z_base + height))),
                        bm.verts.new(Vector((seg_end, y - self.wall_thickness/2, z_base + height))),
                        bm.verts.new(Vector((seg_end, y + self.wall_thickness/2, z_base + height))),
                        bm.verts.new(Vector((seg_start, y + self.wall_thickness/2, z_base + height))),
                    ]
                    self._create_box_faces(bm, verts)

            # Créer le mesh
            if len(bm.verts) > 0:
                mesh = bpy.data.meshes.new(f"Partition_F{partition.get('floor', 0)}_{partition_idx}")
                bm.to_mesh(mesh)
                bm.free()

                obj = bpy.data.objects.new(mesh.name, mesh)
                obj["house_part"] = "partition"
                obj["floor"] = partition.get('floor', 0)
                collection.objects.link(obj)
                return obj
            else:
                bm.free()
                return None

        except Exception as e:
            print(f"[RoomLayout] Erreur création cloison: {e}")
            bm.free()
            return None

    def _calculate_wall_segments(self, start, end, doors, is_vertical):
        """
        Calcule les segments de mur entre les portes.

        Args:
            start: Position de début
            end: Position de fin
            doors: Liste des portes sur cette cloison
            is_vertical: True si cloison verticale (portes sur Y), False si horizontale (portes sur X)

        Returns:
            Liste de tuples (seg_start, seg_end) pour chaque segment de mur
        """
        if not doors:
            return [(start, end)]

        # Trier les portes par position
        doors_sorted = sorted(doors, key=lambda d: d['position_along'])

        segments = []
        current_pos = start

        for door in doors_sorted:
            door_pos = door['position_along']
            door_width = door['width']
            door_start = door_pos - door_width / 2
            door_end = door_pos + door_width / 2

            # Segment avant la porte
            if current_pos < door_start - 0.01:
                segments.append((current_pos, door_start))

            # Sauter la porte
            current_pos = door_end

        # Segment final après la dernière porte
        if current_pos < end - 0.01:
            segments.append((current_pos, end))

        return segments

    def _create_box_faces(self, bm, verts):
        """Crée les faces d'une boîte"""
        bm.verts.ensure_lookup_table()

        faces = [
            (0, 1, 2, 3),  # Bottom
            (4, 7, 6, 5),  # Top
            (0, 4, 5, 1),  # Side 1
            (2, 6, 7, 3),  # Side 2
            (0, 3, 7, 4),  # End 1
            (1, 5, 6, 2),  # End 2
        ]

        for face_verts in faces:
            try:
                bm.faces.new([verts[j] for j in face_verts])
            except:
                pass
