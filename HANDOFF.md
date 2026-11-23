# Enrollment Tracker — Handoff Guide

**Start here.** This file is the operating manual for whoever runs the tracker next. `CLAUDE.md` is
the detailed technical reference (every data convention, caveat and adjustment); Claude reads it
automatically at the start of every session in this repo. This file covers what `CLAUDE.md` doesn't:
access, the update calendar, where each source file comes from, ready-to-paste prompts, and the
judgment calls behind the numbers.

Handoff date: November 23, 2026 (Isaac → successor). Latest data at handoff: Medicaid/CHIP
July 2026, BHP October 2026, Medicare June 2026, Marketplace effectuated August 2026, ESI CPS 2025 /
ACS 2024 / MEPS-IC 2025 / KFF 2025, state Marketplace probe through Nov 23, 2026.

---

## 1. What this is

A single-page, publicly hosted dashboard tracking coverage across six programs, each on its own tab:

| Tab | What it shows | Main source |
|---|---|---|
| Medicaid | Enrollment, adult enrollment, renewal outcomes (ex parte, procedural, ineligible), state rankings, pre-unwinding peak comparison | CMS Medicaid & CHIP Eligibility Operations and Enrollment Snapshot |
| CHIP & Medicaid Child | CHIP, derived Medicaid child, combined child; two peak strips | Same CMS snapshot |
| Basic Health Program | MN, NY, OR, DC enrollment | State reports (MN DHS, NY State of Health, Oregon OHA) |
| ACA Marketplace | OEP plan selections, effectuated enrollment, premiums before/after APTC, metal tiers, cost sharing by tier, 2027 state-reported OEP table, national context card | CMS OEP PUF, CMS effectuated data, Exchange PUFs, state marketplaces, KFF/CBO/Mark Farrah |
| Medicare | Total, MA penetration (of Part A&B), Part D, duals, aged/disabled | CMS Medicare Monthly Enrollment |
| Employer (ESI) | Covered persons (ACS by state, CPS national trend), premiums/contributions/deductibles | Census ACS & CPS ASEC, AHRQ MEPS-IC, KFF EHBS |

- **Live site:** `https://inicchitta12.github.io/enrollment-tracker/` (GitHub Pages serves `index.html` from `main`).
- **Repo:** `https://github.com/INicchitta12/enrollment-tracker` (public).
- **Audience and standard:** internal policy analysts; figures feed advocacy materials, so every
  number must survive scrutiny from CMS, CBO, Hill staff and opposing stakeholders. When in doubt,
  disclose the caveat rather than smooth it over.

## 2. Getting set up

1. **GitHub access.** Isaac adds you as a collaborator: repo → **Settings → Collaborators → Add
   people**. (Alternatively, transfer the repo or fork it to your account; if you fork, Pages and the
   URL change — update the URL in this file and in `README.md`.)
2. **Claude.** Two ways to run it; both read `CLAUDE.md` automatically:
   - **Claude Code on the web (claude.ai/code)** — what Isaac used, because it needs no local
     install. Start a new task with **only** `enrollment-tracker` attached. A session copies the repo
     when it starts, so commit uploaded files first, then start the session.
   - **Claude Code on your own computer** — `git clone https://github.com/INicchitta12/enrollment-tracker`,
     then `make install` (Python 3.11, `pandas`, `openpyxl`), then run Claude in the folder.
3. **Network access (web sessions only).** The default cloud environment blocks most websites. The
   Marketplace probe and any source verification need **Full** network access: claude.ai/code →
   environment selector → edit → **Network access: Full**. Use an environment dedicated to this repo.
4. **Check the build works:** `make dashboard` then `python -m unittest discover -s tests`
   (26 tests pass at handoff). Open `index.html` in a browser and click through every tab.

## 3. How a change gets published

1. Claude works on a branch (`claude/...`) and pushes it. It never merges.
2. On GitHub: **Compare & pull request → Files changed** (check only expected files changed) →
   **Merge pull request**.
3. The GitHub Action (`.github/workflows/build.yml`) rebuilds on every PR and fails if a control total
   trips, a placeholder is left, or the committed `index.html` is stale. Don't merge a red PR.
