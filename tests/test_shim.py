"""Run: python tests/test_shim.py -- the deprecated import paths still work."""
import importlib
import sys
import unittest
import warnings


class TestShim(unittest.TestCase):
    def test_old_imports_resolve_to_receipt_evidence_and_warn(self):
        sys.modules.pop("clicked", None)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            import clicked
        self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))
        self.assertEqual(clicked.__version__, "0.2.0")
        self.assertIs(importlib.import_module("clicked.capture"), importlib.import_module("receipt_evidence.browser"))
        self.assertIs(clicked.capture, importlib.import_module("receipt_evidence.browser").capture)
        self.assertIs(clicked.Capture, importlib.import_module("receipt_evidence.browser").Capture)


if __name__ == "__main__":
    unittest.main()
