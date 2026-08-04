#!/usr/bin/env python3
"""
Aggregate the CMS Medicare Monthly Enrollment file into data/medicare.json.

Reads the raw CMS CSV straight from its zip in source-data/ (the extracted CSV
is far too large for the repo and is gitignored) and writes a small per-state
monthly summary that build_dashboard.py injects. build_dashboard.py never reads
the raw source — it reads only data/medicare.json. Rerun this only when CMS
publishes a refreshed Medicare Monthly Enrollment file (a new zip).

    python build_medicare.py

Key decisions (see the Medicare section of CLAUDE.md):

  * One file, three geography levels + annual roll-ups. The CSV interleaves
    National / State / County rows AND annual `MONTH == "Year"` rows. We keep
    STATE-level, MONTHLY rows only (BENE_COUNTY_DESC == "Total", month is a real
    month), and build the national total ourselves as the sum of the 50 states
    + DC. Summing naively across levels would double- or triple-count.

  * The CMS "National" row INCLUDES territories, so we do NOT use it. Beyond
    50+DC the State level also carries Puerto Rico, Guam, the Virgin Islands,
    American Samoa, the Northern Mariana Islands, and "Foreign and Other Outlying
    Areas" (~1.4M people); the CMS National row is their sum WITH those. The
    dashboard covers 50 states + DC, so territories are excluded and the national
    series is rebuilt from the 50+DC rows to match that scope. (Consequence: this
    national total runs ~1.4M below CMS's published national — disclosed on the
    tab.)

  * Suppressed cells are the literal "*". Suppression is heavy at county level
    (~11%) but the fields kept here are never suppressed for any of the 50 states
    + DC in any month (verified). We still fail loudly if that ever changes,
    rather than silently summing around a hole and undercounting.

  * Reconciliation holds exactly in the source: Original + MA == Total,
    Aged + Disabled == Total, and PDP + MAPD == Part D, per state and per month.
    We re-check the rebuilt national totals and abort on any mismatch.
"""

import io
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE_ZIP = ROOT / "source-data" / "Medicare_Monthly_Data.zip"
CSV_NAME = "Medicare_Monthly_Data.csv"
OUTPUT = ROOT / "data" / "medicare.json"

MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
    "July": 7, "August": 8, "September": 9, "October": 10, "November": 11,
    "December": 12,
}
MONTH_ABBR = {v: k[:3] for k, v in MONTHS.items()}

# Non-state areas carried at "State" level that are excluded from the 50+DC scope.
TERRITORIES = {
    "American Samoa", "Guam", "Northern Mariana Islands", "Puerto Rico",
    "Virgin Islands", "Foreign and Other Outlying Areas",
}

# Source column -> compact key kept in medicare.json. Only these are read; every
# other column (demographics, race, age bands, Part A/B detail, dual subtypes,
# LIS tiers) is dropped to keep the injected file small.
FIELDS = {
    "tot": "TOT_BENES",              # Total Medicare
    "org": "ORGNL_MDCR_BENES",       # Original / Traditional Medicare
    "ma": "MA_AND_OTH_BENES",        # Medicare Advantage & other health plans
    "abtot": "A_B_TOT_BENES",        # beneficiaries with BOTH Part A and Part B
    "aged": "AGED_TOT_BENES",        # entitled by age
    "dsbld": "DSBLD_TOT_BENES",      # entitled by disability
    "dual": "DUAL_TOT_BENES",        # Medicare-Medicaid dual eligibles
    "partd": "PRSCRPTN_DRUG_TOT_BENES",  # any Part D
    "pdp": "PRSCRPTN_DRUG_PDP_BENES",    # standalone drug plan
    "mapd": "PRSCRPTN_DRUG_MAPD_BENES",  # MA prescription-drug plan
}

EXPECTED_STATES = 51  # 50 states + DC


def num(cell):
    """Parse a count cell; '*' (suppressed) and blank return None."""
    s = cell.strip()
    if s in ("*", ""):
        return None
    return int(s.replace(",", ""))


def read_rows():
    if not SOURCE_ZIP.exists():
        sys.exit(f"ERROR: Medicare source zip not found at {SOURCE_ZIP}")
    import csv
    with zipfile.ZipFile(SOURCE_ZIP) as z:
        name = CSV_NAME if CSV_NAME in z.namelist() else z.namelist()[0]
        with z.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8-sig")
            yield from csv.DictReader(text)


