# Wholesale2Flip – Fixed Website (Streamlit Single-File)

This is the **new fixed version** ready for **GitHub** and **Streamlit Cloud**.

## Features
- Auth with demo roles (admin/demo/wholesaler/investor)
- Landing + Dashboard + Deal Analyzer (ARV, MAO 70/75, Rehab, Profit, Cap Rate)
- Lead Manager (CRM with scoring + sources + notes)
- Deal Pipeline (stages + deal list)
- Buyer Network (verified buyers, cash available, areas, preferences)
- Contract & LOI generators (download .txt)
- RVM Campaigns (cost calc at $0.15/msg, response rate 15–20% sim)
- Analytics charts (leads, spend)
- SQLite persistence (wtf.db created on first run)
- Mobile-responsive Streamlit layout

## Run Locally
```bash
pip install -r requirements.txt
streamlit run wtf_app_fixed.py
```

Login with any of:
- Admin: `admin` / `admin123`
- Demo: `demo` / `demo`
- Wholesaler: `wholesaler` / `demo123`
- Investor: `investor` / `invest123`

## Deploy to GitHub + Streamlit Cloud
1. **Push these files to a repo** (at minimum):
   - `wtf_app_fixed.py`
   - `requirements.txt`
   - `.streamlit/config.toml` (optional theming)
2. On **Streamlit Cloud**:
   - Click *New app* → choose your repo
   - Set **Main file path** to `wtf_app_fixed.py`
   - Deploy
3. (Optional) Add Streamlit *Secrets* if you later use APIs. See `wtf_secrets_example.toml`.

## Data & Demo
- Analyzer seeded with: **21372 W Memorial Dr, Porter, TX** (Owner: EDGAR LORI G; Value $267,000; 1,643 sqft; 3/2; 1969; Rent $1,973; Mortgage $27,986; Equity $239,014; Taxes $1,497).
- `wtf.db` is created in the working directory automatically.

## Notes
- This is a single-file app for simplicity. You can later split into pages.
- LOI/Contract export is plain text; e-sign simulation allowed. If you want a PDF exporter, I can add it.
