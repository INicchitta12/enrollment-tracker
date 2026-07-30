#!/usr/bin/env python3
"""
Build the Enrollment Tracker dashboard.

Reads the source workbook, injects all data into template.html,
and writes index.html for GitHub Pages.

Usage:  python build_dashboard.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
WORKBOOK = ROOT / "data" / "Enrollment_Tracker.xlsx"
PDF_HISTORY = ROOT / "data" / "pdf_history.json"
TEMPLATE = ROOT / "template.html"
OUTPUT = ROOT / "index.html"

# Marketplace tabs: "Marketplace (2)" supersedes "Marketplace"
MKT_SHEET = "Marketplace (2)"

STATE_ABBR = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
    'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
    'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
    'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan',
    'MN': 'Minnesota', 'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana',
    'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire', 'NJ': 'New Jersey',
    'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
    'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania',
    'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee',
    'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington',
    'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming',
}

MCAID_COLS = {
    'enroll': 'Total Medicaid Enrollment',
    'adult': 'Total Medicaid Adult Enrollment',
    'due': 'Beneficiaries with a Renewal Due',
    'renewed': 'Beneficiaries Whose Coverage Was Renewed (Total)',
    'exparte': 'Beneficiaries Whose Coverage Was Renewed on an Ex Parte Basis',
    'form': 'Beneficiaries Whose Coverage Was Renewed based on a Renewal Form',
    'disenrolled': 'Beneficiaries Disenrolled at Renewal (Total)',
    'ineligible': 'Beneficiaries Determined Ineligible at Renewal',
    'procedural': 'Beneficiaries Disenrolled for Procedural Reasons at Renewal',
    'pending': 'Beneficiaries with a Pending Renewal',
}

# California revised its Medicaid reporting in March 2026 to exclude
# limited-benefit enrollees and did not restate prior months, which makes March
# onward non-comparable to earlier months and inflates the apparent national
# decline. We apply a continuity adjustment: California's average monthly
# enrollment change over Dec 2025-Feb 2026 was -106,996 total and -78,132 adult;
# treating that as the expected March change and attributing the excess decline
# to the reclassification gives the add-backs below (expected March value minus
# the value California actually reported). These are estimates, not CMS figures.
# The revision is permanent, so the adjustment applies to March 2026 and every
# later month. Enrollment counts only -- renewal fields are never touched.
CA_ADJUST_FROM = '2026-03'
CA_ENROLL_ADJUST = 384186
CA_ADULT_ADJUST = 372782

MKT_COLS = {
    'total': 'Number of Consumers with an Exchange Plan Selection',
    'new': 'New Consumers', 'reenroll': 'Total Re-enrollees',
    'active': 'Active Re-enrollees', 'auto': 'Automatic Re-enrollees',
    'aptc': 'Consumers with APTC', 'avgPrem': 'Average Premium  ',
    'avgNet': 'Average Premium after APTC  ', 'cat': 'Catastrophic',
    'bronze': 'Bronze', 'silver': 'Silver ', 'gold': 'Gold', 'platinum': 'Platinum',
}

# The national (United States) post-OEP Marketplace series is limited to reported
# effectuated months. CMS reported national effectuated totals only through
# February 2026: the workbook has no March figure, and the April value
# (19,200,000) is a rounded placeholder, not a reported count. Publishing them
# would render a misleading isolated dot on the national trend line, so we
# explicitly exclude March 2026 onward for the United States series only. State
# series are unaffected — 12 states report genuine March, April, and May figures.
NATIONAL_POST_OEP_EXCLUDE_FROM = pd.Timestamp('2026-03-01')


def to_int(v):
    return None if pd.isna(v) else int(v)


def normalize_dc(name):
    return 'District of Columbia' if name.strip().lower() == 'district of columbia' else name.strip()


def mix_percentages(rec):
    """Five renewal outcomes as percentages of renewals due, rescaled to sum to exactly 100."""
    parts = [rec['exparte'], rec['form'], rec['ineligible'], rec['procedural'], rec['pending']]
    pcts = [p / rec['due'] * 100 for p in parts]
    total = sum(pcts)
    return [round(p / total * 100, 1) for p in pcts]


def apply_california_adjustment(periods, national, states):
    """Continuity add-back for California's March 2026 reporting revision.

    Adjusts California's own enrollment counts from CA_ADJUST_FROM onward, then
    re-derives the national enrollment counts from state totals so the national
    row stays the exact sum of states. Renewal fields are left untouched. Raises
    if the national == sum-of-states identity does not hold on the raw data.
    """
    def sum_states(key, field):
        return sum(s[key][field] for s in states.values()
                   if key in s and s[key][field] is not None)

    for key in periods:
        for field in ('enroll', 'adult'):
            if national[key][field] != sum_states(key, field):
                sys.exit(f"ERROR: national {field} != sum of states at {key}; "
                         "cannot re-derive national after California adjustment")

    ca = states.get('California', {})
    for key in periods:
        if key >= CA_ADJUST_FROM and key in ca:
            ca[key]['enroll'] += CA_ENROLL_ADJUST
            ca[key]['adult'] += CA_ADULT_ADJUST
            national[key]['enroll'] = sum_states(key, 'enroll')
            national[key]['adult'] = sum_states(key, 'adult')


def load_medicaid(xl):
    df = pd.read_excel(xl, sheet_name="Mcaid")
    df['State'] = df['State'].astype(str).map(normalize_dc)
    df['P'] = pd.to_datetime(df['Reporting Period'])
    df['key'] = df['P'].dt.strftime('%Y-%m')

    periods = sorted(df['key'].unique())
    labels = [pd.Timestamp(p + '-01').strftime('%b %Y') for p in periods]

    states, national = {}, {}
    for _, row in df.iterrows():
        rec = {k: to_int(row[c]) for k, c in MCAID_COLS.items()}
        if row['State'] == 'United States':
            national[row['key']] = rec
        else:
            states.setdefault(row['State'], {})[row['key']] = rec

    apply_california_adjustment(periods, national, states)

    # Top 12 states by disenrollment rate in the most recent month
    latest = periods[-1]
    recent = df[(df['key'] == latest) & (df['State'] != 'United States')].copy()
    recent['rate'] = recent[MCAID_COLS['disenrolled']] / recent[MCAID_COLS['due']]
    top = recent.nlargest(12, 'rate')
    top12 = {
        'labels': list(top['State']),
        'rates': [round(r * 100, 1) for r in top['rate']],
        'disen': [int(v) for v in top[MCAID_COLS['disenrolled']]],
        'due': [int(v) for v in top[MCAID_COLS['due']]],
    }
    return periods, labels, latest, national, states, top12


def build_mix(periods, labels, national, states):
    """Renewal outcome mix. National blends PDF history (Mar-Nov 2025) with workbook data."""
    hist = json.loads(PDF_HISTORY.read_text())
    keys = ['exparte', 'form', 'inelig', 'proc', 'pend']

    nat = {k: list(hist[k]) for k in keys}
    nat_labels = list(hist['labels'])
    for p, lab in zip(periods, labels):
        e, f, i, pr, pe = mix_percentages(national[p])
        nat_labels.append(lab)
        for k, v in zip(keys, [e, f, i, pr, pe]):
            nat[k].append(v)
    nat['labels'] = nat_labels

    st = {}
    for name, by_period in states.items():
        series = {k: [] for k in keys}
        for p in periods:
            rec = by_period.get(p)
            vals = mix_percentages(rec) if rec else [None] * 5
            for k, v in zip(keys, vals):
                series[k].append(v)
        st[name] = series

    return {'natLabels': nat_labels, 'nat': nat, 'stLabels': labels, 'states': st}


def load_marketplace(xl):
    df = pd.read_excel(xl, sheet_name=MKT_SHEET)
    df['State'] = df['State'].astype(str).map(normalize_dc)
    for col in MKT_COLS.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')

    oep_rows = df[df['Reporting Period'] == 'OEP']
    oep, national_oep = {}, None
    for _, row in oep_rows.iterrows():
        rec = {k: (0 if pd.isna(row[c]) else int(row[c])) for k, c in MKT_COLS.items()}
        rec['plat'] = rec.pop('platinum')
        if row['State'] == 'United States':
            national_oep = rec
        elif rec['total'] > 0:
            oep[row['State']] = rec

    dated = df[df['Reporting Period'] != 'OEP'].copy()
    dated['P'] = pd.to_datetime(dated['Reporting Period'])
    months = sorted(dated['P'].unique())
    labels = ['OEP'] + [pd.Timestamp(m).strftime('%b') for m in months]

    series = {}
    for name in list(oep) + ['United States']:
        sub = dated[dated['State'] == name].set_index('P')
        base = national_oep if name == 'United States' else oep[name]
        vals = [base['total']]
        for m in months:
            # National post-OEP data is limited to reported months (through Feb 2026);
            # exclude the missing/placeholder March-onward values for United States only.
            if name == 'United States' and pd.Timestamp(m) >= NATIONAL_POST_OEP_EXCLUDE_FROM:
                vals.append(None)
            else:
                vals.append(to_int(sub.loc[m, MKT_COLS['total']]) if m in sub.index else None)
        if any(v is not None for v in vals[1:]):
            series[name] = vals

    return oep, national_oep, labels, series


def load_effectuated(xl):
    df = pd.read_excel(xl, sheet_name="Marketplace Feb. Effec. Enroll")
    df['S'] = df['State'].astype(str).str.strip().map(
        lambda s: 'United States' if s == 'United States' else STATE_ABBR.get(s, s))
    df['E'] = pd.to_numeric(df['Effectuated Enrollment'], errors='coerce')

    out = {}
    for name, group in df.groupby('S'):
        vals = {f"{int(r['Year'])}-{r['Month'][:3]}": to_int(r['E']) for _, r in group.iterrows()}
        out[name] = {'jan25': vals.get('2025-Jan'), 'feb25': vals.get('2025-Feb'),
                     'jan26': vals.get('2026-Jan'), 'feb26': vals.get('2026-Feb')}
    return out


def load_bhp(xl):
    df = pd.read_excel(xl, sheet_name="BHP")
    df['State'] = df['State'].astype(str).map(normalize_dc)
    df['P'] = pd.to_datetime(df['Reporting Period'])
    df['v'] = pd.to_numeric(df['BHP Enrollment'], errors='coerce')

    months = sorted(df['P'].unique())
    labels = [pd.Timestamp(m).strftime('%b %Y') for m in months]
    series = {}
    for name, group in df[df['State'] != 'United States'].groupby('State'):
        g = group.set_index('P')
        series[name] = [to_int(g.loc[m, 'v']) if m in g.index else None for m in months]
    return labels, series


def state_pills(prefix, fn, names):
    out = [f'<button class="state-pill active" onclick="{fn}(null)" id="{prefix}-btn-national">National</button>']
    for s in sorted(names):
        sid = s.replace(' ', '-').replace('.', '')
        out.append(f'<button class="state-pill" onclick="{fn}(\'{s}\')" id="{prefix}-btn-{sid}">{s}</button>')
    return '\n      '.join(out)


def main():
    if not WORKBOOK.exists():
        sys.exit(f"ERROR: workbook not found at {WORKBOOK}")

    xl = pd.ExcelFile(WORKBOOK)
    periods, labels, latest, mc_nat, mc_states, top12 = load_medicaid(xl)
    mix = build_mix(periods, labels, mc_nat, mc_states)
    mkt_oep, mkt_nat, post_labels, post_series = load_marketplace(xl)
    yoy = load_effectuated(xl)
    bhp_labels, bhp_series = load_bhp(xl)

    compact = lambda o: json.dumps(o, separators=(',', ':'))
    replacements = {
        'MCAID_PILLS': state_pills('mcaid', 'selectMcaidState', mc_states),
        'MKT_PILLS': state_pills('mkt', 'selectMktState', mkt_oep),
        '__MCAID_PERIODS__': compact(periods),
        '__MCAID_LABELS__': compact(labels),
        '__MCAID_LATEST__': compact(latest),
        '__MCAID_NAT__': compact(mc_nat),
        '__MCAID_STATES__': compact(mc_states),
        '__TOP12__': compact(top12),
        '__MIX__': compact(mix),
        '__MKT_OEP__': compact(mkt_oep),
        '__MKT_NAT_OEP__': compact(mkt_nat),
        '__POST_LABELS__': compact(post_labels),
        '__POST_OEP__': compact(post_series),
        '__YOY__': compact(yoy),
        '__BHP_LABELS__': compact(bhp_labels),
        '__BHP_SERIES__': compact(bhp_series),
    }

    html = TEMPLATE.read_text()
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    leftover = [p for p in replacements if p in html]
    if leftover:
        sys.exit(f"ERROR: unsubstituted placeholders: {leftover}")

    OUTPUT.write_text(html)

    print(f"Built {OUTPUT.name}  ({len(html) // 1024} KB)")
    print(f"  Medicaid    {labels[0]} - {labels[-1]}  ({len(mc_states)} states)")
    print(f"  BHP         {bhp_labels[0]} - {bhp_labels[-1]}  ({len(bhp_series)} states)")
    print(f"  Marketplace OEP + {len(post_labels) - 1} months  ({len(mkt_oep)} states)")
    print(f"  Outcome mix {mix['natLabels'][0]} - {mix['natLabels'][-1]} national, "
          f"{mix['stLabels'][0]} - {mix['stLabels'][-1]} by state")


if __name__ == "__main__":
    main()
