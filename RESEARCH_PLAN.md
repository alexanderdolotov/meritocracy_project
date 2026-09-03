# Perceived Meritocracy and Norm Violation

**Research plan — MIT DEDP master's application**
Alex Dolotov · draft

Pre-registered on OSF: [osf.io/3gvfk](https://osf.io/3gvfk/overview) accepted 2026-08-05.
Stage 1 results are in [`FINDINGS.md`](FINDINGS.md).

**Timeline:** the analysis completed within the four-week window, by **2026-09-02**.

---

## The question

When people believe advantage is allocated by luck and connections rather than effort,
do they become more willing to violate economic norms — and is that relationship
stronger where inequality is higher?

The claim under test is **not** that poor people are less honest. It is that a
*perception about process* changes behaviour, and that the perception is itself
shaped by the structure of the economy people live in.

## Why it matters for policy

The project's starting motivation is Piketty's argument (quoted in full in Related
literature, below) that when capital's return persistently outpaces economic growth
(r > g), wealth concentrates in ways no individual's effort determines — producing,
in his words, "arbitrary and unsustainable inequalities that radically undermine the
meritocratic values on which democratic societies are based." If perceived
unmeritocratic *concentration* is what actually drives H1 (`luck_belief` predicting
justification of norm violation) and H2 (that association strengthening with
inequality — both defined in full under Three-stage design, below), rather than
income inequality generally, the policy implication is not
chiefly about how transfers to low earners are structured (conditional vs.
unconditional) but about taxing the capital stock that concentration accrues in.

Piketty's own proposed remedy was a global wealth tax; Saez & Zucman (2019) develop a
more administrable version aimed at the U.S. case specifically. If `luck_belief` and
its downstream effects on norm violation and trust respond to wealth concentration
rather than income inequality generally, that is a direct behavioral argument for
taxing capital stock itself, not just income or consumption.

**A measurement gap this framing exposes.** H2's registered moderator is SWIID
Gini — income inequality, not the wealth-*stock* concentration Piketty's argument is
actually about. The World Inequality Database (top income and wealth shares, already
listed under Data sources) would test the wealth-concentration channel more directly;
see Next steps for this as a proposed, non-registered extension rather than a
substitute for the registered H2 specification.

## Related literature

**Where this started.** The starting intuition for this project, before any of the
papers below were located, was Piketty (2014). Piketty argues that extreme
capital-income inequality (via r > g, capital's return outpacing economic growth)
produces, in his words, "arbitrary and unsustainable inequalities that radically
undermine the meritocratic values on which democratic societies are based." That
argument is about the legitimacy of a whole economic
system, not about individual belief predicting individual rule-violation - Piketty
doesn't run anything resembling H1-H3, and the book is a work of economic history
and political economy, not survey-based social science. But it's the conceptual
seed of H2's specific prediction: the belief-to-norm-violation link should
strengthen where inequality is starker, because that is where meritocratic
legitimacy is under the most strain. This project is meant to check this idea.

**H1 is a rediscovery, not a discovery - checked directly against the closest
predecessor, PDF now read in full (`literature/kline_galeotti_orsini_2025.pdf`).**
Kline, Galeotti & Orsini (2025) already test the same core relationship as this
project's H1: the same WVS item as this project's `luck_belief`/E040 - they don't
cite a variable code, but the wording they quote ("hard work brings success" vs.
"luck and connections") is identical to this project's own item text - against
three of this project's four outcome items (bribery, benefits fraud, tax cheating -
their fourth is fare evasion, this project's is stealing property), across WVS waves
1-6 (1981-2014, 77 countries; both figures stated directly in their text), combined
with a lab experiment (a letter-counting task ranks participants as high- or
low-performers, then crosses equal/unequal pay with whether that pay honors or
violates the performance ranking, followed by a misreporting/honesty measure,
their term for it: the "custodial stage").

They report a positive, significant relationship (coefficients 0.046-0.080, p<0.001 across
all four outcomes, their Table 4 baseline column) - the same direction, and a comparable rough magnitude, to this
project's own 0.084 for `norm_index` (`FINDINGS.md`, Result 1). Three things do
differ from this project's design: (1) they use a multilevel model with random
intercepts and slopes; this project uses country + wave *fixed* effects as the
primary specification, a stricter within-country identification that doesn't
require assuming the random country effect is uncorrelated with the predictors. (2)
They include Gini only as an additive country-level control, never interacted with
the belief measure - H2 (does the effect itself strengthen with inequality) is not
tested there, and does not appear to have a direct precedent elsewhere either. (3)
They don't test a trust outcome. Their lab experiment is also worth flagging
directly against Stage 3, below, but not as closely as it might first appear:
their endowments are always performance-based - there is no luck or
random-assignment condition anywhere in their design. What they randomize is
whether the resulting *pay* honors or violates that performance ranking, then
measure a subsequent misreporting outcome. Stage 3 needs to engage with this
design explicitly rather than be framed as an untried design space, but its
proposed effort-vs-random-assignment manipulation is a genuinely different
treatment from theirs, not a rerun of it.

**A related cross-level design, different moderator and outcome.** Geng, Chiu &
Wang (2025) test meritocracy belief's relationship with institutional trust across
84,638 WVS respondents in 57 societies, finding the relationship holds only in
societies with more economic freedom - the same underlying design logic behind this
project's H2 and H3 (individual belief × macro-context interaction, trust as an
outcome), applied to a different trust measure (institutional, not generalized).
Their abstract states they also collected society-level economic inequality data
alongside economic freedom, but economic freedom is the moderator in their
headline finding.

**Beliefs about luck vs. effort and redistribution preferences.** Alesina & Angeletos
(2005) show experimentally and cross-nationally that whether people believe outcomes
are effort-driven or luck/connections-driven shapes support for redistribution -
people are far more tolerant of inequality they see as earned. Bénabou & Tirole
(2006) model "belief in a just world" (the world is fair, effort is rewarded) as a
motivated belief that itself responds to policy and culture, not just a fixed prior -
relevant here because it implies `luck_belief` is not simply exogenous, which is part
of why Stage 1 cannot establish direction (see Limitations, and Stage 2 below). Both
papers are about redistribution preferences, not norm violation directly - this
project's outcome (willingness to justify cheating, bribery, tax evasion) is a
different, more behaviorally-adjacent measure than a stated redistribution preference.

**Inequality and corruption/norm tolerance.** You & Khagram (2005) find inequality
predicts corruption cross-nationally and argue part of the mechanism is normative:
high inequality erodes the perceived legitimacy of the rules. Uslaner (2008) proposes
a related but distinct channel - inequality lowers generalized trust, and low trust
enables corruption - and reports a weaker direct inequality-corruption link than You &
Khagram once trust is accounted for. Neither uses individual-level *belief* data;
both work with country-level inequality and country-level corruption indices. H2
(does the `luck_belief` effect strengthen with country-year Gini) is this project's
individual-level, belief-based version of the same underlying question - and, per
the Kline et al. comparison above, the one piece of H1-H3 that doesn't appear to
already exist in a closely comparable form elsewhere.

**The situational mechanism.** Mani, Mullainathan, Shafir & Zhao (2013) show the same
person's cognitive performance changes with their financial circumstances (comparing
farmers before vs. after harvest) - direct evidence that scarcity is situational, not
a fixed trait of poor people. This project's framing - that `luck_belief` reflects a
perception shaped by circumstance, not a stable character trait - follows the same
logic, applied to normative beliefs rather than cognition. See also "Note on
interpretation" in `README.md`.

