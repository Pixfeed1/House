"""
FORCE RELOAD - Nettoie TOUT et recharge l'addon House
À exécuter dans Blender Console Python
"""

import bpy
import sys
import importlib

print("\n" + "="*70)
print("FORCE RELOAD ADDON HOUSE")
print("="*70)

# 1. DÉSACTIVER L'ADDON
print("\n[1/5] Désactivation addon...")
try:
    bpy.ops.preferences.addon_disable(module="House")
    print("     ✅ Addon désactivé")
except Exception as e:
    print(f"     ⚠️ {e}")

# 2. NETTOYER TOUS LES MODULES
print("\n[2/5] Nettoyage modules Python...")
modules_to_remove = []
for module_name in list(sys.modules.keys()):
    if 'House' in module_name or 'house' in module_name:
        modules_to_remove.append(module_name)

for module_name in modules_to_remove:
    try:
        del sys.modules[module_name]
        print(f"     ✅ Supprimé: {module_name}")
    except:
        pass

print(f"     Total: {len(modules_to_remove)} modules nettoyés")

# 3. NETTOYER LE CACHE importlib
print("\n[3/5] Nettoyage cache importlib...")
try:
    importlib.invalidate_caches()
    print("     ✅ Cache invalidé")
except Exception as e:
    print(f"     ⚠️ {e}")

# 4. RÉACTIVER L'ADDON
print("\n[4/5] Réactivation addon...")
try:
    bpy.ops.preferences.addon_enable(module="House")
    print("     ✅ Addon réactivé")
except Exception as e:
    print(f"     ❌ ERREUR: {e}")
    print("\n⚠️ SOLUTION:")
    print("   1. Edit → Preferences → Add-ons")
    print("   2. Chercher 'House'")
    print("   3. Cliquer sur 'Remove' (bouton X)")
    print("   4. Cliquer sur 'Install...'")
    print("   5. Sélectionner: /home/user/House/__init__.py")

# 5. VÉRIFIER LA VERSION
print("\n[5/5] Vérification version...")
try:
    import os
    addon_path = None
    for addon in bpy.context.preferences.addons:
        if "House" in addon.module:
            addon_path = os.path.dirname(addon.module.__file__)
            break

    if addon_path:
        print(f"     📂 Chemin addon: {addon_path}")

        gutter_file = os.path.join(addon_path, "gutters", "gutter_geometry.py")
        if os.path.exists(gutter_file):
            with open(gutter_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "mesh.calc_normals()" in content:
                    print("     ❌ VIEILLE VERSION! contient calc_normals()")
                elif "mesh.update()" in content:
                    print("     ✅ VERSION CORRECTE (mesh.update)")
                else:
                    print("     ⚠️ Version inconnue")
    else:
        print("     ❌ Addon non trouvé")

except Exception as e:
    print(f"     ❌ Erreur: {e}")

print("\n" + "="*70)
print("✅ TERMINÉ - Essayez de générer une maison maintenant")
print("="*70 + "\n")
