"""Frozen machine-readable contract for Task 11 hypothesis registration."""

from types import MappingProxyType


TASK11_SPEC_PATH = "docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.md"
TASK11_SPEC_COMMIT = "7a3553770ea51e4ae72662fa44907f507779d22d"
TASK11_SPEC_BLOB_SHA = "99e93ef6ca7cf1038561e7d6c4217e226ba99dfb"
TASK11_SPEC_LOCK_RECORD_PATH = "docs/superpowers/specs/2026-09-01-task11-evidence-review-hypothesis-registration-design.LOCKED.md"
TASK11_SPEC_LOCK_COMMIT = "a51dc7f76a5c3ea4c8e2929be7859c02c879a2d9"
TASK11_SPEC_LOCK_RECORD_BLOB_SHA = "de87a930b424b0cf9e58e14c8b27dca336954f33"

TASK10_IMPLEMENTATION_COMMIT = "0a780ca95c4e6853bb2530436c6045c54f508e80"
TASK10_PRODUCTION_PACKAGE_FILENAME = "TASK10_PRODUCTION_RUN1.zip"
TASK10_PRODUCTION_PACKAGE_SHA256 = "464465ef3dd435ed3a574bf8ded917095dcb76bb614416625b8c96db78c48903"
TASK10_MAIN_DOSSIERS_MEMBER_SHA256 = "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3"
TASK10_MANIFEST_MEMBER_SHA256 = "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20"

TIMEFRAMES = ("M5", "M15", "M30", "H1")
TASK10_CANONICAL_PAIR_KEYS = (
    "active_bar_count__net_thrust",
    "active_bar_count__gross_close_path",
    "active_bar_count__net_close_displacement",
    "active_bar_count__directional_efficiency",
    "active_bar_count__directional_continuity_ratio",
    "active_bar_count__close_confirmation_ratio",
    "active_bar_count__gap_path_share",
    "active_bar_count__body_strength_ratio",
    "active_bar_count__shadow_position_imbalance",
    "active_bar_count__overlap_ratio",
    "active_bar_count__normalized_directional_close_ols_slope",
    "active_bar_count__mean_tick_activity",
    "net_thrust__gross_close_path",
    "net_thrust__net_close_displacement",
    "net_thrust__directional_efficiency",
    "net_thrust__directional_continuity_ratio",
    "net_thrust__close_confirmation_ratio",
    "net_thrust__gap_path_share",
    "net_thrust__body_strength_ratio",
    "net_thrust__shadow_position_imbalance",
    "net_thrust__overlap_ratio",
    "net_thrust__normalized_directional_close_ols_slope",
    "net_thrust__mean_tick_activity",
    "gross_close_path__net_close_displacement",
    "gross_close_path__directional_efficiency",
    "gross_close_path__directional_continuity_ratio",
    "gross_close_path__close_confirmation_ratio",
    "gross_close_path__gap_path_share",
    "gross_close_path__body_strength_ratio",
    "gross_close_path__shadow_position_imbalance",
    "gross_close_path__overlap_ratio",
    "gross_close_path__normalized_directional_close_ols_slope",
    "gross_close_path__mean_tick_activity",
    "net_close_displacement__directional_efficiency",
    "net_close_displacement__directional_continuity_ratio",
    "net_close_displacement__close_confirmation_ratio",
    "net_close_displacement__gap_path_share",
    "net_close_displacement__body_strength_ratio",
    "net_close_displacement__shadow_position_imbalance",
    "net_close_displacement__overlap_ratio",
    "net_close_displacement__normalized_directional_close_ols_slope",
    "net_close_displacement__mean_tick_activity",
    "directional_efficiency__directional_continuity_ratio",
    "directional_efficiency__close_confirmation_ratio",
    "directional_efficiency__gap_path_share",
    "directional_efficiency__body_strength_ratio",
    "directional_efficiency__shadow_position_imbalance",
    "directional_efficiency__overlap_ratio",
    "directional_efficiency__normalized_directional_close_ols_slope",
    "directional_efficiency__mean_tick_activity",
    "directional_continuity_ratio__close_confirmation_ratio",
    "directional_continuity_ratio__gap_path_share",
    "directional_continuity_ratio__body_strength_ratio",
    "directional_continuity_ratio__shadow_position_imbalance",
    "directional_continuity_ratio__overlap_ratio",
    "directional_continuity_ratio__normalized_directional_close_ols_slope",
    "directional_continuity_ratio__mean_tick_activity",
    "close_confirmation_ratio__gap_path_share",
    "close_confirmation_ratio__body_strength_ratio",
    "close_confirmation_ratio__shadow_position_imbalance",
    "close_confirmation_ratio__overlap_ratio",
    "close_confirmation_ratio__normalized_directional_close_ols_slope",
    "close_confirmation_ratio__mean_tick_activity",
    "gap_path_share__body_strength_ratio",
    "gap_path_share__shadow_position_imbalance",
    "gap_path_share__overlap_ratio",
    "gap_path_share__normalized_directional_close_ols_slope",
    "gap_path_share__mean_tick_activity",
    "body_strength_ratio__shadow_position_imbalance",
    "body_strength_ratio__overlap_ratio",
    "body_strength_ratio__normalized_directional_close_ols_slope",
    "body_strength_ratio__mean_tick_activity",
    "shadow_position_imbalance__overlap_ratio",
    "shadow_position_imbalance__normalized_directional_close_ols_slope",
    "shadow_position_imbalance__mean_tick_activity",
    "overlap_ratio__normalized_directional_close_ols_slope",
    "overlap_ratio__mean_tick_activity",
    "normalized_directional_close_ols_slope__mean_tick_activity",
)

