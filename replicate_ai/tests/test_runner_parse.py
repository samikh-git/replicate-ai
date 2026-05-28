"""Tests for parsing workspace JSON into TUI events."""

from __future__ import annotations

import json

import pytest

from replicate_ai.runner.parse import (
    build_model_spec_line,
    parse_coefficients_event,
    significance_to_stars,
)


class TestSignificanceToStars:
    def test_p_value_thresholds(self):
        assert significance_to_stars(p_value=0.005) == "***"
        assert significance_to_stars(p_value=0.03) == "**"
        assert significance_to_stars(p_value=0.08) == "*"
        assert significance_to_stars(p_value=0.2) == ""

    def test_bucket_strings(self):
        assert significance_to_stars(bucket="p<0.01") == "***"
        assert significance_to_stars(bucket="p<0.05") == "**"
        assert significance_to_stars(bucket="n.s.") == ""


class TestBuildModelSpecLine:
    def test_did_template(self):
        target = {
            "outcome_variable": "fte",
            "treatment_indicator": "nj_post",
            "model_form": "DiD",
        }
        line = build_model_spec_line(target)
        assert "fte" in line
        assert "nj_post" in line
        assert "β" in line


class TestParseCoefficientsEvent:
    def test_parses_matching_target_and_results(self):
        target = {
            "paper_citation": "Card & Krueger (1994), AER 84(4), Table 3",
            "outcome_variable": "fte",
            "treatment_indicator": "nj_post",
            "model_form": "DiD",
            "expected_coefficients": [
                {
                    "name": "nj_post",
                    "published_estimate": 2.76,
                    "published_se": 1.36,
                    "published_significance": "p<0.05",
                }
            ],
        }
        coeffs = {
            "status": "success",
            "estimates": [
                {
                    "name": "nj_post",
                    "point_estimate": 2.85,
                    "std_error": 1.32,
                    "p_value": 0.031,
                    "significance_bucket": "p<0.05",
                }
            ],
        }
        ev = parse_coefficients_event(
            json.dumps(target),
            json.dumps(coeffs),
        )
        assert ev is not None
        assert ev.estimate == 2.85
        assert ev.published == 2.76
        assert ev.delta == pytest.approx(0.09)
        assert ev.verdict == "ok"
        assert "Card & Krueger" in ev.citation_line

    def test_parses_null_published_se(self):
        target = {
            "paper_citation": "Imbens et al. (2001)",
            "outcome_variable": "yearn.2",
            "treatment_indicator": "yearlpr",
            "expected_coefficients": [
                {
                    "name": "prize_on_earnings",
                    "published_estimate": -0.11,
                    "published_se": None,
                    "published_significance": "elasticity",
                }
            ],
        }
        coeffs = {
            "status": "success",
            "estimates": [
                {
                    "name": "prize_on_earnings",
                    "point_estimate": -0.09,
                    "std_error": 0.03,
                    "p_value": 0.01,
                }
            ],
        }
        ev = parse_coefficients_event(json.dumps(target), json.dumps(coeffs))
        assert ev is not None
        assert ev.published_se is None
        assert ev.published == -0.11
        assert ev.estimate == -0.09

    def test_returns_none_when_results_failed(self):
        target = {"expected_coefficients": [{"name": "x", "published_estimate": 1.0, "published_se": 0.1}]}
        coeffs = {"status": "failed", "diagnosis": "bad data"}
        assert parse_coefficients_event(json.dumps(target), json.dumps(coeffs)) is None

    def test_returns_none_when_estimate_fields_missing(self):
        target = {
            "expected_coefficients": [
                {"name": "nj_post", "published_estimate": 2.76, "published_se": 1.36}
            ],
        }
        coeffs = {
            "status": "success",
            "estimates": [{"name": "nj_post", "std_error": 1.32}],
        }
        assert parse_coefficients_event(json.dumps(target), json.dumps(coeffs)) is None

    def test_accepts_estimate_alias_keys(self):
        target = {
            "paper_citation": "Test",
            "expected_coefficients": [
                {"name": "x", "published_estimate": 1.0, "published_se": 0.2}
            ],
        }
        coeffs = {
            "status": "success",
            "estimates": [{"name": "x", "estimate": 1.05, "se": 0.18}],
        }
        ev = parse_coefficients_event(json.dumps(target), json.dumps(coeffs))
        assert ev is not None
        assert ev.estimate == 1.05
        assert ev.estimate_se == 0.18
