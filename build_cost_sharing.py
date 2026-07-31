"""Aggregate ACA Marketplace plan-level cost sharing by state and metal tier.

Reads two CMS Exchange PUFs (Plan Attributes + Benefits & Cost Sharing) from
``source-data/`` — the large PUF zips are kept there and gitignored once
extracted, never committed — and writes ``data/cost_sharing.csv`` with the
simple (plan-level, NOT enrollment-weighted) mean deductible, out-of-pocket
maximum, and primary care copay for each state x metal tier, plus a pooled
United States row.

This is a once-per-benefit-year step, separate from the monthly
``build_dashboard.py`` rebuild. Rerun it only when a new PUF is published:

    python build_cost_sharing.py

See CLAUDE.md ("ACA cost sharing by metal tier") for the full methodology.
"""

import csv
import glob
import os
import re
import sys
import tempfile
import zipfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(HERE, "source-data")
OUT_CSV = os.path.join(HERE, "data", "cost_sharing.csv")

BENEFIT_YEAR = "2026"  # current benefit year (py26 PUFs)

# Metal tiers we keep, in canonical (most→least cost-sharing) order.
TIER_ORDER = ["Bronze", "Silver", "Gold", "Platinum", "Catastrophic"]
# MetalLevel values kept; "Expanded Bronze" is folded into Bronze.
METALS_KEEP = {"Bronze", "Expanded Bronze", "Silver", "Gold", "Platinum", "Catastrophic"}

PRIMARY_CARE_BENEFIT = "Primary Care Visit to Treat an Injury or Illness"

# A base/standard on-exchange plan variant (excludes every CSR variant:
# Zero/Limited Cost Sharing, 73/87/94% AV Silver, and off-exchange duplicates).
BASE_ON_EXCHANGE_RE = re.compile(r"^Standard .* On Exchange Plan$")

_MONEY_RE = re.compile(r"\$\s*([\d,]+(?:\.\d+)?)")


def _find(pattern):
    matches = glob.glob(os.path.join(SOURCE_DIR, pattern))
    if not matches:
        sys.exit(f"ERROR: no file matching {pattern!r} in {SOURCE_DIR}")
    # Newest wins if several CMS re-releases sit side by side.
    return max(matches, key=os.path.getmtime)


def _extract(zip_path, member_hint, tmpdir):
    with zipfile.ZipFile(zip_path) as zf:
        member = next((n for n in zf.namelist() if member_hint in n), None)
        if member is None:
            sys.exit(f"ERROR: no {member_hint!r} CSV inside {zip_path}")
        zf.extract(member, tmpdir)
        return os.path.join(tmpdir, member)


def parse_dollar(value):
    """'$6,350' -> 6350.0 ; 'Not Applicable' / '' -> None."""
    v = (value or "").strip()
    if v == "" or v.lower().startswith("not applicable"):
        return None
    m = _MONEY_RE.search(v)
    return float(m.group(1).replace(",", "")) if m else None


def parse_copay(value):
    """Parse a CopayInnTier1 string to (usable, amount).

    'No Charge[...]'      -> (True, 0.0)     treat No Charge as $0
    '$30 Copay[...]'      -> (True, 30.0)    parse the dollar amount
    'Not Applicable' / '' -> (False, None)   coinsurance-only / unspecified;
                                             EXCLUDE from the copay mean
    """
    if value is None:
        return (False, None)
    v = value.strip()
    low = v.lower()
    if low.startswith("no charge"):
        return (True, 0.0)
    if "$" in v:
        m = _MONEY_RE.search(v)
        return (True, float(m.group(1).replace(",", ""))) if m else (False, None)
    # 'Not Applicable', blank, or anything coinsurance-based lives in CoinsInnTier1.
    return (False, None)


