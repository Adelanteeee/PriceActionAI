from research.combined_audit_stats import (
    average_ranks,
    partial_spearman_duration,
    spearman_pairwise,
)


def test_average_ranks_use_average_for_ties():
    assert average_ranks([10.0, 20.0, 20.0, 40.0]) == [1.0, 2.5, 2.5, 4.0]


def test_raw_spearman_uses_pairwise_complete_only():
    result = spearman_pairwise(
        [1.0, 2.0, None, 4.0],
        [1.0, None, 3.0, 4.0],
    )
    assert result.n_total == 4
    assert result.n_valid_pairwise == 2
    assert result.n_missing_x == 1
    assert result.n_missing_y == 1
    assert result.status == "DEFINED"
    assert result.rho_raw == 1.0


def test_raw_spearman_insufficient_precedes_constant_check():
    result = spearman_pairwise([1.0, None], [1.0, None])
    assert result.n_valid_pairwise == 1
    assert result.status == "UNDEFINED_INSUFFICIENT_OBSERVATIONS"
    assert result.rho_raw is None


def test_raw_spearman_constant_is_undefined_not_zero():
    result = spearman_pairwise([5.0, 5.0, 5.0], [1.0, 2.0, 3.0])
    assert result.status == "UNDEFINED_CONSTANT_INPUT"
    assert result.rho_raw is None


def test_partial_uses_triple_complete_sample_and_separate_raw_for_delta():
    values_x = [1.0, 2.0, 3.0, 4.0, 5.0]
    values_y = [1.0, 5.0, 2.0, 4.0, 3.0]
    duration = [1.0, 2.0, None, 1.0, 3.0]

    main_raw = spearman_pairwise(values_x, values_y)
    partial = partial_spearman_duration(values_x, values_y, duration)

    assert main_raw.n_valid_pairwise == 5
    assert partial.n_valid_triple == 4
    assert partial.rho_raw_for_delta == spearman_pairwise(
        [1.0, 2.0, 4.0, 5.0],
        [1.0, 5.0, 4.0, 3.0],
    ).rho_raw
    assert partial.rho_raw_for_delta != main_raw.rho_raw


def test_partial_requires_three_triple_complete_observations():
    result = partial_spearman_duration(
        [1.0, 2.0, None],
        [2.0, 1.0, None],
        [1.0, 2.0, None],
    )
    assert result.n_valid_triple == 2
    assert result.status == "UNDEFINED_INSUFFICIENT_OBSERVATIONS"


def test_partial_constant_control_is_undefined():
    result = partial_spearman_duration(
        [1.0, 2.0, 4.0],
        [4.0, 1.0, 3.0],
        [5.0, 5.0, 5.0],
    )
    assert result.status == "UNDEFINED_CONSTANT_INPUT"
