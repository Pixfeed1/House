# 🏠 Installation Addon House sur Windows - GUIDE SIMPLE

## 📥 TÉLÉCHARGER L'ADDON

### Méthode 1: Télécharger ZIP depuis GitHub (Le plus simple)

1. **Aller sur GitHub**:
   ```
   https://github.com/Pixfeed1/House
   ```

2. **Sélectionner la branche**:
   - Cliquer sur le menu déroulant (par défaut "main")
   - Chercher: `claude/audit-system-analysis-01L2vNqbCURTqVnFbdy74gbs`
   - Cliquer dessus

3. **Télécharger**:
   - Cliquer sur bouton vert "Code"
   - Cliquer sur "Download ZIP"
   - Le fichier `House-claude-audit-system-analysis-01L2vNqbCURTqVnFbdy74gbs.zip` se télécharge

4. **Extraire**:
   - Aller dans Téléchargements
   - Clic droit sur le ZIP → Extraire tout...
   - Choisir: `C:\Users\maete\Downloads\House`

---

## 🔧 INSTALLER DANS BLENDER

### Étape 1: Supprimer l'ancienne version

1. Ouvrir Blender
2. `Edit` → `Preferences` → `Add-ons`
3. Dans la barre de recherche, taper: `House`
4. Si l'addon apparaît:
   - Décocher la case ☑ → ☐ (désactiver)
   - Cliquer sur le bouton **X** (Remove)
   - Confirmer la suppression

### Étape 2: Installer la nouvelle version

1. Toujours dans `Edit` → `Preferences` → `Add-ons`
2. Cliquer sur bouton **Install...** (en haut)
3. Naviguer vers: `C:\Users\maete\Downloads\House`
4. Sélectionner le fichier: `__init__.py`
5. Cliquer **Install Add-on**

### Étape 3: Activer l'addon

1. L'addon "House" apparaît dans la liste
2. Cocher la case ☐ → ☑
3. **IMPORTANT**: Fermer complètement Blender
4. Redémarrer Blender

---

## ✅ VÉRIFIER QUE ÇA MARCHE

### Test 1: Addon chargé correctement

1. Dans Blender, ouvrir la **Console Python**:
   - `Window` → `Toggle System Console` (console Windows)
   - Dans Blender: Workspace → Scripting
   - En bas: Console Python

2. Copier-coller ce code:

```python
import bpy
import os

# Vérifier addon
if "House" in bpy.context.preferences.addons:
    print("✅ Addon House activé")
    addon = bpy.context.preferences.addons["House"]
    addon_path = os.path.dirname(addon.module.__file__)
    print(f"📂 Chemin: {addon_path}")

    # Vérifier fix calc_normals
    gutter_file = os.path.join(addon_path, "gutters", "gutter_geometry.py")
    if os.path.exists(gutter_file):
        with open(gutter_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "mesh.calc_normals()" in content:
                print("❌ VIEILLE VERSION - calc_normals() présent")
            elif "mesh.update()" in content:
                print("✅ VERSION CORRECTE - mesh.update() utilisé")
else:
    print("❌ Addon House non activé")
```

**Résultat attendu**:
```
✅ Addon House activé
📂 Chemin: C:\Users\maete\Downloads\House
✅ VERSION CORRECTE - mesh.update() utilisé
```

### Test 2: Générer une maison

1. Supprimer le cube par défaut
2. `Add` → `Mesh` → `House`
3. Dans le panneau à droite:
   - Choisir "3D Brick" pour les murs
   - Cocher "Windows"
   - Cliquer **Generate House**

**Résultat attendu**: Maison générée SANS erreur calc_normals()

---

## 🚨 SI ÇA NE MARCHE TOUJOURS PAS

### Solution 1: Vider le cache Blender

1. Fermer complètement Blender
2. Aller dans:
   ```
   C:\Users\maete\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons
   ```
3. Supprimer le dossier `House` s'il existe
4. Redémarrer Blender
5. Réinstaller (voir Étape 2 ci-dessus)

### Solution 2: Vider __pycache__

1. Dans le dossier addon:
   ```
   C:\Users\maete\Downloads\House
   ```
2. Chercher tous les dossiers `__pycache__`
3. Les supprimer tous
4. Redémarrer Blender

### Solution 3: Script force reload

1. Dans Console Python Blender:

```python
import bpy
import sys

# Désactiver
try:
    bpy.ops.preferences.addon_disable(module="House")
except:
    pass

# Nettoyer modules
for name in list(sys.modules.keys()):
    if "House" in name or "house" in name:
        del sys.modules[name]

# Réactiver
bpy.ops.preferences.addon_enable(module="House")
print("✅ Rechargé")
```

---

## 📞 BESOIN D'AIDE?

Si après tout ça l'erreur persiste, exécutez le script de diagnostic:

```python
exec(open(r"C:\Users\maete\Downloads\House\DIAGNOSTIC_ADDON.py").read())
```

Et envoyez-moi la sortie complète.

---

## 🎯 RÉSUMÉ RAPIDE

1. ⬇️ Télécharger ZIP depuis GitHub (branche claude/audit-system...)
2. 📂 Extraire dans C:\Users\maete\Downloads\House
3. 🗑️ Supprimer ancien addon dans Blender
4. ➕ Installer nouveau (sélectionner __init__.py)
5. ✅ Activer addon
6. 🔄 Redémarrer Blender
7. 🏠 Générer maison de test

**Tout devrait fonctionner sans erreur calc_normals()!**

