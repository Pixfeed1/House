"""
EXTERIOR WALLS - Finitions extérieures
========================================
Système de finitions pour les façades extérieures.

Types supportés:
- Crépi/Enduit (Gratté, Taloché, Ribbé, Écrasé, Projeté, Lisse)
"""

from .crepi import ExteriorCrepi

__all__ = [
    'ExteriorCrepi',
]
