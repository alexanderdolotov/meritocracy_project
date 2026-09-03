# Findings — Perceived Meritocracy and Norm Violation (Stage 1)

**Alex Dolotov**
Pre-registered: [osf.io/3gvfk](https://osf.io/3gvfk/overview) (accepted 2026-08-05)
Full pipeline output: [`output/pipeline_run_log.txt`](output/pipeline_run_log.txt)
Sample: WVS Longitudinal file v5.0, waves 3–7, merged with SWIID Gini — 322,373 respondents, 104 countries, 231 country-wave clusters

---

## Question

Does believing that success comes from luck and connections rather than hard
work (`luck_belief`) predict willingness to justify economic norm violation
(`norm_index`), and does that relationship strengthen where inequality is
higher?

## Result 1: the three pre-registered hypotheses are confirmed

| Hypothesis | Spec | Coefficient | 95% CI | p (Holm-corrected) |
|---|---|---|---|---|
| H1: `luck_belief` → `norm_index` | M2 (country + wave FE) | +0.084 | [0.068, 0.100] | <0.0001 |
| H2: interaction with Gini | M3 | +0.004 | [0.001, 0.007] | 0.013 |
| H3: `luck_belief` → `trust` | M2 | −0.010 | [−0.014, −0.006] | <0.0001 |

All three are signed in the pre-registered direction and survive
Holm-Bonferroni correction across the three-test confirmatory family. None of
the three pre-specified refutation criteria hold: the association does not
disappear once country fixed effects are added, it does vary with inequality,
and it does not reverse in high-inequality countries.

A 1-SD increase in luck attribution is associated with a 0.084-SD increase in
the norm-violation composite, within the same country and survey wave. The
effect size is modest but precisely estimated, given a sample in the hundreds
of thousands, and stable under every robustness check below.

H1 is not a new finding. Kline, Galeotti & Orsini (2025) test the same core
relationship — the same WVS predictor, three of the same four outcome items — and
report a positive, significant coefficient (0.046–0.080 across their four
outcomes, their Table 4 baseline column, p<0.001 for each; verified against the
full text — local copy: `literature/kline_galeotti_orsini_2025.pdf`) in the same
direction and a comparable rough magnitude to the 0.084 above. This
project rediscovered that relationship using country + wave fixed effects (a
stricter within-country identification than their random-effects specification)
and a shifted WVS wave range (3–7, vs. their 1–6 - overlapping on waves 3–6, but
extending to wave 7 and excluding waves 1–2). H2 is the piece
that doesn't appear to have a
direct precedent: Kline et al. include Gini only as an additive control, never
interacted with the belief measure, and none of the other WVS-based studies found
here test that interaction on this outcome either — see `RESEARCH_PLAN.md`'s Related literature
for the full comparison, including a related but non-identical design (Geng, Chiu
& Wang, 2025) that tests a similar belief × macro-context interaction on
institutional trust with a different moderator.

That two independently-built pipelines - different team, non-identical wave
range, fixed effects here vs. random effects there - converge on a similar
coefficient is itself informative, though about a narrower question than it
might first sound like. It's evidence against this project's own execution
having a silent error: a coding mistake, a mismatched variable, or a broken
merge would be unlikely to coincidentally reproduce someone else's number. It's
also evidence the result isn't an artifact of the fixed- vs. random-effects
choice specifically, since both converge on it. It is not evidence on the
causal question - both studies pull from the same WVS item, so a translation
or response-style quirk in that item would show up identically in both, and
both are observational, so the reverse-causality concern in Limitations applies
to this comparison exactly as it applies to either study alone.

More broadly, H1/H2 sit inside two literatures that don't fully connect to each
other: belief-based work on luck/effort attribution and fairness (Alesina &
Angeletos, 2005; Bénabou & Tirole, 2006), which studies redistribution preferences
rather than norm violation, and country-level work on inequality and corruption
(You & Khagram, 2005; Uslaner, 2008), which doesn't measure individual belief. See
`RESEARCH_PLAN.md`'s Related literature for the fuller discussion.

**Variance explained.** The M2 model's overall R² (0.13 for `norm_index`) is
dominated by the country and wave fixed effects themselves — roughly 104
country dummies and 4 wave dummies mechanically absorb a large share of
between-group variance regardless of `luck_belief_z`. Isolating
`luck_belief_z`'s own contribution (refitting the same model without it, on
the same sample, and taking the drop in R²) gives its unique share:
**1.05% of variance in `norm_index`**, **0.04% in `trust`**. The interaction
term (H2) explains even less — 0.03–0.19% across the six outcomes here (the
negative control is treated separately, in Result 4). This is not a
p-value and is not affected by sample size the way a p-value is; it is a
direct answer to how much of the outcome `luck_belief_z` accounts for on its
own, and the answer is: precisely estimated, correctly signed, and small.
Full detail in `output/tables/incremental_r2.csv`.

