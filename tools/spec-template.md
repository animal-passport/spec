# Animal Passport — specification, version 0.1

**Status:** draft. Version 0.1 may still change as other systems review and implement it.
Version 1.0 will be declared when a second, independent records system reads or writes
passports and the specification has been reviewed by a group of registrars, veterinary staff and developers of other records systems in which no single vendor holds a majority. From 1.0, changes within a major version are
additive only.

**Schema:** [`schema/0.1/passport.schema.json`](../schema/0.1/passport.schema.json). Its `$id`
is `https://animalpassport.org/schema/0.1/passport.schema.json`, where it will be served.

**Examples:** [`examples/`](../examples/) — two invented animals that together carry
almost every field defined here.

---

## 1. Introduction

When an animal moves between facilities, its records must move with it. AZA accreditation
standard 1.4.12 requires an animal's complete records, including history from previous
holding institutions, to accompany it on transfer, preferably in a computer-readable format,
and the receiving facility needs that history to continue the animal's care.

Animal Passport is a file format for those records. A sending system writes a passport for
one animal, containing the record types the sending facility chooses to share; any
receiving system can read it, import what it can store, and show the rest.

### 1.1 Scope

A passport carries the records that should accompany an animal at the time of its transfer:
identity, medical, husbandry, welfare and behavior, training, transaction history and media.

Animal Passport is **not**:

- a records system, a live synchronization between facilities, or a backup;
- a standard for the values within a record. It does not define diagnosis names,
  observation types, feed items or other option lists; each value arrives as the sending
  system recorded it;
- a container for permits or transfer agreements. These vary too much between facilities to
  standardize, and stay with the facilities involved.

How a passport travels (email, a shared drive, a transfer portal) is outside this
specification. Signing is not part of version 0.1.

### 1.2 Conformance

The key words MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are to be interpreted as described
in RFC 2119.

A **writer** is software that produces passports; a **reader** is software that opens them,
whether to import them or to display them. A conforming writer produces packages as described
in sections 2 to 5 and 7, and a `passport.json` that is valid against the schema. A
conforming reader follows section 6.

---

## 2. The package

A passport is a single zip file containing:

| Path | Required | Content |
|---|---|---|
| `passport.json` | yes | The data file, at the root of the zip. The record. |
| `media/<fileName>` | as referenced | Every file a record in `passport.json` refers to, under its `fileName`. |
| `summary.pdf` | no | A human-readable summary. Informative only (see below). |

- `passport.json` MUST be UTF-8 encoded JSON.
- Every file named in the `media` record type, and every file a record refers to, MUST be in
  `media/` under exactly that name, unless the writer could not obtain it, in which case its
  `sha256` is `null`.
- A writer SHOULD produce a zip even when there are no media files, so that every passport
  has the same shape. A reader SHOULD also accept a bare `passport.json`.
- `summary.pdf`, if present, is a convenience for a person without passport software. It is
  not part of the record: `passport.json` is authoritative, and a reader MAY ignore the
  summary.
- A reader MUST ignore any other file in the zip, and MUST NOT write any entry outside the
  folder it extracts to (an entry name containing `..` or an absolute path is refused).

---

## 3. The data file

```json
{
  "$schema": "https://animalpassport.org/schema/0.1/passport.schema.json",
  "animalPassport": {
    "manifest": { ... },
    "core": { ... },
    "records": { ... }
  }
}
```

- `$schema` names the schema the file follows.
- `manifest` describes the file: version, package key, who wrote it and what it contains.
- `core` identifies the animal. It is always present.
- `records` holds the records, by record type. Every record type is optional.

---

## 4. Conventions

These apply throughout the file.

### Unknown fields and files

A reader MUST ignore fields it does not recognize, at any level, and files in the package it
does not recognize. This is what lets a reader for one version open a file written for a
later one.

### extensions

Any object MAY carry an `extensions` object holding values only the writing system
understands, under a namespace named for that system:

```json
"extensions": { "examplerecords": { "taxonKey": "PHOVIT" } }
```

A reader ignores namespaces it does not know. A writer SHOULD put system-specific values in
`extensions` rather than adding fields of its own beside the defined ones.

### Empty values

A field with no value is omitted, not written as `null`, `""` or `[]`. In particular:

- a **tri-state boolean** (shown as "boolean or null") is `true` or `false` when the source
  recorded an answer; `null` or an absent field both mean it recorded none;
- a record type the sender chose to share but for which the animal has no records is listed
  in the manifest with `recordCount: 0` and has no key under `records` — except a grouped type
  (`measurements`, `enrichment`, `training`), which may still carry its configuration (ranges,
  processes, behaviors) with no `records`;
- a record with nothing to say is left out rather than written empty: a note with no text, an
  identifier with no value.

A zero is a value, not an empty: `"0.0000"` is written.

### Dates and times

There are two kinds, and a field's name says which:

