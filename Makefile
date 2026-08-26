# Enrollment Tracker — build entry points.
# See CLAUDE.md for the full monthly/yearly procedure and data caveats.

.PHONY: help install update dashboard medicare cost-sharing verify

help:
	@echo "Enrollment Tracker — make targets"
	@echo
	@echo "  make install       Install pinned Python deps (first time only)"
	@echo "  make update        MONTHLY: rebuild the dashboard from the workbook + reminders"
	@echo "  make dashboard     Rebuild index.html only (what 'update' runs)"
	@echo "  make verify        Rebuild and fail if committed index.html is stale (what CI runs)"
	@echo
	@echo "  make medicare      On a new Medicare drop: merge source-data CSV+zip -> data/medicare.json"
	@echo "  make cost-sharing  Yearly, on a new benefit-year PUF: rebuild data/cost_sharing.csv"

install:
	pip install -r requirements.txt

# ── Monthly path ──────────────────────────────────────────────────────────────
# Drop the refreshed data/Enrollment_Tracker.xlsx first. build_dashboard.py reads
# data/medicare.json and data/cost_sharing.csv but does NOT regenerate them — run
# `make medicare` / `make cost-sharing` first if those sources also changed.
update: dashboard
	@echo
	@echo "✓ index.html rebuilt. Reminders before committing:"
	@echo "  • New CMS snapshot PDF? add it to source-data/cms-snapshots/ and update data/cms_data_notes.md,"
	@echo "    then surface any newly-active state caveat on the dashboard (see CLAUDE.md)."
	@echo "  • New Medicare monthly drop in source-data/? run 'make medicare' BEFORE this, then rebuild."
	@echo "  • New ACA benefit year? run 'make cost-sharing' (yearly only)."
	@echo "  • Open index.html, click through every tab + a few state toggles, then commit & push."

dashboard:
	python build_dashboard.py

verify: dashboard
	@git diff --exit-code --stat index.html README.md \
	  || { echo "ERROR: index.html/README.md is out of date — commit the rebuilt files."; exit 1; }

# ── Occasional sources (not part of the monthly rebuild) ──────────────────────
medicare:
	python build_medicare.py

cost-sharing:
	python build_cost_sharing.py
