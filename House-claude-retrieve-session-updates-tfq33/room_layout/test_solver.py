#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le système room_layout.
Peut être exécuté en dehors de Blender pour valider le solver.

Usage:
    python test_solver.py
"""

import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from room_layout import (
    RoomLayoutManager,
    ROOM_TYPES,
    HOUSING_PRESETS,
    SolverConfig,
    generate_floor_plan,
    Rectangle,
)


def print_separator(title=""):
    """Affiche un séparateur."""
    print("\n" + "=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)


def test_room_types():
    """Teste les définitions des types de pièces."""
    print_separator("TEST: Définitions des pièces")

    print(f"Nombre de types de pièces: {len(ROOM_TYPES)}")

    for room_id, room_def in ROOM_TYPES.items():
        window_str = "🪟" if room_def.requires_window else "  "
        print(f"  {window_str} {room_def.name:20} | {room_def.area_min:4.1f} - {room_def.area_default:5.1f} - {room_def.area_max:5.1f} m²")

    # Vérifier les adjacences
    print("\nTest adjacences Salon-Cuisine:", end=" ")
    from room_layout.room_types import calculate_adjacency_score
    score = calculate_adjacency_score('SALON', 'CUISINE')
    print(f"score = {score} (attendu: 6)")

    print("Test adjacences Cuisine-WC:", end=" ")
    score = calculate_adjacency_score('CUISINE', 'WC')
    print(f"score = {score} (attendu: -4)")

    return True


def test_presets():
    """Teste les presets de logements."""
    print_separator("TEST: Presets de logements")

    print(f"Nombre de presets: {len(HOUSING_PRESETS)}")

    for preset_id, preset in HOUSING_PRESETS.items():
        rooms_list = preset.get_rooms_list()
        total_area = sum(area for _, area in rooms_list)

        print(f"\n  {preset.name}")
        print(f"    Description: {preset.description}")
        print(f"    Surface recommandée: {preset.area_recommended}m²")
        print(f"    Pièces: {len(rooms_list)} ({total_area:.0f}m² demandés)")

        for room_type, count, area in preset.rooms:
            room_def = ROOM_TYPES.get(room_type)
            name = room_def.name if room_def else room_type
            area_str = f"{area}m²" if area else "défaut"
            print(f"      - {count}x {name} ({area_str})")

    return True


def test_rectangle():
    """Teste les opérations géométriques."""
    print_separator("TEST: Géométrie Rectangle")

    r1 = Rectangle(0, 0, 10, 8)
    r2 = Rectangle(5, 0, 5, 8)

    print(f"R1: {r1}")
    print(f"R2: {r2}")
    print(f"R1 area: {r1.area}m²")
    print(f"R1 center: {r1.center}")
    print(f"R1 aspect ratio: {r1.aspect_ratio:.2f}")

    print(f"\nR1 intersects R2: {r1.intersects(r2)}")
    print(f"R1 touches R2: {r1.touches(r2)}")

    # Test subdivision
    left, right = r1.subdivide_vertical(0.4)
    print(f"\nSubdivision verticale 40%:")
    print(f"  Left: {left}")
    print(f"  Right: {right}")

    # Test shrink
    shrunk = r1.shrink(0.2)
    print(f"\nR1 shrunk by 0.2m: {shrunk}")

    return True


def test_solver_simple():
    """Teste le solver avec un cas simple."""
    print_separator("TEST: Solver Simple (T2)")

    # Configuration simple
    config = SolverConfig(
        wall_thickness=0.10,
        random_seed=42  # Pour reproductibilité
    )

    # Générer un T2 dans 8x10m
    result = generate_floor_plan(
        width=8.0,
        depth=10.0,
        preset_id='T2',
        config=config
    )

    print(f"Succès: {result.success}")
    print(f"Score: {result.score:.1f}")

    if result.messages:
        print("Messages:")
        for msg in result.messages:
            print(f"  - {msg}")

    if result.floor_plan:
        fp = result.floor_plan
        print(f"\nPlan généré: {fp}")
        print(f"Pièces placées: {len(fp.placed_rooms)}/{len(fp.rooms)}")

        print("\nDétail des pièces:")
        for room in fp.rooms:
            status = "✓" if room.is_placed else "✗"
            if room.bounds:
                print(f"  {status} {room.name:20} | {room.area:5.1f}m² @ ({room.bounds.x:.1f}, {room.bounds.y:.1f})")
            else:
                print(f"  {status} {room.name:20} | Non placée")

        # Score d'adjacence
        adj_score = fp.calculate_total_adjacency_score()
        print(f"\nScore d'adjacence total: {adj_score}")

        # Validation
        valid, messages = fp.validate()
        print(f"\nValidation: {'OK' if valid else 'ERREURS'}")
        for msg in messages:
            print(f"  - {msg}")

    return result.success


def test_solver_t4():
    """Teste le solver avec un T4 plus complexe."""
    print_separator("TEST: Solver T4")

    config = SolverConfig(random_seed=123)

    result = generate_floor_plan(
        width=12.0,
        depth=10.0,
        preset_id='T4',
        config=config
    )

    print(f"Succès: {result.success}")
    print(f"Score: {result.score:.1f}")

    if result.floor_plan:
        fp = result.floor_plan
        print(f"Pièces placées: {len(fp.placed_rooms)}/{len(fp.rooms)}")
        print(f"Portes générées: {len(fp.doors)}")

        for room in fp.placed_rooms:
            ext = room.bounds.get_exterior_walls(fp.bounds) if room.bounds else []
            ext_str = ", ".join(w.name for w in ext) if ext else "intérieur"
            print(f"  {room.name:20} | {room.area:5.1f}m² | {ext_str}")

    return result.success


def test_solver_custom():
    """Teste le solver avec une configuration personnalisée."""
    print_separator("TEST: Solver Personnalisé")

    custom_rooms = [
        ('SALON', 25.0),
        ('CUISINE', 12.0),
        ('CHAMBRE', 14.0),
        ('CHAMBRE', 12.0),
        ('SDB', 6.0),
        ('WC', 2.0),
        ('ENTREE', 4.0),
    ]

    config = SolverConfig(random_seed=456)

    result = generate_floor_plan(
        width=11.0,
        depth=9.0,
        preset_id='CUSTOM',
        custom_rooms=custom_rooms,
        config=config
    )

    print(f"Succès: {result.success}")

    if result.floor_plan:
        total_requested = sum(area for _, area in custom_rooms)
        total_placed = sum(r.area for r in result.floor_plan.placed_rooms)

        print(f"Surface demandée: {total_requested:.1f}m²")
        print(f"Surface placée: {total_placed:.1f}m²")
        print(f"Efficacité: {total_placed/total_requested*100:.1f}%")

    return result.success


def test_manager():
    """Teste le RoomLayoutManager."""
    print_separator("TEST: RoomLayoutManager")

    manager = RoomLayoutManager()

    # Test validation
    valid, messages = manager.validate_configuration(
        width=8.0,
        depth=6.0,
        preset_id='T4'
    )

    print(f"Validation T4 dans 8x6m: {'OK' if valid else 'ERREUR'}")
    for msg in messages:
        print(f"  - {msg}")

    # Test génération
    result = manager.generate_layout(
        width=12.0,
        depth=10.0,
        preset_id='T3'
    )

    print(f"\nGénération T3 dans 12x10m: {'Succès' if result.success else 'Échec'}")

    # Test partition data
    if result.success and result.floor_plan:
        partitions = manager.get_partition_data(result.floor_plan)
        print(f"Cloisons générées: {len(partitions)}")
        for p in partitions[:3]:  # Afficher les 3 premières
            print(f"  - {p['start']} → {p['end']}, {len(p['openings'])} ouvertures")

    return True


def test_edge_cases():
    """Teste les cas limites."""
    print_separator("TEST: Cas Limites")

    # Espace trop petit
    print("\n1. Espace trop petit (5x5m pour T4):")
    result = generate_floor_plan(5.0, 5.0, 'T4')
    print(f"   Succès: {result.success} (attendu: False)")
    if result.messages:
        print(f"   Message: {result.messages[0]}")

    # Pièces impossibles
    print("\n2. Trop de pièces nécessitant fenêtre (3x3m):")
    custom = [('CHAMBRE', 9.0), ('CHAMBRE', 9.0), ('CHAMBRE', 9.0), ('CHAMBRE', 9.0)]
    result = generate_floor_plan(6.0, 6.0, 'CUSTOM', custom)
    print(f"   Succès: {result.success}")

    # Grand espace
    print("\n3. Grand espace (20x15m pour T3):")
    result = generate_floor_plan(20.0, 15.0, 'T3')
    print(f"   Succès: {result.success}")
    if result.floor_plan:
        print(f"   Surface utilisée: {sum(r.area for r in result.floor_plan.placed_rooms):.1f}m²")

    return True


def main():
    """Point d'entrée principal."""
    print("\n" + "=" * 60)
    print("  TESTS DU SYSTÈME ROOM_LAYOUT")
    print("  (Exécution hors Blender)")
    print("=" * 60)

    all_passed = True

    try:
        all_passed &= test_room_types()
        all_passed &= test_presets()
        all_passed &= test_rectangle()
        all_passed &= test_solver_simple()
        all_passed &= test_solver_t4()
        all_passed &= test_solver_custom()
        all_passed &= test_manager()
        all_passed &= test_edge_cases()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    print_separator("RÉSULTAT")
    if all_passed:
        print("✅ Tous les tests passent!")
    else:
        print("❌ Certains tests ont échoué")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