## Result 2: country fixed effects change the conclusion for trust

The pooled model without fixed effects (M1) is not significant for `trust`
(coefficient −0.0061, p = 0.145, CI crosses zero). The effect appears only
once country fixed effects are added (M2: −0.0098, p < 0.0001). Pooling across
countries without fixed effects masks a real within-country relationship in
this case — the reason the pre-registration designates M2, not M1, as the
primary specification for H1.

## Result 3: robustness checks

| Check | Result |
|---|---|
| Exclude 16 highest-leverage clusters (M2, registered check) | 0.084 → 0.087 (3.3% change) |
| Education/income as dummies vs. ordinal (M2) | 0.084 → 0.084 (0.2% change) |
| Unadjusted M1 (bare `luck_belief_z`, no covariates, no FE) vs. adjusted M2 | `norm_index`: 0.096 → 0.084, both significant. `trust`: −0.005 (not significant, CI crosses zero) → −0.010 (significant) |
| Logit vs. linear probability model (trust) | Same sign, both significant |
| GDP per capita added as a control (M2, not pre-registered) | `norm_index`: 0.084 → 0.085 (1.4% change), both significant. `trust`: −0.010 → −0.011 (9.9% change), both significant |

Covariates (chiefly `education`, 34% missing) drop the estimation sample by
39–57% depending on outcome, exceeding the pre-registered 30% flag, which
triggers the registered unadjusted-model comparison above. For `norm_index`
the unadjusted and adjusted estimates are close. For `trust`, the bare
bivariate relationship is not statistically significant on its own — the
significant effect in Result 1 depends on the covariates and fixed effects
being included, consistent with Result 2's finding that fixed effects change
the conclusion for this outcome.

An additional (not pre-registered) check excluding country-wave clusters with
dual EVS/WVS reporting was not applicable here — this file contains no EVS
rows (`study` is constant).

## Result 4: the negative control

The pre-registered negative control — `just_divorce`, selected as a
justifiability item with no theoretical link to perceived meritocracy — has
an M2 coefficient of 0.131, larger than H1's own 0.084.

The pre-registered decision rule for this test: a comparable-or-larger
coefficient on an outcome with no theoretical link to perceived meritocracy
is evidence for a general response-style effect rather than the hypothesized
mechanism. By that rule, this result does not support reading H1 as specific
to economic norm violation.

That decision rule assumes `just_divorce` has no theoretical link to
`luck_belief`, and that assumption is not as clean as intended. `luck_belief`
(hard work vs. luck/connections determining success) is closely related to
locus of control (Rotter, 1966), a disposition meta-analytically linked to
effort and motivation at work specifically (Ng, Sorensen & Eby, 2006) and,
in the broader literature, to outcomes across other life domains as well -
not only economic ones. A person who
believes outcomes are mostly luck-driven could extend that belief to
relationships - "why invest effort if outcomes aren't really within my
control" - and show more permissive divorce attitudes for a substantive,
non-artifactual reason. This means a large `just_divorce` coefficient is
consistent with two different explanations that the current design cannot
distinguish: a general response-style artifact (respondents who pick high
values on `luck_belief` pick high values on any justifiability item,
regardless of content), or a genuine generalized disposition effect
(`luck_belief` capturing something broader than economic-specific beliefs,
which would predict both outcomes through a real mechanism). `just_divorce`
was selected as the specific instantiation of the registered "a candidate
WVS item unrelated to economic norms" commitment; in hindsight it carries
more of a plausible mechanism than a negative control ideally would.