**Do the four justifiability items measure one thing?** Allison, Wang & Kaminsky
(2021) apply item response theory to WVS justifiability items across 56 countries and
find `just_steal`, `just_bribe`, and `just_taxes` load strongly (loadings -0.70 to
-0.77) onto a single latent "Fairness" dimension - independent confirmation, from a
different dataset and method, of this project's own Cronbach's alpha check
(`FINDINGS.md`, Result 6). Their Fairness dimension also includes violence and
domestic-abuse justifiability alongside the economic items, which is worth flagging
given `FINDINGS.md`'s negative-control discussion: it's consistent with the concern
that these items may share a general permissiveness/disengagement factor that isn't
narrowly economic - not something this project discovered in isolation.

Full citations in References, below.

---

## Three-stage design

### Stage 1 — Establish the pattern (descriptive, this repo)

**Data:** World Values Survey, waves 3–7, ~100 countries, individual level.
Merged with country-year inequality (SWIID Gini).

**Independent variable.** WVS asks respondents to place themselves on a 1–10 scale between:

> 1 = "In the long run, hard work usually brings a better life"
> 10 = "Hard work doesn't generally bring success — it's more a matter of luck and connections"

This is a direct measure of perceived meritocracy. Call it `luck_belief`.

**Outcome variables.** WVS justifiability items, each 1 (never justifiable) – 10 (always):

