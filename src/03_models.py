"""
Stage 1c — regression models.

Three specifications, each stricter than the last:
  M1  pooled OLS, individual controls
  M2  + country and wave fixed effects   (within-country identification)
  M3  + interaction with country-year Gini

Plus a battery of robustness/diagnostic checks, most pre-registered (OSF
3gvfk) and clearly labeled where not - including robustness_gdp_control(),
which asks whether the Gini results survive controlling for country-year
GDP per capita. That one is NOT part of the registration.

Run:  python src/03_models.py
"""

import sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import config as CFG


def load() -> pd.DataFrame:
    for path in (CFG.CLEAN_FILE, CFG.CLEAN_FILE.with_suffix(".csv")):
        if path.exists():
            return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
    sys.exit("Run 01_load_clean.py first.")
    return pd.read_parquet(CFG.CLEAN_FILE)


def controls_available(df: pd.DataFrame) -> list[str]:
    candidates = ["female", "age", "age_sq", "education", "income_decile"]
    return [c for c in candidates if c in df.columns and df[c].notna().mean() > 0.5]


def fit(df: pd.DataFrame, formula: str, label: str, weighted: bool = True):
    """Fit OLS (or WLS with the registered survey weight) with cluster-robust SEs."""
    needed = [v for v in df.columns if v in formula]
    use_weights = weighted and CFG.WEIGHT_VAR in df.columns
    if use_weights:
        needed = needed + [CFG.WEIGHT_VAR]
    sub = df.dropna(subset=needed)
    if len(sub) < 500:
        print(f"  {label}: too few complete cases ({len(sub)}) - skipped")
        return None

    if use_weights:
        model = smf.wls(formula, data=sub, weights=sub[CFG.WEIGHT_VAR]).fit(
            cov_type="cluster",
            cov_kwds={"groups": sub[CFG.CLUSTER_VAR]},
        )
    else:
        model = smf.ols(formula, data=sub).fit(
            cov_type="cluster",
            cov_kwds={"groups": sub[CFG.CLUSTER_VAR]},
        )
    print(f"\n--- {label} ---")
    print(f"n = {int(model.nobs):,}   clusters = {sub[CFG.CLUSTER_VAR].nunique()}   "
          f"R2 = {model.rsquared:.4f}   {'WLS (' + CFG.WEIGHT_VAR + ')' if use_weights else 'OLS (unweighted)'}")

    # "luck_belief" catches luck_belief_z and its interaction term; "gini_c"
    # separately catches gini_c's own main-effect coefficient (M3's formula
    # is luck_belief_z * gini_c, which patsy expands to both main effects
    # plus the interaction - without this, gini_c's own coefficient was
    # fitted every time but never shown anywhere).
    key = [p for p in model.params.index if "luck_belief" in p or p == "gini_c"]
    for p in key:
        b, se, pv = model.params[p], model.bse[p], model.pvalues[p]
        lo, hi = b - 1.96 * se, b + 1.96 * se
        stars = "***" if pv < .001 else "**" if pv < .01 else "*" if pv < .05 else ""
        print(f"  {p:<28} {b:>8.4f}{stars:<3} (SE {se:.4f})  95% CI [{lo:.4f}, {hi:.4f}]")

    return model


def incremental_r2(df: pd.DataFrame, outcome: str, term_label: str,
                    full_formula: str, reduced_formula: str):
    """How much of the outcome's variance does one term explain on its own,
    net of everything else in the model? NOT pre-registered - added because
    the model's overall R2 is dominated by ~100+ country dummies and ~4 wave
    dummies, which mechanically absorb a lot of between-group variance
    regardless of luck_belief_z - it doesn't answer "how much does
    luck_belief_z itself explain." Refitting the same model with the term of
    interest removed, on the exact same sample, and taking the drop in R2
    (semi-partial R2) isolates that term's unique contribution. Uses plain
    (unweighted-covariance) fit here since R2 doesn't depend on the SE
    method - only the coefficient-estimation weighting matters for R2, which
    both models share.
    """
    needed = [v for v in df.columns if v in full_formula]
    use_weights = CFG.WEIGHT_VAR in df.columns
    if use_weights:
        needed = needed + [CFG.WEIGHT_VAR]
    sub = df.dropna(subset=needed)
    if len(sub) < 500:
        return None

    if use_weights:
        full = smf.wls(full_formula, data=sub, weights=sub[CFG.WEIGHT_VAR]).fit()
        reduced = smf.wls(reduced_formula, data=sub, weights=sub[CFG.WEIGHT_VAR]).fit()
    else:
        full = smf.ols(full_formula, data=sub).fit()
        reduced = smf.ols(reduced_formula, data=sub).fit()

    delta = full.rsquared - reduced.rsquared
    print(f"  incremental R2 of {term_label} on {outcome}: {delta:.4f} "
          f"({delta * 100:.2f}% of variance) - full model R2={full.rsquared:.4f}, "
          f"without {term_label} R2={reduced.rsquared:.4f}")
    return {"outcome": outcome, "term": term_label, "n": int(full.nobs),
            "r2_full": round(full.rsquared, 4), "r2_reduced": round(reduced.rsquared, 4),
            "incremental_r2": round(delta, 4), "incremental_r2_pct": round(delta * 100, 2)}


