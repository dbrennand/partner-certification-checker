"""Exercise the standalone Nox driver without starting containers or using Galaxy."""

import importlib.util
import os
import unittest
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch


DRIVER = Path(__file__).resolve().parents[2] / ".github/scripts/certification_noxfile.py"


class SanityRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("certification_noxfile", DRIVER)
        cls.driver = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.driver)

    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.workspace = self.root / "workspace"
        self.collection = self.workspace / "nested" / "collection"
        self.collection.mkdir(parents=True)
        self.prepared = self.root / "prepared" / "ansible_collections" / "test" / "sample"
        self.output = self.prepared / "tests" / "output" / "junit"
        self.output.mkdir(parents=True)
        (self.output / "sanity.xml").write_text("<testsuite/>")
        self.env = patch.dict(os.environ, {
            "GITHUB_WORKSPACE": str(self.workspace),
            "RUNNER_TEMP": str(self.root),
            "COLLECTION_ROOT": "nested/collection",
            "COLLECTION_DEPS": "kubernetes.core amazon.aws",
        })
        self.env.start()
        self.addCleanup(self.env.stop)
        self.session = Mock()
        self.current_dir = None

        @contextmanager
        def chdir(path):
            previous = self.current_dir
            self.current_dir = path
            try:
                yield
            finally:
                self.current_dir = previous

        self.session.chdir.side_effect = chdir

    def run_driver(self, prepared=True):
        def prepare(session, **kwargs):
            self.assertEqual(self.current_dir, self.collection)
            self.assertEqual(kwargs["extra_collections"], ["kubernetes.core", "amazon.aws"])
            self.assertFalse(kwargs["install_in_site_packages"])
            self.assertTrue(kwargs["install_out_of_tree"])
            self.assertEqual(
                kwargs["ansible_core_version"], os.environ["SANITY_BRANCH"].removeprefix("stable-")
            )
            return SimpleNamespace(current_path=self.prepared) if prepared else None

        with patch.object(self.driver, "prepare_collections", side_effect=prepare):
            self.driver.certification_sanity(self.session)

    def test_all_branches_pin_controller_without_restricting_targets(self):
        self.assertEqual(self.driver.certification_sanity.python, "3.12")
        for branch in ("stable-2.16", "stable-2.18", "stable-2.20"):
            with self.subTest(branch=branch), patch.dict(os.environ, SANITY_BRANCH=branch):
                self.session.reset_mock()

                def check_command(*args):
                    self.assertEqual(self.current_dir, self.prepared)
                    self.assertEqual(args[:2], ("ansible-test", "sanity"))
                    self.assertEqual(args[args.index("--controller") + 1], "docker:default,python=3.12")
                    for restricted in ("--python", "--target-python", "--docker", "--changed"):
                        self.assertNotIn(restricted, args)

                self.session.run.side_effect = check_command
                self.run_driver()
                self.session.install.assert_called_once_with(
                    f"https://github.com/ansible/ansible/archive/{branch}.tar.gz"
                )
                self.session.run.assert_called_once()

    def test_reports_survive_a_sanity_failure(self):
        self.session.run.side_effect = RuntimeError("sanity failed")
        with patch.dict(os.environ, SANITY_BRANCH="stable-2.20"):
            with self.assertRaisesRegex(RuntimeError, "sanity failed"):
                self.run_driver()
        result = self.root / "certification-sanity-results" / "junit" / "sanity.xml"
        self.assertEqual(result.read_text(), "<testsuite/>")

    def test_missing_collection_prevents_successful_noop(self):
        self.session.error.side_effect = RuntimeError("Collection preparation failed")
        with patch.dict(os.environ, SANITY_BRANCH="stable-2.20"):
            with self.assertRaisesRegex(RuntimeError, "Collection preparation failed"):
                self.run_driver(prepared=False)
        self.session.run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
