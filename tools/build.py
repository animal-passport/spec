"""
Generate spec/animal-passport-0.1.md and schema/0.1/passport.schema.json from tools/spec_model.py.

    python tools/build.py

The prose of the specification is tools/spec-template.md; the field tables are generated into it
at {{MANIFEST}}, {{CORE}} and {{RECORDS}}. Edit the model or the template, then run this.
"""
import json, os, re, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import spec_model as M

SCHEMA_ID = 'https://animalpassport.org/schema/0.1/passport.schema.json'

DATE = r'^\d{4}-\d{2}-\d{2}$'
DATETIME = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$'
AUDIT = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2}) .+$'
DECIMAL = r'^-?\d+(\.\d+)?$'


def fields_of(name):
    desc, fields = M.DEFS[name]
    if name in M.NOT_RECORDS:
        return fields
    have = {f[0].rstrip('*') for f in fields}
    return [c for c in M.COMMON if c[0].rstrip('*') not in have][:1] + fields + \
           [c for c in M.COMMON[1:] if c[0].rstrip('*') not in have]


def schema_for(t):
    if t.startswith('token:'):
        vals = t[6:].split('|')
        return {'const': vals[0]} if len(vals) == 1 else {'enum': vals}
    if t.startswith('obj:'):
        return {'$ref': f'#/$defs/{t[4:]}'}
    if t.startswith('arr:'):
        return {'type': 'array', 'items': {'$ref': f'#/$defs/{t[4:]}'}}
    return {
        'string': {'type': 'string'},
        'text': {'$ref': '#/$defs/text'},
        'date': {'$ref': '#/$defs/date'},
        'date|null': {'oneOf': [{'$ref': '#/$defs/date'}, {'type': 'null'}]},
        'dateTime': {'$ref': '#/$defs/dateTime'},
        'decimal': {'$ref': '#/$defs/decimal'},
        'integer': {'type': 'integer', 'minimum': 0},
        'boolean': {'type': 'boolean'},
        'bool?': {'type': ['boolean', 'null']},
        'amount': {'$ref': '#/$defs/amount'},
        'rate': {'$ref': '#/$defs/rate'},
        'range': {'$ref': '#/$defs/range'},
        'rating': {'$ref': '#/$defs/rating'},
        'facility': {'$ref': '#/$defs/facility'},
        'ref': {'$ref': '#/$defs/originRef'},
        'refs': {'type': 'array', 'items': {'$ref': '#/$defs/originRef'}},
        'files': {'type': 'array', 'items': {'$ref': '#/$defs/fileName'}},
        'strings': {'type': 'array', 'items': {'type': 'string'}},
        'people': {'type': 'array', 'items': {'type': 'string'}},
        'animals': {'$ref': '#/$defs/animals'},
        'population': {'$ref': '#/$defs/population'},
        'populationChange': {'$ref': '#/$defs/populationChange'},
        'schedule': {'$ref': '#/$defs/schedule'},
        'doseDuration': {'$ref': '#/$defs/doseDuration'},
        'drug': {'$ref': '#/$defs/Drug'},
        'sha256': {'oneOf': [{'type': 'string', 'pattern': '^[0-9a-f]{64}$'}, {'type': 'null'}]},
        'uuid': {'type': 'string', 'pattern': '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'},
        'audit': {'$ref': '#/$defs/audit'},
        'extensions': {'$ref': '#/$defs/extensions'},
    }[t]


def object_schema(name):
    desc, _ = M.DEFS[name]
    props, req = {}, []
    for n, t, d in fields_of(name):
        key = n.rstrip('*')
        s = dict(schema_for(t))
        if d:
            s = {**s, 'description': re.sub(r'\[([^\]]+)\]\(#[^)]+\)', r'\1', d)}
        props[key] = s
        if n.endswith('*'):
            req.append(key)
    out = {'type': 'object'}
    if desc:
        out['description'] = desc
    out['properties'] = props
    if req:
        out['required'] = req
    if name in getattr(M, 'ANY_OF', {}):
        out['anyOf'] = [{'required': r} for r in M.ANY_OF[name]]
    return out