- claiming government benefits you are not entitled to
- cheating on taxes
- accepting a bribe
- stealing property

Three of these four load strongly onto a single latent factor in independent
WVS-based work (Allison, Wang & Kaminsky, 2021 - see Related literature, above);
use both the individual items and a standardised index.

**Secondary outcome.** Generalised trust (binary: most people can be trusted).

**Covariates (registered):** sex, age, age², education, subjective income decile.

**Sample (registered).**

- **Inclusion:** non-missing `luck_belief`, and at least one of the four justifiability
  outcome items non-missing.
- **Exclusion:** WVS missing-value codes and out-of-range values set to missing; waves
  before wave 3 dropped (inconsistent item fielding); country-waves with fewer than 200
  valid respondents on `luck_belief` excluded.
- **Sample size:** fixed by the existing datasets — no a priori power analysis; expected
  150,000–300,000 respondents across 250–400 country-wave clusters. With n in the
  hundreds of thousands, trivially small effects will reach statistical significance, so
  **effect sizes and 95% CIs are the primary quantities reported, not p-values.**

**Specifications, in order:**

1. Pooled OLS, outcome on `luck_belief`, individual controls.
2. Add country and wave fixed effects — identifies off *within-country* variation,
   removing time-invariant national culture. **This is the pre-specified primary
   specification for H1; where M1 and M2 disagree, M2 governs the conclusion.**
3. Interact `luck_belief` with country-year Gini, **grand-mean centered**. The
   prediction is that the slope is steeper where inequality is higher. **Contingency:**
   if the Gini merge yields fewer than 100 matched country-wave clusters, M3 is reported
   as descriptive only, not a confirmatory test.
4. Cluster standard errors at country-wave. **Weighted least squares using the WVS
   equilibrated post-stratification weight (S018)**, not unweighted OLS.

**Prediction:** `luck_belief` is positively associated with justifying norm violation,
and the association strengthens with inequality.

**Norm-violation index construction.** Each justifiability item standardized to mean 0,
SD 1 across the full analytic sample; the index is the mean of available standardized
items per respondent (so a respondent needs only 1 of the 4 items, not all 4).
**Contingency:** if Cronbach's alpha < 0.60, the four items become the primary outcomes
instead of the composite.

**Pre-registered hypotheses (OSF, see below).**

- **H1:** `luck_belief` → higher justification of norm violation, within-country (spec 2).
- **H2:** the H1 association strengthens with country-year Gini (spec 3).
- **H3:** `luck_belief` → **lower** generalised trust, within-country.

**Multiple comparisons.** H1, H2, and H3 are the confirmatory family; Holm-Bonferroni
correction is applied across exactly these three tests. The individual justifiability
items (as opposed to the composite `norm_index`), and the negative control below, remain
uncorrected but must be explicitly labeled secondary/exploratory wherever reported.

**Negative control (pre-registered).** An unrelated WVS justifiability item (divorce),
same 1–10 response format, included to test whether an effect reflects a general
response-style / permissiveness confound rather than something specific to economic
norm violation. Registered decision rule: if the M2 coefficient is comparable in
magnitude for this outcome — which has no theoretical link to perceived meritocracy —
that counts as evidence for a response-style confound rather than the hypothesized
mechanism.

**Robustness checks (pre-registered).**

- Logistic regression as an alternative to the linear probability model for the binary
  trust outcome; conclusions based on agreement between both.
