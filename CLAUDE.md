# Enrollment Tracker — project context

Single-page dashboard tracking Medicaid, Basic Health Program (BHP), and ACA Marketplace
enrollment. Published via GitHub Pages. Audience is internal policy analysts; the output
supports advocacy materials, so **figures must be defensible and conservatively sourced**.

## CMS data caveats — consult before touching data

`data/cms_data_notes.md` is the register of every caveat CMS publishes in the "Data Notes"
appendix of its monthly Enrollment Snapshot PDFs (source PDFs in `source-data/cms-snapshots/`),
consolidated and deduplicated across editions. **Consult it before you:**

- **add or refresh any data** — check whether the new month or state carries a known caveat;
- **investigate an anomaly** — an implausible jump is often a documented CMS reporting issue, not
  a real change or a bug (see the watch items below for the pattern);
- **change how a metric is calculated** — a caveat may explain, or be undone by, the change.

**Any state flagged as an active caveat there must have its caveat surfaced on the dashboard when
that state is selected** (as Nevada and California already are on the Medicaid tab, and the CHIP
caveats on the CHIP tab). If a flagged state has no on-page note yet, add one rather than showing
the figure unqualified. `data/cms_data_notes.md` also records caveats affecting data currently in
the dashboard that are **not yet** reflected in this file or the code — read its Active-caveats
section and gap note before trusting a state's figure.

## Layout

