"""
Stage 1b — descriptives and figures.

Run:  python src/02_explore.py
"""

import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

import config as CFG

sns.set_theme(style="whitegrid", context="talk")
PALETTE = "viridis"


def load() -> pd.DataFrame:
    for path in (CFG.CLEAN_FILE, CFG.CLEAN_FILE.with_suffix(".csv")):
        if path.exists():
            return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    sys.exit("Run 01_load_clean.py first.")
    return pd.read_parquet(CFG.CLEAN_FILE)


def describe(df: pd.DataFrame):
    cols = ["luck_belief", "norm_index"] + [c for c in CFG.NORM_ITEMS if c in df.columns]
    cols += [c for c in ("trust", "age", "income_decile", "gini", "gdp_pc") if c in df.columns]

    desc = df[cols].describe().T
    desc["missing_pct"] = (1 - df[cols].notna().mean()) * 100
    desc = desc.round(3)

    out = CFG.TABLES / "descriptives.csv"
    desc.to_csv(out)
    print(f"\n=== Descriptives ===\n{desc}\nwrote {out}")


def plot_distributions(df: pd.DataFrame):
    # Everything on the same 1-10 justifiability/luck scale, plus the
    # negative control (just_divorce) - it's on the same scale too, so it
    # belongs in this panel rather than off on its own.
    items = [c for c in CFG.NORM_ITEMS if c in df.columns]
    if "just_divorce" in df.columns:
        items = items + ["just_divorce"]
    n = len(items) + 1
    fig, axes = plt.subplots(1, n, figsize=(4.2 * n, 4), constrained_layout=True)

    sns.histplot(df["luck_belief"].dropna(), bins=10, ax=axes[0], color="#2a6f97")
    axes[0].set_title("Luck belief\n(1=hard work → 10=luck)", fontsize=11)
    axes[0].set_xlabel("")

    for ax, item in zip(axes[1:], items):
        color = "#4a7c59" if item == "just_divorce" else "#8c4a5f"
        sns.histplot(df[item].dropna(), bins=10, ax=ax, color=color)
        label = item.replace("_", " ") + ("\n(negative control)" if item == "just_divorce" else "")
        ax.set_title(label, fontsize=11)
        ax.set_xlabel("")

    out = CFG.FIGURES / "distributions.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    # trust is binary, not a 1-10 scale, so it doesn't belong in the
    # histogram panel above - a simple bar of the two proportions instead.
    if "trust" in df.columns:
        counts = df["trust"].value_counts(normalize=True, dropna=True).sort_index()
        fig, ax = plt.subplots(figsize=(4, 4), constrained_layout=True)
        ax.bar(["Can't be too\ncareful (0)", "Most people can\nbe trusted (1)"],
               [counts.get(0, 0), counts.get(1, 0)], color="#2a6f97")
        ax.set_ylabel("Share of respondents")
        ax.set_title("Generalised trust")
        out = CFG.FIGURES / "trust_distribution.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"wrote {out}")


def plot_binned_relationship(df: pd.DataFrame):
    """Mean norm index at each level of luck_belief, with 95% CI."""
    g = (
        df.dropna(subset=["luck_belief", "norm_index"])
        .groupby("luck_belief")["norm_index"]
        .agg(["mean", "sem", "count"])
        .reset_index()
    )
    g["lo"] = g["mean"] - 1.96 * g["sem"]
    g["hi"] = g["mean"] + 1.96 * g["sem"]

    fig, ax = plt.subplots(figsize=(8, 5.5), constrained_layout=True)
    ax.errorbar(g["luck_belief"], g["mean"],
                yerr=1.96 * g["sem"], fmt="o-", color="#2a6f97",
                capsize=4, linewidth=2, markersize=7)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Luck belief  (1 = hard work pays → 10 = luck & connections)")
    ax.set_ylabel("Norm-violation index (z)")
    ax.set_title("Perceived meritocracy and justifying norm violation")

    out = CFG.FIGURES / "binned_relationship.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")
    print(f"\n=== Binned means ===\n{g[['luck_belief','mean','count']].round(3)}")


def plot_negative_control_comparison(df: pd.DataFrame):
    """Same binned-mean view as plot_binned_relationship, but with
    just_divorce (the pre-registered negative control) drawn alongside
    norm_index on the same axes.

    The point of a negative control is that it shouldn't show the pattern
    the real outcome shows - it's a 1-10 justifiability item too, so it
    goes through the same response scale and the same respondents, but
    divorce has no theoretical link to perceived meritocracy. If this line
    tracks norm_index's line, that's a sign the whole pattern might be a
    general response-style effect (some people just rate everything higher)
    rather than something specific to economic norm violation.
    03_models.py checks this numerically; this is the visual version at the
    exploratory stage.
    """
    if "just_divorce" not in df.columns:
        return

    # z-score just_divorce so it's on the same scale as norm_index - without
    # this the two lines aren't comparable, since norm_index is already
    # standardized and just_divorce (1-10, raw) isn't.
    divorce_z = (df["just_divorce"] - df["just_divorce"].mean()) / df["just_divorce"].std()
    plot_df = df[["luck_belief"]].copy()
    plot_df["norm_index"] = df["norm_index"]
    plot_df["just_divorce_z"] = divorce_z

    fig, ax = plt.subplots(figsize=(8, 5.5), constrained_layout=True)
    for col, label, color in [
        ("norm_index", "norm_index (real outcome)", "#2a6f97"),
        ("just_divorce_z", "just_divorce, standardized (negative control)", "#c1666b"),
    ]:
        g = (
            plot_df.dropna(subset=["luck_belief", col])
            .groupby("luck_belief")[col]
            .agg(["mean", "sem"])
            .reset_index()
        )
        ax.errorbar(g["luck_belief"], g["mean"], yerr=1.96 * g["sem"],
                    fmt="o-", color=color, capsize=4, linewidth=2,
                    markersize=6, label=label)

    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Luck belief  (1 = hard work pays → 10 = luck & connections)")
    ax.set_ylabel("Standardized mean")
    ax.set_title("Real outcome vs. negative control")
    ax.legend(loc="best", fontsize=9)

    out = CFG.FIGURES / "negative_control_comparison.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")


