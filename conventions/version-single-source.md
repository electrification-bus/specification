# Version Single Source of Truth

**Status:** DRAFT
**Version:** 0.1
**Date:** 2026-07-11
**Authors:** Don Jackson

## Purpose

A Python package's version tends to be written down in more than one place, and those copies drift. In the eBus Python repositories the version can appear in as many as three places:

1. `[project].version` in `pyproject.toml` (read by modern setuptools, and it becomes the published wheel's metadata),
2. `__version__` in `src/<package>/__init__.py` (importable at runtime, and read by the legacy `setup.py` shim), and
3. the **git tag** `vX.Y.Z` that triggers the publish workflow.

Nothing forces these to agree. A publish workflow that fires on any `v*` tag will happily build and upload a wheel whose metadata disagrees with the tag name; two hand-maintained literals silently diverge the first time someone bumps one and forgets the other.

This convention makes the version have **one source of truth** and adds a release-time guard so a mismatched artifact can never be published. After adopting it, cutting a release is "edit one line, commit, tag, push", and CI refuses to publish if the tag and the packaged version disagree.

## The single source

**`__version__` in `src/<package>/__init__.py` is the one place the version is written.** It is a plain top-level string literal:

```python
__version__ = "0.1.2"
```

Every other consumer reads it rather than repeating it:

- **The modern build** (`pyproject.toml`) reads it via setuptools' dynamic-version support.
- **The legacy build** (`setup.py` shim, for repos that need the Yocto / kirkstone setuptools-59 path) reads it by parsing the same file.
- **The release** is a git tag that must equal `v` + `__version__`, checked by a CI guard before anything is published.

Bump the literal in one place; the tag is the only other thing to get right, and CI enforces that it matches.

### Why a literal, and why in `__init__.py`

setuptools resolves a dynamic `attr:` version by **parsing the module's AST without importing it**, so a simple top-level `__version__ = "..."` assignment resolves at build time even when `__init__.py` also imports subpackages (the imports are not executed during the scan). It only falls back to importing the module (which would require the package's dependencies to be installed in the build environment) if the value cannot be read statically, for example if it is computed from `importlib.metadata` or built with an f-string. **Keep `__version__` a plain string literal** so the static path always applies.

If a particular package's `__init__.py` cannot be statically parsed for the attribute, move the literal into a dependency-free `src/<package>/_version.py` (`__version__ = "..."`), have `__init__.py` do `from ._version import __version__`, and point the `attr:` at `<package>._version.__version__`.

## The three pieces

### 1. `pyproject.toml`: dynamic version from the literal

Declare the version dynamic and tell setuptools to read the attribute:

```toml
[project]
name = "your-package"
# Single source of truth: src/your_package/__init__.py's __version__.
dynamic = ["version"]
# ... (no static `version = "..."` line)

[tool.setuptools.dynamic]
version = {attr = "your_package.__version__"}
```

Remove the static `version = "..."` line from `[project]`; a table cannot declare a field both statically and as dynamic.

### 2. `setup.py`: legacy shim reads the same literal (only if you need the legacy build)

Repos that must build under old setuptools (notably the 59.5.0 pinned in Yocto kirkstone, which predates PEP 621 and ignores `pyproject.toml` metadata) carry a `setup.py` shim. The shim reads `__version__` from `__init__.py` by regex, so the legacy path uses the same source and cannot drift from it:

```python
import re
from pathlib import Path

from setuptools import find_packages, setup

version = re.search(
    r'^__version__ = "([^"]+)"',
    Path("src/your_package/__init__.py").read_text(encoding="utf-8"),
    re.M,
).group(1)

setup(
    name="your-package",
    version=version,
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    entry_points={"console_scripts": ["your-cmd = your_package.cli:main"]},
)
```

Repos with no legacy-build requirement do not need `setup.py` at all; the modern dynamic-version path is enough.

### 3. Publish workflow: guard the tag against the version

The publish workflow triggers on `v*` tags. Add a step, before build, that fails the run if the tag does not equal `v` + `__version__`. It reads the literal by regex (no install, no import needed at that point):

```yaml
      # Refuse to publish an artifact whose version disagrees with the tag.
      - name: Verify tag matches package version
        run: |
          pkg_version="v$(python -c 'import re,pathlib; print(re.search(r"__version__ = \"([^\"]+)\"", pathlib.Path("src/your_package/__init__.py").read_text()).group(1))')"
          echo "tag=${GITHUB_REF_NAME} package=${pkg_version}"
          test "${pkg_version}" = "${GITHUB_REF_NAME}"
```