```
data/Enrollment_Tracker.xlsx   source workbook — the only file that changes monthly
data/pdf_history.json          national outcome mix Mar–Nov 2025 (from CMS PDF; static)
data/cms_data_notes.md         consolidated CMS "Data Notes" caveats, deduped across snapshots
source-data/cms-snapshots/     CMS monthly Enrollment Snapshot PDFs (provenance for the above)
data/cost_sharing.csv          ACA plan-level cost sharing by state × metal tier (annual; from PUFs)
data/medicare.json             per-state monthly Medicare summary (50+DC; from build_medicare.py)
source-data/                   large CMS PUF/Medicare zips + data dictionaries (extracted CSVs gitignored)
template.html                  page markup, CSS, and chart JS with __PLACEHOLDER__ tokens
build_dashboard.py             reads workbook + cost_sharing.csv + medicare.json + template -> writes index.html
build_cost_sharing.py          reads the PUF zips -> writes data/cost_sharing.csv (run yearly)
build_medicare.py              reads the Medicare CSV zip -> writes data/medicare.json (run on new Medicare drop)
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
| `CHIP` | 5 columns (`State`, `Reporting Period`, `Total CHIP Enrollment`, `Medicaid Child Enrollment`, `Medicaid and CHIP Child Enrollment`), one row per state per month + a `United States` row. Currently Dec 2025–May 2026, 51 states + US. **CHIP is a separate population, not a Medicaid subset** (see below). The dashboard **derives** Medicaid child from `Medicaid and CHIP Child` − `Total CHIP`; the sheet's own `Medicaid Child Enrollment` column is a cross-check only (see the Medicaid-child section). No adult or renewal fields. |
| `CHIP Peak Baseline` | Same 5-column layout as `CHIP`, one row per state + `United States`, all dated Mar 2023. Reference point for the CHIP and Medicaid-child peak strips; never a series. In this sheet Arizona's `Medicaid and CHIP Child` is `0` (breakout not reported in its Feb 2020–Apr 2024 window), so its derived child peak is negative and suppressed (see below). |
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

**California enrollment carries a continuity restatement of its pre-March-2026 months.**
California revised its Medicaid reporting in March 2026 to exclude limited-benefit enrollees and
did not restate prior months, making March-onward non-comparable to earlier months and inflating
the apparent national decline. To keep the trend comparable, `load_medicaid()` puts the whole
series on the revised (exclude-limited-benefit) basis by restating the **pre-revision** months
**down** — subtracting a fixed amount from California's `enroll` and `adult` counts for every
month *before* `CA_ADJUST_FROM` (`2026-03`), and leaving March 2026 and later **exactly as CMS
reports them**. This is deliberately the opposite of an add-back to the future: the two framings
produce an identical trend (they differ only by a uniform level shift), so the choice is which
end of the series stays real — and anchoring the current/most-recent months to CMS's published
figures keeps them tied to CMS control totals (national April = 66,725,217, which the load is
validated against) and cross-checkable, leaving only the shrinking pre-March tail as an estimate.
The amounts are derived by taking California's average monthly change over Dec 2025–Feb 2026
(−106,996 total, −78,132 adult), treating that as the expected March change, and attributing the
excess decline to the reclassification (i.e. the estimated limited-benefit population removed):
`CA_ENROLL_ADJUST = 384186` (Total Medicaid Enrollment) and `CA_ADULT_ADJUST = 372782` (Total
Medicaid Adult Enrollment). **These are estimates, not CMS figures.** As reported, March
California enrollment was 10,715,787 — shown unchanged. The restatement touches enrollment counts
only; no renewal field is altered. The national row is the exact sum of states, so national
enrollment is re-derived from state totals after the restatement rather than adjusted separately,
and the sum-of-states identity is checked before it is applied. A visible note on the Medicaid tab
discloses this to viewers. Because March onward is left as reported, the raw post-revision changes flow
through untouched: March→April −138,192 and April→May −71,676 — both far from the −491,182
one-time March reclassification drop, so the level-shift interpretation holds and the constants
are unchanged.

*Corroborated by the May 2026 data.* With two full post-revision months in hand, California's
average monthly change on the revised basis is **−104,934 total / −76,044 adult** (Apr–May),
against the **−106,996 / −78,132** pre-revision Dec–Feb trend used as the counterfactual for
March — a gap of just **1.9% / 2.7%**. The trend either side of the March cliff is effectively
the same, which is exactly what a one-time level shift predicts and what a second, undisclosed
exclusion would not. May's −71,676 is the *smallest* monthly decline in the series, not another
drop. The May 2026 edition also repeats the California data note **verbatim**, still stating the
state has not revised prior months — so no restatement has occurred and the adjustment stays.

*Why March, not November?* CMS's Dec 2025–Feb 2026 editions dated this revision to November 2025,
then the Mar–May editions restated it to March 2026 (see `data/cms_data_notes.md`). The workbook
data settle it: California runs a smooth trend Dec→Feb (−103,503, −110,489) and then a single
−491,182 cliff at Feb→March — there is **no level break in the Dec/Jan/Feb figures**, so the
exclusion landed in the March data and those earlier months are fully on the old include-basis.
March is therefore the operative revision month, and subtracting the full constant from each
pre-March month is the correct restatement; no separate November adjustment is warranted.

**The April 2026 Medicaid rows arrived mislabeled `2025-04` in the workbook** — a year
typo (confirmed against all three CMS control totals: 66,725,217 total, 38,489,574 adult,
5,828,803 renewals due). Corrected in place to `2026-04-01` via a scoped XML edit of the 52
`Reporting Period` cells (Mcaid sheet column B) so the `=SUM()` formula caches on the
`United States` rows were preserved — a full openpyxl round-trip drops those caches and
breaks the national rows. If a future drop repeats the typo, re-check the year before building.

**Nevada's March 2026 adult/child split is distorted by ~12,000 — the total is not.** CMS's
April 2026 note says Nevada's March *child* enrollment was overstated by approximately 12,000
due to a reporting error. It says nothing about the total, and the data show why: the child
overstatement is **offset by an almost equal understatement of Medicaid adult**, so Nevada's
March *total* is unaffected. In the workbook, March moves child **+11,447** and adult
**−13,183**, while the total moves only **−1,736** — squarely in family with its neighbours
(−576, −2,531); April reverses it (child −12,482, adult +9,951). CMS's own March 2026 edition
published Nevada's March total at **−0.3%**, confirming the total was never disturbed. Do
**not** adjust the figures — CMS corrects them upstream. The Medicaid tab surfaces the caveat
against the **adult** figure and the CHIP tab against the **derived child** figure; neither
claims the total is wrong.

⚠️ *Earlier editions of this file and of the dashboard caveat described the March **total** as
overstated by 12,000. That was a mis-transcription of the CMS note and is corrected above.*

**The May 2026 edition dropped the Nevada note, but the data are not yet corrected.** The May
Data Notes appendix no longer carries it, yet the May state tables report **May only** (no March
column), and every Dec 2025–Apr 2026 cell in the workbook is unchanged from the April vintage —
the March spike and its April reversal are both still present. The register's usual "a caveat
that stops being repeated is resolved" heuristic is therefore **overridden here by direct
inspection**: the caveat stays on both tabs until a March revision actually lands in the data.
Re-check on the next drop.

**Watch items (not CMS-flagged, left as reported).** States showing month-over-month movement
implausible enough to suggest a reporting artifact rather than a real shift; documented here
rather than silently presented. Nothing is adjusted.

*Idaho — resolved as a recurring artifact, still watch.* The April reading (renewed 97.5%,
procedural 13 of 24,149 due = 0.1%) **fully reverted in May**: renewed 65.3%, procedural 6,039
(25.3%), ex parte 46.3% — back in family with Dec/Jan/Mar (66.4/69.7/73.5% renewed, 25.6/21.6/
19.6% procedural). Note the shape: **February and April are both anomalous in the same
direction** (renewed ≥95%, procedural ≈0) while Dec, Jan, Mar and May are normal. That
alternating pattern points to a periodic reporting/timing artifact in Idaho's submission, not a
policy change. Treat any future near-zero Idaho procedural month as suspect.

*Alabama — cohort spike explained; a residual shift is not.* The April doubling of renewals due
(94,392→201,219) is **mechanical**: Alabama's `Renewal Due` equals its `Renewal Initiated` two
months earlier in every month of the series, so April's cohort is February's unusually large
initiation. May reverts to 101,259 (= March's initiation), as predicted. But the outcome mix has
**not** fully reverted: procedural disenrollment ran 9.2 / 7.6 / 6.1 / 5.6% Dec–Mar, then
**12.7%** in April and **17.2%** in May — roughly triple the pre-April level and the highest in
the series — while ex parte (36.4%) is still below its 41.7–42.9% Dec–Mar band. The cohort-size
story does not explain that. Re-check on the next drop.

*Alaska — new in May 2026.* Renewals due jump **17,318→30,712 (+77%)** and completion
deteriorates sharply: renewed **44.5%→27.4%** (the lowest of any state in May), form-based
renewals 17.2%→9.5%, procedural 24.5%→31.3%, and pending 20.6%→**33.7%** — a third of the
cohort unresolved at month end. Alaska is one of the states whose `due` does **not** track a
lagged `initiated`, so this is not a clean cohort effect. Consistent with a state overwhelmed by
an enlarged cohort, but a reporting change cannot be ruled out. **Highest-priority re-check.**

*Benign cohort swings (no action).* Montana (due −62%), Hawaii (+50%) and Kentucky (−41%) all
moved sharply in May, but each tracks its own lagged `initiated` cohort and their outcome mixes
stayed stable — mechanical, not a reporting change.

*Structural note — `due` is a lagged `initiated`.* In **19 states** the `Beneficiaries with a
Renewal Due` figure equals that state's `Beneficiaries with a Renewal Initiated` from a fixed
number of months earlier (1, 2 or 3, state-specific) in **every** month of the series — Alabama
and Kentucky lag 2 and 1 respectively. This is consistent with CMS's cohort reporting (outcomes
are reported in the month the cohort is due) and means large swings in `renewals due` are often
propagated cohort sizes rather than reporting errors. Check this before flagging a due-count
spike.

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
- **Current value = the latest month's enrollment** (same figure as the KPI). Under the
  California restatement the latest month is left exactly as CMS reports it, so the current side
  is the real reported figure — no add-back is applied to it.
- **California peak non-comparability.** The Mar 2023 peak predates California's reporting
  revision, so California's peak still includes limited-benefit enrollees its current figure now
  excludes; the peak overstates California's decline by roughly the excluded population
  (~384,000). The strip discloses this in a per-state note when California is selected rather than
  restating the peak (a small effect on the national total).

## CHIP (its own tab — "CHIP & Medicaid Child")

The tab is labelled **"CHIP & Medicaid Child"** because it reports both programs; it sits between
Medicaid and Basic Health Program in the tab bar, with a distinct violet accent
(`--chip:#5B4B9E`, light panel tint `--chip-light:#EDEBF6`) — separate from Medicaid navy, BHP
teal, and Marketplace crimson. Fed by `load_chip()`, `load_chip_peak_baseline()`,
`load_chip_child()`, `load_chip_child_peak()`, and `load_chip_both()` in `build_dashboard.py`,
reading the `CHIP` and `CHIP Peak Baseline` sheets. There is no renewal data, so it is a simpler
tab than Medicaid. Layout:

