#!/usr/bin/env python3
"""Generate and verify the machine-readable property-definition JSON siblings.

The normative source is the Markdown. Each capability catalog (capabilities/*.md)
gets a co-located capabilities/<name>.json (kind: capability-catalog) generated
from its property tables; each data model (data-models/*.md) will likewise get a
data-models/<name>.json (kind: device-profile). See conventions/property-json.md
for the contract and conventions/schemas/ for the JSON Schemas.

Prose is the single source of truth: the JSON is generated FROM the tables and
inherits the document's **Version:**. `--check` regenerates in memory and fails
if any committed JSON is stale, structurally invalid (against the schema), or
violates a semantic invariant, so the JSON can never silently diverge from the
prose.

Scope: capability catalogs are implemented. Device profiles are the next
increment (their per-property Req overrides live in prose Notes cells and need a
dedicated pass); parse_profile() is stubbed below.

Usage:
    python3 tools/check-property-catalogs.py            # write capabilities/*.json from the prose
    python3 tools/check-property-catalogs.py --check    # exit 1 if any JSON is stale or invalid
"""
import io, json, os, re, sys, importlib.util

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP_DIR = os.path.join(REPO, "capabilities")
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
PROP_REQ_RE = re.compile(r"`([a-z][a-z0-9-]*)`[^.`|]*?\b(MUST|SHOULD|MAY)\b")
ENUM_TOKEN_RE = re.compile(r"`([A-Z][A-Z0-9_]*)`")
RANGE_RE = re.compile(r"\[\s*(-?\d[\d.]*)\s*,\s*(-?\d[\d.]*)\s*\]")
BRACE_RE = re.compile(r"\{([^}]*)\}")

PROP_ID_HEADERS = {"property id", "property id pattern", "property"}


