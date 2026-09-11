"""
Stage 1a — load WVS, recode, merge inequality, write analysis file.

This is the first of three scripts (01/02/03) that turn raw survey data into
the analysis-ready dataset the OSF-registered models run on. It does five
things:

  1. Reads the WVS trend file (a 1,046-column, ~443k-row file covering
     hundreds of survey questions across 7 waves, 1981-2022) and pulls out
     only the ~18 columns this project actually uses (see config.WVS_VARS).
  2. Applies WVS's missing-value codes and the registered wave/inclusion
     exclusion criteria, so downstream code never sees a "-4" pretending to
     be a real answer or a respondent who shouldn't be in the sample.
  3. Derives the variables the models actually run on: the standardized
     composite outcome (norm_index), the standardized predictor
     (luck_belief_z), and the cluster/fixed-effect identifiers.
  4. Merges in country-year Gini from SWIID. WVS and SWIID key countries
     differently (numeric ISO code vs. free-text name) and don't always
     agree on what to call the same country, so this step has to match
     them up first.
  5. Writes data/processed/analysis.parquet, which 02_explore.py and
     03_models.py both read and never touch the raw WVS/SWIID files again.

The non-obvious choices below come from one of two places: a specific line
in the OSF pre-registration (3gvfk), or something we found wrong by
inspecting the real downloaded data (config.py's inline comments say what
was checked and when). If a choice here looks like an unexplained guess,
that's a bug to report, not something to assume is fine.

Run:  python src/01_load_clean.py
"""

import difflib
import sys
import numpy as np
import pandas as pd

import config as CFG
import country_crosswalk as CW


def load_wvs() -> pd.DataFrame:
    """Read the WVS trend file. Handles csv / dta / sav."""
    path = CFG.WVS_FILE
    if not path.exists():
        # Fail loud and early with instructions, rather than a confusing
        # FileNotFoundError three functions later - this is usually the
        # first thing a new machine/checkout hits.
        sys.exit(
            f"\nWVS file not found at {path}\n"
            "Download the Longitudinal (Trend) file from\n"
            "  https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp\n"
            "and place it in data/raw/ (update WVS_FILE in src/config.py).\n"
        )

    print(f"Reading {path.name} ...")
    suffix = path.suffix.lower()

    if suffix == ".csv":
        wanted = list(CFG.WVS_VARS.keys())
        # The real trend file is ~1,046 columns and ~1.4GB; reading all of it
        # would be slow and wasteful when we only want ~18 columns. Reading
        # just the header first (nrows=0) lets us compute which of our
        # wanted codes actually exist BEFORE the full read, so we can pass
        # usecols= to pandas and skip parsing the other 1,028 columns
        # entirely - much faster, and it also means a renamed/dropped WVS
        # code fails as a clear "not in file" warning here rather than as a
        # silent all-NaN column three steps downstream.
        header = pd.read_csv(path, nrows=0, low_memory=False)
        present = [c for c in wanted if c in header.columns]
        missing = sorted(set(wanted) - set(present))
        if missing:
            print(f"  ! not in file, skipping: {missing}")
        df = pd.read_csv(path, usecols=present, low_memory=False)
    elif suffix in (".dta", ".sav"):
        # WVS also distributes Stata/SPSS versions of the same trend file -
        # support them too since not everyone will download the CSV.
        import pyreadstat
        if suffix == ".dta":
            df, _ = pyreadstat.read_dta(str(path))
        else:
            df, _ = pyreadstat.read_sav(str(path))
        present = [c for c in CFG.WVS_VARS if c in df.columns]
        df = df[present]
    else:
        sys.exit(f"Unsupported file type: {suffix}")

    # Rename WVS's cryptic codes (E040, F114A, ...) to the readable names
    # the rest of the pipeline uses (luck_belief, just_benefits, ...) right
    # away, so nothing downstream has to know the raw survey codebook.
    df = df.rename(columns=CFG.WVS_VARS)
    print(f"  {len(df):,} rows, {df.shape[1]} columns")
    return df


