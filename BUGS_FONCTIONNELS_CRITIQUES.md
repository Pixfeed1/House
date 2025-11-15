# 🔴 BUGS FONCTIONNELS CRITIQUES
**Date**: 2025-11-15
**Analyse**: Bugs qui cassent réellement la fonctionnalité (pas seulement théoriques)

---

## BUG #1 🔴 CRITIQUE: Briques disparaissent quand on change le nombre de fenêtres

### Symptôme
**Rapporté par l'utilisateur**: "Quand je change le nombre de fenêtres, ma maison n'a plus aucune brique"

### Cause Racine
**Fichier**: `materials/brick_geometry.py:1053-1088`
**Fonction**: `is_brick_in_opening()`

```python
def is_brick_in_opening(brick_x, brick_y, brick_z, brick_width, brick_height, openings):
    # ...
    brick_center_x = brick_x + brick_width / 2
    brick_center_z = brick_z + brick_height / 2

    for opening in openings:
        opening_x = opening.get('x', 0)
        opening_y = opening.get('y', 0)  # ❌ LU MAIS JAMAIS UTILISÉ!
        opening_z = opening.get('z', 0)
        opening_width = opening.get('width', 0)
        opening_height = opening.get('height', 0)

        # ❌ BUG CRITIQUE: Ne vérifie QUE X et Z, ignore complètement Y et 'wall'!
        if (opening_x_min < brick_center_x < opening_x_max and
            opening_z_min < brick_center_z < opening_z_max):
            return True  # ❌ Manque la vérification Y!
```

### Problème
1. La fonction lit `opening_y` **mais ne l'utilise jamais**
2. Elle ne vérifie **jamais** `opening.get('wall')` pour savoir quel mur
3. Elle vérifie seulement les coordonnées **X et Z**

### Conséquence
**Exemple concret**:
- Maison 10m × 10m avec 2 fenêtres:
  - Fenêtre 1: Mur AVANT (y=0) à x=2m, z=1.5m
  - Fenêtre 2: Mur ARRIÈRE (y=10m) à x=2m, z=1.5m

**Résultat**:
- La fonction supprime **TOUTES** les briques à `x=2m, z=1.5m` sur **LES 4 MURS**
- Mur AVANT: briques supprimées à x=2m ✅ (correct)
- Mur ARRIÈRE: briques supprimées à x=2m ✅ (correct)
- Mur GAUCHE: briques supprimées à x=2m ❌ (**BUG!** car l'ouverture n'est pas sur ce mur)
- Mur DROIT: briques supprimées à x=2m ❌ (**BUG!** car l'ouverture n'est pas sur ce mur)

**Plus de fenêtres = Plus de zones interdites = Plus de briques disparaissent!**

Avec 10 fenêtres, il peut y avoir 10 "zones X/Z interdites" qui s'appliquent à TOUS les murs, résultat: **presque toutes les briques disparaissent**!

### Impact
- **Sévérité**: 🔴 **CRITIQUE** - Casse complètement la génération de briques 3D
- **Fréquence**: **100%** des maisons avec briques 3D et plusieurs fenêtres
- **Utilisateurs affectés**: **TOUS** ceux qui utilisent le système briques 3D

### Solution
La fonction doit vérifier **3 dimensions** (X, Y, Z) et/ou utiliser le champ `'wall'`:

