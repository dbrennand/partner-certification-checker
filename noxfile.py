from __future__ import annotations

import os
import shutil
from pathlib import Path

import nox

CONTAINER_ENGINES = ("podman", "docker")
CHOSEN_CONTAINER_ENGINE = os.environ.get("CONTAINER_ENGINE")
ACTIONLINT_IMAGE = "docker.io/rhysd/actionlint"


def _get_container_engine(session: nox.Session) -> str:
    path: str | None = None
    if CHOSEN_CONTAINER_ENGINE:
        path = shutil.which(CHOSEN_CONTAINER_ENGINE)
        if not path:
            session.error(
                f"CONTAINER_ENGINE {CHOSEN_CONTAINER_ENGINE!r} does not exist!"
            )
        return path
    for engine in CONTAINER_ENGINES:
        if path := shutil.which(engine):
            return path
    session.error(
        f"None of the following container engines were found: {CONTAINER_ENGINES}."
        f" {session.name} requires a container engine installed."
    )


@nox.session
def actionlint(session: nox.Session) -> None:
    """
    Run actionlint to lint Github Actions workflows.
    The actionlint tool is run in a Podman/Docker container.
    """
    engine = _get_container_engine(session)
    session.run_always(engine, "pull", ACTIONLINT_IMAGE, external=True)
    session.run(
        engine,
        "run",
        "--rm",
        # fmt: off
        "--volume", f"{Path.cwd()}:/pwd:z",
        "--workdir", "/pwd",
        # fmt: on
        ACTIONLINT_IMAGE,
        *session.posargs,
        external=True,
    )


@nox.session
def zizmor(session: nox.Session) -> None:
    """
    Run zizmor, a Github Actions security checker
    """
    args: list[str] = list(session.posargs)
    if not any(a.startswith("--persona") for a in args):
        args.append("--persona=regular")
    session.install("zizmor")
    session.run("zizmor", *args, ".github/workflows")


@nox.session
def workflow_tests(session: nox.Session) -> None:
    """Check the sanity driver's controller, target selection, and report handling."""
    session.install("-r", "requirements/sanity.txt")
    session.run("python", "-m", "unittest", "discover", "-s", "tests/workflow", "-v")
