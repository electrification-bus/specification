#!/usr/bin/env python3
"""Generate and verify the machine-readable property-definition JSON siblings.

These artifacts are DESCRIPTIVE, not prescriptive. The framework is permissive by
design (see framework.md Design Principles): properties are MAY by default
(principle 8), a publisher publishes what it has and omits the rest (principle 3),
and a device's Homie 5 `$description` / `$format` is the runtime authority for what
it actually publishes. A publisher may add properties this spec does not list, and
may redefine a property's datatype or enum value set, as long as it advertises the
shape it publishes in `$format` (principles 8 and 10). So:

- capabilities/<name>.json (kind: capability-catalog) is the RECOMMENDED, extensible
  vocabulary for a capability: for each property, how to publish it (datatype, unit,
  the core enum/range `format`, settable) IF you publish it. Datatypes are the
  recommended common case and enum formats are the core set; both are extensible.
- devices/<name>.json (kind: device-profile) is an ADVISORY composition: which
  capabilities each device type in the model typically publishes, and the spec's
  capability-level Req guidance where it states one. It is not an exhaustive or
  required property set; different device types and different OEMs legitimately
  differ.

The Markdown is the single source of truth. The JSON is generated FROM it and
inherits the document's **Version:**. `--check` regenerates in memory and fails if
any committed JSON is stale or structurally invalid (against the JSON Schemas), so
the JSON never silently drifts from the prose. It does NOT force the prose to be
exhaustively tabulated: illustrative prose examples stay prose.

Usage:
    python3 tools/check-property-catalogs.py            # write the JSON from the prose
    python3 tools/check-property-catalogs.py --check    # exit 1 if any JSON is stale or invalid
"""
import io, json, os, re, sys, importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP_DIR = os.path.join(REPO, "capabilities")
DM_DIR = os.path.join(REPO, "devices")
SCHEMA_DIR = os.path.join(REPO, "conventions", "schemas")
SCHEMA_VERSION = "property-schema-v1"

HOMIE_DATATYPES = {"integer", "float", "boolean", "string", "enum", "color", "datetime", "duration", "json"}
NUMERIC = {"integer", "float"}
REQ = {"MUST", "SHOULD", "MAY"}
NO_UNIT = {"", "-", "—", "–", "n/a", "none"}  # em/en dashes read as "no unit"

VERSION_RE = re.compile(r"^\*\*Version:\*\*\s*(\S+)", re.M)
STATUS_RE = re.compile(r"^\*\*Status:\*\*\s*(\w+)", re.M)
DATE_RE = re.compile(r"^\*\*Date:\*\*\s*(\S+)", re.M)
NODE_RE = re.compile(r"\*\*Node type:\*\*\s*`energy\.ebus\.capability\.([a-z0-9-]+)`")
TYPE_RE = re.compile(r"\*\*Type:\*\*\s*`energy\.ebus\.device\.([a-z0-9-]+)`")
IDENT_RE = re.compile(r"`energy\.ebus\.capability\.([a-z0-9-]+)`")
BOLD_NODE_RE = re.compile(r"^\*\*([a-z][a-z0-9-]+):\*\*")
REQ_KEYWORD_RE = re.compile(r"\b(MUST|SHOULD|MAY)\b", re.I)
ENUM_TOKEN_RE = re.compile(r"`([A-Z][A-Z0-9_]*)`")
RANGE_RE = re.compile(r"\[\s*(-?\d[\d.]*)\s*,\s*(-?\d[\d.]*)\s*\]")
BRACE_RE = re.compile(r"\{([^}]*)\}")
SAME_DOMAIN_REF_RE = re.compile(r"same[^`]*?(?:domain|as)[^`]*?`([a-z0-9-]+)`", re.I)
SAME_DOMAIN_RE = re.compile(r"same\s+domain", re.I)

PROP_ID_HEADERS = {"property id", "property id pattern", "property"}


