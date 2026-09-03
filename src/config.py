"""
Configuration: paths, variable mappings, recode rules.

IMPORTANT
---------
The WVS variable codes below are used in the Longitudinal (Trend) file. Most have
been confirmed against the official Common_EVS_WVS_Dictionary_IVS.xlsx (2026-08-23,
copy at data/raw/WVS_EVS_Dictionary.xlsx) - see each entry's inline comment for what's
verified vs. assumed. Two real errors were caught this way: F115 (assumed "stealing")
is actually "avoiding a fare on public transport" - the real stealing item is F114B;
F120 (assumed "divorce") is actually "Abortion" - the real divorce item is F121.
Both are fixed below. Codes differ between the trend file and individual-wave files,
and some items are not asked in every wave.

Codebook: https://www.worldvaluessurvey.org/WVSEVStrend.jsp (under "IVS Documentation")
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "output" / "figures"
TABLES = ROOT / "output" / "tables"

for _d in (RAW, PROCESSED, FIGURES, TABLES):
    _d.mkdir(parents=True, exist_ok=True)

# Set this to whatever you actually downloaded.
WVS_FILE = RAW / "WVS_TimeSeries_1981_2022_v5_0.csv"
SWIID_FILE = RAW / "swiid_summary.csv"
# World Bank WDI, indicator NY.GDP.PCAP.PP.KD (GDP per capita, PPP, constant
# 2021 international $). NOT part of the OSF registration - added only to
# support the additional, non-registered robustness check in 03_models.py
# that asks whether gini_c/the H2 interaction survive controlling for
# country-year wealth level. See README.md for the download (free, no login).
GDP_FILE = RAW / "wb_gdp_pc.csv"
CLEAN_FILE = PROCESSED / "analysis.parquet"

# --------------------------------------------------------------------------
# WVS variable mapping  ->  VERIFY THESE
# --------------------------------------------------------------------------
# Trend-file codes. `S` variables are study/meta, `A`/`E`/`F` are items.
WVS_VARS = {
    # --- identifiers / meta -------------------------------------------------
    # S002VS/S003/S020 CONFIRMED against the dictionary 2026-08-23: S002VS =
    # "Chronology of EVS-WVS waves" (dictionary lists it as lowercase
    # "s002vs" - inconsistent casing in their spreadsheet, same variable);
    # S003 = "Country (ISO 3166-1 Numeric code)" - direct primary-source
    # confirmation for country_crosswalk.py's core assumption; S020 = "Year
    # survey".
    "S002VS": "wave",          # wave number
    "S003": "country_code",    # country (numeric ISO-ish)
    "S020": "year",            # year of survey
    # CORRECTED 2026-08-23: S017 is NOT equilibrated (WVS labels it "weight
    # [with split ups]" - it sums to the true sample size per country-wave,
    # so larger-sample countries dominate a pooled/no-FE model). S018 is the
    # actual equilibrated weight (WVS label "equilibrated weight-1000" -
    # confirmed empirically: sums to a constant 1000 per country-wave). This
    # is what WEIGHT_VAR (config.py) should point to for cross-national
    # pooling to be meaningful.
    "S018": "weight",          # equilibrated weight (sums to 1000/country-wave)
    "S017": "weight_raw",      # NOT equilibrated - kept for sensitivity checks only
    # Source study, 1=EVS 2=WVS - used for the dual-reporting robustness check
    # (OSF 3gvfk). Variable name/label ("Study") confirmed against the
    # dictionary 2026-08-23; the 1=EVS/2=WVS value coding is the documented
    # WVS-wide convention, not re-derived from a value-label table (this
    # dictionary only lists variable names/labels, not response categories).
    "S001": "study",

    # --- key independent variable ------------------------------------------
    # "In the long run hard work usually brings a better life" (1)
    #   ... vs ...
    # "Hard work doesn't generally bring success - it's more a matter of
    #  luck and connections" (10)
    "E040": "luck_belief",

    # --- outcomes: justifiability (1 never .. 10 always) --------------------
    # CONFIRMED against the official Common_EVS_WVS_Dictionary_IVS.xlsx
    # (2026-08-23, see data/raw/WVS_EVS_Dictionary.xlsx):
    # - F114 splits into F114A-F114E in the trend file. F114A = "Claiming
    #   government benefits to which you are not entitled" (all 7 waves,
    #   412,715 non-missing) - correct.
    # - F114B = "Stealing property" - this is the fourth registered item.
    #   Only available in waves 6-7 (135,525 non-missing), which is fine:
    #   norm_index is the mean of *available* items per respondent, so
    #   waves 1-5 just contribute 3 items instead of 4.
    # - F115 is actually "Avoiding a fare on public transport", NOT
    #   stealing - it was wrongly used for just_steal before this fix and
    #   is now unused.
    "F114A": "just_benefits",  # claiming government benefits not entitled to
    "F116": "just_taxes",      # cheating on taxes
    "F117": "just_bribe",      # accepting a bribe
    "F114B": "just_steal",     # stealing property (waves 6-7 only)

    # --- secondary outcome ---------------------------------------------------
    "A165": "trust",           # most people can be trusted (1 yes, 2 no)

    # --- negative control (OSF 3gvfk, pre-registered) -----------------------
    # Same 1-10 justifiability format, conceptually unrelated to economic
    # cheating. Tests whether an effect is response-style/general moral
    # permissiveness rather than specific to economic norm violation.
    # CORRECTED 2026-08-23: F120 is actually "Abortion", not Divorce -
    # F121 is the real "Justifiable: Divorce" item, confirmed against the
    # dictionary. Switched to keep this consistent with what the project
    # docs already describe.
    "F121": "just_divorce",

    # --- individual controls -------------------------------------------------
    "X001": "sex",             # 1 male, 2 female
    "X003": "age",
    "X025": "education",       # highest level attained
    # CONFIRMED against the real v5.0 file: X047 is split into X047_WVS (the
    # harmonized 1-10 scale, 407,296 non-missing, all waves), X047R_WVS (a
    # collapsed 1-3 tertile recode - wrong shape, not used), and X047CS
    # (country-specific variant, far lower coverage - not used).
    "X047_WVS": "income_decile",  # subjective income scale 1-10
    "X028": "employment",
}

# Items that make up the composite outcome
NORM_ITEMS = ["just_benefits", "just_taxes", "just_bribe", "just_steal"]

# Pre-registered negative control - NOT part of the composite, run separately.
NEGATIVE_CONTROL = "just_divorce"

# --------------------------------------------------------------------------
# Missing-value codes
# --------------------------------------------------------------------------
# WVS encodes non-response as negatives; some files use large positives.
MISSING_CODES = [-1, -2, -3, -4, -5, -6, -7, -8, -9, 999, -999]

# Plausible ranges after recoding. Values outside -> NaN.
VALID_RANGES = {
    "luck_belief": (1, 10),
    "just_benefits": (1, 10),
    "just_taxes": (1, 10),
    "just_bribe": (1, 10),
    "just_steal": (1, 10),
    "age": (15, 105),
    "income_decile": (1, 10),
    "education": (1, 9),
    "just_divorce": (1, 10),
    "study": (1, 2),
}

# Sample-drop transparency threshold (OSF 3gvfk, pre-registered): flag any
# outcome where adding covariates shrinks the complete-case sample by more
# than this fraction.
COVARIATE_DROP_FLAG = 0.30

# Registered exclusion criterion: WVS waves before 3 are dropped (inconsistent
# item fielding in earlier waves).
MIN_WAVE = 3

# Registered contingency: if the Gini merge yields fewer than this many
# matched country-wave clusters, M3 is reported as descriptive-only /
# underpowered rather than a confirmatory test.
MIN_GINI_CLUSTERS_FOR_M3 = 100

# Registered contingency: if Cronbach's alpha for the four justifiability
# items falls below this, the individual items become the primary outcomes
# instead of the composite norm_index (decision must be stated explicitly).
ALPHA_CONTINGENCY_THRESHOLD = 0.60

# Registered robustness check: country-wave clusters in the top decile of
# mean per-observation leverage (hat value) on the primary M2 spec are
# flagged as disproportionately influential; M2 is reported with and without
# them.
INFLUENCE_LEVERAGE_QUANTILE = 0.90

# --------------------------------------------------------------------------
# Analysis settings
# --------------------------------------------------------------------------
CLUSTER_VAR = "country_wave"   # SE clustering level
MIN_COUNTRY_N = 200            # drop country-waves with fewer respondents
RANDOM_SEED = 20261101
WEIGHT_VAR = "weight"          # S018 equilibrated weight (see WVS_VARS comment above); WLS uses this

# --------------------------------------------------------------------------
# Country crosswalk (WVS numeric S003 -> SWIID country name)
# --------------------------------------------------------------------------
# src/country_crosswalk.py resolves most codes automatically via pycountry +
# fuzzy matching. Whatever it can't resolve (or resolves ambiguously) is
# written to output/tables/country_match_report.csv by 01_load_clean.py -
# inspect that against your actual downloaded files and pin the stragglers
# here. Format: {wvs_country_code: swiid_country_name_exactly_as_in_the_file}
#
# The three below are pre-seeded best guesses (World Bank-style naming SWIID
# commonly uses) for cases the automated matcher in country_crosswalk.py
# reliably misses - VERIFY against your actual swiid_summary.csv before
# trusting them; they are not confirmed against real data.
MANUAL_COUNTRY_OVERRIDES: dict[int, str] = {
    418: "Lao PDR",           # Laos
    417: "Kyrgyz Republic",   # Kyrgyzstan
    703: "Slovak Republic",   # Slovakia
    # Confirmed 2026-08-23 against the real downloaded swiid_summary.csv:
    275: "Palestinian Territories",  # Palestine
    364: "Iran",
    410: "Korea",                    # South Korea; SWIID doesn't distinguish
    792: "Turkey",                   # was already fuzzy-matched, pinned explicitly
    # WVS code 909 = Northern Ireland (447 rows, wave 7 only - EVS/UK
    # breakdown). SWIID has no separate NI entry, so this maps it to the UK
    # overall Gini as the closest available proxy - imperfect, but affects a
    # small subsample. Leave unmapped instead if you'd rather it stay NaN.
    909: "United Kingdom",
    # 446 (Macao) has NO SWIID match at all - it's simply not covered by
    # SWIID. Left unmapped; those rows will have gini = NaN, which is
    # correct (there's no honest proxy), not a bug to fix.
}

# Same idea as MANUAL_COUNTRY_OVERRIDES above, but for the World Bank GDP
# merge (alpha-3 codes, not free-text names). Most WVS codes resolve to a
# real ISO alpha-3 automatically via country_crosswalk.iso_numeric_to_alpha3
# and need no entry here - this dict only covers non-ISO WVS codes.
MANUAL_COUNTRY_OVERRIDES_ALPHA3: dict[int, str] = {
    # WVS code 909 = Northern Ireland - same reasoning as the Gini override
    # above: no separate World Bank entry, so UK GDP is used as the closest
    # available proxy.
    909: "GBR",
}

# --------------------------------------------------------------------------
# Pre-registered confirmatory tests (OSF 3gvfk) - Holm-Bonferroni family
# --------------------------------------------------------------------------
# (outcome, spec, param_substring, hypothesis_label). These three, and only
# these three, get the multiple-comparison correction; everything else
# (other justifiability items, the negative control, robustness checks) is
# exploratory/diagnostic and reported unadjusted.
PRIMARY_TESTS = [
    ("norm_index", "M2", "luck_belief_z",       "H1: luck_belief -> norm_index (within-country)"),
    ("norm_index", "M3", "luck_belief_z:gini_c", "H2: luck_belief x inequality interaction"),
    ("trust",      "M2", "luck_belief_z",       "H3: luck_belief -> trust (within-country)"),
]