def run_outcome(df: pd.DataFrame, outcome: str, ctrls: list[str]):
    """Run the three-specification ladder for one outcome."""
    print("\n" + "=" * 70)
    print(f"OUTCOME: {outcome}")
    print("=" * 70)

    ctrl_str = (" + " + " + ".join(ctrls)) if ctrls else ""
    results = {}
    r2_rows = []

    # M1 — pooled
    results["M1"] = fit(df, f"{outcome} ~ luck_belief_z{ctrl_str}", "M1  pooled OLS")

    # M2 — country + wave fixed effects
    m2_full_formula = f"{outcome} ~ luck_belief_z{ctrl_str} + C(country_code) + C(wave)"
    results["M2"] = fit(df, m2_full_formula, "M2  + country & wave FE")
    if results["M2"] is not None:
        m2_reduced_formula = (f"{outcome} ~{ctrl_str} + C(country_code) + C(wave)"
                               if ctrls else f"{outcome} ~ C(country_code) + C(wave)")
        row = incremental_r2(df, outcome, "luck_belief_z", m2_full_formula, m2_reduced_formula)
        if row:
            r2_rows.append(row)

    # M3 — interaction with inequality (grand-mean-centered Gini, per OSF 3gvfk)
    if "gini_c" in df.columns and df["gini_c"].notna().mean() > 0.3:
        # Registered contingency: fewer than MIN_GINI_CLUSTERS_FOR_M3 matched
        # country-wave clusters -> M3 is descriptive-only, not confirmatory.
        # Must be counted on THIS outcome's actual M3 estimation sample (after
        # listwise-deleting on the outcome itself and the controls), not on
        # the raw df's gini_c coverage - that count is the same for every
        # outcome regardless of its own missingness and never reflects what
        # M3 is actually fit on. (Found 2026-09-10: this previously used the
        # raw-df count, which stayed ~207 for every outcome and never
        # tripped the 100-cluster floor - even for just_steal, whose real M3
        # sample, restricted to waves 6-7, has only 53 clusters.)
        m3_needed = [outcome, "luck_belief_z", "gini_c", CFG.CLUSTER_VAR] + ctrls
        if CFG.WEIGHT_VAR in df.columns:
            m3_needed = m3_needed + [CFG.WEIGHT_VAR]
        n_gini_clusters = df.dropna(subset=m3_needed)[CFG.CLUSTER_VAR].nunique()
        underpowered = n_gini_clusters < CFG.MIN_GINI_CLUSTERS_FOR_M3
        label = "M3  + Gini interaction (centered)"
        if underpowered:
            label += (f"  [UNDERPOWERED - DESCRIPTIVE ONLY: {n_gini_clusters} < "
                      f"{CFG.MIN_GINI_CLUSTERS_FOR_M3} registered minimum clusters]")
        m3_full_formula = f"{outcome} ~ luck_belief_z * gini_c{ctrl_str} + C(country_code) + C(wave)"
        results["M3"] = fit(df, m3_full_formula, label)
        if results["M3"] is not None:
            results["M3"].underpowered = underpowered
            # Incremental R2 of the interaction term specifically, holding
            # both main effects (luck_belief_z, gini_c) in the reduced model
            # too - isolates what the moderation itself adds, not what
            # luck_belief_z or gini_c explain on their own.
            m3_reduced_formula = f"{outcome} ~ luck_belief_z + gini_c{ctrl_str} + C(country_code) + C(wave)"
            row = incremental_r2(df, outcome, "luck_belief_z:gini_c interaction",
                                  m3_full_formula, m3_reduced_formula)
            if row:
                r2_rows.append(row)
    else:
        print("\n--- M3  + Gini interaction (centered) ---")
        print("  skipped: gini_c not populated (see merge_inequality in 01_load_clean.py "
              "and output/tables/country_match_report.csv)")

    return results, r2_rows


def run_negative_control(df: pd.DataFrame, ctrls: list[str]):
    """Pre-registered negative control (OSF 3gvfk): an unrelated 1-10
    justifiability item. A luck_belief effect here would suggest a general
    response-style / permissiveness confound rather than something specific
    to economic norm violation - it should NOT show the theorized pattern.
    """
    item = CFG.NEGATIVE_CONTROL
    if item not in df.columns or df[item].notna().mean() < 0.2:
        print(f"\nskipping negative control ({item}): insufficient coverage")
        return {}, []
    print("\n" + "#" * 70)
    print(f"NEGATIVE CONTROL: {item}  (expected: null / no theorized pattern)")
    print("#" * 70)
    return run_outcome(df, item, ctrls)


