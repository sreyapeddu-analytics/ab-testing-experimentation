"""Generate synthetic A/B experiment data (seeded, reproducible).

Three experiments, ~20k users each, assigned over 14 days:
  exp1_checkout_cta : binary conversion (control 12.0% vs variant 13.3%) -> wins
  exp2_onboarding    : binary activation  (control 34.0% vs variant 34.35%) -> null result
  exp3_pricing_page  : revenue per visitor (control ~$4.20 vs variant ~$4.79) -> wins,
                      with a slight sample-ratio mismatch (10150/9850) to demo the SRM check.

All data is SYNTHETIC. No real users, no real company.
"""
import numpy as np
import pandas as pd

SEED = 42
N_PER_ARM = 10_000
START_DATE = "2026-10-01"
N_DAYS = 14


def _assign_dates(rng, n):
    days = rng.integers(0, N_DAYS, size=n)
    return pd.to_datetime(START_DATE) + pd.to_timedelta(days, unit="D")


def _binary_experiment(rng, exp_id, p_control, p_variant, n_control, n_variant):
    variants = (["control"] * n_control) + (["variant"] * n_variant)
    probs = np.array([p_control] * n_control + [p_variant] * n_variant)
    converted = rng.binomial(1, probs)
    df = pd.DataFrame({
        "experiment_id": exp_id,
        "user_id": [f"{exp_id}-{i:06d}" for i in range(n_control + n_variant)],
        "variant": variants,
        "converted": converted,
        "revenue": 0.0,
        "assignment_date": _assign_dates(rng, n_control + n_variant),
    })
    return df


def _revenue_experiment(rng, exp_id, buy_p_c, buy_p_v, mu, sigma, n_control, n_variant):
    """Revenue per visitor: most visitors spend $0; buyers ~ lognormal."""
    n = n_control + n_variant
    variants = (["control"] * n_control) + (["variant"] * n_variant)
    buy_p = np.array([buy_p_c] * n_control + [buy_p_v] * n_variant)
    bought = rng.binomial(1, buy_p)
    spend = np.where(bought == 1, rng.lognormal(mean=mu, sigma=sigma, size=n), 0.0)
    df = pd.DataFrame({
        "experiment_id": exp_id,
        "user_id": [f"{exp_id}-{i:06d}" for i in range(n)],
        "variant": variants,
        "converted": bought,
        "revenue": np.round(spend, 2),
        "assignment_date": _assign_dates(rng, n),
    })
    return df


def main():
    rng = np.random.default_rng(SEED)

    exp1 = _binary_experiment(rng, "exp1_checkout_cta",
                             p_control=0.120, p_variant=0.133,
                             n_control=N_PER_ARM, n_variant=N_PER_ARM)
    exp2 = _binary_experiment(rng, "exp2_onboarding",
                             p_control=0.340, p_variant=0.3435,
                             n_control=N_PER_ARM, n_variant=N_PER_ARM)
    # slight sample-ratio mismatch: 10150 vs 9850
    exp3 = _revenue_experiment(rng, "exp3_pricing_page",
                              buy_p_c=0.120, buy_p_v=0.135,
                              mu=3.0, sigma=0.9,
                              n_control=10_150, n_variant=9_850)

    df = pd.concat([exp1, exp2, exp3], ignore_index=True)
    # shuffle so arms/dates are interleaved like a real log
    df = df.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    out = "data/experiments.csv"
    df.to_csv(out, index=False)
    print(f"wrote {out}: {len(df):,} rows")
    print(df.groupby(["experiment_id", "variant"]).agg(
        users=("user_id", "count"),
        conv_rate=("converted", "mean"),
        mean_revenue=("revenue", "mean")).round(4))


if __name__ == "__main__":
    main()
