# Schema Checker CLI

Validate JSON/YAML config files against required fields in Python.

## What It Does

`schema-checker.py` validates configuration files by checking that all required fields are present—perfect for:

- **API configs**: Ensure mandatory API keys, endpoints, and timeouts  
- **Database configs**: Validate connection strings, hostnames, ports  
- **Deployment manifests**: Confirm required environment flags  
- **Config management**: Prevent misconfiguration before startup  

Uses Python's standard library only—no external dependencies.

## Usage

### Check JSON File Against Required Fields

```bash
# Quick validation (comma-separated fields)
python3 schema-checker.py production.json -r 'host,port,database'

# Output:
# [production.json] All required fields present: host, port, database
```

### Validate with Requirement File

For complex configs with many required fields:

```bash
python3 schema-checker.sh config.yaml \
  --requirement-file requirements.txt
  
# requirements.txt format (one per line):
#   database_url
#   cache_host
#   timeout_seconds
#   retry_count
```

### Show Found Fields

```bash
python3 schema-checker.py api-config.json \
  -r 'api_key,version,environment' --verbose
  
# Output:
# [api-config.json] Found fields: environment, version, api_key
# [SUCCESS] All required fields present: api_key, environment, version
```

## Examples

### Validate Production Config

For API deployments where `host`, `port`, and `database` are required:

```bash
python3 schema-checker.py production.json \
  -r 'host,port,database'
  
# Valid output:
# [production.json] All required fields present: host, port, database
# Exit code: 0 (success)

# Missing field error:
# [production.json] Missing required fields: host
# Validation failed
# Exit code: 2
```

### Database Connection Validator

In CI/CD pipelines:

```bash
#!/bin/bash
python3 schema-checker.sh $CI_JOB_CONFIG \
  -r 'database_url,username,password,max_connections' > \
  /tmp/validation-result.txt || exit 1
```

This runs in pipeline checks: if missing required database fields—deploy fails early.

### Environment Manifest Validator

For multi-environment deployments:

```bash
# requirements.txt:
api_version
environment
debug_mode
rate_limit

python3 schema-checker.sh config.json \
  --requirement-file ./requirements.txt
  
# Validates all env-specific fields before deployment
```

## Output Format

The tool provides:

- **Success messages**: `[FILENAME] All required fields present: field1, field2`  
- **Error messages**: `[FILENAME] Missing required fields: missing_field1, missing_field2`  
- **Validation results**: Exit code 0 for success, 2 for failure  

For CI integration—check exit codes:

```bash
python3 schema-checker.sh config.json -r 'required1' && \
  echo "Config valid" || \
  echo "Missing required fields!" 
```

## Why Pure Python?

Existing tools like `jq` or `yq` require:
- **Compilation** (C-based binaries) or  
- **External dependencies** (Perl, Ruby, etc.)  

Schema Checker CLI solves this by:
- **Zero imports overhead** (runs instantly)  
- **Cross-platform** (works wherever Python exists)  
- **Handles both formats**: JSON and YAML with same interface  
- **CI/CD friendly**: Exit codes for automation  

## Implementation Notes

### How Validation Works

The tool checks field presence in config dictionaries:

```python
def validate_json(filepath, required_fields):
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)  
    except json.JSONDecodeError:
        raise
    
    # Handle nested structures
    missing = set(required_fields) - data.keys()
    
    if missing:
        print(f'Missing required:', ', '.join(missing))
        return False
        
    return True
```

### Supporting Multiple Config Formats

The tool handles:

- **JSON**: `{"host": "localhost", "port": 8080, "database": "db"}`  
- **YAML**: `---\nhost: localhost\nport: 8080\n`  

Both validated against same fields list—use `.json` or `.yaml` extension to signal format.

### Field Name Normalization

When comparing required vs found fields, the tool normalizes:

- **Case-insensitive matching**: `Port` matches `port`  
- **Trailing whitespace trimming**: `'  port '` → `port`  
- **Whitespace normalization**: Comma-separated list splits on `,` and spaces  

This prevents validation failures from formatting inconsistencies.

## Use Cases

### API Deployment Validator

Ensure all mandatory config fields exist before deploying APIs:

```bash
python3 schema-checker.sh /etc/api/config.json \
  -r 'api_key,environment,version,timeout' > deploy-result.txt
  
# Exit code determines deployment gates
[ $? -eq 0 ] && deploy_api || abort --missing-fields
```

### CI/CD Pipeline Integration

For GitHub Actions or similar:

```yml
steps:
  - run: python schema-checker.sh config.json -r 'required_fields'
  
    if: ${{ failure }}
      continue-on-error: true
  
# Validates before build pipeline proceeds
```

### Config Drift Detection

Compare configs across environments:

```bash
python3 schema-checker.sh /etc/config/deploy.json \
  --requirement-file ./prod-reqs.txt || {
    echo "Production config missing required field!"
    exit 1
  }
```

### Environment-Specific Validation

Different environments can have differing field requirements:

```bash
python3 schema-checker.sh production.json \
  --requirement-file prod-requirements.txt
  
python3 schema-checker.sh development.json \
  --requirement-file dev-requirements.txt
```

## Requirements File Format

Simple text file, one required field per line:

```txt
# /path/to/requirements.txt
database_url  
cache_host  
timeout_seconds  
retry_count
```

The tool strips whitespace and ignores comment lines—useful for documentation-rich requirement files.

## Limitations & Future Plans

Current v0.1 features:
- ✅ JSON and YAML validation
- ✅ Required field checking
- ✅ Field normalization (case-insensitive, whitespace trimming)
- ✅ File-based requirements listing

Coming in future releases:
- `--type strict` (exact case-matching, no normalization)
- `--allow-additional` (skip validation if extra fields present)
- `--show-all-fields` (list all found vs required)  
- `--generate-requirements-file <config> > req.txt` (auto-generate requirements from existing configs)

For complex schema validation with types and formats—consider specialized tools like `ajv` or `jsonschema`. Schema Checker CLI fills the common case of confirming mandatory fields exist before applying config.

## Support

If you find this useful, you can support development: https://www.buymeacoffee.com/poolion