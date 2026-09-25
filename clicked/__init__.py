"""Deprecated: clicked-evidence is now part of receipt-evidence.

`from receipt_evidence.browser import capture` replaces `from clicked import capture`.
This package only keeps old imports working; it will get no new features.
"""
import importlib
import sys
import warnings

__version__ = "0.2.0"

warnings.warn(
    "clicked-evidence is now part of receipt-evidence; import receipt_evidence instead of clicked",
    DeprecationWarning, stacklevel=2)

# Old submodule paths resolve to the new modules themselves, so
# `from clicked.X import Y` and `import clicked.X` keep working unchanged.
capture = sys.modules[__name__ + ".capture"] = importlib.import_module("receipt_evidence.browser")
capture = importlib.import_module("receipt_evidence.browser").capture
Capture = importlib.import_module("receipt_evidence.browser").Capture