4. Pages redeploys in about a minute; hard-refresh (Ctrl/Cmd+Shift+R).

Never hand-edit `index.html` — edit `template.html` or the build scripts and rebuild.

## 4. Update calendar

| Cadence | What | Trigger | Section |
|---|---|---|---|
| Monthly (~end of month) | Medicaid, CHIP, BHP from the new CMS snapshot | CMS posts a new snapshot (released ~3 months after the data month; July 2026 data came out Oct 30) | §6.1 |
| Monthly | Medicare | New Medicare Monthly Enrollment file on data.cms.gov | §6.2 |
| Mon & Thu (OEP), Mon after Feb 15 | State Marketplace probe → review PR | Scheduled task (§7) | §6.3 |
| When CMS publishes | Marketplace effectuated months; 2027 OEP state-level PUF (spring 2027) | data.cms.gov / CMS Marketplace products page | §6.4 |
| Yearly (Oct–Nov) | ACA cost sharing for the new benefit year | New Exchange PUFs | §6.5 |
| Yearly (Sept) | CPS ASEC (ESI national trend) | Census HHI-01 release | §6.6 |
| When released | ACS 1-year (ESI by state) — **2025 release delayed indefinitely by Census** | Census | §6.6 |
| Yearly | MEPS-IC (summer), KFF EHBS (Oct) | AHRQ, KFF | §6.6 |
| **Feb 16, 2027** | Switch the probe schedule to Mondays only | Calendar | §7 |

## 5. Where each source file comes from

Raw files go in `source-data/` (kept for provenance; the build never reads them directly except via
the staging scripts). Small staged files go in `data/`.

| Domain | Source (where to download) | File in repo | How it's loaded |
|---|---|---|---|
| Medicaid, CHIP, BHP, Marketplace sheets | Workbook compiled by hand from CMS data and state BHP reports (see §5.1) | `data/Enrollment_Tracker.xlsx` | `build_dashboard.py` |
| CMS snapshot PDF (control totals + Data Notes) | medicaid.gov → *Medicaid and CHIP Eligibility Operations and Enrollment Snapshot* (`https://www.medicaid.gov/medicaid-and-chip-eligibility-operations-and-enrollment-snapshot`) | `source-data/cms-snapshots/snapshot-YYYY-MM.pdf`; caveats in `data/cms_data_notes.md` | Read by Claude during updates |
| Medicaid/CHIP monthly data (workbook source) | CMS snapshot data, Excel/CSV: https://data.medicaid.gov/medicaid-chip-eligibility-enrollment-snapshot-data | Copied into the workbook (§5.1) | Monthly |
| Medicaid/CHIP state history (revised) | data.medicaid.gov → *State Medicaid and CHIP Applications, Eligibility Determinations, and Enrollment Data* (Performance Indicator file) | Not in repo yet — upload to `source-data/cms-performance-indicator/` if you need history before Dec 2025 | Ad hoc |
| Medicare | data.cms.gov → *Medicare Monthly Enrollment* | `source-data/Medicare_Monthly_Data.csv` (latest drop) + `.zip` (full history) | `make medicare` → `data/medicare.json` |
| ACA cost sharing | CMS → Marketplace *Public Use Files* (Plan Attributes PUF; Benefits & Cost-Sharing PUF) | `source-data/plan-attributes-puf (13).zip`, `benefits-and-cost-sharing-puf (2).zip` + dictionaries | `make cost-sharing` → `data/cost_sharing.csv` |
| ESI national trend | Census → CPS ASEC health insurance tables, **HHI-01** | `source-data/asec_2025.xlsx` | Staged to `data/esi_coverage_cps.csv` |
| ESI by state | Census → ACS 1-year, **HI05** | `source-data/acs_2024.xlsx` | Staged to `data/esi_coverage_acs.csv` |
| ESI premiums/contributions | AHRQ MEPS-IC → Table II, one CSV per state (`State2025-TableII.csv`) | `source-data/meps-ic/1yr/` | Staged to `data/esi_cost_meps.csv` |
| ESI benchmark | KFF Employer Health Benefits Survey | `data/esi_benchmark_kff.csv` | Direct |
| State Marketplace figures | Each state marketplace's site (register: `config/marketplace_sources.csv`) | `data/marketplace_state_reported.csv`; documents in `source-data/state-marketplace/` | Probe + human review |
| National Marketplace context | KFF, CBO, CMS, Mark Farrah Associates | `data/marketplace_national_context.csv` | Probe + human review |

