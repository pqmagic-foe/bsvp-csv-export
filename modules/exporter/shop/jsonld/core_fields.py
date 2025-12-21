# -*- coding: utf-8 -*-
"""
Core product fields generator for JSON-LD export
Handles: mpn, model
"""

from .normalizer import parse_template
from modules.logger import Logger


def generate_core_fields(prod_fields, mapping):
    core_config = mapping.get("core", {})
    result = {}
    logger = Logger()
    
    product_name = prod_fields.get("NAME", prod_fields.get("ARTNR", "Unknown"))
    logger.log(f"[JSON-LD] Product '{product_name}': Processing {len(core_config)} core field(s)")
    
    for field_name, template in core_config.items():
        value = parse_template(template, prod_fields, log_field_name=f"core field '{field_name}'")
        
        if not value:
            continue
        
        result[field_name] = str(value)
    
    if result:
        logger.log(f"[JSON-LD] Product '{product_name}': Added {len(result)} core field(s): {', '.join(result.keys())}")
    else:
        logger.log(f"[JSON-LD] Product '{product_name}': No core fields added")
    
    return result if result else None


def has_core_fields(jsonld_data):
    core_field_names = ["mpn", "model"]
    
    for field_name in core_field_names:
        if field_name in jsonld_data:
            return True
    
    return False
