# -*- coding: utf-8 -*-
"""Exportiert nur die zusätzlichen Produktkategorien (p_cat_add) als Shop-Import-CSV."""

from .base_exporter import BaseExporter
from modules.constants import BSVP_CORE_NAME, ARTICLE_NUMBER

ADDITIONAL_CATEGORY_PREFIX = "p_cat_add."

# Anzahl der p_cat_add Spalten in der CSV Datei. Produkte mit mehr zusätzlichen
# Kategorien werden übersprungen und im Log vermerkt, damit nichts unbemerkt
# verloren geht.
MAX_ADDITIONAL_CATEGORIES = 10

# Erste Spalte jeder Zeile; der Importer erkennt daran den Anfang eines
# Datensatzes (siehe xtcImport::get_line_content)
RECORD_MARKER = "XTSOL"

DEFAULT_ACTION = "update"


def additional_category_ids(prod_fields):
    """Liest p_cat_add.0, p_cat_add.1, ... nach Index sortiert aus."""
    category_ids = []
    for field_name, field_value in prod_fields.items():
        if not field_name.startswith(ADDITIONAL_CATEGORY_PREFIX):
            continue
        index = field_name[len(ADDITIONAL_CATEGORY_PREFIX):]
        if not index.isdigit():
            continue
        if not isinstance(field_value, str) or field_value.strip() == "":
            continue
        category_ids.append((int(index), field_value.strip()))
    return [category_id for index, category_id in sorted(category_ids)]


class BsvpCoreExporter(BaseExporter):
    def __init__(self, manufacturers):
        super().__init__(manufacturers)
        self.csv_separator = self.shop_csv_separator

    def name(self):
        return BSVP_CORE_NAME

    def header_fields(self):
        additional_category_fields = [
            ADDITIONAL_CATEGORY_PREFIX + str(index)
            for index in range(MAX_ADDITIONAL_CATEGORIES)
        ]
        return [RECORD_MARKER, "action", "p_model"] + additional_category_fields

    def skip_product(self, fields):
        skip_product, error_code = super().skip_product(fields)
        if error_code != None or skip_product:
            return skip_product, error_code

        # Produkte ohne zusätzliche Kategorien werden nicht exportiert, damit
        # der Import wirklich nur Kategorien anlegt
        return len(additional_category_ids(fields)) == 0, None

    def write_to_csv(self, parameters):
        prod_fields = parameters["fields"]
        manufacturer_name = parameters["manufacturer_name"]

        if not ARTICLE_NUMBER in prod_fields:
            return "KEINE_ARTIKELNUMMER"

        category_ids = additional_category_ids(prod_fields)
        if len(category_ids) > MAX_ADDITIONAL_CATEGORIES:
            return "ZU_VIELE_ZUSAETZLICHE_KATEGORIEN ({})".format(len(category_ids))

        csv_path = self.output_directory() + manufacturer_name + ".csv"
        self.maybe_create_csv(csv_path, self.header_fields())

        csv_row = [
            RECORD_MARKER,
            prod_fields.get("ACTION", DEFAULT_ACTION),
            prod_fields[ARTICLE_NUMBER]
        ]
        for index in range(MAX_ADDITIONAL_CATEGORIES):
            csv_row.append(category_ids[index] if index < len(category_ids) else None)
        return self.write_csv_row(csv_path, csv_row)