def clean_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Convert WVS missing codes to NaN and enforce valid ranges."""
    # WVS doesn't use blank cells for non-response - it uses small negative
    # integers to distinguish *why* an answer is missing (e.g. -1 "don't
    # know", -2 "no answer", -4 "not asked in this wave/country", -5 "not
    # applicable"). If we don't convert these to real NaN, they'd get
    # treated as legitimate survey responses - e.g. a "-4" sitting inside
    # luck_belief (a real 1-10 scale) would silently corrupt every mean,
    # z-score, and regression that touches it. Column-wise mask rather than
    # df.replace(list, nan): the latter is both slower and hits a refcount
    # bug on some pandas 3.x builds.
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].mask(df[col].isin(CFG.MISSING_CODES))

    # Belt-and-suspenders: even after the missing-code pass, enforce that
    # each variable only holds values its actual response scale allows
    # (e.g. luck_belief must be 1-10; a stray 97/98/99-style code that isn't
    # in MISSING_CODES, or a genuine data error, gets caught here instead of
    # quietly poisoning downstream statistics).
    for col, (lo, hi) in CFG.VALID_RANGES.items():
        if col in df.columns:
            before = df[col].notna().sum()
            df.loc[~df[col].between(lo, hi), col] = np.nan
            dropped = before - df[col].notna().sum()
            if dropped:
                print(f"  {col}: {dropped:,} out-of-range -> NaN")
    return df


def build_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the analysis variables."""
    # Backfill `education` for wave 7 from X025A_01 (see the WVS_VARS
    # comment in config.py for why this is needed: X025 is 0% populated in
    # wave 7). X025A_01 is ISCED-2011 one-digit, range 0-8, vs. X025's 8-cat
    # WVS-harmonized ISCED-97-era scale (range 1-8) - not the same standard,
    # so this assumes the two scales' *ranks* line up closely enough to use
    # as one ordinal control: ISCED-2011's "0 = early childhood/no
    # education" is treated as the same bottom rung as X025's own "1 = no
    # formal education/incomplete primary" (shift +1, landing 0-8 -> 1-9,
    # which is why `education`'s VALID_RANGES upper bound is 9, not 8 - that
    # headroom already existed before this change and is what makes the
    # shift land cleanly). This is an assumption about cross-vintage
    # category alignment, not a verified one-to-one crosswalk - flagged
    # here, and in FINDINGS.md, as a specific, revisitable judgment call.
    # Only fills where `education` (X025) is actually missing, so waves 3-6
    # are completely untouched by this.
    if "education_isced11_w7" in df.columns:
        before = df["education"].notna().sum() if "education" in df.columns else 0
        shifted = df["education_isced11_w7"] + 1
        df["education"] = df["education"].fillna(shifted) if "education" in df.columns else shifted
        filled = df["education"].notna().sum() - before
        print(f"  education: backfilled {filled:,} wave-7 rows from X025A_01 "
              "(ISCED-2011, +1 shift) - see build_variables() comment")
        df = df.drop(columns=["education_isced11_w7"])

    # Trust: WVS codes 1 = can be trusted, 2 = need to be careful. We remap
    # to 1/0 rather than leaving it 1/2 so it works directly as a binary
    # outcome in a linear probability model (an OLS on a 1/2-coded variable
    # would still "work" numerically, but the coefficient would be twice
    # what you'd expect and impossible to read as a probability).
    if "trust" in df.columns:
        df["trust"] = df["trust"].map({1: 1, 2: 0})

    # Composite norm-violation index (the primary confirmatory outcome for
    # H1/H2): z-score each of the four justifiability items, then average.
    # Two reasons to standardize before averaging, not after:
    #   1. The four items don't necessarily share a mean or spread even
    #      though they're all nominally 1-10 scales - people are, e.g.,
    #      systematically less willing to justify bribery than tax cheating
    #      (see the M1 pooled coefficients: just_bribe's intercept sits
    #      lower than just_taxes'). Averaging raw scores would let whichever
    #      item happens to have the widest spread dominate the composite.
    #   2. Registered construction rule (OSF 3gvfk): "the index is the
    #      arithmetic mean of the available standardized items ... ignoring
    #      missing items." skipna=True below is what implements "ignoring
    #      missing items" - a respondent only needs ONE of the four items
    #      answered to get a norm_index value, which matters a lot here
    #      since just_steal (F114B) only exists in waves 6-7 (see
    #      config.py) - without skipna, every wave 1-5 respondent would get
    #      norm_index = NaN and the composite would be nearly useless.
    items = [c for c in CFG.NORM_ITEMS if c in df.columns]
    if not items:
        sys.exit("No justifiability items found. Check WVS_VARS in config.py.")

    print(f"  building norm_index from: {items}")
    z = df[items].apply(lambda s: (s - s.mean()) / s.std())
    df["norm_index"] = z.mean(axis=1, skipna=True)

    # Cronbach's alpha: does it actually make sense to average these four
    # items into one score, or are they measuring unrelated things that just
    # happen to be bundled together? Alpha is high when people who justify
    # one norm violation tend to justify the others too (the items "hang
    # together" as one underlying trait); low if they're not really related.
    # Registered contingency: if alpha < ALPHA_CONTINGENCY_THRESHOLD, that's
    # a signal the composite isn't trustworthy, and the four items become
    # the primary outcomes instead of norm_index - that decision must be
    # stated explicitly (not decided after peeking at whether it helps the
    # results), so we write it to a small report rather than just printing
    # it where it can be missed.
    sub = df[items].dropna()
    alpha_report = {"alpha": None, "n": len(sub),
                     "primary_outcome_switch": False,
                     "threshold": CFG.ALPHA_CONTINGENCY_THRESHOLD}
    if len(sub) > 100:
        k = len(items)
        alpha = (k / (k - 1)) * (1 - sub.var(ddof=1).sum() / sub.sum(axis=1).var(ddof=1))
        print(f"  Cronbach's alpha ({k} items, n={len(sub):,}): {alpha:.3f}")
        alpha_report["alpha"] = round(alpha, 4)
        if alpha < CFG.ALPHA_CONTINGENCY_THRESHOLD:
            alpha_report["primary_outcome_switch"] = True
            print(f"  ! alpha < {CFG.ALPHA_CONTINGENCY_THRESHOLD} - REGISTERED CONTINGENCY TRIGGERED: "
                  "treat the four justifiability items as the primary outcomes, "
                  "norm_index as secondary, in reporting.")
    pd.DataFrame([alpha_report]).to_csv(CFG.TABLES / "reliability_check.csv", index=False)
    reliability_by_group(df, items)

    # Standardise the key predictor so coefficients read as per-SD effects
    # (e.g. "a 1-SD increase in luck attribution is associated with a
    # 0.36-SD increase in norm_index"), rather than "a 1-point increase on
    # an arbitrary 1-10 scale", which is harder to interpret and not
    # comparable across outcomes with different scales. This also matters
    # for M3's interaction term: gini_c is on a totally different scale
    # (Gini points, roughly 20-60) than a raw 1-10 luck_belief, so an
    # unstandardized interaction coefficient would be nearly unreadable.
    df["luck_belief_z"] = (
        (df["luck_belief"] - df["luck_belief"].mean()) / df["luck_belief"].std()
    )

    # Cluster / fixed-effect identifier: one specific country's one specific
    # survey round (e.g. "8_3" = Albania, wave 3). Every model clusters
    # standard errors at this level (see config.CLUSTER_VAR) - necessary
    # because Gini only varies at this level too, not at the individual
    # level, so treating individuals as independent observations for
    # anything touching Gini would badly understate the true uncertainty
    # (the "Moulton problem" - see the country_wave-clustering discussion
    # for why this isn't solved by aggregating to country-level means
    # instead: that would destroy the within-country variation in
    # luck_belief that M2's country-fixed-effects spec needs to identify
    # H1 in the first place).
    df["country_wave"] = (
        df["country_code"].astype("Int64").astype(str) + "_" + df["wave"].astype("Int64").astype(str)
    )

    # female: a 0/1 dummy is more directly interpretable in a regression
    # than raw sex codes (1=male, 2=female) - the coefficient reads as
    # "the female-vs-male difference" rather than an arbitrary per-unit
    # slope on a coding that was never meant to be numeric. Built with
    # .map(), not (df["sex"] == 2) - the == comparison would silently turn
    # a missing sex into female=0 (NaN == 2 is False, not NaN), coding
    # "unknown" as "male" without ever saying so. .map() leaves anything
    # not in the dict as NaN, so missing sex stays missing.
    if "sex" in df.columns:
        df["female"] = df["sex"].map({1: 0.0, 2: 1.0})
    # age_sq: standard practice for age in social-science regressions - it
    # lets the model fit a curved (e.g. rising-then-falling) relationship
    # between age and the outcome instead of forcing a straight line, which
    # is often the wrong shape for attitudes/behavior across the life course.
    if "age" in df.columns:
        df["age_sq"] = df["age"] ** 2

    # Dual-reporting flag (OSF 3gvfk, pre-registered robustness check): a
    # country-wave is "dual-reported" if both EVS (study=1) and WVS (study=2)
    # cover it in the integrated trend file - those clusters get excluded in
    # one robustness run in 03_models.py.
    if "study" in df.columns:
        n_studies = df.groupby("country_wave")["study"].transform(lambda s: s.dropna().nunique())
        df["dual_reporting"] = (n_studies > 1).fillna(False)
        n_flagged = df.loc[df["dual_reporting"], "country_wave"].nunique()
        print(f"  {n_flagged} country-wave clusters flagged as dual-reported (EVS+WVS)")
    else:
        df["dual_reporting"] = False

    return df