HYPOTHESIS_ID_PREFIX = "TASK11_HYPOTHESIS__"
TEST_QUESTION_TEMPLATE_ID = "TASK11_PAIRWISE_NEUTRAL_V1"
TEST_QUESTION_TEMPLATE = (
    "Under a future separately locked controlled ablation protocol, "
    "does the information relationship between {feature_x} and {feature_y} "
    "remain measurable when their incremental information contributions "
    "are evaluated separately?"
)

TASK10_MEMBER_SHA256_BY_FILENAME = MappingProxyType({
    "TASK10_MAIN_RELATIONSHIP_DOSSIERS.json": "954bd97aeb41b33669c99695b88a1715aa01a19bd697282f8e1b437be57de4d3",
    "TASK10_SUPPLEMENTARY_EVIDENCE.csv": "d4bd7ba2162429b0224fb1de39d4c4d71b5558b3a470d2224390faba7d1fbcf0",
    "TASK10_FEATURE_DOSSIERS.json": "8eeefc8393485e77e688e9ad298aba56bcbf20eac9d995f3c6b803dec6e97354",
    "TASK10_FUTURE_ABLATION_HYPOTHESES.json": "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570",
    "TASK10_MANIFEST.json": "f6736c59bc120b8ed8bb5bcaf9ea0d3fb65931cfc2a82e142295c33333500a20",
})

