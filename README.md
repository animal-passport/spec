# Animal Passport

An open file format for the records that travel with an animal when it moves between
facilities: identity, medical, husbandry, welfare and behavior, training, transaction history
and media. Any records system can write a passport, and any other can read it.

**Version 0.1 — draft.** Version 0.1 may still change as other systems review and implement
it. Version 1.0 will be declared when a second, independent records system reads or writes
passports and the specification has been reviewed by a group of registrars, veterinary staff and
developers of other records systems in which no single vendor holds a majority.

## Contents

| Path | What it is |
|---|---|
| [`spec/animal-passport-0.1.md`](spec/animal-passport-0.1.md) | The specification: the package, the data file, the conventions, and every record type field by field. |
| [`schema/0.1/passport.schema.json`](schema/0.1/passport.schema.json) | The JSON Schema (draft 2020-12) for `passport.json`. Its `$id` is `https://animalpassport.org/schema/0.1/passport.schema.json`. |
| [`examples/`](examples/) | Two invented sample passports that together carry almost every field the specification defines. |
| [`CHANGELOG.md`](CHANGELOG.md) | Changes between versions. |
| [`tools/`](tools/) | Generates the specification's field tables and the schema from one definition, and validates passports. |

## Validating a passport

Any JSON Schema validator that supports draft 2020-12 can check a `passport.json` against the
schema. The schema accepts fields it does not define, because readers must ignore them; a
writer should put its own values in `extensions`.

## Contributing

Open an issue to report a problem or propose a change, especially where the format does not fit
the records your system holds.

## Licence

- The specification text (`spec/`, and its sources `tools/spec-template.md` and the field
  descriptions in `tools/spec_model.py`) is licensed under
  [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) —
  see [`LICENSE-docs`](LICENSE-docs).
- The schema, examples and any code are licensed under the Apache License 2.0 — see
  [`LICENSE`](LICENSE).
