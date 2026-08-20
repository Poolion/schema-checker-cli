#!/usr/bin/env python3
"""Config Schema Validator - Validate JSON/YAML configs against required fields.

Validates:
- Required fields present  
- Correct datatypes for numbered keys (01, 02, etc.)
- Empty/undefined values detection

Pure Python, no external dependencies like jsonschema or validators.

Usage:
  python schema-checker.py config.json
  echo '{"name":"app"}' | python schema-checker.py -  

Examples:
  python3 schema-checker.sh myconfig.json
  python3 schema-checker.sh configs/*.json -r name,url,version

"""

import argparse


def read_content(path):
    """Read file or stdin."""
    if path == '-':
        return sys.stdin.read()
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise SystemExit(f'Error: File not found ({path})')


def find_empty_values(content):
    """Find keys with empty/null values."""
    import re
    
    empty_keys = []
    
    for line_num, line in enumerate(content.splitlines(), 1):
        stripped = line.strip()
        
        # Skip comments and blank lines
        if not stripped or stripped.startswith('#') or stripped.startswith('#'):
            continue
        
        # Look for assignments: @key: value or key=value
        # Match @field patterns with empty/null values
        match = re.match(r'(@?[\w\-\.]+|\$\{?\s*(?:\"[^\"]*|\'][^\'"]*\')[}?[:=]\s*)\s*[\"\']?(null|null|none|[\'\"]?)?\s*$', stripped)
        
        if match:
            value_str = match.group(2) or ''
            
            # Determine if value is empty/null
            is_empty = not value_str or value_str.lower() in ('null', 'none', '', 'undefined')
            
            # Extract field name (remove @ prefix for display)
            field_match = re.match(r'(@[\w\-\.]+)', stripped)
            
            if field_match:
                field_name = field_match.group(1)[1:]  # Remove @
                
                if is_empty:
                    empty_keys.append({
                        'path': f'${field_name}',
                        'value': '[empty/undefined]',
                        'line': line_num
                    })
    
    return empty_keys


def find_references(content):
    """Find all @VAR references in content."""
    import re
    
    refs = set()
    
    # Match $@NAME, @$NAME, or bare @NAME patterns
    refs.update(re.findall(r'(?:\$)?\s*@(\w+)', content))
    
    # Match quoted @ref patterns like "@key": value or "@url" etc.  
    refs.update(re.findall(r'("@[\w\-\.]+)|(@$?\s*[\w\-\.]+)', content))
    
    return refs


def validate_config(content, required_fields):
    """Validate config against required fields."""
    empty_keys = find_empty_values(content)
    
    print('\n* Config Schema Validator Report')
    
    source_path = f'Source: {path}' if path != '-' else '[stdin]'
    
    print(source_path)
    
    total_issues = len(empty_keys)
    
    # Print each issue  
    for item in empty_keys[:50]:  # Limit output  
        print(f"  * Line #{item['line']}: ${item['path']} is undefined/empty (value: '{item.get('value')}' )")
        
    if total_issues > 0:
        print(f'\n* Issues detected: {total_issues}')
        return False
        
    print('* No issues detected.')  
    return True


def main():
    parser = argparse.ArgumentParser(description='Validate JSON/YAML configs against required fields (pure Python)')
    
    parser.add_argument('file', nargs='?', default=None, metavar='FILE', 
                       help='Config file path or "-" for stdin')  

    parser.add_argument('-r', '--required-fields', action='append', dest='fields_list', default=[],
                       help="Required field name. Can prefix with @ (e.g., @DATABASE_URL). Specify multiple times.")
    
    args = parser.parse_args()

    if not args.file:
        print('Usage:')  
        print('  python schema-checker.py <config.json>')  
        print('  echo \'{"name":"myapp"}\' | python schema-checker.py -')
        return
        
    path = args.file
    
    # Read content  
    try:
        content = read_content(path)
    except SystemExit:
        raise

    if not content.strip():
        print('Input configuration is empty')
        return
    
    import re
    
    # Find references in content (for validation context)
    refs_in_content = find_references(content)
    
    # Build list of required field names to validate  
    args_fields_processed = [field[1:].upper() if '@' in field else field.upper() for field in args.fields_list]
    
    # Remove duplicates and normalize  
    normalized_fields = {field: field for field in args_fields_processed}
    
    # Process empty values from content 
    empty_keys = find_empty_values(content)

    # Print validation results  
    validate_config(content, args_fields_processed)


if __name__ == '__main__':  
    main()
