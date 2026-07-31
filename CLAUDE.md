# Enrollment Tracker — project context

Single-page dashboard tracking Medicaid, Basic Health Program (BHP), and ACA Marketplace
enrollment. Published via GitHub Pages. Audience is internal policy analysts; the output
supports advocacy materials, so **figures must be defensible and conservatively sourced**.

## Layout

```
data/Enrollment_Tracker.xlsx   source workbook — the only file that changes monthly
data/pdf_history.json          national outcome mix Mar–Nov 2025 (from CMS PDF; static)
data/cost_sharing.csv          ACA plan-level cost sharing by state × metal tier (annual; from PUFs)
source-data/                   large CMS PUF zips + data dictionaries (extracted CSVs gitignored)
template.html                  page markup, CSS, and chart JS with __PLACEHOLDER__ tokens
build_dashboard.py             reads workbook + cost_sharing.csv + template -> writes index.html
build_cost_sharing.py          reads the PUF zips -> writes data/cost_sharing.csv (run yearly)
index.html                     generated output; GitHub Pages serves this. Do not hand-edit.
```

## Rebuild

```bash
pip install -r requirements.txt   # first time only
python build_dashboard.py
```

Dependencies are pinned in `requirements.txt` (pandas, openpyxl). In a cloud session,
install them before building. The script fails loudly if the workbook is missing or a
placeholder goes unsubstituted. **Never edit `index.html` directly** — edit `template.html`
or `build_dashboard.py` and rebuild, or the change is lost on the next run.

`build_dashboard.py` reads `data/cost_sharing.csv` but does **not** regenerate it —
that file is refreshed once a year by `build_cost_sharing.py` from the CMS PUFs (see the
ACA cost-sharing section below). The monthly rebuild leaves it untouched.

## Workbook sheets

| Sheet | Notes |
|---|---|
| `Mcaid` | One row per state per month, plus a `United States` row |
| `Mcaid Peak Baseline` | **Different layout** — 3 columns (`State`, `Reporting Period`, `Total Medicaid Enrollment`), one row per state + `United States`, all dated Mar 2023. Total enrollment only: no adult, no renewal fields. Reference point for the peak strip; never a series. |
| `BHP` | Only DC, MN, NY, OR participate |
| `Marketplace` | **Superseded — do not read.** Kept for reference only |
| `Marketplace (2)` | The live Marketplace sheet. `Reporting Period` is the string `OEP` or a date |
| `Marketplace Feb. Effec. Enroll` | Two-letter state codes; needs abbreviation mapping |

## Data conventions that matter

**Marketplace post-OEP figures are effectuated enrollment, not plan selections.** The OEP
number counts plan selections at close of open enrollment; every later month counts
effectuated coverage. Different measures — label them distinctly and never describe the
gap between them as pure attrition. Confirmed by matching `Marketplace (2)` monthly values
against the effectuated sheet exactly.

**National post-OEP data is limited to reported months.** The United States post-OEP
series carries only OEP, Jan, and Feb 2026 — the months CMS actually reported national
effectuated totals. The workbook has no March figure, and its April value (19,200,000) is
a rounded placeholder, not a reported count, so both are excluded to avoid a misleading
isolated dot on the national trend line. The exclusion is an explicit, documented cutoff in
`load_marketplace()` (`NATIONAL_POST_OEP_EXCLUDE_FROM`), applied to the national series only.
State series are untouched — 12 states report genuine March, April, and May figures.

**Renewal denominators.** Renewed / disenrolled / pending are shares of *renewals due* that
month, not of total enrollment. Procedural and ineligible are shares of *total disenrolled*.

**The national outcome mix blends two sources.** Dec 2025 onward comes from the workbook.
Mar–Nov 2025 comes from `pdf_history.json` (CMS snapshot slides 17–18), where `pend` was
derived as the residual. The two agree within 0.4pt on overlapping months. State-level
outcome mix is workbook-only and covers the workbook's months.

**Outcome-mix components are rescaled to sum to exactly 100** so stacked bars render
cleanly. Adjustments are under ~0.25pt.

