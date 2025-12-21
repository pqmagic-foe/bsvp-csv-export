#!/usr/bin/env python3
"""Update jsonld-mapping.json from Technische-Masken .bcm.json files."""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Set


EXCLUDED_LABELS = {
    "gpsr-pflicht",
    "lieferant",
    "listenpreis",
    "artikelnummer",
    "herstellerbezeichnung"
}


def slugify_label(label: str) -> str:
    """Convert label to slug (e.g., 'Außen Breite in mm' -> 'aussen_breite_in_mm')."""
    slug = label.lower()

    transliterations = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'à': 'a', 'á': 'a',
        'ó': 'o', 'ò': 'o', 'ú': 'u', 'ù': 'u', 'í': 'i', 'ì': 'i',
    }

    for char, replacement in transliterations.items():
        slug = slug.replace(char, replacement)

    slug = re.sub(r'[\s/\-]+', '_', slug)
    slug = re.sub(r'[^\w_]', '', slug)
    slug = re.sub(r'_+', '_', slug).strip('_')

    return slug


def read_bcm_json_files(directory: Path) -> List[Dict]:
    """Read all .bcm.json files from directory."""
    json_files = []

    for file_path in directory.glob("*.bcm.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_files.append({'filename': file_path.name, 'data': data})
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return json_files


def extract_properties_and_types(json_files: List[Dict]) -> tuple:
    """Extract property definitions and product types from JSON files."""
    property_definitions = {}
    product_types = {}

    for file_info in json_files:
        data = file_info['data']
        filename = file_info['filename']

        product_type_name = None
        for item in data:
            if item.get('tag') == 'NAME' and item.get('id') is None:
                product_type_name = item.get('value')
                break

        if not product_type_name:
            print(f"Warning: No product type name found in {filename}")
            continue

        properties = []
        for item in data:
            item_id = item.get('id')
            item_label = item.get('label', '')

            if item_label.lower() in EXCLUDED_LABELS:
                continue

            if item_id is None or item_id == "0000191":
                continue

            if item.get('tag') == 'HEAD':
                continue

            if item_label:
                slug_key = slugify_label(item_label)

                if slug_key not in property_definitions:
                    property_definitions[slug_key] = {
                        "label": item_label,
                        "value": f"$TECHDATA::{item_id}$"
                    }

                properties.append(slug_key)

        if properties:
            product_types[product_type_name] = {"additional_properties": properties}
            print(f"Processed: {product_type_name} ({len(properties)} properties)")

    return property_definitions, product_types


def update_jsonld_mapping(
    mapping_file: Path,
    new_property_definitions: Dict,
    new_product_types: Dict
) -> None:
    """Update jsonld-mapping.json, preserving existing property definitions."""
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {mapping_file} not found, creating new file")
        mapping = {"defaults": {}, "property_definitions": {}, "product_types": {}}

    existing_props = mapping.get("property_definitions", {})
    new_props_count = 0

    for key, value in new_property_definitions.items():
        if key not in existing_props:
            existing_props[key] = value
            new_props_count += 1

    mapping["property_definitions"] = existing_props
    mapping["product_types"] = new_product_types

    with open(mapping_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated {mapping_file}:")
    print(f"  - Added {new_props_count} new property definitions")
    print(f"  - Total property definitions: {len(existing_props)}")
    print(f"  - Updated {len(new_product_types)} product types")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    technische_masken_dir = project_root / "Technische-Masken"
    mapping_file = project_root / "mappings" / "jsonld" / "jsonld-mapping.json"

    print("=" * 60)
    print("Updating jsonld-mapping.json from Technische-Masken")
    print("=" * 60)
    print(f"Reading from: {technische_masken_dir}")
    print(f"Updating: {mapping_file}")
    print()

    print("Reading .bcm.json files...")
    json_files = read_bcm_json_files(technische_masken_dir)
    print(f"Found {len(json_files)} files\n")

    if not json_files:
        print("Error: No .bcm.json files found!")
        return

    print("Extracting properties and product types...")
    property_definitions, product_types = extract_properties_and_types(json_files)
    print()

    print("Updating jsonld-mapping.json...")
    update_jsonld_mapping(mapping_file, property_definitions, product_types)

    print("\n" + "=" * 60)
    print("Update completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
