from __future__ import annotations

import inspect
import unittest

import updater


class UpdateDefaultContractTests(unittest.TestCase):
    def test_auto_update_is_not_check_only_by_default(self):
        source = inspect.getsource(updater.auto_update)
        self.assertIn("_automatic_install_enabled", source)
        self.assertNotIn('== "1"', source)


if __name__ == "__main__":
    unittest.main()