def _load_sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "tools", filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ccc = _load_sibling("ccc", "check-capability-catalogs.py")
ALLOWLIST_INLINE = _ccc.ALLOWLIST_INLINE
REGISTERED = set(_ccc.registered_capabilities())


# ---------------------------------------------------------------- markdown scanning

def _split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def _is_sep(line):
    s = line.strip()
    return "|" in s and "-" in s and set(s) <= set("|:- ")


def _context_node(line):
    """A line that (re)binds the current capability node: a `**Node type:**`, or a bold
    `**<cap>:**` label whose name is a registered capability (the enclosure's per-capability
    markers). Returns the node id or None."""
    m = NODE_RE.search(line)
    if m:
        return m.group(1)
    b = BOLD_NODE_RE.match(line)
    if b and b.group(1) in REGISTERED:
        return b.group(1)
    return None


def tables(md):
    """Yield {headers, rows, section, major, node, devtype} for every Markdown table.
    A level-2 heading resets node+devtype and a `**Type:**` resets node, so stale
    section context never leaks across a document's parts."""
    lines = md.splitlines()
    section = major = node = devtype = None
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        h = re.match(r"^(#{2,6})\s+(.*)", line)
        if h:
            section = h.group(2).strip()
            if len(h.group(1)) == 2:
                major, node, devtype = section, None, None
        else:
            mt = TYPE_RE.search(line)
            if mt:
                devtype, node = mt.group(1), None
            else:
                cn = _context_node(line)
                if cn:
                    node = cn
        if line.lstrip().startswith("|") and i + 1 < n and _is_sep(lines[i + 1]):
            headers = _split_row(line)
            rows = []
            j = i + 2
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append(_split_row(lines[j]))
                j += 1
            out.append({"headers": headers, "rows": rows, "section": section,
                        "major": major, "node": node, "devtype": devtype})
            i = j
            continue
        i += 1
    return out


def node_declarations(md):
    """Yield (node, devtype, major) for every capability declaration (a `**Node type:**`
    or bold `**cap:**` marker), used to attribute capability presence to a device type."""
    major = devtype = None
    for line in md.splitlines():
        h = re.match(r"^(#{2,6})\s+(.*)", line)
        if h:
            if len(h.group(1)) == 2:
                major, devtype = h.group(2).strip(), None
            continue
        mt = TYPE_RE.search(line)
        if mt:
            devtype = mt.group(1)
            continue
        cn = _context_node(line)
        if cn:
            yield cn, devtype, major


def _colmap(headers):
    return {h.strip().lower(): idx for idx, h in enumerate(headers)}


def is_property_table(t):
    """A property-DEFINITION table (capability catalog): Property-ID + Datatype columns."""
    cm = _colmap(t["headers"])
    return bool(cm) and bool(set(cm) & PROP_ID_HEADERS) and "datatype" in cm


def is_capability_table(t):
    """A device model's `| Capability | ... | Req/Required | ... |` composition table."""
    cm = _colmap(t["headers"])
    return "capability" in cm and ("req" in cm or "required" in cm) and "datatype" not in cm


def _header(md):
    def g(rx):
        m = rx.search(md)
        return m.group(1) if m else None
    return g(VERSION_RE), g(STATUS_RE), g(DATE_RE)


# ---------------------------------------------------------------- capability catalogs

def _clean(cell):
    return cell.strip().strip("`").strip()


def _unit(cell):
    u = _clean(cell)
    return None if u.lower() in NO_UNIT else u


def _settable(cell):
    v = _clean(cell).lower()
    return bool(v) and v not in {"no", "false"} and v not in NO_UNIT


def _extract_format(datatype, desc):
    """Lift the RECOMMENDED value domain from the Description: the core enum tokens, or a
    numeric range. A publisher may extend or redefine this and advertise it in `$format`."""
    if datatype == "enum":
        seen, toks = set(), []
        for m in ENUM_TOKEN_RE.finditer(desc):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                toks.append(m.group(1))
        return ",".join(toks) if toks else None
    m = RANGE_RE.search(desc)
    return f"{m.group(1)}:{m.group(2)}" if m else None


