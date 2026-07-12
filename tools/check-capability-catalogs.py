#!/usr/bin/env python3
"""Enforce the capability-catalog completeness policy.

Every capability is potentially cross-cutting (the same functional aspect can
appear on devices of different types), so every capability MUST have its own
standalone versioned catalog under capabilities/ — its authoritative versioned
home, which downstream `.ebus-spec.json` lockfiles pin and the drift tooling
tracks. The single exception is a *device-defining* capability, intrinsically
bound to one device type (it defines what that device fundamentally is), which
may remain inline in its device model; those are allowlisted below.

This check reads registries/capability-types.md, and fails if any registered
`energy.ebus.capability.*` identifier lacks a capabilities/<name>.md catalog and
is not allowlisted. Its output is the canonicalization backlog.

Usage:
    python3 tools/check-capability-catalogs.py
"""
import io, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Device-defining capabilities: intrinsically bound to a single device type, so
# their one data model is a permanent, reliable versioned home. Keep this list
# short and justified; a capability that ANY device could publish is NOT here.
ALLOWLIST_INLINE = {
    "water-heater",  # the appliance's own setpoint / tank-temperature / operating-mode surface
}

CAP_RE = re.compile(r"`energy\.ebus\.capability\.([a-z0-9-]+)`")


def registered_capabilities():
    text = io.open(os.path.join(REPO, "registries", "capability-types.md"), encoding="utf-8").read()
    # Only the registry rows (lines that start a table row with the identifier).
    return sorted({m.group(1) for line in text.splitlines() if line.startswith("| `energy.ebus.capability.")
                   for m in [CAP_RE.search(line)] if m})


def main():
    caps = registered_capabilities()
    have_catalog = {fn[:-3] for fn in os.listdir(os.path.join(REPO, "capabilities"))
                    if fn.endswith(".md") and fn.upper() != "README.MD"}
    missing = [c for c in caps if c not in have_catalog and c not in ALLOWLIST_INLINE]
    inline_ok = [c for c in caps if c in ALLOWLIST_INLINE]

    print(f"{len(caps)} registered capabilities: {len(have_catalog & set(caps))} catalogued, "
          f"{len(inline_ok)} device-defining (allowlisted), {len(missing)} missing a catalog.")
    if inline_ok:
        print("  device-defining (inline OK): " + ", ".join(inline_ok))
    if missing:
        print("\nMISSING a capabilities/<name>.md catalog (canonicalization backlog):")
        for c in missing:
            print(f"  - {c}")
        print("\nEvery capability needs a versioned catalog (see capabilities/README.md). "
              "Author capabilities/<name>.md, or add a justified device-defining capability to ALLOWLIST_INLINE.")
        sys.exit(1)
    print("All registered capabilities have a catalog (or are allowlisted device-defining).")


if __name__ == "__main__":
    main()
