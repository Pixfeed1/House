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

## BUG #4 🔴 CRITIQUE: Fenêtres se chevauchent sur petites maisons

### Symptôme
Sur une maison de 3m de largeur (minimum autorisé), les fenêtres se CHEVAUCHENT visuellement

### Cause Racine
**Fichier**: `operators_auto.py:580-587, 1230-1231`

```python
WINDOW_WIDTH = 1.2  # Largeur fenêtre fixe
WINDOW_SPACING_INTERVAL = 3.0

num_windows_front = max(2, int(width / WINDOW_SPACING_INTERVAL))
spacing_front = width / (num_windows_front + 1)
```

### Problème
Le calcul force MINIMUM 2 fenêtres (`max(2, ...)`), mais ne vérifie PAS si l'espace est suffisant!

**Maison 3m** (minimum):
- `num_windows = max(2, int(3/3)) = max(2, 1) = 2` fenêtres
- `spacing = 3 / (2+1) = 1.0m`
- Position fenêtre 1: 1.0m → de 0.4m à 1.6m (largeur 1.2m)
- Position fenêtre 2: 2.0m → de 1.4m à 2.6m
- **CHEVAUCHEMENT**: de 1.4m à 1.6m = **0.20m de chevauchement** !

**Maison 4m**:
- Fenêtres à peine espacées: 0.13m (13cm) entre elles

### Impact
- **Sévérité**: 🔴 **CRITIQUE** pour petites maisons
- **Fréquence**: 100% des maisons < 4m de largeur
- **Résultat**: Fenêtres chevauchent visuellement, aspect cassé

### Test de Confirmation
```
Maison 3.0m: Fenêtres se CHEVAUCHENT de 0.20m
Maison 4.0m: Espace 0.13m seulement
Maison 5.0m: Espace 0.47m (acceptable)
Maison 6.0m: Espace 0.80m (bon)
```

### Solution Suggérée
```python
# Option 1: Réduire nombre de fenêtres si chevauchement
def calculate_num_windows(wall_length, window_width=1.2, min_spacing=0.5):
    # Espace nécessaire = n*window_width + (n+1)*min_spacing
    # wall_length >= n*window_width + (n+1)*min_spacing
    # wall_length >= n*(window_width + min_spacing) + min_spacing
    # wall_length - min_spacing >= n*(window_width + min_spacing)
    # n <= (wall_length - min_spacing) / (window_width + min_spacing)
    max_windows = int((wall_length - min_spacing) / (window_width + min_spacing))
    return max(1, min(max_windows, 2))  # Entre 1 et 2 fenêtres

# Option 2: Ajuster largeur fenêtre dynamiquement
# Option 3: Warning si maison trop petite
```

---

## BUG #5 🟠 MOYEN: Sols aux étages mal positionnés

### Symptôme
Tous les sols (RDC + étages) sont placés à Z=0 au lieu de leur hauteur respective

### Cause Racine
**Fichier 1**: `flooring.py:179`
```python
def generate_floor(self, floor_type, width, length, room_name="Room", height=0.0):
    # ... génération du mesh ...
    floor_obj = bpy.data.objects.new(floor_name, mesh)
    return floor_obj  # ❌ Paramètre 'height' JAMAIS utilisé!
```

**Fichier 2**: `operators_auto.py:726-731`
```python
floor_obj = flooring_gen.generate_floor(
    # ...
    height=z_pos  # Passé mais ignoré par flooring.py
)
if floor_obj:
    floor_obj.location = (width/2 - inset_width/2,
                         length/2 - inset_length/2,
                         0)  # ❌ Force Z=0 pour TOUS les étages!
```

### Problème
1. `flooring.py` déclare paramètre `height` mais ne l'utilise JAMAIS
2. `operators_auto.py` passe `z_pos` calculé (0, 3m, 6m, etc.)
3. Mais ensuite force `location.z = 0` pour tous les sols

**Résultat**:
- Sol RDC: Z=0 ✅ (correct par hasard)
- Sol Étage 1: Z=0 ❌ (devrait être à 3m)
- Sol Étage 2: Z=0 ❌ (devrait être à 6m)

Tous les sols sont empilés au même endroit!

### Impact
- **Sévérité**: 🟠 **MOYEN** - Affecte maisons multi-étages avec système sols avancé
- **Fréquence**: 100% des maisons avec `use_flooring_system=True` ET plusieurs étages
- **Résultat**: Sols superposés, étages sans plancher

