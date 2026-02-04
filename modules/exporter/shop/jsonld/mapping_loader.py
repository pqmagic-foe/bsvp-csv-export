# -*- coding: utf-8 -*-
"""
Mapping configuration loader for JSON-LD export
"""

import json
import os
from modules.constants import JSONLD_MAPPING_PATH
from modules.logger import Logger


_mapping_cache = None


def load_mappings():
    global _mapping_cache

    if _mapping_cache is not None:
        return _mapping_cache

    mapping_path = JSONLD_MAPPING_PATH
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
        from .normalizer import get_product_name
        product_name = get_product_name(prod_fields)
        logger.log(f"[JSON-LD] [INFO] Product '{product_name}': No product type found (field 0000191 empty)")

    return product_type if product_type else None


def load_mapping(product_type):
    if not product_type:
        return None

    mappings = load_mappings()
    logger = Logger()

    product_types = mappings.get("product_types", {})
    product_fields = mappings.get("product", {})

    # Try exact match first, then case-insensitive
    if product_type in product_types:
        logger.log(f"[JSON-LD] [INFO] Found mapping for product type: '{product_type}'")
        product_config = product_types[product_type]
    else:
        lower_map = {k.lower(): k for k in product_types}
        original_key = lower_map.get(product_type.lower())
        if original_key:
            logger.log(f"[JSON-LD] [INFO] Found mapping for product type: '{product_type}' (case-insensitive match with '{original_key}')")
            product_config = product_types[original_key]
        else:
            return None

    # Copy product fields (can be overridden by product-type-specific config)
    merged_config = {"product": dict(product_fields)}

    # Override product fields with product-type-specific fields if present
    if "product" in product_config:
        merged_config["product"].update(product_config["product"])

    if "additional_properties" in product_config:
        merged_config["additional_properties"] = product_config["additional_properties"]

    return merged_config


def reload_mappings():
    global _mapping_cache
    _mapping_cache = None
    return load_mappings()
