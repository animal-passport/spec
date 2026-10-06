# Changelog

Changes to the Animal Passport format. Within 0.x any part of the format may change; from 1.0,
changes within a major version are additive only.

## 0.1 — draft

The first published draft: the specification text, the JSON Schema and two sample passports.

The format was developed against complete animal histories exported from, and re-imported into,
a production records system. Notable decisions in this version:

- A passport is one zip: `passport.json` at the root and its files under `media/`. An optional
  `summary.pdf` is informative only.
- The data file has three parts: `manifest`, `core` and `records`. The manifest lists every
  record type the sender shared, with its record count.
- Every record carries an opaque `originRef`, kept across transfers so a record is never
  imported twice.
- Measured values are decimal text; amounts are `{value, unit}` with UCUM units where known;
  ratings are `{score, display}`; dose frequencies and meal schedules share one vocabulary.
- Dates are either calendar dates (`…Date`) or local date-times with their UTC offset
  (`…DateTime`).
- Transaction history (acquisitions, dispositions, moves, births and deaths, with the holder
  and owner after each) is included; permits and transfer agreements are not.
- Readers ignore fields and files they do not recognize; system-specific values go in
  `extensions`.
- Signing is not part of 0.1.
