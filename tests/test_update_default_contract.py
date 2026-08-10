from __future__ import annotations

import os
import unittest
from unittest import mock

import updater


class UpdateDefaultContractTests(unittest.TestCase):
    def test_auto_update_is_not_check_only_by_default(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertTrue(updater._automatic_install_enabled())
        with mock.patch.dict(os.environ, {"F3PLUS_CHECK_ONLY_UPDATE": "1"}, clear=True):
            self.assertFalse(updater._automatic_install_enabled())
        with mock.patch.dict(os.environ, {"F3PLUS_AUTO_UPDATE": "0"}, clear=True):
            self.assertFalse(updater._automatic_install_enabled())


if __name__ == "__main__":
    unittest.main()
