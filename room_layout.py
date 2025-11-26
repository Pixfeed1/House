# ##### BEGIN GPL LICENSE BLOCK #####
#
#  House - Système de Distribution des Pièces (BLENDER 4.2+ COMPATIBLE)
#  Copyright (C) 2025
#
#  Génération automatique et manuelle de cloisons/murs intérieurs
#  pour créer des pièces (chambres, cuisine, salle de bain, etc.)
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from mathutils import Vector
import math


class RoomLayoutGenerator:
    """Générateur de distribution de pièces avec cloisons"""

    def __init__(self, width, length, wall_thickness=0.10):
        """
        Initialise le générateur de distribution.

        Args:
            width: Largeur totale de la maison
            length: Longueur totale de la maison
            wall_thickness: Épaisseur des cloisons (10cm par défaut)
        """
        self.width = width
        self.length = length
        self.wall_thickness = wall_thickness
        self.partitions = []  # Liste des cloisons à générer

    def generate_auto_layout(self, num_rooms, include_kitchen=True, include_bathroom=True, num_bathrooms=1):
        """
        Génère une distribution automatique intelligente des pièces.

        Args:
            num_rooms: Nombre de pièces principales (chambres/salon)
            include_kitchen: Inclure une cuisine
            include_bathroom: Inclure salle(s) de bain
            num_bathrooms: Nombre de salles de bain

        Returns:
            Liste de dictionnaires décrivant chaque cloison
        """
        self.partitions = []

        print(f"[RoomLayout] Génération AUTO: {num_rooms} pièces, cuisine={include_kitchen}, SDB={num_bathrooms}")

        # Stratégies selon le nombre de pièces
        if num_rooms == 1:
            # Studio : juste une salle de bain si demandée
            self._layout_studio(include_bathroom, num_bathrooms)
        elif num_rooms == 2:
            # T2 : salon + 1 chambre + cuisine + SDB
            self._layout_t2(include_kitchen, include_bathroom, num_bathrooms)
        elif num_rooms == 3:
            # T3 : salon + 2 chambres + cuisine + SDB
            self._layout_t3(include_kitchen, include_bathroom, num_bathrooms)
        elif num_rooms == 4:
            # T4 : salon + 3 chambres + cuisine + SDB
            self._layout_t4(include_kitchen, include_bathroom, num_bathrooms)
        else:
            # T5+ : distribution adaptative
            self._layout_large(num_rooms, include_kitchen, include_bathroom, num_bathrooms)

        print(f"[RoomLayout] {len(self.partitions)} cloisons générées")
        return self.partitions

    def _layout_studio(self, include_bathroom, num_bathrooms):
        """Studio : espace ouvert + SDB"""
        if include_bathroom and num_bathrooms > 0:
            # SDB dans le coin arrière gauche (2m x 2m)
            bathroom_width = min(2.0, self.width * 0.3)
            bathroom_length = min(2.0, self.length * 0.3)

            # Cloison horizontale pour fermer la SDB (côté longueur)
            self.partitions.append({
                'type': 'horizontal',
                'x_start': 0,
                'x_end': bathroom_width,
                'y': bathroom_length,
                'height': 2.5,
                'room': 'bathroom'
            })

            # Cloison verticale pour fermer la SDB (côté largeur)
            self.partitions.append({
                'type': 'vertical',
                'y_start': 0,
                'y_end': bathroom_length,
                'x': bathroom_width,
                'height': 2.5,
                'room': 'bathroom'
            })

    def _layout_t2(self, include_kitchen, include_bathroom, num_bathrooms):
        """T2 : Salon + 1 chambre + cuisine + SDB"""

        # Division principale verticale au milieu
        mid_x = self.width / 2

        # Cloison centrale verticale (divise en 2 moitiés)
        self.partitions.append({
            'type': 'vertical',
            'y_start': self.length * 0.3,  # Laisser passage
            'y_end': self.length,
            'x': mid_x,
            'height': 2.5,
            'room': 'separator'
        })

        # Côté gauche = salon
        # Côté droit = chambre

        # SDB dans coin arrière droit (dans la chambre)
        if include_bathroom and num_bathrooms > 0:
            bathroom_width = min(1.8, self.width * 0.25)
            bathroom_length = min(2.5, self.length * 0.35)

            # Cloison horizontale SDB
            self.partitions.append({
                'type': 'horizontal',
                'x_start': mid_x,
                'x_end': self.width,
                'y': self.length - bathroom_length,
                'height': 2.5,
                'room': 'bathroom'
            })

            # Cloison verticale SDB
            self.partitions.append({
                'type': 'vertical',
                'y_start': self.length - bathroom_length,
                'y_end': self.length,
                'x': self.width - bathroom_width,
                'height': 2.5,
                'room': 'bathroom'
            })

        # Cuisine en L dans le salon (coin avant gauche)
        if include_kitchen:
            kitchen_width = min(2.5, self.width * 0.4)
            kitchen_length = min(2.0, self.length * 0.3)

            # Cloison horizontale cuisine (partielle pour cuisine ouverte)
            self.partitions.append({
                'type': 'horizontal',
                'x_start': 0,
                'x_end': kitchen_width * 0.6,  # Cuisine semi-ouverte
                'y': kitchen_length,
                'height': 2.5,
                'room': 'kitchen'
            })

    def _layout_t3(self, include_kitchen, include_bathroom, num_bathrooms):
        """T3 : Salon + 2 chambres + cuisine + SDB"""

        # Division verticale : gauche (salon + cuisine) / droite (chambres + SDB)
        mid_x = self.width * 0.55

        # Cloison centrale verticale principale
        self.partitions.append({
            'type': 'vertical',
            'y_start': self.length * 0.25,
            'y_end': self.length,
            'x': mid_x,
            'height': 2.5,
            'room': 'separator'
        })

        # Côté droit : diviser en 2 chambres (horizontal au milieu)
        mid_y = self.length / 2

        # Cloison horizontale séparant les 2 chambres
        self.partitions.append({
            'type': 'horizontal',
            'x_start': mid_x,
            'x_end': self.width,
            'y': mid_y,
            'height': 2.5,
            'room': 'bedroom_separator'
        })

        # SDB dans la chambre du haut (coin arrière droit)
        if include_bathroom and num_bathrooms > 0:
            bathroom_width = min(1.8, (self.width - mid_x) * 0.4)
            bathroom_length = min(2.2, (self.length - mid_y) * 0.5)

            # Cloison horizontale SDB
            self.partitions.append({
                'type': 'horizontal',
                'x_start': self.width - bathroom_width,
                'x_end': self.width,
                'y': self.length - bathroom_length,
                'height': 2.5,
                'room': 'bathroom'
            })

            # Cloison verticale SDB
            self.partitions.append({
                'type': 'vertical',
                'y_start': self.length - bathroom_length,
                'y_end': self.length,
                'x': self.width - bathroom_width,
                'height': 2.5,
                'room': 'bathroom'
            })

        # Cuisine dans le salon (coin avant gauche)
        if include_kitchen:
            kitchen_width = min(3.0, mid_x * 0.5)
            kitchen_length = min(2.5, self.length * 0.3)

            # Cloison horizontale cuisine (semi-ouverte)
            self.partitions.append({
                'type': 'horizontal',
                'x_start': 0,
                'x_end': kitchen_width * 0.7,
                'y': kitchen_length,
                'height': 2.5,
                'room': 'kitchen'
            })

    def _layout_t4(self, include_kitchen, include_bathroom, num_bathrooms):
        """T4 : Salon + 3 chambres + cuisine + SDB(s)"""

        # Division : gauche 40% (salon+cuisine) / droite 60% (chambres)
        mid_x = self.width * 0.4

        # Cloison centrale verticale
        self.partitions.append({
            'type': 'vertical',
            'y_start': self.length * 0.2,
            'y_end': self.length,
            'x': mid_x,
            'height': 2.5,
            'room': 'separator'
        })

        # Côté droit : diviser en 3 chambres (2 rangées)
        # Rangée du haut : 2 chambres
        # Rangée du bas : 1 grande chambre

        third_y = self.length / 3
        two_thirds_y = 2 * self.length / 3

        # Cloison horizontale séparant rangée haute et basse
        self.partitions.append({
            'type': 'horizontal',
            'x_start': mid_x,
            'x_end': self.width,
            'y': two_thirds_y,
            'height': 2.5,
            'room': 'bedroom_separator'
        })

        # Diviser le haut en 2 chambres (verticale au milieu)
        right_mid_x = mid_x + (self.width - mid_x) / 2

        self.partitions.append({
            'type': 'vertical',
            'y_start': two_thirds_y,
            'y_end': self.length,
            'x': right_mid_x,
            'height': 2.5,
            'room': 'bedroom_separator'
        })

        # SDB dans chambre arrière gauche (du côté chambres)
        if include_bathroom and num_bathrooms > 0:
            bathroom_width = min(1.8, (right_mid_x - mid_x) * 0.5)
            bathroom_length = min(2.0, (self.length - two_thirds_y) * 0.6)

            # Cloison horizontale SDB
            self.partitions.append({
                'type': 'horizontal',
                'x_start': mid_x,
                'x_end': mid_x + bathroom_width,
                'y': self.length - bathroom_length,
                'height': 2.5,
                'room': 'bathroom'
            })

            # Cloison verticale SDB
            self.partitions.append({
                'type': 'vertical',
                'y_start': self.length - bathroom_length,
                'y_end': self.length,
                'x': mid_x + bathroom_width,
                'height': 2.5,
                'room': 'bathroom'
            })

            # 2ème SDB si demandée (dans grande chambre du bas)
            if num_bathrooms >= 2:
                bathroom2_width = min(1.6, (self.width - mid_x) * 0.3)
                bathroom2_length = min(2.0, two_thirds_y * 0.4)

                self.partitions.append({
                    'type': 'horizontal',
                    'x_start': self.width - bathroom2_width,
                    'x_end': self.width,
                    'y': bathroom2_length,
                    'height': 2.5,
                    'room': 'bathroom2'
                })

                self.partitions.append({
                    'type': 'vertical',
                    'y_start': 0,
                    'y_end': bathroom2_length,
                    'x': self.width - bathroom2_width,
                    'height': 2.5,
                    'room': 'bathroom2'
                })

        # Cuisine dans le salon
        if include_kitchen:
            kitchen_width = min(3.0, mid_x * 0.6)
            kitchen_length = min(3.0, self.length * 0.35)

            self.partitions.append({
                'type': 'horizontal',
                'x_start': 0,
                'x_end': kitchen_width * 0.7,
                'y': kitchen_length,
                'height': 2.5,
                'room': 'kitchen'
            })

    def _layout_large(self, num_rooms, include_kitchen, include_bathroom, num_bathrooms):
        """T5+ : Distribution adaptative pour grandes maisons"""
        # Pour simplifier : utiliser T4 et ajouter des divisions supplémentaires
        self._layout_t4(include_kitchen, include_bathroom, num_bathrooms)

        # Ajouter des divisions supplémentaires selon num_rooms
        # (peut être amélioré avec un algorithme plus sophistiqué)

    def generate_manual_layout(self, partitions_list):
        """
        Génère une distribution manuelle basée sur une liste de cloisons.

        Args:
            partitions_list: Liste de dict avec specs des cloisons
                Ex: [{'type': 'vertical', 'x': 3.0, 'y_start': 0, 'y_end': 5, 'height': 2.5}]
        """
        self.partitions = partitions_list
        print(f"[RoomLayout] Génération MANUELLE: {len(partitions_list)} cloisons")
        return self.partitions

    def create_partition_meshes(self, collection, floor_height=2.5):
        """
        Crée les mesh 3D des cloisons.

        Args:
            collection: Collection Blender où ajouter les objets
            floor_height: Hauteur par défaut si non spécifiée

        Returns:
            Liste des objets créés
        """
        partition_objects = []

        for i, partition in enumerate(self.partitions):
            partition_type = partition['type']
            height = partition.get('height', floor_height)

            bm = bmesh.new()

            try:
                if partition_type == 'vertical':
                    # Cloison verticale (direction Y)
                    x = partition['x']
                    y_start = partition['y_start']
                    y_end = partition['y_end']
                    length = y_end - y_start

                    # Créer un plan vertical
                    verts = [
                        bm.verts.new(Vector((x - self.wall_thickness/2, y_start, 0))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, y_start, 0))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, y_end, 0))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, y_end, 0))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, y_start, height))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, y_start, height))),
                        bm.verts.new(Vector((x + self.wall_thickness/2, y_end, height))),
                        bm.verts.new(Vector((x - self.wall_thickness/2, y_end, height))),
                    ]

                elif partition_type == 'horizontal':
                    # Cloison horizontale (direction X)
                    y = partition['y']
                    x_start = partition['x_start']
                    x_end = partition['x_end']
                    width = x_end - x_start

                    # Créer un plan horizontal
                    verts = [
                        bm.verts.new(Vector((x_start, y - self.wall_thickness/2, 0))),
                        bm.verts.new(Vector((x_end, y - self.wall_thickness/2, 0))),
                        bm.verts.new(Vector((x_end, y + self.wall_thickness/2, 0))),
                        bm.verts.new(Vector((x_start, y + self.wall_thickness/2, 0))),
                        bm.verts.new(Vector((x_start, y - self.wall_thickness/2, height))),
                        bm.verts.new(Vector((x_end, y - self.wall_thickness/2, height))),
                        bm.verts.new(Vector((x_end, y + self.wall_thickness/2, height))),
                        bm.verts.new(Vector((x_start, y + self.wall_thickness/2, height))),
                    ]
                else:
                    print(f"[RoomLayout] Type cloison inconnu: {partition_type}")
                    continue

                bm.verts.ensure_lookup_table()

                # Créer les faces
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

                # Créer le mesh
                mesh = bpy.data.meshes.new(f"Partition_{i}")
                bm.to_mesh(mesh)
                bm.free()

                # Créer l'objet
                obj = bpy.data.objects.new(f"Partition_{partition.get('room', 'wall')}_{i}", mesh)
                obj["house_part"] = "partition"
                obj["room"] = partition.get('room', 'unknown')
                collection.objects.link(obj)
                partition_objects.append(obj)

            except Exception as e:
                print(f"[RoomLayout] Erreur création cloison {i}: {e}")
                bm.free()

        print(f"[RoomLayout] {len(partition_objects)} cloisons créées")
        return partition_objects
