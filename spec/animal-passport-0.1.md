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

| Field | Type | Description |
|---|---|---|
| `specVersion` (required) | `0.1` | The version of this specification the file follows. |
| `transferBatchKey` (required) | UUID | A UUID identifying this package. A reader can use it to refuse importing the same package twice. |
| `exportedDateTime` (required) | [date-time](#dates-and-times) | When the package was written. |
| `exportedBy` | string | The person who exported it, as the source system writes the name. |
| `originSoftware` (required) | [Software](#software) | The system that wrote the file. |
| `holderFacility` | [facility](#facilities) | The facility holding the animal when the passport was written. Expected; absent only when the source does not know it. |
| `ownerFacility` | [facility](#facilities) | The animal's owner, when known. |
| `contents` (required) | array of [ContentsRow](#contentsrow) | One row for every record type the file carries, and for every type the sender chose to share even when it has no records. A record type the sender did not share is absent. |

#### Software

| Field | Type | Description |
|---|---|---|
| `name` (required) | string | The software's name. |
| `version` | string | Its version. |

#### ContentsRow

| Field | Type | Description |
|---|---|---|
| `recordType` (required) | string | The key under `records`, for example `prescriptions`. |
| `recordCount` (required) | integer | How many records of that type the file carries. For a grouped type (`measurements`, `enrichment`, `training`) it counts the `records`, not the configuration beside them. 0 means the type was shared and the animal has none. |

### Core

At least one of `localId` and `gan` is required.

| Field | Type | Description |
|---|---|---|
| `gan` | string | The animal's Global Accession Number, when it has one. At least one of `localId` and `gan` is required. |
| `localId` | string | The holder's local identifier for the animal. At least one of `localId` and `gan` is required. |
| `taxonomy` (required) | [Taxonomy](#taxonomy) | What the animal is. |
| `currentSex` | string | The current sex, as the source writes it (for example `Female`). |
| `birth` | [Birth](#birth) | Birth or hatch. |
| `animalType` | one of `individual`, `group`, `colony` | Whether the record is one animal, a group or a colony. |
| `lifeCycle` | [LifeCycle](#lifecycle) | Life-cycle state. |
| `population` | [population](#numbers) | The current count as males.females.unknown: for an individual `1.0.0`, `0.1.0` or `0.0.1`; for a group or colony, its members. |

#### Taxonomy

| Field | Type | Description |
|---|---|---|
| `common` | string | The common name. |
| `scientificName` (required) | string | The scientific name. |
| `rank` | string | The taxonomic rank of that name (for example `Species`, `Subspecies`). |
| `taxonIds` | array of [TaxonId](#taxonid) | Identifiers in public taxonomic databases. |

#### TaxonId

| Field | Type | Description |
|---|---|---|
| `scheme` (required) | string | The database: `itis` or `gbif`. Other public schemes may be added in later versions. |
| `value` (required) | string | The identifier in that database. |

#### Birth

| Field | Type | Description |
|---|---|---|
| `birthDate` | [date](#dates-and-times) | The best single date of birth or hatch. |
| `birthDateEarliest` | [date](#dates-and-times) or null | The earliest the date can be. Equal to `birthDate` when the date is exact; `null` when there is no lower bound. |
| `birthDateLatest` | [date](#dates-and-times) or null | The latest the date can be; `null` when there is no upper bound. |
| `birthType` | string | For example `Captive born`, `Wild born`. |
| `hybrid` | string | Hybrid status, as the source writes it. |
| `birthInstitution` | [facility](#facilities) | Where the animal was born or hatched. |

#### LifeCycle

| Field | Type | Description |
|---|---|---|
| `current` | string | `live`, `preBirth` or `dead`. A value outside these is shipped as the source holds it. |
| `initial` | string | The state the record began in, with the same values. |

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

### Identity

#### `identifiers`

Names, tags, transponders and other identifiers. The primary identifier is always shipped, even when the sender did not choose this type. An array of records.

| Field | Type | Description |
|---|---|---|
| `primary` | boolean | `true` on the animal's primary identifier, which is always shipped and listed first. Absent on the others. |
| `identifierType` | string | For example `House Name`, `Transponder`, `Flipper Tag`. |
| `value` (required) | string | The identifier itself. |
| `location` | string | Where on the animal it is, for a physical identifier. |
| `recordDateTime` | [date-time](#dates-and-times) | When it was applied or recorded. |
| `removalDateTime` | [date-time](#dates-and-times) | When it was removed. An identifier with a removal date is no longer current. |
| `removalComments` | string |  |
| `comments` | string |  |
| `media` | array of [file name](#media-links) | Photographs of the identifier. On the primary identifier, the identification photo. |

#### `parents`

The animal's parents. An array of records.

| Field | Type | Description |
|---|---|---|
| `parentType` | string | For example `Dam`, `Sire`. |
| `probability` | [decimal](#numbers) | The probability of parentage, 0 to 1, when the source records one. |
| `unknownReason` | one of `undetermined`, `wild` | Why the parent is unknown: `wild` for a wild parent, `undetermined` otherwise. Present only when the parent is not identified. |
| `ids` | array of [ParentId](#parentid) | The parent's identifiers, each with the facility it applies at. |
| `birthDate` | [date](#dates-and-times) | The parent's date of birth. |
| `taxon` | string | The parent's scientific name. |
| `comments` | string |  |

##### ParentId

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `scheme` (required) | one of `local`, `gan` | `local` for a facility's local identifier, `gan` for a Global Accession Number. |
| `role` | one of `source`, `holder`, `owner` | `source`: the identifier at the exporting facility; `holder` or `owner`: at the parent's holder or owner. |
| `facility` | [facility](#facilities) | The facility the identifier belongs to. |
| `value` (required) | string | The identifier. |

#### `populations`

For a group or colony, the current count by life stage. An array.

A count by life stage, for a group or colony. Derived at the source, so it carries no `originRef`.

| Field | Type | Description |
|---|---|---|
| `lifeStage` | string | For example `Adult`, `Juvenile`. |
| `population` (required) | [population](#numbers) | The count as males.females.unknown. |
| `extensions` | [extensions](#extensions) |  |

#### `rearings`

How the animal was reared. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `rearingType` (required) | string | For example `Hand`, `Parent`. |
| `comments` | string |  |

#### `sexHistory`

Sex determinations over time. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the sex was determined or recorded. |
| `sex` (required) | string | The sex, as the source writes it. |
| `comments` | string |  |

### Medical

#### `anesthesias`

Anesthesia and immobilization records. An array of records.

| Field | Type | Description |
|---|---|---|
| `number` | string | The source's anesthesia number. |
| `year` | string |  |
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `reason` | string |  |
| `anesthetist` | string |  |
| `primaryVet` | string |  |
| `recorder` | string |  |
| `health` | string |  |
| `physicalStatus` | string | For example an ASA-style class. |
| `activityLevel` | string |  |
| `demeanor` | string |  |
| `bodyCondition` | string |  |
| `fastingFood` | string |  |
| `fastingWater` | string |  |
| `socialConditions` | string |  |
| `immobilizationConditions` | string |  |
| `operantConditioning` | boolean or null | Whether trained behavior was used. |
| `environmentTemperature` | [amount](#amounts-and-units) |  |
| `waterTemperature` | [amount](#amounts-and-units) |  |
| `waterType` | string |  |
| `gasAnestheticCircuit` | string |  |
| `vitalsMonitor` | string |  |
| `bpCuff` | [BpCuff](#bpcuff) |  |
| `endotrachealTube` | string |  |
| `endotrachealTubeComments` | string |  |
| `inductionRating` | [rating](#ratings) |  |
| `recoveryRating` | [rating](#ratings) |  |
| `overallRating` | [rating](#ratings) |  |
| `restraintStartDateTime` | [date-time](#dates-and-times) |  |
| `initialEffectDateTime` | [date-time](#dates-and-times) |  |
| `recumbentDateTime` | [date-time](#dates-and-times) |  |
| `intubatedDateTime` | [date-time](#dates-and-times) |  |
| `extubatedDateTime` | [date-time](#dates-and-times) |  |
| `restraintEndDateTime` | [date-time](#dates-and-times) |  |
| `approvedDateTime` | [date-time](#dates-and-times) |  |
| `weightRef` | [ref](#references-between-records) | The `originRef` of the measurement set holding the weight used. |
| `estimatedWeightRef` | [ref](#references-between-records) | The same, for an estimated weight. |
| `monitoredTypes` | array of string | What was monitored, for example `Heart Rate`. The readings themselves are physiological readings with an `anesthesiaRef`. |
| `anesthetics` | array of [Anesthetic](#anesthetic) |  |
| `catheters` | array of [Catheter](#catheter) |  |
| `complications` | array of [Complication](#complication) |  |
| `effectObservations` | array of [EffectObservation](#effectobservation) |  |
| `recoveryObservations` | array of [RecoveryObservation](#recoveryobservation) |  |
| `summary` | string |  |
| `comments` | string |  |

##### BpCuff

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `size` | string |  |
| `location` | string |  |

##### Anesthetic

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `givenDateTime` | [date-time](#dates-and-times) |  |
| `delivery` | string | For example `Hand Syringe`, `Dart`. |
| `deliverySite` | string |  |
| `injectionRoute` | string |  |
| `needle` | [Needle](#needle) |  |
| `remoteDelivery` | [RemoteDelivery](#remotedelivery) |  |
| `animalWeight` | [amount](#amounts-and-units) | The weight the doses were calculated for. |
| `drugUse` | array of [DrugUse](#druguse) |  |
| `comments` | string |  |

##### Needle

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `length` | [amount](#amounts-and-units) |  |
| `gauge` | string |  |

##### RemoteDelivery

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `system` | string |  |
| `dartType` | string |  |
| `dartCharge` | string |  |
| `powerSetting` | string |  |
| `metersToAnimal` | [decimal](#numbers) |  |
| `percentDelivered` | [decimal](#numbers) |  |

##### Catheter

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `catheterType` | string |  |
| `length` | [amount](#amounts-and-units) |  |
| `gauge` | string |  |
| `location` | string |  |
| `comments` | string |  |

##### Complication

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `complication` (required) | string |  |
| `level` | string |  |
| `comments` | string |  |

##### EffectObservation

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `stage` | string |  |

##### RecoveryObservation

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `stage` | string |  |
| `comments` | string |  |

#### `cases`

Veterinary cases. Clinical notes refer to them with `caseRef`. An array of records.

| Field | Type | Description |
|---|---|---|
| `caseNumber` | string | The source's case number. |
| `caseYear` | string | The year the case number belongs to. |
| `caseType` | string | For example `Clinical`, `Preshipment`. |
| `status` | one of `open`, `closed` | An open case is still being worked at the sending facility. |
| `openedDateTime` | [date-time](#dates-and-times) |  |
| `closedDateTime` | [date-time](#dates-and-times) |  |
| `primaryVet` | string |  |
| `complaint` | string |  |
| `workingDiagnosis` | string |  |
| `finalDiagnosis` | array of string | The final diagnoses. |
| `finalDiagnosisText` | string | Free-text final diagnosis. |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `chronicConditions`

Long-term conditions and their reviews. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the condition was recorded. |
| `condition` | string | The condition. Expected, though some sources hold conditions recorded without a name. |
| `status` | string | For example `Active`, `Closed`, `Unmonitored`. |
| `detailedDescription` | string |  |
| `reviews` | array of [ConditionReview](#conditionreview) |  |

##### ConditionReview

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `reviewDateTime` | [date-time](#dates-and-times) |  |
| `rating` | [rating](#ratings) | How the condition was judged at the review, for example better, same or worse. |
| `comments` | string |  |
| `action` | string | What was decided. |

#### `clinicalNotes`

Veterinary notes. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `category` | string |  |
| `caseRef` | [ref](#references-between-records) | The `originRef` of the case the note belongs to, when it belongs to one. |
| `noteText` (required) | [text](#text) | The note. Records embedded in a note travel inside it; see [Text](#text). |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `digitalImaging`

Radiographs and other diagnostic images. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDate` | [date](#dates-and-times) |  |
| `description` | string |  |
| `diagnosis` | string |  |
| `comments` | string |  |
| `slide` | string |  |
| `fileNumber` | string |  |
| `equipmentId` | string |  |
| `otherId` | string |  |
| `externalId` | string | An identifier in an external imaging system. |
| `media` | array of [file name](#media-links) | The image files. |

#### `drugReactions`

Adverse drug reactions. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the reaction was recorded. |
| `drug` (required) | [Drug](#drug) |  |
| `reactionLevel` | string | For example `Mild`, `Severe`, `Fatal`. |
| `comments` | string |  |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `labCollections`

Sample collections, samples, tests and findings. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the samples were collected. |
| `collectionReason` | string |  |
| `fasting` | string |  |
| `restraintType` | string |  |
| `activityLevel` | string |  |
| `healthStatus` | string |  |
| `collectedBy` | string |  |
| `comments` | string |  |
| `samples` | array of [LabSample](#labsample) |  |
| `animals` | [animals](#records-covering-several-animals) |  |

##### LabSample

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `sampleId` | string | The source's sample identifier. |
| `sampleType` | string |  |
| `sampleSite` | string |  |
| `quantity` | [amount](#amounts-and-units) |  |
| `typical` | boolean or null | Whether the sample is considered typical of the animal. |
| `storedOnly` | boolean | `true` when the sample was stored rather than tested. |
| `tests` | array of [LabTest](#labtest) |  |

##### LabTest

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `lab` | string |  |
| `testMethod` | string |  |
| `labLocalId` | string | The lab's own reference. |
| `currentStatus` | string | The test's status as the source names it. |
| `statuses` | array of [LabStatus](#labstatus) | Each stage the test reached, in order. |
| `findings` | array of [LabFinding](#labfinding) |  |
| `textResults` | string |  |
| `finalDiagnosis` | string |  |
| `comments` | string |  |

##### LabStatus

Not a record, so it carries no `originRef`.

| Field | Type | Description |
|---|---|---|
| `status` (required) | one of `requested`, `sentOut`, `resultsIn`, `approved` |  |
| `by` | string |  |
| `dateTime` | [date-time](#dates-and-times) |  |

##### LabFinding

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `finding` (required) | string | What was measured, for example `WBC`. |
| `result` | [amount](#amounts-and-units) | The result. Its value may be text where the result is not a number, for example `1+`. |
| `reference` | [Reference](#reference) | The reference range the source holds for this finding and taxon. |

##### Reference

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `mean` | [decimal](#numbers) |  |
| `low` | [decimal](#numbers) |  |
| `high` | [decimal](#numbers) |  |

#### `medicalAlerts`

Alerts for people working with the animal. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the alert was created. |
| `alertLevel` | string | For example `Extreme`, `High`, `Medium`, `Low`. |
| `alertText` (required) | string |  |
| `closedDateTime` | [date-time](#dates-and-times) | When the alert was closed. An alert without one is open. |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `necropsies`

Post-mortem examinations. An array of records.

| Field | Type | Description |
|---|---|---|
| `necropsyNumber` | string |  |
| `necropsyYear` | string |  |
| `recordDate` | [date](#dates-and-times) | When the necropsy was performed. |
| `deathTransactionRef` | [ref](#references-between-records) | The `originRef` of the death transaction. |
| `performedBy` | string |  |
| `staff` | array of [person](#people) | Everyone involved, one person per entry. |
| `approvedDateTime` | [date-time](#dates-and-times) |  |
| `finalDiagnoses` | array of string |  |
| `noteText` | [text](#text) | The diagnosis and every findings section, each section under an `<h3>` heading. |
| `grossNecropsy` | string | Gross findings recorded as a single text, where the source keeps one. |
| `histopathology` | [Histopathology](#histopathology) |  |
| `labTestRefs` | array of [ref](#references-between-records) | The `originRef`s of related lab tests. |
| `measurementRefs` | array of [ref](#references-between-records) | The `originRef`s of related measurement sets. |
| `media` | array of [file name](#media-links) |  |

##### Histopathology

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `lab` | string |  |
| `labNumber` | string |  |
| `performedBy` | string |  |
| `approvedDateTime` | [date-time](#dates-and-times) |  |
| `noteText` | [text](#text) | The diagnosis, comments and each section, under `<h3>` headings. |

#### `prescriptions`

Prescriptions, drugs and doses. An array of records.

| Field | Type | Description |
|---|---|---|
| `status` | one of `prescribed`, `dispensed`, `closed` | `prescribed`: written and not yet dispensed; `dispensed`: being given; `closed`: ended. |
| `recordDateTime` | [date-time](#dates-and-times) | When it was prescribed. |
| `treatmentStartDate` | [date](#dates-and-times) | When treatment starts. |
| `treatmentEndDate` | [date](#dates-and-times) | When treatment ends, if it has an end. |
| `prescribedBy` | string |  |
| `route` | string | For example `orally`, `ophthalmic`. |
| `instructions` | string |  |
| `deliveryComments` | string |  |
| `anesthesiaRef` | [ref](#references-between-records) | The `originRef` of the anesthesia the prescription belongs to, when it does. |
| `drugUse` | array of [DrugUse](#druguse) | The drugs prescribed. |
| `animals` | [animals](#records-covering-several-animals) |  |

##### DrugUse

One drug within a prescription or an anesthetic, and its doses.

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `drug` | [Drug](#drug) | The drug, when the source names one. |
| `prescriptionType` | string | For example `Supplement`, `Preventive`. |
| `anestheticType` | string | Within an anesthetic, for example `Preanesthetic`. |
| `doses` | array of [Dose](#dose) |  |

##### Drug

A drug. Not a record, so it carries no `originRef`.

At least one of `name`, `genericName` and `shortName` is required.

| Field | Type | Description |
|---|---|---|
| `name` | string | The drug's full name as the source writes it. At least one of `name`, `genericName` and `shortName` is present. |
| `shortName` | string |  |
| `genericName` | string |  |
| `concentration` | [Concentration](#concentration) |  |

##### Concentration

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `value` | [decimal](#numbers) | The amount of drug in one unit of the delivery form. |
| `unit` | string | The unit of that amount (UCUM where known). |
| `description` | string | The concentration as the source describes it, for example `100 mg tablet`. |
| `deliveryForm` | string | The form the drug is given in, for example `Tablet`, `mL`. |

##### Dose

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `doseRate` | [rate](#amounts-and-units) | The dose per unit of body weight, for example 5 mg per kg. |
| `drugAmount` | [amount](#amounts-and-units) | The amount of drug in one dose. |
| `dose` | [amount](#amounts-and-units) | The dose in the delivery form, for example 1 Tablet. Its unit is the delivery form as the source writes it, which in 0.1 is not necessarily a UCUM unit. |
| `administration` | one of `apply`, `give` | `apply` for a topical application, `give` otherwise. Absent when unknown. |
| `frequency` | [schedule](#schedules) | How often the dose is given. |
| `duration` | [duration](#schedules) | How long it continues. |

### Husbandry

#### `contraceptions`

Contraception. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDate` | [date](#dates-and-times) | When it started. |
| `contraceptionType` | string |  |
| `status` | one of `active`, `inactive` | `active` while it has no removal date. |
| `permanent` | boolean or null |  |
| `removalDate` | [date](#dates-and-times) |  |
| `removalComments` | string |  |
| `comments` | string |  |

#### `diets`

Diets, meal by meal. An array of records.

| Field | Type | Description |
|---|---|---|
| `name` | string |  |
| `startDate` | [date](#dates-and-times) |  |
| `endDate` | [date](#dates-and-times) |  |
| `discontinuedReason` | string |  |
| `fedIndividually` | boolean or null |  |
| `batchDiet` | boolean or null |  |
| `energyGoal` | [rate](#amounts-and-units) | The energy goal, for example 50 kcal per kg. `perUnit` is absent when the goal is a plain amount. |
| `comments` | string |  |
| `meals` | array of [Meal](#meal) |  |
| `animals` | [animals](#records-covering-several-animals) |  |

##### Meal

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `name` | string |  |
| `schedule` | [schedule](#schedules) | When the meal is fed. |
| `items` | array of [MealItem](#mealitem) |  |

##### MealItem

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `feedItem` (required) | string |  |
| `quantity` | [amount](#amounts-and-units) |  |
| `unitEquivalent` | [amount](#amounts-and-units) | For a quantity in a custom unit, the size of one unit, for example 1 `Medium` = 40 g. |
| `feedingMethod` | string |  |
| `description` | string |  |

#### `enrichment`

Enrichment processes and records. An object.

| Field | Type | Description |
|---|---|---|
| `processes` | array of [EnrichmentProcess](#enrichmentprocess) | The enrichment processes the records refer to. |
| `records` | array of [EnrichmentRecord](#enrichmentrecord) |  |

##### EnrichmentProcess

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `name` | string | The process's name. |
| `summary` | string | A one-line description of the process (for example its status, taxa and goals) as the source composes it. Informative, for display only. |
| `goalRatingLabels` | array of string | The labels of the process's goal rating scale, in order. |
| `levelRatingLabels` | array of string | The labels of its level rating scale, in order. |

##### EnrichmentRecord

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `processRef` | [ref](#references-between-records) | The `originRef` of the process. |
| `process` | string | The process's name. |
| `levelRating` | [rating](#ratings) |  |
| `duration` | [amount](#amounts-and-units) |  |
| `foodUsed` | boolean or null |  |
| `onExhibit` | boolean or null |  |
| `recordedBy` | string |  |
| `comments` | string |  |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `feedings`

Feeding records. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `items` | array of [FeedingItem](#feedingitem) |  |
| `appetite` | string |  |
| `comments` | string |  |
| `animals` | [animals](#records-covering-several-animals) |  |

##### FeedingItem

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `feedItem` (required) | string |  |
| `offered` | [amount](#amounts-and-units) |  |
| `consumed` | [amount](#amounts-and-units) |  |
| `offeredEnergy` | [amount](#amounts-and-units) |  |
| `consumedEnergy` | [amount](#amounts-and-units) |  |
| `unitEquivalent` | [amount](#amounts-and-units) |  |
| `feedingMethod` | string |  |
| `description` | string |  |

#### `measurements`

Measurement ranges and measurements. An object.

| Field | Type | Description |
|---|---|---|
| `ranges` | array of [MeasurementRange](#measurementrange) | The animal's acceptable and goal ranges. |
| `records` | array of [MeasurementSet](#measurementset) | The measurements, grouped in sets taken together. |

##### MeasurementRange

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `measureCode` (required) | [MeasureCode](#measurecode) |  |
| `startDate` | [date](#dates-and-times) | When the range took effect. |
| `acceptable` | [range](#amounts-and-units) |  |
| `goal` | [range](#amounts-and-units) |  |
| `unit` | string | The unit of both ranges. |
| `comments` | string |  |

##### MeasureCode

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `description` (required) | string | What is measured, for example `Weight`. |
| `unitType` | string | The kind of unit, for example `Weight`, `Length`. |

##### MeasurementSet

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `measurements` | array of [Measurement](#measurement) |  |

##### Measurement

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `measureCode` (required) | [MeasureCode](#measurecode) |  |
| `quantity` (required) | [amount](#amounts-and-units) |  |
| `estimated` | boolean or null |  |
| `method` | string |  |
| `comments` | string |  |

#### `nutritionNotes`

Nutrition notes. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `category` | string |  |
| `noteText` (required) | [text](#text) |  |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `physiologicalReadings`

Physiological readings such as heart rate. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `anesthesiaRef` | [ref](#references-between-records) | The `originRef` of the anesthesia the readings were taken during, when they were. |
| `details` | array of [PhysiologicalDetail](#physiologicaldetail) |  |

##### PhysiologicalDetail

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `type` (required) | string | For example `Heart Rate`. |
| `result` | [amount](#amounts-and-units) |  |

### Welfare and behavior

#### `actionPlans`

Action plans. An array of records.

| Field | Type | Description |
|---|---|---|
| `referenceNumber` | string |  |
| `category` | string |  |
| `priority` | string |  |
| `status` | one of `unsubmitted`, `pending`, `approved`, `inProgress`, `completed`, `canceled` | Where the plan stands. |
| `statusDate` | [date](#dates-and-times) |  |
| `startDate` | [date](#dates-and-times) |  |
| `completionDate` | [date](#dates-and-times) |  |
| `reason` | string |  |
| `description` | string |  |
| `notes` | array of [ActionPlanNote](#actionplannote) | The plan's log of comments. |
| `media` | array of [file name](#media-links) |  |
| `animals` | [animals](#records-covering-several-animals) |  |

##### ActionPlanNote

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `noteText` (required) | [text](#text) |  |
| `automated` | boolean | `true` for an entry the source system wrote itself. |

#### `animalNotes`

General notes about the animal. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `category` | string | The note's category, as the source names it. |
| `noteText` (required) | [text](#text) | The note. See [Text](#text). |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `observations`

Observations. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `observationType` (required) | string | For example `Body Condition`. |
| `value` | [rating](#ratings) | The observed value and its label. |
| `observedBy` | string |  |
| `duration` | [amount](#amounts-and-units) |  |
| `comments` | string |  |
| `animals` | [animals](#records-covering-several-animals) |  |

#### `welfareAssessments`

Welfare assessments. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `protocol` | string | The assessment protocol used. |
| `calculationMethod` | string | How the overall score was calculated. |
| `score` | [decimal](#numbers) | The overall score. |
| `questions` | array of [WelfareQuestion](#welfarequestion) | Each question answered. A question left unanswered and without comment is omitted. |
| `animals` | [animals](#records-covering-several-animals) |  |

##### WelfareQuestion

Part of its assessment, so it carries no `originRef`.

| Field | Type | Description |
|---|---|---|
| `question` (required) | string |  |
| `answer` | [rating](#ratings) |  |
| `comments` | string |  |

### Training

#### `training`

Trained behaviors and training sessions. An object.

| Field | Type | Description |
|---|---|---|
| `behaviors` | array of [TrainingBehavior](#trainingbehavior) |  |
| `records` | array of [TrainingSession](#trainingsession) | The training sessions. |

##### TrainingBehavior

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `name` (required) | string |  |
| `behaviorGoal` | string |  |
| `approvalStatus` | string |  |
| `audioCue` | string |  |
| `visualCue` | string |  |
| `tactileCue` | string |  |
| `primaryReinforcement` | string |  |
| `completedBehaviorDescription` | string |  |
| `resources` | string |  |
| `schedule` | [TrainingSchedule](#trainingschedule) |  |

##### TrainingSchedule

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `timePerSession` | [amount](#amounts-and-units) |  |
| `sessionsPerDay` | [decimal](#numbers) |  |
| `daysPerWeek` | [decimal](#numbers) |  |

##### TrainingSession

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) |  |
| `sessionRating` | [rating](#ratings) |  |
| `duration` | [amount](#amounts-and-units) |  |
| `trainers` | array of [person](#people) | The trainers, one person per entry. |
| `comments` | string |  |
| `sessionBehaviors` | array of [SessionBehavior](#sessionbehavior) |  |
| `undesirableBehavior` | [UndesirableBehavior](#undesirablebehavior) |  |

##### SessionBehavior

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `behaviorRef` | [ref](#references-between-records) | The `originRef` of the behavior. |
| `behavior` | string | The behavior's name. |
| `responseRating` | [rating](#ratings) |  |
| `progressToGoal` | [decimal](#numbers) | Percent. |
| `comments` | string |  |

##### UndesirableBehavior

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `description` | string |  |
| `comments` | string |  |

### Transaction history

#### `transactions`

Acquisitions, dispositions, moves, births and deaths. An array of records.

| Field | Type | Description |
|---|---|---|
| `recordDateTime` | [date-time](#dates-and-times) | When the transaction took place. |
| `transactionType` (required) | [TransactionType](#transactiontype) | What kind of transaction it was. |
| `enclosureName` | string | The enclosure involved, by name. |
| `population` | array of [TransactionPopulation](#transactionpopulation) | The animals the transaction involves, by life stage. See TransactionPopulation. |
| `ownerAfterTransaction` | [facility](#facilities) | The owner after the transaction. |
| `holderAfterTransaction` | [facility](#facilities) | The holder after the transaction. |
| `geo` | [Geo](#geo) | Where it happened, for a transaction outside a facility such as a wild capture or stranding. |
| `death` | [Death](#death) | Death details, on a death. |
| `rescue` | [Rescue](#rescue) | Rescue and stranding details. |
| `comments` | string |  |

##### TransactionType

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `description` (required) | string | The transaction type as the source names it (for example `Move Animal`, `Death`). |
| `category` | string | The broad category the type belongs to (for example `Acquisition`, `Disposition`, `Death`, `Move Animal`), so a reader can act on types it does not recognize. |

##### TransactionPopulation

The animals a transaction involves in one life stage, as males.females.unknown: for a death or a move, how many; for a life-stage change, the change in each stage, so a count may be negative (`0.-1.0` in one stage and `0.1.0` in the next).

*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.

| Field | Type | Description |
|---|---|---|
| `lifeStage` | string |  |
| `population` (required) | [population](#numbers), counts may be negative |  |

##### Geo

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `description` | string | The place, described. |
| `city` | string |  |
| `county` | string |  |
| `state` | string |  |
| `country` | string |  |
| `bodyOfWater` | string |  |
| `latitude` | [decimal](#numbers) | Decimal degrees. |
| `longitude` | [decimal](#numbers) | Decimal degrees. |
| `latLonType` | string | How the position was taken, for example `GPS`. |
| `latLonEstimated` | boolean or null |  |
| `depth` | [amount](#amounts-and-units) |  |
| `airTemperature` | [amount](#amounts-and-units) |  |
| `waterTemperature` | [amount](#amounts-and-units) |  |
| `weather` | string |  |

##### Death

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `submittedDateTime` | [date-time](#dates-and-times) | When the death record was submitted. |
| `submittedBy` | string |  |
| `history` | string | The clinical history leading to the death. |
| `carcassCondition` | string |  |
| `deathType` | string | For example `Euthanasia`, `Found dead`. |
| `euthanasiaMethod` | string |  |
| `ageAtDeathDays` | [decimal](#numbers) | Age at death in days, as the source recorded it. |
| `ageCategory` | string |  |
| `inZooSinceDate` | [date](#dates-and-times) | When the animal arrived at the facility where it died. |
| `acquisitionTransactionRef` | [ref](#references-between-records) | The `originRef` of the transaction by which that facility acquired the animal. |
| `acquisitionInstitution` | [facility](#facilities) | The facility it was acquired from. |
| `environmentNote` | string |  |
| `exhibitStatus` | string |  |
| `medicalStatus` | string |  |
| `deathCode` | string | The source's own death code. |

##### Rescue

Details of a rescue or stranding response. They can include the name, telephone and address of a member of the public; a sender should share them only where that is appropriate.

*Not a record:* part of the record that contains it, with no `originRef` of its own.

| Field | Type | Description |
|---|---|---|
| `eventConfirmed` | boolean or null | Whether the stranding or rescue was confirmed. |
| `confirmation` | string |  |
| `observerName` | string |  |
| `observerPhone` | string |  |
| `observerAddress` | string |  |
| `reportDate` | [date](#dates-and-times) |  |
| `animalConditionAtReport` | string |  |
| `weatherConditionAtReport` | string |  |
| `animalConditionAtRescue` | string |  |
| `fisheryInteraction` | string |  |
| `fisheryInteractionDetails` | string |  |
| `boatStrike` | string |  |
| `boatStrikeDetails` | string |  |
| `humanInteraction` | string |  |
| `humanInteractionDetails` | string |  |
| `gearList` | string |  |
| `gearDescriptionList` | string |  |
| `potGear` | string |  |
| `gillnetGear` | string |  |
| `otherGear` | string |  |
| `line1Diameter` | [amount](#amounts-and-units) |  |
| `line1DiameterEstimated` | boolean or null |  |
| `line1Type` | string |  |
| `line1Color` | string |  |
| `line2Diameter` | [amount](#amounts-and-units) |  |
| `line2DiameterEstimated` | boolean or null |  |
| `line2Type` | string |  |
| `line2Color` | string |  |
| `line3Diameter` | [amount](#amounts-and-units) |  |
| `line3DiameterEstimated` | boolean or null |  |
| `line3Type` | string |  |
| `line3Color` | string |  |
| `floatBuoys` | string |  |
| `buoyPotId` | string |  |
| `gearCollected` | boolean or null |  |
| `gearCollectedDetails` | string |  |
| `gearRemoved` | boolean or null |  |
| `gearRemovedDetails` | string |  |
| `typeOfHook` | string |  |
| `locationOfHook` | string |  |
| `lineAttached` | boolean or null |  |
| `leaderLineAttached` | boolean or null |  |
| `surgeryNecessary` | boolean or null |  |
| `causeOfStranding` | string |  |
| `strandingType` | string |  |
| `ageCategory` | string |  |

### Media

#### `media`

The files in the package. An array of records.

| Field | Type | Description |
|---|---|---|
| `fileName` (required) | string | The file's name in the package's `media/` folder, without the folder. Records refer to the file by this name. |
| `mediaType` | string | The IANA media type, for example `image/jpeg`. |
| `sha256` | string or null | The lowercase hexadecimal SHA-256 of the file; `null` when the writer could not include the file. |
| `description` | string |  |
| `credits` | string |  |
| `fileDateTime` | [date-time](#dates-and-times) | When the file was created or taken. |

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
