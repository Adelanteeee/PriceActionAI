"""Frozen machine-readable contract for Task 10 interpretation outputs."""

from itertools import combinations
import re

from research.combined_audit_contract import (
    DIRECTIONS,
    MAIN_FEATURES,
    RAW_DIRECTION_SENSITIVE,
    TIMEFRAMES,
)

TASK9_EVIDENCE_PACKAGE_FILENAME = "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip"
TASK9_EVIDENCE_SHA256 = "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d"
TASK9_ACTIVITY_INPUT_SHA256 = "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192"
TASK9_AUDIT_CODE_COMMIT = "1c40cd3d3507c473fd07ea25c010d386be8a0043"
TASK9_REGISTRATION_COMMIT = "78e54fb50ce82a0cba7f91f40a6451e82996008d"
TASK10_SPEC_COMMIT = "dfc91e3c75a12a3dfa008c17453b622f03ed41ad"

CONTROL_FEATURE = "active_bar_count"
CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"
MAIN_PAIR_KEYS = tuple(combinations(MAIN_FEATURES, 2))
PARTIAL_PAIR_KEYS = tuple(p for p in MAIN_PAIR_KEYS if CONTROL_FEATURE not in p)
CONTROL_PAIR_KEYS = tuple(p for p in MAIN_PAIR_KEYS if CONTROL_FEATURE in p)
SUPPLEMENTARY_FEATURES = MAIN_FEATURES + RAW_DIRECTION_SENSITIVE
SUPPLEMENTARY_PAIR_KEYS = tuple(combinations(SUPPLEMENTARY_FEATURES, 2))

_FEATURE_ORDER = {
    name: i for i, name in enumerate(MAIN_FEATURES + RAW_DIRECTION_SENSITIVE)
}


def canonical_pair(x: str, y: str) -> tuple[str, str]:
    if x == y:
        raise ValueError("pair requires two distinct features")
    try:
        return tuple(sorted((x, y), key=_FEATURE_ORDER.__getitem__))
    except KeyError as exc:
        raise ValueError(f"unknown Task 10 feature: {exc.args[0]}") from exc


def pair_key(x: str, y: str) -> str:
    a, b = canonical_pair(x, y)
    return f"{a}__{b}"


MAIN_DOSSIERS_FILENAME = "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json"
SUPPLEMENTARY_FILENAME = "TASK10_SUPPLEMENTARY_EVIDENCE.csv"
FEATURE_DOSSIERS_FILENAME = "TASK10_FEATURE_DOSSIERS.json"
HYPOTHESES_FILENAME = "TASK10_FUTURE_ABLATION_HYPOTHESES.json"
MANIFEST_FILENAME = "TASK10_MANIFEST.json"
OUTPUT_ZIP_FILENAME = "TASK10_DEPENDENCY_REDUNDANCY_INTERPRETATION_PACKAGE.zip"

TASK10_LOGICAL_FILENAMES = (
    MAIN_DOSSIERS_FILENAME,
    SUPPLEMENTARY_FILENAME,
    FEATURE_DOSSIERS_FILENAME,
    HYPOTHESES_FILENAME,
    MANIFEST_FILENAME,
)

SUPPLEMENTARY_OUTPUT_FIELDS = (
    "timeframe",
    "direction",
    "source_artifact",
    "pair_key",
    "feature_x",
    "feature_y",
    "contains_raw_direction_sensitive",
    "is_main_pair",
    "n_total",
    "n_valid_pairwise",
    "n_missing_x",
    "n_missing_y",
    "rho_raw",
    "raw_status",
    "rho_raw_for_delta",
    "rho_duration_controlled",
    "delta_rho",
    "n_valid_triple",
    "controlled_status",
    "evidence_scope",
)

_PROHIBITED_QUALITATIVE_TERMS = (
    "STRONG", "WEAK", "STABLE", "UNSTABLE", "REDUNDANT", "ORTHOGONAL",
    "NEAR_DUPLICATE", "KEEP", "DROP", "BEST", "WORST", "IMPORTANT",
    "UNIMPORTANT",
)
_PROHIBITED_RE = re.compile(
    r"\b(?:" + "|".join(map(re.escape, _PROHIBITED_QUALITATIVE_TERMS)) + r")\b",
    re.IGNORECASE,
)


def validate_observation_text(text: str) -> None:
    match = _PROHIBITED_RE.search(text)
    if match:
        raise ValueError(
            "Task 10 observation contains prohibited qualitative term: "
            f"{match.group(0)!r}"
        )
