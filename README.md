# Perceived Meritocracy and Norm Violation

Does believing that success comes from luck and connections rather than hard work
predict willingness to justify cheating, bribery, and benefit fraud — and is that
relationship stronger where inequality is higher?

Stage 1 of a three-stage design. See `RESEARCH_PLAN.md` for the full argument and
**[`FINDINGS.md`](FINDINGS.md) for the results.**
Pre-registered on OSF: [osf.io/3gvfk](https://osf.io/3gvfk/overview) (accepted
2026-08-05; analysis completed within the four-week window, by 2026-09-02).

---

## Setup

**If this project's folder is inside OneDrive-synced storage — put the venv outside it.**
Cloud-sync clients (OneDrive, Dropbox, iCloud) dehydrate rarely-touched files to save
space, and a venv's compiled `.so` extensions are exactly the kind of file that gets
evicted, then breaks on import days later with an opaque `mmap ... errno=60` error
(hit this exact failure 2026-08-23, on `scipy.linalg`). Code/data/docs are fine to
keep in OneDrive; the venv specifically shouldn't be.

```bash
python3 -m venv ~/.venvs/meritocracy_project
source ~/.venvs/meritocracy_project/bin/activate     # Windows: ...\Scripts\activate
pip install -r requirements.txt
```

## Get the data

**World Values Survey** — free, but gated behind login + accepting their Data Usage
Agreement, so there's no plain `curl` one-liner for this one (the download link is
tied to an authenticated session, and scripting past that isn't something to automate
around). Two legitimate options:

1. Browser: go to https://www.worldvaluessurvey.org/WVSDocumentationWVL.jsp, download
   the **Longitudinal (Trend) file, 1981–2022** (CSV or Stata), save it to `data/raw/`.
2. Scripted, after logging in once via browser: export your session cookies (e.g. the
   "Get cookies.txt" browser extension) to `wvs_cookies.txt`, then reuse that session
   for the actual download link shown on the site:
   ```bash
   curl -L -b wvs_cookies.txt -o data/raw/wvs.zip "<the download URL from the site>"
   ```

Once you have the zip (from either path — WVS ships the CSV zipped, filename usually
`F<request-id>-WVS_Time_Series_<years>_csv_v<version>.zip`), extract and place it:

```bash
cd ~/Downloads   # or wherever the zip landed
unzip -o "F<request-id>-WVS_Time_Series_1981-2022_csv_v5_0.zip" -d wvs_extracted
find wvs_extracted -iname "*.csv"   # confirm the actual CSV filename inside
cp wvs_extracted/*.csv /path/to/meritocracy_project/data/raw/WVS_TimeSeries_1981_2022_v5_0.csv
```
The destination filename must match `WVS_FILE` in `src/config.py` (already updated to
`WVS_TimeSeries_1981_2022_v5_0.csv` for the v5.0 release) — if WVS ships a different
version later, update that constant to match.

**WVS/EVS variable dictionary** — needed to actually verify the variable codes in
`src/config.py`'s `WVS_VARS`, on the same login-gated page as the raw data:

1. Go to https://www.worldvaluessurvey.org/WVSEVStrend.jsp (same session as the data
   download above)
2. Under "IVS Documentation", download **`Common_EVS_WVS_Dictionary_IVS.xlsx`** (and
   optionally `EVS_WVS_ParticipatingCountries.xlsx`, useful for double-checking the
   country crosswalk)