def main():
    states = {}            # stateName -> {period: {key: int}}
    seen = {}              # period -> set(stateName) for completeness check

    for row in read_rows():
        month = row["MONTH"]
        if month not in MONTHS:                       # skip annual "Year" rows
            continue
        if row["BENE_COUNTY_DESC"].strip() != "Total":  # skip county rows
            continue
        st = row["BENE_STATE_DESC"].strip()
        if st == "National" or st in TERRITORIES:     # skip CMS national + territories
            continue

        period = f"{int(row['YEAR'])}-{MONTHS[month]:02d}"
        rec = {}
        for key, col in FIELDS.items():
            v = num(row[col])
            if v is None:
                sys.exit(f"ERROR: {col} suppressed for {st} {period}; a kept "
                         "field is masked for a 50+DC state — investigate before "
                         "building (do not sum around it).")
            rec[key] = v
        # Per-state reconciliation — the identities the dashboard relies on.
        if rec["org"] + rec["ma"] != rec["tot"]:
            sys.exit(f"ERROR: Original+MA != Total for {st} {period}")
        if rec["aged"] + rec["dsbld"] != rec["tot"]:
            sys.exit(f"ERROR: Aged+Disabled != Total for {st} {period}")
        if rec["pdp"] + rec["mapd"] != rec["partd"]:
            sys.exit(f"ERROR: PDP+MAPD != Part D for {st} {period}")
        # A&B is the MA-penetration denominator (must have both parts to enroll in
        # MA), so it must be a positive subset of the total.
        if not 0 < rec["abtot"] <= rec["tot"]:
            sys.exit(f"ERROR: A_B_TOT out of range for {st} {period}")

        states.setdefault(st, {})[period] = rec
        seen.setdefault(period, set()).add(st)

    periods = sorted(seen)
    if not periods:
        sys.exit("ERROR: no Medicare state-month rows found")

    # Every month must carry the full 50+DC panel, or the national sum is short a
    # state. (Verified {51} across the current file; guard against a partial drop.)
    for p in periods:
        if len(seen[p]) != EXPECTED_STATES:
            sys.exit(f"ERROR: {p} has {len(seen[p])} states+DC, expected "
                     f"{EXPECTED_STATES}; national sum would be incomplete")

    # National = exact sum of the 50 states + DC (NOT the CMS National row).
    national = {}
    for p in periods:
        agg = {k: 0 for k in FIELDS}
        for st in states:
            rec = states[st].get(p)
            if rec:
                for k in FIELDS:
                    agg[k] += rec[k]
        national[p] = agg

    # Re-check reconciliation on the rebuilt national totals.
    for p in periods:
        n = national[p]
        assert n["org"] + n["ma"] == n["tot"], f"national Original+MA != Total {p}"
        assert n["aged"] + n["dsbld"] == n["tot"], f"national Aged+Disabled != Total {p}"
        assert n["pdp"] + n["mapd"] == n["partd"], f"national PDP+MAPD != Part D {p}"

    labels = [f"{MONTH_ABBR[int(p[5:7])]} {p[:4]}" for p in periods]
    out = {
        "periods": periods,
        "labels": labels,
        "latest": periods[-1],
        "national": national,
        "states": states,
    }
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(json.dumps(out, separators=(",", ":")))

    latest, first = periods[-1], periods[0]
    n_now, n_then = national[latest], national[first]
    size_kb = OUTPUT.stat().st_size // 1024
    print(f"Wrote {OUTPUT.relative_to(ROOT)}  ({size_kb} KB)")
    print(f"  {len(states)} states + DC (territories excluded)  ·  "
          f"{labels[0]} – {labels[-1]}  ({len(periods)} months)")
    print(f"  National {labels[-1]}: total {n_now['tot']:,}  ·  "
          f"MA penetration {n_now['ma'] / n_now['abtot'] * 100:.1f}% (of A&B)  ·  "
          f"dual {n_now['dual'] / n_now['tot'] * 100:.1f}%  ·  "
          f"Part D {n_now['partd'] / n_now['tot'] * 100:.1f}%")
    print(f"  MA penetration (MA / Part A&B) {labels[0]} {n_then['ma'] / n_then['abtot'] * 100:.1f}%"
          f"  ->  {labels[-1]} {n_now['ma'] / n_now['abtot'] * 100:.1f}%")


if __name__ == "__main__":
    main()
