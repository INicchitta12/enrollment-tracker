# Enrollment Tracker Dashboard

Interactive dashboard tracking enrollment and disenrollment trends across **Medicaid**, the **Basic Health Program (BHP)**, and the **ACA Marketplace**.

**Live site:** `https://<username>.github.io/<repo-name>/`

---

## What's in it

| Tab | Contents |
|---|---|
| **Medicaid** | Enrollment KPIs with month-over-month deltas · renewal outcome cascade · procedural vs. ineligible disenrollment breakdown · cumulative impact strip · total/adult enrollment trend · renewal outcome mix (ex parte vs. form) · state disenrollment rate ranking |
| **BHP** | Per-state enrollment trends (small multiples) · state share of national total |
| **ACA Marketplace** | OEP plan selection KPIs · post-OEP effectuated enrollment trend · year-over-year effectuated comparison · state ranking · metal tier and enrollment type composition · premium waterfall before/after APTC |

Medicaid and Marketplace tabs include a **state selector** — every chart and figure on the tab recalculates for the selected state. BHP is national only (four participating states).

---

## Data sources

| Source | Used for | Coverage |
|---|---|---|
| CMS Medicaid & CHIP Eligibility Operations and Enrollment Snapshot | Medicaid enrollment, renewal outcomes, ex parte / form renewals | Dec 2025 – Mar 2026 |
| CMS Medicaid & CHIP Snapshot (published PDF) | National renewal outcome mix, Mar–Nov 2025 only | Mar 2025 – Nov 2025 |
| CMS Basic Health Program enrollment data | BHP enrollment by state | Jan – Jul 2026 |
| CMS Marketplace OEP snapshot | Plan selections, premiums, APTC, metal tiers | OEP 2026 |
| CMS Marketplace effectuated enrollment | Monthly effectuated enrollment, YoY comparison | Jan 2025 – May 2026 |

---

## Methodology notes

**Marketplace post-OEP figures are effectuated enrollment, not plan selections.** The OEP figure (23.1M nationally) counts plan selections at the close of open enrollment; monthly figures thereafter count consumers with effectuated coverage. These are different measures and the drop between them is expected. Tooltips label each accordingly.

**National renewal outcome mix blends two sources.** December 2025 onward uses exact counts from the source workbook. March–November 2025 uses percentages published in the CMS PDF, where *pending* is derived as the residual after the four reported components. Values were validated across the overlapping months and agree within 0.4 percentage points.

**Renewal outcome components are normalized to sum to 100%.** Rounding to one decimal can leave columns at 99.9 or 100.2; components are rescaled proportionally so stacked bars render cleanly. Adjustments are under a quarter of a percentage point.

**BHP reporting coverage varies by state.** Minnesota reports through July 2026, Oregon through June, New York through April, and DC has reported January only (program launched Jan 2026). The national total reflects January, the single month all four states report. New York's figure is Essential Plan Expansion enrollment, reported in the BHP series under a section 1332 waiver.

**Medicaid renewal denominators.** Renewed, disenrolled, and pending are expressed as shares of *renewals due* in the reporting month, not of total enrollment. Procedural and ineligible shares are expressed against total disenrolled.

---

## Updating the dashboard

1. Open the repository on GitHub
2. Click `index.html`
3. Click the pencil (**Edit**) icon, or use **Add file → Upload files** to replace it wholesale
4. Commit to `main`

GitHub Pages redeploys automatically, usually within a minute. Hard-refresh the live page (Ctrl+Shift+R / Cmd+Shift+R) to clear the browser cache.

To regenerate the file from an updated workbook, see `build/` if the build pipeline has been added to this repo.

---

## Technical notes

- Single self-contained HTML file — all data is embedded, no database or backend
- Charts render via Chart.js loaded from CDN, so **an internet connection is required** to view
- Tagged `noindex, nofollow` so the page is link-shareable but not surfaced in search results
- Renders in any modern browser; designed for desktop viewing

## Embedding in PowerPoint

Insert → Object → Create from File → select the HTML file. Requires internet access when presenting. For a static slide, screenshot the tab you need instead.
