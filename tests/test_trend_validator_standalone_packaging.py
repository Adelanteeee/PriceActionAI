from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parents[1]


def test_base_inspector_has_pinned_engine_resolver():
    base = importlib.import_module("prototype.visual_leg_inspector")
    assert hasattr(base, "resolve_engine_root")
    assert base.PINNED_ENGINE_COMMIT == "b2595784edc09d88f436fe447354f35a3cf4a850"
    assert base.ENGINE_BLOB_SHA1["price_action_ai_swing_v1_locked.py"] == "e3c2ae1ea250bd4ec755f5f2d9a3d7b641ca6d2d"


def test_trend_validator_uses_standalone_resolver_when_available():
    text = (ROOT / "prototype" / "trend_leg_visual_validator.py").read_text(encoding="utf-8")
    assert "base.resolve_engine_root(args.repo_root)" in text
    assert "base.load_locked_engines(engine_root)" in text