If the disposition explanation is correct, that does not contradict the
underlying theory - `RESEARCH_PLAN.md`'s own framing is "a perception about
process changes behaviour," not a claim restricted to economics. It would
mean the finding is broader than "specific to economic norm violation," not
that it is spurious. The data cannot distinguish the two explanations, and
neither should be presented as the resolved one.

H1–H3 are not refuted by this result under the three pre-specified refutation
criteria, and the estimated effect is stable under every other robustness
check performed. Three statements hold simultaneously: the pattern is real
and robust; it is not demonstrated to be specific to economic norm violation;
and the negative control used to establish that cannot itself distinguish a
methodological artifact from a genuine broader mechanism.

One additional, not pre-registered, comparison is reported here for
completeness even though it complicates rather than resolves the picture:
`just_divorce`'s incremental R² (0.16%) is smaller than `norm_index`'s
(1.05%) — the coefficient comparison above and the variance-explained
comparison here rank the two outcomes in opposite order. The pre-registered
decision rule is stated in terms of coefficient magnitude, not variance
explained, so the coefficient comparison is what governs the conclusion
above; the R² comparison is reported as additional information, not used to
override or explain away the registered result.

## Result 5: Gini's own association with the outcomes (not pre-registered)

M3's formula (`luck_belief_z * gini_c`) estimates `gini_c`'s own main-effect
coefficient alongside the interaction, but only the interaction term was part
of the registered confirmatory family — `gini_c`'s own coefficient was
computed in every M3 fit and not examined until this check. Reported here for
completeness, uncorrected:

| Outcome | `gini_c` coefficient | SE | p |
|---|---|---|---|
| `norm_index` | +0.021 | 0.010 | 0.037 |
| `just_benefits` | +0.007 | 0.026 | 0.782 |
| `just_taxes` | +0.040 | 0.019 | 0.034 |
| `just_bribe` | +0.069 | 0.031 | 0.028 |
| `just_steal` | +0.024 | 0.0006 | <0.0001 |
| `trust` | +0.004 | 0.003 | 0.257 |
| `just_divorce` (negative control) | −0.091 | 0.032 | <0.01 |

`norm_index`'s association with `gini_c` net of `luck_belief_z` and the
interaction is positive and marginal (p=0.037). Two things limit how much
weight this carries: it is not Holm-corrected, and with country fixed
effects in the model, `gini_c` is identified mostly from within-country
change in inequality across survey waves, not from comparing high- and
low-inequality countries directly. `just_steal`'s standard error (0.0006) is
roughly 5 to over 50 times tighter than every other outcome's and is not treated as reliable
without further checking — `just_steal` is restricted to waves 6–7, leaving
`gini_c` very little within-country temporal variation to identify off,
which can produce an artificially precise cluster-robust standard error. The
negative control's coefficient is negative, the opposite sign from
`norm_index`'s positive one — consistent with the construct-specificity
concern in Result 4, on an already-exploratory statistic.

### Does gini_c survive controlling for GDP per capita?

Country fixed effects absorb each country's *average* wealth level, but
`gini_c` is identified almost entirely from within-country Gini change
across survey waves (see above) - the same window a country's GDP per
capita is also changing in. If wealth and inequality move together within a
country over time, `gini_c` could be standing in for "the country got
richer" rather than "the country got more unequal." Not pre-registered, but
tested directly: M2 and M3 were refit for every outcome with country-year
GDP per capita (World Bank, PPP, grand-mean centered) added as an
additional control.

