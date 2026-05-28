import pytest
from app.core.score_calculator import calculate_score, count_issues


def test_no_issues_returns_100():
    assert calculate_score({}) == 100.0


def test_single_critical_deducts_25():
    data = {"security_issues": [{"severity": "CRITICAL"}]}
    assert calculate_score(data) == 75.0


def test_single_high_deducts_10():
    data = {"bugs": [{"severity": "HIGH"}]}
    assert calculate_score(data) == 90.0


def test_single_medium_deducts_5():
    data = {"quality_issues": [{"severity": "MEDIUM"}]}
    assert calculate_score(data) == 95.0


def test_single_low_deducts_2():
    data = {"security_issues": [{"severity": "LOW"}]}
    assert calculate_score(data) == 98.0


def test_multiple_issues_stack():
    data = {
        "security_issues": [{"severity": "CRITICAL"}],
        "bugs": [{"severity": "HIGH"}],
        "quality_issues": [{"severity": "MEDIUM"}],
    }
    assert calculate_score(data) == 60.0


def test_cross_file_issues_deduct_as_medium():
    data = {"cross_file_issues": [{"description": "x"}, {"description": "y"}]}
    assert calculate_score(data) == 90.0


def test_score_cannot_go_below_zero():
    data = {
        "security_issues": [{"severity": "CRITICAL"}] * 5,
        "bugs": [{"severity": "HIGH"}] * 5,
        "quality_issues": [{"severity": "MEDIUM"}] * 10,
    }
    assert calculate_score(data) == 0.0


def test_unknown_severity_defaults_to_low():
    data = {"bugs": [{"severity": "UNKNOWN"}]}
    assert calculate_score(data) == 98.0


def test_count_issues_no_issues():
    total, critical = count_issues({})
    assert total == 0
    assert critical == 0


def test_count_issues_counts_correctly():
    data = {
        "security_issues": [{"severity": "CRITICAL"}, {"severity": "HIGH"}],
        "bugs": [{"severity": "MEDIUM"}],
        "quality_issues": [],
        "cross_file_issues": [{"description": "x"}],
    }
    total, critical = count_issues(data)
    assert total == 4
    assert critical == 1


def test_severity_case_insensitive():
    data = {"bugs": [{"severity": "critical"}]}
    assert calculate_score(data) == 75.0
