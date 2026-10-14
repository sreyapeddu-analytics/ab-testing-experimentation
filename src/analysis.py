"""Descriptive helpers: conversion rates, Wilson CIs, relative lift."""
import numpy as np
from scipy import stats


def wilson_ci(successes, n, alpha=0.05):
    """Wilson score interval for a binomial proportion."""
    z = stats.norm.ppf(1 - alpha / 2)
    p = successes / n
    denom = 1 + z ** 2 / n
    center = (p + z ** 2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return center - half, center + half


def conversion_summary(df, experiment_id, value_col="converted"):
    """Per-variant rate, Wilson 95% CI, absolute + relative lift of variant vs control."""
    sub = df[df["experiment_id"] == experiment_id]
    rows = {}
    for variant in ("control", "variant"):
        v = sub[sub["variant"] == variant][value_col]
        n = len(v)
        rate = v.mean()
        lo, hi = wilson_ci(int(v.sum()), n)
        rows[variant] = {"n": n, "rate": rate, "ci_lo": lo, "ci_hi": hi}
    c, t = rows["control"], rows["variant"]
    abs_lift = t["rate"] - c["rate"]
    rel_lift = abs_lift / c["rate"] if c["rate"] else float("nan")
    return {"control": c, "variant": t,
            "abs_lift": abs_lift, "rel_lift": rel_lift}
