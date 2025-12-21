# -*- coding: utf-8 -*-
"""
Dimensions generator for JSON-LD export
Handles: width, depth, height, weight as QuantitativeValue structures
"""

from .normalizer import normalize_decimal, is_empty_value, parse_template
from modules.logger import Logger


def generate_dimensions(prod_fields, mapping):
    dimensions_config = mapping.get("dimensions", {})
    logger = Logger()

    product_name = prod_fields.get("NAME", prod_fields.get("ARTNR", "Unknown"))
    logger.log(f"[JSON-LD] Product '{product_name}': Processing {len(dimensions_config)} dimension(s)")

    result = {}

    for dimension_name, template in dimensions_config.items():
        if not template:
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Dimension '{dimension_name}' has no value configured")
            continue

        resolved_value = parse_template(template, prod_fields, log_field_name=f"dimension '{dimension_name}'")

        if resolved_value is None:
            continue

        normalized_value = normalize_decimal(resolved_value, field_name=f"{dimension_name}")

        if isinstance(normalized_value, (int, float)):
            unit_code = "KGM" if dimension_name == "weight" else "MMT"

            result[dimension_name] = {
                "@type": "QuantitativeValue",
                "value": normalized_value,
                "unitCode": unit_code
            }
            logger.log(f"[JSON-LD] [INFO] Product '{product_name}': Dimension '{dimension_name}' = {normalized_value} {unit_code}")
        else:
            logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': Dimension '{dimension_name}': Value '{resolved_value}' is not numeric after normalization")

    if result:
        logger.log(f"[JSON-LD] Product '{product_name}': Added {len(result)} dimension(s): {', '.join(result.keys())}")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': No dimensions added")

    return result if result else None


def has_dimensions(jsonld_data):
    dimension_names = ["width", "depth", "height", "weight"]
    return any(name in jsonld_data for name in dimension_names)
