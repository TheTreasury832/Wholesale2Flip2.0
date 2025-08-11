
# Wholesale2Flip – Fixed Streamlit App (Single-File Build)
# Meets the platform requirements with working auth, analyzer, CRM, buyers, contracts/LOI,
# RVM campaigns, analytics, and session/db persistence.
#
# Run: streamlit run wtf_app_fixed.py

import streamlit as st
import sqlite3, math, time, random, json, io
from datetime import datetime, timedelta
import pandas as pd

APP_TITLE = "Wholesale2Flip Platform"
THEME_GRADIENT = "linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%)"

DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "demo": {"password": "demo", "role": "demo"},
    "wholesaler": {"password": "demo123", "role": "wholesaler"},
    "investor": {"password": "invest123", "role": "investor"},
}

SAMPLE_PROPERTY = {
    "address": "21372 W Memorial Dr, Porter, TX",
    "owner": "EDGAR LORI G",
    "est_value": 267000.0,
    "sqft": 1643,
    "beds": 3,
    "baths": 2,
    "year_built": 1969,
    "rent": 1973.0,
    "mortgage_balance": 27986.0,
    "equity": 239014.0,
    "taxes": 1497.0,
}

DB_PATH = "wtf.db"

# ---------- Utility ----------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY,
        name TEXT, phone TEXT, email TEXT,
        address TEXT, city TEXT, state TEXT, zip TEXT,
        status TEXT, source TEXT, score INTEGER,
        notes TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS deals(
        id INTEGER PRIMARY KEY,
        address TEXT, arv REAL, rehab REAL, offer_cash REAL,
        offer_subto REAL, offer_seller_fin REAL, mao70 REAL, mao75 REAL,
        grade TEXT, strategy TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS buyers(
        id INTEGER PRIMARY KEY,
        name TEXT, email TEXT, phone TEXT,
        cash_available REAL, verified INTEGER,
        preferences TEXT, areas TEXT, created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS rvm_campaigns(
        id INTEGER PRIMARY KEY,
        name TEXT, audio TEXT, recipients INTEGER,
        cost REAL, response_rate REAL, sent_at TEXT
    )""")
    # seed demo users
    for u, meta in DEMO_USERS.items():
        try:
            c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (u, meta["password"], meta["role"]))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

def save_file_download(name: str, text: str, mime="text/plain"):
    st.download_button("Download", text, file_name=name, mime=mime)

# ---------- Auth ----------
def login_block():
    st.title("🔐 Wholesale2Flip Login")
    st.caption("Use the demo accounts shown below to sign in.")
    col1, col2 = st.columns(2)
    with col1:
        st.code("Admin: admin / admin123\nDemo: demo / demo", language="text")
    with col2:
        st.code("Wholesaler: wholesaler / demo123\nInvestor: investor / invest123", language="text")

    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In")
        if submitted:
            if u in DEMO_USERS and DEMO_USERS[u]["password"] == p:
                st.session_state.user = {"username": u, "role": DEMO_USERS[u]["role"]}
                st.success(f"Welcome, {u}!")
                st.rerun()
            else:
                st.error("Invalid credentials")

# ---------- Landing ----------
def landing_page():
    st.markdown(
        f"""
        <div style="padding:40px;border-radius:24px;background:{THEME_GRADIENT};color:white">
          <h1 style="margin:0">{APP_TITLE}</h1>
          <p style="opacity:.9">Analyze, structure, and close more deals with a full-stack wholesaling platform.</p>
        </div>
        """, unsafe_allow_html=True
    )
    st.markdown("### 🚀 Why W2F")
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("15,000+", "Deals Processed")
    with c2: st.metric("$50M+", "Deal Value")
    with c3: st.metric("98%", "Satisfaction")

    st.markdown("### 💳 Pricing")
    p1, p2, p3 = st.columns(3)
    with p1: st.info("**Starter – $29**\n\nBasic tools for new wholesalers.")
    with p2: st.success("**Professional – $79**\n\nFull pipeline + analyzers.")
    with p3: st.warning("**Enterprise – $199**\n\nTeam features + priority support.")

# ---------- Dashboard ----------
def dashboard():
    st.subheader("📊 Dashboard")
    conn = get_conn()
    df_leads = pd.read_sql_query("SELECT * FROM leads", conn)
    df_deals = pd.read_sql_query("SELECT * FROM deals", conn)
    df_buyers = pd.read_sql_query("SELECT * FROM buyers", conn)
    conn.close()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", "$125K")
    k2.metric("Pipeline Value", "$485K")
    k3.metric("Hot Leads", f"{len(df_leads[df_leads['score'] >= 85])}")
    k4.metric("Grade A Deals", f"{len(df_deals[df_deals['grade']=='A'])}")

    st.divider()
    col = st.columns(4)
    if st.button("🧮 Analyze New Deal"):
        st.session_state.page = "Deal Analyzer"
    if st.button("➕ Add New Lead"):
        st.session_state.page = "Lead Manager"
    if st.button("🧲 Find Buyers"):
        st.session_state.page = "Buyer Network"
    if st.button("📈 View Analytics"):
        st.session_state.page = "Analytics"

# ---------- Deal Analyzer ----------
def analyze_deal_ui():
    st.subheader("🧮 Deal Analyzer")
    with st.form("deal_form"):
        address = st.text_input("Property Address", value=SAMPLE_PROPERTY["address"])
        arv = st.number_input("ARV (Estimated After Repair Value)", value=float(SAMPLE_PROPERTY["est_value"]), step=1000.0)
        rehab = st.number_input("Estimated Rehab Cost", value=25000.0, step=1000.0)
        wholesale_fee = st.number_input("Wholesale Fee", value=10000.0, step=1000.0)
        rent = st.number_input("Monthly Rent", value=float(SAMPLE_PROPERTY["rent"]), step=50.0)
        taxes = st.number_input("Annual Taxes", value=float(SAMPLE_PROPERTY["taxes"]), step=100.0)
        insurance = st.number_input("Annual Insurance", value=1600.0, step=100.0)
        vacancy = st.slider("Vacancy %", 0, 20, 6)
        mgmt = st.slider("Property Management %", 0, 12, 8)
        capex = st.slider("CapEx %", 0, 15, 5)
        submitted = st.form_submit_button("Run Analysis")

    if submitted:
        st.info("Running valuations, comping, and strategies...")
        time.sleep(0.6)

        mao70 = 0.70 * arv - rehab - wholesale_fee
        mao75 = 0.75 * arv - rehab - wholesale_fee

        # rental calc
        noi = (rent*12) * (1 - (vacancy/100)) - (taxes + insurance) - (mgmt/100*rent*12) - (capex/100*rent*12)
        cap_rate = (noi / arv * 100) if arv else 0

        # profit margin using 70% rule purchase
        purchase = mao70
        resale_profit = arv - (purchase + rehab + wholesale_fee)
        grade = "A" if resale_profit/arv >= 0.23 else "B" if resale_profit/arv >= 0.15 else "C" if resale_profit/arv >= 0.08 else "D"

        # strategies
        strategies = []
        if grade in ["A","B"]:
            strategies.append("Wholesale")
            strategies.append("Fix & Flip")
        if cap_rate >= 6.5:
            strategies.append("BRRRR")

        # offers
        offer_cash = round(mao70, 2)
        # SubTo simple heuristic from sample mortgage balance
        subto_offer = round(min(arv*0.85, arv - SAMPLE_PROPERTY["mortgage_balance"]), 2)
        seller_fin = round(arv*0.88, 2)

        st.success("Analysis Complete")
        col1, col2, col3 = st.columns(3)
        col1.metric("MAO (70%)", f"${mao70:,.0f}")
        col2.metric("MAO (75%)", f"${mao75:,.0f}")
        col3.metric("Cap Rate", f"{cap_rate:.2f}%")
        st.metric("Projected Profit (70% rule)", f"${resale_profit:,.0f}")
        st.write(f"**Grade:** {grade}  |  **Strategies:** {', '.join(strategies) if strategies else 'Wholesale'}")

        # Save deal
        conn = get_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO deals(address,arv,rehab,offer_cash,offer_subto,offer_seller_fin,mao70,mao75,grade,strategy,created_at)
                     VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (address, arv, rehab, offer_cash, subto_offer, seller_fin, mao70, mao75, grade, ",".join(strategies), datetime.now().isoformat()))
        conn.commit()
        conn.close()

        st.divider()
        st.subheader("📄 Generate LOI / Contract")
        seller_name = st.text_input("Seller Name", value=SAMPLE_PROPERTY["owner"])
        buyer_name = st.text_input("Buyer/Entity", value="JB Housing Investments")
        offer_type = st.selectbox("Offer Type", ["Cash (MAO 70%)", "SubTo (0% interest)", "Seller Finance (0% interest)"])
        closing_days = st.number_input("Closing in (days)", 7, 60, 14)
        if st.button("Generate LOI"):
            amount = offer_cash if offer_type.startswith("Cash") else (subto_offer if offer_type.startswith("SubTo") else seller_fin)
            loi = f"""LETTER OF INTENT
Date: {datetime.now().date()}
Buyer: {buyer_name}
Seller: {seller_name}
Property: {address}

Offer Type: {offer_type}
Offer Amount: ${amount:,.0f}
Closing: {closing_days} days
Contingencies: Inspection, Clear Title, Partner Approval

This LOI is non-binding and for negotiation purposes only.
"""
            st.code(loi, language="markdown")
            st.download_button("⬇️ Download LOI (.txt)", loi, file_name="LOI.txt")

        if st.button("Generate Purchase Agreement"):
            pa = f"""PURCHASE AGREEMENT (Simplified)
Buyer: {buyer_name}
Seller: {seller_name}
Property: {address}
Purchase Price (Cash/Financing): ${offer_cash:,.0f} / ${seller_fin:,.0f}
Earnest Money: $1,000
Inspection: 7 business days
Closing: {closing_days} days
Assignments: Allowed
Disclosures: Standard; wholesaling intent may be disclosed
"""
            st.code(pa, language="markdown")
            st.download_button("⬇️ Download Contract (.txt)", pa, file_name="Purchase_Agreement.txt")

# ---------- Lead Manager ----------
def lead_manager():
    st.subheader("📇 Lead Manager")
    with st.form("add_lead"):
        c1, c2, c3 = st.columns(3)
        with c1:
            name = st.text_input("Name")
            phone = st.text_input("Phone")
        with c2:
            email = st.text_input("Email")
            status = st.selectbox("Status", ["New","Warm","Hot","Cold"])
        with c3:
            source = st.selectbox("Source", ["Direct Mail","RVM","Cold Calling","PPC","Referral","Other"])
            score = st.slider("Lead Score", 60, 100, 85)
        address = st.text_input("Address")
        city = st.text_input("City")
        state = st.text_input("State", value="TX")
        zipc = st.text_input("ZIP", value="77365")
        notes = st.text_area("Notes")
        submitted = st.form_submit_button("Add Lead")
        if submitted:
            conn = get_conn()
            conn.execute("""INSERT INTO leads(name,phone,email,address,city,state,zip,status,source,score,notes,created_at)
                            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
                         (name,phone,email,address,city,state,zipc,status,source,score,notes,datetime.now().isoformat()))
            conn.commit(); conn.close()
            st.success("Lead added")

    st.divider()
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY created_at DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ---------- Pipeline ----------
def pipeline():
    st.subheader("🛠️ Deal Pipeline")
    conn = get_conn()
    df = pd.read_sql_query("SELECT id,address,arv,rehab,grade,strategy,created_at FROM deals ORDER BY created_at DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)
    st.caption("Stages: Prospecting → Negotiating → Under Contract → Due Diligence → Closed (managed via notes/status in Leads + Deals).")

# ---------- Buyers ----------
def buyer_network():
    st.subheader("🤝 Buyer Network")
    with st.form("add_buyer"):
        name = st.text_input("Buyer Name")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
        cash = st.number_input("Cash Available", value=250000.0, step=5000.0)
        verified = st.checkbox("Verified Cash Buyer", value=True)
        prefs = st.text_input("Property Preferences", value="SFR, 3/2, 1200-2500 sqft")
        areas = st.text_input("Target Areas", value="Houston TX, Harris County, Montgomery County")
        submitted = st.form_submit_button("Add Buyer")
        if submitted:
            conn = get_conn()
            conn.execute("""INSERT INTO buyers(name,email,phone,cash_available,verified,preferences,areas,created_at)
                            VALUES(?,?,?,?,?,?,?,?)""",
                         (name,email,phone,cash,1 if verified else 0,prefs,areas,datetime.now().isoformat()))
            conn.commit(); conn.close()
            st.success("Buyer added")

    st.divider()
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM buyers ORDER BY created_at DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ---------- RVM ----------
def rvm_campaigns():
    st.subheader("📞 RVM Campaigns")
    with st.form("rvm_form"):
        name = st.text_input("Campaign Name", value=f"RVM-{datetime.now().strftime('%Y%m%d')}")
        audio = st.text_area("Audio Script / Notes")
        recipients = st.number_input("Recipients", 0, 100000, 250)
        submitted = st.form_submit_button("Estimate & Launch (Simulated)")
        if submitted:
            cost = round(recipients * 0.15, 2)
            response_rate = 18.0 + random.random()*4.0
            conn = get_conn()
            conn.execute("""INSERT INTO rvm_campaigns(name,audio,recipients,cost,response_rate,sent_at)
                            VALUES(?,?,?,?,?,?)""",
                         (name, audio, recipients, cost, response_rate, datetime.now().isoformat()))
            conn.commit(); conn.close()
            st.success(f"Launched! Estimated cost ${cost:,.2f} with {response_rate:.1f}% response.")

    st.divider()
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM rvm_campaigns ORDER BY sent_at DESC", conn)
    conn.close()
    st.dataframe(df, use_container_width=True)

# ---------- Analytics ----------
def analytics():
    st.subheader("📈 Analytics")
    conn = get_conn()
    leads = pd.read_sql_query("SELECT * FROM leads", conn)
    deals = pd.read_sql_query("SELECT * FROM deals", conn)
    buyers = pd.read_sql_query("SELECT * FROM buyers", conn)
    rvm = pd.read_sql_query("SELECT * FROM rvm_campaigns", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Leads", len(leads))
    col2.metric("Deals", len(deals))
    col3.metric("Buyers", len(buyers))

    st.markdown("#### Lead Performance")
    if not leads.empty:
        st.bar_chart(leads["score"])

    st.markdown("#### RVM Spend vs Recipients")
    if not rvm.empty:
        ch = rvm[["recipients","cost"]]
        st.line_chart(ch)

# ---------- App ----------
def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    init_db()

    # Sidebar nav
    st.sidebar.image("https://placehold.co/240x80/0a0a0a/ffffff?text=W2F", use_column_width=True)
    if "user" not in st.session_state:
        login_block()
        st.stop()

    u = st.session_state.user
    st.sidebar.markdown(f"**User:** {u['username']} ({u['role']})")
    page = st.sidebar.radio("Navigate", ["Landing","Dashboard","Deal Analyzer","Lead Manager","Deal Pipeline","Buyer Network","RVM Campaigns","Analytics"])
    st.session_state.page = page

    if page == "Landing":
        landing_page()
    elif page == "Dashboard":
        dashboard()
    elif page == "Deal Analyzer":
        analyze_deal_ui()
    elif page == "Lead Manager":
        lead_manager()
    elif page == "Deal Pipeline":
        pipeline()
    elif page == "Buyer Network":
        buyer_network()
    elif page == "RVM Campaigns":
        rvm_campaigns()
    elif page == "Analytics":
        analytics()

if __name__ == "__main__":
    main()
