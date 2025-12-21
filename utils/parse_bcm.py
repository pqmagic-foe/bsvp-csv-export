import argparse
import re
import json
import sys
import os

def parse_bcm(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # The file is semicolon delimited
    segments = content.split(';')
    parsed_data = []

    for segment in segments:
        if not segment.strip():
            continue

        # Extract internal ID @[[12345]] if present
        id_match = re.search(r'@\[\[(\d+)\]\]', segment)
        element_id = id_match.group(1) if id_match else None
        
        # Remove the ID from the string to clean up parsing
        clean_segment = re.sub(r'@\[\[\d+\]\]', '', segment).strip()

        parts = clean_segment.split('::')
        tag = parts[0]

        entry = {
            'tag': tag,
            'id': element_id
        }

        if tag == 'NAME':
            entry['label'] = 'Name'
            entry['value'] = parts[1] if len(parts) > 1 else ''
        
        elif tag == 'DESC':
            entry['label'] = 'Description'
            entry['value'] = parts[1] if len(parts) > 1 else ''

        elif tag in ['EF', 'HEAD']:
            # EF = Entry Field, HEAD = Header
            # Format: EF::Label::Value
            entry['type'] = 'Field' if tag == 'EF' else 'Section Header'
            entry['label'] = parts[1] if len(parts) > 1 else ''
            entry['default_value'] = parts[2] if len(parts) > 2 else ''

        elif tag == 'PUM':
            # Format: PUM::Label::Def1::Def2][Option1][Option2]...
            entry['type'] = 'Dropdown/Menu'
            entry['label'] = parts[1] if len(parts) > 1 else ''
            
            # Reconstruct remainder to parse options
            remainder = "::".join(parts[2:])
            
            # Options are enclosed in brackets [Option]
            # We filter out the '][' separator logic by just finding all bracketed content
            options = re.findall(r'\[(.*?)\]', remainder)
            
            # Sometimes defaults are before the first bracket
            pre_bracket_defs = remainder.split('][')[0].split('::')
            entry['defaults'] = [x for x in pre_bracket_defs if x and '[' not in x]
            entry['options'] = options

        parsed_data.append(entry)

    return parsed_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Parse .bcm file content.')
    parser.add_argument('file', help='Path to the .bcm file')
    
    args = parser.parse_args()
    
    try:
        result = parse_bcm(args.file)
        print(json.dumps(result, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"An error occurred: {e}")