3. Copy them into the project so they're referenced from one place:
   ```bash
   cp ~/Downloads/F*-Common_EVS_WVS_Dictionary_IVS.xlsx data/raw/WVS_EVS_Dictionary.xlsx
   cp ~/Downloads/F*-EVS_WVS_ParticipatingCountries*.xlsx data/raw/WVS_EVS_ParticipatingCountries.xlsx
   ```
   (Neither is committed — same `data/raw/*` gitignore rule as the data files; WVS
   documentation isn't ours to redistribute either.)
4. **Done** — every code in `WVS_VARS` has been checked against this dictionary
   (2026-08-23) and matches its assumed meaning. See `config.py`'s inline comments for
   what was checked and when. The one thing this dictionary doesn't cover is
   value-level response coding (e.g. confirming `S001`'s 1=EVS/2=WVS) — it's a
   variable-name/label dictionary, not a full codebook with response categories; that
   coding is the documented WVS-wide convention, not literally re-derived from this
   file.
5. If a future WVS release changes a code, fix the mapping in `WVS_VARS` and re-run
   `01_load_clean.py`.

**SWIID (inequality)** — free, no login, hosted on Harvard Dataverse. Verified working
(tested 2026-08-23, downloads the real v9.92 archive):

```bash
curl -L -o data/raw/swiid.zip "https://dataverse.harvard.edu/api/access/datafile/13657070"
unzip -o data/raw/swiid.zip -d data/raw/swiid_extracted
cp data/raw/swiid_extracted/swiid9_92/swiid9_92_summary.csv data/raw/swiid_summary.csv
```
That file ID is the current SWIID release (v9.92). If a later version has replaced it,
the exact filenames inside the zip will differ too — check with `unzip -l data/raw/swiid.zip`
and adjust the `cp`. Current release/file ID: https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/LM4OWF

Neither file is committed — see `.gitignore`.

**World Bank GDP per capita** — free, no login, no session cookies needed.
Supports an additional (not pre-registered) robustness check — see "Method"
below:

```bash
curl -L -o /tmp/wb_gdp.zip "https://api.worldbank.org/v2/en/indicator/NY.GDP.PCAP.PP.KD?downloadformat=csv"
unzip -o /tmp/wb_gdp.zip -d /tmp/wb_gdp_extracted
cp /tmp/wb_gdp_extracted/API_NY.GDP.PCAP.PP.KD_*.csv data/raw/wb_gdp_pc.csv
```
`NY.GDP.PCAP.PP.KD` is GDP per capita, PPP (constant international $) —
comparable across countries the same way SWIID's Gini is, which is why this
one was picked over a current-dollar series. If the file World Bank ships
has a different name inside the zip, the `cp` above needs the actual
filename - check with `unzip -l /tmp/wb_gdp.zip`. Not committed - same
`data/raw/*` gitignore rule as the other raw files.

## Validate the pipeline before touching real data

```bash
python src/00_synthetic_smoke_test.py
```

This fabricates WVS/SWIID/World Bank-shaped data with a known, injected effect (matching H1/H2/H3's
registered directions) and runs it through the full 01→02→03 pipeline, checking that
the pipeline runs cleanly and recovers the injected signs. This is the artifact behind
the OSF registration's process-rigor claim ("analysis code was written and validated
against synthetic data before either dataset was accessed") — re-run it after any
change to `src/`, before trusting it on real data.

## Run

```bash
python src/01_load_clean.py       # harmonise, recode, merge inequality + GDP
python src/02_explore.py          # descriptives, distributions, country scatter
python src/03_models.py           # OLS, fixed effects, interaction
```

Outputs land in `output/figures/` and `output/tables/`.

---

## Variables

| Name | WVS code | WVS item | Coding |
|---|---|---|---|
| `luck_belief` | `E040` | hard work vs. luck and connections | 1–10, higher = more luck-attributing |
| `just_benefits` | `F114A` | claiming unentitled government benefits | 1–10, higher = more justifiable |
| `just_taxes` | `F116` | cheating on taxes | 1–10 |
| `just_bribe` | `F117` | accepting a bribe | 1–10 |
| `just_steal` | `F114B` | stealing property — **waves 6–7 only** | 1–10 |
| `norm_index` | — | mean of available standardized items above | z-scored |
| `trust` | `A165` | most people can be trusted | binary |
| `just_divorce` | `F121` | negative control (pre-registered) — divorce, unrelated to economic norm violation | 1–10 |
| `gini` | — | SWIID disposable-income Gini | country-year |
| `gini_c` | — | `gini`, grand-mean centered (used in the M3 interaction) | country-year |
| `gdp_pc` | — | World Bank GDP per capita, PPP — **not pre-registered** | country-year |
| `gdp_pc_1000_c` | — | `gdp_pc` in $1,000s, grand-mean centered (used in the GDP control check) | country-year |

All codes above are **confirmed against the official
`Common_EVS_WVS_Dictionary_IVS.xlsx`** (2026-08-23, copy at
`data/raw/WVS_EVS_Dictionary.xlsx`) — see "Get the data" above for where that came
from. Two real errors were caught this way and are now fixed: the code originally
used for `just_steal` (`F115`) turned out to be "avoiding a fare on public transport,"
not stealing — the real stealing item, `F114B`, only exists in waves 6–7, which is why
`just_steal` has much lower coverage than the other three (fine: `norm_index` uses the
mean of whichever items each respondent has). The negative control originally used
`F120` on the assumption it was "divorce" — it's actually "Abortion"; `F121` is the
real Divorce item.

`X001` (sex), `X003` (age), `X025` (education), `X028` (employment), `X047_WVS`
(income decile), `S018`/`weight` (equilibrated weight — confirmed the "equilibrated"
one is S018, not S017), and `S001`/`study` are also confirmed against the same
dictionary.

WVS variable codes differ across waves. The mapping lives in `src/config.py` and
**must be verified against the codebook before trusting any result.**

WVS numeric country codes are matched to SWIID's country names automatically
(`src/country_crosswalk.py`, via pycountry + fuzzy matching). Running
`01_load_clean.py` writes `output/tables/country_match_report.csv` listing every
code that didn't match cleanly — confirm those against your actual files and add
fixes to `MANUAL_COUNTRY_OVERRIDES` in `src/config.py`. The GDP merge uses a
separate, simpler match (numeric → ISO alpha-3, both straight from pycountry —
no fuzzy name matching needed since World Bank identifies countries by code, not
free text); unresolved codes are printed to the console rather than written to
their own report, and go in `MANUAL_COUNTRY_OVERRIDES_ALPHA3` if confirmed.

---

## Method

Three specifications, each stricter than the last:

1. **Pooled OLS** — outcome on `luck_belief` plus individual controls.
2. **Country + wave fixed effects** — identifies off within-country variation only.
   **Primary spec for H1**; where M1 and M2 disagree, M2 governs.
3. **Interaction with Gini** (grand-mean centered) — tests whether the slope
   steepens with inequality. Reported as descriptive-only if fewer than 100
   country-wave clusters have matched Gini values (see `MIN_GINI_CLUSTERS_FOR_M3`
   in `config.py`) — `03_models.py` labels this in the console output and in
   `regression_results.csv`'s `underpowered` column.

Standard errors clustered at country-wave. **Weighted least squares (WLS)** using the
WVS equilibrated post-stratification weight (`S018`/`weight`), not plain OLS — see
`fit()` in `03_models.py`.

**Sample:** inclusion requires non-missing `luck_belief` and at least one of the four
justifiability items; waves before wave 3 are dropped; country-waves with fewer than
200 valid respondents on `luck_belief` are dropped. Both applied in `01_load_clean.py`.

**Reporting standard:** effect sizes and 95% CIs, not p-values — with n in the hundreds
of thousands, trivially small effects will be statistically significant.

**Confirmatory family:** H1 (spec 2, `norm_index`), H2 (spec 3 interaction), and H3
(spec 2, `trust`) get Holm-Bonferroni correction — see `output/tables/primary_tests_holm.csv`
after running `03_models.py`. Everything else (other justifiability items, the negative
control, robustness checks) is exploratory/diagnostic and unadjusted.

**Negative control:** an unrelated justifiability item (divorce), run separately, expected
to show no relationship with `luck_belief`.

**Reliability contingency:** Cronbach's alpha for the four items is computed and written
to `output/tables/reliability_check.csv`; if it's below 0.60, `03_models.py` prints a
loud banner saying the four items (not `norm_index`) are now primary. `01_load_clean.py`
also computes alpha separately by country and by wave (`reliability_by_group`, **not
pre-registered**) — the pooled check above assumes the four items hang together the
same way everywhere `norm_index` is used; this tests that directly instead of leaving
it assumed. Written to `output/tables/reliability_by_group.csv`.

**Robustness:** logit as an alternative to the LPM for the binary `trust` outcome;
education/income as dummies instead of ordinal scales
(`robustness_dummy_coded_covariates`, compares the `luck_belief_z` coefficient between
ordinal and dummy coding and reports the % change); excluding disproportionately
influential country-wave clusters, both results reported
(`robustness_exclude_influential_clusters`, leverage/hat-value diagnostics) — this is
the registered check, confirmed verbatim against osf.io/3gvfk: *"If any country-wave
cluster exerts disproportionate influence, models will be re-estimated excluding it
and both results reported."* `robustness_exclude_dual_reporting` (EVS/WVS overlap, via
`study`/`S001`) is a separate, **additional check not found in the registered text** —
kept because it's informative, not because it's required; on this WVS-only file it
never triggers anyway (`study` is constant). `robustness_gdp_control` (`03_models.py`)
is another **additional, not pre-registered** check: country fixed effects absorb each
country's *average* wealth level, but `gini_c` is identified mostly off within-country
Gini change across waves, and if GDP per capita moves with Gini over that same window,
`gini_c` could partly be standing in for "got richer" rather than "got more unequal."
This refits M2/M3 with country-year GDP per capita added and reports the coefficient
change — see `output/tables/gdp_control_check.csv` and `FINDINGS.md`.
`exploratory_gini_movers_did` (`03_models.py`) is a separate, **not pre-registered,
not causally identified** exploratory check: countries whose mean Gini rose between
their earliest and latest survey wave ("risers") vs. those where it didn't, compared
on the change in mean `norm_index` — a diff-in-differences-*style* comparison, not the
project's actual identification strategy (that's Stage 2's proposed diff-in-diff
around dated corruption shocks — see `RESEARCH_PLAN.md`). Which country's Gini rose
isn't randomly assigned, so this can't rule out confounding; see `FINDINGS.md` and
`output/tables/gini_movers_did.csv`.