_KEY_ORDER = ["datatype", "unit", "format", "settable", "req", "description", "expand"]


def _ordered(p):
    return {k: p[k] for k in _KEY_ORDER if k in p}


def _property(cm, row):
    get = lambda name: row[cm[name]].strip() if name in cm and cm[name] < len(row) else ""
    datatype = _clean(get("datatype")).lower()
    desc = get("description")
    prop = {"datatype": datatype}
    if "req" in cm:
        req_cell = get("req")
        m = REQ_KEYWORD_RE.search(req_cell)
        if m:
            prop["req"] = m.group(1).upper()
            qualifier = (req_cell[:m.start()] + req_cell[m.end():]).strip(" .")
            if qualifier:
                desc = (desc + " " + qualifier).strip() if desc else qualifier
    unit = _unit(get("unit")) if "unit" in cm else None
    if unit:
        prop["unit"] = unit
    fmt = _extract_format(datatype, desc)
    if fmt:
        prop["format"] = fmt
    if "settable" in cm and _settable(get("settable")):
        prop["settable"] = True
    if desc:
        prop["description"] = desc
    return _ordered(prop)


def _resolve_same_domain(props):
    """An enum whose Description defers to another property's value set ('same value domain
    as `X`', or a bare 'Same domain.') inherits that property's recommended format."""
    order = list(props.items())
    for idx, (pid, p) in enumerate(order):
        if p.get("datatype") != "enum" or "format" in p:
            continue
        desc = p.get("description", "")
        m = SAME_DOMAIN_REF_RE.search(desc)
        if m and props.get(m.group(1), {}).get("format"):
            p["format"] = props[m.group(1)]["format"]
        elif SAME_DOMAIN_RE.search(desc):
            seg = pid.rsplit("-", 1)[-1]
            for prev_pid, prev in reversed(order[:idx]):
                if prev.get("datatype") == "enum" and prev.get("format") and prev_pid.rsplit("-", 1)[-1] == seg:
                    p["format"] = prev["format"]
                    break


def _capability_id(md):
    m = NODE_RE.search(md) or IDENT_RE.search(md)
    return m.group(1) if m else None


def parse_catalog(path):
    md = io.open(path, encoding="utf-8").read()
    version, status, date = _header(md)
    cap = _capability_id(md)
    obj = {
        "$schema": "https://ebus.energy/schemas/property-catalog.json",
        "schema_version": SCHEMA_VERSION,
        "kind": "capability-catalog",
        "capability": f"energy.ebus.capability.{cap}" if cap else None,
        "version": version,
    }
    if status:
        obj["status"] = status
    if date:
        obj["date"] = date
    props, patterns = {}, {}
    for t in tables(md):
        if not is_property_table(t):
            continue
        cm = _colmap(t["headers"])
        id_key = next(k for k in ("property id pattern", "property id", "property") if k in cm)
        for row in t["rows"]:
            if cm[id_key] >= len(row):
                continue
            pid = _clean(row[cm[id_key]])
            if not pid:
                continue
            prop = _property(cm, row)
            brace = BRACE_RE.search(pid)
            if brace:
                prop["expand"] = [tok.strip() for tok in brace.group(1).split(",") if tok.strip()]
                patterns[pid] = prop
            else:
                props[pid] = prop
    _resolve_same_domain(props)
    obj["properties"] = {pid: _ordered(p) for pid, p in props.items()}
    if patterns:
        obj["property_patterns"] = {pid: _ordered(p) for pid, p in patterns.items()}
    return obj