def plot_country_scatter(df: pd.DataFrame):
    """Country-level means. Descriptive only - ecological inference risk."""
    cw = (
        df.groupby(["country_code", "wave"])
        .agg(luck=("luck_belief", "mean"),
             norm=("norm_index", "mean"),
             gini=("gini", "mean"),
             n=("luck_belief", "size"))
        .reset_index()
        .dropna(subset=["luck", "norm"])
    )

    fig, ax = plt.subplots(figsize=(8, 6), constrained_layout=True)
    sc = ax.scatter(cw["luck"], cw["norm"], s=cw["n"] / 15,
                    c=cw["gini"] if cw["gini"].notna().any() else "#2a6f97",
                    cmap=PALETTE, alpha=0.7, edgecolor="white", linewidth=0.5)

    if cw["gini"].notna().any():
        plt.colorbar(sc, ax=ax, label="Gini (disposable)")

    if len(cw) > 2:
        z = np.polyfit(cw["luck"], cw["norm"], 1)
        xs = np.linspace(cw["luck"].min(), cw["luck"].max(), 50)
        ax.plot(xs, np.poly1d(z)(xs), "--", color="black", linewidth=1.5)
        r = cw["luck"].corr(cw["norm"])
        ax.set_title(f"Country-wave means  (r = {r:.3f}, n = {len(cw)})")

    ax.set_xlabel("Mean luck belief")
    ax.set_ylabel("Mean norm-violation index")

    out = CFG.FIGURES / "country_scatter.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {out}")

    cw.to_csv(CFG.TABLES / "country_wave_means.csv", index=False)


def correlations(df: pd.DataFrame):
    cols = ["luck_belief", "norm_index"] + [c for c in CFG.NORM_ITEMS if c in df.columns]
    cols += [c for c in ("trust", "just_divorce", "income_decile", "gini", "gdp_pc") if c in df.columns]
    corr = df[cols].corr().round(3)

    fig, ax = plt.subplots(figsize=(9, 7), constrained_layout=True)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                square=True, ax=ax, cbar_kws={"shrink": 0.7}, annot_kws={"size": 8})
    ax.set_title("Correlation matrix")

    out = CFG.FIGURES / "correlations.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    corr.to_csv(CFG.TABLES / "correlations.csv")
    print(f"wrote {out}")


def missingness_report(df: pd.DataFrame):
    """Missing rate on the key predictor and outcomes, broken out by
    country and wave. Registered commitment (OSF 3gvfk): "Missingness on
    the key predictor and outcomes will be described by country and wave,
    and any systematic patterns reported."

    This isn't a check that blocks anything - it's a look at whether
    missingness is scattered evenly or concentrated in a handful of
    country-waves, which matters for how much to trust results from the
    thinner ones (a country-wave where half the justifiability items are
    missing is contributing much less real information than its raw row
    count suggests).
    """
    watch_cols = ["luck_belief"] + [c for c in CFG.NORM_ITEMS if c in df.columns]
    watch_cols = [c for c in watch_cols if c in df.columns]

    rows = []
    for (country, wave), g in df.groupby(["country_code", "wave"]):
        row = {"country_code": country, "wave": wave, "n": len(g)}
        for col in watch_cols:
            row[f"{col}_missing_pct"] = round((1 - g[col].notna().mean()) * 100, 1)
        rows.append(row)
    report = pd.DataFrame(rows).sort_values(["country_code", "wave"])

    out = CFG.TABLES / "missingness_by_country_wave.csv"
    report.to_csv(out, index=False)

    # Flag the worst offenders rather than print all 231 rows - a
    # country-wave missing more than half of a given item is worth a second
    # look. just_steal is excluded from this flag on purpose: it's a
    # waves-6-7-only item (see config.py), so every wave 3-5 country-wave is
    # ~100% missing on it for a reason we already know - flagging on it
    # would just bury any genuinely new pattern under that already-known one.
    flag_cols = [f"{c}_missing_pct" for c in watch_cols if c != "just_steal"]
    worst = report[(report[flag_cols] > 50).any(axis=1)] if flag_cols else report.iloc[0:0]
    print(f"\n=== Missingness by country-wave ===")
    print(f"wrote {out} ({len(report)} country-waves)")
    if len(worst):
        print(f"{len(worst)} country-waves have >50% missing on at least one of "
              f"{[c for c in watch_cols if c != 'just_steal']} "
              "(just_steal excluded - its wave-6-7-only coverage is expected, "
              "see the full report for it anyway) - see the report for details.")
    else:
        print("No country-wave exceeds 50% missing on the key predictor or "
              "the always-asked items - missingness looks reasonably "
              "scattered, not concentrated in specific country-waves.")


def main():
    df = load()
    print(f"Loaded {len(df):,} rows")

    describe(df)
    missingness_report(df)
    plot_distributions(df)
    plot_binned_relationship(df)
    plot_negative_control_comparison(df)
    plot_country_scatter(df)
    correlations(df)

    print("\nDone. Figures in output/figures/, tables in output/tables/")


if __name__ == "__main__":
    main()