GitHub's web uploader limits files to 25 MB and 100 files per upload. Zip anything larger. To create a
folder in the web uploader, type the path into the filename box (e.g. `source-data/new-folder/README.md`).

### 5.1 The workbook (`data/Enrollment_Tracker.xlsx`)

Keep the filename and sheet names; the build reads sheets by name. Column-level layouts are in
`CLAUDE.md` → *Workbook sheets*. How each sheet is built:

**Shared layout rules (all monthly sheets)**
- Data are stacked in **monthly blocks**, newest block at the bottom. A new month is added by
  appending a block; earlier blocks are never edited unless CMS revises them.
- Each block has **51 rows (50 states + DC) followed by one `United States` row**. States are
  written as full names but **ordered by postal abbreviation** (Alaska, Alabama, Arkansas, Arizona,
  … Wisconsin, West Virginia, Wyoming), which is the order CMS's data downloads use. Order doesn't
  affect the build, but keep it consistent.
- `Reporting Period` is the **first day of the month** as a real Excel date (e.g. `2026-07-01`), except
  the Marketplace OEP block, which uses the text `OEP`. Check the year: April 2026 once arrived as
  `2025-04`.
- The `United States` row is **Excel formulas**, not typed numbers: `=SUM(...)` over that block's 51
  state rows, column by column. The build checks that national equals the sum of states, so never
  type a national figure in. When you append a block, copy the previous block's US row and shift
  its ranges.
- Missing values are left blank or entered as `-`. Never enter 0 for a value that wasn't reported.

**`Mcaid`** (16 columns; Dec 2025 onward)
- Enrollment: `Total Medicaid Enrollment`, `Total Medicaid Adult Enrollment`.
- Renewals: `…Renewal Initiated`, `…Renewal Due`, `…Renewed (Total)`, `…Ex Parte`, `…Renewal Form`,
  `…Disenrolled at Renewal (Total)`, `…Determined Ineligible`, `…Procedural Reasons`, `…Pending Renewal`.
- Three share columns are **formulas**, copied down: `Disenrolled Share` `=J/F` (disenrolled ÷
  due), `Ineligible Share` `=L/J` and `Procedural Share` `=N/J` (each ÷ disenrolled).
- Source: **CMS Medicaid & CHIP Eligibility Operations and Enrollment Snapshot data** (Excel/CSV), https://data.medicaid.gov/medicaid-chip-eligibility-enrollment-snapshot-data. Enrollment and renewal columns both come from this one dataset; the share columns are calculated in the workbook.
- Check every new month against the snapshot PDF (medicaid.gov). Upload the PDF to Claude to confirm the numbers match and to extract the Data Notes into `data/cms_data_notes.md`.

**`CHIP`** (5 columns; Dec 2025 onward)
- `Total CHIP Enrollment` and `Medicaid and CHIP Child Enrollment` are entered as reported.
- `Medicaid Child Enrollment` is a **formula**, `=E−C` (combined child minus CHIP), copied down. CMS
  doesn't publish Medicaid child directly.
