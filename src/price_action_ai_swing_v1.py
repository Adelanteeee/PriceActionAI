from __future__ import annotations

"""Authoritative Swing v1 entry point.

The locked Swing implementation is preserved byte-for-byte in
``price_action_ai_swing_v1_locked.py``. This wrapper re-exports that API and
routes Data Integrity gap classification through the bounded ADE-12 Change
Request module so every caller sees the same scheduled/unexpected gap rules.

No Swing detection, Reference, Major, Temporal Gate, or threshold logic lives
in this wrapper.
"""

import importlib.util
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_locked = _load("price_action_ai_swing_v1_locked_impl", _HERE / "price_action_ai_swing_v1_locked.py")
_data_integrity = _load("price_action_ai_data_integrity_authoritative", _HERE / "price_action_ai_data_integrity_cr.py")

# Re-export the locked Swing API without copying or editing its implementation.
for _name, _value in vars(_locked).items():
    if not _name.startswith("__"):
        globals()[_name] = _value

# ADE-12 authoritative Data Integrity entry points.
classify_time_gaps = _data_integrity.classify_time_gaps
segment_on_unexpected_gaps = _data_integrity.segment_on_unexpected_gaps

# Ensure calls made from inside the locked module also use the authoritative
# Data Integrity implementation.
_locked.classify_time_gaps = classify_time_gaps
_locked.segment_on_unexpected_gaps = segment_on_unexpected_gaps


def _load_core():
    """Preserve the public self-contained-core contract of Swing v1."""
    return sys.modules[__name__]


# Keep internal callers aligned with the public contract too.
_locked._load_core = _load_core


def main():
    """Run the locked Swing CLI with the authoritative gap classifier patched in."""
    return _locked.main()


if __name__ == "__main__":
    main()