**California enrollment carries a continuity adjustment from March 2026 onward.** California
revised its Medicaid reporting in March 2026 to exclude limited-benefit enrollees and did not
restate prior months, making March-onward non-comparable to earlier months and inflating the
apparent national decline. To keep the trend comparable, `load_medicaid()` adds back a fixed
amount to California's `enroll` and `adult` counts for March 2026 and every later month (the
revision is permanent). The add-backs are derived by taking California's average monthly change
over Dec 2025–Feb 2026 (−106,996 total, −78,132 adult), treating that as the expected March
change, and attributing the excess decline to the reclassification:
`CA_ENROLL_ADJUST = 384186` (Total Medicaid Enrollment) and `CA_ADULT_ADJUST = 372782` (Total
Medicaid Adult Enrollment). **These are estimates, not CMS figures** — as reported, March
California enrollment was 10,715,787. The adjustment touches enrollment counts only; no renewal
field is altered. The national row is the exact sum of states, so national enrollment is
re-derived from state totals after the adjustment rather than adjusted separately, and the
sum-of-states identity is checked before the adjustment is applied. A visible note on the
Medicaid tab discloses the adjustment to viewers. The April 2026 CMS snapshot reconfirms
California's data is non-comparable from March forward; the raw March→April change is −138,192
(steeper than the ~−107,000 pre-revision trend but far from the −491,182 one-time March
reclassification drop), so the level-shift interpretation holds and the constants are
unchanged. Because the same constant is added to both March and April, the March→April delta
is unaffected by the adjustment.

**The April 2026 Medicaid rows arrived mislabeled `2025-04` in the workbook** — a year
typo (confirmed against all three CMS control totals: 66,725,217 total, 38,489,574 adult,
5,828,803 renewals due). Corrected in place to `2026-04-01` via a scoped XML edit of the 52
`Reporting Period` cells (Mcaid sheet column B) so the `=SUM()` formula caches on the
`United States` rows were preserved — a full openpyxl round-trip drops those caches and
breaks the national rows. If a future drop repeats the typo, re-check the year before building.

**Nevada's March 2026 total is overstated by ~12,000.** CMS acknowledges a reporting error
that inflated Nevada's March *child* enrollment (adult enrollment is unaffected), to be
corrected in a future CMS release. Do **not** adjust the figure — CMS corrects it upstream.
The Medicaid tab surfaces a caveat when Nevada is selected, noting the March total is
overstated and its March→April change is therefore understated.

**April 2026 watch items (not CMS-flagged, left as reported).** Two states show implausible
month-over-month movement that may be genuine or a reporting artifact; documented here rather
than silently presented. *Idaho:* renewal rate jumps 73.5%→97.5% while procedural
disenrollments collapse from 4,348 (19.6%) to 13 (0.1%) of 24,149 due. *Alabama:* renewals
due more than double (94,392→201,219) while ex parte falls 41.7%→20.6%. Re-check both against
the next CMS release.

**BHP reporting coverage is uneven** — states report through different months. Charts plot
only each state's reported range. NY's figure is Essential Plan Expansion under a 1332
waiver, reported in the BHP series. National total uses January, the one month all four
states report.

**Ex parte** = renewal completed from data the state already holds, no beneficiary action.
It is the key operational metric: nationally it fell from 56% to 48% over 13 months while
procedural disenrollments rose from 10% to 15%. Across states the two correlate at r = -0.50
(n = 51) — a moderate association, so describe it as such rather than as causation.

## Peak baseline comparison (Medicaid tab)

A compact strip between the Medicaid state selector and the lower chart grid compares the
**most recent reported month** to the **March 2023 pre-unwinding peak** (peak value, current
value, absolute change, percent change, and a proportional bar of current as a share of peak).
It updates with the state selector. Data comes from `load_peak_baseline()` reading the
`Mcaid Peak Baseline` sheet into `MCAID_PEAK` ({state|`United States`: peak total}).

Rules that keep it honest:

- **The baseline is a reference point, not a series point.** March 2023 is never added to
  `MCAID_PERIODS` or any trend/series — a 34-month gap would render as a straight line and
  misrepresent the decline. It is also **not** a reference line on the enrollment trend chart
  (that axis spans ~66–68.5M; a line at ~87M would flatten the actual trend).
- **Total enrollment only.** The sheet has no adult or renewal fields; no adult/renewal code
  path reads from it, and the strip is labelled total enrollment. `load_peak_baseline()`
  checks the sheet's `United States` row equals the sum of its states.
- **Current value = the latest month's *adjusted* enrollment** (same figure as the KPI), so
  the California continuity add-back is included on the current side.
- **California peak non-comparability.** The Mar 2023 peak predates California's reporting
  revision, so California's peak still includes limited-benefit enrollees its current figure
  excludes; the +384,186 current-side adjustment only partly offsets this, so California's
  decline-from-peak is somewhat overstated. The strip discloses this in a per-state note when
  California is selected rather than restating the peak (a small effect on the national total).

## ACA cost sharing by metal tier

The Marketplace tab's bottom-right card shows average **individual medical deductible,
individual out-of-pocket maximum, and primary-care-visit copay** for each state × metal tier,
updating with the state selector. Figures are a **plan-level simple average (not
enrollment-weighted)** — every qualifying plan counts once regardless of how many people
enrolled in it. The card labels this explicitly; keep that label.

