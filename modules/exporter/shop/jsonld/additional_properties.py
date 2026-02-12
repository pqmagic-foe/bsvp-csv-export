# -*- coding: utf-8 -*-
"""
Additional properties generator for JSON-LD export
Builds additionalProperty array from technical mask fields
"""

from .normalizer import parse_template, get_product_name, strip_unit_suffix
from .mapping_loader import load_mappings
from modules.logger import Logger


def generate_additional_properties(prod_fields, mapping):
    property_ids = mapping.get("additional_properties", [])
    logger = Logger()

    product_name = get_product_name(prod_fields)
    total_properties = len(property_ids)
    logger.log(f"[JSON-LD] Product '{product_name}': Processing {total_properties} additional properties")

    mappings = load_mappings()
    property_definitions = mappings.get("property_definitions", {})

    additional_properties = []
    skipped_empty_value = 0
    skipped_missing_config = 0

    for property_id in property_ids:
        prop_def = property_definitions.get(property_id)

        if not prop_def:
            skipped_missing_config += 1
            #logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Property definition not found for ID: '{property_id}'")
            continue

        template = prop_def.get("value")
        name = prop_def.get("name")

        if not template or not name:
            skipped_missing_config += 1
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Property definition '{property_id}' missing value or name: {prop_def}")
            continue

        resolved_value = parse_template(template, prod_fields, log_field_name=f"property '{name}'")

        if resolved_value is None:
            skipped_empty_value += 1
            continue

        # Copy all keys from prop_def, then override value with resolved template
        property_value = {"@type": "PropertyValue"}
        property_value.update(prop_def)
        property_value["value"] = resolved_value

        # Strip duplicate unit from value end if unitText is present
        unit = prop_def.get("unitText")
        if unit:
            stripped_value, was_stripped = strip_unit_suffix(resolved_value, unit)
            if was_stripped:
                property_value["value"] = stripped_value
                logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{name}' - removed duplicate unit: '{resolved_value}' -> '{stripped_value}'")
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{name}' = '{property_value['value']}' (unit: '{unit}') (template: '{template}')")
        else:
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{name}' = '{resolved_value}' (template: '{template}')")

        additional_properties.append(property_value)

    logger.log(f"[JSON-LD] Product '{product_name}': Additional properties summary - Total: {total_properties}, Added: {len(additional_properties)}, Skipped (empty): {skipped_empty_value}, Skipped (config error): {skipped_missing_config}")

    return additional_properties if additional_properties else None
