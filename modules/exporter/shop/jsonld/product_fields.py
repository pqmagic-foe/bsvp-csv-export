# -*- coding: utf-8 -*-
"""
Generic field processor for JSON-LD export
Handles fields based on their type definition: simple, QuantitativeValue, etc.
"""

from .normalizer import parse_template, normalize_decimal, get_product_name
from modules.logger import Logger


def generate_product_fields(prod_fields, mapping):
    product_config = mapping.get("product", {})
    result = {}
    logger = Logger()

    product_name = get_product_name(prod_fields)
    logger.log(f"[JSON-LD] Product '{product_name}': Processing {len(product_config)} product field(s)")

    for field_name, field_config in product_config.items():
        if not isinstance(field_config, dict):
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Field '{field_name}' has invalid config (not a dict)")
            continue

        field_type = field_config.get("type", "simple")
        template = field_config.get("value")

        if not template:
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Field '{field_name}' has no value template")
            continue

        resolved_value = parse_template(template, prod_fields, log_field_name=f"field '{field_name}'")

        if resolved_value is None:
            continue

        if field_type == "simple":
            result[field_name] = str(resolved_value)
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Field '{field_name}' = '{resolved_value}'")
        else:
            # Structured type (QuantitativeValue, etc.): copy all config keys except "type" and "value"
            type_data = {"@type": field_type}
            for key, val in field_config.items():
                if key not in ("type", "value"):
                    type_data[key] = val

            # For QuantitativeValue, normalize to numeric
            if field_type == "QuantitativeValue":
                normalized_value = normalize_decimal(resolved_value, field_name=field_name)
                if not isinstance(normalized_value, (int, float)):
                    logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Field '{field_name}': Value '{resolved_value}' is not numeric")
                    continue
                type_data["value"] = normalized_value
            else:
                type_data["value"] = str(resolved_value)

            result[field_name] = type_data
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Field '{field_name}' (@type: {field_type}) = '{type_data['value']}'")

    if result:
        logger.log(f"[JSON-LD] Product '{product_name}': Added {len(result)} product field(s): {', '.join(result.keys())}")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': No product fields added")

    return result if result else None