TASK10_MAIN_DOSSIER_FIELDS = (
    "cross_tf", "cross_tf_source_artifact", "cross_tf_source_row_locator",
    "deterministic_context", "direct_deterministic_dependency",
    "direct_deterministic_relation_ids", "feature_x", "feature_x_analysis_role",
    "feature_x_direction_semantics", "feature_x_formula", "feature_y",
    "feature_y_analysis_role", "feature_y_direction_semantics", "feature_y_formula",
    "observations", "pair_key", "partial_applicability", "partial_by_tf",
    "partial_source_artifact_by_tf", "partial_source_row_locator_by_tf", "raw_by_tf",
    "raw_source_artifact_by_tf", "raw_source_row_locator_by_tf", "source_pair_key",
)
TASK10_RAW_TF_FIELDS = (
    "feature_x", "feature_y", "n_missing_x", "n_missing_y", "n_total",
    "n_valid_pairwise", "rho_raw", "status",
)
TASK10_ELIGIBLE_PARTIAL_TF_FIELDS = (
    "feature_x", "feature_y", "rho_raw_for_delta", "rho_duration_controlled",
    "delta_rho", "n_valid_triple", "status",
)
TASK10_CONTROL_PARTIAL_TF_FIELDS = (
    "rho_raw_for_delta", "rho_duration_controlled", "delta_rho",
    "n_valid_triple", "status",
)
TASK10_CROSS_TF_FIELDS = (
    "controlled_eligible", "controlled_rho_H1", "controlled_rho_M15",
    "controlled_rho_M30", "controlled_rho_M5", "feature_x", "feature_y",
    "n_defined_tf", "n_negative_tf", "n_positive_tf", "n_undefined_tf",
    "n_valid_H1", "n_valid_M15", "n_valid_M30", "n_valid_M5", "n_zero_tf",
    "rho_H1", "rho_M15", "rho_M30", "rho_M5", "rho_max", "rho_min", "rho_range",
    "sign_agreement_count", "sign_agreement_modal_signs", "sign_agreement_tie",
)
TASK10_DETERMINISTIC_CONTEXT_FIELDS = (
    "co_participating_relation_ids", "co_participation_semantics",
)

TASK11_HYPOTHESIS_RECORD_FIELDS = (
    "hypothesis_id", "pair_key", "feature_x", "feature_y",
    "raw_evidence_by_tf", "duration_control_applicability",
    "controlled_evidence_by_tf", "cross_tf_evidence",
    "direct_deterministic_dependency", "deterministic_relation_ids",
    "deterministic_context", "evidence_summary",
    "test_question_template_id", "test_question", "source_locators",
)
TASK11_SOURCE_LOCATOR_FIELDS = (
    "task10_main_dossier", "upstream_raw_source_artifact_by_tf",
    "upstream_raw_source_row_locator_by_tf", "upstream_partial_source_artifact_by_tf",
    "upstream_partial_source_row_locator_by_tf", "upstream_cross_tf_source_artifact",
    "upstream_cross_tf_source_row_locator",
)
TASK11_MANIFEST_FIELDS = (
    "task", "task11_spec_commit", "task11_implementation_commit",
    "hypothesis_registry_filename", "hypothesis_registry_sha256",
    "production_archive_filename", "logical_output_filenames",
    "task10_implementation_commit", "task10_production_package_filename",
    "task10_production_package_sha256", "task10_main_dossiers_member_sha256",
    "task10_manifest_member_sha256", "hypothesis_unit", "hypothesis_cardinality",
    "hypothesis_id_policy", "hypothesis_id_prefix", "test_question_policy",
    "test_question_template_id", "evidence_summary_policy", "cross_tf_evidence_policy",
    "main_pair_count", "hypothesis_count", "duration_control_eligible_count",
    "control_feature_non_applicable_count", "deterministic_context_pair_count",
    "logical_file_count", "new_statistics_computed", "raw_cross_tf_pooling",
    "ranking_performed", "score_computed", "threshold_applied", "outcome_used",
    "prediction_performed", "optimization_performed", "ablation_executed",
    "causal_replay_executed", "causal_claims_made", "ablation_protocol_designed",
    "directional_tests_defined", "feature_importance_assessed", "feature_selection_performed",
    "feature_removal_recommended", "keep_drop_recommendation_made",
)
TASK11_FALSE_SCOPE_FIELDS = (
    "new_statistics_computed", "raw_cross_tf_pooling", "ranking_performed", "score_computed",
    "threshold_applied", "outcome_used", "prediction_performed", "optimization_performed",
    "ablation_executed", "causal_replay_executed", "causal_claims_made",
    "ablation_protocol_designed", "directional_tests_defined", "feature_importance_assessed",
    "feature_selection_performed", "feature_removal_recommended", "keep_drop_recommendation_made",
)
TASK11_LOGICAL_FILENAMES = (
    "TASK11_HYPOTHESIS_REGISTRY.json", "TASK11_MANIFEST.json",
)
OUTPUT_ZIP_FILENAME = "TASK11_EVIDENCE_REVIEW_HYPOTHESIS_REGISTRATION_PACKAGE.zip"