- **Top panel (KPI row) reports three enrollment totals side by side**, each with a
  month-over-month delta: **Total CHIP (reported, violet)**, **Medicaid child (derived, navy)**,
  and **Medicaid & CHIP child (reported, indigo)** — the last being the combined column
  (`load_chip_both()`), i.e. CHIP + Medicaid child. **Peak and peak-comparison figures are
  deliberately kept OFF the top panel** and live in the peak strips below.
- A state selector defaulting to National.
- An enrollment **trend chart** plotting **two distinct series — total CHIP (reported) and
  derived Medicaid child** (see below).
- **Two "vs. Pre-Unwinding Peak" strips**, each headed with its program so it is unambiguous:
  *CHIP · vs. Pre-Unwinding Peak* (violet) and *Medicaid Child · vs. Pre-Unwinding Peak* (navy,
  which mimics the CHIP strip — same metrics and proportional bar).
- **Two "Cumulative Impact · Dec 2025 – Apr 2026" strips**, one labelled *Total CHIP* and one
  *Medicaid Child (derived)*, side by side (net change, average monthly change, and vs. the Mar
  2023 peak). The child strip's peak cell shares the Arizona-aware `childPeakEndpoints()` logic
  with the child peak strip (national excludes Arizona from both endpoints; Arizona itself shows
  "suppressed").
