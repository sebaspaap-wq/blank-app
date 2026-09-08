"""QUITTER — 90 dagen. Volgens schema.

Het complete bedrijfssysteem: merk, catalogus, afbouwschema's, rekenmodel,
regels en het AI-team dat er dagelijks mee werkt.
"""

from .brand import MERK, RODE_DRAAD
from .catalog import EXTRAS, PROGRAMMAS, product
from .taper import SCHEMAS

__version__ = "0.1.0"
__all__ = ["MERK", "RODE_DRAAD", "PROGRAMMAS", "EXTRAS", "product", "SCHEMAS"]