def build_schema():
    defs = {
        'date': {'type': 'string', 'pattern': DATE, 'description': 'A calendar date, YYYY-MM-DD, never shifted between time zones.'},
        'dateTime': {'type': 'string', 'pattern': DATETIME, 'description': 'ISO 8601 local date and time with its UTC offset, for example 2026-08-18T13:34:37-10:00.'},
        'audit': {'type': 'string', 'pattern': AUDIT, 'description': 'The creation date-time, one space, then the creator\'s name as the source writes it.'},
        'decimal': {'type': 'string', 'pattern': DECIMAL, 'description': 'A number written as decimal text, so no precision is lost.'},
        'text': {'type': 'string', 'description': 'HTML or plain text. The reader decides which from the content.'},
        'originRef': {'type': 'string', 'minLength': 1, 'description': 'An opaque record identity. Compare for equality; never parse.'},
        'fileName': {'type': 'string', 'minLength': 1, 'pattern': r'^[^/\\]+$', 'description': 'The name of a file in the package\'s media/ folder.'},
        'population': {'type': 'string', 'pattern': r'^\d+\.\d+\.\d+$', 'description': 'A count as males.females.unknown, for example 1.0.2.'},
        'populationChange': {'type': 'string', 'pattern': r'^-?\d+\.-?\d+\.-?\d+$', 'description': 'Animals involved, as males.females.unknown; a count may be negative where it is a change.'},
        'amount': {'type': 'object', 'description': 'A measured amount. The value is decimal text (text for a non-numeric lab result); the unit is UCUM where the writer knows the code, otherwise the source\'s spelling.',
                   'properties': {'value': {'type': 'string'}, 'unit': {'type': 'string'}}, 'required': ['value']},
        'rate': {'type': 'object', 'description': 'An amount per unit, for example 5 mg per kg.',
                 'properties': {'value': {'type': 'string'}, 'unit': {'type': 'string'}, 'perUnit': {'type': 'string'}}, 'required': ['value']},
        'range': {'type': 'object', 'properties': {'low': {'$ref': '#/$defs/decimal'}, 'high': {'$ref': '#/$defs/decimal'}}},
        'rating': {'type': 'object', 'description': 'A rating: the source\'s score and its label. Either may be absent.',
                   'properties': {'score': {'type': 'string'}, 'display': {'type': 'string'}}, 'anyOf': [{'required': ['score']}, {'required': ['display']}]},
        'facility': {'type': 'object', 'description': 'A facility: its name, and its code and mnemonic when known. At least one of the three is present; the name should be.',
                     'properties': {'institutionCode': {'type': 'string'}, 'mnemonic': {'type': 'string'}, 'name': {'type': 'string'}, 'extensions': {'$ref': '#/$defs/extensions'}},
                     'anyOf': [{'required': ['name']}, {'required': ['mnemonic']}, {'required': ['institutionCode']}]},
        'animals': {'type': 'object', 'description': 'On a record that covers more than one animal: how many, and up to ten of their local identifiers, the exported animal first.',
                    'properties': {'count': {'type': 'integer', 'minimum': 2}, 'localIds': {'type': 'array', 'items': {'type': 'string'}, 'maxItems': 10}},
                    'required': ['count']},
        'extensions': {'type': 'object', 'description': 'Values only the writing system understands, under a namespace named for that system. Readers ignore namespaces they do not know.',
                       'additionalProperties': {'type': 'object'}},
        'weekDay': {'enum': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']},
        'schedule': {
            'type': 'object', 'description': 'A repeating schedule, shared by dose frequencies and diet meals.',
            'properties': {
                'pattern': {'enum': ['everyHours', 'everyDays', 'everyWeeks', 'everyMonths', 'timesPerDay', 'timesPerWeek',
                                     'timesPerMonth', 'fixedDates', 'asNeeded', 'singleDose', 'notScheduled']},
                'every': {'type': 'integer', 'minimum': 1},
                'times': {'type': 'integer', 'minimum': 1},
                'weekDays': {'type': 'array', 'items': {'$ref': '#/$defs/weekDay'}},
                'monthDay': {'type': 'integer', 'minimum': 1, 'maximum': 31},
                'monthWeek': {'enum': ['first', 'second', 'third', 'fourth', 'last']},
                'weekDay': {'$ref': '#/$defs/weekDay'},
                'dates': {'type': 'array', 'items': {'$ref': '#/$defs/date'}},
                'timeOfDay': {'type': 'string'},
                'firstDate': {'$ref': '#/$defs/date'},
            },
            'required': ['pattern'],
        },
        'doseDuration': {
            'description': 'How long a dose continues: a value in days, doses or weeks, or until further notice.',
            'oneOf': [
                {'type': 'object', 'properties': {'value': {'$ref': '#/$defs/decimal'}, 'unit': {'enum': ['days', 'doses', 'weeks']}}, 'required': ['value', 'unit']},
                {'type': 'object', 'properties': {'untilFurtherNotice': {'const': True}}, 'required': ['untilFurtherNotice']},
            ],
        },
    }
    for name in M.DEFS:
        defs[name] = object_schema(name)

    records = {'type': 'object', 'description': 'The records, by record type. Every key is optional.', 'properties': {}}
    for _, types in M.GROUPS:
        for key, kind, d, desc in types:
            records['properties'][key] = ({'type': 'array', 'items': {'$ref': f'#/$defs/{d}'}} if kind == 'arr'
                                          else {'$ref': f'#/$defs/{d}'}) | {'description': desc.replace('`', '')}
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        '$id': SCHEMA_ID,
        'title': 'Animal Passport 0.1',
        'description': 'passport.json in an Animal Passport package. Readers ignore properties they do not recognize, so this schema allows them; a writer should put its own values in extensions.',
        'type': 'object',
        'properties': {
            '$schema': {'type': 'string'},
            'animalPassport': {
                'type': 'object',
                'properties': {
                    'manifest': {'$ref': '#/$defs/Manifest'},
                    'core': {'$ref': '#/$defs/Core'},
                    'records': records,
                },
                'required': ['manifest', 'core', 'records'],
            },
        },
        'required': ['animalPassport'],
        '$defs': defs,
    }


