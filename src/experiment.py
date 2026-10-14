"""Experiment design + inference: power, z/t-tests, SRM check, recommendations.

Convention: alpha=0.05 two-sided per test; with 3 experiments we apply a
Bonferroni correction (alpha_adj = 0.05/3) when judging significance.
"""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest
from statsmodels.stats.power import NormalIndPower

from data_cleaning import load_and_clean

ALPHA = 0.05
N_EXPERIMENTS = 3
ALPHA_ADJ = ALPHA / N_EXPERIMENTS  # Bonferroni


def required_n_per_arm(p_control, mde_relative, alpha=ALPHA, power=0.8):
    """Sample size per arm to detect a relative lift of mde_relative on a proportion."""
    p_variant = p_control * (1 + mde_relative)
    effect = (p_variant - p_control) / np.sqrt(p_control * (1 - p_control))
    n = NormalIndPower().solve_power(effect_size=effect, alpha=alpha,
                                     power=power, alternative="two-sided")
    return int(np.ceil(n))


def power_curve(p_control, mde_relative, n_range, alpha=ALPHA):
    p_variant = p_control * (1 + mde_relative)
    effect = (p_variant - p_control) / np.sqrt(p_control * (1 - p_control))
    return [NormalIndPower().power(effect_size=effect, nobs1=n,
                                   alpha=alpha, alternative="two-sided")
            for n in n_range]


def two_proportion_ztest(success_c, n_c, success_v, n_v):
    stat, pval = proportions_ztest([success_v, success_c], [n_v, n_c],
                                   alternative="two-sided")
    return stat, pval


def welch_t_test(x_c, x_v):
    stat, pval = stats.ttest_ind(x_v, x_c, equal_var=False)
    return stat, pval


def srm_check(n_control, n_variant, expected_ratio=0.5):
    """Chi-square test of the observed split vs the expected 50/50 split."""
    n = n_control + n_variant
    expected = np.array([n * expected_ratio, n * (1 - expected_ratio)])
    observed = np.array([n_control, n_variant])
    stat, pval = stats.chisquare(observed, expected)
    return stat, pval


def recommend(exp_id, p_value, rel_lift, mde_relative, srm_pvalue):
    """Ship / no-ship decision rule."""
    if srm_pvalue < ALPHA:
        return ("DO NOT SHIP - investigate SRM",
                "Sample-ratio mismatch detected: the variant split deviates from 50/50. "
                "Check randomization/logging before trusting any result.")
    if p_value >= ALPHA_ADJ:
        return ("NO SHIP",
                f"No significant effect (p={p_value:.3f} >= Bonferroni alpha={ALPHA_ADJ:.4f}). "
                "Do not ship; consider iterating on the hypothesis.")
    if rel_lift < mde_relative:
        return ("HOLD - marginal",
                f"Significant (p={p_value:.4f}) but relative lift {rel_lift:.1%} is below "
                f"the MDE of {mde_relative:.0%} — not practically meaningful. Consider a longer run.")
    return ("SHIP",
            f"Significant (p={p_value:.4f}) with relative lift {rel_lift:.1%} above the MDE. "
            "Recommend shipping to 100%.")


EXPERIMENTS = {
    "exp1_checkout_cta": {"kind": "proportion", "mde_relative": 0.05,
                          "desc": "Checkout CTA: control vs variant conversion"},
    "exp2_onboarding": {"kind": "proportion", "mde_relative": 0.05,
                        "desc": "Onboarding flow: activation rate"},
    "exp3_pricing_page": {"kind": "revenue", "mde_relative": 0.05,
                          "desc": "Pricing page: revenue per visitor"},
}


def analyze(df, exp_id):
    cfg = EXPERIMENTS[exp_id]
    sub = df[df["experiment_id"] == exp_id]
    c = sub[sub["variant"] == "control"]
    v = sub[sub["variant"] == "variant"]

    srm_stat, srm_p = srm_check(len(c), len(v))

    if cfg["kind"] == "proportion":
        p_c, p_v = c["converted"].mean(), v["converted"].mean()
        stat, pval = two_proportion_ztest(int(c["converted"].sum()), len(c),
                                          int(v["converted"].sum()), len(v))
        rel_lift = (p_v - p_c) / p_c
        metric = {"control_rate": p_c, "variant_rate": p_v}
    else:
        stat, pval = welch_t_test(c["revenue"].values, v["revenue"].values)
        m_c, m_v = c["revenue"].mean(), v["revenue"].mean()
        rel_lift = (m_v - m_c) / m_c
        metric = {"control_rpv": m_c, "variant_rpv": m_v}

    decision, reason = recommend(exp_id, pval, rel_lift, cfg["mde_relative"], srm_p)
    return {"experiment": exp_id, "description": cfg["desc"], **metric,
            "test_stat": stat, "p_value": pval,
            "alpha_bonferroni": ALPHA_ADJ,
            "significant_bonferroni": bool(pval < ALPHA_ADJ),
            "rel_lift": rel_lift, "srm_chi2": srm_stat, "srm_p": srm_p,
            "decision": decision, "reason": reason}


def main():
    df, report = load_and_clean()
    print("data quality:", {k: v for k, v in report.items()
                            if k in ("rows_raw", "rows_clean",
                                     "duplicate_rows_removed", "missing_values")})
    print(f"\nBonferroni-adjusted alpha for {N_EXPERIMENTS} experiments: {ALPHA_ADJ:.4f}\n")
    rows = [analyze(df, e) for e in EXPERIMENTS]
    table = pd.DataFrame(rows)[["experiment", "p_value", "significant_bonferroni",
                                "rel_lift", "srm_p", "decision"]]
    print(table.to_string(index=False, float_format=lambda x: f"{x:.4f}"))
    print()
    for r in rows:
        print(f"[{r['experiment']}] {r['decision']}\n  {r['reason']}\n")

    # design check: was exp1 adequately powered for a 5% relative MDE?
    n_needed = required_n_per_arm(0.12, 0.05, power=0.8)
    print(f"Power check: to detect a 5% relative lift on a 12% baseline "
          f"(80% power, alpha=0.05) needs ~{n_needed:,} users/arm; "
          f"exp1 ran 10,000/arm.")


if __name__ == "__main__":
    main()
