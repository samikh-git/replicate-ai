Run complete

# Replication Audit

- **Paper**: Estimating the Effect of Unearned Income on Labor Earnings, Savings, and Consumption
- **Citation**: Imbens, G. W., Rubin, D. B., & Sacerdote, B. I. (2001). AER 91(4): 778–794.
- **Overall verdict**: MATCH
- **Date**: 2026-05-27

## Per-coefficient verdicts

| Coefficient | Published | Estimated | Rel. dev. | Sig. (pub) | Sig. (est) | Verdict |
|---|---|---|---|---|---|---|
| prize_on_earnings | -0.11 (SE: N/A) | -0.1145 (SE: N/A) | 4.1% | significant (elasticity benchmark) | significant (all component years p < 0.01) | MATCH |

## Notes

The sole named target coefficient is `prize_on_earnings`, defined in target_specification.json as the average reduced-form elasticity across post-win years 1–6 (modest-prize sample, N=453); the agent's estimates entry of the same name reports −0.1145, yielding a relative deviation of 4.1% against the published benchmark of −0.11, well within the 5% MATCH threshold with correct sign. The published benchmark is sourced from target_spec_reference.json (curator-designated), as paper_tables.json is heavily garbled with slash-encoded OCR artifacts rendering Table 4 elasticity columns unreadable. No SE is published for this averaged elasticity, so significance is assessed from the component-year estimates, all of which are highly significant (p < 0.01), consistent with the paper.