- A **state-ranking chart** that the user can **toggle between Total CHIP and Medicaid child**
  (the toggle re-colours to violet/navy and re-titles); top states nationally, or
  state-vs-largest-states when a state is selected.

Every chart routes through `makeChart`; value axes use `axisFmt`.

**CHIP is a separate population, not a Medicaid subset.** It covers Medicaid-expansion CHIP,
separate CHIP, and pregnant adults in separate CHIP. Medicaid and CHIP enrollment therefore
add together rather than overlap: for May 2026, Medicaid (66,388,522, the raw workbook US
total) + CHIP (7,137,750) = 73,526,272 — matching the combined total CMS publishes. `load_chip()` verifies the `United States` row equals
the exact sum of states in every period; if that identity fails, a state is missing or
something is double-counted — stop and investigate rather than building. National CHIP control
totals (summed across states): Dec 2025 7,243,961; Jan 2026 7,241,058; Feb 2026 7,227,658;
Mar 2026 7,213,381; Apr 2026 7,145,807; May 2026 7,137,750.

**The March total has two acceptable vintages.** The CMS PDF published 7,213,496, but New
Hampshire was subsequently revised from 19,058 to 18,943, giving 7,213,381. The current
workbook carries the revised NH value (18,943 → national 7,213,381). Either vintage is
acceptable depending on the data's age; any *other* March mismatch means stop and report.

**The Medicaid adjustments do NOT apply to the CHIP total.** The California continuity
restatement concerned Medicaid limited-benefit enrollees only, and the Nevada March 2026 caveat
concerned Medicaid *child* enrollment — neither touches Total CHIP. `load_chip()` applies no
adjustment, and the CHIP-total figures carry no California disclosure. **The Nevada caveat,
however, now surfaces on this tab** because the tab derives and shows Medicaid child enrollment
(the metric Nevada overstated) — see the Medicaid-child section below. California is not
disclosed here because its revision did not touch child enrollment.

**The Mar 2023 peak is a reference point, never a series point.** As on the Medicaid tab, it is
never added to `CHIP_PERIODS` or any trend series (a 34-month gap would render as a straight
line), and it is not a reference line on the trend chart (it would compress the visible range).
Gaps in a state's monthly series render as gaps (`spanGaps:false`), never interpolated.

**State-level data-quality caveats** (from CMS footnotes; affect cross-state comparability).
The tab surfaces a brief per-state note when the selected state is one of these:

- **Montana, Ohio, West Virginia** reported "individuals enrolled at any time in month" rather
  than a point-in-time count for a stretch of earlier periods, so their figures run
  structurally higher and are not directly comparable to other states.
- **Rhode Island** has no data for Dec 2024 and Jan 2025 (system limitations) — any national
  total spanning those months is missing a state.
- **Colorado, Hawaii, New Hampshire** include retroactive enrollments, which makes their
  figures subject to later revision.
- **Alaska** did not include all CHIP enrollees for several months in late 2023 and early 2024.