- Source: the same CMS snapshot dataset (https://data.medicaid.gov/medicaid-chip-eligibility-enrollment-snapshot-data). Check: for every state, `Medicaid Child` should equal `Mcaid` Total − Adult for
  the same month. The July 2026 upload failed this check.

**`Mcaid Peak Baseline` and `CHIP Peak Baseline`** — one block dated March 2023, the pre-unwinding
peak. Static; never updated monthly. Arizona's `Medicaid and CHIP Child` is 0 (not reported then).
Source: the same CMS snapshot dataset, March 2023 reporting period.

**`BHP`** (3 columns; Jan 2026 onward) — blocks of **4 states (DC, MN, NY, OR) + a `United States`
row** (`=SUM` of the four). States that haven't reported a month are entered as `-`, so the national
total is meaningful only for months all four report (currently January only). Sources, one per state:
- **Minnesota** (MinnesotaCare): MN DHS enrollment report, https://www.dhs.state.mn.us/main/idcplg?IdcService=GET_DYNAMIC_CONVERSION&RevisionSelectionMethod=LatestReleased&dDocName=DHS16_141529
- **New York** (Essential Plan; BHP from July 2026): NY State of Health monthly enrollment data, https://info.nystateofhealth.ny.gov/enrollmentdata
- **Oregon** (OHP Bridge): OHA Medicaid enrollment reports, https://www.oregon.gov/oha/hpa/analytics/pages/medicaid-enrollment.aspx
- **DC:** no ongoing source. The sheet holds a single January 2026 figure (15,722) and `-` for later months; see the open question below.

**`Marketplace (2)`** (18 columns) — the live Marketplace sheet. (`Marketplace` is an old copy;
leave it, the build ignores it.)
- **OEP block:** one row per state from CMS's 2026 **OEP State-Level Public Use File**: platform,
  plan selections, new and re-enrollees, average premium before/after APTC, APTC counts and
  averages, and metal-tier counts. Suppressed metal cells are `-`. The US row sums the
  count columns.
- **Monthly blocks (Jan–Aug 2026):** only `Number of Consumers with an Exchange Plan Selection` is
  filled. Despite the column name, these are **effectuated** enrollment counts. Other columns are
  blank. States CMS hasn't reported for a month are blank. Source: CMS **Health Insurance Exchanges Monthly Effectuated Enrollment**, https://data.cms.gov/summary-statistics-on-beneficiary-enrollment/health-insurance-marketplace/health-insurance-exchanges-monthly-effectuated-enrollment.
- The national monthly rows are `=SUM` formulas over the states, so they only exist for months all 51 report (Jan and Feb 2026).
- **The April 2026 national cell holds 19,200,000.** That is February 2026 effectuated enrollment (19,169,147) rounded, entered in the April row. The build excludes it (`NATIONAL_POST_OEP_EXCLUDE_FROM`); it is safe to clear the cell.

**`Marketplace Feb. Effec. Enroll`** (4 columns: State, Year, Month, Effectuated Enrollment) —
January and February effectuated enrollment for 2025 and 2026, from CMS's effectuated enrollment
data. Uses **two-letter state codes**, with the `United States` row first in each block. Source:
the same CMS monthly effectuated enrollment dataset (https://data.cms.gov/summary-statistics-on-beneficiary-enrollment/health-insurance-marketplace/health-insurance-exchanges-monthly-effectuated-enrollment). National: Jan 2025 22,216,133; Feb 2025
21,776,626; Jan 2026 20,191,459; Feb 2026 19,169,147.

**National totals:** for Medicaid, CHIP, BHP and Marketplace, the `United States` row is the sum of
the 50 states + DC. CMS's own national figures aren't used. (Medicare works the same way, but
`build_medicare.py` does the summing because it must drop the territories.)

**Monthly routine (Medicaid, CHIP):**
1. Download the newest month from the CMS snapshot dataset (link above).
2. Append a block of 51 state rows to `Mcaid` and `CHIP`, keeping the existing order, plus a
   `United States` row with `=SUM` formulas. Copy the formula columns (shares; Medicaid child) down.
3. Download the snapshot PDF from medicaid.gov and give both files to Claude with prompt §6.1. Claude
   confirms the numbers match the PDF and updates the Data Notes register.

**Open question:** where did DC's January 2026 BHP figure (15,722) come from? If there's no
ongoing source, note it on the BHP tab or drop DC.

Known workbook traps (all caught before, all documented in `CLAUDE.md`): April 2026 rows arrived
mislabeled `2025-04`; the July 2026 upload first keyed Total Medicaid + CHIP into the `Medicaid and
CHIP Child` column. Before building, confirm the new month's CHIP `Medicaid Child` equals Medicaid
`Total − Adult` for every state.

## 6. Ready-to-paste prompts

Paste these into a new Claude session with the repo attached. Each tells Claude to stop and report
rather than guess.

### 6.1 Monthly Medicaid/CHIP/BHP update

> New monthly data. I've uploaded the updated `data/Enrollment_Tracker.xlsx` and the CMS snapshot PDF
> for [MONTH YEAR] (move it to `source-data/cms-snapshots/snapshot-YYYY-MM.pdf` if it landed at the repo
> root). Follow CLAUDE.md's *Monthly update* procedure. Specifically:
> 1. Confirm only the new month was added to `Mcaid`, `CHIP` and `BHP`, that earlier months are
>    unchanged (report any revisions), the year in `Reporting Period` is right, and CHIP `Medicaid
>    Child` = Medicaid `Total − Adult` for every state.
> 2. Check every national and state figure against the PDF's tables (Medicaid, adult, CHIP, Medicaid
>    and CHIP child, renewals due, renewal outcome percentages). Stop and report any mismatch.
> 3. Extract the PDF's Data Notes appendix and update `data/cms_data_notes.md` (new, resolved, changed
>    caveats). Surface any newly active state caveat on the dashboard.
> 4. Re-check California (constants hold?), Nevada (corrected yet?), Illinois (any further shift?),
>    Arizona, New York BHP, and every watch item in CLAUDE.md; flag new anomalies (any state moving >3%
>    or an implausible renewal mix) without adjusting them.
> 5. Add the new month to `CHIP_CHILD_CONTROL` and the strict set.
> 6. Rebuild, run tests, render every tab, confirm untouched tabs' data constants are byte-identical.
> 7. Report headline figures as reported and like-for-like (California restated; Illinois excluded at
>    both ends), plus changes since January and year over year. Push a branch; don't merge.

