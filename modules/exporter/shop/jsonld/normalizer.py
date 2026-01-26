# -*- coding: utf-8 -*-
"""
Unit normalization and value validation utilities for JSON-LD export
"""

import re
from modules.logger import Logger
from modules.formatter import format_field


def parse_template(template, prod_fields, log_field_name=None):
    logger = Logger()

    pattern = r'\$([A-Z]+)::([^\$]+)\$'
    matches = re.findall(pattern, template)

    if not matches:
        return template

    result = template

    for source, field_id in matches:
        placeholder = f"${source}::{field_id}$"

        if source == "TECHDATA":
            techdata = prod_fields.get("TECHDATA", {})
            value = techdata.get(field_id)
            if value is not None and isinstance(value, str):
                value = format_field(value, field_id)
        elif source == "PROD":
            value = prod_fields.get(field_id)
        else:
            if log_field_name:
                logger.log(f"[JSON-LD] [WARNING] Template for '{log_field_name}': Invalid source '{source}' in placeholder '{placeholder}'")
            return None

        if is_empty_value(value):
            if log_field_name:
                logger.log(f"[JSON-LD] [DEBUG] Template for '{log_field_name}': Placeholder '{placeholder}' has empty value, skipping entire template")
            return None

        result = result.replace(placeholder, str(value))

    return result.strip()


def normalize_decimal(value, field_name=None, log_errors=True):
    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        original_value = value
        value = value.strip()

        # german format: dots as thousand sep, comma as decimal
        value_cleaned = value.replace(".", "").replace(",", ".")

        try:
            return float(value_cleaned)
        except ValueError:
            if log_errors:
                logger = Logger()
                field_info = f" for field '{field_name}'" if field_name else ""
                logger.log(f"[JSON-LD] [WARNING] Failed to convert '{original_value}' to numeric value{field_info}")
            return value

    return value


def is_empty_value(value, log_reason=False, field_name=None):
    if value is None:
        if log_reason:
            logger = Logger()
            field_info = f" (field: {field_name})" if field_name else ""
            logger.log(f"[JSON-LD] [DEBUG] Value is None{field_info}")
        return True

    if isinstance(value, str):
        original_value = value
        value = value.strip()

        if value == "":
            if log_reason:
                logger = Logger()
                field_info = f" (field: {field_name})" if field_name else ""
                logger.log(f"[JSON-LD] [DEBUG] Value is empty string{field_info}")
            return True

        invalid_values = [
            "keine angabe",
            "keine werte vorhanden",
            "nicht vorhanden",
            "keine",
            "kein neuer eintrag einfügen",
            "xxxx",
            "$",
        ]

        value_lower = value.lower()
        for invalid in invalid_values:
            if invalid in value_lower:
                if log_reason:
                    logger = Logger()
                    field_info = f" (field: {field_name})" if field_name else ""
                    logger.log(f"[JSON-LD] [DEBUG] Value '{original_value}' matches placeholder pattern '{invalid}'{field_info}")
                return True

    return False
