# -*- coding: utf-8 -*-
"""Shop exporter with JSON-LD structured data support."""

from .shop import ShopExporter
from .shop.jsonld import export_jsonld
from modules.constants import SHOP_JSONLD_NAME


class ShopJsonLDExporter(ShopExporter):

    def __init__(self, manufacturers):
        super().__init__(manufacturers, "Shop + JSON-LD")
        self.special_cases["products_jsonld_extra"] = export_jsonld

    def name(self):
        return SHOP_JSONLD_NAME