def load_base_plans(plan_attr_csv):
    """Filter the Plan Attributes PUF down to standard on-exchange base plans.

    Returns (rows, filter_report). Each row carries the join key (PlanId),
    state, folded metal tier, and coalesced individual deductible / OOP max.
    """
    counts = dict(start=0, f1_dental=0, f2_exchange=0, f3_year=0, f4_csr=0, f5_metal=0)
    folded = 0
    rows = []
    with open(plan_attr_csv, newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            counts["start"] += 1
            if r["DentalOnlyPlan"] != "No":                       # exclude dental-only
                counts["f1_dental"] += 1
                continue
            if r["QHPNonQHPTypeId"] not in ("Both", "On the Exchange"):  # on-exchange only
                counts["f2_exchange"] += 1
                continue
            if r["BusinessYear"] != BENEFIT_YEAR:                 # current benefit year
                counts["f3_year"] += 1
                continue
            if not BASE_ON_EXCHANGE_RE.match(r["CSRVariationType"] or ""):  # base variant only
                counts["f4_csr"] += 1
                continue
            metal = r["MetalLevel"]
            if metal not in METALS_KEEP:                          # keep the five metal tiers
                counts["f5_metal"] += 1
                continue
            tier = "Bronze" if metal in ("Bronze", "Expanded Bronze") else metal
            if metal == "Expanded Bronze":
                folded += 1
            # Individual deductible / OOP: use the combined (Total EHB) field when
            # present, else the medical-only (MEHB) field. A plan populates exactly
            # one side depending on whether medical & drug limits are integrated.
            ded = parse_dollar(r["TEHBDedInnTier1Individual"])
            if ded is None:
                ded = parse_dollar(r["MEHBDedInnTier1Individual"])
            oop = parse_dollar(r["TEHBInnTier1IndividualMOOP"])
            if oop is None:
                oop = parse_dollar(r["MEHBInnTier1IndividualMOOP"])
            rows.append(dict(plan_id=r["PlanId"], state=r["StateCode"],
                             tier=tier, ded=ded, oop=oop, copay=None))
    return rows, counts, folded


def load_primary_care_copay(benefits_csv, wanted_plan_ids):
    """Map PlanId -> CopayInnTier1 for the primary-care benefit, base plans only."""
    lookup = {}
    with open(benefits_csv, newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            if r["BenefitName"] == PRIMARY_CARE_BENEFIT and r["PlanId"] in wanted_plan_ids:
                lookup[r["PlanId"]] = r["CopayInnTier1"]
    return lookup


def mean_or_blank(values):
    vals = [v for v in values if v is not None]
    return round(sum(vals) / len(vals)) if vals else None


def validate(us, table):
    """Run the four sanity checks; exit non-zero if a hard check fails.

    ``us`` maps tier -> {ded, oop, copay} for the United States row. ``table`` is
    the full list of [state, tier, ded, oop, copay] output rows. Zeros/blanks are
    only tolerated for the documented cases: Platinum deductibles (genuinely ~$0)
    and Catastrophic copays (No Charge -> 0, or coinsurance -> blank).
    """
    problems = []

    ded = [us[t]["ded"] for t in ["Bronze", "Silver", "Gold", "Platinum"]]
    if not all(a > b for a, b in zip(ded, ded[1:])):
        problems.append(f"deductibles not monotonic Bronze>Silver>Gold>Platinum: {ded}")

    cat = us["Catastrophic"]
    if abs(cat["ded"] - cat["oop"]) > 0.02 * cat["oop"]:
        problems.append(f"Catastrophic deductible {cat['ded']} not ~= OOP max {cat['oop']}")

    if not us["Silver"]["ded"] > 1.2 * us["Gold"]["ded"]:
        problems.append(f"Silver deductible {us['Silver']['ded']} not >> Gold "
                        f"{us['Gold']['ded']} — CSR variants may have leaked in")

    for state, tier, d, o, c in table:
        if d in (None, 0) and tier != "Platinum":   # Platinum ~$0 deductibles are real
            problems.append(f"{state} {tier} deductible missing/zero: {d}")
        if o in (None, 0):                           # OOP max should never be 0
            problems.append(f"{state} {tier} OOP max missing/zero: {o}")
        if (c is None or c == 0) and tier != "Catastrophic":  # cat copay No Charge/coins ok
            problems.append(f"{state} {tier} copay missing/zero: {c}")

    if problems:
        print("\nSANITY CHECKS FAILED:")
        for p in problems:
            print("  - " + p)
        sys.exit(1)
    print("\nSanity checks passed: deductibles monotonic, Catastrophic ded=OOP, "
          "Silver >> Gold (no CSR leak), no undocumented zero/missing cells.")


def main():
    plan_zip = _find("*plan-attributes*puf*.zip")
    benefits_zip = _find("*benefits*cost*sharing*puf*.zip")
    print(f"Plan Attributes PUF: {os.path.basename(plan_zip)}")
    print(f"Benefits PUF:        {os.path.basename(benefits_zip)}")

    with tempfile.TemporaryDirectory() as tmp:
        plan_csv = _extract(plan_zip, "Plan_Attributes_PUF.csv", tmp)
        base, counts, folded = load_base_plans(plan_csv)

        print("\nPlan Attributes filtering:")
        print(f"  start                         {counts['start']:6d}")
        print(f"  - dental-only excluded        {counts['f1_dental']:6d}")
        print(f"  - non-on-exchange excluded     {counts['f2_exchange']:6d}")
        print(f"  - wrong benefit year excluded  {counts['f3_year']:6d}")
        print(f"  - CSR/off-exchange excluded   {counts['f4_csr']:6d}")
        print(f"  - metal level excluded         {counts['f5_metal']:6d}")
        print(f"  = base plans kept             {len(base):6d}  "
              f"(Expanded Bronze folded into Bronze: {folded})")

        benefits_csv = _extract(benefits_zip, "Benefits_Cost_Sharing_PUF.csv", tmp)
        copay_raw = load_primary_care_copay(benefits_csv, {r["plan_id"] for r in base})

    matched = sum(1 for r in base if r["plan_id"] in copay_raw)
    print(f"\nPrimary care copay join: {matched}/{len(base)} base plans matched "
          f"({100 * matched / len(base):.1f}%)")

    # Attach parsed copay; count per-field drops.
    n = len(base)
    ded_missing = oop_missing = copay_excluded = 0
    for r in base:
        if r["ded"] is None:
            ded_missing += 1
        if r["oop"] is None:
            oop_missing += 1
        usable, amount = parse_copay(copay_raw.get(r["plan_id"]))
        r["copay"] = amount if usable else None
        if not usable:
            copay_excluded += 1
    print("\nPer-field drop share (of base plans):")
    print(f"  deductible missing : {ded_missing:5d} ({100 * ded_missing / n:.2f}%)")
    print(f"  OOP max missing    : {oop_missing:5d} ({100 * oop_missing / n:.2f}%)")
    print(f"  copay excluded     : {copay_excluded:5d} ({100 * copay_excluded / n:.2f}%)  "
          "(coinsurance-only / Not Applicable)")

    # Aggregate: simple mean by state x tier, plus a pooled United States row
    # (mean across ALL plans nationally, NOT the mean of state means).
    groups = defaultdict(list)
    for r in base:
        groups[(r["state"], r["tier"])].append(r)
        groups[("United States", r["tier"])].append(r)

    states = sorted({r["state"] for r in base})
    out_rows = []
    for state in ["United States"] + states:
        for tier in TIER_ORDER:
            items = groups.get((state, tier))
            if not items:
                continue
            out_rows.append([
                state, tier,
                mean_or_blank(x["ded"] for x in items),
                mean_or_blank(x["oop"] for x in items),
                mean_or_blank(x["copay"] for x in items),
            ])

    us = {tier: {"ded": ded, "oop": oop, "copay": copay}
          for state, tier, ded, oop, copay in out_rows if state == "United States"}
    validate(us, out_rows)

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["State", "MetalTier", "AvgDeductible", "AvgOOPMax", "AvgPrimaryCareCopay"])
        for state, tier, ded, oop, copay in out_rows:
            w.writerow([state, tier,
                        "" if ded is None else ded,
                        "" if oop is None else oop,
                        "" if copay is None else copay])

    print(f"\nWrote {OUT_CSV}: {len(out_rows)} rows, "
          f"{len(states)} states + United States, tiers {TIER_ORDER}")


if __name__ == "__main__":
    main()
