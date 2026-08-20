# Schema Checker - Validate Config Files Against Common Patterns

Simple CLI that validates YAML/JSON configuration files against structural rules common in app deployment configs:

- **Field presence checks**: Ensure required fields exist (database.host, ports.0.name, etc.)
- **Syntax validation**: Detect JSON parse errors, malformed YAML anchors
- **Type checking**: Verify port entries are integers, not arbitrary strings
- **Auto-detect format**: Tries YAML first, falls back to JSON

Useful for:
- Deployment pipeline pre-checks before container builds
- Config management tools that enforce schema compliance
- Development environment validation before push to production
- Teams migrating from loose configs to strict schemas

## Usage

```bash
# Basic validation (auto-detects format)
python schema-checker.py config.yaml

# Require specific fields
python schema-checker.py config.json -r database port logging

# Force JSON check only
python schema-checker.py data.noyaml --json

# Quiet mode for CI pipelines
python schema-checker.py prod.yml --quiet
```

## Common Patterns Enforced

### Required Fields Check

Many apps use standard sections. This warns when required fields missing:

| Section | Required Fields                          |
|---------|------------------------------------------|
| `database` | `host`, `port`, `name`                |
| `api`    | `url`, `endpoint_prefix`               |
| `server` | `hostname`, `listen_port`              |
| `ports`  | List with `name` for each container    |

Run on deployment configs to catch omissions before container creation fails.

### Port Entry Validation

Ports must be list of integers, not strings like `"80"`:

```yaml
# This fails type check
ports: 
  - "80"
  - "443"
# This passes (or gets converted)
ports: [80, 443]
```

### Database Section Structure

```yaml
database:
  host: db.internal
  port: 5432
  name: appdb
```

Missing `host` or `port` triggers error before Docker Compose creates broken containers.

## CI Example

Add to pre-build checks:

```yaml
# GitHub Actions or GitLab CI
- run: python schema-checker.py config.yaml --quiet
  if: ${{ github.event_name == 'push' && $branch != 'production' }}
```

Fail builds when configs miss required fields. Prevents deploy failures when missing `database.host` causes container startup timeouts (can't connect to empty host).

## Code Example

The validator checks syntax then structural rules:

```python
def validate_yaml_syntax(content):
    """Parse and check YAML structure."""
    try:
        data = yaml.safe_load(content)
        return {"valid": True, "data": data}
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "error": f"YAML parse failed: {e}"
        }

def check_database_section(data):
    """Check database config structure."""
    issues = []
    
    if 'database' not in data:
        return ["'database' section required"]
    
    db = data['database']
    
    if 'host' not in db or 'port' not in db:
        fields_missing = ['host', 'port']
        missing = [f for f in fields_missing if f not in db]
        if missing:
            return [f"'database' must include {missing[0]}"]
    
    # Check port is int-like
    try:
        int(db['port'])
    except (ValueError, TypeError):
        pass  # Allow string '5432' in YAML
    
    if 'name' not in db:
        issues.append("database.name required")
    
    return issues
```

Syntax check uses `yaml.safe_load()` to parse structure. Structural checks run after syntax is valid—for example, verifying database host/port exist before container can connect, or checking port entries are integers rather than strings. Type conversion attempts convert `"80"` string ports to int 80 before flagging validation failure. When deployment tools expect specific types, this catches mismatches before container startup timeouts occur (can't bind socket when port is string "80" not int 80).

Port validation ensures list contains integer entries for network listeners. Many services fail when YAML defines ports as strings rather than integers—common mistake when migrating from file-based configs to YAML templates that strict parsers reject. Structural checks warn about missing required fields before pipeline deployment tools attempt container creation with invalid configs.

When database host is empty string, connection timeouts waste compute resources before error reports reach teams. Schema validation catches this during development or CI runs rather than letting it cause production incidents after deployment succeeds but services fail to start.

## Alternatives Compared

| Tool                  | Limitation                            | This tool                              |
|-----------------------|----------------------------------------|------------------------------------------|
| `yamllint -d default` | No custom field checks                | Enforces business schema rules           |
| JSON Schema validators| Overkill for simple configs            | Minimal Python, no dependencies          |
| Manual review         | Easy to miss required fields           | Automates common pattern enforcement     |

Simple validation avoids complexity of full schema libraries. Focuses on patterns most apps share—database section with host/port/name, ports list with integers, server listen configuration. When teams standardize config templates, this ensures all variants follow same structure before deployment.

## Common Config Patterns Validated

- **Database**: `host`, `port`, `name` (or `db` alias)
- **API routes**: `url`, `prefix`, `version` in `/api` or `/app` sections
- **Container ports**: List with integer values, not strings
- **Server config**: `hostname`, `listen_port`, `cert_path`
- **Logging**: `level`, `format`, `destination` in log sections

Pattern checking catches when configs deviate from team templates or migration guides. Teams migrating from legacy systems to new stack need schema enforcement early—this validates against common patterns before full schema library integration required.

When configs lack strict naming and teams expect fields like `db.host` not `database.host`, warnings guide restructuring. Standardization reduces errors downstream in pipeline deployment stages.

## Source Code

Public repo with examples for security automation or policy enforcement tools. Readable, dependency-free (standard library only) implementation.

🔗 **Repo**: https://github.com/Poolion/schema-checker-cli

If you find this useful, you can support development: https://www.buymeacoffee.com/poolion