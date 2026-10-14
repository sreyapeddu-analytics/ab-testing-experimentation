"""Data validation and cleaning for the synthetic experiment log."""
import pandas as pd

EXPECTED_EXPERIMENTS = {"exp1_checkout_cta", "exp2_onboarding", "exp3_pricing_page"}


def load_and_clean(path="data/experiments.csv"):
    df = pd.read_csv(path, parse_dates=["assignment_date"])
    report = {}

    report["rows_raw"] = len(df)
    report["missing_values"] = int(df.isna().sum().sum())

    # drop exact duplicates (keep first)
    dupes = int(df.duplicated().sum())
    df = df.drop_duplicates().reset_index(drop=True)
    report["duplicate_rows_removed"] = dupes

    # standardize variant labels
    df["variant"] = df["variant"].str.strip().str.lower()
    bad_variants = sorted(set(df["variant"]) - {"control", "variant"})
    report["unexpected_variant_labels"] = bad_variants

    # sanity checks
    assert set(df["experiment_id"].unique()) == EXPECTED_EXPERIMENTS, "unexpected experiment ids"
    assert ((df["converted"] == 1) | (df["converted"] == 0)).all(), "converted must be 0/1"
    assert (df["revenue"] >= 0).all(), "revenue must be non-negative"
    # converted flag must agree with revenue>0 for the revenue experiment
    rev = df[df["experiment_id"] == "exp3_pricing_page"]
    assert ((rev["converted"] == 1) == (rev["revenue"] > 0)).all(), "converted/revenue mismatch"

    report["rows_clean"] = len(df)
    report["users_per_experiment_variant"] = (
        df.groupby(["experiment_id", "variant"]).size().to_dict()
    )
    return df, report


if __name__ == "__main__":
    df, report = load_and_clean()
    for k, v in report.items():
        print(f"{k}: {v}")