def reliability_by_group(df: pd.DataFrame, items: list[str]):
    """NOT pre-registered. The single pooled Cronbach's alpha computed above
    assumes the four justifiability items hang together the same way in
    every country and every survey wave - averaging them into one
    `norm_index` composite only makes sense if that's true. This checks the
    assumption directly instead of leaving it untested (see FINDINGS.md
    Limitations, "Composite reliability"): recomputes alpha separately by
    country and by wave, using the same formula as the pooled check, on
    whichever complete cases exist within each group. Groups with fewer than
    100 complete cases are recorded but not scored - alpha on a tiny sample
    is noise, not a reliability estimate.
    """
    k = len(items)
    rows = []
    for group_type, group_col in (("country", "country_code"), ("wave", "wave")):
        if group_col not in df.columns:
            continue
        for group_val, g in df.groupby(group_col):
            sub = g[items].dropna()
            row = {"group_type": group_type, "group": group_val, "n": len(sub), "alpha": None}
            if len(sub) >= 100:
                alpha = (k / (k - 1)) * (1 - sub.var(ddof=1).sum() / sub.sum(axis=1).var(ddof=1))
                row["alpha"] = round(alpha, 4)
            rows.append(row)

    tab = pd.DataFrame(rows)
    out = CFG.TABLES / "reliability_by_group.csv"
    tab.to_csv(out, index=False)

    print("\n  Composite reliability by group (not pre-registered):")
    for group_type in ("country", "wave"):
        scored = tab[(tab["group_type"] == group_type) & tab["alpha"].notna()]
        skipped = tab[(tab["group_type"] == group_type) & tab["alpha"].isna()]
        if len(scored):
            print(f"    by {group_type}: {len(scored)} groups scored (n>=100), "
                  f"alpha range [{scored['alpha'].min():.3f}, {scored['alpha'].max():.3f}], "
                  f"median {scored['alpha'].median():.3f}"
                  + (f", {len(skipped)} groups skipped (n<100)" if len(skipped) else ""))
    print(f"  wrote {out}")
    return tab


