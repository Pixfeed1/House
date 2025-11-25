# 🔍 COMMENT TROUVER LE PANEL "MURS INTÉRIEURS"

## ❓ PROBLÈME

Vous ne voyez pas le panel "Murs intérieurs" dans le menu House de Blender.

## ✅ SOLUTION

Le panel **EXISTE** dans le code, mais il est **FERMÉ PAR DÉFAUT**.

---

## 📋 INSTRUCTIONS ÉTAPE PAR ÉTAPE

### Étape 1: Ouvrir Blender

Lancez Blender 4.2+

### Étape 2: Ouvrir le Sidebar

Dans la vue 3D, appuyez sur la touche **N** pour ouvrir le sidebar (panneau latéral droit)

```
┌─────────────────────────────────────┐
│         Vue 3D Blender              │
│                                     │
│                                     │  ← Appuyez sur N
│                                     │
│                         ┌───────────┤
│                         │  SIDEBAR  │
│                         │           │
│                         │  [House]  │ ← Cliquez ici
│                         │  Tool     │
│                         │  Item     │
│                         └───────────┤
└─────────────────────────────────────┘
```

### Étape 3: Onglet "House"

Dans le sidebar, cliquez sur l'onglet **"House"**

### Étape 4: Trouver le panel "Murs intérieurs"

Le panel "Murs intérieurs" est un **SOUS-PANEL** du panel principal. Il apparaît **APRÈS** le panel "House Generator".

**IMPORTANT**: Il est **FERMÉ PAR DÉFAUT** - vous devez cliquer sur le petit triangle ▶ pour l'ouvrir !

```
┌─────────────────────────────────────┐
│ House Generator          [▼]        │ ← Panel principal
├─────────────────────────────────────┤
│ Mode de génération                  │
│ ○ Automatique  ○ Manuel            │
│                                     │
│ [Générer la maison]                 │
├─────────────────────────────────────┤
│                                     │
│ ▶ Toit                             │ ← Sous-panel (fermé)
│                                     │
│ ▶ Fenêtres                         │ ← Sous-panel (fermé)
│                                     │
│ ▶ Portes                           │ ← Sous-panel (fermé)
│                                     │
│ ▶ Murs                             │ ← Sous-panel (fermé)
│                                     │
│ ▶ Sols                             │ ← Sous-panel (fermé)
│                                     │
│ ▶ Murs intérieurs          ← ICI ! │ ← CHERCHEZ CE PANEL
│                                     │
│ ▶ Matériaux                        │ ← Sous-panel (fermé)
│                                     │
└─────────────────────────────────────┘
```

### Étape 5: Ouvrir le panel "Murs intérieurs"

Cliquez sur le triangle **▶** à côté de "Murs intérieurs" pour l'ouvrir :

```
┌─────────────────────────────────────┐
│ ▼ Murs intérieurs          ← OUVERT│
├─────────────────────────────────────┤
│ ☐ Activer finitions intérieures     │ ← Cochez cette case
├─────────────────────────────────────┤
│                                     │
│ Finition murale                     │
│ ┌─────────────────────────────────┐ │
│ │ Peinture            [▼]         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ── Peinture ──────────────────────  │
│ Couleur:                            │
│ ┌─────────────────────────────────┐ │
│ │ Blanc cassé         [▼]         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Type de finition:                   │
│ ┌─────────────────────────────────┐ │
│ │ Satinée             [▼]         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ℹ️ Lessivable, polyvalent           │
│                                     │
│ Qualité géométrie                   │
│ ┌─────────────────────────────────┐ │
│ │ Moyenne             [▼]         │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## 🚨 SI VOUS NE VOYEZ TOUJOURS PAS LE PANEL

### Raison 1: Addon non installé

Vérifiez que l'addon est bien activé :
1. Edit → Preferences → Add-ons
2. Cherchez "House"
3. Cochez la case pour l'activer

### Raison 2: Ancienne version

L'addon doit être installé depuis la branche Git avec le commit `0af6910` ou plus récent.

**Vérifiez** :
```bash
cd /home/user/House
git log --oneline -1
```

Devrait afficher : `7083e5f Doc: Analyse UI incomplète - Options manquantes interface`

Si ce n'est pas le cas, faites :
```bash
git pull origin claude/audit-system-analysis-01L2vNqbCURTqVnFbdy74gbs
```

Puis **REDÉMARREZ BLENDER** complètement.

### Raison 3: Blender utilise une autre copie de l'addon

**Problème fréquent** : Blender peut avoir chargé l'addon depuis `AppData` (Windows) ou `~/.config/blender` (Linux) au lieu de votre dépôt Git.

**Solution Windows** :
```
C:\Users\VotreNom\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons\House
```
→ Supprimez ce dossier si il existe

**Solution Linux** :
```
~/.config/blender/4.2/scripts/addons/House
```
→ Supprimez ce dossier si il existe

Puis dans Blender :
1. Edit → Preferences → Add-ons
2. Désactivez "House"
3. Cliquez sur le bouton "Remove" (supprimer)
4. Redémarrez Blender
5. Edit → Preferences → Add-ons → Install
6. Naviguez vers `/home/user/House`
7. Sélectionnez `__init__.py`
8. Cliquez "Install Add-on"

---

## 🧪 SCRIPT DE DIAGNOSTIC

Pour vérifier si le panel est bien enregistré, exécutez ce script dans la console Python de Blender :

```python
# Copiez-collez ce code dans la console Python de Blender
exec(open("/home/user/House/DIAGNOSTIC_UI.py").read())
```

Ce script va afficher :
- ✅ Si l'addon est chargé
- ✅ Si les panels sont enregistrés
- ✅ Si le panel "Murs intérieurs" existe
- ✅ Le chemin de l'addon chargé

---

## 📊 STATUT DES OPTIONS

Une fois le panel ouvert, voici ce qui fonctionne :

| Type finition | Options affichées | Status |
|---------------|-------------------|--------|
| **Peinture** | Couleur + Type finition | ✅ COMPLET |
| **Papier peint** | Image + Type papier | ✅ COMPLET |
| **Bois** | _Aucune option_ | ⚠️ "À venir" |
| **Brique apparente** | _Aucune option_ | ⚠️ "À venir" |
| **Pierre naturelle** | _Aucune option_ | ⚠️ "À venir" |
| **Enduit** | _Aucune option_ | ⚠️ "À venir" |

**Seules PEINTURE et PAPIER PEINT ont des options réelles.**

Les autres types affichent juste "À venir dans prochaine version".

---

## ✅ RÉSUMÉ

1. **Le panel existe** dans le code (ligne 541 de ui_panels.py)
2. **Il est fermé par défaut** - cherchez le triangle ▶
3. **C'est un sous-panel** - il apparaît sous "House Generator"
4. **Seules 2 finitions fonctionnent** : Peinture et Papier peint

Si après tout ça vous ne le voyez toujours pas, **exécutez le script DIAGNOSTIC_UI.py** et envoyez-moi le résultat !

---

**Document créé le** : 2025-11-25
**Branche Git** : claude/audit-system-analysis-01L2vNqbCURTqVnFbdy74gbs
**Commit** : 7083e5f
