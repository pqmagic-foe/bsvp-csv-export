# -*- coding: utf-8 -*-
"""Shop exporter with JSON-LD structured data support."""

from .shop import ShopExporter
from .shop.jsonld import export_jsonld
from modules.constants import SHOP_JSONLD_NAME


jsonld_special_cases = {
    "products_jsonld_extra": export_jsonld
}


def jsonld_special_case_names():
    return list(jsonld_special_cases.keys())


class ShopJsonLDExporter(ShopExporter):

    def __init__(self, manufacturers):
        super().__init__(manufacturers, SHOP_JSONLD_NAME)
        self.special_cases.update(jsonld_special_cases)

    def name(self):
        return SHOP_JSONLD_NAME
