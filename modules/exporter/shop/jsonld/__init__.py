# -*- coding: utf-8 -*-
"""
JSON-LD export module for BSVP shop products
Generates structured schema product data for AI bots and Google
"""

from .mapping_loader import identify_product_type, load_mapping
from .product_fields import generate_product_fields
from .additional_properties import generate_additional_properties
from .renderer import render_script_tag
from modules.logger import Logger


def export_jsonld(parameters):
    prod_fields = parameters.get("prod_fields", {})
    logger = Logger()

    product_name = prod_fields.get("NAME", prod_fields.get("ARTNR", "Unknown"))
    product_artnr = prod_fields.get("ARTNR", "N/A")

    logger.log("")
    logger.log(f"[JSON-LD] ========== Starting JSON-LD export for product: '{product_name}' (ARTNR: {product_artnr}) ==========")

    logger.log(f"[JSON-LD] Product '{product_name}': Identifying product type")
    product_type = identify_product_type(prod_fields)

    if not product_type:
        logger.log(f"[JSON-LD] Product '{product_name}': SKIPPED - No product type identified (field 0000191 is empty)")
        logger.log(f"[JSON-LD] ========== Finished (skipped) ==========")
        logger.log("")
        return None

    logger.log(f"[JSON-LD] Product '{product_name}': Product type identified as '{product_type}'")

    logger.log(f"[JSON-LD] Product '{product_name}': Loading mapping configuration")
    mapping = load_mapping(product_type)

    if not mapping:
        logger.log(f"[JSON-LD] [WARNING] Product '{product_name}': SKIPPED - No mapping configured for product type '{product_type}'")
        logger.log(f"[JSON-LD] ========== Finished (skipped) ==========")
        logger.log("")
        return None

    logger.log(f"[JSON-LD] Product '{product_name}': Building JSON-LD structure")
    jsonld_data = {
        "@context": "https://schema.org",
        "@type": "Product"
    }

    logger.log(f"[JSON-LD] Product '{product_name}': Generating product fields")
    product_fields = generate_product_fields(prod_fields, mapping)
    if product_fields:
        jsonld_data.update(product_fields)
        logger.log(f"[JSON-LD] Product '{product_name}': Product fields added successfully")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': No product fields generated")

    logger.log(f"[JSON-LD] Product '{product_name}': Generating additional properties")
    additional_props = generate_additional_properties(prod_fields, mapping)
    if additional_props:
        jsonld_data["additionalProperty"] = additional_props
        logger.log(f"[JSON-LD] Product '{product_name}': Additional properties added successfully")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': No additional properties generated")

    total_fields = len(jsonld_data)
    logger.log(f"[JSON-LD] Product '{product_name}': Validating generated data (total fields: {total_fields})")

    if total_fields <= 2:
        logger.log(f"[JSON-LD] Product '{product_name}': SKIPPED - No useful data generated (only @context and @type)")
        logger.log(f"[JSON-LD] ========== Finished (skipped - no data) ==========")
        logger.log("")
        return None

    logger.log(f"[JSON-LD] Product '{product_name}': Rendering script tag")
    script_tag = render_script_tag(jsonld_data)
    
    if script_tag:
        logger.log(f"[JSON-LD] Product '{product_name}': SUCCESS - JSON-LD export completed successfully")
        logger.log(f"[JSON-LD] ========== Finished (success) ==========")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': FAILED - Rendering returned None")
        logger.log(f"[JSON-LD] ========== Finished (failed) ==========")
    
    logger.log("")
    
    return script_tag


__all__ = ['export_jsonld']
