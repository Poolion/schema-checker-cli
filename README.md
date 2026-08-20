# Config Schema Validator

Validate JSON/YAML configuration files against required fields without external dependencies.

## What It Does

`schema-checker.py` checks:
- Required fields are present in the config
- Empty/undefined values for @field patterns  
- Proper formatting of numbered keys (01, 02, etc.)

All validation uses pure Python - no jsonschema, validators, or other external deps.

## Install/Usage

```bash
# Validate a file
python3 schema-checker.py config.json

# Read from stdin
echo '{"name":"myapp","@version":"1.0"}' | python3 schema-checker.py -

# Specify required fields (use -r multiple times)
python3 schema-checker.py configs/*.json \
  -r name,url,version,\@DATABASE_URL
  
```

## How to Use

### Basic Validation

```bash
python3 schema-checker.py myconfig.json
```

Validates that a file contains properly defined configuration keys.

### Check for Empty Values

```bash
echo '@database:' | python3 schema-checker.py -
```

The tool will report any @field patterns with empty/null values.

## Notable Implementation Details

- **No external dependencies**: Pure Python, uses only standard library
- **Pure pattern matching**: Uses regex to find @field references without full JSON/YAML parsing  
- **Flexible input**: Accepts files or stdin pipes
- **Simple reporting**: Clear line-by-line issues with file locations

## Support

If you find this useful, you can support development: https://www.buymeacoffee.com/poolion