def semantic_warnings_catalog(obj):
    """Advisory consistency notes (never fatal): the vocabulary is recommended, not closed."""
    warns = []
    cap = (obj.get("capability") or "").rsplit(".", 1)[-1]
    if cap and cap not in REGISTERED and cap not in ALLOWLIST_INLINE:
        warns.append(f"capability '{cap}' is not registered in registries/capability-types.md")
    for pid, p in list(obj.get("properties", {}).items()) + list(obj.get("property_patterns", {}).items()):
        dt = p.get("datatype")
        if dt not in HOMIE_DATATYPES:
            warns.append(f"{pid}: datatype '{dt}' is not a Homie 5 datatype")
        if "unit" in p and dt not in NUMERIC:
            warns.append(f"{pid}: unit '{p['unit']}' on non-numeric datatype '{dt}'")
        if dt == "enum" and "format" not in p:
            warns.append(f"{pid}: enum has no recommended value set in prose (a publisher advertises its own in $format)")
    return warns


# ---------------------------------------------------------------- device profiles (light, advisory)

_CATALOG_VERSIONS = {}


def _catalog_versions():
    if not _CATALOG_VERSIONS:
        for path in catalog_paths():
            jp = path[:-3] + ".json"
            if os.path.exists(jp):
                d = json.load(io.open(jp, encoding="utf-8"))
                cap = (d.get("capability") or "").rsplit(".", 1)[-1]
                if cap:
                    _CATALOG_VERSIONS[cap] = d.get("version")
    return _CATALOG_VERSIONS


def parse_profile(path):
    """A light, advisory composition: which capabilities each device type composes, and the
    model's capability-level Req guidance where it states one. No property-level detail: how
    to publish each property lives in the capability catalogs, and what a device actually
    publishes is authoritative in its runtime `$description`."""
    md = io.open(path, encoding="utf-8").read()
    version, status, date = _header(md)
    versions = _catalog_versions()
    types = [m.group(1) for m in TYPE_RE.finditer(md)]
    primary = types[0] if types else None
    multi = len(set(types)) > 1
    dts = {}

    def dt(name):
        e = dts.setdefault(name, {"capabilities": {}})
        if multi:
            e.setdefault("role", "parent" if name == primary else "child")
        return e

    def add_cap(target, node, req=None):
        ce = dt(target)["capabilities"].setdefault(node, {})
        ce.setdefault("catalog", f"energy.ebus.capability.{node}")
        if versions.get(node):
            ce.setdefault("catalog_version", versions[node])
        if req and "req" not in ce:
            ce["req"] = req
        return ce

    for name in types:
        dt(name)

    # composition + capability-level Req from the model's Capability/Required tables
    for t in tables(md):
        if is_capability_table(t) and t["devtype"]:
            cm = _colmap(t["headers"])
            rk = "req" if "req" in cm else "required"
            for row in t["rows"]:
                if cm["capability"] >= len(row) or cm[rk] >= len(row):
                    continue
                node = _clean(row[cm["capability"]])
                m = REQ_KEYWORD_RE.search(row[cm[rk]])
                if node:
                    add_cap(t["devtype"], node, m.group(1).upper() if m else None)

    def targets(node, devtype, major):
        # Capabilities documented in a shared "## Capability Node Types" section (the bess
        # convention) attribute to the device type(s) that publish them; elsewhere to the
        # enclosing device type.
        if major == "Capability Node Types":
            if node in dts.get(primary, {}).get("capabilities", {}):
                return [primary]
            pub = [n for n, e in dts.items() if node in e["capabilities"]]
            return pub or ([primary] if primary else [])
        return [devtype] if devtype else []

    # composition (presence) from Node-type / bold-label declarations (device types with no
    # Capability/Required table, e.g. the distribution enclosure, get their set from here)
    for node, devtype, major in node_declarations(md):
        for tt in targets(node, devtype, major):
            add_cap(tt, node)

    device_types = {}
    for name in sorted(dts):
        e = dts[name]
        entry = {"role": e["role"]} if "role" in e else {}
        entry["capabilities"] = {
            n: {k: c[k] for k in ("catalog", "catalog_version", "req") if k in c}
            for n, c in sorted(e["capabilities"].items())
        }
        device_types[f"energy.ebus.device.{name}"] = entry

    obj = {
        "$schema": "https://ebus.energy/schemas/device-profile.json",
        "schema_version": SCHEMA_VERSION,
        "kind": "device-profile",
        "device": f"energy.ebus.device.{primary}" if primary else None,
        "version": version,
    }
    if status:
        obj["status"] = status
    if date:
        obj["date"] = date
    obj["device_types"] = device_types
    return obj


