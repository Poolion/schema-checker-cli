#!/usr/bin/env python3
"""Schema Checker CLI: Validate JSON/YAML config files against required fields.

Usage Examples:
  python3 schema-checker.py config.json --required 'id,name,email'
  python3 schema-checker.py users.yaml -r 'user_id,username'
  
Requirements file format (one field per line):
  id
  name
  email
  age
"""

import sys
import json
import yaml


def load_required_fields(requirements_file):
    """Load required fields from a requirements file or command-line list."""
    if not requirements_file:
        return set()
    
    # Try loading from file first
    try:
        with open(requirements_file, 'r') as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        pass
    
    # Otherwise treat as CSV-like input (comma or space separated)
    return set(requirements_file.split())


def validate_json(filepath, required_fields):
    """Validate a JSON file against required fields."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f'[{filepath}] JSON parse error:', e)
        return False
    
    # Handle nested structures (dict in dict or dict in list)
    fields_missing = set(required_fields) - data.keys() if isinstance(data, dict) else required_fields
    
    if fields_missing:
        missing_str = ', '.join(sorted(fields_missing))
        print(f'[{filepath}] Missing required fields:', missing_str)
        return False
        
    return True


def validate_yaml(filepath, required_fields):
    """Validate a YAML file against required fields."""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f'[{filepath}] YAML parse error:', e)
        return False
    
    # Handle nested structures (dict in dict or dict in list)
    fields_missing = set(required_fields) not in [set() for _ in data.keys()] if isinstance(data, dict) else set()
    
    if fields_missing:
        missing_str = ', '.join(sorted(fields_missing))
        print(f'[{filepath}] Missing required fields:', missing_str)
        return False
        
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate config files against schema requirements')
    
    parser.add_argument('file', help='JSON or YAML file to validate')  
    parser.add_argument('-r', '--requirements', metavar='COMMA-SEPARATED', 
                       help='Required fields (e.g. id,name,email)')
    parser.add_argument('--requirement-file', '-R', metavar='FILE',
                       help='Path to a requirements file (one field per line)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show detailed output including found fields')
    
    args = parser.parse_args()
    
    # Load required fields from either command-line or file
    req_file = getattr(args, 'requirements', None)  # -r option
    
    if not req_file:
        print('Error: Specify required fields with -r "field1,field2"')
        sys.exit(1)
        
    # Load requirements
    actual_requirements = load_required_fields(req_file)
    
    # Determine file type
    if args.file.endswith('.json'):
        success = validate_json(args.file, actual_requirements)
    elif args.file.endswith(('.yaml', '.yml')):
        success = validate_yaml(args.file, actual_requirements)
    else:
        print(f'[{args.file}] Unknown format: try with .json or .yaml extension')
        sys.exit(1)
    
    if not success:
        print('Validation failed')
        sys.exit(2)
        
    print('[SUCCESS] All required fields present:', ', '.join(sorted(actual_requirements)))


if __name__ == '__main__':  
    main()