# ---------------- markdown ----------------

TYPE_TEXT = {
    'string': 'string', 'text': '[text](#text)', 'date': '[date](#dates-and-times)', 'date|null': '[date](#dates-and-times) or null',
    'dateTime': '[date-time](#dates-and-times)', 'decimal': '[decimal](#numbers)', 'integer': 'integer', 'boolean': 'boolean',
    'bool?': 'boolean or null', 'amount': '[amount](#amounts-and-units)', 'rate': '[rate](#amounts-and-units)',
    'range': '[range](#amounts-and-units)', 'rating': '[rating](#ratings)', 'facility': '[facility](#facilities)',
    'ref': '[ref](#references-between-records)', 'refs': 'array of [ref](#references-between-records)',
    'files': 'array of [file name](#media-links)', 'strings': 'array of string', 'people': 'array of [person](#people)',
    'animals': '[animals](#records-covering-several-animals)', 'population': '[population](#numbers)',
    'populationChange': '[population](#numbers), counts may be negative',
    'schedule': '[schedule](#schedules)', 'doseDuration': '[duration](#schedules)', 'drug': '[Drug](#drug)',
    'sha256': 'string or null', 'uuid': 'UUID', 'audit': '[audit](#audit)', 'extensions': '[extensions](#extensions)',
}


def anchor(name):
    return name.lower()


ARRAY_ITEMS = {t[4:] for _, fs in M.DEFS.values() for _, t, _ in fs if t.startswith('arr:')}