**Source: two CMS Exchange PUFs**, not the workbook. The zips + data dictionaries live in
`source-data/` (kept small, tracked); the extracted CSVs are far too large for the repo /
GitHub Pages and are gitignored. `build_cost_sharing.py` reads them and writes
`data/cost_sharing.csv`; `build_dashboard.py` then injects that CSV. Rerun
`build_cost_sharing.py` only when CMS publishes a new benefit year (`CS_BENEFIT_YEAR`).

- **Plan Attributes PUF** (`Plan_Attributes_PUF.csv`) → deductible + OOP max.
  - Individual deductible = `TEHBDedInnTier1Individual` (combined medical+drug, integrated
    plans) coalesced with `MEHBDedInnTier1Individual` (medical-only, separate-limit plans).
    Each plan populates exactly one side; coalescing covers all plans. OOP max uses the
    matching `…IndividualMOOP` pair. Values are `$X` / `Not Applicable` / blank — parse `$`
    and commas.
- **Benefits & Cost-Sharing PUF** (`Benefits_Cost_Sharing_PUF.csv`) → primary care copay.
  - Benefit row `BenefitName == "Primary Care Visit to Treat an Injury or Illness"`, field
    `CopayInnTier1`, joined to the base plans by 17-char `PlanId` (100% match). Copay parsing:
    `No Charge*` → 0; `$X Copay*` (any "after/with deductible", "per Day/Stay" suffix) → X;
    `Not Applicable` / blank → **excluded** (these plans express primary care as coinsurance
    in `CoinsInnTier1`; excluded from the copay mean rather than coerced to 0, ~9% of plans).

**Filters** (applied to Plan Attributes, in order), keeping one standard on-exchange row per
plan:
1. `DentalOnlyPlan == "No"` — exclude dental-only plans.
2. `QHPNonQHPTypeId in {"Both", "On the Exchange"}` — on-exchange only. (Dictionary lists the
   allowable values as "On/Off Exchange"; the data actually uses "Both"/"On the Exchange"/
   "Off the Exchange" — trust the data.)
3. `BusinessYear == CS_BENEFIT_YEAR` — current benefit year.
4. `CSRVariationType` matches `^Standard .* On Exchange Plan$` — **base variant only**. This is
   the critical filter: it drops every CSR variant (Zero/Limited Cost Sharing, 73/87/94% AV
   Silver) *and* the off-exchange duplicate rows, leaving exactly one row per plan. CSR
   variants have far lower deductibles and would badly distort Silver if included — the Silver
   ≫ Gold deductible sanity check exists to catch that leak.
5. `MetalLevel in {Bronze, Expanded Bronze, Silver, Gold, Platinum, Catastrophic}`; **Expanded
   Bronze is folded into Bronze**.

**United States row = mean across all plans nationally** (pooled), not the mean of state means.

**Coverage: the PUF only includes FFE / SBE-FP states (~30).** Full state-based-exchange
states (California, New York, etc.) are absent, so their selector shows a "no data" card. This
is a source limitation, not a bug — do not fabricate values for them.

**Known-legitimate zeros/blanks** (verified real, not parse errors): Platinum mean deductibles
are ~$0 in several states (Platinum plans genuinely carry ~$0 deductibles); Catastrophic
plans have deductible = OOP max = the federal limit ($10,600 in 2026) and often list primary
care as `No Charge after deductible` (→ $0) or coinsurance (→ blank). The four sanity checks in
`build_cost_sharing.py`'s validation are: deductibles decrease Bronze→Platinum; Catastrophic
deductible ≈ OOP max; Silver deductible ≫ Gold (no CSR leak); no missing/zero cell outside the
documented Platinum/Catastrophic cases.

## Conventions

- **Axis labels carry no decimals.** `axisFmt` picks its unit from tick spacing so narrow
  ranges don't collapse into repeated labels. Percent axes use `pctFmt`.
- **All charts route through `makeChart(id, config)`**, which destroys any prior instance
  first. Creating a Chart directly leaves a stale instance that state toggles can't replace.
- Medicaid and Marketplace tabs have state selectors; every figure on the tab recalculates.
  BHP is national only.
- No organizational branding on the page — it is publicly hosted.
- `noindex, nofollow` is set in `template.html`. Preserve it.
- Chart.js loads from CDN, so the page needs internet access.

## Monthly update

1. Drop the new workbook at `data/Enrollment_Tracker.xlsx` (keep the filename)
2. `python build_dashboard.py`
3. Sanity-check the console summary — month ranges and state counts should look right
4. Open `index.html` locally, click through all three tabs and a few state toggles
5. Commit and push; GitHub Pages redeploys within about a minute

## Verification habit

When new columns or sources appear, cross-check them against data already in the workbook
before wiring them into the dashboard, and report what matched and what didn't. Past checks
have caught a state-level off-by-one and confirmed that PDF-derived percentages agreed with
workbook counts within rounding. Prefer flagging a discrepancy over silently normalizing it.
