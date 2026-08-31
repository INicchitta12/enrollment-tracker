# CMS Snapshot — Data Notes register

Consolidated "Data Notes" appendix (the *Data Type × Data Notes* table near the end of each
CMS Eligibility Operations and Enrollment Snapshot PDF). One row per **distinct** caveat, with
the range of report editions it appeared in. The identical "What You Should Know When Using the
Data" boilerplate slides are deliberately **not** captured here.

**Source PDFs:** `source-data/cms-snapshots/snapshot-YYYY-MM.pdf`
**Editions processed (6):** Dec 2025, Jan 2026, Feb 2026, Mar 2026, Apr 2026, May 2026.
**Dashboard data window (Medicaid & CHIP):** Dec 2025 – May 2026. A caveat is *Active* if it
touches any month in that window; *Historical* if it only touches earlier periods (kept for when
the range is extended back).

**How to read "Appeared in":** the first edition listing a caveat is when it *first appeared*;
the last is when it *stopped being repeated*. A caveat dropping out usually means CMS resolved it
— confirm before assuming, but treat disappearance as a resolution signal.

> Some existing CHIP tab caveats in `CLAUDE.md` (Montana/Ohio/West Virginia point-in-time,
> Colorado/Hawaii/New Hampshire retroactive, Alaska, Rhode Island) come from the **S-CHIP
> enrollment-by-state appendix footnotes**, a different source than this Data Notes table, so
> they do not all reappear below. That is expected.

---

## Active caveats

Issues touching data currently in the dashboard (Dec 2025 – May 2026).

| State | Program / data type | Issue | Period affected | Dashboard impact | CMS will correct? | Appeared in |
|---|---|---|---|---|---|---|
| **California** | Medicaid enrollment (total, adult) | Revised reporting to exclude limited-benefit individuals; prior months not restated, so data are **not comparable to earlier months**. CMS's revision date shifted between editions: Dec 2025 / Jan 2026 / Feb 2026 editions said **November 2025**; Mar 2026 / Apr 2026 / May 2026 editions say **March 2026** — the workbook data confirm the break is at March (see gap note). | Mar 2026 forward | CA + national Medicaid total & adult. Dashboard now puts the whole series on the revised (exclude) basis by **restating the pre-March-2026 months down** (`CA_ENROLL_ADJUST`, `CA_ADULT_ADJUST`), leaving Mar 2026+ as CMS reports them so current figures tie to CMS control totals. Disclosed on the Medicaid tab. | No — state has still not restated prior months (re-confirmed verbatim in the May 2026 edition) | Dec 2025 – May 2026 (wording changed after Feb 2026) |
| **Nevada** | Medicaid child enrollment | March 2026 child enrollment overstated by ~12,000 due to a reporting error. CMS's wording flags **child only**; the workbook and CMS's own March edition show the overstatement is **offset by an equal understatement of Medicaid adult**, leaving the March **total** unaffected (CMS published NV March total at −0.3%, in line with neighbouring months). **Dropped from the May 2026 Data Notes**, but the correction has **not** reached the data — the March spike (child +11,447, adult −13,183) and its April reversal (child −12,482, adult +9,951) are both still present unchanged. | Mar 2026 | NV national child & adult splits; NV Mar→Apr child change overstated as a decline and Mar→Apr adult change overstated as a rise. **Total** Medicaid enrollment unaffected. Surfaced on the Medicaid and CHIP tabs; left as reported. | **Yes** — still pending; note withdrawn before the data were fixed | Apr 2026 – May 2026 (note dropped May 2026; issue unresolved in data) |
| **Georgia** | Eligibility processing (renewal outcomes) | Reports individuals who stayed eligible after a change in circumstances and were granted a new 12-month period **together with** those due for renewal in the month. | Ongoing (all editions) | Inflates Georgia's "renewals due" denominator and distorts its renewal-outcome mix vs other states. **Surfaced** on the Medicaid tab when Georgia is selected. | No — methodology | Dec 2025 – May 2026 (all) |
| **North Carolina** | Eligibility processing (renewal outcomes) | Reports renewal outcomes only for renewals it *initiated* and scheduled to complete in the report month; excludes renewals due that it could not initiate in time. | Ongoing (all editions) | Undercounts NC renewals due / outcomes; not comparable to states reporting all due renewals. **Surfaced** on the Medicaid tab when North Carolina is selected. | No — methodology | Dec 2025 – May 2026 (all) |
| **Wyoming** | Eligibility processing (renewal outcomes) | State identified an issue with its **January 2026** eligibility-processing submission; corrected data forthcoming. | Jan 2026 | WY Jan 2026 renewal-outcome figures suspect. **Intentionally not surfaced** on the dashboard — one month, dropped from later editions (resolved); a standing warning would misread. Documented here only. | **Yes** — appears resolved (dropped Feb 2026) | Jan 2026 only |