Nothing changes materially. Across the six outcomes tested (`norm_index`,
the four items, `trust`), `luck_belief_z`'s M2 coefficient moves by
0.1–9.9%, `gini_c`'s own M3 coefficient moves by 2.2–31.6%, and the H2
interaction term - the one actually under moderation test - moves by
1.0–5.4%, the most stable of the three. No coefficient changes sign, and no
significance pattern flips in either direction: everything significant
before stays significant, everything not stays not. With GDP added: H1 is
0.0850 (SE 0.0083, still p<0.0001), H2's interaction is 0.0038 (SE 0.0015,
unchanged to four decimal places), H3 is −0.0108 (SE 0.0023, still
p<0.0001). Full detail in `output/tables/gdp_control_check.csv`.

The negative control (`just_divorce`) was checked too, for completeness. Its
M2 coefficient - the number Result 4's conclusion rests on - moves by only
0.5% (0.1310 → 0.1303), the smallest change of any outcome in this check.
Its `gini_c` coefficient stays negative and significant (−0.091 → −0.102),
the opposite sign from `norm_index`'s positive one that Result 5's synthesis
already reads as one signal against a pure response-style explanation. Both
negative-control findings hold up under the GDP control.

This doesn't rule out every possible development-related confound, but it
rules out the specific one this check targets: `gini_c` is not simply
proxying for country-year wealth level.

### What the negative control shows, taken together

Three separate comparisons between `norm_index` and `just_divorce` do not
agree with each other:

| Comparison | Result | Reads as |
|---|---|---|
| M2 coefficient (pre-registered test) | divorce (0.131) > norm_index (0.084) | fails the negative control |
| Incremental R² (exploratory) | divorce (0.16%) < norm_index (1.05%) | passes |
| `gini_c` association (exploratory) | opposite signs | passes |

This is a mixed result, not a clean pass or fail, and it should be read as
such. The coefficient comparison is the one stated in the pre-registration
and is what governs the conclusion in Result 4 - it was committed to before
any of these numbers existed, which is the entire reason to trust it over
the other two. The other two comparisons are reported for completeness, not
used to overturn it: one plausible, unconfirmed explanation is that country,
wave, and demographic factors already predict divorce attitudes far better
than they predict economic-norm attitudes (R²=0.24 vs. 0.13 for the full
model), leaving proportionally less variance for `luck_belief_z` to explain
even if its per-respondent coefficient is comparably sized.

### Why no better negative control was substituted

Divorce's flaw (Result 4) is not a one-off item-selection problem. `luck_belief`
is close to a general locus-of-control construct, and the theorized mechanism -
believing the system does not reward effort erodes willingness to comply with
its rules - is not inherently economic. It would just as plausibly predict
reduced compliance with any social norm: driving safely, not littering,
investing in a marriage, honesty in general. Every item in the WVS
justifiability battery is, by definition, a norm a respondent can choose to
violate, so every candidate considered as a replacement (homosexuality,
littering, drunk driving, among others) carried some version of the same
problem: either a plausible connection to a generalized disengagement-from-
norms mechanism, or - for identity/values items such as homosexuality - such
heavy stratification by religion and country that little within-country
variance would be left for `luck_belief` to act on once country fixed effects
are in the model.

No substitute was found, and none is expected to exist within this battery:
the contamination risk is a property of the item category (anything phrased
as "is this norm violation justifiable") interacting with a broad, general
predictor, not a defect specific to any one item. The only within-scale
comparison that could still isolate pure response-style bias from a real
generalized-disengagement effect would be a same-scale item with no normative
content at all - a rating rather than a moral judgment (e.g. life
satisfaction, interest in politics) - and even that would not settle whether
a real effect is economically specific, since generalized normative
disengagement would remain a live explanation either way. This is recorded as
a structural limitation of the negative-control strategy as designed, not
something a different item choice would have fixed.

This isn't only this project's own read of its own data. Allison, Wang &
Kaminsky (2021), applying item-response theory to WVS justifiability items
across 56 countries, find a single "Fairness" latent factor that bundles
`just_steal`, `just_bribe`, and `just_taxes` together with violence and
domestic-abuse justifiability - non-economic items, in an independent
dataset and method. That's consistent with the same general
permissiveness/disengagement dimension being the concern here, not a
pattern specific to this project's choice of negative control. See
`RESEARCH_PLAN.md`'s Related literature.