- A **date** is `YYYY-MM-DD`. It is a calendar date and is never shifted between time zones.
  Fields holding one end in `Date` (`startDate`, `birthDate`, `recordDate`).
- A **date-time** is ISO 8601 local date and time, to the second, with its UTC offset:
  `2026-08-18T13:34:37-10:00`. The offset travels; the time-zone name does not. Fields
  holding one end in `DateTime` (`recordDateTime`, `closedDateTime`).

Two fields are named otherwise: `birthDateEarliest` and `birthDateLatest` are dates, and a
lab test stage's `dateTime` is a date-time.

A record's own date is `recordDateTime`, or `recordDate` for the few record types whose source
holds a date only. It is expected, but a record MAY lack one where the source holds none (an
animal's origin transaction, for example). A date-time holding midnight is still a date-time.

### Numbers

- **Measured values** — quantities, results, scores, durations — are written as decimal
  text (`"61.4000"`), so no precision is lost to floating point. A writer SHOULD write the
  value as its source holds it.
- **Counts** — manifest counts, schedule counts, the number of animals a record covers — are
  JSON numbers. A count the source stores as a measured value (a training behavior's sessions
  per day and days per week) is decimal text like other measured values.
- A **population** is a count written as `males.females.unknown`, for example `"1.0.2"`.

### Amounts and units

A measured amount is an object:

```json
{ "value": "5.0000", "unit": "mg" }
```

- `unit` is a [UCUM](https://ucum.org) code wherever the writer knows the equivalent (`mg`,
  `mL`, `kg`, `Cel`, `[lb_av]`, `mg/dL`). UCUM is case-sensitive. Otherwise it is the
  source's own spelling (`cells/hpf`, `Tablet`).
- A **rate** adds `perUnit`: `{ "value": "5.0000", "unit": "mg", "perUnit": "kg" }` is 5 mg
  per kg.
- A **range** is `{ "low": "...", "high": "..." }`.

### Ratings

A rating is the source's score and its label:

```json
{ "score": "4", "display": "Above average" }
```

Either half MAY be absent. The score is the value the source stores; the label is what a
person reads. A reader comparing ratings across systems should use the label, since scales
differ.

### Text

`noteText` and other text fields marked as text hold either HTML or plain text; the reader
decides which from the content. A reader that displays HTML MUST sanitize it first.

A record embedded in a note — a prescription or lab test shown inline in a clinical note, for
example — is written into the note as an element:

```html
<div data-record="prescription" data-ref="prescription.4412"> ...the record, as text... </div>
```

- `data-record` names the kind of record: `prescription`, `measurement`, `labTest`,
  `labSample`, `digitalImaging`, `anesthesia`, `media`, `identifier`, or `record` when the
  writer has no more specific name.
- `data-ref` is the embedded record's `originRef`. A writer MUST include it only when that
  record is also in the file, so a reader can link to it.

### People

A person is written as a string, as the source writes the name (`"Okafor, Grace"`). People
are not identified across systems. In a list of people (`trainers`, `staff`), each entry is
one person.

A field naming who performed an action is `<action>By` (`prescribedBy`, `collectedBy`); a
field naming who held a role is the role (`primaryVet`, `anesthetist`).

### Facilities

A facility is an object:

```json
{ "institutionCode": "900101", "mnemonic": "GULLSTON", "name": "Gullstone Bay Aquarium" }
```

At least one of the three is present. A writer SHOULD give the `name`; `institutionCode` and
`mnemonic` are given when known.

### audit

`audit` records when a record was created and by whom: the creation date-time, one space,
then the creator's name as the source writes it.

```json
"audit": "2026-09-20T09:52:18-07:00 Okafor, Grace"
```

### originRef

Every record, and every nested record within one, leads with `originRef`: its identity in the
system that first recorded it, for example `prescription.4412`.

- An `originRef` is **opaque**. A reader MUST compare it only for equality and MUST NOT parse
  it.
- An `originRef` is unique within the system that recorded the record, not across systems.
  A record's identity is therefore the pair: the facility that recorded it — its `recordedAt`,
  or the manifest's `holderFacility` when it has none — and its `originRef`. Two records in one
  file may share an `originRef` if they were recorded at different facilities.
- A writer MUST keep a record's `originRef`, and its `recordedAt`, when that record arrived in
  an earlier passport, and write them back out unchanged, so that the record keeps one identity
  across a chain of transfers. A reader SHOULD use that identity to avoid importing the same
  record twice.

### recordedAt

A record MAY carry `recordedAt`, a [facility](#facilities), naming where it was recorded when
that is not the exporting holder. It is absent for records the holder made itself. A writer
re-exporting a record that came from an earlier passport SHOULD write the facility it came
from.

### References between records

A field ending in `Ref` holds another record's `originRef` (`caseRef`, `anesthesiaRef`,
`deathTransactionRef`); a field ending in `Refs` holds several. Where the referenced thing has
a name, the name is written beside the reference (`processRef` with `process`), so a reader
that does not resolve the reference can still show it.

The referenced record is not always in the file: its record type may not have been shared, or
it may belong to another animal — an anesthesia or a training behavior recorded for a group, or
the transaction by which a group was acquired. A reader MUST NOT treat an unresolved reference
as an error.

### Media links

A record refers to a file by its `fileName`, in a `media` array (`"media": ["4180.jpg"]`).
The file is in the package at `media/<fileName>`, and the `media` record type describes it. A
file travels whenever a record that refers to it does.

### Records covering several animals

A record that covers more than one animal — a group feeding, a diet for several animals —
carries `animals`:

```json
"animals": { "count": 3, "localIds": ["PV-17-02", "PV-15-01", "PV-15-04"] }
```

`count` is how many animals the record covers; `localIds` lists up to ten of their local
identifiers, the passport's own animal first. A record covering only this animal carries no
`animals`.

### Schedules

Dose frequencies and diet meals share one schedule vocabulary:

| `pattern` | Other fields | Meaning |
|---|---|---|
| `everyHours` | `every` | Every *n* hours |
| `everyDays` | `every` | Every *n* days |
| `everyWeeks` | `every`, `weekDays` | Every *n* weeks, on the given days |
| `everyMonths` | `every`, and `monthDay`, or `monthWeek` with `weekDay` | Every *n* months, on a day of the month or, for example, the second Saturday |
| `timesPerDay` | `times` | *n* times a day |
| `timesPerWeek` | `times`, optional `every`, optional `weekDays` | *n* times a week (or every *n* weeks) |
| `timesPerMonth` | `times`, optional `every` | *n* times a month (or every *n* months) |
| `fixedDates` | `dates` | On the listed dates |
| `asNeeded` | | As needed |
| `singleDose` | | Once |
| `notScheduled` | | Not scheduled |

- `every`, `times` and `monthDay` are JSON numbers. `monthWeek` is `first`, `second`,
  `third`, `fourth` or `last`.
- Day names are `Monday` to `Sunday`.
- A meal schedule MAY also carry `timeOfDay` (as the source writes it) and `firstDate`.

A dose's **duration** is either `{ "value": "7", "unit": "days" }`, with `unit` one of
`days`, `doses` or `weeks`, or `{ "untilFurtherNotice": true }`.

### Values from option lists

A value chosen from a list in the source system — a sex, a birth type, a diagnosis, an
observation type — is written as the source's description of it (`"Captive born"`), never as
a code. A value the source could not match to its list is written as the source holds it.

Values this specification defines are camelCase tokens (`open`, `inProgress`, `sentOut`) and
are listed with each field.

---

## 5. Manifest and core

### Manifest

{{MANIFEST}}

### Core

{{CORE}}

---

## 6. Reading a passport

This section is guidance for readers, and is normative where it says MUST.

- A reader MUST check `manifest.specVersion` and SHOULD refuse, or warn about, a version it
  was not written for.
- A reader MUST ignore unknown fields and files, and MUST NOT parse `originRef`.
- A reader importing records SHOULD use `manifest.transferBatchKey` to refuse a package it has
  already imported, and each record's identity (its facility and `originRef`, see
  [originRef](#originref)) to skip records it already holds.
- A reader SHOULD treat the facilities in the file as the sender's, and match them to its own
  only deliberately.
- A reader SHOULD NOT treat open items from the sending facility — an open case, an active
  medical alert, a current prescription — as open work at the receiving facility without a
  person deciding so.
- A reader SHOULD check each media file against its `sha256`.
- A reader displaying `noteText` as HTML MUST sanitize it.
- A reader SHOULD show, rather than drop, fields and record types it cannot import, so that
  nothing in the file is silently lost.

---

## 7. Record types

Every record type under `records` is optional. The manifest's `contents` lists the types the
sender shared. Record types are grouped below by kind.

Every top-level record carries `originRef` (required) and may carry `recordedAt`, `audit` and
`extensions`; these are not repeated in each table. Nested objects are marked as either *a
record* — with its own `originRef` — or *not a record*, which is part of the record that
contains it.

{{RECORDS}}

---

## 8. Versioning

- `manifest.specVersion` is `0.1` for this version.
- Within 0.x, any part of the format may change. Changes are recorded in
  [`CHANGELOG.md`](../CHANGELOG.md).
- Version 1.0 will be declared when a second, independent records system reads or writes
  passports and the specification has been reviewed by a group of registrars, veterinary staff and developers of other records systems in which no single vendor holds a majority. From 1.0, changes within a
  major version are additive only: new optional fields and record types may be added, and
  readers ignore what they do not recognize. A change that removes or redefines a field
  requires a new major version.

---

## Licence

The text of this specification is licensed under CC BY 4.0, including its sources in
`tools/` (the prose in `spec-template.md` and the field descriptions in `spec_model.py`). The
schema, the examples and the code are licensed under Apache 2.0.
