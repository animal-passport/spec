"""
Validate passport.json files against the 0.1 schema.

    python tools/validate.py                      # the examples
    python tools/validate.py path/to/passport.json [...]

Needs the jsonschema package (pip install jsonschema). Exits non-zero if any file is invalid.
"""
import glob, json, os, sys

from jsonschema import Draft202012Validator

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)

with open(os.path.join(REPO, 'schema', '0.1', 'passport.schema.json'), encoding='utf-8') as f:
    schema = json.load(f)
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)

files = sys.argv[1:] or sorted(glob.glob(os.path.join(REPO, 'examples', '*.json')))
failed = 0
for path in files:
    with open(path, encoding='utf-8') as f:
        errors = list(validator.iter_errors(json.load(f)))
    print(f'{os.path.relpath(path, REPO)}: {"valid" if not errors else f"{len(errors)} error(s)"}')
    for e in errors[:20]:
        where = '/'.join(str(p) for p in e.absolute_path)
        print(f'    {where}: {e.message}')
    failed += bool(errors)
sys.exit(1 if failed else 0)
