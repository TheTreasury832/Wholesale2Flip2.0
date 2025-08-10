
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# -----------------------------
# App Config & Theming
# -----------------------------
st.set_page_config(page_title="WTF — Wholesale on Steroids", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")

THEME_CSS = """
<style>
.stApp { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%); font-family: 'Inter', sans-serif; }
#MainMenu, header, footer, .stDeployButton { visibility: hidden; }
h1,h2,h3,h4,h5 { color: #fff; }
.hero { background: linear-gradient(135deg, #8B5CF6 0%, #10B981 30%, #3B82F6 60%, #F59E0B 100%);
        color: white; padding: 2.5rem; border-radius: 20px; box-shadow: 0 20px 40px rgba(0,0,0,0.4); }
.card { background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 16px; padding: 1.25rem; }
.metric { background: linear-gradient(135deg, rgba(139,92,246,.15), rgba(16,185,129,.10)); border: 1px solid rgba(139,92,246,.4);
         border-radius: 16px; padding: 1rem 1.25rem; color: #fff; }
button, .stButton>button { background: linear-gradient(90deg, #8B5CF6, #10B981) !important; color: #fff !important;
         border: 0 !important; border-radius: 10px !important; padding: .6rem 1rem !important; font-weight: 600 !important; }
.badge { display:inline-block; padding:.25rem .6rem; border-radius:999px; background:#10B981; color:#04110a; font-weight:700; }
.small { color:#cbd5e1; font-size:.9rem }
.label { color:#cbd5e1; }
.kpi { font-size:1.4rem; font-weight:800; color:#fff; }
.sub { color:#cbd5e1; font-size:.85rem; }
hr { border-color: rgba(255,255,255,0.1) }
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)

# -----------------------------
# Demo Auth (swap to Whop later)
# -----------------------------
USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Admin"},
    "demo": {"password": "demo", "role": "demo", "name": "Demo User"},
    "wholesaler": {"password": "demo123", "role": "wholesaler", "name": "Wholesaler Pro"},
    "investor": {"password": "invest123", "role": "investor", "name": "Investor"}
}

def init_state():
    ss = st.session_state
    ss.setdefault("auth", {"ok": False, "user": None})
    ss.setdefault("page", "Landing")
    ss.setdefault("leads", [])
    ss.setdefault("deals", [])
    ss.setdefault("buyers", init_buyers())
    ss.setdefault("current_property", None)
    ss.setdefault("campaigns", [])
    ss.setdefault("recent_actions", [])

def init_buyers():
    # Example verified buyers (expandable with real DB later)
    return [
        {"id": "B001", "name": "Empire Capital Partners", "verified": True, "cash": 2500000,
         "min_price": 75000, "max_price": 300000, "states": ["TX","FL","GA"], "types": ["SFR"], "close_days": 14},
        {"id": "B002", "name": "Pinnacle Real Estate Group", "verified": True, "cash": 1800000,
         "min_price": 90000, "max_price": 400000, "states": ["TX","AZ","NC","SC"], "types": ["SFR","Townhome"], "close_days": 21},
        {"id": "B003", "name": "Sunbelt Rental Fund", "verified": True, "cash": 3200000,
         "min_price": 60000, "max_price": 240000, "states": ["TX","AL","MS","TN","FL"], "types": ["SFR"], "close_days": 28},
        {"id": "B004", "name": "Great Lakes Holdings", "verified": False, "cash": 900000,
         "min_price": 50000, "max_price": 180000, "states": ["OH","MI","IN","IL"], "types": ["SFR","Duplex"], "close_days": 30},
    ]

def login_ui():
    with st.container():
        st.markdown('<div class="hero">', unsafe_allow_html=True)
        st.markdown("### WTF — Wholesale on Steroids")
        st.markdown("**Sign in** (Whop OAuth coming; demo logins below)")
        col1, col2 = st.columns([1,1])
        with col1:
            u = st.text_input("Username", value="", key="auth_user")
            p = st.text_input("Password", value="", type="password", key="auth_pass")
            if st.button("Sign In"):
                if u in USERS and USERS[u]["password"] == p:
                    st.session_state.auth = {"ok": True, "user": {**USERS[u], "username": u}}
                    st.session_state.page = "Dashboard"
                    st.success("Signed in successfully.")
                else:
                    st.error("Invalid credentials.")
        with col2:
            st.caption("**Demo accounts**")
            st.code("admin / admin123\n_demo / demo_\nwholesaler / demo123\ninvestor / invest123")
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Utility: Sample Property Data & Calculations
# -----------------------------
SAMPLE_ADDR = "21372 W Memorial Dr, Porter, TX 77365"
SAMPLE_DATA = {
    "address": SAMPLE_ADDR,
    "owner": "EDGAR LORI G",
    "est_value": 267000,
    "sqft": 1643,
    "beds": 3,
    "baths": 2,
    "year_built": 1969,
    "lot_sqft": 24300,
    "rent": 1973,
    "mortgage_balance": 27986,
    "equity": 239014,
    "taxes": 1497,
    "condition": "Good",
    "market_price_change": 0.0437,
    "market_rent_change": 0.0169,
    "state": "TX", "city": "Porter", "type": "SFR"
}

def analyze_property(addr: str, arv: float=None, rehab: float=0.0):
    # If matches sample, load it; else create a basic record using inputs
    base = SAMPLE_DATA.copy() if addr.strip().lower() == SAMPLE_ADDR.lower() else {
        "address": addr.strip(),
        "owner": "Unknown",
        "est_value": float(arv) if arv else 200000.0,
        "sqft": None, "beds": None, "baths": None, "year_built": None, "lot_sqft": None,
        "rent": None, "mortgage_balance": None, "equity": None, "taxes": None,
        "condition": "Unknown",
        "market_price_change": 0.02, "market_rent_change": 0.01,
        "state": "TX", "city": "", "type": "SFR"
    }
    est_arv = float(arv) if arv else base["est_value"]
    mao70 = 0.70 * est_arv - float(rehab or 0)
    mao75 = 0.75 * est_arv - float(rehab or 0)
    # simple profit calc assuming buyer pays mao70 and rehab occurs
    profit_wholesale = max(0, (mao75 - mao70))  # spread between 70/75 anchors
    grade = "A" if mao70/est_arv >= 0.60 else ("B" if mao70/est_arv >= 0.55 else ("C" if mao70/est_arv >= 0.50 else "D"))
    base.update({
        "arv": est_arv, "rehab": float(rehab or 0),
        "mao70": round(mao70, 2), "mao75": round(mao75, 2),
        "profit_est": round(profit_wholesale, 2), "grade": grade
    })
    return base

def match_buyers(prop, buyers):
    matches = []
    for b in buyers:
        in_state = prop.get("state") in b["states"]
        price_ok = b["min_price"] <= prop.get("mao70", 0) <= b["max_price"]
        type_ok = prop.get("type", "SFR") in b["types"]
        if in_state and price_ok and type_ok:
            offer = round(prop["mao75"], 2)  # simple suggested offer anchor
            matches.append({**b, "offer": offer})
    return matches

# -----------------------------
# Pages
# -----------------------------
def page_landing():
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("## WTF — Wholesale on Steroids")
    st.markdown("Professional platform for wholesalers, flippers, and BRRRR investors with **real** calculations and **deal automation**.")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown('<div class="metric"><div class="kpi">15,000+</div><div class="sub">Deals Analyzed</div></div>', unsafe_allow_html=True)
    with col2: st.markdown('<div class="metric"><div class="kpi">$50M+</div><div class="sub">Pipeline Value</div></div>', unsafe_allow_html=True)
    with col3: st.markdown('<div class="metric"><div class="kpi">2,500+</div><div class="sub">Active Users</div></div>', unsafe_allow_html=True)
    with col4: st.markdown('<div class="metric"><div class="kpi">98%</div><div class="sub">Satisfaction</div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### Pricing")
    c1,c2,c3 = st.columns(3)
    for c, plan, price in [(c1,"Starter","$29/mo"),(c2,"Professional","$79/mo"),(c3,"Enterprise","$199/mo")]:
        with c:
            st.markdown(f'<div class="card"><h3 style="margin:0;color:#fff">{plan}</h3><div class="small">All core features</div><h2 style="color:#8B5CF6">{price}</h2><div class="small">Cancel anytime</div></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown("#### Sign in below with demo credentials to explore the full platform.")

def page_dashboard():
    user = st.session_state.auth["user"]["name"]
    st.markdown(f"### Welcome back, **{user}** 👋")
    k1,k2,k3,k4,k5 = st.columns(5)
    k1.markdown('<div class="metric"><div class="sub">Revenue</div><div class="kpi">$125K</div></div>', unsafe_allow_html=True)
    k2.markdown('<div class="metric"><div class="sub">Pipeline</div><div class="kpi">$485K</div></div>', unsafe_allow_html=True)
    k3.markdown('<div class="metric"><div class="sub">Hot Leads</div><div class="kpi">28</div></div>', unsafe_allow_html=True)
    k4.markdown('<div class="metric"><div class="sub">Grade A Deals</div><div class="kpi">67</div></div>', unsafe_allow_html=True)
    k5.markdown('<div class="metric"><div class="sub">Conversion</div><div class="kpi">18.5%</div></div>', unsafe_allow_html=True)

    st.write("")
    qa1, qa2, qa3, qa4 = st.columns(4)
    if qa1.button("🔎 Analyze New Deal"):
        st.session_state.page = "Deal Analyzer"
    if qa2.button("➕ Add New Lead"):
        st.session_state.page = "Lead Manager"
    if qa3.button("🧭 Find Buyers"):
        st.session_state.page = "Buyer Network"
    if qa4.button("📊 View Analytics"):
        st.session_state.page = "Analytics"

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Recent Deals")
        if st.session_state.deals:
            df = pd.DataFrame(st.session_state.deals)
            st.dataframe(df[["address","grade","mao70","mao75","status"]].tail(10), use_container_width=True)
        else:
            st.info("No deals yet — analyze a property to get started.")
    with c2:
        st.subheader("Recent Leads")
        if st.session_state.leads:
            df = pd.DataFrame(st.session_state.leads)
            st.dataframe(df[["name","phone","address","score","status"]].tail(10), use_container_width=True)
        else:
            st.info("No leads yet — add a lead from the Lead Manager.")

def page_deal_analyzer():
    st.subheader("Deal Analyzer")
    with st.form("analyze"):
        addr = st.text_input("Property Address", value=SAMPLE_ADDR)
        arv = st.number_input("After Repair Value (ARV)", value=267000.0, step=1000.0)
        rehab = st.number_input("Estimated Rehab ($)", value=25000.0, step=1000.0)
        submitted = st.form_submit_button("Analyze 🔎")
    if submitted:
        prop = analyze_property(addr, arv, rehab)
        st.session_state.current_property = prop
        st.success("Analysis complete.")
    prop = st.session_state.get("current_property")
    if prop:
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("ARV", f"${prop['arv']:,.0f}")
        c2.metric("MAO 70%", f"${prop['mao70']:,.0f}")
        c3.metric("MAO 75%", f"${prop['mao75']:,.0f}")
        c4.metric("Est. Profit", f"${prop['profit_est']:,.0f}")
        c5.metric("Deal Grade", prop['grade'])

        st.markdown("#### Strategy Suggestions")
        st.markdown("- **Wholesale**: Lock near MAO 70% and dispo to matched buyer.\n- **Fix & Flip**: Consider if rehab < 20% ARV and DOM low.\n- **BRRRR**: If rent supports DSCR ≥ 1.2 at 75% LTV.")
        st.write("")
        st.markdown("#### Buyer Matches")
        matches = match_buyers(prop, st.session_state.buyers)
        if matches:
            for m in matches:
                col1, col2, col3, col4 = st.columns([2,1,1,1])
                col1.markdown(f"**{m['name']}** {'✅' if m['verified'] else ''}  \nCash: ${m['cash']:,.0f} · Close ~{m['close_days']}d")
                col2.markdown(f"Offer: **${m['offer']:,.0f}**")
                if col3.button("📄 Send Deal", key=f"send_{m['id']}"):
                    st.session_state.recent_actions.append({"ts": datetime.now().isoformat(), "action": "send_deal", "buyer": m["name"], "address": prop["address"]})
                    st.success(f"Deal sent to {m['name']}")
                if col4.button("📞 Contact", key=f"call_{m['id']}"):
                    st.info(f"Contacting {m['name']}… (open CRM)")
        else:
            st.warning("No buyer matches yet. Try adjusting ARV, rehab, or target buyers — or run an RVM campaign.")

        # Save to deals list
        if st.button("💾 Save to Pipeline"):
            st.session_state.deals.append({
                "address": prop["address"], "grade": prop["grade"],
                "mao70": prop["mao70"], "mao75": prop["mao75"],
                "status": "Analyzing"
            })
            st.success("Deal added to pipeline.")

def page_lead_manager():
    st.subheader("Lead Manager (CRM)")
    with st.form("add_lead"):
        name = st.text_input("Seller Name")
        phone = st.text_input("Phone")
        address = st.text_input("Property Address")
        motivation = st.selectbox("Motivation", ["Low","Medium","High"])
        equity = st.selectbox("Equity", ["<10%","10-30%","30-50%","50%+"])
        timeline = st.selectbox("Timeline", ["ASAP","30-60 days","60+ days"])
        source = st.selectbox("Source", ["Direct Mail","RVM","Cold Calling","PPC","Referral"])
        submit = st.form_submit_button("Add Lead ➕")
    if submit:
        score = 60
        score += {"Low":0,"Medium":10,"High":20}[motivation]
        score += {"<10%":0,"10-30%":10,"30-50%":15,"50%+":20}[equity]
        score += {"ASAP":15,"30-60 days":8,"60+ days":0}[timeline]
        st.session_state.leads.append({
            "name": name, "phone": phone, "address": address,
            "motivation": motivation, "equity": equity, "timeline": timeline,
            "source": source, "score": score, "status": "New"
        })
        st.success(f"Lead added with score **{score}**.")
    if st.session_state.leads:
        df = pd.DataFrame(st.session_state.leads)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No leads yet.")

def page_pipeline():
    st.subheader("Deal Pipeline")
    stages = ["Prospecting","Negotiating","Under Contract","Due Diligence","Closed"]
    if st.session_state.deals:
        for i, d in enumerate(st.session_state.deals):
            cols = st.columns([3,2,2])
            cols[0].markdown(f"**{d['address']}**  \nGrade **{d['grade']}** · 70% ${d['mao70']:,.0f} · 75% ${d['mao75']:,.0f}")
            new_status = cols[1].selectbox("Stage", stages, index=stages.index(d.get("status","Prospecting")), key=f"stage_{i}")
            if new_status != d.get("status"):
                st.session_state.deals[i]["status"] = new_status
            if cols[2].button("Remove", key=f"del_{i}"):
                st.session_state.deals.pop(i)
                st.experimental_rerun()
        # Revenue forecast (simple)
        df = pd.DataFrame(st.session_state.deals)
        est_rev = (df["mao75"] - df["mao70"]).clip(lower=0).sum() if not df.empty else 0
        st.markdown(f"**Forecasted Assignment Spread (sum):** ${est_rev:,.0f}")
    else:
        st.info("No deals yet — add from the Deal Analyzer.")

def page_buyer_network():
    st.subheader("Buyer Network")
    for b in st.session_state.buyers:
        cols = st.columns([3,2,2,1])
        cols[0].markdown(f"**{b['name']}** {'✅' if b['verified'] else ''}  \nStates: {', '.join(b['states'])} · Types: {', '.join(b['types'])}")
        cols[1].markdown(f"Cash: **${b['cash']:,.0f}**")
        cols[2].markdown(f"Buy Box: **${b['min_price']:,.0f} - ${b['max_price']:,.0f}**")
        cols[3].markdown(f"~{b['close_days']}d")
    st.info("Upload more buyers or edit criteria in the Admin panel (future).")

def generate_contract_text(data):
    return f"""
PURCHASE AND SALE AGREEMENT
Property: {data.get('address','')}
Seller: {data.get('seller','')}
Buyer:  {data.get('buyer','')}
Purchase Price: ${data.get('price',0):,.0f}
Earnest Money: ${data.get('emd',1000):,.0f}
Closing Date: {data.get('close_date','')}

Standard terms and conditions apply, including inspection and clear title. This agreement is assignable.
"""

def page_contracts():
    st.subheader("Contract Generator")
    prop = st.session_state.get("current_property")
    with st.form("contract"):
        address = st.text_input("Property Address", value=(prop["address"] if prop else ""))
        seller = st.text_input("Seller Name", value=(SAMPLE_DATA["owner"] if prop and prop["address"] == SAMPLE_ADDR else ""))
        buyer = st.text_input("Buyer Name / LLC", value="WTF Holdings LLC")
        price = st.number_input("Purchase Price ($)", value=float(prop["mao70"]) if prop else 100000.0, step=1000.0)
        emd = st.number_input("Earnest Money ($)", value=1000.0, step=100.0)
        close_date = st.date_input("Closing Date", value=datetime.today()+timedelta(days=30))
        gen = st.form_submit_button("Generate Contract 📄")
    if gen:
        text = generate_contract_text({"address": address, "seller": seller, "buyer": buyer, "price": price, "emd": emd, "close_date": close_date})
        st.text_area("Preview", value=text, height=260)
        # Download as .txt
        st.download_button("Download .txt", data=text, file_name="contract.txt")

def page_loi():
    st.subheader("LOI Generator")
    with st.form("loi"):
        address = st.text_input("Property Address", value=SAMPLE_ADDR)
        offer = st.number_input("Offer Price ($)", value=200000.0, step=1000.0)
        terms = st.text_area("Key Terms", value="- Inspection period: 7–10 days\n- Close in 14–30 days\n- Buyer pays closing costs")
        gen = st.form_submit_button("Generate LOI 📄")
    if gen:
        txt = f"""LETTER OF INTENT

To Whom It May Concern,

We are pleased to submit this Letter of Intent to purchase the property at {address} for ${offer:,.0f}. 
Key terms:
{terms}

This LOI is non-binding and intended to outline the basic terms prior to a formal agreement.

Sincerely,
WTF Holdings LLC
"""
        st.text_area("Preview", value=txt, height=240)
        st.download_button("Download .txt", data=txt, file_name="loi.txt")

def page_rvm():
    st.subheader("RVM Campaigns")
    with st.form("rvm"):
        name = st.text_input("Campaign Name", value=f"RVM {datetime.now().strftime('%Y-%m-%d')}")
        msg = st.text_area("Voicemail Script", value="Hi, I'm interested in buying your property. Call me back if you'd consider an offer. Thanks!")
        recipients = st.text_area("Recipient Phone Numbers (one per line)", value="2815551234\n9365559876")
        cost = 0.15
        submit = st.form_submit_button("Launch Campaign 🚀")
    if submit:
        nums = [n.strip() for n in recipients.splitlines() if n.strip()]
        total_cost = len(nums) * cost
        st.success(f"Campaign '{name}' launched to {len(nums)} recipients. Est. cost: ${total_cost:,.2f}")
        st.session_state.campaigns.append({"name": name, "count": len(nums), "cost": total_cost, "ts": datetime.now().isoformat()})

def page_analytics():
    st.subheader("Analytics")
    # Simple analytics from session
    deals = pd.DataFrame(st.session_state.deals) if st.session_state.deals else pd.DataFrame(columns=["status","grade","mao70","mao75"])
    leads = pd.DataFrame(st.session_state.leads) if st.session_state.leads else pd.DataFrame(columns=["status","score","source"])
    campaigns = pd.DataFrame(st.session_state.campaigns) if st.session_state.campaigns else pd.DataFrame(columns=["name","count","cost"])

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Deals by Stage**")
        if not deals.empty:
            chart = deals["status"].value_counts().reset_index()
            fig = px.bar(chart, x="index", y="status", labels={"index":"Stage","status":"Count"})
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No deals yet.")
    with c2:
        st.markdown("**Lead Score Distribution**")
        if not leads.empty:
            fig = px.histogram(leads, x="score", nbins=10)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No leads yet.")

    st.markdown("**Campaign Summary**")
    if not campaigns.empty:
        st.dataframe(campaigns, use_container_width=True)
    else:
        st.info("No campaigns yet.")

# -----------------------------
# App Router
# -----------------------------
def main():
    init_state()

    # Sidebar Navigation
    if st.session_state.auth["ok"]:
        with st.sidebar:
            st.markdown("### WTF — Navigation")
            choice = st.radio("Go to", ["Dashboard","Deal Analyzer","Lead Manager","Deal Pipeline","Buyer Network","Contracts","LOI Generator","RVM Campaigns","Analytics"])
            st.session_state.page = choice
            if st.button("Sign Out", type="primary"):
                st.session_state.auth = {"ok": False, "user": None}
                st.session_state.page = "Landing"

    # Page Selection
    if not st.session_state.auth["ok"]:
        page_landing()
        login_ui()
    else:
        page = st.session_state.page
        if page == "Dashboard": page_dashboard()
        elif page == "Deal Analyzer": page_deal_analyzer()
        elif page == "Lead Manager": page_lead_manager()
        elif page == "Deal Pipeline": page_pipeline()
        elif page == "Buyer Network": page_buyer_network()
        elif page == "Contracts": page_contracts()
        elif page == "LOI Generator": page_loi()
        elif page == "RVM Campaigns": page_rvm()
        elif page == "Analytics": page_analytics()
        else: page_dashboard()

if __name__ == "__main__":
    main()
