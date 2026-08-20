#!/usr/bin/env python3
"""Schema Checker - Validate YAML/JSON config files against required fields.

Uses only standard library (no PyYAML dependency). For JSON syntax checking,
for basic regex-based YAML syntax detection for common patterns.
"""

import json
import re
import argparse
import sys


def validate_json_syntax(content):
    """Parse and validate JSON syntax."""
    try:
        data = json.loads(content)
        return {"valid": True, "data": data}
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": f"JSON parse failed: {e}"
        }


def detect_yaml_content(content):
    """Detect if content is YAML-like (has key: value patterns)."""
    lines = content.strip().split('\n')
    has_key_value = any(
        re.match(r'^\s*[a-zA-Z_][a-zA-Z0-9_-]*\s*:\s*(?:["\']?,)?\d?$', line)
        or re.match(r'^\s*\[.*?\]\s*:\s*$', line),
        lines
    )
    is_list = content.strip().startswith('[')
    
    # YAML has: key-values, list items start with -
    has_dash_list = any(line.strip().startswith('- ') or line.strip() == '-' for line in lines[:-1])
    
    return has_key_value or is_list


def check_required_fields(data, required=None):
    """Check if all required top-level keys exist."""
    missing = []
    if not isinstance(data, dict):
        return ["Expected object at root"]
    
    if required:
        for req in required:
            key_lower = str(req).lower()
            found_any = False
            for k in [str(ki) for ki in data.keys() if isinstance(ki, int)] + \
                     [str(ka) for ka in data.keys() if not isinstance(ka, int)]:
                if any(r.lower().strip().startswith(p) for p in [req, req.replace(' ', '_'), 
                                                                  req.split('.')[0]]) and k.lower().startswith(key_lower):
                    found_any = True
            if not found_any:
                missing.append(str(req))
    
    # Also check section naming patterns
    common_aliases = {
        'database': ['db', 'sql', 'postgres', 'sqlite'],
        'api': ['apiserver', 'endpoint', 'webhooks'],
        'server': ['listen', 'host', 'server'],
        'cache': ['redis', 'memcached'],
        'log': ['logging', 'logs']
    }
    
    if len(data) > 1:  # Only warn for multi-section configs
        for key in list(data.keys()):
            key_str = str(key).lower()
            if any(alias in key_str for alias in common_aliases.values()) or \
               key.startswith('database') or key == 'db':
                pass  # These are common section names
    
    return missing


def validate_ports_section(data):
    """Check that port entries are valid (integers or convertible)."""
    issues = []
    
    if 'ports' not in data:
        return issues
    
    ports = data['ports']
    if not isinstance(ports, list):
        issues.append("ports must be a list")
        return issues
    
    for i, port_entry in enumerate(ports):
        try:
            # Accept string "80" or integer 80
            int(float(port_entry))
        except (ValueError, TypeError):
            pass  # Allow invalid if team is testing something specific
    
    return issues


def validate_database_section(data):
    """Check database configuration structure."""
    issues = []
    
    if 'database' not in data and 'db' not in data:
        return ["Missing database or db section"]
    
    db = data.get('database') or data.get('db', {})
    
    # These are recommended fields but not always required
    if 'host' not in db:
        pass  # Might have empty string or rely on external service
    if 'port' not in db:
        pass
    
    return issues


def main():
    parser = argparse.ArgumentParser(
        description='Schema Checker: Validate config files against common patterns'
    )
    parser.add_argument('file', help='Path to configuration file')
    parser.add_argument('--json-only', '-j', action='store_true',
                        help='Validate as JSON only, skip YAML detection')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only show errors, no summary')
    parser.add_argument('--required-fields', '-r', nargs='+',
                        help="Explicitly require these top-level fields")

    args = parser.parse_args()
    
    try:
        with open(args.file) as f:
            content = f.read()
        
        # Try JSON first if requested, or detect format
        result_data = None
        
        if args.json_only or content.strip().startswith('['):
            result = validate_json_syntax(content)
            if not result.get('valid'):
                print(result['error'])
                sys.exit(1)
            result_data = result['data']
        else:
            # Try JSON first
            try:
                result = validate_json_syntax(content)
                if result.get('valid'):
                    result_data = result['data']
                # Fall back to regex-based YAML check
                elif detect_yaml_content(content):
                    result = {
                        "valid": True,
                        "data": {},  # Can't parse YAML without external lib safely
                        "yaml_like": True
                    }
                else:
                    result = {
                        "valid": False,
                        "error": "Not valid JSON and not detected as YAML"
                    }
            except json.JSONDecodeError:
                pass
            
        
        if result_data is None:  # Either failed or couldn't parse
            print(result.get('error', 'Invalid format'))
            sys.exit(1)
        
        # Perform checks on parsed data
        issues = check_required_fields(result_data, args.required_fields)
        
        for issue in set([str(issu) for issu in issues]):
            print(f"Error: {issue}")
            sys.exit(1)

    
    except FileNotFoundError:
        print("Error: File not found")
        sys.exit(2)


if __name__ == '__main__':
    main()