- Education and income coded as dummy variables instead of ordinal scales.
- Excluding country-wave clusters with disproportionate influence, both results
  reported. Confirmed verbatim against osf.io/3gvfk: *"If any country-wave cluster
  exerts disproportionate influence, models will be re-estimated excluding it and both
  results reported."* Implemented as `robustness_exclude_influential_clusters`
  (leverage/hat-value diagnostics) in `03_models.py`. A separate exclusion by dual
  EVS/WVS reporting (`robustness_exclude_dual_reporting`) is also in the codebase but
  is **not** part of the registered text — kept as an additional check, not a
  substitute.
- **Not part of the registered text:** `robustness_gdp_control` refits M2/M3 with
  country-year GDP per capita (World Bank, PPP) added as a control, to check whether
  `gini_c` and the H2 interaction are actually picking up inequality rather than
  general economic development within a country over time — country fixed effects
  absorb each country's average wealth level but not its wealth *change* across
  waves, which is the same window `gini_c` is identified from. Added after Stage 1
  results were already in hand, so it is reported as a post-hoc addition, not folded
  into the confirmatory tests. See `FINDINGS.md`.
- **Not part of the registered text:** Cronbach's alpha for the four-item composite is
  also computed separately by country and by wave (`reliability_by_group` in
  `01_load_clean.py`), not just pooled — checks whether the composite hangs together
  the same way everywhere `norm_index` is used, instead of leaving that assumed. See
  `output/tables/reliability_by_group.csv` and `FINDINGS.md`.
- **Not part of the registered text, and not the project's causal identification
  strategy** (that's the diff-in-diff proposed for Stage 2, below, using actual dated
  events): `exploratory_gini_movers_did` in `03_models.py` splits countries into those
  whose mean Gini rose between their earliest and latest survey wave versus those
  where it didn't, and compares the change in mean `norm_index` between the two
  groups. Added after Stage 1 results were already in hand. Which country's Gini rose
  over this period is not randomly assigned, so this cannot support a causal reading —
  it is reported as an exploratory descriptive check, not evidence toward
  identification. See `FINDINGS.md`.
- If adding covariates in M1 drops the analysis sample by more than 30% relative to the
  unadjusted model, the unadjusted model (bare `luck_belief_z`, no covariates, no fixed
  effects) is also reported.

**Process rigor.** Analysis code was written and validated against synthetic data
before either dataset (WVS, SWIID) was accessed — see `src/00_synthetic_smoke_test.py`,
which fabricates data with a known injected effect and checks the pipeline recovers it.

### Stage 2 — Address endogeneity (proposed)

Stage 1 cannot establish direction. People who cheat may rationalise by concluding the
system is rigged. Five candidate strategies, to be argued in the research statement:

- **Asset-price/wage divergence shocks as diff-in-diff, with `luck_belief` itself as
  the outcome.** Piketty's r > g framework (Related literature, above) predicts that
  periods where asset prices (housing, equities) outpace wage growth are exactly when
  the "hard work pays off" narrative should lose credibility - a plausible source of
  exogenous variation in `luck_belief` specifically. Structurally similar to the
  corruption-shocks strategy below (both treat a macro shock as an exogenous shifter
  of `luck_belief`, then check whether `norm_index` moves after it), but arguably a
  cleaner source of exogeneity: a housing or equity boom driven by monetary policy or
  global capital flows is less obviously endogenous to a society's own norm-violation
  tendencies than a corruption scandal surfacing is. Country-years with a sharp
  asset-price/wage divergence landing between WVS waves as the treatment; `luck_belief`
  as the outcome; `norm_index` in a following wave as a secondary check on whether a
  belief shift here precedes an attitude shift there. If it holds, this attacks the
  reverse-causality problem directly rather than sitting alongside it, and the same
  shock could double as an instrument for `luck_belief` in the IV strategy below.
  Needs country-year housing/equity and wage data with WVS-wave coverage (e.g. BIS
  Residential Property Price Statistics, OECD House Price Indices) - availability
  should be checked before committing.