def merge_inequality(df: pd.DataFrame) -> pd.DataFrame:
    """Attach country-year Gini from SWIID, matched via country_crosswalk.py.

    This is a left merge on (country, year). If SWIID ever had more than one
    row for the same (country, year), the merge would turn into one-to-many
    and silently duplicate WVS respondents - one copy per matching SWIID
    row. The row count before and after this function is stashed on the
    returned dataframe (via .attrs) so run_quality_checks() can verify that
    never happened, rather than trusting it by assumption.

    WVS `country_code` is numeric (ISO-3166-1 numeric, per WVS docs); SWIID's
    `country` column is free text. We resolve numeric -> name via pycountry,
    normalise both sides, and match - exact first, fuzzy fallback second.
    Anything left over (or resolved only by fuzzy match) is written to
    output/tables/country_match_report.csv for manual review; confirmed fixes
    go in CFG.MANUAL_COUNTRY_OVERRIDES.

    Why this two-tier approach (automated matching + a manual-override
    escape hatch) instead of just hand-typing a ~100-country lookup table:
    a hand-typed table can't be verified against real data until you already
    have the real data, by which point any typo is silently wrong forever.
    Building the matching logic instead means every run re-derives the
    mapping from the actual downloaded files and tells you exactly what it
    couldn't resolve - confirmed 5 of 6 country codes really were wrong
    guesses this way (Iran, Korea, Turkey, Palestine, Northern Ireland - see
    MANUAL_COUNTRY_OVERRIDES), which a static table would never have caught.
    """
    path = CFG.SWIID_FILE
    if not path.exists():
        print(f"  ! SWIID not found at {path} - continuing without gini")
        df["gini"] = np.nan
        df["gini_c"] = np.nan
        return df

    swiid = pd.read_csv(path)
    # SWIID summary uses: country, year, gini_disp, gini_mkt
    cols = {c.lower(): c for c in swiid.columns}
    gini_col = cols.get("gini_disp") or cols.get("gini_disp_se") or "gini_disp"
    name_col = cols.get("country", "country")
    year_col = cols.get("year", "year")

    swiid = swiid.rename(columns={name_col: "swiid_name", year_col: "year", gini_col: "gini"})
    keep = [c for c in ("swiid_name", "year", "gini") if c in swiid.columns]
    swiid = swiid[keep]
    print(f"  SWIID: {len(swiid):,} country-years")

    if "swiid_name" not in swiid.columns:
        print("  ! could not find a country-name column in SWIID file - skipping merge")
        df["gini"] = np.nan
        df["gini_c"] = np.nan
        return df

    swiid["_norm"] = swiid["swiid_name"].map(CW.normalize_name)
    norm_to_name = swiid.drop_duplicates("_norm").set_index("_norm")["swiid_name"].to_dict()

    wvs_codes = sorted(int(c) for c in df["country_code"].dropna().unique())
    code_to_swiid_name: dict[int, str] = {}
    report_rows = []

    for code in wvs_codes:
        if code in CFG.MANUAL_COUNTRY_OVERRIDES:
            code_to_swiid_name[code] = CFG.MANUAL_COUNTRY_OVERRIDES[code]
            continue

        iso_name = CW.iso_numeric_to_name.get(code)
        if iso_name is None:
            report_rows.append((code, None, "no ISO numeric match - add to MANUAL_COUNTRY_OVERRIDES"))
            continue

        norm = CW.normalize_name(iso_name)
        if norm in norm_to_name:
            code_to_swiid_name[code] = norm_to_name[norm]
            continue

        close = difflib.get_close_matches(norm, norm_to_name.keys(), n=1, cutoff=0.72)
        if close:
            matched_name = norm_to_name[close[0]]
            code_to_swiid_name[code] = matched_name
            report_rows.append((code, iso_name, f"fuzzy match -> '{matched_name}' - VERIFY"))
        else:
            report_rows.append((code, iso_name, "no SWIID match found"))

    if report_rows:
        report = pd.DataFrame(report_rows, columns=["wvs_country_code", "iso_name_guess", "status"])
        out = CFG.TABLES / "country_match_report.csv"
        report.to_csv(out, index=False)
        print(f"  ! {len(report_rows)}/{len(wvs_codes)} country codes need review -> {out}")
        print("    Confirmed mappings go in MANUAL_COUNTRY_OVERRIDES in config.py.")

    print(f"  Resolved {len(code_to_swiid_name)}/{len(wvs_codes)} country codes cleanly")

    n_before = len(df)
    df["_swiid_name"] = df["country_code"].map(
        lambda c: code_to_swiid_name.get(int(c)) if pd.notna(c) else None
    )
    merged = df.merge(
        swiid[["swiid_name", "year", "gini"]].rename(columns={"swiid_name": "_swiid_name"}),
        on=["_swiid_name", "year"],
        how="left",
    )
    merged = merged.drop(columns=["_swiid_name"])
    merged.attrs["pre_merge_row_count"] = n_before

    matched_pct = merged["gini"].notna().mean() * 100
    print(f"  Gini populated for {matched_pct:.1f}% of rows")

    # Grand-mean center (pre-registered, OSF 3gvfk): a single scalar (the
    # overall sample mean Gini) subtracted from every row - not a per-group
    # centering. Why center at all: in M3's interaction formula
    # (luck_belief_z * gini_c), the *main effect* of luck_belief_z is
    # mathematically defined as "the effect when the interacting variable is
    # 0." Without centering, gini_c=0 would mean an actual Gini of 0 - a
    # country with perfectly equal incomes, which doesn't exist in the data
    # and isn't a meaningful reference point. Centered, gini_c=0 means
    # "average inequality in this sample," so the main effect reads as "the
    # luck_belief effect at a typical country's inequality level" - the
    # quantity you'd actually want to interpret.
    if merged["gini"].notna().any():
        merged["gini_c"] = merged["gini"] - merged["gini"].mean()
    else:
        merged["gini_c"] = np.nan

    return merged


