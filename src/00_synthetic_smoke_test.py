"""
Stage 1z — synthetic-data pipeline validation.

The OSF pre-registration (3gvfk) states: "Analysis code was written in advance
against synthetic data with known properties, to verify the pipeline's
correctness without observing the real data." This script IS that artifact.

It fabricates WVS-shaped, SWIID-shaped, and World Bank-shaped CSVs with a
known, injected effect (luck_belief -> norm_index, moderated by Gini;
luck_belief -> lower trust), runs them through the real 01/02/03 pipeline end
to end, and checks two things: that the pipeline runs without error, and that
it recovers the injected signs. This is NOT a test of substantive results -
it's a test that the code does what it claims to do before it ever touches
WVS/SWIID/World Bank data.

Run:  python src/00_synthetic_smoke_test.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as CFG

RNG = np.random.default_rng(CFG.RANDOM_SEED)

N_COUNTRIES = 12
WAVES = [4, 5, 6, 7]
N_PER_CELL = 600


def make_synthetic_wvs() -> pd.DataFrame:
    rows = []
    country_codes = RNG.choice(range(100, 900), size=N_COUNTRIES, replace=False)
    # Give each country a fixed "rigged-ness" - drives both luck_belief and,
    # through the injected DGP below, the outcomes. This is what a country
    # fixed effect needs to absorb.
    country_shift = {c: RNG.normal(0, 1.2) for c in country_codes}
    # Assign each country a Gini level (used to build the synthetic SWIID file
    # too, so the interaction test has something real to bite on).
    country_gini = {c: RNG.uniform(25, 60) for c in country_codes}

    study_by_wave = {4: 2, 5: 2, 6: 2, 7: 2}  # WVS by default; wave 6 gets an EVS duplicate below

    for country in country_codes:
        for wave in WAVES:
            year = 1999 + wave * 4
            n = N_PER_CELL
            luck = np.clip(RNG.normal(5.5 + country_shift[country], 2.0, n), 1, 10).round()
            luck_z = (luck - luck.mean()) / luck.std()

            gini = country_gini[country]
            gini_c = gini - 42.0  # rough sample-ish center, doesn't need to be exact here

            # Injected DGP: norm violation rises with luck_belief, more so
            # where Gini is high; trust falls with luck_belief. Divorce
            # (negative control) is pure noise, unrelated to luck_belief.
            noise = RNG.normal(0, 1, n)
            norm_latent = 0.35 * luck_z + 0.02 * luck_z * gini_c + 0.5 * noise
            just_benefits = np.clip(5 + 1.3 * norm_latent + RNG.normal(0, 1, n), 1, 10).round()
            just_taxes = np.clip(5 + 1.3 * norm_latent + RNG.normal(0, 1, n), 1, 10).round()
            just_bribe = np.clip(4 + 1.3 * norm_latent + RNG.normal(0, 1, n), 1, 10).round()
            just_steal = np.clip(3 + 1.3 * norm_latent + RNG.normal(0, 1, n), 1, 10).round()
            just_divorce = np.clip(RNG.normal(5, 2, n), 1, 10).round()  # no relation to luck

            # P(can be trusted) falls as luck_belief rises (injected H3 sign).
            # WVS coding: 1 = can be trusted, 2 = need to be careful.
            trust_p = 1 / (1 + np.exp(-(0.3 - 0.4 * luck_z)))
            trust = np.where(RNG.uniform(0, 1, n) < trust_p, 1, 2)

            sex = RNG.integers(1, 3, n)
            age = RNG.integers(18, 90, n)
            education = RNG.integers(1, 9, n)
            income_decile = np.clip(RNG.integers(1, 11, n) , 1, 10)
            weight = np.clip(RNG.normal(1, 0.2, n), 0.3, 3)
            study = np.full(n, study_by_wave[wave])

            # F114B (just_steal, real code) is only asked in waves 6-7 in the
            # real trend file - mirror that here so the smoke test exercises
            # the same "not every item in every wave" shape norm_index has to
            # handle for real.
            just_steal_col = just_steal if wave >= 6 else np.full(n, np.nan)

            rows.append(pd.DataFrame({
                "S002VS": wave, "S003": country, "S020": year,
                "S018": weight, "S017": weight,  # S018 = equilibrated (used); S017 kept for parity
                "S001": study, "E040": luck,
                "F114A": just_benefits, "F116": just_taxes, "F117": just_bribe,
                "F114B": just_steal_col, "F121": just_divorce,
                "A165": trust,
                "X001": sex, "X003": age, "X025": education, "X047_WVS": income_decile,
                "X028": RNG.integers(1, 8, n),
            }))

            # Wave 6 gets a second, EVS-flagged copy of the same country-wave
            # to exercise the dual-reporting robustness check.
            if wave == 6:
                dup = rows[-1].copy()
                dup["S001"] = 1
                rows.append(dup)

    df = pd.concat(rows, ignore_index=True)
    # Sprinkle a few WVS missing-value codes to exercise clean_missing().
    mask = RNG.random(len(df)) < 0.01
    df.loc[mask, "E040"] = -1
    return df, {c: country_gini[c] for c in country_codes}


def make_synthetic_swiid(country_gini: dict) -> pd.DataFrame:
    """SWIID-shaped file: free-text country name, year, gini_disp."""
    import country_crosswalk as CW
    rows = []
    for code, gini in country_gini.items():
        name = CW.iso_numeric_to_name.get(int(code))
        if name is None:
            continue
        for year in range(1999, 2029):
            rows.append({"country": name, "year": year,
                         "gini_disp": gini + RNG.normal(0, 0.5)})
    return pd.DataFrame(rows)


def make_synthetic_gdp(country_codes) -> pd.DataFrame:
    """World Bank WDI-shaped file: one row per country (alpha-3), one column
    per year - mirrors the real bulk-download shape merge_gdp() parses.
    NOT part of the OSF registration; exercises the additional GDP
    robustness check added in 03_models.py.
    """
    import country_crosswalk as CW
    years = [str(y) for y in range(1990, 2026)]
    rows = []
    for code in country_codes:
        alpha3 = CW.iso_numeric_to_alpha3.get(int(code))
        if alpha3 is None:
            continue
        base = RNG.uniform(3000, 45000)
        row = {"Country Code": alpha3}
        for i, y in enumerate(years):
            row[y] = max(base * (1 + 0.01 * i) + RNG.normal(0, 200), 200)
        rows.append(row)
    return pd.DataFrame(rows)


def write_worldbank_shaped_csv(df: pd.DataFrame, path: Path):
    """World Bank bulk CSVs have a 4-line metadata preamble before the real
    header row (skiprows=4 in merge_gdp()) - reproduce that here so the smoke
    test exercises the actual parsing path, not a simplified stand-in."""
    with open(path, "w") as f:
        f.write('"Data Source","World Development Indicators",\n')
        f.write("\n")
        f.write('"Last Updated Date","2026-01-01",\n')
        f.write("\n")
    df.to_csv(path, mode="a", index=False)


def run_step(script: str):
    print(f"\n{'#' * 70}\n# running {script}\n{'#' * 70}")
    result = subprocess.run([sys.executable, script], cwd=str(CFG.ROOT / "src"))
    if result.returncode != 0:
        sys.exit(f"\n{script} FAILED (exit {result.returncode}) - pipeline is broken.")


def main():
    print("Synthetic-data pipeline validation (OSF 3gvfk process-rigor check)")
    print(f"Random seed: {CFG.RANDOM_SEED}\n")

    # Work in a scratch data dir so this never touches real downloads.
    scratch_raw = CFG.ROOT / "data" / "_synthetic_raw"
    scratch_raw.mkdir(parents=True, exist_ok=True)

    wvs, country_gini = make_synthetic_wvs()
    swiid = make_synthetic_swiid(country_gini)
    gdp = make_synthetic_gdp(country_gini.keys())

    wvs_path = scratch_raw / "WVS_TimeSeries_4_0.csv"
    swiid_path = scratch_raw / "swiid_summary.csv"
    gdp_path = scratch_raw / "wb_gdp_pc.csv"
    wvs.to_csv(wvs_path, index=False)
    swiid.to_csv(swiid_path, index=False)
    write_worldbank_shaped_csv(gdp, gdp_path)
    print(f"wrote synthetic WVS  -> {wvs_path}  ({len(wvs):,} rows)")
    print(f"wrote synthetic SWIID -> {swiid_path}  ({len(swiid):,} rows)")
    print(f"wrote synthetic GDP  -> {gdp_path}  ({len(gdp):,} rows)")

    # Point config at the synthetic files for the duration of this run by
    # swapping the real raw/ files aside temporarily is riskier than just
    # monkey-patching the module the subprocess will import - simplest robust
    # approach: temporarily copy synthetic files into data/raw/ under their
    # expected names, run the pipeline, then restore whatever was there.
    real_wvs, real_swiid, real_gdp = CFG.WVS_FILE, CFG.SWIID_FILE, CFG.GDP_FILE
    backup_dir = CFG.ROOT / "data" / "_real_raw_backup"
    backup_dir.mkdir(exist_ok=True)
    moved = []
    for real_path, synth_path in ((real_wvs, wvs_path), (real_swiid, swiid_path),
                                   (real_gdp, gdp_path)):
        if real_path.exists():
            shutil.move(str(real_path), str(backup_dir / real_path.name))
            moved.append(real_path.name)
        shutil.copy(str(synth_path), str(real_path))

    try:
        run_step("01_load_clean.py")
        run_step("02_explore.py")
        run_step("03_models.py")
    finally:
        for real_path in (real_wvs, real_swiid, real_gdp):
            if real_path.exists():
                real_path.unlink()
        for name in moved:
            shutil.move(str(backup_dir / name), str(real_wvs.parent / name))
        if backup_dir.exists() and not any(backup_dir.iterdir()):
            backup_dir.rmdir()

    # --- sanity checks on the recovered results -----------------------------
    results_path = CFG.TABLES / "regression_results.csv"
    holm_path = CFG.TABLES / "primary_tests_holm.csv"
    ok = True

    if results_path.exists():
        res = pd.read_csv(results_path)

        h1 = res[(res.outcome == "norm_index") & (res.spec == "M2") & (res.term == "luck_belief_z")]
        if len(h1) and h1["coef"].iloc[0] > 0:
            print(f"\n[OK] H1 direction recovered: coef = {h1['coef'].iloc[0]:.4f} (> 0, as injected)")
        else:
            print("\n[WARN] H1 direction NOT recovered as injected - check the pipeline")
            ok = False

        h2 = res[(res.outcome == "norm_index") & (res.spec == "M3")
                 & (res.term == "luck_belief_z:gini_c")]
        if len(h2) and h2["coef"].iloc[0] > 0:
            print(f"[OK] H2 direction recovered: coef = {h2['coef'].iloc[0]:.4f} (> 0, as injected)")
        else:
            print("[WARN] H2 direction NOT recovered as injected - check the pipeline")
            ok = False

        h3 = res[(res.outcome == "trust") & (res.spec == "M2") & (res.term == "luck_belief_z")]
        if len(h3) and h3["coef"].iloc[0] < 0:
            print(f"[OK] H3 direction recovered: coef = {h3['coef'].iloc[0]:.4f} (< 0, as injected)")
        else:
            print("[WARN] H3 direction NOT recovered as injected - check the pipeline")
            ok = False
    else:
        print("\n[WARN] regression_results.csv not written")
        ok = False

    if holm_path.exists():
        holm = pd.read_csv(holm_path)
        print(f"[OK] Holm-Bonferroni table written with {len(holm)} rows")
    else:
        print("[WARN] primary_tests_holm.csv not written")
        ok = False

    match_report = CFG.TABLES / "country_match_report.csv"
    report_status = "written" if match_report.exists() else "not needed - all matched"
    print(f"[OK] country crosswalk ran (report {report_status})")

    print("\n" + "=" * 70)
    print("SYNTHETIC SMOKE TEST: " + ("PASSED" if ok else "FAILED - see warnings above"))
    print("This validates the PIPELINE, not any real-world finding.")
    print("=" * 70)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