**Transparency check:** if adding covariates drops an outcome's complete-case sample by
more than 30% relative to the unadjusted model, `03_models.py` also fits and reports
the unadjusted model (`fit_unadjusted_if_flagged`, bare `luck_belief_z` only — the
registered comparator) and writes `output/tables/sample_drop_report.csv`. A second,
FE-retained version (`fit_unadjusted_m2_if_flagged`) is reported alongside it as an
additional, non-registered comparison.

## Status

- [x] Verify variable codes against the official WVS/EVS dictionary — done
      2026-08-23, caught and fixed two real errors (`just_steal`: F115→F114B;
      negative control: F120→F121). See the Variables section above.
- [x] Verify WVS↔SWIID country matches — 103/104 resolved; Macao has no SWIID
      entry (left `NaN`, not fakeable)
- [x] Confirm the literal OSF wording for the influential-cluster robustness check —
      confirmed 2026-08-23: it's leverage/influence diagnostics, not dual-reporting
- [x] Synthetic-data pipeline validation (`src/00_synthetic_smoke_test.py`) — passing
- [x] Stage 1 descriptives (`02_explore.py`) — see `FINDINGS.md`
- [x] Stage 1 models (`03_models.py`) — see `FINDINGS.md`
- [x] GDP per capita control check (not pre-registered) — H1/H2/H3 survive,
      see `FINDINGS.md`
- [x] Pre-register Stage 1 on OSF (osf.io/3gvfk, accepted 2026-08-05)
- [ ] Pre-register Stage 3 on OSF
- [ ] Stage 3 pilot

---

## Note on interpretation

The hypothesis is about a **perception of process**, not about the character of poor
people. The mechanism being proposed — following Mani, A., Mullainathan, S., Shafir,
E., & Zhao, J. (2013), "Poverty impedes cognitive function," *Science*, 341(6149),
976–980 — is situational: the same person behaves differently under different
conditions. Any writeup should be explicit about this. See `RESEARCH_PLAN.md`'s
"Related literature" section for the fuller grounding, including work this
hypothesis builds on that isn't yet in a writeup anywhere else in this repo.
