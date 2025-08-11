# Wholesale2Flip (WTF) Platform - Export 2025-08-11T18:24:44

This bundle contains all project files you uploaded/asked for, plus this README and a CSV manifest.

## Quick Start (local)
1) Create a virtualenv (recommended) and install deps:
   pip install -r requirements_final.txt || pip install -r requirements.txt

2) Run the Streamlit app (pick one of the complete builds):
   streamlit run wtf_ultimate_complete.py
   # or:
   streamlit run wtf_complete_platform.py
   streamlit run wtf_complete_working.py

3) Default credentials (for demos):
   - Admin: admin / admin123
   - Demo: demo / demo
   - Wholesaler: wholesaler / demo123
   - Investor: investor / invest123

4) Sample property (for analyzers):
   21372 W Memorial Dr, Porter, TX
   (Owner: EDGAR LORI G; Value: $267,000; 1,643 sqft; 3/2; 1969; Rent: $1,973; Mortgage: $27,986; Equity: $239,014; Taxes: $1,497)

## Files
See `wtf_platform_manifest.csv` for the full list with sizes and hashes.

Tip: Some variants are alternatives of the full app. Preferred entry points:
- wtf_ultimate_complete.py  (most polished)
- wtf_live_platform.py      (live-data schema)
- wtf_app_complete.py       (compact complete app)