- **Corruption shocks as diff-in-diff.** Large revelations landing between WVS waves —
  Lava Jato (Brazil, 2014), 1MDB (Malaysia, 2015), Panama Papers (2016) — plausibly
  shift perceived meritocracy without directly changing individual honesty.
  Untreated countries serve as controls. Threats: media environment, concurrent shocks.
- **Instrumental variable.** Parental occupational mobility, or regional intergenerational
  elasticity, as an instrument for individual `luck_belief`. Exclusion restriction is
  demanding and must be argued, not assumed.
- **Cohort exposure.** Variation in inequality trajectory during formative years.
- **Program rollout as a natural experiment.** NREGA and comparable work-conditional
  transfer programs (Government of India, 2005; Imbert & Papp, 2015) were phased in
  geographically rather than launched everywhere at once - phase-in order is a
  plausible (though not automatic; parallel-trends needs arguing, not assuming) source
  of quasi-random variation in local exposure to the earned/unearned distinction,
  giving a staggered-rollout diff-in-diff on whether that distinction itself shifts
  `luck_belief` - a design question distinct from "Why it matters for policy," above,
  which is now framed around wealth concentration rather than transfer conditionality,
  but still a plausible source of exogenous variation in the belief measure itself.
  Binding constraint to check before committing: whether WVS/EVS has enough
  district-level (not just national) coverage and sample size in the relevant country
  to support this.

### Stage 3 — Causal test (proposed experiment)

Lab experiment holding the endowment *distribution* constant and randomising only the
*process* that produced it (effort-based vs. random assignment), measuring subsequent
honesty via a die-roll reporting task. Protocol not yet written.

**Not a blank design space, though less directly overlapping than it first
appears.** Kline, Galeotti & Orsini (2025) - see Related literature, above -
already ran a related lab experiment: a letter-counting task ranks participants by
performance, then randomizes whether the resulting pay honors or violates that
ranking, followed by a "custodial stage" that measures misreporting for personal
gain. Their endowments are always performance-based - they never randomize effort
vs. luck as the process generating the endowment, which is exactly what this Stage
3 proposes. Before writing the Stage 3 protocol, their design still needs to be
read directly and this project's version positioned explicitly against it (a
genuine extension, a replication in a new population, or an argued improvement)
rather than presented as untried.

---

## What Stage 1 must produce

1. A coefficient table: `luck_belief` → each justifiability item, three specifications.
2. An interaction plot: marginal effect of `luck_belief` across the Gini range.
3. A country-level scatter: mean `luck_belief` vs. mean norm-violation index.
4. An honest limitations section.

All four are complete; see `FINDINGS.md` and `output/tables/regression_results.csv`.

## What would refute the hypothesis

- No association once country fixed effects are included.
- Association exists but does not vary with inequality — implies a general
  disposition effect rather than anything structural.
- Association reverses in high-inequality countries.

Any of these is a publishable finding for the statement's purposes and should be
reported as-is. None of the three held in Stage 1: the association is present with
country fixed effects, it varies with inequality, and it does not reverse. See
`FINDINGS.md` for the full result, including the negative-control finding not
anticipated by this list.

---

## Data sources

| Source | Use | Access |
|---|---|---|
| World Values Survey (waves 3–7) | main individual-level data | free, registration at worldvaluessurvey.org |
| Integrated Values Surveys (WVS+EVS) | extended country coverage | free |
| SWIID | comparable Gini, country-year | free, R/Stata/CSV |
| World Bank (WDI, GDP per capita PPP) | non-registered robustness check (see `FINDINGS.md`) | free, no login |
| World Inequality Database (WID) | top income and wealth shares | free API |
| Afrobarometer / Latinobarómetro | developing-country robustness | free |

## Limitations to state, not hide

- Self-reported justifiability is not behaviour.
- Cross-country comparability of survey items is imperfect.
- Reverse causality is unresolved in Stage 1 — that is the argument for Stage 3.
- Survey non-response correlates with the things being measured.
- The WVS-to-SWIID country match (numeric code → country name) is automated and was
  hand-verified against the real downloaded files: 103 of 104 countries matched
  cleanly; Macao has no SWIID entry and is excluded rather than imputed. See
  `output/tables/country_match_report.csv` and `src/country_crosswalk.py`.