## Result 6: composite reliability across countries and waves (not pre-registered)

The pooled Cronbach's alpha (0.798, reported above) assumes the four
justifiability items hang together the same way in every country and every
survey wave — that assumption was never tested until now. Alpha was
recomputed separately by country and by wave, using the same formula, on
whichever complete cases exist within each group (groups with fewer than
100 complete cases are not scored — alpha on a handful of respondents is
noise, not an estimate).

**By country:** 83 of 104 countries had enough complete-case data to score.
Alpha ranges from 0.506 (Germany) to 0.959 (Ethiopia), median 0.737 —
noticeably below the pooled 0.798, and with real spread: the four items
measure a meaningfully less unified construct in some countries than
others. 21 countries had too few complete cases to score at all.

**By wave:** only waves 6 and 7 could be scored (0.818 and 0.779). Waves 3
and 5 have zero complete cases across all four items — `just_steal` is only
fielded in waves 6–7, so no respondent from an earlier wave can answer all
four simultaneously — and wave 4 has no qualifying respondents in this
sample at all. This means the by-wave check can't actually speak to whether
reliability changed across the full span this sample covers, only that it
looks stable between two adjacent waves in the 2010s–2020s.

This does not change the registered contingency: that fires on the pooled
alpha (0.798, well above the 0.60 threshold), not on any per-group value,
so `norm_index` remains the primary outcome as registered. What it does
show is a real, previously untested source of measurement variability
across countries — nothing here suggests it's correlated with
`luck_belief` in a way that would bias H1, but it means `norm_index`
behaves somewhat differently as a measure from country to country. Full
detail in `output/tables/reliability_by_group.csv`.

## Result 7: gini-movers diff-in-differences-style check (not pre-registered, not causally identified)

A different, cruder way of asking the same question M3 already answers:
split the 66 countries with at least two survey waves and a matched Gini
value into those whose mean Gini rose between their earliest and latest
available wave ("risers," n=29) and those where it didn't ("non-risers,"
n=37), then compare the change in mean `norm_index` between the two
groups. This is a two-period diff-in-differences-*style* comparison, not
the project's actual identification strategy — that's the diff-in-diff
Stage 2 proposes around actual dated corruption shocks (`RESEARCH_PLAN.md`).
It uses the same within-country Gini variation M3 already identifies off,
just aggregated to two periods and a binary split instead of used
continuously with individual-level data and country/wave fixed effects.

The estimate: risers − non-risers = +0.043 (SE 0.074, 95% CI
[−0.103, 0.188], p = 0.57) — not distinguishable from zero. Risers' mean
`norm_index` moved by +0.044 on average; non-risers' by +0.002 —
directionally consistent with H2 (rising inequality, more justification),
but with only 66 countries and a typical Gini movement between waves of
just 1.65 points — some of which is plausibly SWIID measurement noise
rather than real change (see "Gini measurement uncertainty" in
Limitations) — the difference between groups is well within noise.

This is not causally identified: which country's Gini happened to rise
over this period is not randomly assigned, so a difference here (or its
absence) could reflect anything else that changed alongside inequality in
those particular countries, not inequality itself. It doesn't strengthen
or weaken H2 — M3's individual-level, continuously-measured, fixed-effects
result is the actual test, and it already reported the correctly-signed,
Holm-corrected result in Result 1. This is reported because it's a natural
sanity check on the same finding from a cruder angle, not because it adds
identification.

There's also a conceptual mismatch here, not just a power problem. This
design implicitly treats attitude change as something that tracks Gini
movement within the survey window. Normative beliefs about corruption and
fairness plausibly form and shift on a much slower, more mediated timescale
than year-to-year inequality statistics — through lived experience,
generational turnover, and salience created by a specific narrated event or
media coverage, not by respondents tracking a Gini coefficient. A quiet
few-point drift in Gini between two survey waves, with no distinguishing
event attached to it, is a weak stimulus even setting aside the small
sample and short window. This is part of the logic behind Stage 2's
proposed design: dated corruption shocks (Lava Jato, 1MDB, Panama Papers)
are salient, widely covered events, not a slow background statistic — a
more plausible test of whether perceived unfairness moves attitudes than
tracking Gini's gradual drift. Full detail in
`output/tables/gini_movers_did.csv` and `output/figures/gini_movers_did.png`.