def merge_gdp(df: pd.DataFrame) -> pd.DataFrame:
    """Attach country-year GDP per capita (PPP) from the World Bank, matched
    via ISO alpha-3 code. NOT part of the OSF registration - see GDP_FILE in
    config.py for why this exists: it supports an additional, non-registered
    robustness check in 03_models.py asking whether gini_c and the H2
    interaction survive controlling for country-year wealth level, since
    country fixed effects absorb a country's *average* wealth but not
    within-country wealth *change* across waves, which could otherwise be
    confounded with within-country Gini change.

    Unlike merge_inequality()'s SWIID join, this doesn't need fuzzy name
    matching: World Bank identifies countries by ISO alpha-3, and WVS's
    numeric country_code maps to alpha-3 directly through the same pycountry
    table country_crosswalk.py already builds for the Gini merge - both sides
    are ISO codes, so the only manual step is
    CFG.MANUAL_COUNTRY_OVERRIDES_ALPHA3's handful of non-ISO WVS codes
    (Northern Ireland).

    Left merge on (alpha3, year) - same duplicate-row risk as
    merge_inequality if the World Bank file ever had more than one row per
    (country, year); checked the same way via row count before/after,
    stashed on .attrs for run_quality_checks() to verify.
    """
    path = CFG.GDP_FILE
    if not path.exists():
        print(f"  ! World Bank GDP file not found at {path} - continuing without gdp_pc")
        df["gdp_pc"] = np.nan
        df["gdp_pc_1000_c"] = np.nan
        return df

    wb = pd.read_csv(path, skiprows=4)
    year_cols = [c for c in wb.columns if c.isdigit()]
    wb_long = wb.melt(id_vars=["Country Code"], value_vars=year_cols,
                       var_name="year", value_name="gdp_pc")
    wb_long["year"] = wb_long["year"].astype(int)
    wb_long = wb_long.dropna(subset=["gdp_pc"]).rename(columns={"Country Code": "alpha3"})
    print(f"  World Bank GDP: {len(wb_long):,} country-years with data")

    wvs_codes = sorted(int(c) for c in df["country_code"].dropna().unique())
    code_to_alpha3: dict[int, str] = {}
    unresolved = []
    for code in wvs_codes:
        if code in CFG.MANUAL_COUNTRY_OVERRIDES_ALPHA3:
            code_to_alpha3[code] = CFG.MANUAL_COUNTRY_OVERRIDES_ALPHA3[code]
            continue
        alpha3 = CW.iso_numeric_to_alpha3.get(code)
        if alpha3 is None:
            unresolved.append(code)
            continue
        code_to_alpha3[code] = alpha3

    if unresolved:
        print(f"  ! {len(unresolved)}/{len(wvs_codes)} country codes have no ISO alpha-3 "
              f"match (no GDP data for these rows): {unresolved}")
    print(f"  Resolved {len(code_to_alpha3)}/{len(wvs_codes)} country codes to alpha-3")

    n_before = len(df)
    df["_alpha3"] = df["country_code"].map(
        lambda c: code_to_alpha3.get(int(c)) if pd.notna(c) else None
    )
    merged = df.merge(
        wb_long.rename(columns={"alpha3": "_alpha3"}),
        on=["_alpha3", "year"],
        how="left",
    )
    merged = merged.drop(columns=["_alpha3"])
    merged.attrs["pre_gdp_merge_row_count"] = n_before

    matched_pct = merged["gdp_pc"].notna().mean() * 100
    print(f"  GDP per capita populated for {matched_pct:.1f}% of rows")

    # Same centering logic as gini_c, and for the same reason (see
    # merge_inequality's comment on gini_c): rescale to $1,000s first so the
    # robustness-check coefficient isn't a vanishingly small per-dollar
    # number, then grand-mean center so 0 reads as "average wealth level in
    # this sample" rather than an actual GDP per capita of zero.
    if merged["gdp_pc"].notna().any():
        gdp_1000 = merged["gdp_pc"] / 1000
        merged["gdp_pc_1000_c"] = gdp_1000 - gdp_1000.mean()
    else:
        merged["gdp_pc_1000_c"] = np.nan

    return merged