def robustness_logit_trust(df: pd.DataFrame, ctrls: list[str]):
    """Pre-registered robustness check: logit instead of the LPM used above,
    for the binary trust outcome."""
    if "trust" not in df.columns or df["trust"].notna().mean() < 0.2:
        return None

    ctrl_str = (" + " + " + ".join(ctrls)) if ctrls else ""
    formula = f"trust ~ luck_belief_z{ctrl_str} + C(country_code) + C(wave)"
    needed = ["trust", "luck_belief_z", CFG.CLUSTER_VAR] + ctrls
    sub = df.dropna(subset=needed)
    if len(sub) < 500:
        print("\n--- Robustness: logit(trust) ---\n  too few complete cases - skipped")
        return None

    print("\n" + "=" * 70)
    print("ROBUSTNESS: logit(trust) as an alternative to the LPM used in M1-M3")
    print("=" * 70)
    model = smf.logit(formula, data=sub).fit(
        disp=False, cov_type="cluster", cov_kwds={"groups": sub[CFG.CLUSTER_VAR]}
    )
    b = model.params["luck_belief_z"]
    se = model.bse["luck_belief_z"]
    print(f"  luck_belief_z (log-odds): {b:.4f}  SE {se:.4f}  "
          f"95% CI [{b - 1.96*se:.4f}, {b + 1.96*se:.4f}]")
    print("  (log-odds, not AME - convert via model.get_margeff() if needed for writeup)")
    return model


def robustness_exclude_dual_reporting(df: pd.DataFrame, ctrls: list[str]):
    """NOT part of the registered text. A verbatim check of the registration
    (2026-08-23) found the actual robustness commitment is leverage-based
    influence diagnostics - see robustness_exclude_influential_clusters()
    below, which is the pre-registered check. This function refits the
    primary spec (M2) excluding country-wave clusters with dual EVS/WVS
    reporting instead; kept as an additional check, not a substitute for
    the registered one. On the WVS-only trend file used here it never
    triggers anyway (study/S001 is constant)."""
    print("\n" + "=" * 70)
    print("ADDITIONAL CHECK (not pre-registered): exclude dual-reporting (EVS/WVS overlap) clusters")
    print("=" * 70)

    if "dual_reporting" not in df.columns or not df["dual_reporting"].any():
        print("  skipped: no dual-reporting flag populated - needs `study` (S001) "
              "in config.py WVS_VARS, see 01_load_clean.py")
        return {}

    n_excluded = df.loc[df["dual_reporting"], CFG.CLUSTER_VAR].nunique()
    sub = df[~df["dual_reporting"]]
    print(f"  excluding {n_excluded} clusters ({len(df) - len(sub):,} rows)")

    ctrl_str = (" + " + " + ".join(ctrls)) if ctrls else ""
    results = {}
    for outcome in ("norm_index", "trust"):
        if outcome not in sub.columns or sub[outcome].notna().mean() < 0.2:
            continue
        results[outcome] = fit(
            sub,
            f"{outcome} ~ luck_belief_z{ctrl_str} + C(country_code) + C(wave)",
            f"M2 ({outcome}), dual-reporting clusters excluded",
        )
    return results


def robustness_exclude_influential_clusters(df: pd.DataFrame, ctrls: list[str]):
    """Pre-registered robustness check (OSF 3gvfk), confirmed verbatim
    2026-08-23: "If any country-wave cluster exerts disproportionate
    influence, models will be re-estimated excluding it and both results
    reported." Country-wave clusters in the top decile of mean
    per-observation leverage (hat value) on the primary M2 spec (norm_index)
    are flagged as disproportionately influential; M2 is reported both with
    and without them - neither presented as the sole result, per the
    registration's outlier-handling text.
    """
    outcome = "norm_index"
    if outcome not in df.columns:
        return {}

    ctrl_str = (" + " + " + ".join(ctrls)) if ctrls else ""
    formula = f"{outcome} ~ luck_belief_z{ctrl_str} + C(country_code) + C(wave)"
    needed = [outcome, "luck_belief_z", CFG.CLUSTER_VAR] + ctrls
    if CFG.WEIGHT_VAR in df.columns:
        needed = needed + [CFG.WEIGHT_VAR]
    sub = df.dropna(subset=needed)
    if len(sub) < 500:
        print("\n--- Robustness: influence diagnostics ---\n  too few complete cases - skipped")
        return {}

    print("\n" + "=" * 70)
    print("ROBUSTNESS: leverage-based influence diagnostics on M2 (norm_index)")
    print("=" * 70)

    with_all = fit(sub, formula, "M2 (norm_index), all clusters")
    if with_all is None:
        return {}

    # Leverage diagnostics from the (unweighted) OLS hat matrix - WLS hat
    # values aren't directly comparable across observations with different
    # weights, so this uses a plain OLS fit purely for the diagnostic.
    diag_model = smf.ols(formula, data=sub).fit()
    hat = diag_model.get_influence().hat_matrix_diag
    sub = sub.copy()
    sub["_hat"] = hat
    cluster_leverage = sub.groupby(CFG.CLUSTER_VAR)["_hat"].mean()
    cutoff = cluster_leverage.quantile(CFG.INFLUENCE_LEVERAGE_QUANTILE)
    flagged = cluster_leverage[cluster_leverage > cutoff].index.tolist()
    print(f"  {len(flagged)}/{cluster_leverage.size} clusters flagged "
          f"(mean leverage > {CFG.INFLUENCE_LEVERAGE_QUANTILE:.0%}ile = {cutoff:.5f})")

    sub_excl = sub[~sub[CFG.CLUSTER_VAR].isin(flagged)]
    without_flagged = fit(
        sub_excl, formula,
        f"M2 (norm_index), {len(flagged)} high-leverage clusters excluded",
    )
    return {"with_all": with_all, "without_flagged": without_flagged, "flagged_clusters": flagged}


