# Tools

The field tables in the specification and the JSON Schema are both generated from one
definition of the format, so they cannot drift apart.

| File | What it is |
|---|---|
| `spec_model.py` | The definition: every record type and nested object, field by field — type, whether it is required, and its description. |
| `spec-template.md` | The prose of the specification. The generated tables go in at `{{MANIFEST}}`, `{{CORE}}` and `{{RECORDS}}`. |
| `build.py` | Writes `spec/animal-passport-0.1.md` and `schema/0.1/passport.schema.json`. |
| `validate.py` | Checks passport files against the schema — the examples by default. |

## Changing the format

1. Edit `spec_model.py` (fields) or `spec-template.md` (prose). Never edit the generated
   files directly; the next build overwrites them.
2. Run `python tools/build.py`.
3. Run `python tools/validate.py` (needs `pip install jsonschema`). Update the examples if the
   change affects them.
4. Record the change in `CHANGELOG.md`.

Python 3.9 or later; `build.py` uses only the standard library.
