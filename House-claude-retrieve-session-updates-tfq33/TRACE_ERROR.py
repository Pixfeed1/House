"""
TRACE COMPLÈTE DE L'ERREUR calc_normals()
À exécuter dans Blender AVANT de générer une maison
"""

import bpy
import sys
import traceback
import os

print("\n" + "="*80)
print("TRACE COMPLÈTE - LOCALISATION ADDON HOUSE")
print("="*80)

# 1. TROUVER D'OÙ BLENDER CHARGE LE MODULE
print("\n[1] Chemins d'import Python:")
for i, path in enumerate(sys.path):
    if "House" in path or "addon" in path.lower() or "blender" in path.lower():
        print(f"  {i}. {path}")

# 2. TROUVER LE MODULE HOUSE
print("\n[2] Module House chargé:")
house_module = None
for module_name, module in sys.modules.items():
    if module_name == "House" or module_name.startswith("House."):
        if hasattr(module, "__file__"):
            print(f"  {module_name}: {module.__file__}")
            if module_name == "House":
                house_module = module

# 3. VÉRIFIER LE CHEMIN DU MODULE HOUSE
if house_module and hasattr(house_module, "__file__"):
    house_path = os.path.dirname(house_module.__file__)
    print(f"\n[3] Addon House chargé depuis:")
    print(f"  📂 {house_path}")

    # Vérifier gutter_geometry.py
    gutter_file = os.path.join(house_path, "gutters", "gutter_geometry.py")
    if os.path.exists(gutter_file):
        print(f"\n[4] Contenu gutters/gutter_geometry.py:")
        with open(gutter_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i, line in enumerate(lines, 1):
                if "calc_normals" in line.lower() or "mesh.update" in line.lower():
                    print(f"  Ligne {i}: {line.rstrip()}")
    else:
        print(f"\n[4] ❌ gutters/gutter_geometry.py N'EXISTE PAS!")
        print(f"  Cherché ici: {gutter_file}")
else:
    print("\n[3] ❌ Module House non trouvé dans sys.modules")

# 4. ACTIVER LE MODE TRACEBACK COMPLET
print("\n[5] Installation gestionnaire d'erreurs personnalisé...")

original_excepthook = sys.excepthook

def custom_excepthook(exc_type, exc_value, exc_traceback):
    """Capture TOUTES les erreurs avec traceback complet"""
    if "calc_normals" in str(exc_value):
        print("\n" + "!"*80)
        print("!!! ERREUR calc_normals() DÉTECTÉE !!!")
        print("!"*80)
        print("\nTRACEBACK COMPLET:")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
        print("\nFICHIER EXACT:")
        for frame_summary in traceback.extract_tb(exc_traceback):
            if "calc_normals" in frame_summary.line:
                print(f"  📁 Fichier: {frame_summary.filename}")
                print(f"  📍 Ligne: {frame_summary.lineno}")
                print(f"  🔧 Fonction: {frame_summary.name}")
                print(f"  💻 Code: {frame_summary.line}")
        print("!"*80 + "\n")

    # Appeler le handler original
    original_excepthook(exc_type, exc_value, exc_traceback)

sys.excepthook = custom_excepthook

print("  ✅ Gestionnaire installé!")
print("\n" + "="*80)
print("✅ PRÊT - Générez une maison maintenant")
print("   L'erreur sera tracée avec le fichier exact!")
print("="*80 + "\n")