def type_md(t):
    if t.startswith('token:'):
        vals = t[6:].split('|')
        return f'`{vals[0]}`' if len(vals) == 1 else 'one of ' + ', '.join(f'`{v}`' for v in vals)
    if t.startswith('obj:'):
        return f'[{t[4:]}](#{anchor(t[4:])})'
    if t.startswith('arr:'):
        return f'array of [{t[4:]}](#{anchor(t[4:])})'
    return TYPE_TEXT[t]


def table(name, include_common=False):
    rows = ['| Field | Type | Description |', '|---|---|---|']
    for n, t, d in M.DEFS[name][1]:
        req = n.endswith('*')
        rows.append(f"| `{n.rstrip('*')}`{' (required)' if req else ''} | {type_md(t)} | {d} |")
    return '\n'.join(rows)


def any_of_note(name):
    rules = getattr(M, 'ANY_OF', {}).get(name)
    if not rules:
        return []
    names = [f'`{r[0]}`' for r in rules]
    return [f'At least one of {", ".join(names[:-1])} and {names[-1]} is required.', '']


def def_section(name, level='####', note_record=True):
    desc = M.DEFS[name][0]
    out = [f'{level} {name}', '']
    if desc:
        out += [desc, '']
    if note_record and 'originRef' not in desc:
        if name in M.NOT_RECORDS:
            out += ['*Not a record:* part of the record that contains it, with no `originRef` of its own.', '']
        else:
            out += ['*A record:* it carries its own `originRef` (required) and may carry `recordedAt`, `audit` and `extensions`.', '']
    out += any_of_note(name)
    out += [table(name), '']
    return out


def nested_defs(name, seen):
    """Definitions reachable from name, depth first, each once."""
    order = []
    for _, t, _ in M.DEFS[name][1]:
        for prefix in ('obj:', 'arr:'):
            if t.startswith(prefix):
                child = t[len(prefix):]
                if child not in seen:
                    seen.add(child)
                    order.append(child)
                    order += nested_defs(child, seen)
    return order


def build_record_sections():
    out = []
    seen = {'Drug', 'Concentration', 'DrugUse', 'Dose'}  # documented once, under prescriptions
    for group, types in M.GROUPS:
        out += [f'### {group}', '']
        for key, kind, d, desc in types:
            kind_text = ' An object.' if kind == 'obj' else (' An array.' if d in M.NOT_RECORDS else ' An array of records.')
            out += [f'#### `{key}`', '', desc + kind_text, '']
            if d in M.NOT_RECORDS and M.DEFS[d][0] and kind == 'arr':
                out += [M.DEFS[d][0], '']
            out += [table(d), '']
            if key == 'prescriptions':
                children = ['DrugUse', 'Drug', 'Concentration', 'Dose']
            else:
                children = nested_defs(d, seen)
            for c in children:
                out += def_section(c, level='#####')
    return '\n'.join(out)


def build_envelope_sections():
    out = []
    for name, title in (('Manifest', 'manifest'), ('Core', 'core')):
        out += any_of_note(name) + [table(name), '']
        for c in nested_defs(name, set()):
            out += def_section(c, level='####', note_record=False)
        out += ['@@SPLIT@@']
    return '\n'.join(out).split('@@SPLIT@@')


if __name__ == '__main__':
    schema = build_schema()
    os.makedirs(os.path.join(REPO, 'schema', '0.1'), exist_ok=True)
    with open(os.path.join(REPO, 'schema', '0.1', 'passport.schema.json'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(schema, indent=2, ensure_ascii=False) + '\n')

    manifest_md, core_md, _ = build_envelope_sections()
    parts = {'MANIFEST': manifest_md.strip(), 'CORE': core_md.strip(), 'RECORDS': build_record_sections().strip()}
    with open(os.path.join(TOOLS, 'spec-template.md'), encoding='utf-8') as f:
        tpl = f.read()
    for k, v in parts.items():
        tpl = tpl.replace('{{' + k + '}}', v)
    os.makedirs(os.path.join(REPO, 'spec'), exist_ok=True)
    with open(os.path.join(REPO, 'spec', 'animal-passport-0.1.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(tpl)
    print('wrote spec/animal-passport-0.1.md and schema/0.1/passport.schema.json')