DETERMINISTIC_RELATION_IDS_BY_PAIR_KEY = MappingProxyType({
    "active_bar_count__directional_continuity_ratio": ("CONTINUITY_RATIO",),
    "active_bar_count__normalized_directional_close_ols_slope": ("SLOPE_NORMALIZATION",),
    "active_bar_count__mean_tick_activity": ("TICK_ACTIVITY_IDENTITY",),
    "gross_close_path__gap_path_share": ("GAP_PATH_SHARE",),
})

MAIN_PAIR_COUNT = 78
HYPOTHESIS_COUNT = 78
DURATION_CONTROL_ELIGIBLE_COUNT = 66
CONTROL_FEATURE_NON_APPLICABLE_COUNT = 12
DETERMINISTIC_CONTEXT_PAIR_COUNT = 4
LOGICAL_FILE_COUNT = 2
CONTROL_FEATURE = "active_bar_count"
CONTROL_NOT_APPLICABLE = "NOT_APPLICABLE_CONTROL_FEATURE"
ELIGIBLE = "ELIGIBLE"
LOCKED_STATISTICAL_STATUSES = frozenset({
    "DEFINED", "UNDEFINED_INSUFFICIENT_OBSERVATIONS", "UNDEFINED_CONSTANT_INPUT",
})

TASK10_MANIFEST_FIELDS = (
    "ablation_executed", "causal_replay_executed", "control_feature_non_applicable_pair_count",
    "cutoff_applied", "feature_dossier_count", "feature_removal_recommended",
    "future_ablation_hypothesis_count", "main_relationship_dossier_count",
    "new_association_statistics_computed", "outcome_used", "partial_delta_eligible_pair_count",
    "ranking_performed", "raw_cross_tf_pooling", "score_computed", "supplementary_evidence_row_count",
    "task", "task10_implementation_commit", "task10_spec_commit", "task9_activity_input_sha256",
    "task9_audit_code_commit", "task9_evidence_package_filename", "task9_evidence_package_sha256",
    "task9_registration_commit", "threshold_applied",
)
TASK10_MANIFEST_EXPECTED_VALUES = MappingProxyType({
    "ablation_executed": False, "causal_replay_executed": False,
    "control_feature_non_applicable_pair_count": 12, "cutoff_applied": False,
    "feature_dossier_count": 13, "feature_removal_recommended": False,
    "future_ablation_hypothesis_count": 0, "main_relationship_dossier_count": 78,
    "new_association_statistics_computed": False, "outcome_used": False,
    "partial_delta_eligible_pair_count": 66, "ranking_performed": False,
    "raw_cross_tf_pooling": False, "score_computed": False,
    "supplementary_evidence_row_count": 960,
    "task": "Task 10 Dependency / Redundancy Interpretation",
    "task10_implementation_commit": "0a780ca95c4e6853bb2530436c6045c54f508e80",
    "task10_spec_commit": "dfc91e3c75a12a3dfa008c17453b622f03ed41ad",
    "task9_activity_input_sha256": "1e9f13fd88fc1e8e0e66d801be8c15d726639eaea25e53fef7c3bb88bfd05192",
    "task9_audit_code_commit": "1c40cd3d3507c473fd07ea25c010d386be8a0043",
    "task9_evidence_package_filename": "GOLD_COMBINED_LEG_FEATURE_AUDIT_PACKAGE.zip",
    "task9_evidence_package_sha256": "968f4826858a0bbb8254218711f4ad3e3487370ca8d0f288133ee36f7a4fa40d",
    "task9_registration_commit": "78e54fb50ce82a0cba7f91f40a6451e82996008d",
    "threshold_applied": False,
})