## Item-level detail (secondary, not Holm-corrected)

All four justifiability items move in the same direction as the composite,
each significant. These coefficients are on each item's own raw 1–10 scale,
not standardized like `norm_index`, and are not directly comparable to the
0.084 headline estimate or to each other without rescaling.

| Item | M2 coef | M3 interaction | Notes |
|---|---|---|---|
| `just_benefits` | 0.188*** | 0.0074* | |
| `just_taxes` | 0.202*** | 0.0063 (p=0.064) | interaction not significant alone |
| `just_bribe` | 0.161*** | 0.0100*** | |
| `just_steal` | 0.186*** | 0.0099 (p=0.064) | waves 6–7 only, n=78,521; interaction not significant alone |

## Limitations

- **Construct specificity:** the negative control gives a mixed result across
  three comparisons (Result 4/5 synthesis). The pre-registered comparison
  (coefficient magnitude) does not support a "specific to economic norm
  violation" reading of H1; two exploratory follow-up comparisons point the
  other way. The pre-registered comparison governs the conclusion, but the
  mixed picture itself is a limitation worth stating plainly. Beyond that:
  no suitable negative control was located within the WVS justifiability
  battery at all - `luck_belief` is close to a general
  locus-of-control construct, so the theorized mechanism plausibly extends to
  disengagement from any social norm, not just economic ones, and every
  candidate item considered (divorce, littering, drunk
  driving) carries some version of the same confound or is too stratified by
  religion/country (homosexuality) to leave usable within-country variance. This is treated
  as a structural limitation of the negative-control strategy, not an item
  that a better choice would have fixed - see "Why no better negative
  control was substituted" under Result 5.
- **Reverse causality:** Stage 1 cannot rule out that people who already
  justify cheating rationalize by concluding the system is rigged. This is
  the reason Stage 2 (identification strategy) and Stage 3 (lab experiment)
  are part of the three-stage design.
- **Self-reported justifiability is not behavior.**
- **Sample composition:** the covariate-adjusted sample is 60–61% of the full
  sample for five of the six outcomes, and 43% for `just_steal` specifically
  (restricted to waves 6–7, so it starts from a smaller bare denominator too
  — see Result 3's 39–57% drop-percentage range, which reflects the same
  gap). Not a random subset of the full sample either way. The unadjusted
  and adjusted estimates are close for `norm_index`; for
  `trust` they differ more (see Result 3). Whether the covariate missingness
  driving this drop (chiefly on `education`) is itself related to
  `luck_belief` or the outcomes was not tested directly beyond that
  comparison.
- **Cross-country comparability of survey items is imperfect,** as with any
  pooled multi-country survey instrument.
- **Country-Gini matching:** 103 of 104 countries matched cleanly to SWIID.
  Macao has no SWIID entry and is excluded from the Gini-dependent models
  rather than imputed.
- **Gini measurement uncertainty:** the SWIID values used here are point
  estimates from the summary file (`swiid_summary.csv`), not the full set of
  100 multiple-imputation replicates SWIID provides specifically because
  Gini estimates carry real uncertainty — larger for countries with sparser
  underlying survey coverage. Treating Gini as measured without error means
  the confidence intervals on H2 and on the `gini_c` coefficients in Result 5
  likely understate the true uncertainty on the inequality side.
- **Composite reliability:** Cronbach's alpha varies by country (0.506 to
  0.959, median 0.737 across the 83 countries with enough data to score —
  see Result 6), noticeably more spread than the pooled 0.798 suggests.
  `norm_index` does not behave identically as a measure everywhere it is
  used; nothing in this spread points toward a bias on H1, but it is a real
  source of measurement variability the pooled alpha alone doesn't show.