**CMS Performance Indicator CSV downloads are revised over time; the monthly PDF snapshots are
point-in-time.** Where they conflict, the CSV is authoritative, and differences on older months
reflect state resubmissions (the New Hampshire March revision above is one example). Use PDF
totals to validate a fresh load, but expect small variances rather than treating them as
errors. This applies to Medicaid and CHIP alike.

### Derived Medicaid child enrollment (CHIP tab)

The CHIP tab also shows **Medicaid child enrollment**, which **CMS does not publish directly**
in the Performance Indicator data. It is **derived**, per state per month, as:

```
Medicaid child = Medicaid and CHIP Child Enrollment − Total CHIP Enrollment
```

Both inputs are columns on the `CHIP` / `CHIP Peak Baseline` sheets. `load_chip_child()` and
`load_chip_child_peak()` compute this via `derive_child()`; it is reported across the tab — a
**top-panel KPI**, a **second, distinct line** on the trend chart (dashed navy, unfilled)
alongside Total CHIP (solid filled violet), its own **"vs. Pre-Unwinding Peak" strip** mirroring
the CHIP one (`renderChipChildPeak()` mimics `renderChipPeak()`), its own **Cumulative Impact
strip** beside the CHIP one, and a **toggle option on the state-ranking chart**. The reported
**combined column** ("Medicaid and CHIP Child Enrollment" = CHIP + Medicaid child) is loaded by
`load_chip_both()` and shown as the **third top-panel KPI** (`CHIP_BOTH_NAT`/`CHIP_BOTH_STATES`).
The two component programs are **separate programs that add together — never stacked** (stacking
would imply CHIP is a Medicaid subset, which it is not), and Medicaid child is always **labelled
"derived"**, not reported. The sheets carry their own `Medicaid Child Enrollment` column; the
dashboard derives the value independently and uses that column only as a cross-check (they match
on every `CHIP` row).

**"Medicaid and CHIP Child" is not purely children.** CMS's figure includes **pregnant adult
women enrolled in separate CHIP**, so the derived "Medicaid child" figure is not strictly a
child count. The arithmetic reconciles exactly (it is a clean subtraction of two published
columns), but the *label* is imprecise — the surfaced value is best read as "Medicaid children
plus a small pregnant-adult residual," and should not be presented as an exact child census.

**Never render a derived value that is negative or zero.** A derived value ≤ 0 (or a missing
input) means the state **did not report the child breakout that month** — not that it has no
child enrollment — so `derive_child()` returns `None` and the dashboard renders a **gap**
(`spanGaps:false`), never a number. In the current `CHIP` sheet (Dec 2025–Apr 2026) all 51
states report positive in every month; the only ≤ 0 case anywhere is Arizona in the Mar 2023
baseline (below).

**National control totals (derived Medicaid child), validated in `load_chip_child()`:** the
national row must equal the exact sum of reported states each month, and is checked against the
CMS PDF state tables — **May 2026 = 28,080,687** and **April 2026 = 28,235,643**, both
**hard asserts** (`CHIP_CHILD_CONTROL_STRICT`). March 2026 derives to **28,357,494** on the
workbook's revised-NH vintage, **636 below the PDF's 28,358,130**; per the "two acceptable
vintages"/CSV-authoritative rule above this is expected, so the build emits a note rather than
failing. Any *other* control mismatch — especially on the two strict months — means stop and
investigate. When a new month lands, add it to `CHIP_CHILD_CONTROL` and to the strict set, and
drop the oldest month out of the strict set once it starts drifting from resubmissions.

**Arizona — the child peak is suppressed.** CMS states Arizona did not report the Medicaid
adult/child breakout from **Feb 2020 through Apr 2024**, and national child totals before May
2024 include Arizona's CHIP only. The Mar 2023 baseline sits inside that window, so Arizona's
`Medicaid and CHIP Child` there is `0` and its derived child peak is **−147,213** — unreal.
Handling:

- **Per-state:** Arizona's Medicaid-child *peak comparison* is **suppressed entirely** (a note
  explains why); its post-May-2024 monthly values in `CHIP` are valid and **display normally**.
- **National:** Arizona is **excluded from both endpoints** of the national child peak
  comparison, not the whole comparison suppressed — dropping one contaminated cell should not
  cost 50 states + DC of good data. `load_chip_child_peak()` builds the national child peak as
  the **sum of reported states only** (Arizona's `None` is excluded) = **35,171,296** (this
  equals the workbook's own pre-computed US `Medicaid Child` cell, which likewise floors
  Arizona). The JS then subtracts Arizona's current children from the current endpoint so the
  comparison is like-for-like (~35.17M → ~27.63M, −21.4%), and a note discloses that Arizona is
  excluded from both endpoints. Arizona's current children **remain in the national trend/level**
  above, where they are valid. **CHIP-total peak comparisons are unaffected throughout** — this
  concerns the derived child series only.