def semantic_warnings_profile(obj):
    warns = []
    for dtype, dt in obj.get("device_types", {}).items():
        for node, ce in dt.get("capabilities", {}).items():
            cap = (ce.get("catalog") or "").rsplit(".", 1)[-1]
            if cap not in REGISTERED and cap not in ALLOWLIST_INLINE:
                warns.append(f"{dtype}: capability '{cap}' is not registered in registries/capability-types.md")
            if ce.get("req") and ce["req"] not in REQ:
                warns.append(f"{dtype}/{node}: req '{ce['req']}' is not MUST/SHOULD/MAY")
    return warns


# ---------------------------------------------------------------- driver

def _validator(schema_file):
    from jsonschema import Draft202012Validator
    return Draft202012Validator(json.load(io.open(os.path.join(SCHEMA_DIR, schema_file), encoding="utf-8")))


def dumps(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


def catalog_paths():
    return [os.path.join(CAP_DIR, fn) for fn in sorted(os.listdir(CAP_DIR))
            if fn.endswith(".md") and fn.upper() != "README.MD"]


# Every data model gets a device profile, EXCEPT proxy.md, which is the proxy-publication
# convention and declares no device type (energy.ebus.device.*), so it has no profile.
# pv / evse / mid join here once those data models are authored.
PROFILES_READY = {"bess", "circuit", "distribution-enclosure", "outlet", "pdu", "utility-meter", "water-heater"}


def profile_paths():
    return [os.path.join(DM_DIR, f"{s}.md") for s in sorted(PROFILES_READY)
            if os.path.exists(os.path.join(DM_DIR, f"{s}.md"))]


def main():
    check = "--check" in sys.argv
    validators = {"catalog": _validator("property-catalog.schema.json"),
                  "profile": _validator("device-profile.schema.json")}
    stale, invalid, counts, warn_count = [], [], {"catalog": 0, "profile": 0}, 0

    def process(path, kind, parse, warn):
        nonlocal warn_count
        out_path = path[:-3] + ".json"
        rel_json = os.path.relpath(out_path, REPO)
        obj = parse(path)
        schema_errs = [f"schema: {e.message} (at {list(e.path)})" for e in validators[kind].iter_errors(obj)]
        for w in warn(obj):
            warn_count += 1
            print(f"  note  {rel_json}: {w}")
        if schema_errs:
            invalid.append((rel_json, schema_errs))
            return
        new = dumps(obj)
        if check:
            old = io.open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else None
            if old != new:
                stale.append(rel_json)
        else:
            io.open(out_path, "w", encoding="utf-8").write(new)
        counts[kind] += 1

    for path in catalog_paths():
        process(path, "catalog", parse_catalog, semantic_warnings_catalog)
    for path in profile_paths():
        process(path, "profile", parse_profile, semantic_warnings_profile)

    if invalid:
        print("\nINVALID (structurally malformed against the schema):")
        for rel_json, errs in invalid:
            print(f"  {rel_json}")
            for e in errs:
                print(f"      {e}")
    summary = f"{counts['catalog']} capability catalog(s) + {counts['profile']} device profile(s)"
    if check:
        if stale:
            print("\nSTALE (run tools/check-property-catalogs.py): " + ", ".join(stale))
        if stale or invalid:
            sys.exit(1)
        print(f"{summary} up to date and valid; {warn_count} advisory note(s).")
    else:
        if invalid:
            sys.exit(1)
        print(f"wrote {summary}; {warn_count} advisory note(s).")


if __name__ == "__main__":
    main()