def robustness_dummy_coded_covariates(df: pd.DataFrame, ctrls: list[str]):
    """Pre-registered robustness check (OSF 3gvfk): education and
    income_decile entered as categorical dummies instead of the continuous
    ordinal scales used everywhere else in this file. Registered decision
    rule: report this if conclusions differ from the ordinal coding.

    Ordinal coding assumes each one-step increase in education or income
    decile has the same effect on the outcome - a flat, straight-line
    assumption. Dummy coding drops that assumption and lets each category
    have its own separate effect. If luck_belief_z barely moves between the
    two versions, the ordinal assumption wasn't doing much work; if it
    moves a lot, that's worth knowing before trusting the ordinal-coded
    result everywhere else.
    """
    outcome = "norm_index"
    if outcome not in df.columns:
        return {}

    dummy_targets = [c for c in ("education", "income_decile") if c in ctrls]
    if not dummy_targets:
        print("\n--- Robustness: dummy-coded education/income ---")
        print("  skipped: neither education nor income_decile is in the active control set")
        return {}

    ordinal_ctrls = [c for c in ctrls if c not in dummy_targets]
    dummy_terms = [f"C({c})" for c in dummy_targets]
    ctrl_str_ordinal = (" + " + " + ".join(ctrls)) if ctrls else ""
    combined = ordinal_ctrls + dummy_terms
    ctrl_str_dummy = (" + " + " + ".join(combined)) if combined else ""

    print("\n" + "=" * 70)
    print(f"ROBUSTNESS: {dummy_targets} as dummies instead of ordinal scales (M2, {outcome})")
    print("=" * 70)

    ordinal = fit(
        df, f"{outcome} ~ luck_belief_z{ctrl_str_ordinal} + C(country_code) + C(wave)",
        "M2, ordinal-coded education/income",
    )
    dummy = fit(
        df, f"{outcome} ~ luck_belief_z{ctrl_str_dummy} + C(country_code) + C(wave)",
        "M2, dummy-coded education/income",
    )

    if ordinal is not None and dummy is not None:
        b_ord, b_dum = ordinal.params["luck_belief_z"], dummy.params["luck_belief_z"]
        pct_change = abs(b_dum - b_ord) / abs(b_ord) * 100 if b_ord else float("nan")
        print(f"\n  luck_belief_z: ordinal={b_ord:.4f}  dummy={b_dum:.4f}  "
              f"({pct_change:.1f}% change)")

    return {"ordinal": ordinal, "dummy": dummy}


def robustness_gdp_control(df: pd.DataFrame, ctrls: list[str], all_results: dict):
    """NOT part of the OSF registration. Country fixed effects (M2/M3)
    absorb each country's *average* wealth level, but not within-country
    wealth *change* across waves - and gini_c is identified almost entirely
    off that same within-country, across-wave variation (see FINDINGS.md,
    Result 5). If a country's GDP per capita and its Gini move together over
    time, gini_c could be partly standing in for "the country got richer"
    rather than "the country got more unequal." This refits M2 and M3 with
    country-year GDP per capita (World Bank, PPP, in $1,000s, grand-mean
    centered - see merge_gdp() in 01_load_clean.py) added as an additional
    control, for every outcome, and compares the luck_belief_z / gini_c /
    interaction coefficients against the baseline M2/M3 fits already in
    all_results. Kept as a separate check, not folded into the main tables,
    so it stays clearly labeled as an addition rather than a registered spec.
    """
    if "gdp_pc_1000_c" not in df.columns or df["gdp_pc_1000_c"].notna().mean() < 0.2:
        print("\n" + "=" * 70)
        print("ADDITIONAL CHECK (not pre-registered): GDP per capita control")
        print("=" * 70)
        print("  skipped: gdp_pc_1000_c not populated - see merge_gdp() in "
              "01_load_clean.py and README.md for how to get the World Bank file")
        return []

    print("\n" + "=" * 70)
    print("ADDITIONAL CHECK (not pre-registered): does luck_belief_z / gini_c")
    print("survive controlling for country-year GDP per capita (PPP)?")
    print("=" * 70)

    ctrl_str = (" + " + " + ".join(ctrls)) if ctrls else ""
    rows = []
    for outcome, baseline in all_results.items():
        if outcome not in df.columns or df[outcome].notna().mean() < 0.2:
            continue

        m2_gdp = fit(
            df, f"{outcome} ~ luck_belief_z + gdp_pc_1000_c{ctrl_str} + C(country_code) + C(wave)",
            f"M2+GDP ({outcome})",
        )
        m2_base = baseline.get("M2")
        if m2_base is not None and m2_gdp is not None:
            b0, b1 = m2_base.params["luck_belief_z"], m2_gdp.params["luck_belief_z"]
            pct = abs(b1 - b0) / abs(b0) * 100 if b0 else float("nan")
            rows.append({"outcome": outcome, "spec": "M2", "term": "luck_belief_z",
                         "coef_baseline": round(b0, 4), "coef_with_gdp": round(b1, 4),
                         "pct_change": round(pct, 1)})
            print(f"  {outcome} M2 luck_belief_z: baseline={b0:.4f}  with GDP={b1:.4f}  "
                  f"({pct:.1f}% change)")

        if "gini_c" in df.columns and df["gini_c"].notna().mean() > 0.3:
            m3_gdp = fit(
                df,
                f"{outcome} ~ luck_belief_z * gini_c + gdp_pc_1000_c{ctrl_str} "
                f"+ C(country_code) + C(wave)",
                f"M3+GDP ({outcome})",
            )
            m3_base = baseline.get("M3")
            if m3_base is not None and m3_gdp is not None:
                for term in ("gini_c", "luck_belief_z:gini_c"):
                    if term in m3_base.params.index and term in m3_gdp.params.index:
                        b0, b1 = m3_base.params[term], m3_gdp.params[term]
                        pct = abs(b1 - b0) / abs(b0) * 100 if b0 else float("nan")
                        rows.append({"outcome": outcome, "spec": "M3", "term": term,
                                     "coef_baseline": round(b0, 4), "coef_with_gdp": round(b1, 4),
                                     "pct_change": round(pct, 1)})
                        print(f"  {outcome} M3 {term}: baseline={b0:.4f}  with GDP={b1:.4f}  "
                              f"({pct:.1f}% change)")

    return rows


