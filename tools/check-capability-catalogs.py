#!/usr/bin/env python3
"""Enforce two capability-registry invariants.

1. Completeness: every capability is potentially cross-cutting (the same
   functional aspect can appear on devices of different types), so every
   registered capability MUST have its own standalone versioned catalog under
   capabilities/ (its authoritative versioned home, which downstream
   .ebus-spec.json lockfiles pin and the drift tooling tracks). The single
   exception is a *device-defining* capability, intrinsically bound to one
   device type, which may remain inline in its device model; those are
   allowlisted below.

2. Registration: every capability actually *used* (declared as a `**Node type:**`
   in a data model) MUST be registered in registries/capability-types.md, so it
   is visible to the manifest, the lockfiles, and check (1). An unregistered but
   used capability is a silent blind spot.

This check fails if either invariant is violated; its output is the backlog.

Usage:
    python3 tools/check-capability-catalogs.py
"""
import io, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Device-defining capabilities: intrinsically bound to a single device type, so
# their one data model is a permanent, reliable versioned home. Keep short and
# justified; a capability that ANY device could publish is NOT here.
ALLOWLIST_INLINE = {
    "water-heater",  # the appliance's own setpoint / tank-temperature / operating-mode surface
}

CAP_RE = re.compile(r"`energy\.ebus\.capability\.([a-z0-9-]+)`")
NODE_RE = re.compile(r"\*\*Node type:\*\*\s*`energy\.ebus\.capability\.([a-z0-9-]+)`")


def registered_capabilities():
    text = io.open(os.path.join(REPO, "registries", "capability-types.md"), encoding="utf-8").read()
    return sorted({m.group(1) for line in text.splitlines()
                   if line.startswith("| `energy.ebus.capability.")
                   for m in [CAP_RE.search(line)] if m})


def used_capabilities():
    """Capability node types actually declared in the data models."""
    used = {}
    d = os.path.join(REPO, "data-models")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".md"):
            continue
        txt = io.open(os.path.join(d, fn), encoding="utf-8").read()
        for m in NODE_RE.finditer(txt):
            used.setdefault(m.group(1), set()).add(fn[:-3])
    return used


def main():
    caps = registered_capabilities()
    have_catalog = {fn[:-3] for fn in os.listdir(os.path.join(REPO, "capabilities"))
                    if fn.endswith(".md") and fn.upper() != "README.MD"}
    missing = [c for c in caps if c not in have_catalog and c not in ALLOWLIST_INLINE]
    inline_ok = [c for c in caps if c in ALLOWLIST_INLINE]

    used = used_capabilities()
    unregistered = sorted(c for c in used if c not in caps)

    print(f"{len(caps)} registered capabilities: {len(have_catalog & set(caps))} catalogued, "
          f"{len(inline_ok)} device-defining (allowlisted), {len(missing)} missing a catalog. "
          f"{len(used)} used in data models; {len(unregistered)} unregistered.")
    if inline_ok:
        print("  device-defining (inline OK): " + ", ".join(inline_ok))

    fail = False
    if unregistered:
        fail = True
        print("\nUSED but NOT REGISTERED (add a row to registries/capability-types.md):")
        for c in unregistered:
            print(f"  - {c}  (in: {', '.join(sorted(used[c]))})")
    if missing:
        fail = True
        print("\nMISSING a capabilities/<name>.md catalog (canonicalization backlog):")
        for c in missing:
            print(f"  - {c}")
    if fail:
        print("\nEvery capability must be registered and have a versioned catalog "
              "(see capabilities/README.md), unless it is an allowlisted device-defining capability.")
        sys.exit(1)
    print("All used capabilities are registered, and all registered capabilities have a catalog "
          "(or are allowlisted device-defining).")


if __name__ == "__main__":
    main()