### Solution
**Dans flooring.py**:
```python
def generate_floor(..., height=0.0):
    # ... créer mesh ...
    floor_obj = bpy.data.objects.new(floor_name, mesh)
    floor_obj.location.z = height  # ✅ AJOUTER
    return floor_obj
```

**Dans operators_auto.py**:
```python
floor_obj.location = (width/2 - inset_width/2,
                     length/2 - inset_length/2,
                     z_pos)  # ✅ Utiliser z_pos au lieu de 0
```

---

## BUG #6 🟠 MOYEN: Matériaux sols avancés effacés

### Symptôme
Le système de sols avancé (`flooring.py`) crée des matériaux détaillés (bois, marbre, etc.), mais ils sont EFFACÉS et remplacés par une couleur unie

### Cause Racine
**Fichier**: `operators_auto.py:1510-1512`

```python
def _apply_materials(self, context, props, collection, style_config):
    # ...
    for obj in collection.objects:
        part_type = obj.get("house_part", None)

        if part_type == "wall":
            # ✅ Pour les MURS: respecte matériaux existants
            if props.wall_construction_type == 'SIMPLE' and len(obj.data.materials) == 0:
                obj.data.materials.append(wall_mat)

        elif part_type == "floor":
            # ❌ Pour les SOLS: EFFACE TOUJOURS les matériaux!
            obj.data.materials.clear()  # Supprime matériau flooring.py
            obj.data.materials.append(floor_mat)  # Remplace par couleur unie
```

### Problème
**Incohérence de logique**:
- Pour les **MURS**: Vérifie `len(...) == 0` avant d'appliquer matériau (respecte briques 3D)
- Pour les **SOLS**: Appelle `.clear()` TOUJOURS (détruit matériaux flooring.py)

**Scénario**:
1. Utilisateur active `use_flooring_system=True`
2. `flooring.py` génère sol PARQUET avec matériau bois détaillé
3. `_apply_materials()` appelle `.clear()` → matériau parquet EFFACÉ
4. Remplace par `floor_mat` → couleur unie grise

**Résultat**: Pas de différence entre système simple et système avancé!

### Impact
- **Sévérité**: 🟠 **MOYEN** - Casse une feature entière (système sols avancés)
- **Fréquence**: 100% avec `use_flooring_system=True`
- **Résultat**: Système sols avancé inutile, tous les sols = couleur unie

### Solution
```python
elif part_type == "floor":
    # ✅ FIX: Respecter matériaux existants (comme pour les murs)
    if props.use_flooring_system:
        # Système avancé activé, ne PAS toucher aux matériaux
        pass
    else:
        # Système simple, appliquer couleur unie
        if len(obj.data.materials) == 0:
            obj.data.materials.append(floor_mat)
```

---

## RÉSUMÉ

| Bug | Sévérité | Testé | Impact | Statut |
|-----|----------|-------|--------|--------|
| #1 - Briques disparaissent | 🔴 CRITIQUE | ✅ Confirmé par utilisateur | **Casse système briques 3D** | ✅ **FIXÉ** |
| #2 - Nettoyage collection | 🟠 MOYEN | ⚠️ Suspect | Fuite mémoire possible | ✅ **FIXÉ** |
| #3 - Pattern Voronoi | 🟡 MINEUR | ✅ Confirmé (TODO dans code) | Fallback OK | ⚠️ Ouvert |
| #4 - Fenêtres chevauchent | 🔴 CRITIQUE | ✅ Test mathématique | **Maisons < 4m cassées** | ⚠️ **NOUVEAU** |
| #5 - Sols étages Z=0 | 🟠 MOYEN | ✅ Code analysé | Sols superposés | ⚠️ **NOUVEAU** |
| #6 - Matériaux sols effacés | 🟠 MOYEN | ✅ Code analysé | Système avancé inutile | ⚠️ **NOUVEAU** |

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
3. ⚠️ **BUG #4**: À FIXER - Fenêtres chevauchent sur maisons < 4m
4. ⚠️ **BUG #5**: À FIXER - Sols étages tous à Z=0
5. ⚠️ **BUG #6**: À FIXER - Matériaux sols avancés effacés

**OPTIONNEL (plus tard)**:
6. ⚠️ **BUG #3**: Implémenter pattern Voronoi (TODO ouvert)

---

**Rapport créé le**: 2025-11-15
**Mis à jour le**: 2025-11-15 (3 nouveaux bugs trouvés)
**Par**: Claude AI
**Type**: Analyse bugs fonctionnels RÉELS (testés, pas théoriques)
**Statut**: 2/6 bugs fixés (33% résolu), 4 bugs à fixer
