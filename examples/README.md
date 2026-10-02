# Examples

Two sample passports in draft format 0.1. Everything in them is invented: the animals,
facilities, people, places, numbers and notes. Phone numbers use the fictional 555-01xx
range, and the transponder number uses the 999 test prefix. The taxonomy ids are the
real public ITIS and GBIF ids for *Phoca vitulina*.

| File | What it shows |
|---|---|
| `pebble.json` | Pebble, a living harbor seal. She was born in rehabilitation, released, restranded entangled, and is now held by an aquarium for her owner. Together, the two files carry every field the draft defines. This one has all of them except the fields only a dead animal can have. |
| `skerry.json` | Skerry, Pebble's dam, who has died. Only events and necropsies were chosen, so it shows the event death block, the necropsy with its histopathology, and a manifest that lists only what was sent. The necropsy photo travels with the necropsy, so media is listed too. |

Some of Pebble's records begin with `TP-` and name another facility in `recordedAt`.
They came to her current holder in an earlier passport, and they keep the originRef that
facility gave them. That is how a record keeps its identity across a chain of transfers.

The software that wrote them is invented too. `originSoftware` names a fictitious
`examplerecords`, and its one `extensions` block shows how a writer can carry a value
only it understands. Any software may write its own namespace, and readers ignore
namespaces they do not know.

A real passport is one zip holding `passport.json` and its media files under `media/`, and
optionally a human-readable `summary.pdf` (informative only; `passport.json` is the record).
These samples are the JSON alone, and their `sha256` values are digests of no real file.
`_note` is a comment for readers of the sample, not a format field.

The `$schema` URL does not resolve yet; the JSON Schema for 0.1 is still to be written.
This is a starting point. If something here is wrong or missing for your records, please
open an issue.