- The pre-registered negative control (an unrelated justifiability item) returned a
  coefficient comparable to or larger than the main effect, which does not support
  reading the confirmed hypotheses as specific to economic norm violation. No
  substitute item was found within the WVS justifiability battery: `luck_belief` is
  close to a general locus-of-control construct (Rotter, 1966; see also Ng,
  Sorensen & Eby, 2006 for a meta-analysis of its behavioral correlates), so the
  same contamination risk
  applies to any norm-violation item, not only the one used. Treated as a structural
  limitation of the negative-control strategy, not a defect of the specific item
  chosen. See `FINDINGS.md`.
- Gini values are SWIID point estimates (`swiid_summary.csv`), not the full
  multiple-imputation replicate set SWIID provides to capture its own estimation
  uncertainty, which is larger for countries with sparser underlying survey
  coverage. H2 and the `gini_c` results in `FINDINGS.md` treat Gini as measured
  without error, so their confidence intervals likely understate true uncertainty
  on the inequality side.
- Cronbach's alpha for the four-item composite varies meaningfully by country
  (0.506 to 0.959, median 0.737 across the 83 scoreable countries) - noticeably more
  spread than the pooled 0.798 alone suggests. See `FINDINGS.md`, Result 6.
- The ~40–57% sample drop from adding covariates was checked against the
  unadjusted model (see `FINDINGS.md`, Result 3) but whether the missingness
  itself (chiefly on `education`) relates to `luck_belief` was not tested directly.
- **Gini is not wealth concentration.** The project's own motivating argument
  (Piketty, r > g — see Related literature and "Why it matters for policy") is
  about capital-stock concentration; H2's registered moderator, SWIID Gini, is a
  broader income-inequality measure and was never a wealth-concentration measure
  specifically. Everything reported for H2 and `gini_c` (`FINDINGS.md`, Results 1
  and 5) is a statement about income inequality, not a direct test of the
  wealth-concentration mechanism the policy argument leans on. See Next steps for
  the proposed WID top-wealth-share extension this gap motivates.

## Next steps

Stage 1 is done: the registered hypotheses are tested and Holm-corrected, the
registered robustness checks are complete, the negative control was 
interrogated, and the result has been checked against the
closest published work. Below is what's next.

Causal identification (IV, natural experiments, the lab RCT) 
is already Stage 2 and Stage 3's job; this list assumes
those happen and asks what else would strengthen the project alongside them.

**Closing the two remaining Stage 1 gaps (bounded effort, still within Stage 1's
scope).**

- Refit H2 and the `gini_c` results using SWIID's full 100-replicate multiple
  imputation set instead of the point-estimate summary file, pooling via Rubin's
  rules. Addresses the "Gini measurement uncertainty" limitation directly instead
  of just stating it.
- Test whether covariate missingness (chiefly on `education`) is itself related
  to `luck_belief`, e.g. a logistic regression of the missingness indicator on
  `luck_belief` and country/wave fixed effects. Addresses the "Sample composition"
  limitation directly instead of relying on the indirect unadjusted-vs-adjusted
  proxy currently used.

**Acting on the Kline, Galeotti & Orsini (2025) overlap, now that it's been
found.**

- Check whether their WVS analysis code/data is available (via the paper's
  supplementary materials or by contacting the authors). If so, refit their exact
  specification with `luck_belief_z * gini_c` added, to test H2 with the
  fixed-vs-random-effects choice and the wave-range choice no longer confounded
  together - right now this project's H2 test differs from their design on both
  dimensions at once, so a currently-untested interaction can't be cleanly
  attributed to either difference specifically.
- Read their lab experiment protocol in full before writing Stage 3's. Decide
  explicitly whether Stage 3 is a replication in a new population, an argued
  improvement, or a genuine extension - and if extension, consider adding a
  between-subjects background-inequality-salience manipulation alongside their
  existing effort-vs-luck endowment manipulation, which would let Stage 3 test
  H2's logic (does context-level inequality change the belief effect) in a lab
  setting, something neither their experiment nor this project's Stage 1 data can
  do on its own.

**Extending Stage 1's scope, if a second descriptive pass is ever worth doing.**