def export_gdp_control_report(rows: list):
    """NOT pre-registered. See robustness_gdp_control()."""
    if not rows:
        return
    tab = pd.DataFrame(rows)
    out = CFG.TABLES / "gdp_control_check.csv"
    tab.to_csv(out, index=False)
    print("\n" + "=" * 70)
    print("GDP CONTROL CHECK (not pre-registered): coefficients with vs. without")
    print("country-year GDP per capita added to M2/M3")
    print("=" * 70)
    print(tab.to_string(index=False))
    print(f"\nwrote {out}")


def exploratory_gini_movers_did():
    """NOT pre-registered, and explicitly NOT the causal identification
    Stage 2 exists for - see RESEARCH_PLAN.md's Stage 2, which proposes
    diff-in-diff around actual dated corruption shocks (Lava Jato, 1MDB,
    Panama Papers) as the project's real identification strategy. This is a
    much cruder, purely exploratory two-period diff-in-differences-STYLE
    comparison: countries whose mean Gini rose between their earliest and
    latest available survey wave ("risers") vs. countries where it didn't
    ("non-risers"), comparing the change in mean norm_index between the two
    groups. It uses the same within-country Gini variation M3 already
    identifies off, just aggregated to country means and split into two
    groups instead of used continuously.

    This is NOT causally identified: which country's Gini rose over this
    particular period is not randomly assigned, so a difference here could
    reflect anything else that changed alongside inequality in those
    countries, not inequality itself - the same reverse-causality and
    omitted-variable concerns that apply to every other result in this
    file apply here too, undiminished. Reported for exploratory interest
    only, clearly separate from H1/H2/H3.
    """
    path = CFG.TABLES / "country_wave_means.csv"
    if not path.exists():
        print("\n  skipped gini-movers DiD: country_wave_means.csv not found "
              "- run 02_explore.py first")
        return None

    cw = pd.read_csv(path).dropna(subset=["gini", "norm"])
    # country_wave_means.csv is built from the same cleaned file 01/03 use,
    # which already dropped country-waves below MIN_COUNTRY_N - this filter
    # is a defensive no-op in practice, kept so this function doesn't
    # silently depend on that upstream invariant holding forever.
    cw = cw[cw["n"] >= CFG.MIN_COUNTRY_N].sort_values(["country_code", "wave"])

    multi_wave = cw.groupby("country_code")["wave"].transform("nunique") >= 2
    cw = cw[multi_wave]
    if cw["country_code"].nunique() < 10:
        print(f"\n  skipped gini-movers DiD: only {cw['country_code'].nunique()} "
              "countries have >=2 qualifying waves - too few to report")
        return None

    first = cw.groupby("country_code").first()
    last = cw.groupby("country_code").last()
    did_df = pd.DataFrame({
        "country_code": first.index,
        "wave_first": first["wave"].values, "wave_last": last["wave"].values,
        "gini_first": first["gini"].values, "gini_last": last["gini"].values,
        "norm_first": first["norm"].values, "norm_last": last["norm"].values,
    })
    did_df["delta_gini"] = did_df["gini_last"] - did_df["gini_first"]
    did_df["delta_norm"] = did_df["norm_last"] - did_df["norm_first"]
    did_df["riser"] = (did_df["delta_gini"] > 0).astype(int)

    n_riser = int(did_df["riser"].sum())
    n_non_riser = int((did_df["riser"] == 0).sum())
    print("\n" + "=" * 70)
    print("EXPLORATORY, NOT CAUSALLY IDENTIFIED (not pre-registered):")
    print("gini-movers diff-in-differences-style comparison")
    print("=" * 70)
    print(f"  {len(did_df)} countries with >=2 qualifying waves "
          f"({n_riser} Gini risers, {n_non_riser} flat/fell)")
    print(f"  median |delta_gini| = {did_df['delta_gini'].abs().median():.2f} Gini points "
          "- some of this is plausibly SWIID measurement noise, not real movement "
          "(see FINDINGS.md, 'Gini measurement uncertainty')")

    out = CFG.TABLES / "gini_movers_did.csv"
    did_df.to_csv(out, index=False)
    print(f"  wrote {out}")

    if n_riser < 5 or n_non_riser < 5:
        print("  too few countries in one group for a DiD estimate - skipped")
        return did_df

    model = smf.ols("delta_norm ~ riser", data=did_df).fit(cov_type="HC1")
    b, se, p = model.params["riser"], model.bse["riser"], model.pvalues["riser"]
    lo, hi = b - 1.96 * se, b + 1.96 * se
    print(f"  DiD estimate (risers - non-risers, change in mean norm_index): "
          f"{b:.4f}  SE {se:.4f}  95% CI [{lo:.4f}, {hi:.4f}]  p={p:.4f}")
    print(f"  mean delta_norm: risers={did_df.loc[did_df.riser == 1, 'delta_norm'].mean():.4f}  "
          f"non-risers={did_df.loc[did_df.riser == 0, 'delta_norm'].mean():.4f}")

    fig, ax = plt.subplots(figsize=(7, 5.5), constrained_layout=True)
    ax.scatter(did_df.loc[did_df.riser == 1, "delta_gini"],
               did_df.loc[did_df.riser == 1, "delta_norm"],
               color="#c1666b", label=f"Gini rose (n={n_riser})", alpha=0.8)
    ax.scatter(did_df.loc[did_df.riser == 0, "delta_gini"],
               did_df.loc[did_df.riser == 0, "delta_norm"],
               color="#2a6f97", label=f"Gini flat/fell (n={n_non_riser})", alpha=0.8)
    ax.axhline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.axvline(0, color="grey", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Change in country-mean Gini (first to last available wave)")
    ax.set_ylabel("Change in country-mean norm_index")
    ax.set_title("Exploratory: does the outcome move when Gini moves?\n"
                  "(not pre-registered, not causally identified)")
    ax.legend(fontsize=9)
    out_fig = CFG.FIGURES / "gini_movers_did.png"
    fig.savefig(out_fig, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out_fig}")

    return did_df


def fit_unadjusted_if_flagged(df: pd.DataFrame, outcome: str, drop_info: dict | None):
    """Pre-registered companion to the covariate sample-drop check. Registered
    text, verbatim: "If adding covariates in M1 reduces the sample by more
    than 30% relative to the unadjusted model, an unadjusted version will
    also be reported." That specifies M1 - the plain pooled model, no fixed
    effects - compared against a bare bivariate regression with no
    covariates at all. Fits that bare model (luck_belief_z only) when the
    sample-drop flag fires.
    """
    if drop_info is None or not drop_info.get("flagged"):
        return None
    print(f"  -> fitting unadjusted M1 for {outcome} (full {drop_info['bare_n']:,}-row "
          f"sample, no covariates, no fixed effects) for comparison")
    return fit(
        df, f"{outcome} ~ luck_belief_z",
        f"M1 ({outcome}), UNADJUSTED - no covariates, per >30% sample-drop rule",
    )


def fit_unadjusted_m2_if_flagged(df: pd.DataFrame, outcome: str, drop_info: dict | None):
    """NOT part of the registered text - see fit_unadjusted_if_flagged()
    above for the actual registered check. This is an additional comparison
    (country/wave fixed effects retained, individual covariates dropped)
    kept because it's informative, but it should not be read as satisfying
    the pre-registered "unadjusted model" commitment on its own."""
    if drop_info is None or not drop_info.get("flagged"):
        return None
    print(f"  -> [additional, not pre-registered] fitting unadjusted M2 for {outcome} "
          f"(full {drop_info['bare_n']:,}-row sample, FE retained, no individual "
          f"covariates) for comparison")
    return fit(
        df, f"{outcome} ~ luck_belief_z + C(country_code) + C(wave)",
        f"M2 ({outcome}), UNADJUSTED [additional check, not pre-registered]",
    )


def check_covariate_sample_drop(df: pd.DataFrame, outcome: str, ctrls: list[str]):
    """Pre-registered transparency check (OSF 3gvfk): flag if adding the
    covariate set shrinks the complete-case sample by more than
    CFG.COVARIATE_DROP_FLAG (30%)."""
    bare_n = df.dropna(subset=[outcome, "luck_belief_z"]).shape[0]
    if not ctrls or bare_n == 0:
        return None

    full_n = df.dropna(subset=[outcome, "luck_belief_z"] + ctrls).shape[0]
    drop_pct = (1 - full_n / bare_n) * 100 if bare_n else 0.0
    flagged = drop_pct > CFG.COVARIATE_DROP_FLAG * 100

    if flagged:
        print(f"  ! covariates drop the {outcome} sample by {drop_pct:.1f}% "
              f"({bare_n:,} -> {full_n:,}) - exceeds the pre-registered "
              f"{CFG.COVARIATE_DROP_FLAG:.0%} flag")

    return {"outcome": outcome, "bare_n": bare_n, "full_n": full_n,
            "drop_pct": round(drop_pct, 1), "flagged": flagged}


def export_sample_drop_report(rows: list):
    if not rows:
        return
    tab = pd.DataFrame(rows)
    out = CFG.TABLES / "sample_drop_report.csv"
    tab.to_csv(out, index=False)
    print("\n" + "=" * 70)
    print("COVARIATE SAMPLE-DROP CHECK (pre-registered, OSF 3gvfk)")
    print("=" * 70)
    print(tab.to_string(index=False))
    print(f"\nwrote {out}")


def export_incremental_r2_report(rows: list):
    """NOT pre-registered. Written for the record because the full model's
    R2 (dominated by ~100+ country and ~4 wave dummies) doesn't answer how
    much variance luck_belief_z, or its interaction with gini_c, explains on
    its own - see incremental_r2()."""
    if not rows:
        return
    tab = pd.DataFrame(rows)
    out = CFG.TABLES / "incremental_r2.csv"
    tab.to_csv(out, index=False)
    print("\n" + "=" * 70)
    print("INCREMENTAL R2 (not pre-registered): unique variance explained by each term")
    print("=" * 70)
    print(tab.to_string(index=False))
    print(f"\nwrote {out}")


def holm_bonferroni_summary(all_results: dict):
    """Apply Holm-Bonferroni correction to exactly the three pre-registered
    confirmatory tests (OSF 3gvfk). Everything else stays unadjusted."""
    rows = []
    for outcome, spec, param_substr, label in CFG.PRIMARY_TESTS:
        model = all_results.get(outcome, {}).get(spec)
        if model is None:
            rows.append({"hypothesis": label, "outcome": outcome, "spec": spec,
                         "term": None, "coef": np.nan, "p_raw": np.nan})
            continue
        matches = [p for p in model.params.index if param_substr in p]
        if not matches:
            rows.append({"hypothesis": label, "outcome": outcome, "spec": spec,
                         "term": None, "coef": np.nan, "p_raw": np.nan})
            continue
        term = matches[0]
        rows.append({
            "hypothesis": label, "outcome": outcome, "spec": spec, "term": term,
            "coef": round(model.params[term], 4), "p_raw": model.pvalues[term],
            "underpowered": getattr(model, "underpowered", False),
        })

    tab = pd.DataFrame(rows)
    valid = tab["p_raw"].notna()
    if valid.sum():
        _, p_adj, _, _ = multipletests(tab.loc[valid, "p_raw"], method="holm")
        tab.loc[valid, "p_holm"] = p_adj
    tab["p_raw"] = tab["p_raw"].round(4)
    if "p_holm" in tab.columns:
        tab["p_holm"] = tab["p_holm"].round(4)

    out = CFG.TABLES / "primary_tests_holm.csv"
    tab.to_csv(out, index=False)
    print("\n" + "=" * 70)
    print("PRIMARY CONFIRMATORY TESTS (Holm-Bonferroni corrected, OSF 3gvfk)")
    print("=" * 70)
    print(tab.to_string(index=False))
    print(f"\nwrote {out}")
    return tab


def marginal_effect_plot(model, df: pd.DataFrame, outcome: str):
    """Marginal effect of luck_belief across the observed Gini range."""
    if model is None:
        return
    inter = [p for p in model.params.index if "luck_belief_z:gini_c" in p]
    if not inter:
        return

    b_main = model.params["luck_belief_z"]
    b_int = model.params[inter[0]]
    cov = model.cov_params()

    gini_range = np.linspace(df["gini_c"].quantile(.05), df["gini_c"].quantile(.95), 60)
    me = b_main + b_int * gini_range
    var = (cov.loc["luck_belief_z", "luck_belief_z"]
           + gini_range ** 2 * cov.loc[inter[0], inter[0]]
           + 2 * gini_range * cov.loc["luck_belief_z", inter[0]])
    se = np.sqrt(var)

    fig, ax = plt.subplots(figsize=(8, 5.5), constrained_layout=True)
    ax.plot(gini_range, me, color="#2a6f97", linewidth=2.5)
    ax.fill_between(gini_range, me - 1.96 * se, me + 1.96 * se,
                    alpha=0.2, color="#2a6f97")
    ax.axhline(0, color="red", linestyle="--", linewidth=1)
    ax.set_xlabel("Gini (disposable income, grand-mean centered)")
    ax.set_ylabel(f"Marginal effect of luck belief on {outcome}")
    ax.set_title("Does inequality amplify the relationship?")

    out = CFG.FIGURES / f"marginal_effect_{outcome}.png"
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {out}")


def export_table(all_results: dict):
    rows = []
    for outcome, models in all_results.items():
        for spec, m in models.items():
            if m is None:
                continue
            for p in [x for x in m.params.index if "luck_belief" in x or x == "gini_c"]:
                rows.append({
                    "outcome": outcome,
                    "spec": spec,
                    "term": p,
                    "coef": round(m.params[p], 4),
                    "se": round(m.bse[p], 4),
                    "p": round(m.pvalues[p], 4),
                    "n": int(m.nobs),
                    "r2": round(m.rsquared, 4),
                    "underpowered": getattr(m, "underpowered", False),
                })
    if not rows:
        return
    tab = pd.DataFrame(rows)
    out = CFG.TABLES / "regression_results.csv"
    tab.to_csv(out, index=False)
    print(f"\nwrote {out}")
    print(tab.to_string(index=False))


def main():
    print("=" * 70)
    print("Registered reporting standards (OSF 3gvfk):")
    print("  - M2 is the pre-specified primary spec for H1; where M1 and M2")
    print("    disagree, M2 governs the conclusion.")
    print("  - Effect sizes and 95% CIs are the primary quantities reported,")
    print("    not p-values - with n in the hundreds of thousands, trivially")
    print("    small effects will be statistically significant.")
    print("=" * 70)

    df = load()
    ctrls = controls_available(df)
    print(f"Loaded {len(df):,} rows")
    print(f"Controls: {ctrls or 'none available'}")

    reliability_path = CFG.TABLES / "reliability_check.csv"
    if reliability_path.exists():
        rel = pd.read_csv(reliability_path)
        if len(rel) and bool(rel["primary_outcome_switch"].iloc[0]):
            print("\n" + "!" * 70)
            print(f"ALPHA CONTINGENCY TRIGGERED (alpha={rel['alpha'].iloc[0]}): per the")
            print("registration, treat the four justifiability items as PRIMARY outcomes")
            print("and norm_index as secondary when reporting results.")
            print("!" * 70)

    outcomes = ["norm_index"] + [c for c in CFG.NORM_ITEMS if c in df.columns]
    if "trust" in df.columns:
        outcomes.append("trust")

    all_results = {}
    sample_drop_rows = []
    r2_rows = []
    for outcome in outcomes:
        if df[outcome].notna().mean() < 0.2:
            print(f"\nskipping {outcome}: {df[outcome].notna().mean():.1%} coverage")
            continue
        drop_info = check_covariate_sample_drop(df, outcome, ctrls)
        if drop_info:
            sample_drop_rows.append(drop_info)
        res, outcome_r2_rows = run_outcome(df, outcome, ctrls)
        r2_rows.extend(outcome_r2_rows)
        unadjusted = fit_unadjusted_if_flagged(df, outcome, drop_info)
        if unadjusted is not None:
            res["M1_unadjusted"] = unadjusted
        unadjusted_m2 = fit_unadjusted_m2_if_flagged(df, outcome, drop_info)
        if unadjusted_m2 is not None:
            res["M2_unadjusted_EXTRA"] = unadjusted_m2
        all_results[outcome] = res
        if res.get("M3") is not None:
            marginal_effect_plot(res["M3"], df, outcome)

    # Negative control results go into all_results too - not just its own
    # r2 rows - so export_table() below actually writes its coefficients to
    # regression_results.csv ("every coefficient from every specification"
    # should include the negative control) and robustness_gdp_control()
    # further down checks it along with every other outcome. Previously this
    # was discarded (`_, negative_control_r2_rows = ...`), which silently
    # left just_divorce out of both.
    negative_control_results, negative_control_r2_rows = run_negative_control(df, ctrls)
    r2_rows.extend(negative_control_r2_rows)
    if negative_control_results:
        all_results[CFG.NEGATIVE_CONTROL] = negative_control_results

    export_table(all_results)
    export_sample_drop_report(sample_drop_rows)

    holm_bonferroni_summary(all_results)
    export_incremental_r2_report(r2_rows)
    robustness_logit_trust(df, ctrls)
    robustness_exclude_dual_reporting(df, ctrls)
    robustness_exclude_influential_clusters(df, ctrls)
    robustness_dummy_coded_covariates(df, ctrls)
    gdp_rows = robustness_gdp_control(df, ctrls, all_results)
    export_gdp_control_report(gdp_rows)
    exploratory_gini_movers_did()

    print("\n" + "=" * 70)
    print("REMINDER: these are correlations. Reverse causality is unresolved.")
    print("People who justify cheating may rationalise by deciding the system")
    print("is rigged. Stage 2 (identification) and Stage 3 (experiment) exist")
    print("precisely because this stage cannot settle direction.")
    print("=" * 70)


if __name__ == "__main__":
    main()
