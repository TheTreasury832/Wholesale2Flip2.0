
"""
WTF (Wholesale2Flip) — Incremental Upgrades (Patched)
- Plotly now optional (graceful fallback to bar_chart if not installed)
- Google Sheets importer updated to use google.oauth2.service_account (no oauth2client)
- Adds Streamlit server file watcher guidance via config.toml (see supplied config)
"""
import os, io, json, uuid, math, sqlite3, datetime as dt
from pathlib import Path
from typing import Dict, Optional

import streamlit as st
import pandas as pd

# Try Plotly (optional). If missing, we fallback to st.bar_chart.
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

# Optional PDF libs (graceful fallback to .txt if missing)
try:
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas as rl_canvas
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_OK = True
except Exception:
    PYPDF2_OK = False

st.set_page_config(page_title="WTF — Wholesale2Flip", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

THEME = {"primary": "#8B5CF6", "bg": "#0a0a0a", "bg2": "#1a1a2e", "text": "#ffffff"}
st.markdown(f"""
<style>
    .stApp {{ background: linear-gradient(135deg, {THEME['bg']} 0%, {THEME['bg2']} 50%, #16213e 100%); }}
    .main-header {{
        background: linear-gradient(90deg, #8B5CF6 0%, #10B981 30%, #3B82F6 60%, #F59E0B 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-size: 2.4rem; font-weight: 900; text-align: center; margin: .75rem 0 1.25rem;
    }}
    .metric-card {{ background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.35); border-radius: 14px; padding: 1rem; }}
    .kanban-col {{ background: rgba(255,255,255,.06); border: 1px solid rgba(255,255,255,.12); border-radius: 12px; padding: .75rem; min-height: 220px; }}
    .deal-card {{ background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.15); border-radius: 12px; padding: .75rem; margin-bottom: .5rem; }}
    .stButton > button {{ background: linear-gradient(90deg, #8B5CF6, #10B981); color: #fff; border: none; border-radius: 10px; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)

DB_PATH = os.environ.get("WTF_DB", "wtf_platform.db")
KANBAN_STAGES = ["Prospecting","Negotiating","Under Contract","Due Diligence","Closed"]

def db(): return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with db() as conn:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY, address TEXT, city TEXT, state TEXT, zip_code TEXT,
            property_type TEXT, bedrooms INTEGER, bathrooms REAL, square_feet INTEGER,
            year_built INTEGER, list_price REAL, arv REAL DEFAULT 0, rehab_cost REAL DEFAULT 0,
            max_offer REAL DEFAULT 0, profit_potential REAL DEFAULT 0, condition TEXT DEFAULT 'fair',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY, first_name TEXT, last_name TEXT, phone TEXT, email TEXT,
            property_address TEXT, motivation TEXT, timeline TEXT, source TEXT,
            status TEXT DEFAULT 'new', score INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS buyers (
            id TEXT PRIMARY KEY, name TEXT, email TEXT, phone TEXT,
            property_types TEXT, min_price REAL, max_price REAL, states TEXT, cities TEXT, deal_types TEXT,
            verified BOOLEAN DEFAULT 0, proof_of_funds BOOLEAN DEFAULT 0, cash_available REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS deals (
            id TEXT PRIMARY KEY, title TEXT, property_id TEXT, buyer_id TEXT, lead_id TEXT,
            purchase_price REAL, assignment_fee REAL, status TEXT DEFAULT 'lead',
            stage TEXT DEFAULT 'Prospecting', probability INTEGER DEFAULT 10,
            contract_date TIMESTAMP, closing_date TIMESTAMP, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS contracts (
            id TEXT PRIMARY KEY, deal_id TEXT, contract_type TEXT, purchase_price REAL, earnest_money REAL,
            closing_date TIMESTAMP, buyer_name TEXT, seller_name TEXT, property_address TEXT, state TEXT,
            status TEXT DEFAULT 'draft', pdf_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        c.execute("""CREATE TABLE IF NOT EXISTS lois (
            id TEXT PRIMARY KEY, lead_id TEXT, property_address TEXT, offer_price REAL, state TEXT, terms TEXT,
            status TEXT DEFAULT 'draft', pdf_path TEXT, sent_date TIMESTAMP, response_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
        conn.commit()

def list_deals():
    with db() as conn:
        return pd.read_sql_query("SELECT * FROM deals ORDER BY created_at DESC", conn)

def update_deal_stage(deal_id, stage):
    with db() as conn:
        conn.execute("UPDATE deals SET stage=? WHERE id=?", (stage, deal_id)); conn.commit()

def create_dummy_deals():
    df = list_deals()
    if df.empty:
        with db() as conn:
            conn.execute("INSERT INTO deals (id,title,stage,purchase_price,assignment_fee,probability,status) VALUES (?,?,?,?,?,?,?)",
                         (uuid.uuid4().hex,"123 Main St, Dallas TX","Prospecting",165000,12000,35,"lead"))
            conn.execute("INSERT INTO deals (id,title,stage,purchase_price,assignment_fee,probability,status) VALUES (?,?,?,?,?,?,?)",
                         (uuid.uuid4().hex,"456 Oak Ave, Houston TX","Negotiating",210000,15000,55,"active"))
            conn.commit()

def buyers_df():
    with db() as conn:
        return pd.read_sql_query("SELECT * FROM buyers ORDER BY created_at DESC", conn)

def upsert_buyer(row: Dict):
    row = row.copy()
    row["id"] = row.get("id") or uuid.uuid4().hex
    for k in ["states","cities","property_types","deal_types"]:
        v = row.get(k,"")
        if isinstance(v, list): row[k] = ",".join([str(x).strip() for x in v if str(x).strip()])
    cols = ["id","name","email","phone","property_types","min_price","max_price","states","cities","deal_types","verified","proof_of_funds","cash_available"]
    vals = [row.get(c) for c in cols]
    with db() as conn:
        conn.execute(f"INSERT OR REPLACE INTO buyers ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})", vals)
        conn.commit()

def match_buyers(city, state, price):
    df = buyers_df()
    if df.empty: return df
    def ok_states(s): return state.upper() in str(s).upper().split(",") if pd.notna(s) else False
    def ok_cities(s):
        if pd.isna(s) or not str(s).strip(): return True
        return city.upper() in [t.strip().upper() for t in str(s).split(",")]
    m = df[df["states"].apply(ok_states) & df["cities"].apply(ok_cities)]
    m = m[(m["min_price"].fillna(0) <= price) & (price <= m["max_price"].fillna(10**9))]
    return m.sort_values(["verified","cash_available"], ascending=[False,False])

# PDF helpers
def _write_text_pdf(lines, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if REPORTLAB_OK and str(out_path).lower().endswith(".pdf"):
        c = rl_canvas.Canvas(str(out_path), pagesize=LETTER)
        width, height = LETTER; y = height - 72
        for line in lines:
            c.setFont("Times-Roman", 11); c.drawString(60, y, str(line)[:110]); y -= 16
            if y < 72: c.showPage(); y = height - 72
        c.save(); return out_path
    else:
        txt = Path(str(out_path).replace(".pdf",".txt"))
        txt.write_text("\n".join(lines), encoding="utf-8")
        return txt

def _merge_with_template(gen_pdf: Path, tmpl: Optional[Path]):
    if not (PYPDF2_OK and tmpl and tmpl.exists() and gen_pdf.suffix.lower()==".pdf"): return gen_pdf
    out = gen_pdf.parent / f"{gen_pdf.stem}_merged.pdf"
    w = PdfWriter()
    for p in [gen_pdf, tmpl]:
        try:
            r = PdfReader(str(p))
            for page in r.pages: w.add_page(page)
        except Exception: pass
    with open(out, "wb") as f: w.write(f)
    return out

def generate_loi_pdf(payload: Dict):
    state = (payload.get("state") or "TX").upper()
    lines = [
        "LETTER OF INTENT (LOI)",
        f"Date: {dt.date.today():%Y-%m-%d}",
        f"Property: {payload.get('property_address','')}",
        f"Offer Price: ${payload.get('offer_price',0):,.2f}",
        f"Buyer: {payload.get('buyer_name','')}",
        f"Seller: {payload.get('seller_name','')}",
        f"Earnest Money: ${payload.get('earnest_money',0):,.2f}",
        f"Inspection: {payload.get('inspection_days',7)} days",
        f"Closing: on/before {payload.get('closing_date','TBD')}",
        f"State: {state}",
        "Terms:", payload.get("terms","(none)")
    ]
    tmp = _write_text_pdf(lines, Path("exports/loi") / f"LOI_{uuid.uuid4().hex}.pdf")
    return _merge_with_template(tmp, Path(f"templates/loi/{state}.pdf"))

def generate_contract_pdf(payload: Dict):
    state = (payload.get("state") or "TX").upper()
    lines = [
        "PURCHASE & SALE AGREEMENT",
        f"Date: {dt.date.today():%Y-%m-%d}",
        f"Property: {payload.get('property_address','')}",
        f"Purchase Price: ${payload.get('purchase_price',0):,.2f}",
        f"Buyer: {payload.get('buyer_name','')}",
        f"Seller: {payload.get('seller_name','')}",
        f"Earnest: ${payload.get('earnest_money',0):,.2f}",
        f"Closing: on/before {payload.get('closing_date','TBD')}",
        f"State: {state}", "Terms:", payload.get("terms","(standard)")
    ]
    tmp = _write_text_pdf(lines, Path("exports/contracts") / f"CONTRACT_{uuid.uuid4().hex}.pdf")
    return _merge_with_template(tmp, Path(f"templates/contracts/{state}.pdf"))

# Calculators
def brrrr_calc(purchase, rehab, arv, ltv=0.75, closing_costs=6000, rate=0.07, rent=0, taxes=0, ins=0, mgmt=0.08, maint=0.05):
    total_cost = purchase + rehab + closing_costs
    new_loan = arv * ltv
    pmt = (rate/12 * new_loan) / (1 - (1+rate/12)**(-360)) if new_loan>0 else 0
    noi = rent - (rent*mgmt) - (rent*maint) - taxes/12 - ins/12
    cashflow = noi - pmt
    cash_out = max(0, new_loan - total_cost)
    coc = (cashflow*12) / max(1, total_cost - new_loan) * 100
    equity = max(0, arv - new_loan)
    return {"total_cost":total_cost,"new_loan":new_loan,"cash_out":cash_out,"monthly_pmt":pmt,"noi":noi,"cashflow":cashflow,"coc":coc,"equity":equity}

def subto_calc(arv, balance, existing_rate, piti, arrears=0, down=10000, assign_fee=0, wrap_rate=0.085, exit_rent=0):
    invest = down + assign_fee + arrears
    wrap_pmt = (wrap_rate/12 * balance) / (1 - (1+wrap_rate/12)**(-360)) if balance>0 else 0
    monthly_cf = exit_rent - max(piti, wrap_pmt)
    equity = max(0, arv - balance)
    roi = (monthly_cf*12) / max(1, invest) * 100
    return {"buyer_investment":invest,"wrap_pmt":wrap_pmt,"monthly_cashflow":monthly_cf,"equity":equity,"roi":roi}

# UI
def sidebar_nav():
    with st.sidebar:
        st.markdown("## 🏠 WTF Pro")
        for key, label in {"pipeline":"📊 Deal Pipeline","buyers":"🤝 Buyer Network","calculators":"🧮 BRRRR & SubTo","docs":"📄 LOI / Contracts"}.items():
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.page = key; st.experimental_rerun()
        st.caption("DB + Theme preserved.")

def page_pipeline():
    st.markdown('<div class="main-header">Deal Pipeline</div>', unsafe_allow_html=True)
    create_dummy_deals()
    import numpy as np
    df = list_deals()
    stage_counts = df["stage"].value_counts().reindex(KANBAN_STAGES, fill_value=0)
    cols = st.columns(len(KANBAN_STAGES))
    colors = ["#6B7280","#F59E0B","#8B5CF6","#3B82F6","#10B981"]
    for i,(stage,count) in enumerate(stage_counts.items()):
        with cols[i]:
            st.markdown(f"<div class='metric-card'><h4 style='margin:0;color:{colors[i]}'>{stage}</h4><div style='font-size:28px;font-weight:800;color:white'>{int(count)}</div></div>", unsafe_allow_html=True)
    if PLOTLY_OK:
        fig = go.Funnel(y=KANBAN_STAGES, x=[stage_counts.get(s,0) for s in KANBAN_STAGES], textinfo="value+percent initial", marker_color=colors)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#fff")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Plotly not installed; showing fallback bar chart. Add `plotly` to requirements.txt for the funnel.")
        st.bar_chart(pd.DataFrame({"count": [stage_counts.get(s,0) for s in KANBAN_STAGES]}, index=KANBAN_STAGES))

    # Kanban
    kcols = st.columns(len(KANBAN_STAGES))
    for i, stage in enumerate(KANBAN_STAGES):
        with kcols[i]:
            st.markdown(f"### {stage}")
            st.markdown("<div class='kanban-col'>", unsafe_allow_html=True)
            rows = df[df["stage"]==stage]
            if rows.empty: st.caption("No deals.")
            for _, r in rows.iterrows():
                st.markdown("<div class='deal-card'>", unsafe_allow_html=True)
                st.write(f"**{r['title']}**")
                st.caption(f"Price ${r.get('purchase_price') or 0:,.0f} | Fee ${r.get('assignment_fee') or 0:,.0f} | Prob {int(r.get('probability') or 0)}%")
                new_stage = st.selectbox("Move to…", KANBAN_STAGES, index=KANBAN_STAGES.index(stage), key=f"move_{r['id']}")
                if st.button("Move", key=f"btn_{r['id']}", use_container_width=True):
                    update_deal_stage(r["id"], new_stage); st.success(f"Moved to {new_stage}"); st.experimental_rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

def _parse_bool(x):
    if isinstance(x,(int,float)): return int(x)==1
    if isinstance(x,str): return x.strip().lower() in ["1","true","yes","y"]
    return False

def importer_from_csv(file):
    df = pd.read_csv(file)
    mapping = {"name":["name","buyer","company","buyer_name"],"email":["email","e-mail"],"phone":["phone","mobile","cell"],
               "min_price":["min_price","min","minimum"],"max_price":["max_price","max","maximum"],
               "states":["states","state"],"cities":["cities","city","markets"],"property_types":["property_types","types","asset_types"],
               "deal_types":["deal_types","strategy","strategies"],"verified":["verified","is_verified"],
               "proof_of_funds":["proof_of_funds","pof"],"cash_available":["cash","cash_available","capital"]}
    std = pd.DataFrame()
    for dst, aliases in mapping.items():
        for a in aliases:
            if a in df.columns: std[dst] = df[a]; break
        if dst not in std: std[dst] = None
    for col in ["states","cities","property_types","deal_types"]:
        std[col] = std[col].fillna("").astype(str).str.replace(";", ",")
    std["verified"] = std["verified"].map(_parse_bool).fillna(False)
    std["proof_of_funds"] = std["proof_of_funds"].map(_parse_bool).fillna(False)
    for col in ["cash_available","min_price","max_price"]:
        std[col] = pd.to_numeric(std[col], errors="coerce").fillna(0)
    for rec in std.to_dict(orient="records"): upsert_buyer(rec)
    return len(std)

def importer_from_google_sheet(sheet_url: str) -> int:
    """
    Uses google.oauth2.service_account (no oauth2client).
    Put service account JSON in .streamlit/secrets.toml under [gcp_service_account].
    Share the sheet with that service account email.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        scopes = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_url(sheet_url); ws = sh.sheet1
        records = ws.get_all_records()
        if not records: return 0
        df = pd.DataFrame(records); buf = io.StringIO(); df.to_csv(buf, index=False); buf.seek(0)
        return importer_from_csv(buf)
    except Exception as e:
        st.error(f"Google Sheets import failed: {e}"); return 0

def page_buyers():
    st.markdown('<div class="main-header">Buyer & Lender Network</div>', unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["Directory","Import (CSV/Sheets)","Auto-Match"])
    with tab1:
        st.subheader("All Buyers/Lenders"); st.dataframe(buyers_df(), use_container_width=True, hide_index=True)
    with tab2:
        c1,c2 = st.columns(2)
        with c1:
            up = st.file_uploader("Upload CSV", type=["csv"])
            if up is not None:
                n = importer_from_csv(up); st.success(f"Imported/updated {n} buyers.")
        with c2:
            url = st.text_input("Google Sheet URL")
            if st.button("Import from Google Sheet", use_container_width=True):
                n = importer_from_google_sheet(url)
                if n>0: st.success(f"Imported/updated {n} buyers from Google Sheet.")
    with tab3:
        colA,colB,colC = st.columns(3)
        city = colA.text_input("City","Dallas"); state = colB.text_input("State","TX")
        price = colC.number_input("Target Price",0.0, value=250000.0, step=1000.0)
        if st.button("Find Matches", use_container_width=True):
            m = match_buyers(city, state, price)
            if m.empty: st.info("No matches yet. Try importing your buyer list.")
            else: st.success(f"Found {len(m)} matching buyers."); st.dataframe(m, use_container_width=True, hide_index=True)

def page_calculators():
    st.markdown('<div class="main-header">BRRRR & SubTo Calculators</div>', unsafe_allow_html=True)
    tb1, tb2 = st.tabs(["BRRRR Calculator","SubTo / Wrap"])
    with tb1:
        c1,c2,c3 = st.columns(3)
        purchase = c1.number_input("Purchase Price",0.0,value=180000.0,step=5000.0)
        rehab    = c2.number_input("Rehab Budget",0.0,value=35000.0,step=1000.0)
        arv      = c3.number_input("ARV",0.0,value=260000.0,step=5000.0)
        c4,c5,c6 = st.columns(3)
        rent = c4.number_input("Market Rent (monthly)",0.0,value=1900.0,step=50.0)
        taxes = c5.number_input("Annual Taxes",0.0,value=4200.0,step=100.0)
        ins   = c6.number_input("Annual Insurance",0.0,value=1600.0,step=50.0)
        c7,c8,c9 = st.columns(3)
        ltv = c7.slider("Refi LTV",0.5,0.85,0.75,0.01)
        rate = c8.slider("Refi Rate (APR)",0.03,0.12,0.07,0.005)
        closing = c9.number_input("Closing Costs (acq+refi)",0.0,value=6000.0,step=500.0)
        if st.button("Calculate BRRRR", use_container_width=True):
            r = brrrr_calc(purchase, rehab, arv, ltv, closing, rate, rent, taxes, ins)
            st.metric("Cash Out at Refi", f"${r['cash_out']:,.0f}")
            st.metric("Monthly Cashflow", f"${r['cashflow']:,.0f}")
            st.metric("Cash-on-Cash", f"{r['coc']:.1f}%")
            st.metric("Equity After Refi", f"${r['equity']:,.0f}")
            st.json(r)
    with tb2:
        c1,c2,c3 = st.columns(3)
        arv = c1.number_input("ARV",0.0,value=300000.0,step=5000.0, key="s_arv")
        balance = c2.number_input("Existing Loan Balance",0.0,value=240000.0,step=5000.0)
        existing_rate = c3.slider("Existing Loan Rate (APR)",0.01,0.12,0.035,0.005)
        c4,c5,c6 = st.columns(3)
        piti = c4.number_input("Existing PITI (monthly)",0.0,value=1700.0,step=50.0)
        arrears = c5.number_input("Seller Arrears",0.0,value=0.0,step=500.0)
        down = c6.number_input("Down Payment",0.0,value=10000.0,step=1000.0)
        c7,c8,c9 = st.columns(3)
        assign_fee = c7.number_input("Assignment/Acq Fee",0.0,value=5000.0,step=500.0)
        wrap_rate = c8.slider("Wrap Rate (APR)",0.04,0.12,0.085,0.005)
        exit_rent = c9.number_input("Exit Rent (monthly)",0.0,value=2000.0,step=50.0)
        if st.button("Calculate SubTo", use_container_width=True):
            r = subto_calc(arv, balance, existing_rate, piti, arrears, down, assign_fee, wrap_rate, exit_rent)
            st.metric("Investor Cash In", f"${r['buyer_investment']:,.0f}")
            st.metric("Monthly Cashflow", f"${r['monthly_cashflow']:,.0f}")
            st.metric("ROI (annualized)", f"{r['roi']:.1f}%")
            st.metric("Equity Position", f"${r['equity']:,.0f}")
            st.json(r)

def page_docs():
    st.markdown('<div class="main-header">LOI & Contracts</div>', unsafe_allow_html=True)
    t1, t2 = st.tabs(["Generate LOI","Generate Contract"])
    with t1:
        with st.form("loi_form"):
            address = st.text_input("Property Address")
            offer = st.number_input("Offer Price",0.0,step=1000.0)
            buyer = st.text_input("Buyer Name")
            seller = st.text_input("Seller Name")
            earnest = st.number_input("Earnest Money",0.0,step=500.0,value=1000.0)
            insp = st.number_input("Inspection Days",1,21,7)
            state = st.text_input("State","TX")
            terms = st.text_area("Additional Terms","(as-is, buyer pays all closing costs, assignable)")
            closing = st.text_input("Closing Date","TBD")
            submit = st.form_submit_button("Generate LOI (PDF)")
        if submit:
            payload = dict(property_address=address, offer_price=offer, buyer_name=buyer, seller_name=seller,
                           earnest_money=earnest, inspection_days=insp, closing_date=closing, state=state, terms=terms)
            pdf = generate_loi_pdf(payload)
            with db() as conn:
                conn.execute("""INSERT INTO lois (id, lead_id, property_address, offer_price, state, terms, status, pdf_path, sent_date)
                                VALUES (?,?,?,?,?,?,?,?,?)""",
                             (uuid.uuid4().hex,"",address,offer,state,terms,"generated",str(pdf),dt.datetime.now()))
                conn.commit()
            st.success("LOI generated."); st.markdown(f"[Download LOI]({pdf})")
    with t2:
        with st.form("contract_form"):
            address = st.text_input("Property Address", key="c_addr")
            price = st.number_input("Purchase Price",0.0,step=1000.0, key="c_price")
            buyer = st.text_input("Buyer Name", key="c_buyer")
            seller = st.text_input("Seller Name", key="c_seller")
            earnest = st.number_input("Earnest Money",0.0,step=500.0,value=1500.0, key="c_em")
            closing = st.text_input("Closing Date","TBD", key="c_close")
            state = st.text_input("State","TX", key="c_state")
            terms = st.text_area("Terms","(standard TREC style clauses; assignable addendum)", key="c_terms")
            submit = st.form_submit_button("Generate Contract (PDF)")
        if submit:
            payload = dict(property_address=address, purchase_price=price, buyer_name=buyer,
                           seller_name=seller, earnest_money=earnest, closing_date=closing, state=state, terms=terms)
            pdf = generate_contract_pdf(payload)
            with db() as conn:
                conn.execute("""INSERT INTO contracts (id, deal_id, contract_type, purchase_price, earnest_money, closing_date, buyer_name, seller_name, property_address, state, status, pdf_path)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                             (uuid.uuid4().hex,"","PSA",price,earnest,closing,buyer,seller,address,state,"generated",str(pdf)))
                conn.commit()
            st.success("Contract generated."); st.markdown(f"[Download Contract]({pdf})")

def main():
    init_db()
    if "page" not in st.session_state: st.session_state.page = "pipeline"
    sidebar_nav()
    page = st.session_state.page
    if page=="pipeline": page_pipeline()
    elif page=="buyers": page_buyers()
    elif page=="calculators": page_calculators()
    elif page=="docs": page_docs()
    else: page_pipeline()

if __name__ == "__main__":
    main()