def run_quality_checks(
    df: pd.DataFrame,
    pre_merge_row_count: int | None,
    post_merge_row_count: int | None,
    pre_gdp_merge_row_count: int | None = None,
    post_gdp_merge_row_count: int | None = None,
) -> pd.DataFrame:
    """Run a battery of sanity checks on the final dataset, right before it
    gets written to disk. Two kinds of checks:

      - FAIL checks stop the run. These are for things that would silently
        corrupt every downstream model if they slipped through - the Gini
        merge multiplying rows, missing identifiers, out-of-range values,
        non-positive weights, or a cluster smaller than the filter that's
        supposed to have already removed it.
      - WARN checks just get reported. These are things worth knowing about
        but not necessarily wrong - e.g. the row count landing outside a
        rough expected range could be fine if WVS ships more/fewer waves
        later.

    Results are written to output/tables/data_quality_checks.csv either way,
    so there's a record of what was checked even when everything passes.
    """
    checks = []

    def add(name, severity, passed, detail):
        checks.append({"check": name, "severity": severity,
                        "passed": passed, "detail": detail})

    # Exact duplicate rows, informational only. This is NOT a reliable sign
    # of a merge bug here: we keep ~24 mostly-categorical columns (age,
    # education, 6 survey items, sex, ...) out of the raw file's 1,046, and
    # weight/weight_raw take only a handful of distinct values per
    # country-wave (they come from post-stratification cells, not a
    # per-person ID). In a country-wave with 1,000-3,800 respondents, two
    # different real people coincidentally matching on all 24 columns is
    # expected, not a bug - confirmed by checking the raw 1,046-column file
    # directly: zero full-row duplicates there. The check that actually
    # catches a merge bug is merge_preserves_row_count below.
    n_dup = df.duplicated().sum()
    add("no_duplicate_rows", "WARN", n_dup == 0,
        f"{n_dup:,} fully-duplicate rows on the ~24 kept columns (expected "
        f"in large samples - see merge_preserves_row_count for the real check)")

    # The actual thing worth being strict about: the Gini merge must not
    # change the row count. It's a left join on (country, year), so it's
    # only safe if SWIID has at most one row per (country, year) - true as
    # of this run (checked directly against swiid_summary.csv), but if a
    # future SWIID release ever had two rows for the same country-year,
    # this merge would turn one-to-many and silently duplicate every
    # respondent in that country-year. This is the check that would catch
    # that, unlike no_duplicate_rows above.
    if pre_merge_row_count is not None:
        add("merge_preserves_row_count", "FAIL",
            post_merge_row_count == pre_merge_row_count,
            f"{pre_merge_row_count:,} rows before merge_inequality(), "
            f"{post_merge_row_count:,} immediately after")

    # Same check for the World Bank GDP merge (not pre-registered, see
    # merge_gdp()) - it's also a left join that's only safe if the World
    # Bank file has at most one row per (country, year), which is true of
    # the source file's shape (one row per country, years as columns) but
    # worth verifying rather than assuming.
    if pre_gdp_merge_row_count is not None:
        add("gdp_merge_preserves_row_count", "FAIL",
            post_gdp_merge_row_count == pre_gdp_merge_row_count,
            f"{pre_gdp_merge_row_count:,} rows before merge_gdp(), "
            f"{post_gdp_merge_row_count:,} immediately after")

    # The identifier columns every downstream step depends on should never
    # be missing by this point - if one is, every model that groups or
    # clusters on it will quietly drop those rows or crash.
    id_cols = [c for c in ("country_code", "wave", "year", "country_wave") if c in df.columns]
    n_missing_ids = df[id_cols].isna().sum().sum()
    add("no_missing_identifiers", "FAIL", n_missing_ids == 0,
        f"{n_missing_ids:,} missing values across {id_cols}")

    # Weights have to be strictly positive - WLS with a zero or negative
    # weight either drops that respondent silently or breaks the math.
    for wcol in ("weight", "weight_raw"):
        if wcol in df.columns:
            bad = (df[wcol].dropna() <= 0).sum()
            add(f"{wcol}_positive", "FAIL", bad == 0,
                f"{bad:,} non-positive values")

    # Re-check VALID_RANGES on the final dataframe, not just right after
    # clean_missing() - catches a bug where a later step (build_variables,
    # merge_inequality) accidentally reintroduced an out-of-range value.
    for col, (lo, hi) in CFG.VALID_RANGES.items():
        if col in df.columns:
            bad = (~df[col].dropna().between(lo, hi)).sum()
            add(f"{col}_in_range", "FAIL", bad == 0,
                f"{bad:,} values outside [{lo}, {hi}]")

    # Every country-wave cluster should already be at or above
    # MIN_COUNTRY_N - main() filters this before calling here, so a failure
    # would mean the filter itself has a bug.
    cluster_sizes = df.groupby("country_wave").size()
    small = (cluster_sizes < CFG.MIN_COUNTRY_N).sum()
    add("min_cluster_size", "FAIL", small == 0,
        f"{small:,} clusters below MIN_COUNTRY_N={CFG.MIN_COUNTRY_N} "
        f"(smallest: {cluster_sizes.min():,})")

    # Standardized variables should actually be standardized - mean ~0,
    # std ~1 for luck_belief_z; mean ~0 for gini_c (its std isn't 1, it's
    # just gini's std, since centering doesn't rescale).
    if "luck_belief_z" in df.columns:
        m, s = df["luck_belief_z"].mean(), df["luck_belief_z"].std()
        add("luck_belief_z_standardized", "FAIL",
            abs(m) < 0.01 and abs(s - 1) < 0.01,
            f"mean={m:.4f}, std={s:.4f} (expected ~0, ~1)")
    if "gini_c" in df.columns and df["gini_c"].notna().any():
        m = df["gini_c"].mean()
        add("gini_c_centered", "FAIL", abs(m) < 0.01, f"mean={m:.4f} (expected ~0)")

    # Row count in a rough plausible range for this design (the registration
    # expected 150k-300k, but 400k+ across a wider covariate set is also
    # reasonable) - informational only, since WVS could ship more/fewer
    # waves in a future release without anything being wrong.
    n = len(df)
    add("row_count_plausible", "WARN", 50_000 <= n <= 500_000,
        f"{n:,} rows (expected roughly 50,000-500,000)")

    # No country should report the same year under two different waves -
    # merge_inequality() joins Gini on year, so this would mean two waves
    # silently pulling identical Gini values, which isn't wrong exactly but
    # would be a surprise worth knowing about.
    multi = df.groupby(["country_code", "year"])["wave"].nunique()
    n_multi = (multi > 1).sum()
    add("no_country_year_spans_multiple_waves", "WARN", n_multi == 0,
        f"{n_multi:,} country-year combinations span more than one wave")

    # norm_index should be non-missing exactly when at least one of the
    # four items is non-missing - if the two disagree, skipna isn't doing
    # what build_variables() assumes it's doing.
    item_cols = [c for c in CFG.NORM_ITEMS if c in df.columns]
    has_any_item = df[item_cols].notna().any(axis=1)
    has_index = df["norm_index"].notna()
    mismatch = (has_any_item != has_index).sum()
    add("norm_index_matches_item_availability", "WARN", mismatch == 0,
        f"{mismatch:,} rows where norm_index and item availability disagree")

    # Gini values, where present, should fall in a plausible real-world
    # range - not a hard rule (SWIID could legitimately report something
    # unusual for one country-year), just a flag to look twice at.
    if "gini" in df.columns and df["gini"].notna().any():
        g = df["gini"].dropna()
        out_of_range = ((g < 15) | (g > 75)).sum()
        add("gini_plausible_range", "WARN", out_of_range == 0,
            f"{out_of_range:,} values outside [15, 75] "
            f"(actual range: {g.min():.1f}-{g.max():.1f})")

    report = pd.DataFrame(checks)
    report.to_csv(CFG.TABLES / "data_quality_checks.csv", index=False)

    print("\nData quality checks:")
    for row in checks:
        status = "PASS" if row["passed"] else row["severity"]
        marker = " " if row["passed"] else "!"
        print(f"  {marker} [{status:4}] {row['check']}: {row['detail']}")

    failed = [r for r in checks if r["severity"] == "FAIL" and not r["passed"]]
    if failed:
        names = ", ".join(r["check"] for r in failed)
        sys.exit(f"\n{len(failed)} data quality check(s) FAILED: {names}\n"
                  f"See output/tables/data_quality_checks.csv - fix before trusting "
                  f"anything downstream of this file.")

    return report