- Re-run against the Integrated Values Survey (WVS+EVS combined) for wider country
  coverage than the WVS-only trend file used here - `robustness_exclude_dual_reporting`
  already exists in the codebase for exactly this eventuality but has never
  triggered on this WVS-only file.
- Test economic freedom (Geng, Chiu & Wang, 2025's moderator) alongside Gini in
  the same model, to see whether the two macro-context moderators pick up
  independent variation or are substitutes for each other.
- Refit H2 with World Inequality Database top wealth/income shares in place of (or
  alongside) SWIID Gini as the moderator. Addresses the measurement gap flagged in
  "Why it matters for policy," above: Gini captures income inequality broadly, not
  the wealth-stock concentration the project's Piketty-derived motivation is actually
  about, so this is closer to a direct test of that specific mechanism than the
  registered H2 specification is.
- Replicate once WVS wave 8 is released, extending past this project's current
  wave 7 cutoff.

## References

- Alesina, A., & Angeletos, G.-M. (2005). Fairness and redistribution. *American
  Economic Review*, 95(4), 960–980. https://doi.org/10.1257/0002828054825655
- Allison, L., Wang, C., & Kaminsky, J. (2021). Religiosity, neutrality, fairness,
  skepticism, and societal tranquility: A data science analysis of the World Values
  Survey. *PLOS ONE*, 16(1), e0245231. https://doi.org/10.1371/journal.pone.0245231
- Bénabou, R., & Tirole, J. (2006). Belief in a just world and redistributive
  politics. *The Quarterly Journal of Economics*, 121(2), 699–746.
  https://doi.org/10.1162/qjec.2006.121.2.699
- Geng, X., Chiu, C.-Y., & Wang, Y. (2025). Meritocracy beliefs are positively
  related to institutional trust only in societies with many economic freedoms: A
  multi-society multi-level analysis. *Journal of Social Issues*, 81(4), e70046.
  https://doi.org/10.1111/josi.70046
- Government of India. (2005). *The National Rural Employment Guarantee Act, 2005*
  (Act No. 42 of 2005). Ministry of Law and Justice.
- Imbert, C., & Papp, J. (2015). Labor market effects of social programs: Evidence
  from India's employment guarantee. *American Economic Journal: Applied
  Economics*, 7(2), 233–263. https://doi.org/10.1257/app.20130401
- Kline, R., Galeotti, F., & Orsini, R. (2025). Meritocracy or malfeasance:
  violations of meritocracy erode civic rule following. *Frontiers in Behavioral
  Economics*, 4, 1492421. https://doi.org/10.3389/frbhe.2025.1492421 — local copy:
  [`literature/kline_galeotti_orsini_2025.pdf`](literature/kline_galeotti_orsini_2025.pdf)
  (open access, CC BY 4.0)
- Mani, A., Mullainathan, S., Shafir, E., & Zhao, J. (2013). Poverty impedes
  cognitive function. *Science*, 341(6149), 976–980.
  https://doi.org/10.1126/science.1238041
- Ng, T. W. H., Sorensen, K. L., & Eby, L. T. (2006). Locus of control at work: A
  meta-analysis. *Journal of Organizational Behavior*, 27(8), 1057–1087.
- Piketty, T. (2014). *Capital in the Twenty-First Century* (A. Goldhammer, Trans.).
  Cambridge, MA: The Belknap Press of Harvard University Press.
- Rotter, J. B. (1966). Generalized expectancies for internal versus external
  control of reinforcement. *Psychological Monographs*, 80(1), 1–28.
- Saez, E., & Zucman, G. (2019). Progressive wealth taxation. *Brookings Papers on
  Economic Activity*, 50(2), 437–533. https://doi.org/10.1353/eca.2019.0017
- Uslaner, E. M. (2008). *Corruption, Inequality, and the Rule of Law: The Bulging
  Pocket Makes the Easy Life*. Cambridge University Press.
- You, J.-S., & Khagram, S. (2005). A comparative study of inequality and
  corruption. *American Sociological Review*, 70(1), 136–157.
  https://doi.org/10.1177/000312240507000107