def _load_sibling(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(REPO, "tools", filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ccc = _load_sibling("ccc", "check-capability-catalogs.py")
ALLOWLIST_INLINE = _ccc.ALLOWLIST_INLINE
REGISTERED = set(_ccc.registered_capabilities())


# ---------------------------------------------------------------- markdown tables

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


def tables(md):
    """Yield dicts {headers, rows, section, node, devtype} for every Markdown table.
    node tracks the last `**Node type:**` (a capability); devtype the last `**Type:**`
    (a device type)."""
    lines = md.splitlines()
    section = node = devtype = None
    out = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        h = re.match(r"^#{2,6}\s+(.*)", line)
        if h:
            section = h.group(1).strip()
        m = NODE_RE.search(line)
        if m:
            node = m.group(1)
        m = TYPE_RE.search(line)
        if m:
            devtype = m.group(1)
        if line.lstrip().startswith("|") and i + 1 < n and _is_sep(lines[i + 1]):
            headers = _split_row(line)
            rows = []
            j = i + 2
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append(_split_row(lines[j]))
                j += 1
            out.append({"headers": headers, "rows": rows, "section": section, "node": node, "devtype": devtype})
            i = j
            continue
        i += 1
    return out


def _colmap(headers):
    return {h.strip().lower(): idx for idx, h in enumerate(headers)}


def is_property_table(t):
    """A property-DEFINITION table: a Property-ID column plus a Datatype column."""
    cm = _colmap(t["headers"])
    return bool(cm) and (set(cm) & PROP_ID_HEADERS) and "datatype" in cm


# ---------------------------------------------------------------- field extraction

def _clean(cell):
    return cell.strip().strip("`").strip()


def _unit(cell):
    u = _clean(cell)
    return None if u.lower() in NO_UNIT else u


def _settable(cell):
    v = _clean(cell).lower()
    return bool(v) and v not in {"no", "false"} and v.lower() not in NO_UNIT


def _extract_format(datatype, desc):
    if datatype == "enum":
        seen, toks = set(), []
        for m in ENUM_TOKEN_RE.finditer(desc):
            if m.group(1) not in seen:
                seen.add(m.group(1))
                toks.append(m.group(1))
        return ",".join(toks) if toks else None
    m = RANGE_RE.search(desc)
    if m:
        return f"{m.group(1)}:{m.group(2)}"
    return None


REQ_KEYWORD_RE = re.compile(r"\b(MUST|SHOULD|MAY)\b", re.I)


def _property(cm, row):
    """Build a property dict from a table row and its column map."""
    get = lambda name: row[cm[name]].strip() if name in cm and cm[name] < len(row) else ""
    datatype = _clean(get("datatype")).lower()
    desc = get("description")
    prop = {"datatype": datatype}
    if "req" in cm:
        # A Req cell may carry a conditional qualifier, e.g. "SHOULD (when `capable = true`)".
        # Take the keyword for req; keep any qualifier in the description so nothing is lost.
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
    # canonical key order: datatype, unit, format, settable, req, description
    order = ["datatype", "unit", "format", "settable", "req", "description"]
    return {k: prop[k] for k in order if k in prop}


_KEY_ORDER = ["datatype", "unit", "format", "settable", "req", "description", "expand"]
SAME_DOMAIN_REF_RE = re.compile(r"same[^`]*?(?:domain|as)[^`]*?`([a-z0-9-]+)`", re.I)
SAME_DOMAIN_RE = re.compile(r"same\s+domain", re.I)


def _ordered(p):
    return {k: p[k] for k in _KEY_ORDER if k in p}


def _resolve_same_domain(props):
    """An enum whose Description defers to another property's value set ('same
    value domain as `X`', or a bare 'Same domain.' within a property family)
    inherits that property's format, so it is not left format-less."""
    order = list(props.items())
    for idx, (pid, p) in enumerate(order):
        if p.get("datatype") != "enum" or "format" in p:
            continue
        desc = p.get("description", "")
        m = SAME_DOMAIN_REF_RE.search(desc)
        if m and props.get(m.group(1), {}).get("format"):
            p["format"] = props[m.group(1)]["format"]
        elif SAME_DOMAIN_RE.search(desc):
            # bare "Same domain": nearest prior enum-with-format sharing the last hyphen segment
            seg = pid.rsplit("-", 1)[-1]
            for prev_pid, prev in reversed(order[:idx]):
                if prev.get("datatype") == "enum" and prev.get("format") and prev_pid.rsplit("-", 1)[-1] == seg:
                    p["format"] = prev["format"]
                    break


# ---------------------------------------------------------------- catalog build

def _header(md):
    def g(rx):
        m = rx.search(md)
        return m.group(1) if m else None
    return g(VERSION_RE), g(STATUS_RE), g(DATE_RE)


def _capability_id(md):
    m = NODE_RE.search(md)
    if m:
        return m.group(1)
    m = IDENT_RE.search(md)
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
            # A row is a pattern iff its id carries a {a,b,c}-style placeholder,
            # decided per-row: a "Property ID pattern" table may also list plain ids.
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


# ---------------------------------------------------------------- validation

def _validator(schema_file):
    from jsonschema import Draft202012Validator
    schema = json.load(io.open(os.path.join(SCHEMA_DIR, schema_file), encoding="utf-8"))
    return Draft202012Validator(schema)


def semantic_errors(obj):
    errs, warns = [], []
    cap = (obj.get("capability") or "").rsplit(".", 1)[-1]
    if cap and cap not in REGISTERED and cap not in ALLOWLIST_INLINE:
        errs.append(f"capability '{cap}' is not registered in registries/capability-types.md")
    if not obj.get("version"):
        errs.append("missing Version header")
    everything = list(obj.get("properties", {}).items()) + list(obj.get("property_patterns", {}).items())
    for pid, p in everything:
        dt = p.get("datatype")
        if dt not in HOMIE_DATATYPES:
            errs.append(f"{pid}: datatype '{dt}' not a Homie 5 datatype")
        if "unit" in p and dt not in NUMERIC:
            errs.append(f"{pid}: unit '{p['unit']}' on non-numeric datatype '{dt}'")
        if "req" in p and p["req"] not in REQ:
            errs.append(f"{pid}: req '{p['req']}' not one of MUST/SHOULD/MAY")
        if dt == "enum" and "format" not in p:
            warns.append(f"{pid}: enum without a format (value set not extractable from prose; tabulate it)")
    return errs, warns


def dumps(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


# ---------------------------------------------------------------- device profiles

_CAP_CACHE = {}
_CAP_ORDER = ["catalog", "catalog_version", "reference_direction", "properties",
              "added", "added_patterns", "defines_capability"]
RANK = {"MAY": 0, "SHOULD": 1, "MUST": 2}


def _catalogs():
    """capability -> {members: set of concrete property ids, req: {id: req}, version}."""
    if _CAP_CACHE:
        return _CAP_CACHE
    for path in catalog_paths():
        jp = path[:-3] + ".json"
        if not os.path.exists(jp):
            continue
        d = json.load(io.open(jp, encoding="utf-8"))
        cap = (d.get("capability") or "").rsplit(".", 1)[-1]
        members, reqs = set(), {}
        for pid, p in d.get("properties", {}).items():
            members.add(pid)
            if "req" in p:
                reqs[pid] = p["req"]
        for key, p in d.get("property_patterns", {}).items():
            for tok in p.get("expand", []):
                members.add(re.sub(r"\{[^}]*\}", tok, key))
        _CAP_CACHE[cap] = {"members": members, "req": reqs, "version": d.get("version")}
    return _CAP_CACHE


def is_capability_table(t):
    cm = _colmap(t["headers"])
    return "capability" in cm and ("req" in cm or "required" in cm) and "datatype" not in cm


def is_override_table(t):
    cm = _colmap(t["headers"])
    return bool(set(cm) & PROP_ID_HEADERS) and "req" in cm and "datatype" not in cm


def _ordered_cap(e):
    return {k: e[k] for k in _CAP_ORDER if k in e}


def _reference_direction(md, node):
    if node not in ("meter", "power-flows"):
        return None
    if re.search(r"positive[^.\n]{0,45}(out of the device|discharg\w*|produc\w*|export\w*|deliver\w*)", md, re.I):
        return "positive-out"
    if re.search(r"positive[^.\n]{0,45}(import\w*|to the load|consum\w*)", md, re.I):
        return "positive-in"
    return None


def parse_profile(path):
    md = io.open(path, encoding="utf-8").read()
    version, status, date = _header(md)
    catalogs = _catalogs()
    devtypes = [m.group(1) for m in TYPE_RE.finditer(md)]
    primary = devtypes[0] if devtypes else None
    multi = len(set(devtypes)) > 1
    device_types, caps = {}, {}

    def cap_entry(node):
        e = caps.setdefault(node, {})
        e.setdefault("catalog", f"energy.ebus.capability.{node}")
        if catalogs.get(node, {}).get("version"):
            e.setdefault("catalog_version", catalogs[node]["version"])
        return e

    for t in tables(md):
        cm = _colmap(t["headers"])
        if is_capability_table(t) and t["devtype"]:
            req_key = "req" if "req" in cm else "required"
            pub = {}
            for row in t["rows"]:
                if cm["capability"] >= len(row) or cm[req_key] >= len(row):
                    continue
                capnode = _clean(row[cm["capability"]])
                m = REQ_KEYWORD_RE.search(row[cm[req_key]])
                if capnode and m:
                    pub[capnode] = m.group(1).upper()
            if pub:
                dt = device_types.setdefault(f"energy.ebus.device.{t['devtype']}", {})
                if multi:
                    dt["role"] = "parent" if t["devtype"] == primary else "child"
                dt.setdefault("publishes", {}).update(pub)
        elif is_override_table(t) and t["node"]:
            e, cm_id = cap_entry(t["node"]), next(k for k in ("property id", "property") if k in cm)
            for row in t["rows"]:
                if cm[cm_id] >= len(row) or cm["req"] >= len(row):
                    continue
                pid, m = _clean(row[cm[cm_id]]), REQ_KEYWORD_RE.search(row[cm["req"]])
                if pid and m:
                    e.setdefault("properties", {})[pid] = {"req": m.group(1).upper()}
        elif is_property_table(t) and t["node"]:
            node = t["node"]
            members = catalogs.get(node, {}).get("members", set())
            has_catalog = node in catalogs
            e = cap_entry(node)
            id_key = next(k for k in ("property id pattern", "property id", "property") if k in cm)
            for row in t["rows"]:
                if cm[id_key] >= len(row):
                    continue
                pid = _clean(row[cm[id_key]])
                if not pid:
                    continue
                prop = _property(cm, row)
                brace = BRACE_RE.search(pid)
                if has_catalog and pid in members:
                    if "req" in prop:
                        e.setdefault("properties", {})[pid] = {"req": prop["req"]}
                elif brace:
                    prop["expand"] = [tok.strip() for tok in brace.group(1).split(",") if tok.strip()]
                    e.setdefault("added_patterns", {})[pid] = _ordered(prop)
                else:
                    e.setdefault("added", {})[pid] = _ordered(prop)
            if not has_catalog:
                e["defines_capability"] = True

    for node in list(caps):
        rd = _reference_direction(md, node)
        if rd:
            caps[node]["reference_direction"] = rd

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
    obj["capabilities"] = {k: _ordered_cap(v) for k, v in caps.items()}
    return obj


def semantic_errors_profile(obj):
    errs, warns = [], []
    catalogs = _catalogs()
    if not obj.get("version"):
        errs.append("missing Version header")
    for dtype, dt in obj.get("device_types", {}).items():
        for cap, req in dt.get("publishes", {}).items():
            if req not in REQ:
                errs.append(f"{dtype} publishes {cap} at '{req}', not MUST/SHOULD/MAY")
    for node, e in obj.get("capabilities", {}).items():
        cap = (e.get("catalog") or "").rsplit(".", 1)[-1]
        inline = e.get("defines_capability")
        if not inline and cap not in catalogs and cap not in ALLOWLIST_INLINE:
            errs.append(f"capability '{cap}' has no catalog and is not allowlisted inline")
        members = catalogs.get(cap, {}).get("members", set())
        creq = catalogs.get(cap, {}).get("req", {})
        for pid, ov in e.get("properties", {}).items():
            if members and pid not in members:
                errs.append(f"{node}: override '{pid}' is not a property of catalog {e.get('catalog')}")
            r = ov.get("req")
            if r and pid in creq and RANK[r] < RANK[creq[pid]]:
                errs.append(f"{node}/{pid}: device req {r} loosens catalog req {creq[pid]}")
        for pid in e.get("added", {}):
            if pid in members:
                warns.append(f"{node}: added '{pid}' also exists in the catalog (should it be an override?)")
    return errs, warns


# ---------------------------------------------------------------- driver

def catalog_paths():
    return [os.path.join(CAP_DIR, fn) for fn in sorted(os.listdir(CAP_DIR))
            if fn.endswith(".md") and fn.upper() != "README.MD"]


DM_DIR = os.path.join(REPO, "data-models")
# Device models whose per-device Req is fully tabulated and whose structure the
# profile parser handles. Others (the multi-DER distribution enclosure, and
# models still stating conformance in prose) are added as they are made ready.
PROFILES_READY = {"bess", "circuit"}


def profile_paths():
    return [os.path.join(DM_DIR, f"{stem}.md") for stem in sorted(PROFILES_READY)
            if os.path.exists(os.path.join(DM_DIR, f"{stem}.md"))]


def main():
    check = "--check" in sys.argv
    validators = {"catalog": _validator("property-catalog.schema.json"),
                  "profile": _validator("device-profile.schema.json")}
    stale, invalid, counts, warn_count = [], [], {"catalog": 0, "profile": 0}, 0

    def process(path, kind, parse, sem):
        nonlocal warn_count
        out_path = path[:-3] + ".json"
        rel_json = os.path.relpath(out_path, REPO)
        obj = parse(path)
        errs = [f"schema: {e.message} (at {list(e.path)})" for e in validators[kind].iter_errors(obj)]
        sem_errs, warns = sem(obj)
        for w in warns:
            warn_count += 1
            print(f"  warn  {rel_json}: {w}")
        errs += sem_errs
        if errs:
            invalid.append((rel_json, errs))
            return
        new = dumps(obj)
        if check:
            old = io.open(out_path, encoding="utf-8").read() if os.path.exists(out_path) else None
            if old != new:
                stale.append(rel_json)
        else:
            io.open(out_path, "w", encoding="utf-8").write(new)
        counts[kind] += 1

    # catalogs first: device profiles classify their properties against the catalog JSON
    for path in catalog_paths():
        process(path, "catalog", parse_catalog, semantic_errors)
    for path in profile_paths():
        process(path, "profile", parse_profile, semantic_errors_profile)

    if invalid:
        print("\nINVALID (fix the prose or the generator):")
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
        print(f"{summary} up to date and valid; {warn_count} warning(s).")
    else:
        if invalid:
            sys.exit(1)
        print(f"wrote {summary}; {warn_count} warning(s).")


if __name__ == "__main__":
    main()