def main():
    # The order below is deliberate, not incidental - each step depends on
    # the one before it having already run:
    #   load -> wave filter -> clean missing codes -> inclusion filter ->
    #   derive variables -> merge Gini -> merge GDP (not registered) ->
    #   drop thin clusters -> write
    df = load_wvs()

    # Registered exclusion criterion: waves before MIN_WAVE dropped
    # (inconsistent item fielding in earlier waves). Done first, before
    # cleaning, purely so the "dropped N rows" counts below are computed on
    # a stable, easy-to-reason-about baseline (rows from waves we're never
    # going to use don't inflate/deflate later stage counts).
    before = len(df)
    df = df[df["wave"] >= CFG.MIN_WAVE]
    print(f"Dropped {before - len(df):,} rows from waves < {CFG.MIN_WAVE} "
          "(registered exclusion criterion)")

    print("\nCleaning ...")
    df = clean_missing(df)

    # Registered inclusion criterion: non-missing predictor AND at least one
    # of the four justifiability outcome items. This has to run AFTER
    # clean_missing() - otherwise WVS's negative missing-codes would still
    # look like "non-missing" values here and respondents who actually
    # answered nothing would wrongly pass the filter.
    before = len(df)
    outcome_cols = [c for c in CFG.NORM_ITEMS if c in df.columns]
    included = df["luck_belief"].notna() & df[outcome_cols].notna().any(axis=1)
    df = df[included]
    print(f"Applied inclusion criterion (non-missing predictor + >=1 outcome item): "
          f"dropped {before - len(df):,} rows -> {len(df):,} remain")

    print("\nBuilding variables ...")
    df = build_variables(df)

    print("\nMerging inequality ...")
    df = merge_inequality(df)
    # Captured right here, immediately before the thin-cluster filter below
    # changes the row count for legitimate reasons - this pair is what
    # run_quality_checks() compares to confirm the merge itself didn't
    # change the row count, independent of any filtering that happens
    # after it. (Not relying on .attrs surviving the filter step either -
    # pandas doesn't guarantee attrs propagation across every operation.)
    pre_merge_row_count = df.attrs.get("pre_merge_row_count")
    post_merge_row_count = len(df)

    print("\nMerging World Bank GDP per capita (not pre-registered) ...")
    df = merge_gdp(df)
    pre_gdp_merge_row_count = df.attrs.get("pre_gdp_merge_row_count")
    post_gdp_merge_row_count = len(df)

    # Registered exclusion criterion: country-waves with too few respondents
    # on the key predictor are dropped entirely - a "country" surveyed with
    # only a handful of people isn't a reliable enough unit to include as
    # its own cluster, and would contribute a noisy, low-precision data
    # point to every model (this runs on country_wave, which build_variables
    # creates, and after merge_inequality since neither step changes row
    # counts - it's here rather than earlier only because it needs
    # country_wave to exist).
    counts = df.groupby("country_wave")["luck_belief"].transform("count")
    before = len(df)
    df = df[counts >= CFG.MIN_COUNTRY_N]
    print(f"\nDropped {before - len(df):,} rows in country-waves with n < {CFG.MIN_COUNTRY_N}")

    # Sanity check, not a filter: confirms the inclusion criterion above
    # actually worked as intended (every row should already have both
    # luck_belief and norm_index by this point, so this should read
    # "X / X", not a smaller number - if it doesn't, something upstream
    # changed in a way that broke the invariant).
    core = ["luck_belief", "norm_index"]
    complete = df.dropna(subset=core)
    print(f"Complete cases on {core}: {len(complete):,} / {len(df):,}")

    # Run the full quality-check battery on the final dataframe, before it
    # gets written anywhere - a FAIL here stops the script, so a broken
    # file never reaches 02_explore.py or 03_models.py.
    run_quality_checks(df, pre_merge_row_count, post_merge_row_count,
                        pre_gdp_merge_row_count, post_gdp_merge_row_count)

    try:
        df.to_parquet(CFG.CLEAN_FILE, index=False)
        written = CFG.CLEAN_FILE
    except ImportError:
        written = CFG.CLEAN_FILE.with_suffix(".csv")
        df.to_csv(written, index=False)
        print("  (pyarrow missing - wrote CSV instead)")
    print(f"\nWrote {written}")
    print(f"  {len(df):,} rows")
    print(f"  {df['country_code'].nunique()} countries, {df['wave'].nunique()} waves")

    sample_cols = [
        "country_code", "wave", "year", "luck_belief", "norm_index",
        "just_benefits", "just_taxes", "just_bribe", "just_steal",
        "trust", "gini_c",
    ]
    sample_cols = [c for c in sample_cols if c in df.columns]
    sample = df.head(10)

    print(f"\nSample (first 10 rows, {len(sample_cols)} of {df.shape[1]} columns "
          f"- full row written to output/tables/sample_head.csv):")
    with pd.option_context("display.max_columns", None, "display.width", 140):
        print(sample[sample_cols].to_string())
    sample.to_csv(CFG.TABLES / "sample_head.csv", index=False)

    # Per-column min/max/mean/std (on non-missing values) plus a NaN count.
    # This is a quick eyeball check, not a substitute for 02_explore.py's
    # fuller descriptives (which also has missing-percent and figures) - the
    # point here is to catch anything obviously wrong (a mean outside a
    # scale's range, a std of 0, an unexpected max, a NaN count that's
    # higher than expected for a given column) right where the file gets
    # written, before moving on to the next script.
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats = df[numeric_cols].agg(["min", "max", "mean", "std"]).T
    stats = stats.round(3)
    stats["n_nan"] = df[numeric_cols].isna().sum()
    print(f"\nColumn stats ({len(numeric_cols)} numeric columns, "
          f"full table written to output/tables/column_stats.csv):")
    with pd.option_context("display.max_columns", None, "display.width", 140):
        print(stats.to_string())
    stats.to_csv(CFG.TABLES / "column_stats.csv")


if __name__ == "__main__":
    main()