### 6.2 Medicare update

> I've uploaded the new Medicare Monthly Enrollment file as `source-data/Medicare_Monthly_Data.csv`.
> Run `make medicare`, report which months came from the CSV and any revisions to earlier months, check
> the reconciliation identities, confirm MA penetration uses the Part A&B denominator, rebuild, and
> report the latest national total, MA penetration and dual share. Push a branch.

### 6.3 Reviewing the Marketplace probe PR

The probe opens or updates one PR titled **"Marketplace probe: pending figures."** For each new row:
open its `source_url`, find the `quote`, confirm the number, measure type and dates match. Edit
`reviewer_status` from `pending` to `approved` (or `rejected` for national rows) in the PR, then merge.
Only approved rows appear on the dashboard. **Pending at handoff:**
- On the open probe PR: Maine's first 2027 snapshot (47,811 plan selections as of Nov 14, plus 1,332
  new consumers) and Washington's Fall 2026 report (260,316 enrolled, 172,305 with APTC, Sep 30).
- Already on `main` as pending: Colorado October effectuated (233,724), Minnesota May effectuated
  (125,700, read from a chart label), and the 2026 `enrolled_other` rows for DC, MA, NY and CT. These
  are 2026 baselines only; approve them only if you want them available for year-over-year comparisons.

### 6.4 Marketplace effectuated or OEP update

> CMS published [effectuated enrollment for MONTH / the 2027 OEP state-level PUF]. I've uploaded it to
> `source-data/`. Add it to the `Marketplace (2)` / effectuated sheet per CLAUDE.md's Marketplace
> conventions (plan selections ≠ effectuated; keep `NATIONAL_POST_OEP_EXCLUDE_FROM` logic; Oregon left
> HealthCare.gov for 2027 — subtract 118,372 from any 2026 HC.gov base). Verify national totals, rebuild,
> report year-over-year changes on a like-for-like basis. Push a branch.

### 6.5 Yearly cost-sharing refresh

> New benefit-year Exchange PUFs are in `source-data/`. Set `CS_BENEFIT_YEAR` to [YEAR], run
> `make cost-sharing`, run the four sanity checks, report cells that moved more than 10%, rebuild. Label
> stays "plan-level simple average (not enrollment-weighted)". Push a branch.

### 6.6 Yearly ESI refresh

> New [CPS ASEC HHI-01 / ACS HI05 / MEPS-IC / KFF EHBS] file uploaded to `source-data/`. Follow
> CLAUDE.md's *Annual ESI update checklist* exactly, including the restatement check on overlapping CPS
> years, `ESI_CPS_MOE`, `ESI_CPS_BREAKS` and `ESI_CPS_NOTES`. Never compare ACS and CPS across different
> years. Push a branch.

### 6.7 Verifying a figure before it goes in a memo, letter or email

