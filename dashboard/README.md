# Dashboard — KPI definitions

The charts in `../images/` track the KPIs a product analyst watches during an experiment:

| KPI | Definition | Why it matters |
|---|---|---|
| Conversion rate | `converted` users ÷ assigned users, per variant (Wilson 95% CI) | Primary metric for exp1/exp2 |
| Relative lift | (variant − control) ÷ control | Business impact in one number |
| p-value | Two-proportion z-test / Welch's t-test, two-sided | Is the difference distinguishable from noise? |
| Confidence interval | 95% CI around the lift | Range of plausible true effects |
| Power | P(detect the MDE \| the MDE is real), here 80% | Was the test even capable of finding the effect? |
| MDE | Minimum detectable effect (5% relative here) | Smallest lift the business cares about |
| SRM p-value | Chi-square test of the observed split vs 50/50 | Catches broken randomization before it burns you |

**Chart guide**
- `power_curve.png` — power vs sample size for 5/10/15% relative MDEs (12% baseline)
- `conversion_ci.png` — conversion by variant with Wilson 95% CI error bars
- `revenue_distribution.png` — revenue distribution by variant (log scale, exp3)
- `pvalue_summary.png` — −log10(p) per experiment vs the Bonferroni threshold
- `lift_forest.png` — relative lift with 95% CI per experiment, MDE reference line
