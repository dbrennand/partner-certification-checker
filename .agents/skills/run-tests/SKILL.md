---
name: run-tests
description: "This skill should be used to determine which test/lint commands apply to a change in the partner-certification-checker repo — GitHub Actions workflow linting (actionlint, zizmor) or checks against the sample/fixture collection. Use before claiming a change is validated."
---

# Skill: run-tests

Identify the correct commands to validate a change in this repository, and what each one covers. Commands below are transcribed from `noxfile.py`, `.github/workflows/ci.yaml`, and `.github/workflows/certification-reusable.yml` — the authoritative sources.

`nox`, `ansible-test`, and `ansible-core` (and a container engine) are not guaranteed to be installed. Confirm availability before running; if you can't execute a command, say so explicitly and cite the exact command and its source file rather than claiming the change is validated.

## Which commands apply

### Changes to `.github/workflows/*.yml` or `.github/actions/**`

Run both nox sessions defined in `noxfile.py` (also run in `ci.yaml` on every push/PR):

```bash
nox -e actionlint
```
Lints workflow YAML with [actionlint](https://github.com/rhysd/actionlint). Runs inside a Podman/Docker container (`docker.io/rhysd/actionlint`) — requires a container engine.

```bash
nox -e zizmor
```
Installs [zizmor](https://github.com/woodruffw/zizmor) via pip and scans `.github/workflows` for GitHub Actions security issues (unpinned actions, secrets misuse, template injection, etc.).

### Changes to the reusable workflow's behavior (inputs, outputs, checks performed)

Run `nox -e workflow_tests` for local regression checks of the embedded sanity
driver: Python 3.12 controller selection, unrestricted targets, collection root
and dependency forwarding, preparation failure, and report preservation on failure.
These tests mock collection preparation and command execution; they do not run
containers or resolve dependencies. Full workflow validation is end-to-end via
GitHub Actions:

- Push the branch / open a PR to trigger [test-certification-main-branch.yml](../../../.github/workflows/test-certification-main-branch.yml), which calls `certification-reusable.yml` several ways against this repo's own sample and fixture collections:
  - default ansible-core version
  - `ansible-core-version: '2.18.0'`
  - `ansible-core-version: '2.20.0'`
  - `collection-root: 'tests/fixtures/collection'`
  - `collection-deps: 'kubernetes.core'`
  - `collection-deps: 'kubernetes.core amazon.aws ansible.mcp'`
- This is the closest thing to an integration-test suite for the checker and cannot be run locally.

### Changes to the sample/fixture collection (`plugins/`, `tests/fixtures/collection/`)

These mirror what the reusable workflow itself checks for consumers:
- `ansible-lint --profile=production` (config: `.ansible-lint`)
- `ansible-test sanity` against the ansible-core stable branches in the sanity matrix (`stable-2.16`, `stable-2.18`, `stable-2.20`) — run via the `ansible-community/ansible-test-gh-action` in CI, containerized.
- A pytest unit test exists at `tests/unit/plugins/modules/test_sample_module.py`, but **it is not currently wired into any CI workflow in this repo** (`ci.yaml` only runs `actionlint`/`zizmor`; `certification-reusable.yml` only runs build-import, lint, and sanity). Treat this as a known gap — mention it if relevant, but don't silently "fix" it as a side effect of unrelated work.
