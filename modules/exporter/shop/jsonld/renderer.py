# -*- coding: utf-8 -*-
"""
JSON-LD renderer for generating final script tag output
"""

import json
from modules.logger import Logger


def render_script_tag(jsonld_data):
    logger = Logger()

    if not jsonld_data:
        logger.log("[JSON-LD] [WARNING] render_script_tag called with empty jsonld_data")
        return None

    try:
        json_string = json.dumps(jsonld_data, ensure_ascii=False, separators=(',', ':'))

        logger.log(f"[JSON-LD] [INFO] Rendered JSON-LD ({len(json_string)} characters, {len(jsonld_data)} top-level fields)")

        pretty_json = json.dumps(jsonld_data, ensure_ascii=False, indent=2)
        logger.log(f"[JSON-LD] [INFO] JSON-LD Output (pretty-printed):")
        logger.log(pretty_json)

        return json_string
    except (TypeError, ValueError) as e:
        logger.log(f"[JSON-LD] [ERROR] Failed to serialize JSON-LD data: {e}")
        return None


def render_compact(jsonld_data):
    if not jsonld_data:
        return None
    return json.dumps(jsonld_data, ensure_ascii=False, separators=(',', ':'))
