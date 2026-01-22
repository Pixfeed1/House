"""
DIAGNOSTIC - Vérifier que l'addon House est bien chargé avec la version corrigée
Exécuter dans la console Python de Blender
"""

import bpy
import sys
import os

print("=" * 60)
print("DIAGNOSTIC ADDON HOUSE")
print("=" * 60)

# 1. Vérifier que l'addon est chargé
if "House" in bpy.context.preferences.addons:
    print("✅ Addon House est activé")
    addon_path = bpy.context.preferences.addons["House"].module.__file__
    print(f"📂 Chemin: {os.path.dirname(addon_path)}")
else:
    print("❌ Addon House N'EST PAS activé!")

# 2. Vérifier la version du fichier gutters/gutter_geometry.py
try:
    house_path = None
    for addon in bpy.context.preferences.addons:
        if "House" in addon.module:
            house_path = os.path.dirname(addon.module.__file__)
            break

    if house_path:
        gutter_file = os.path.join(house_path, "gutters", "gutter_geometry.py")
        if os.path.exists(gutter_file):
            with open(gutter_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "mesh.calc_normals()" in content:
                    print("❌ PROBLÈME TROUVÉ: gutters/gutter_geometry.py contient encore mesh.calc_normals()")
                    print("   → Le fichier N'A PAS été mis à jour!")
                elif "mesh.update()" in content:
                    print("✅ gutters/gutter_geometry.py est à jour (utilise mesh.update())")
                else:
                    print("⚠️ gutters/gutter_geometry.py ne contient ni calc_normals ni mesh.update")
        else:
            print(f"❌ Fichier non trouvé: {gutter_file}")
    else:
        print("❌ Impossible de trouver le chemin de l'addon")

except Exception as e:
    print(f"❌ Erreur diagnostic: {e}")

# 3. Vérifier les modules chargés
print("\n📦 Modules House chargés:")
for module_name in sorted(sys.modules.keys()):
    if "House" in module_name or "house" in module_name:
        print(f"  - {module_name}")

print("\n" + "=" * 60)
print("FIN DIAGNOSTIC")
print("=" * 60)
