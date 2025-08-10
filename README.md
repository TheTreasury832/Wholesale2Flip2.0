# WTF — Wholesale on Steroids (Streamlit)

A complete, professional real estate wholesaling platform built in **Python + Streamlit**.

## Demo Auth
- **admin / admin123**
- **demo / demo**
- **wholesaler / demo123**
- **investor / invest123**

## Features
- Landing page with gradient branding and pricing
- Dashboard with KPI cards and quick actions
- **Deal Analyzer** with ARV, MAO (70/75), rehab, profit, grading
- **Lead Manager (CRM)** with scoring & statuses
- **Deal Pipeline** with stages and simple forecasting
- **Buyer Network** (verified buyers, cash, buy box, matches)
- **Contract Generator** & **LOI Generator** (auto text + download)
- **RVM Campaigns** (wizard with cost calc; ready for Twilio integration)
- **Analytics** (Plotly charts for deals/leads/campaigns)

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push this folder to GitHub.
2. Create a Streamlit Cloud app pointing to `app.py` on main branch.
3. Add secrets later for Whop, Twilio, OpenAI, etc.

## Roadmap (next steps)
- Whop OAuth subscription login
- Postgres persistence for users/leads/deals/buyers
- Twilio RVM/SMS, SendGrid email offers
- OpenAI Underwriter + Script GPT modules
- PDF contracts + e-signature (DocuSign/HelloSign)