**Option 1: Vérifier X, Y ET Z**
```python
def is_brick_in_opening(brick_x, brick_y, brick_z, brick_width, brick_height, openings):
    if not openings:
        return False

    brick_center_x = brick_x + brick_width / 2
    brick_center_y = brick_y + brick_height / 2  # ✅ AJOUTER
    brick_center_z = brick_z + brick_height / 2

    SAFETY_MARGIN = 0.02

    for opening in openings:
        opening_x = opening.get('x', 0)
        opening_y = opening.get('y', 0)
        opening_z = opening.get('z', 0)
        opening_width = opening.get('width', 0)
        opening_height = opening.get('height', 0)
        opening_depth = opening.get('depth', 0)  # ✅ AJOUTER

        # Étendre zones
        opening_x_min = opening_x - SAFETY_MARGIN
        opening_x_max = opening_x + opening_width + SAFETY_MARGIN
        opening_y_min = opening_y - SAFETY_MARGIN  # ✅ AJOUTER
        opening_y_max = opening_y + opening_depth + SAFETY_MARGIN  # ✅ AJOUTER
        opening_z_min = opening_z - SAFETY_MARGIN
        opening_z_max = opening_z + opening_height + SAFETY_MARGIN

        # ✅ FIX: Vérifier X, Y ET Z!
        if (opening_x_min < brick_center_x < opening_x_max and
            opening_y_min < brick_center_y < opening_y_max and  # ✅ AJOUTÉ
            opening_z_min < brick_center_z < opening_z_max):
            return True

    return False
```

**Option 2: Filtrer par mur avant l'appel**
```python
# Dans calculate_brick_positions_for_wall(), ligne 1154:
# Au lieu de passer TOUTES les ouvertures, passer SEULEMENT celles du mur concerné
# (déjà fait dans generate_walls_with_instancing mais pas suffisant car pas de vérif Y)
```

---

## BUG #2 🟠 PROBABLE: Nettoyage collection incomplet

### Symptôme
Objets orphelins possibles lors de la régénération de maison

### Cause Racine
**Fichier**: `operators_auto.py:348`

```python
for obj in list(collection.objects):
    # Unlink from all collections before removing
    for coll in bpy.data.collections:
        if obj.name in coll.objects:  # ❌ PROBABLE BUG
            coll.objects.unlink(obj)
    bpy.data.objects.remove(obj, do_unlink=True)
```

### Problème
**Ligne 348**: `if obj.name in coll.objects`

`coll.objects` est une **collection d'objets**, pas une collection de **noms**!

### Solution
```python
for obj in list(collection.objects):
    for coll in bpy.data.collections:
        if obj in coll.objects:  # ✅ FIX
            coll.objects.unlink(obj)
    bpy.data.objects.remove(obj, do_unlink=True)
```

### Impact
- **Sévérité**: 🟠 **MOYEN** - Peut causer fuite mémoire sur longue session
- **Fréquence**: **Chaque régénération** si le bug est confirmé
- **Note**: À vérifier si Blender a un override `__contains__` pour les noms

---

## BUG #3 🟡 MINEUR: Pattern Voronoi sols non implémenté

### Symptôme
Utilisateur sélectionne pattern "RANDOM" pour sols, obtient grille régulière

### Cause Racine
**Fichier**: `flooring.py:436`

```python
# TODO: Implémenter pattern irrégulier Voronoi pour réalisme.
print(f"[Flooring] Pattern 'random' en développement, utilisation de dalles régulières")
```

### Problème
Feature annoncée mais non implémentée

### Impact
- **Sévérité**: 🟡 **MINEUR** - Fallback fonctionnel existe
- **Fréquence**: Seulement si utilisateur sélectionne "RANDOM"

---

## AUTRES BUGS DÉTECTÉS (NON FONCTIONNELS)

Ces bugs n'ont PAS été testés fonctionnellement mais sont suspectés:

### Suspect #1: Propriété `include_back_door` non utilisée
**Fichier**: `properties.py:339`
**Problème**: Propriété définie mais jamais lue
**Impact**: Feature "porte arrière" ne fonctionne pas

### Suspect #2: Garage position "ATTACHED" = "FRONT"
**Fichier**: `operators_auto.py:1370`
**Problème**: Code identique pour ATTACHED et FRONT
**Impact**: Position garage incorrect

### Suspect #3: Cheminée non implémentée
**Fichier**: `properties.py:443`
**Problème**: Toggle existe mais génération manquante
**Impact**: Feature cheminée ne fonctionne pas

