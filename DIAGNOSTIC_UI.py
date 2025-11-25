"""
Script de diagnostic pour vérifier l'enregistrement des panels UI
À exécuter dans la console Python de Blender
"""

import bpy

print("\n" + "="*70)
print("🔍 DIAGNOSTIC UI - HOUSE ADDON")
print("="*70)

# 1. Vérifier si l'addon est chargé
print("\n1️⃣ ADDON CHARGÉ:")
addon_loaded = False
for addon in bpy.context.preferences.addons:
    if 'House' in addon.module or 'house' in addon.module.lower():
        addon_loaded = True
        print(f"   ✅ Addon trouvé: {addon.module}")
        break
if not addon_loaded:
    print(f"   ❌ Addon 'House' NON chargé")

# 2. Vérifier si les propriétés sont enregistrées
print("\n2️⃣ PROPRIÉTÉS SCENE:")
has_props = hasattr(bpy.context.scene, 'house_generator')
print(f"   {'✅' if has_props else '❌'} scene.house_generator existe: {has_props}")

if has_props:
    props = bpy.context.scene.house_generator
    print(f"   ✅ use_interior_walls_system: {props.use_interior_walls_system}")
    print(f"   ✅ interior_wall_finish: {props.interior_wall_finish}")

# 3. Lister TOUS les panels House enregistrés
print("\n3️⃣ PANELS HOUSE ENREGISTRÉS:")
house_panels = []
for cls_name in dir(bpy.types):
    if cls_name.startswith('HOUSE_PT_'):
        cls = getattr(bpy.types, cls_name)
        if hasattr(cls, 'bl_label'):
            house_panels.append((cls_name, cls.bl_label))
            print(f"   ✅ {cls_name}: '{cls.bl_label}'")

if not house_panels:
    print("   ❌ AUCUN panel House trouvé!")

# 4. Vérifier spécifiquement le panel murs intérieurs
print("\n4️⃣ PANEL MURS INTÉRIEURS:")
has_interior_panel = hasattr(bpy.types, 'HOUSE_PT_interior_walls_panel')
print(f"   {'✅' if has_interior_panel else '❌'} HOUSE_PT_interior_walls_panel existe: {has_interior_panel}")

if has_interior_panel:
    panel = bpy.types.HOUSE_PT_interior_walls_panel
    print(f"   ✅ Label: '{panel.bl_label}'")
    print(f"   ✅ Category: '{panel.bl_category}'")
    print(f"   ✅ Parent: '{getattr(panel, 'bl_parent_id', 'None')}'")
    print(f"   ✅ Options: {getattr(panel, 'bl_options', set())}")

# 5. Vérifier les opérateurs House
print("\n5️⃣ OPÉRATEURS HOUSE ENREGISTRÉS:")
house_operators = []
for cls_name in dir(bpy.types):
    if cls_name.startswith('HOUSE_OT_'):
        house_operators.append(cls_name)
        print(f"   ✅ {cls_name}")

if not house_operators:
    print("   ❌ AUCUN opérateur House trouvé!")

# 6. Vérifier version Blender
print("\n6️⃣ INFORMATIONS BLENDER:")
print(f"   Blender version: {bpy.app.version_string}")
print(f"   Python version: {bpy.app.version[0]}.{bpy.app.version[1]}")

# 7. Vérifier chemin addon
print("\n7️⃣ CHEMINS ADDONS:")
import addon_utils
for mod in addon_utils.modules():
    addon_name = str(mod.bl_info.get('name', ''))
    if 'House' in addon_name or 'house' in addon_name.lower():
        print(f"   ✅ Addon trouvé: {addon_name}")
        print(f"   📂 Chemin: {mod.__file__}")
        print(f"   📦 Version: {mod.bl_info.get('version', 'N/A')}")

print("\n" + "="*70)
print("✅ DIAGNOSTIC TERMINÉ")
print("="*70)
print("\n💡 INSTRUCTIONS:")
print("   1. Ouvrez Blender")
print("   2. Ouvrez la vue 3D")
print("   3. Appuyez sur N pour ouvrir le sidebar")
print("   4. Cherchez l'onglet 'House'")
print("   5. Dans le panel principal, cherchez 'Murs intérieurs' (peut être fermé)")
print("\n")