## Summary

The pre-registered pattern — luck attribution predicting justification of
economic norm violation, moderated by inequality — is present in the data,
correctly signed, statistically robust after correction for multiple
comparisons, and stable across leverage, coding, sample-composition,
functional-form, and country-year GDP per capita checks. It is also small: `luck_belief_z` accounts for about
1% of the variance in `norm_index` and less than 0.1% in `trust`, net of
country, wave, and demographic factors. The pre-registered negative control
does not support reading the effect as specific to economic norm violation,
by the coefficient-magnitude test the registration commits to - but the
control item (`just_divorce`) has a plausible mechanism of its own (locus of
control extending to relationship effort), so a large coefficient there is
consistent with either a response-style artifact or a genuine disposition
broader than economic beliefs; the data cannot distinguish the two. No
better negative control was available to resolve this: `luck_belief` is
close to a general locus-of-control construct, and every candidate
justifiability item considered carries either the same disengagement
mechanism or too much religious/country stratification to be usable, so the
ambiguity is treated as a structural limitation of the negative-control
strategy rather than a fixable item choice. All findings - real and robust,
small in variance-explained terms, and not demonstrated to be
construct-specific for reasons the study cannot fully resolve - are reported
together as part of Stage 1's result, consistent with the pre-registration's
confirmatory design. Two further checks, both exploratory and reported for
completeness rather than to support or weaken the pre-registered
conclusion: the composite's reliability varies more across countries than
the pooled 0.798 alone suggests (Result 6), and a cruder, country-level
diff-in-differences-style comparison of Gini-rising vs. Gini-stable
countries finds the predicted direction but no statistically
distinguishable effect (Result 7) — a much lower-powered version of the
same test M3 already answers with individual-level data.

## Supporting files

- `output/pipeline_run_log.txt` — full console output from all three pipeline scripts, single run
- `output/tables/primary_tests_holm.csv` — H1/H2/H3 with Holm correction
- `output/tables/regression_results.csv` — every coefficient from every specification, including unadjusted models
- `output/tables/sample_drop_report.csv` — the covariate sample-drop check
- `output/tables/incremental_r2.csv` — variance uniquely explained by `luck_belief_z` and its interaction with Gini, per outcome (not pre-registered)
- `output/tables/gdp_control_check.csv` — M2/M3 coefficients with vs. without country-year GDP per capita added as a control (not pre-registered)
- `output/tables/reliability_by_group.csv` — Cronbach's alpha by country and by wave (not pre-registered)
- `output/tables/gini_movers_did.csv` — the country-level Gini-movers diff-in-differences-style comparison (not pre-registered, not causally identified)
- `output/figures/gini_movers_did.png` — the same comparison, plotted
- `output/tables/data_quality_checks.csv` — the 21 data-quality checks run before modeling
- `output/tables/reliability_check.csv` — Cronbach's alpha (0.798) for the composite
- `output/figures/negative_control_comparison.png` — negative-control comparison, plotted
- `output/figures/marginal_effect_norm_index.png` — H2's interaction across the Gini range
- `output/figures/country_scatter.png` — country-level descriptive view

## References

- Kline, R., Galeotti, F., & Orsini, R. (2025). Meritocracy or malfeasance:
  violations of meritocracy erode civic rule following. *Frontiers in Behavioral
  Economics*, 4, 1492421. https://doi.org/10.3389/frbhe.2025.1492421
- Ng, T. W. H., Sorensen, K. L., & Eby, L. T. (2006). Locus of control at work: A
  meta-analysis. *Journal of Organizational Behavior*, 27(8), 1057–1087.
- Rotter, J. B. (1966). Generalized expectancies for internal versus external
  control of reinforcement. *Psychological Monographs*, 80(1), 1–28.

See `RESEARCH_PLAN.md`'s References for the fuller literature grounding the
hypotheses themselves, including Geng, Chiu & Wang (2025), mentioned above but
not listed separately here.
