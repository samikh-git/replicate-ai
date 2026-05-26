"""Parse /workspace JSON artifacts into TUI coefficient events."""

from __future__ import annotations

import json
from typing import Any

from replicate_ai.tui.events import CoefficientsParsed, Verdict


def significance_to_stars(*, p_value: float | None = None, bucket: str | None = None) -> str:
    if bucket:
        b = bucket.lower()
        if "0.01" in b:
            return "***"
        if "0.05" in b:
            return "**"
        if "0.10" in b:
            return "*"
        return ""
    if p_value is None:
        return ""
    if p_value < 0.01:
        return "***"
    if p_value < 0.05:
        return "**"
    if p_value < 0.10:
        return "*"
    return ""


def build_model_spec_line(target: dict[str, Any]) -> str:
    outcome = target.get("outcome_variable", "y")
    treatment = target.get("treatment_indicator", "treatment")
    return f"{outcome}_it = α + β · {treatment} + controls + ε_it"


def _format_estimate_label(name: str) -> str:
    if name == "nj_post":
        return "β̂ (NJ × Post)"
    return f"β̂ ({name})"


def compute_verdict(delta: float, *, published: float) -> Verdict:
    tol = max(0.25, 0.1 * abs(published))
    ad = abs(delta)
    if ad <= tol:
        return "ok"
    if ad <= 2 * tol:
        return "borderline"
    return "fail"


def parse_coefficients_event(
    target_json: str,
    coefficients_json: str,
) -> CoefficientsParsed | None:
    target = json.loads(target_json)
    coeffs = json.loads(coefficients_json)
    if coeffs.get("status") != "success":
        return None

    expected_list = target.get("expected_coefficients") or []
    estimates = coeffs.get("estimates") or []
    if not expected_list or not estimates:
        return None

    exp = expected_list[0]
    est = estimates[0]
    if exp.get("name") != est.get("name"):
        # Fall back to first entries even if names differ.
        pass

    published = float(exp["published_estimate"])
    published_se = float(exp["published_se"])
    estimate = float(est["point_estimate"])
    estimate_se = float(est["std_error"])
    delta = estimate - published

    est_stars = significance_to_stars(
        p_value=est.get("p_value"),
        bucket=est.get("significance_bucket"),
    )
    pub_stars = significance_to_stars(bucket=exp.get("published_significance"))

    citation = target.get("paper_citation") or target.get("paper_title") or "Replication target"

    return CoefficientsParsed(
        model_spec=build_model_spec_line(target),
        estimate_label=_format_estimate_label(str(est.get("name", "coef"))),
        estimate=estimate,
        estimate_se=estimate_se,
        estimate_stars=est_stars,
        published=published,
        published_se=published_se,
        published_stars=pub_stars,
        delta=delta,
        verdict=compute_verdict(delta, published=published),
        citation_line=str(citation),
    )