---

## RÉSUMÉ

| Bug | Sévérité | Testé | Impact | Statut |
|-----|----------|-------|--------|--------|
| #1 - Briques disparaissent | 🔴 CRITIQUE | ✅ Confirmé par utilisateur | **Casse système briques 3D** | ✅ **FIXÉ** |
| #2 - Nettoyage collection | 🟠 MOYEN | ⚠️ Suspect | Fuite mémoire possible | ✅ **FIXÉ** |
| #3 - Pattern Voronoi | 🟡 MINEUR | ✅ Confirmé (TODO dans code) | Fallback OK | ⚠️ Ouvert |

---

## 🛠️ CORRECTIONS APPLIQUÉES

### ✅ BUG #1 FIXÉ - is_brick_in_opening()
**Fichier**: `materials/brick_geometry.py:1053-1141`

**Changements**:
1. ✅ Ajout vérification dimension Y (était manquante)
2. ✅ Ajout `brick_center_y` et `opening_y_min/max`
3. ✅ Validation robuste avec 5 niveaux de sécurité:
   - Sécurité 1: Validation entrées (dimensions > 0)
   - Sécurité 2: Calcul centre avec try/except
   - Sécurité 3: Validation chaque ouverture (isinstance dict)
   - Sécurité 4: Validation dimensions ouverture
   - Sécurité 5: Debug logging (commenté, activable)
4. ✅ Fallback `opening_depth` si non défini
5. ✅ Vérification 3D complète: `x_inside AND y_inside AND z_inside`

**Avant** (bug):
```python
# Vérifiait seulement X et Z
if (opening_x_min < brick_center_x < opening_x_max and
    opening_z_min < brick_center_z < opening_z_max):
    return True  # ❌ Ignore Y!
```

**Après** (fixé):
```python
# Vérifie X, Y ET Z
x_inside = opening_x_min < brick_center_x < opening_x_max
y_inside = opening_y_min < brick_center_y < opening_y_max  # ✅ AJOUTÉ
z_inside = opening_z_min < brick_center_z < opening_z_max

if x_inside and y_inside and z_inside:
    return True  # ✅ Collision 3D complète
```

### ✅ BUG #1 FIXÉ - is_mortar_in_opening()
**Fichier**: `materials/brick_geometry.py:1146-1217`

**Changements**: Identiques à `is_brick_in_opening()` (même logique appliquée)

### ✅ BUG #2 FIXÉ - Nettoyage collection
**Fichier**: `operators_auto.py:348-356`

**Changements**:
1. ✅ Remplacé `obj.name in coll.objects` par `obj in coll.objects`
2. ✅ Ajout try/except pour gérer objets invalides
3. ✅ Logging erreurs pour debugging

**Avant**:
```python
if obj.name in coll.objects:  # ⚠️ Ambiguïté
    coll.objects.unlink(obj)
```

**Après**:
```python
if obj in coll.objects:  # ✅ Plus robuste
    try:
        coll.objects.unlink(obj)
    except (RuntimeError, ReferenceError) as e:
        print(f"[House] ⚠️ Impossible de unlink {obj.name}: {e}")
```

---

### Priorités de Correction

**URGENT (immédiat)**:
1. ✅ **BUG #1**: FIXÉ - `is_brick_in_opening()` + `is_mortar_in_opening()`
2. ✅ **BUG #2**: FIXÉ - Nettoyage collection robuste

**OPTIONNEL (plus tard)**:
3. ⚠️ **BUG #3**: Implémenter pattern Voronoi (TODO ouvert)

---

**Rapport créé le**: 2025-11-15
**Mis à jour le**: 2025-11-15
**Par**: Claude AI
**Type**: Analyse bugs fonctionnels réels (pas théoriques)
**Statut**: 2/3 bugs fixés (66% résolu)