> Verify this sentence against the repo's data and the original source: "[SENTENCE]". Check the
> number, the period, the comparison period, the scope (Marketplace vs. individual market; plan
> selections vs. effectuated; as reported vs. like-for-like), the rounding, and the attribution. Flag
> anything a CMS, CBO or Hill reviewer could challenge.

## 7. The Marketplace probe (scheduled task)

- **What it does:** Mondays and Thursdays at 9:47 ET, reads every state marketplace in
  `config/marketplace_sources.csv` plus CMS, KFF, CBO and Mark Farrah; appends any new figure (with
  exact quote and URL) as `pending`; writes one line per source to `logs/marketplace_probe_log.csv`;
  rebuilds and tests; pushes branch `marketplace-probe`; updates the single probe PR.
- **It runs under Isaac's account.** To take it over, recreate it under yours: claude.ai/code →
  **Scheduled tasks** (claude.ai/code/routines) → **New task** → paste the task prompt (copy it from
  Isaac's task: open it → ⋯ → Edit) → **Repository:** `INicchitta12/enrollment-tracker` → **Cloud
  environment:** your Full-network environment → remove unneeded connectors → save. Then Isaac deletes
  his copy so two probes don't push to the same branch.
- **Rules baked into the prompt (keep them):** WebFetch first, curl only as fallback, never retry with
  altered headers on a 403; never invent, round or sum numbers; reader-facing text in `notes`,
  reasoning in `review_notes`; the probe never approves its own rows; dry-run push check first.
- **Known gaps:** Maryland, Massachusetts and New York block automated reads (403); upload their files
  by hand to `source-data/state-marketplace/` if you need them. Georgia publishes no enrollment data.
  New Mexico, Virginia and Massachusetts use dashboards the probe can't read.
- **Feb 16, 2027:** switch the schedule to Mondays only (edit the task's schedule).

## 8. Caveats you must know (summary — details in CLAUDE.md)

| Issue | What to do |
|---|---|
| **California** dropped ~384,186 limited-benefit enrollees from Medicaid in March 2026 without restating prior months | Dashboard restates pre-March months down (AHA estimate). For year-over-year or since-January comparisons, cite "like-for-like" figures with the California restatement, or say "as reported by CMS". |
| **Illinois** moved ~74,000 children from Medicaid to CHIP (June–July 2026) | Exclude Illinois at both ends for CHIP and Medicaid-child comparisons spanning June 2026. As reported, CHIP looks flat; excluding Illinois, it fell 1.7% year over year. |
| **Nevada** March 2026 adult/child split off by ~12,000 (total fine) | Caveat stays until CMS corrects March. |
| **Arizona** has no child breakout Feb 2020–Apr 2024 | Child peak comparison excludes Arizona at both ends. |
| **New York** Essential Plan became a BHP July 1, 2026 (−343,549 in June) | Program redefinition, not coverage loss. Never add EP to NY Marketplace figures. |
| **Montana, Ohio, West Virginia** count anyone enrolled at any time in the month | Consistent March 2025–April 2026 per CMS footnotes; not comparable across states. |
| **Medicaid child is derived** (Medicaid and CHIP child − CHIP) | Always label "derived"; includes a small number of pregnant women in CHIP. |
| **Renewal outcomes are initial** | Keep the "initial outcomes, as originally reported" labels; don't splice CMS's quarterly updated outcomes in. |
| **Marketplace OEP = plan selections; later months = effectuated** | Different measures; the gap isn't pure attrition. |
| **Individual market ≠ Marketplace** | KFF 20.5M (June 2026, est., incl. off-exchange) and MFA 22M are individual market; CMS 19.2M (Feb 2026) is Marketplace effectuated. Never net or co-plot them. |
| **Oregon** left HealthCare.gov for 2027 | Subtract 118,372 from any 2026 HC.gov base. |
| **ESI: ACS vs CPS** are different measures (point-in-time vs any time in year) | Compare only same-year; never compute a change across sources. ACS 2025 is delayed. CPS 2024 was restated to 180.5M. |
| **CMS PDF vs CSV vintages** | PDFs are point-in-time; the data.medicaid.gov CSV is revised and authoritative. Small differences are expected; for CHIP they can be large relative to the change. |

## 9. Verified figures in current use (as of Nov 23, 2026)

These were checked line by line for recent advocacy pieces. Re-verify before reusing if newer data
exists.

**Medicaid and CHIP, July 2026 vs. July 2025 (as reported by CMS):** Medicaid and CHIP 72.9M (−6.0%);
Medicaid 65.7M (−6.5%); adults 38.1M (−6.4%); children (derived) 27.7M (−6.8%); CHIP 7.2M (roughly flat,
−0.3% to −0.5% depending on vintage). Like-for-like (California restated, Illinois excluded): Medicaid
−5.9%, adults −5.5%, children −6.5%, CHIP −1.7%; Medicaid and CHIP incl. Illinois −5.5%. July 2025
counts are from the CMS Performance Indicator file (Aug 2026 vintage): Medicaid 70,341,156; adult
40,632,703; CHIP 7,242,682; derived child 29,708,453.

**Marketplace:**
- 2026 OEP plan selections 23,130,860, down 1.19M (−4.9%) from 24,319,713 (CMS OEP PUFs; KFF reports "1.2 million").
- Effectuated, Feb 2026: 19.2M vs 21.8M in Feb 2025, down about 2.6M (−12%) (CMS via KFF).
- Individual market, June 2026: an estimated 20.5M, down 18% from 25.2M (KFF, from Mark Farrah data).
- Average premium payments after tax credits, 2026: up 58%, $113 → $178/month across all enrollees (CMS OEP PUFs); among APTC recipients $74 → $96 (+30%).
- Average Marketplace deductible, 2026: up 37%, $2,759 → $3,786 per person, "steepest increase in history" (KFF, May 19, 2026). No 2027 equivalent until spring 2027.
- Benchmark silver, 2027: $703/month for a 40-year-old before tax credits (KFF corrected figure; not $704), +13% vs 2026 (+11% HC.gov states, +16% SBM states), +42% vs 2025.
- 2027 required contribution: up to 10.22% of income; no credit above 400% FPL (IRS Rev. Proc. 2026-26).
- CBO: Marketplace enrollment falls from 22.4M (2025) to 13.1M (2027), down 9.3M (more than 40%). Includes all enacted policy, not only the EPTC expiration; it's an enrollment projection, not "people losing coverage."

**Medicare:** June 2026 MA penetration 55.5% of Part A&B beneficiaries (50 states + DC; includes cost
plans/PACE). KFF's 55% uses a different definition; don't present them as the same measure.

**ESI:** CPS 2025 180.7M (+0.1% vs 2024, within sampling error — don't call it growth); ACS 2024 183.0M.

## 10. Rules for a public repo

- **No organizational branding** on the page, and keep `noindex, nofollow` in `template.html`.
- **No licensed or confidential data.** Strata Decision Technology figures (uncompensated care,
  ED self-pay) are licensed and are **not** in this repo; don't add them. The same goes for any
  member-hospital or confidential data.
- Advocacy labels like "AHA analysis of CMS data" belong in memos, not on the public dashboard.
- Don't commit huge raw files to `data/`; raw files go in `source-data/`, zipped if large.

## 11. Open items at handoff

- Review and merge the open probe PR (Maine 2027 and Washington rows pending; §6.3).
- Recreate the probe under the new owner (§7); switch to Mondays on Feb 16, 2027.
- DC BHP: confirm the source of the January 2026 figure, or drop DC (§5.1).
- Next CMS Medicaid/CHIP snapshot (August 2026 data) is due around end of November 2026.
- ACS 2025 1-year: delayed by Census with no date; restage ESI by state when it lands.
- Watch items in CLAUDE.md: Alabama (procedural elevated), Arkansas (procedural climbing), Virginia
  (pending renewals backlog), Alaska (July enrollment drop), Maine/Oklahoma (CHIP reclassification churn).
- Phone layout: only the ESI tab has one; header and tab bar overflow at 390px.
- Ideas raised but not built: a stacked "all coverage" tab; earlier years of Marketplace data; 2027
  plan-level cost sharing (rerun `make cost-sharing` with `CS_BENEFIT_YEAR = 2027` once the PUFs are in).