**Gap note — California, resolved.** CMS's Dec 2025, Jan 2026 and Feb 2026 editions dated this
revision to **November 2025**; the Mar–Apr editions restate it to **March 2026**. Investigated
against the workbook: California runs a smooth trend Dec→Feb (−103,503, then −110,489) and then a
single **−491,182 cliff at Feb→March 2026** — there is **no level break in the Dec/Jan/Feb
figures**, so the exclusion landed in the March data and those earlier months are fully on the old
include-basis. The "November 2025" label is therefore *not* borne out by the data; **March is the
operative revision month** and no separate November adjustment is warranted. The dashboard now
restates the pre-March-2026 CA months down onto the revised basis (rather than adding back to the
future), so March 2026+ — the most-scrutinized months — are shown exactly as CMS reports them and
tie to CMS control totals. See the California sections of `CLAUDE.md`.

---

## Historical caveats

Issues confined to periods **before** the current window (or to lagged appendix series). Kept so
the caveat is on record if the dashboard range is ever extended back.

| State | Program / data type | Issue | Period affected | Relevance if range extends | Appeared in |
|---|---|---|---|---|---|
| **Arizona** | Medicaid adult/child enrollment | Did not report adult/child Medicaid breakouts. Pre-May 2024, national child+CHIP totals include AZ CHIP only; national Medicaid adult totals exclude AZ adult. | Feb 2020 – Apr 2024 | Any national adult or child trend extended before May 2024 is distorted for AZ. | Dec 2025 – May 2026 (all) |
| **Rhode Island** | Medicaid enrollment | Could not report; **Nov 2024 total used as a proxy** for both months. | Dec 2024 – Jan 2025 | National totals for those months rest on an RI proxy. | Dec 2025 – Jan 2026 (dropped Feb 2026) |
| **Rhode Island** | Applications received | Could not report applications. | Dec 2024 – Jan 2025 | Applications data not shown in dashboard. | Dec 2025 – May 2026 (all) |
| **Rhode Island** | Eligibility processing | Could not report eligibility/renewal data. (Jan 2026 edition narrows this to Jan 2025 only.) | Dec 2024 – Jan 2025 | Renewal outcomes missing RI for those months. | Dec 2025 – Jan 2026 (dropped Feb 2026) |
| **New York** | Applications received | Methodology change to include additional applications required by CMS specs. | Jul 2024 forward | Applications data not shown in dashboard. | Dec 2025 – May 2026 (all) |
| **Pennsylvania, Wyoming** | Updated renewal outcomes (appendix) | Updated the eligibility status of the cohort; data may include eligibility actions occurring after the renewal. | Lagged quarterly cohort | Affects the Updated Renewal Outcomes appendix, not the monthly series. | Dec 2025, Mar 2026 |
| **California / Oregon, Rhode Island** | S-CHIP enrollment (appendix) | S-CHIP counts may be inaccurate — Medicaid-vs-CHIP classification misalignment in T-MSIS. Dec 2025 lists **California & Rhode Island**; Mar 2026 lists **Oregon & Rhode Island** (the flagged states changed). | Lagged S-CHIP quarterly appendix | Concerns the separate-CHIP appendix series, not the monthly total-CHIP figures in the dashboard. | Dec 2025, Mar 2026 |
| **Colorado** | S-CHIP enrollment (appendix) | S-CHIP data not reported for the period. | S-CHIP appendix period (~Oct–Dec 2025) | Separate-CHIP appendix only; monthly total-CHIP identity is checked at build and includes CO. | Mar 2026 only |
| **(national)** | BHP / Other | January 2020 BHP enrollment is folded into the February 2020 total. | Jan–Feb 2020 | Historical BHP only. | Dec 2025 only |

---

## Program-level notes

Structural / non-time-bounded items — coverage facts, methodology, and which states do or don't
run a given program. Not data errors; context for interpretation.

**CHIP program structure**
- **States with no separate (S-)CHIP program** — CHIP is Medicaid-expansion CHIP only:
  **Alaska, District of Columbia, Hawaii, New Hampshire, New Mexico, North Carolina,
  North Dakota, Ohio, South Carolina, Vermont, Wyoming.** *(Dec 2025, Mar 2026 editions.)*

**BHP / Other coverage**
- BHP enrollment is reported by **District of Columbia, Minnesota, New York, Oregon**. *(Dec 2025
  edition lists three states — MN, NY, OR — DC added from the Jan 2026 edition.)*
