from __future__ import annotations

import os
import tomllib
import unittest
from pathlib import Path
from unittest.mock import patch

from minescript import TARGET_MINECRAFT, __version__
from minescript.version import TARGET_MINECRAFT_ID, USER_AGENT, VERSION
from minescript.seed_worldgen import USER_AGENT as WORLDGEN_USER_AGENT
from minescript.runtime_deps import USER_AGENT as DEPS_USER_AGENT
from minescript.rng_recovery import USER_AGENT as RNG_USER_AGENT
from updater import USER_AGENT as UPDATER_USER_AGENT, update_channel

ROOT = Path(__file__).resolve().parents[1]


class ReleaseAudit253Tests(unittest.TestCase):
    def test_runtime_version_is_253_everywhere_authoritative(self):
        self.assertEqual(VERSION, "2.5.3")
        self.assertEqual(__version__, VERSION)
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertEqual(project["project"]["version"], VERSION)

    def test_target_version_has_one_authoritative_value(self):
        self.assertEqual(TARGET_MINECRAFT, "26.3 Snapshot 7")
        self.assertEqual(TARGET_MINECRAFT_ID, "26.3-snapshot-7")

    def test_download_clients_use_current_release_identity(self):
        self.assertEqual(USER_AGENT, "F3Plus/2.5.3")
        self.assertEqual(WORLDGEN_USER_AGENT, USER_AGENT)
        self.assertEqual(DEPS_USER_AGENT, USER_AGENT)
        self.assertEqual(RNG_USER_AGENT, USER_AGENT)
        self.assertIn("2.5.3", UPDATER_USER_AGENT)
        self.assertNotIn("1.16", UPDATER_USER_AGENT)
        self.assertNotIn("2.0.0", UPDATER_USER_AGENT)

    def test_platform_launchers_show_current_release(self):
        for relative in ("START_F3PLUS.bat", "START_F3PLUS.sh", "START_F3PLUS.command", "WINDOWS_BOOTSTRAP.ps1"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("2.5.3", text, relative)
            self.assertNotIn("F3+ 2.4.2", text, relative)

    def test_stable_is_default_update_channel(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("F3PLUS_UPDATE_CHANNEL", None)
            self.assertEqual(update_channel(), ("stable", "stable"))
        with patch.dict(os.environ, {"F3PLUS_UPDATE_CHANNEL": "preview"}):
            self.assertEqual(update_channel(), ("preview", "main"))

    def test_public_docs_describe_current_task_first_product(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        third_party = (ROOT / "THIRD_PARTY.md").read_text(encoding="utf-8")
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# F3+\n"))
        for section in ("Play & Travel", "Explore Worlds", "Plan & Build", "Mechanics & Trading", "App & Safety"):
            self.assertIn(section, readme)
        self.assertIn("Inputs and outputs", readme)
        self.assertIn("Automation and safety", readme)
        self.assertIn("3.11 through 3.13", readme)
        self.assertIn("3.11 through 3.13", third_party)
        self.assertIn("ore", readme.lower())
        self.assertIn("villager", readme.lower())
        self.assertIn("macro studio", readme.lower())
        self.assertIn("world profiles", readme.lower())
        self.assertIn("automation permissions", security.lower())
        self.assertNotIn("historical feature ids", readme.lower())
        self.assertNotIn("compatibility aliases", readme.lower())
        self.assertNotIn("professional desktop shell", readme.lower())

    def test_ai_disclosure_is_neutral_and_does_not_claim_fake_precision(self):
        for relative in ("README.md", "THIRD_PARTY.md"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("AI-assisted development disclosure", text)
            self.assertIn("Generative AI", text)
            self.assertIn("during development", text)
            self.assertNotIn("unfortunately developed", text)
            self.assertNotRegex(text, r"Approximately\s+\d+%.*AI")

    def test_legacy_release_user_agents_are_absent_from_runtime_sources(self):
        for relative in ("updater.py", "minescript/seed_worldgen.py", "minescript/runtime_deps.py", "minescript/rng_recovery.py"):
            text = (ROOT / relative).read_text(encoding="utf-8")
            self.assertNotIn("F3Plus/2.0.0", text, relative)
            self.assertNotIn("F3Plus/1.16.2", text, relative)

    def test_main_launches_canonical_desktop_shell(self):
        text = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("from minescript.desktop import run", text)
        self.assertTrue((ROOT / "minescript" / "desktop.py").exists())


if __name__ == "__main__":
    unittest.main()
