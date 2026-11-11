# AGENTS.md

This file is intended for AI coding agents. It is kept human-readable so contributors can also use it as a quick-reference guide.

When official documentation is not explicitly provided or it's insufficient, you MUST look up current official documentation for the relevant libraries and technologies.

## What This Project Is

The `partner-certification-checker` repository provides a reusable [GitHub Actions workflow](.github/workflows/certification-reusable.yml) — called via [certification.yml](.github/workflows/certification.yml) — that checks whether an Ansible collection is ready for certification on Red Hat Ansible Automation Hub. It runs [Galaxy importer](https://github.com/ansible/galaxy-importer), [Ansible Lint](https://docs.ansible.com/projects/lint/), and [ansible-test sanity](https://docs.ansible.com/projects/ansible/latest/dev_guide/testing/sanity/index.html) checks against the target collection.

The repository root also contains a minimal Ansible collection (`ansible.certification`, see `galaxy.yml`) plus fixture collections under `tests/fixtures/`. They exist solely to test the certification-checker workflow against real collection content (see `.github/workflows/test-certification-main-branch.yml`) — they are not a shipped product, and their module/plugin content should stay minimal.

## Development Environment

- Linting and security-checking the reusable workflow and calling-workflow YAML themselves is done with [nox](noxfile.py):
  - `nox -e actionlint` — lints `.github/workflows/*.yml` with [actionlint](https://github.com/rhysd/actionlint) (runs in a Podman/Docker container).
  - `nox -e zizmor` — scans `.github/workflows` with [zizmor](https://github.com/woodruffw/zizmor) for GitHub Actions security issues.
  - `nox -e workflow_tests` — tests the standalone antsibull-nox sanity driver without containers or Galaxy access.
  - All three sessions are run in [ci.yaml](.github/workflows/ci.yaml) on every push and PR.
- The checker's own end-to-end coverage is [test-certification-main-branch.yml](.github/workflows/test-certification-main-branch.yml), which calls `certification-reusable.yml` several ways (default ansible-core, `2.18.0`, `2.20.0`, an alternate `collection-root`, and single/multiple `collection-deps`) against the sample and fixture collections. This only runs in GitHub Actions.
- For exact commands and what they cover, see `.agents/skills/run-tests/SKILL.md`.

## Coding Guidelines

- Follow these software development principles: KISS (Keep It Simple, Stupid), DRY (Don't Repeat Yourself), YAGNI (You Aren't Gonna Need It), Separation of Concerns, Composition over Inheritance, and Convention Over Configuration.
- Prioritize code simplicity and readability over flexibility.
- Favor simple, short, and easily testable functions with no side effects over classes. Use classes only when they naturally fit the problem and help avoid boilerplate code while grouping tightly related functionality.
- Use `snake_case` for all variable and parameter names in Python code (e.g. `noxfile.py`, sample module code).
- Third-party GitHub Actions (`uses:`) must be pinned to a full commit SHA with a trailing `# vX.Y.Z` comment (e.g. `actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2`), not a floating tag or branch. Exceptions (e.g. the reusable-workflow call in `certification.yml`, pinned to a release tag) must carry a `# zizmor: ignore[...]` comment explaining why.
- Changes to `.github/workflows/*.yml` or `.github/actions/**` must pass `nox -e actionlint` and `nox -e zizmor` before merging.
- Changes to the sample/fixture collection content (`plugins/`, `tests/fixtures/collection/`) must pass `ansible-lint --profile=production` and ansible-test sanity, matching what the reusable workflow itself checks for consumers.
- Keep each piece of work focused on solving a single, specific issue or task. Do not mix unrelated changes (e.g., a bugfix and an unrelated refactoring) in the same branch or PR.
- Use conventional commit message prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`. Example: `fix(certification-reusable): handle missing collection-root input`.

## Development Conventions

- `version_added` in `DOCUMENTATION` blocks only applies to the sample/fixture collection's module content (`plugins/modules/sample_module.py` and similar) — it is rarely touched and not part of the checker's own behavior.
- Every PR that changes the reusable workflow's behavior (new/changed inputs or outputs, checks it performs, pinned tool versions such as `GALAXY_IMPORTER_VER` or `ANSIBLE_LINT_VER`) needs a changelog fragment in `changelogs/fragments/<something>.yaml`, using one of: `major_changes`, `minor_changes`, `bugfixes`, `breaking_changes`, `deprecated_features`, `removed_features`, `security_fixes`, `known_issues` (see `changelogs/config.yaml`). Every other PR (docs, tests, refactoring, chore, CI tooling) still needs a fragment, but under the `trivial` section instead. Fragments are consumed (deleted) at release time (`keep_fragments: false`).
- Breaking changes (e.g. bumping a pinned tool version in a way that can break partners' `tests/sanity/ignore-*.txt` files) require a major version bump and a porting guide in the changelog fragment — see `RELEASING.md`.
- Tests are required for code changes; see `.agents/skills/run-tests/SKILL.md` for test commands, patterns, and requirements.

## Subagents

Subagent definitions live in `.agents/subagents/`. When a task matches a subagent's trigger conditions, delegate to it.

## Agent Skills

Skills live in `.agents/skills/*/SKILL.md` (YAML frontmatter + instructions). At session start, scan and register all skills. When a request matches a skill's trigger, load and apply it.