**Nevada — March 2026 child overstated.** CMS acknowledges a reporting error that overstated
Nevada's March 2026 Medicaid *child* enrollment by roughly **12,000**, offset by an equal
understatement of Medicaid adult (so its March **total** is unaffected — see the Medicaid-tab
section). **Do not adjust it** — CMS corrects it upstream. Because the CHIP tab shows the
derived child series, the Nevada caveat is **carried on this tab too** (`CHIP_CAVEATS`) and
surfaces when Nevada is selected; its Total CHIP enrollment is unaffected. The March→April
change in the derived child series is **overstated as a decline** (−12,482 against a ~−1,900
trend). **The May 2026 CMS edition dropped this note without the data being corrected** — the
caveat stays until a revised March actually lands (see the Medicaid-tab section).

## Medicare (its own tab)

The Medicare tab is the last tab in the bar, with a distinct **burnt-orange accent**
(`--mcare:#B45309`, light panel tint `--mcare-light:#F7EEE1`) — separate from Medicaid
navy, CHIP violet, BHP teal, and Marketplace crimson. It does **not** come from the
workbook: `build_medicare.py` reads two raw CMS sources and **merges** them into a small
per-state monthly summary at `data/medicare.json`; `build_dashboard.py`'s `load_medicare()`
reads only that JSON and **never touches the raw source at build time** (same split as cost
sharing). The two sources:

- `source-data/Medicare_Monthly_Data.zip` — the archived **full history** (Jan 2023 onward).
  Large, so tracked compressed; the extracted CSV is gitignored.
- `source-data/Medicare_Monthly_Data.csv` — the **latest monthly drop**, uncompressed. CMS's
  download carries only the most recent months (currently Jan–May 2026) and **revises** those
  months relative to the archived history, so where the two overlap the CSV **wins** (CMS
  revisions are authoritative — see the "revised over time" rule below); months the CSV does
  not cover come from the zip unchanged. This is optional: if the CSV is absent the build
  proceeds from the zip alone. The new CSV format also carries `BENE_GEO_LVL`/`State_Abrvtn`/
  `FIPS_Cd` columns the older zip omits, but level is still inferred (below) so both parse
  identically.

To land a new month (and its revisions), drop the refreshed CSV in place and rerun
`build_medicare.py`; re-archive the zip only if you want the raw history extended past what the
CSV overlays. The console summary prints which months came from the CSV drop.

**The headline metric is Medicare Advantage penetration** — MA (`MA_AND_OTH_BENES`, labelled
"MA & other health plans", since it also covers cost plans/PACE) as a share of beneficiaries
with **both Part A and Part B** (`A_B_TOT_BENES`), **not** total Medicare — you must carry both
parts to enrol in MA, so A&B is the eligible denominator (the standard CMS penetration basis).
It runs ~4 points above the total-Medicare basis: nationally it rose **52.3% → 55.6%** (Jan 2023
→ Apr 2026); across states Apr 2026 spans **3.2% (Alaska) → 67.6% (Michigan)**. The KPI, hero
trend, ranking, and lookback bar all use this A&B denominator; `mcPen()` is the single source.

Data traps handled in `build_medicare.py` (all verified against the file):

- **Three geography levels + annual roll-ups per file.** The archived zip's CSV has no
  `Bene_Geo_Lvl` column (the dictionary lists one; that vintage omits it, along with
  `State_Abrvtn` and `FIPS_Cd`; the newer drop restores them). To parse both vintages the same
  way, level is **inferred** rather than read from that column: `BENE_STATE_DESC == "National"`, else
  `BENE_COUNTY_DESC == "Total"` is a **state** row, else a **county** row. It also carries
  annual `MONTH == "Year"` roll-ups. We keep **state-level, real-month rows only** and never
  sum counties or let a `Year` row into a series.
