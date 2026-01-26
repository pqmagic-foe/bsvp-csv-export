# -*- coding: utf-8 -*-
"""
Additional properties generator for JSON-LD export
Builds additionalProperty array from technical mask fields
"""

from .normalizer import parse_template
from .mapping_loader import load_mappings
from modules.logger import Logger


def generate_additional_properties(prod_fields, mapping):
    property_ids = mapping.get("additional_properties", [])
    logger = Logger()

    product_name = prod_fields.get("NAME", prod_fields.get("ARTNR", "Unknown"))
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
        label = prop_def.get("label")

        if not template or not label:
            skipped_missing_config += 1
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Property definition '{property_id}' missing value or label: {prop_def}")
            continue

        resolved_value = parse_template(template, prod_fields, log_field_name=f"property '{label}'")

        if resolved_value is None:
            skipped_empty_value += 1
            continue

        unit = prop_def.get("unit")
        if unit:
            value_to_use = resolved_value
            # Strip duplicate unit from value end
            if resolved_value.endswith(" " + unit):
                value_to_use = resolved_value[:-len(" " + unit)].strip()
                logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{label}' - removed duplicate unit from value: '{resolved_value}' -> '{value_to_use}'")
            elif resolved_value.endswith(unit):
                value_to_use = resolved_value[:-len(unit)].strip()
                logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{label}' - removed duplicate unit from value: '{resolved_value}' -> '{value_to_use}'")

            property_value = {
                "@type": "PropertyValue",
                "name": label,
                "value": value_to_use,
                "unitText": unit
            }
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{label}' = '{value_to_use}' (unit: '{unit}')")
        else:
            property_value = {
                "@type": "PropertyValue",
                "name": label,
                "value": resolved_value
            }
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Property '{label}' = '{resolved_value}'")

        additional_properties.append(property_value)

    logger.log(f"[JSON-LD] Product '{product_name}': Additional properties summary - Total: {total_properties}, Added: {len(additional_properties)}, Skipped (empty): {skipped_empty_value}, Skipped (config error): {skipped_missing_config}")

    return additional_properties if additional_properties else None