- **New York** reports the **Essential Plan (EP) Expansion**, a §1332-waiver program, as of the
  **March 2024** data. *(All editions; "new" dropped after Jan 2026. Already reflected in the BHP tab.)*
  **New in the May 2026 edition:** NY's §1332 waiver terminates **1 July 2026** and the state is
  **transitioning the EP back to a BHP**; CMS warns "transition activities are underway and may be
  reflected in the reported data," and attributes the **May 2026 BHP decline** to the start of those
  activities. The workbook's BHP series already shows the step: NY falls **1,663,063 (May) →
  1,319,514 (June)**, −343,549. This is a **programme transition, not a data error** — but the NY
  BHP series is not continuous across July 2026, so a June-onward NY figure should not be read as
  attrition from the EP level. *(May 2026 edition.)*
- **Oregon** began reporting BHP as of the **July 2024** data. *(All editions.)*
- **District of Columbia** began reporting BHP as of the **January 2026** data. *(Jan 2026 onward
  — in the current window; DC's BHP series starts Jan 2026.)*

**Marketplace**
- Dec 2025 edition: Marketplace enrollment includes FFM, SBM-FP, and SBM data.
- **As of the January 2026 data, Marketplace enrollment is no longer in this snapshot** ("available
  separately soon"). *(Jan 2026 onward.)* The dashboard's post-Dec-2025 Marketplace figures
  therefore come from CMS's separate effectuated-enrollment releases, not this snapshot.

**Applications received** *(data type not shown in dashboard)*
- May be an **undercount** — a state may omit some applications, populations, or limited-benefit programs.
- May be an **overcount** — duplicate applications, HealthCare.gov account transfers, administrative
  transfers, or renewals/redeterminations may be included.

**MAGI application processing time** *(data type not shown in dashboard)*
- Counts may omit some MAGI determinations; may include redeterminations or some non-MAGI
  applications; may report at the application/household level rather than per individual.

**Call center** *(data type not shown in dashboard)*
- **South Dakota** has no call center and reports no call-center metrics. *(All editions.)*
- **California** began reporting complete data from all its call centers in **January 2026**.
  *(Jan 2026 onward.)*

**Renewal-outcome timing (all states)**
- Procedural terminations take effect at the **start of the month after** the renewal was due
  (e.g., a renewal due/reported in March terminates effective April 1). Relevant when aligning a
  procedural-disenrollment count to the month it is reported in.
- See **Updated Renewal Outcomes** on Data.Medicaid.gov for states' updated reporting
  methodologies, including states reporting dispositions on a *date-from* specification.
  *(Dec 2025, Mar 2026 editions.)*

---

## Cross-edition change log

Appearances and disappearances that carry meaning:

- **Dec 2025 → Jan 2026:** California call-center note appears; Marketplace becomes "no longer in
  report"; DC added to BHP reporters; Wyoming Jan 2026 eligibility-processing issue flagged;
  Rhode Island enrollment-proxy note still present.
- **Jan 2026 → Feb 2026:** Rhode Island Dec 2024 / Jan 2025 notes (enrollment + eligibility
  processing) **drop out** → resolved / now outside CMS's rolling window. Wyoming Jan 2026 issue
  **drops out** → resolved.
- **Feb 2026 → Mar 2026:** California revision date **changes from November 2025 to March 2026**.
  Quarterly appendices (Updated Renewal Outcomes, S-CHIP by state) return, bringing the PA/WY
  cohort note, the S-CHIP T-MSIS-misalignment note (now Oregon & RI, not California & RI), the
  "no S-CHIP program" list, and a new Colorado S-CHIP "not reported" note.
- **Mar 2026 → Apr 2026:** **Nevada** March 2026 child-enrollment overstatement (~12,000) appears
  for the first time. Quarterly appendix notes drop back out.
- **Apr 2026 → May 2026:** **Nevada** child-enrollment note **drops out** — but, unusually, *not*
  because it was resolved: the March figures are unchanged in the workbook and the May state tables
  carry no March column, so the correction CMS promised has not landed. Treated as **still active**
  rather than resolved (the register's "disappearance = resolution" heuristic is overridden here by
  direct inspection of the data). **New York BHP** bullet gains the §1332-termination / EP→BHP
  transition wording and CMS attributes the May BHP decline to it. California note repeats
  **verbatim**, still stating prior months are not revised → the continuity restatement stands.
  No other additions; Arizona, Georgia, North Carolina, applications, MAGI, call-center and
  procedural-timing notes all repeat unchanged. Quarterly appendix notes remain out.