- **The CMS `National` row includes territories, so we do NOT use it.** Beyond 50+DC the state
  level also carries Puerto Rico, Guam, the Virgin Islands, American Samoa, the Northern
  Mariana Islands, and "Foreign and Other Outlying Areas" (~1.4M). The national series is
  **rebuilt as the exact sum of the 50 states + DC** to match the dashboard's scope, so it runs
  ~1.4M **below** CMS's published national — a compact note on the tab discloses this.
- **Suppression is the literal `*`** (~11% of county cells, 0.73% of state cells). The nine
  fields kept here are never suppressed for any 50+DC state in any month; `build_medicare.py`
  **fails loudly** if that ever changes rather than summing around a hole.
- **Reconciliation holds exactly** in the source and is re-checked on the rebuilt national
  totals: `Original + MA == Total`, `Aged + Disabled == Total`, `PDP + MAPD == Part D`. Every
  month must carry the full 51-area panel or the build aborts.

Tab shape (state selector defaults to National, wired like the others; every figure
recalculates): a **KPI row** (total Medicare + MoM; MA penetration + MoM in points; Original
Medicare; dual-eligible + share; Part D coverage + share), a **3-year lookback strip** (current
vs the same month three years earlier — total then/now/change/%, with the proportional bar
repurposed to show **MA penetration then → now**: a light "3-years-ago" segment (0 → then)
followed by a darker segment for the gain up to now (then → now), so the current rate is the
darker region and its right edge marks today, since a growing series would overrun a
share-of-baseline bar), and a **five-chart grid**: MA penetration trend (hero,
tall, line), three **stacked-area** charts — Original vs MA, Part D (PDP vs MAPD), Aged vs
Disabled — and a state MA-penetration ranking (top-12 nationally; selected-state-vs-largest when a state
is chosen). The lookback month is derived as three years before the latest month, so it tracks
forward as new data lands.

**Dual-eligibles are the bridge to the Medicaid tab.** `DUAL_TOT_BENES` (17.0% of Medicare,
~11.7M nationally) counts beneficiaries jointly enrolled in Medicaid — the same people appear
on the Medicaid tab. Only `DUAL_TOT` is surfaced: the full/partial dual split
(`FULL_DUAL`/`PART_DUAL`) is suppressed in ~26–28 small-state cells, so it is not shown.

**Axis-scaling decisions (deliberate, per the CHIP lesson).** Medicare series carry real level
movement, so unlike the genuinely flat CHIP series they are **not** anchored at zero — with two
exceptions coded on purpose:

- The **MA penetration** charts use `pctAxisFmt`, an adaptive percent formatter that adds
  decimals from the tick spacing so a narrow (~3-point) range doesn't collapse into repeated
  whole-percent labels the way `pctFmt` would. The hero penetration axis is auto-scaled (not
  anchored at zero — that would flatten the genuine rise) but carries ~70% `grace` padding, so
  a few points of movement sit in the middle band instead of stretching across the full height
  and overstating the slope.
- The **stacked-to-total** charts (Original vs MA, PDP vs MAPD, Aged vs Disabled) **do**
  `beginAtZero`: they are compositions of a whole, and a non-zero baseline would exaggerate the
  smaller band (e.g. make ~6M disabled look comparable to ~62M aged).

No per-state Medicare caveats are flagged in the current CMS file; `MCARE_CAVEATS` is wired
(like the Medicaid/CHIP caveat maps) so one can be surfaced under the selector if a future
edition adds one.

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
2. Add the new CMS snapshot PDF to `source-data/cms-snapshots/` (named `snapshot-YYYY-MM.pdf`),
   extract its **Data Notes** appendix — the *Data Type × Data Notes* table near the end; ignore
   the identical "What You Should Know When Using the Data" boilerplate slides — and update
   `data/cms_data_notes.md`: add **new** caveats, mark **resolved** ones (a caveat that stops being
   repeated), and record any that **changed wording** (e.g. a restated date or a changed state
   list). Surface any newly active state caveat on the dashboard per the rule above.
3. `python build_dashboard.py`
4. Sanity-check the console summary — month ranges and state counts should look right
5. Open `index.html` locally, click through all three tabs and a few state toggles
6. Commit and push; GitHub Pages redeploys within about a minute

## Verification habit

When new columns or sources appear, cross-check them against data already in the workbook
before wiring them into the dashboard, and report what matched and what didn't. Past checks
have caught a state-level off-by-one and confirmed that PDF-derived percentages agreed with
workbook counts within rounding. Prefer flagging a discrepancy over silently normalizing it.
