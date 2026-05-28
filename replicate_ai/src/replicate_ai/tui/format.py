from __future__ import annotations

import math

from rich.text import Text

from replicate_ai.tui.events import Verdict
from replicate_ai.tui.theme import TOKENS


def _fmt_num(x: float, *, decimals: int) -> str:
    return f"{x:.{decimals}f}"


def _fmt_se(se: float | None, *, decimals: int) -> str:
    if se is None:
        return "—"
    return _fmt_num(se, decimals=decimals)


def format_model_spec(spec: str) -> Text:
    """Format the model spec equation with β emphasized in accent.

    Expects a single-line Unicode string (Greek letters already present).
    """
    # Best-effort: highlight every 'β' occurrence.
    out = Text()
    for ch in spec:
        if ch == "β":
            out.append(ch, style=TOKENS.accent)
        else:
            out.append(ch)
    return out


def verdict_glyph(verdict: Verdict) -> tuple[str, str]:
    if verdict == "ok":
        return "✓", TOKENS.success
    if verdict == "borderline":
        return "△", TOKENS.warning
    return "✗", TOKENS.error


def format_headline_card(
    *,
    estimate_label: str,
    estimate: float,
    estimate_se: float,
    estimate_stars: str,
    published: float,
    published_se: float | None,
    published_stars: str,
    delta: float,
    verdict: Verdict,
    decimals: int = 2,
) -> str:
    """Return a fixed-width, regression-table-style block (as plain text)."""
    g, _ = verdict_glyph(verdict)
    est = _fmt_num(estimate, decimals=decimals)
    est_se = _fmt_num(estimate_se, decimals=decimals)
    pub = _fmt_num(published, decimals=decimals)
    pub_se = _fmt_se(published_se, decimals=decimals)
    d = f"{delta:+.{decimals}f}"

    # Keep alignment stable and calm.
    label_w = max(len(estimate_label), len("published"), len("Δ")) + 2
    num_w = max(len(est), len(pub), len(d)) + 2

    def row(label: str, num: str, se: str, stars: str) -> str:
        stars = stars.strip()
        star_col = f"  {stars}" if stars else ""
        return f"  {label:<{label_w}}{num:>{num_w}}   ({se}){star_col}"

    lines = [
        "COEFFICIENT  ─────────────────────────────────────────────────────────",
        "",
        row(estimate_label, est, est_se, estimate_stars),
        row("published", pub, pub_se, published_stars),
        f"  {'Δ':<{label_w}}{d:>{num_w}}   {g} {verdict}",
    ]
    return "\n".join(lines)


def format_ci_strip(
    *,
    estimate: float,
    estimate_se: float,
    published: float,
    published_se: float | None,
) -> str:
    """ASCII strip with ● (estimate) and ◆ (published)."""
    lo_candidates = [estimate - 2 * estimate_se]
    hi_candidates = [estimate + 2 * estimate_se]
    if published_se is not None:
        lo_candidates.append(published - 2 * published_se)
        hi_candidates.append(published + 2 * published_se)
    else:
        lo_candidates.append(published)
        hi_candidates.append(published)
    lo = min(lo_candidates)
    hi = max(hi_candidates)
    lo = math.floor(lo)
    hi = math.ceil(hi)
    if hi <= lo:
        hi = lo + 1

    width = 28
    axis = [lo + i * (hi - lo) / 3 for i in range(4)]
    axis_line = "        " + "".join(f"{int(round(v)):>9}" for v in axis).rstrip()
    tick_line = "        " + "|--------" * 3 + "|"

    def pos(x: float) -> int:
        if hi == lo:
            return 0
        p = (x - lo) / (hi - lo)
        return max(0, min(width - 1, int(round(p * (width - 1)))))

    buf = ["─"] * width
    buf[pos(published)] = "◆"
    buf[pos(estimate)] = "●"
    strip = "        [" + "".join(buf) + "]"
    labels = "        " + " " * (pos(estimate)) + "est."
    labels2 = "        " + " " * (pos(published)) + "pub."

    return "\n".join(
        [
            "CI 95%   " + axis_line.strip(),
            "        " + tick_line.strip(),
            strip,
            labels,
            labels2,
        ]
    )

