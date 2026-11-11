"""Run collection sanity checks with a Python 3.12 controller."""

import os
import shutil
from pathlib import Path

import nox
from antsibull_nox.sessions import prepare_collections


@nox.session(python="3.12")
def certification_sanity(session):
    branch = os.environ["SANITY_BRANCH"]
    collection_root = (
        Path(os.environ["GITHUB_WORKSPACE"]) / os.environ["COLLECTION_ROOT"]
    ).resolve()
    results = Path(os.environ["RUNNER_TEMP"]) / "certification-sanity-results"
    session.install(f"https://github.com/ansible/ansible/archive/{branch}.tar.gz")
    with session.chdir(collection_root):
        prepared = prepare_collections(
            session,
            ansible_core_version=branch.removeprefix("stable-"),
            install_in_site_packages=False,
            install_out_of_tree=True,
            extra_collections=os.environ["COLLECTION_DEPS"].split(),
        )
    if prepared is None:
        session.error("Collection preparation failed")
    try:
        with session.chdir(prepared.current_path):
            session.run(
                "ansible-test",
                "sanity",
                "--controller",
                "docker:default,python=3.12",
                "--junit",
                "-v",
                "--color",
                "yes",
            )
    finally:
        output = prepared.current_path / "tests" / "output"
        if output.is_dir():
            shutil.copytree(output, results, dirs_exist_ok=True)
