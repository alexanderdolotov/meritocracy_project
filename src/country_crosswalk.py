"""
ISO-3166-1 numeric <-> country-name helpers, used to merge WVS (`country_code`,
numeric) with SWIID (`country`, free-text name).

WVS documentation states S003 follows ISO 3166-1 numeric, but this is not
airtight: a handful of non-sovereign or historical entities in some WVS/EVS
waves (e.g. Northern Ireland coded apart from Great Britain, USSR-era codes
in very early waves) have no ISO numeric equivalent and cannot be resolved
here. Those go in MANUAL_COUNTRY_OVERRIDES in config.py once you can see them
in your actual downloaded file — see output/tables/country_match_report.csv
after running 01_load_clean.py.

We do NOT hand-maintain a giant numeric -> name table (error-prone, and there
is no way to verify 200 codes without the real files). Instead we generate it
from `pycountry` (the standard ISO 3166 dataset) and do fuzzy, inspectable
matching against whatever SWIID actually calls each country.
"""

import re
import unicodedata
import pycountry

# {ISO numeric code (int): official short name}
iso_numeric_to_name: dict[int, str] = {
    int(c.numeric): c.name for c in pycountry.countries if getattr(c, "numeric", None)
}

# {ISO numeric code (int): ISO alpha-3 code}. Used for the World Bank GDP
# merge (01_load_clean.py's merge_gdp()) - World Bank identifies countries by
# alpha-3, not by free-text name the way SWIID does, so this join doesn't
# need the fuzzy-name matching above at all: numeric -> alpha-3 is a direct
# ISO-to-ISO lookup, both sides from the same pycountry table.
iso_numeric_to_alpha3: dict[int, str] = {
    int(c.numeric): c.alpha_3 for c in pycountry.countries if getattr(c, "numeric", None)
}

# Word-level substitutions applied before comparing names. SWIID tends to use
# World Bank-style short names ("Korea, Rep.", "Egypt, Arab Rep.", "Iran,
# Islamic Rep.") while pycountry uses ISO official names ("Korea, Republic
# of", "Egypt", "Iran, Islamic Republic of") - this closes most of that gap.
#
# NOTE: these patterns match AFTER punctuation (commas, periods, parens) has
# already been stripped and whitespace collapsed - write them without commas.
_SUBSTITUTIONS = [
    (r"\brep\b", "republic"),
    (r"\bdem\b", "democratic"),
    (r"\bst\b", "saint"),
    (r"\bunited states of america\b", "united states"),
    (r"\brussian federation\b", "russia"),
    (r"\bviet nam\b", "vietnam"),
    (r"\blao peoples democratic republic\b", "laos"),
    (r"\bsyrian arab republic\b", "syria"),
    (r"\btanzania united republic of\b", "tanzania"),
    (r"\bmoldova republic of\b", "moldova"),
    (r"\bmacedonia the former yugoslav republic of\b", "macedonia"),
    (r"\bnorth macedonia\b", "macedonia"),
    (r"\bczechia\b", "czech republic"),
    (r"\bcote divoire\b", "ivory coast"),
    (r"\bbolivia plurinational state of\b", "bolivia"),
    (r"\bvenezuela bolivarian republic of\b", "venezuela"),
    (r"\btaiwan province of china\b", "taiwan"),
    (r"\bhong kong\b", "hong kong sar china"),
    (r"\bpalestine state of\b", "palestine"),
    # Generic cleanup for the many ISO names of the form "X, Y of" where
    # SWIID just uses "X, Y" - strip a dangling trailing "of".
    (r"\bof$", ""),
]


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation, apply known aliasing - for matching only."""
    if not isinstance(name, str) or not name:
        return ""
    # Fold diacritics (Côte d'Ivoire -> Cote d'Ivoire, Curaçao -> Curacao, ...)
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[’'`.]", "", s)
    s = re.sub(r"[,()]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    for pattern, repl in _SUBSTITUTIONS:
        s = re.sub(pattern, repl, s)
    s = re.sub(r"\s+", " ", s).strip()
    return s
