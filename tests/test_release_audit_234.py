from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

from minescript import TARGET_MINECRAFT, __version__
from minescript.version import TARGET_MINECRAFT_ID, USER_AGENT, VERSION
from minescript.seed_worldgen import USER_AGENT as WORLDGEN_USER_AGENT
from minescript.runtime_deps import USER_AGENT as DEPS_USER_AGENT
from minescript.rng_recovery import USER_AGENT as RNG_USER_AGENT
from updater import USER_AGENT as UPDATER_USER_AGENT


ROOT = Path(__file__).resolve().parents[1]


class ReleaseAudit234Tests(unittest.TestCase):
    def test_runtime_version_is_234_everywhere_authoritative(self):
        self.assertEqual(VERSION, "2.3.4")
        self.assertEqual(__version__, VERSION)
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], VERSION)

    def test_target_version_has_one_authoritative_value(self):
        self.assertEqual(TARGET_MINECRAFT, "26.3 Snapshot 7")
        self.assertEqual(TARGET_MINECRAFT_ID, "26.3-snapshot-7")

    def test_download_clients_use_current_release_identity(self):
        self.assertEqual(USER_AGENT, "F3Plus/2.3.4")
        self.assertEqual(WORLDGEN_USER_AGENT, USER_AGENT)
        self.assertEqual(DEPS_USER_AGENT, USER_AGENT)
        self.assertEqual(RNG_USER_AGENT, USER_AGENT)
        self.assertIn("2.3.4", UPDATER_USER_AGENT)
        self.assertNotIn("1.16", UPDATER_USER_AGENT)
        self.assertNotIn("2.0.0", UPDATER_USER_AGENT)

    def test_platform_launchers_show_current_release(self):
        for relative in ("START_F3PLUS.bat", "START_F3PLUS.sh", "START_F3PLUS.command", "WINDOWS_BOOTSTRAP.ps1"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("2.3.4", text, relative)
            self.assertNotIn("2.0.0", text, relative)

    def test_public_docs_identify_234_and_supported_python_range(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        features = (ROOT / "FEATURES.md").read_text(encoding="utf-8")
        third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
        self.assertIn("# F3+ 2.3.4", readme)
        self.assertIn("# F3+ 2.3.4 Feature Guide", features)
        self.assertIn("3.11 through 3.13", readme)
        self.assertIn("3.11 through 3.13", third_party)
        self.assertNotIn("# F3+ 2.0", readme)
        self.assertNotIn("# F3+ 2.0", features)

    def test_ai_disclosure_required_sentence_is_preserved(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("F3+ was unfortunately developed with generative AI assistance.", readme)

    def test_legacy_release_user_agents_are_absent_from_runtime_sources(self):
        for relative in (
            "updater.py", "minescript/seed_worldgen.py", "minescript/runtime_deps.py", "minescript/rng_recovery.py"
        ):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("F3Plus/2.0.0", text, relative)
            self.assertNotIn("F3Plus/1.16.2", text, relative)


if __name__ == "__main__":
    unittest.main()