With this in place the tag and the packaged version can never disagree in a published artifact: a mismatch fails the run before build.

## Applicability

Not every repo needs all three pieces. Pick by the constraints of the repo:

| Repo shape | `__version__` | pyproject | `setup.py` | tag guard |
|---|---|---|---|---|
| Publishes to PyPI **and** must build under Yocto / kirkstone | required (literal) | `dynamic` attr | yes (reads the literal) | yes |
| Publishes to PyPI, modern build only | required (literal) | `dynamic` attr | no | yes |
| Publishes to PyPI, and has only ever had the pyproject literal (no `__init__` copy) | optional: adopt only if you want an importable `__version__` | keep static, or move to `dynamic` attr if you add the literal | no | yes (this is the only real gap) |
| Not published (application, internal tool) | optional | either | no | not applicable |

The last two rows are the minimum-effort cases: a repo that has always kept its version in exactly one place (the pyproject literal) already has a single source; its only exposure is the tag, so it just needs the guard. Adopting `__version__` there is worthwhile only if you also want the version available at runtime (`your_package.__version__`).

### Alternative: tag-derived versioning

A different single-source mechanism derives the version **from the git tag** at build time (`hatch-vcs` / `setuptools-scm`), writing it into a generated `_version.py`. That is the purest form: the tag is the only place the version is written, and there is no literal to bump. It is a fine choice for a modern-only repo. It is **not** compatible with the legacy `setup.py` shim path, however, because the old setuptools build has no tag context and expects a literal, so repos that must build under kirkstone should use the `__version__` literal pattern above rather than tag-derived versioning.

## Releasing

Once a repo has adopted this convention, a release is:

1. Bump `__version__` in `src/<package>/__init__.py` (the only place).
2. Commit it (`git commit -am "release X.Y.Z"`).
3. Tag it to match, `v`-prefixed: `git tag vX.Y.Z`.
4. Push the tag: `git push --tags` (a plain `git push` does not trigger a release).

Pushing a `v*` tag runs the publish workflow: it verifies the tag equals `v$__version__` (a mismatch fails before anything is published), builds the sdist and wheel, and publishes via Trusted Publishing (OIDC, no stored token). Document these steps in the repo's own README under a `## Releasing` section so the process is discoverable where the code lives.

## Adoption workflow

1. **Ensure the literal exists:** add `__version__ = "<current version>"` to `src/<package>/__init__.py` if it is not already there, matching whatever the package currently publishes.
2. **Make pyproject dynamic:** replace `[project].version = "..."` with `dynamic = ["version"]` and add `[tool.setuptools.dynamic] version = {attr = "<package>.__version__"}`.
3. **If the repo has a `setup.py` shim:** confirm it reads `__version__` from `__init__.py` (the regex form above), not a hardcoded literal.
4. **Add the tag guard** to the publish workflow, before the build step.
5. **Verify the build:** run `python -m build` and confirm the sdist and wheel filenames carry the expected version (this exercises the dynamic resolution in an isolated build). Confirm any console entry point still reports the right `--version`.
6. **Document releasing** in the README (`## Releasing`).
7. **Commit** the change; do not bump the version as part of adoption (adopting the convention is not itself a release).

## Reference implementation

`electrification-bus/cta2045-proxy` implements this convention in full (Tier 1: dynamic-attr pyproject, `setup.py` shim reading `__version__`, and the publish-workflow tag guard). Use it as the worked example.

## References

- [cta2045-proxy `pyproject.toml`](https://github.com/electrification-bus/cta2045-proxy/blob/main/pyproject.toml) and [`setup.py`](https://github.com/electrification-bus/cta2045-proxy/blob/main/setup.py) - the dynamic-attr + legacy-shim pair.
- [cta2045-proxy `publish.yml`](https://github.com/electrification-bus/cta2045-proxy/blob/main/.github/workflows/publish.yml) - the tag guard.
- [setuptools: dynamic metadata / `attr:`](https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html#dynamic-metadata) - the static-AST-read behavior this convention relies on.
- [`conventions/README.md`](README.md) - the index of eBus conventions.
