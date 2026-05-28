Run complete

# Replication Audit

- **Paper**: Using Maimonides' Rule to Estimate the Effect of Class Size on Scholastic Achievement
- **Citation**: Angrist, J. D., & Lavy, V. (1999). QJE 114(2): 533–575.
- **Overall verdict**: CLOSE
- **Date**: 2026-05-27

## Per-coefficient verdicts

| Coefficient | Published | Estimated | Rel. dev. | Sig. (pub) | Sig. (est) | Verdict |
|---|---|---|---|---|---|---|
| class_size_iv | -0.2500 (0.0800) | -0.2327 (0.0777) | 6.9% | 5% | 5% | CLOSE |

## Notes

`paper_tables.json` is garbled (all rows contain only `["index"]`); the published benchmark of −0.25 (SE 0.08) is sourced from `target_spec_reference.json` and `target_specification.json`, which agree. The estimated coefficient (−0.233, SE 0.078) has the correct negative sign and clears the 5% significance threshold, but the relative deviation of 6.9% just exceeds the 5% MATCH threshold, yielding CLOSE. The specification is consistent with the target (5th-grade math, 2SLS with Maimonides instrument, controls for tipuach and cohsize, weighted by non-missing math test count).
