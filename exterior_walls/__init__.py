"""
EXTERIOR WALLS - Finitions extérieures
========================================
Système de finitions pour les façades extérieures.

Types supportés:
- Crépi/Enduit (Gratté, Taloché, Ribbé, Écrasé, Projeté, Lisse)
- Bardage Bois (Horizontal, Vertical, Claire-voie, Clin)
  * Bois Naturel (Douglas, Mélèze, Cèdre, Pin, Chêne)
  * Bois Peint (12 couleurs scandinaves)
  * Shou Sugi Ban (bois brûlé japonais)
- Pierre de Parement (Assisé régulier, Irrégulier, Opus incertum, Moellons, Pierre sèche)
  * Calcaire, Calcaire Doré
  * Granit, Granit Rose
  * Grès, Ardoise, Meulière
  * Pierre de Taille
"""

from .crepi import ExteriorCrepi
from .bardage import ExteriorBardage
from .pierre_parement import ExteriorPierreParement

__all__ = [
    'ExteriorCrepi',
    'ExteriorBardage',
    'ExteriorPierreParement',
]
