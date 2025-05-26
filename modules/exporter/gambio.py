import json
from collections import OrderedDict
from .shop import ShopExporter, special_cases
from modules.constants import GAMBIO_NAME, SHOP_NAME, TECHDATA
from modules.formatter import format_field

category_prefix = "p_cat"
category_postfix = ".de"
main_category = category_prefix + category_postfix

def export_checkout_information(parameters):
    """Copies the value from p_shortdesc.de to p_checkout_information.de"""
    prod_fields = parameters["prod_fields"]
    return prod_fields.get("SHORTDESC", None)

# Gambio-specific special cases
gambio_special_cases = {
    "p_checkout_information.de": export_checkout_information
}

class GambioExporter(ShopExporter):
    def __init__(self, manufacturers):
        super().__init__(manufacturers, SHOP_NAME)
        gambio_config = self.configs_base_directory + self.name() + ".json"
        with open(gambio_config, "r", encoding="utf-8") as gambio_config_file:
            self.techdata_fields = json.load(gambio_config_file, object_pairs_hook=OrderedDict)

        # Combine Shop special_cases with Gambio special_cases
        self.combined_special_cases = {**special_cases, **gambio_special_cases}

        # Konfiguration des Exporters
        self.skipping_policy["delivery_status"] = False

    def name(self):
        return GAMBIO_NAME

    def header_fields(self, prod_fields, ilugg_fields):
        shop_header_fields = super().header_fields(prod_fields, ilugg_fields)
        header_fields = []
        for header_field in shop_header_fields:
            if header_field == "p_cat.0":
                header_fields.append(main_category)
            elif header_field.startswith(category_prefix):
                header_fields.append(header_field.replace(".", "") + category_postfix)
            else:
                header_fields.append(header_field)

        # Add Gambio-specific fields
        gambio_fields = list(gambio_special_cases.keys())
        header_fields.extend(gambio_fields)
        
        header_fields = header_fields + list(self.techdata_fields.values())
        return header_fields

    def extract_information(self, prod_fields, ilugg_fields, attribute_names, attribute_types):
        row = super().extract_information(prod_fields, ilugg_fields, attribute_names, attribute_types)
        # Fasse Werte von p_cat.x in p_cat.0 zusammen
        # Lasse die übrigen p_cat Felder leer
        header_fields = self.header_fields(prod_fields, ilugg_fields)
        main_category_index = None
        other_category_indices = []
        category_values = []
        current_field_index = 0
        for header_field in header_fields:
            if header_field.startswith(category_prefix):
                category_value = row[current_field_index]
                if category_value != "":
                    category_values.append(category_value)
                if header_field == main_category:
                    main_category_index = current_field_index
                else:
                    other_category_indices.append(current_field_index)
            current_field_index = current_field_index + 1
        row[main_category_index] = " > ".join(category_values)
        for other_category_index in other_category_indices:
            row[other_category_index] = None

        # Add Gambio-specific fields
        for field_name in gambio_special_cases.keys():
            parameters = {
                "prod_fields": prod_fields,
                "ilugg_fields": ilugg_fields,
                "attribute_names": attribute_names,
                "attribute_types": attribute_types,
                "tooltips": self.tooltips,
                "specification": {}
            }
            value = gambio_special_cases[field_name](parameters)
            row.append(value)

        # Füge TECHDATA Felder hinter Shop Feldern an
        for techdata_field in self.techdata_fields.keys():
            value = None
            if TECHDATA in prod_fields:
                techdata = prod_fields[TECHDATA]
                if techdata_field in techdata:
                    value = format_field(techdata[techdata_field], techdata_field)
            row.append(value)
        return row
