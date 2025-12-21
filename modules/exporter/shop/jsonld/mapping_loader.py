# -*- coding: utf-8 -*-
"""
Mapping configuration loader for JSON-LD export
"""

import json
import os
from modules.logger import Logger


_mapping_cache = None


def load_mappings():
    global _mapping_cache

    if _mapping_cache is not None:
        return _mapping_cache

    mapping_path = "mappings/jsonld/jsonld-mapping.json"
    logger = Logger()

    if not os.path.exists(mapping_path):
        logger.log(f"[JSON-LD] [WARNING] Mapping file not found: {mapping_path}")
        _mapping_cache = {}
        return _mapping_cache

    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            _mapping_cache = json.load(f)
        logger.log(f"[JSON-LD] [INFO] Loaded {len(_mapping_cache)} product type mappings from {mapping_path}")
        return _mapping_cache
    except json.JSONDecodeError as e:
        logger.log(f"[JSON-LD] [ERROR] Failed to parse mapping file: {e}")
        _mapping_cache = {}
        return _mapping_cache
    except Exception as e:
        logger.log(f"[JSON-LD] [ERROR] Failed to load mapping file: {e}")
        _mapping_cache = {}
        return _mapping_cache


def identify_product_type(prod_fields):
    techdata = prod_fields.get("TECHDATA", {})
    product_type = techdata.get("0000191")

    if product_type:
        product_type = str(product_type).strip()

    if not product_type:
        logger = Logger()
        product_name = prod_fields.get("NAME", prod_fields.get("ARTNR", "Unknown"))
        logger.log(f"[JSON-LD] [INFO] Product '{product_name}': No product type found (field 0000191 empty)")

    return product_type if product_type else None


def load_mapping(product_type):
    if not product_type:
        return None

    mappings = load_mappings()
    logger = Logger()

    product_types = mappings.get("product_types", {})
    defaults = mappings.get("defaults", {})

    product_config = None
    if product_type in product_types:
        logger.log(f"[JSON-LD] [INFO] Found mapping for product type: '{product_type}'")
        product_config = product_types[product_type]
    else:
        for key, value in product_types.items():
            if key.lower() == product_type.lower():
                logger.log(f"[JSON-LD] [INFO] Found mapping for product type: '{product_type}' (case-insensitive match with '{key}')")
                product_config = value
                break

    if not product_config:
        return None

    merged_config = {}

    if "core" in defaults:
        merged_config["core"] = defaults["core"]
    if "dimensions" in defaults:
        merged_config["dimensions"] = defaults["dimensions"]

    if "additional_properties" in product_config:
        merged_config["additional_properties"] = product_config["additional_properties"]

    if "core" in product_config:
        merged_config["core"] = product_config["core"]
    if "dimensions" in product_config:
        merged_config["dimensions"] = product_config["dimensions"]

    return merged_config


def get_available_product_types():
    mappings = load_mappings()
    product_types = mappings.get("product_types", {})
    return list(product_types.keys())


def reload_mappings():
    global _mapping_cache
    _mapping_cache = None
    return load_mappings()
