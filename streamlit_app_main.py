"""
🏠 WTF - Wholesale2Flip Platform
Complete Real Estate Wholesaling Platform
Ready for Streamlit Community Cloud Deployment
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import io
import json
import time
import random
import math

# Must be first Streamlit command
st.set_page_config(
    page_title="WTF — Wholesale on Steroids", 
    page_icon="🏠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# -----------------------------
# Global Configuration
# -----------------------------
APP_VERSION = "2.1.0"
DB_PATH = "wtf_platform.db"

# Demo users for authentication
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Admin User"},
    "demo": {"password": "demo", "role": "demo", "name": "Demo User"},
    "wholesaler": {"password": "demo123", "role": "wholesaler", "name": "Wholesaler Pro"},
    "investor": {"password": "invest123", "role": "investor", "name": "Investor"}
}

# Sample property data
SAMPLE_PROPERTY = {
    "address": "21372 W Memorial Dr, Porter, TX 77365",
    "owner": "EDGAR LORI G",
    "est_value": 267000,
    "sqft": 1643,
    "beds": 3,
    "baths": 2,
    "year_built": 1969,
    "rent": 1973,
    "mortgage_balance": 27986,
    "equity": 239014,
    "taxes": 1497,
    "condition": "Good",
    "state": "TX",
    "city": "Porter",
    "type": "SFR"
}

# Sample buyers database
SAMPLE_BUYERS = [
    {
        "id": "B001", 
        "name": "Empire Capital Partners", 
        "verified": True, 
        "cash": 2500000,
        "min_price": 75000, 
        "max_price": 300000, 
        "states": ["TX", "FL", "GA"], 
        "types": ["SFR"], 
        "close_days": 14,
        "email": "deals@empirecapital.com",
        "phone": "(713) 555-0001"
    },
    {
        "id": "B002", 
        "name": "Pinnacle Real Estate Group", 
        "verified": True, 
        "cash": 1800000,
        "min_price": 90000, 
        "max_price": 400000, 
        "states": ["TX", "AZ", "NC", "SC"], 
        "types": ["SFR", "Townhome"], 
        "close_days": 21,
        "email": "acquisitions@pinnaclereg.com",
        "phone": "(832) 555-0002"
    },
    {
        "id": "B003", 
        "name": "Sunbelt Rental Fund", 
        "verified": True, 
        "cash": 3200000,
        "min_price": 60000, 
        "max_price": 240000, 
        "states": ["TX", "AL", "MS", "TN", "FL"], 
        "types": ["SFR"], 
        "close_days": 28,
        "email": "invest@sunbeltfund.com",
        "phone": "(281) 555-0003"
    },
    {
        "id": "B004", 
        "name": "Great Lakes Holdings", 
        "verified": False, 
        "cash": 900000,
        "min_price": 50000, 
        "max_price": 180000, 
        "states": ["OH", "MI", "IN", "IL"], 
        "types": ["SFR", "Duplex"], 
        "close_days": 30,
        "email": "deals@greatlakesholdings.com",
        "phone": "(312) 555-0004"
    }
]

# -----------------------------
# Styling & Theme
# -----------------------------
def load_css():
    """Load custom CSS styling"""
    css = """
    <style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu, header, footer, .stDeployButton {
        visibility: hidden;
    }
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
        font-weight: 600;
    }
    
    /* Hero section */
    .hero {
        background: linear-gradient(135deg, #8B5CF6 0%, #10B981 30%, #3B82F6 60%, #F59E0B 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        margin-bottom: 2rem;
    }
    
    /* Card components */
    .card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(139,92,246,0.15), rgba(16,185,129,0.10));
        border: 1px solid rgba(139,92,246,0.4);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        color: #fff;
        margin-bottom: 1rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    
    .metric-label {
        color: #cbd5e1;
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #8B5CF6, #10B981) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 16px rgba(139,92,246,0.3) !important;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .status-new { background: #3B82F6; color: white; }
    .status-hot { background: #EF4444; color: white; }
    .status-warm { background: #F59E0B; color: white; }
    .status-cold { background: #6B7280; color: white; }
    .status-verified { background: #10B981; color: white; }
    
    /* Grade badges */
    .grade-a { background: #10B981; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
    .grade-b { background: #3B82F6; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
    .grade-c { background: #F59E0B; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
    .grade-d { background: #EF4444; color: white; padding: 0.25rem 0.5rem; border-radius: 4px; font-weight: bold; }
    
    /* Text colors */
    .text-primary { color: #8B5CF6; }
    .text-success { color: #10B981; }
    .text-warning { color: #F59E0B; }
    .text-danger { color: #EF4444; }
    .text-muted { color: #6B7280; }
    .text-light { color: #cbd5e1; }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(0,0,0,0.3);
    }
    
    /* Data tables */
    .stDataFrame {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
    
    /* Forms */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        background-color: rgba(255,255,255,0.1) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 8px !important;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background-color: rgba(16,185,129,0.1);
        border: 1px solid rgba(16,185,129,0.3);
        color: #10B981;
    }
    
    .stError {
        background-color: rgba(239,68,68,0.1);
        border: 1px solid rgba(239,68,68,0.3);
        color: #EF4444;
    }
    
    .stWarning {
        background-color: rgba(245,158,11,0.1);
        border: 1px solid rgba(245,158,11,0.3);
        color: #F59E0B;
    }
    
    .stInfo {
        background-color: rgba(59,130,246,0.1);
        border: 1px solid rgba(59,130,246,0.3);
        color: #3B82F6;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# -----------------------------
# Database Functions
# -----------------------------
@st.cache_resource
def init_database():
    """Initialize SQLite database with tables"""
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Leads table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT,
                email TEXT,
                address TEXT,
                city TEXT,
                state TEXT,
                zip_code TEXT,
                status TEXT DEFAULT 'New',
                source TEXT,
                score INTEGER DEFAULT 60,
                motivation TEXT,
                equity TEXT,
                timeline TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Deals table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT NOT NULL,
                arv REAL,
                rehab REAL,
                mao70 REAL,
                mao75 REAL,
                grade TEXT,
                strategy TEXT,
                status TEXT DEFAULT 'Analyzing',
                profit_est REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Buyers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buyers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                cash_available REAL,
                verified BOOLEAN DEFAULT 0,
                min_price REAL,
                max_price REAL,
                states TEXT,
                property_types TEXT,
                close_days INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Campaigns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT,
                message TEXT,
                recipients INTEGER,
                cost REAL,
                response_rate REAL,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed demo users
        for username, user_data in DEMO_USERS.items():
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, password, role, name)
                VALUES (?, ?, ?, ?)
            """, (username, user_data["password"], user_data["role"], user_data["name"]))
        
        # Seed sample buyers
        for buyer in SAMPLE_BUYERS:
            cursor.execute("""
                INSERT OR IGNORE INTO buyers 
                (name, email, phone, cash_available, verified, min_price, max_price, states, property_types, close_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                buyer["name"], buyer["email"], buyer["phone"], buyer["cash"],
                buyer["verified"], buyer["min_price"], buyer["max_price"],
                ",".join(buyer["states"]), ",".join(buyer["types"]), buyer["close_days"]
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {e}")
        return False

def get_db_connection():
    """Get database connection"""
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# -----------------------------
# Session State Management
# -----------------------------
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "authenticated": False,
        "user": None,
        "page": "landing",
        "current_property": None,
        "deals": [],
        "leads": [],
        "buyers": SAMPLE_BUYERS.copy(),
        "campaigns": [],
        "recent_actions": []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# -----------------------------
# Authentication
# -----------------------------
def authenticate_user(username, password):
    """Authenticate user against database or demo users"""
    if username in DEMO_USERS and DEMO_USERS[username]["password"] == password:
        return DEMO_USERS[username]
    return None

def login_form():
    """Display login form"""
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("# 🏠 WTF — Wholesale on Steroids")
    st.markdown("### Professional Real Estate Wholesaling Platform")
    st.markdown("*Sign in with demo credentials below*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("#### 🔐 Sign In")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Sign In", use_container_width=True)
            
            if submit:
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.user = {**user, "username": username}
                    st.session_state.page = "dashboard"
                    st.success(f"Welcome, {user['name']}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
    
    with col2:
        st.markdown("#### 🎯 Demo Accounts")
        st.markdown("""
        **Admin Access:**  
        `admin` / `admin123`
        
        **Wholesaler:**  
        `wholesaler` / `demo123`
        
        **Investor:**  
        `investor` / `invest123`
        
        **Demo User:**  
        `demo` / `demo`
        """)

# -----------------------------
# Business Logic Functions
# -----------------------------
def analyze_property(address, arv=None, rehab=0):
    """Analyze property and calculate key metrics"""
    try:
        # Use sample data if address matches
        if address.lower().strip() == SAMPLE_PROPERTY["address"].lower():
            base_data = SAMPLE_PROPERTY.copy()
            est_arv = arv if arv else base_data["est_value"]
        else:
            base_data = {
                "address": address,
                "owner": "Unknown",
                "est_value": arv if arv else 200000,
                "state": "TX",
                "city": "",
                "type": "SFR"
            }
            est_arv = arv if arv else 200000
        
        # Calculate key metrics
        rehab = float(rehab) if rehab else 0
        mao70 = 0.70 * est_arv - rehab
        mao75 = 0.75 * est_arv - rehab
        
        # Profit estimation (wholesale spread)
        profit_est = max(0, mao75 - mao70)
        
        # Grade the deal
        arv_ratio = mao70 / est_arv if est_arv > 0 else 0
        if arv_ratio >= 0.60:
            grade = "A"
        elif arv_ratio >= 0.55:
            grade = "B"
        elif arv_ratio >= 0.50:
            grade = "C"
        else:
            grade = "D"
        
        # Determine strategies
        strategies = []
        if grade in ["A", "B"]:
            strategies.extend(["Wholesale", "Fix & Flip"])
        if grade == "A":
            strategies.append("BRRRR")
        
        result = {
            **base_data,
            "arv": est_arv,
            "rehab": rehab,
            "mao70": round(mao70, 2),
            "mao75": round(mao75, 2),
            "grade": grade,
            "strategies": strategies,
            "profit_est": round(profit_est, 2)
        }
        
        return result
        
    except Exception as e:
        st.error(f"Error analyzing property: {e}")
        return None

def find_matching_buyers(property_data, buyers):
    """Find buyers that match property criteria"""
    matches = []
    
    if not property_data:
        return matches
    
    prop_price = property_data.get("mao70", 0)
    prop_state = property_data.get("state", "")
    prop_type = property_data.get("type", "SFR")
    
    for buyer in buyers:
        # Check price range
        if buyer["min_price"] <= prop_price <= buyer["max_price"]:
            # Check state
            if prop_state in buyer["states"]:
                # Check property type
                if prop_type in buyer["types"]:
                    matches.append({
                        **buyer,
                        "suggested_offer": round(property_data.get("mao75", 0), 2)
                    })
    
    return matches

def calculate_lead_score(motivation, equity, timeline, source):
    """Calculate lead score based on criteria"""
    base_score = 60
    
    # Motivation scoring
    motivation_scores = {"Low": 0, "Medium": 10, "High": 20}
    base_score += motivation_scores.get(motivation, 0)
    
    # Equity scoring
    equity_scores = {"<10%": 0, "10-30%": 10, "30-50%": 15, "50%+": 20}
    base_score += equity_scores.get(equity, 0)
    
    # Timeline scoring
    timeline_scores = {"ASAP": 15, "30-60 days": 8, "60+ days": 0}
    base_score += timeline_scores.get(timeline, 0)
    
    # Source scoring
    source_scores = {
        "Direct Mail": 5, "RVM": 8, "Cold Calling": 3, 
        "PPC": 12, "Referral": 15, "Other": 0
    }
    base_score += source_scores.get(source, 0)
    
    return min(100, base_score)  # Cap at 100

# -----------------------------
# Page Components
# -----------------------------
def show_landing_page():
    """Display landing/marketing page"""
    st.markdown('<div class="hero">', unsafe_allow_html=True)
    st.markdown("# 🏠 WTF — Wholesale on Steroids")
    st.markdown("## The Complete Real Estate Wholesaling Platform")
    st.markdown("*Analyze deals, manage leads, connect with buyers, and close more deals faster.*")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">15,000+</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Deals Analyzed</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">$50M+</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Pipeline Value</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">2,500+</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Active Users</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">98%</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Satisfaction</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Features
    st.markdown("## 🚀 Platform Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🧮 Deal Analyzer
        - ARV calculations
        - MAO (70% & 75% rules)
        - Deal grading (A-D)
        - Strategy recommendations
        - Profit projections
        """)
    
    with col2:
        st.markdown("""
        ### 📇 CRM System
        - Lead management
        - Scoring algorithms
        - Contact tracking
        - Pipeline management
        - Follow-up automation
        """)
    
    with col3:
        st.markdown("""
        ### 🤝 Buyer Network
        - Verified cash buyers
        - Automated matching
        - Deal distribution
        - Communication tools
        - Performance tracking
        """)
    
    st.markdown("---")
    
    # Pricing
    st.markdown("## 💰 Pricing Plans")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Starter")
        st.markdown("**$29/month**")
        st.markdown("- Basic deal analysis")
        st.markdown("- Lead management")
        st.markdown("- Email support")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Professional")
        st.markdown("**$79/month**")
        st.markdown("- Advanced analytics")
        st.markdown("- Buyer network access")
        st.markdown("- Automation tools")
        st.markdown("- Priority support")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### Enterprise")
        st.markdown("**$199/month**")
        st.markdown("- Team collaboration")
        st.markdown("- Custom integrations")
        st.markdown("- Dedicated support")
        st.markdown("- White label options")
        st.markdown('</div>', unsafe_allow_html=True)

def show_dashboard():
    """Display main dashboard"""
    user = st.session_state.user
    st.markdown(f"# 📊 Welcome back, {user['name']}!")
    
    # Quick stats
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">$125K</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">YTD Revenue</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">$485K</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Pipeline Value</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">28</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Hot Leads</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">67</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Grade A Deals</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col5:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown('<div class="metric-value">18.5%</div>', unsafe_allow_html=True)
        st.markdown('<div class="metric-label">Conversion Rate</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick actions
    st.markdown("## ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🧮 Analyze New Deal", use_container_width=True):
            st.session_state.page = "analyzer"
            st.rerun()
    
    with col2:
        if st.button("➕ Add New Lead", use_container_width=True):
            st.session_state.page = "leads"
            st.rerun()
    
    with col3:
        if st.button("🤝 View Buyers", use_container_width=True):
            st.session_state.page = "buyers"
            st.rerun()
    
    with col4:
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.page = "analytics"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📋 Recent Deals")
        if st.session_state.deals:
            deals_df = pd.DataFrame(st.session_state.deals[-5:])  # Last 5 deals
            st.dataframe(deals_df[["address", "grade", "mao70", "status"]], use_container_width=True, hide_index=True)
        else:
            st.info("No deals yet. Start by analyzing a property!")
    
    with col2:
        st.markdown("### 📞 Recent Leads")
        if st.session_state.leads:
            leads_df = pd.DataFrame(st.session_state.leads[-5:])  # Last 5 leads
            st.dataframe(leads_df[["name", "phone", "status", "score"]], use_container_width=True, hide_index=True)
        else:
            st.info("No leads yet. Add your first lead!")

def show_deal_analyzer():
    """Display deal analyzer page"""
    st.markdown("# 🧮 Deal Analyzer")
    st.markdown("*Analyze properties and calculate key investment metrics*")
    
    # Analysis form
    with st.form("property_analysis"):
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_input(
                "Property Address", 
                value=SAMPLE_PROPERTY["address"],
                placeholder="Enter property address"
            )
            arv = st.number_input(
                "After Repair Value (ARV)", 
                min_value=0.0, 
                value=float(SAMPLE_PROPERTY["est_value"]),
                step=1000.0,
                format="%.0f"
            )
        
        with col2:
            rehab = st.number_input(
                "Estimated Rehab Cost", 
                min_value=0.0, 
                value=25000.0,
                step=1000.0,
                format="%.0f"
            )
            wholesale_fee = st.number_input(
                "Wholesale Assignment Fee", 
                min_value=0.0, 
                value=10000.0,
                step=1000.0,
                format="%.0f"
            )
        
        submitted = st.form_submit_button("🔍 Analyze Property", use_container_width=True)
    
    if submitted and address and arv:
        with st.spinner("Analyzing property..."):
            time.sleep(1)  # Simulate processing
            
            property_data = analyze_property(address, arv, rehab)
            
            if property_data:
                st.session_state.current_property = property_data
                st.success("✅ Analysis complete!")
                
                # Display results
                st.markdown("## 📊 Analysis Results")
                
                # Key metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.metric("ARV", f"${property_data['arv']:,.0f}")
                
                with col2:
                    st.metric("MAO (70%)", f"${property_data['mao70']:,.0f}")
                
                with col3:
                    st.metric("MAO (75%)", f"${property_data['mao75']:,.0f}")
                
                with col4:
                    st.metric("Est. Profit", f"${property_data['profit_est']:,.0f}")
                
                with col5:
                    grade_class = f"grade-{property_data['grade'].lower()}"
                    st.markdown(f'<span class="{grade_class}">Grade {property_data["grade"]}</span>', unsafe_allow_html=True)
                
                # Strategy recommendations
                st.markdown("### 💡 Strategy Recommendations")
                strategies = property_data.get("strategies", [])
                if strategies:
                    for strategy in strategies:
                        if strategy == "Wholesale":
                            st.markdown("🔄 **Wholesale**: Lock under contract at MAO 70% and assign to buyer")
                        elif strategy == "Fix & Flip":
                            st.markdown("🔨 **Fix & Flip**: Purchase, renovate, and resell for profit")
                        elif strategy == "BRRRR":
                            st.markdown("🏠 **BRRRR**: Buy, renovate, rent, refinance, repeat")
                else:
                    st.markdown("📊 **Analysis Only**: Review metrics and consider alternative strategies")
                
                # Buyer matching
                st.markdown("### 🎯 Matching Buyers")
                matching_buyers = find_matching_buyers(property_data, st.session_state.buyers)
                
                if matching_buyers:
                    for buyer in matching_buyers:
                        with st.container():
                            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                            
                            with col1:
                                verified_badge = "✅" if buyer["verified"] else "⏳"
                                st.markdown(f"**{buyer['name']}** {verified_badge}")
                                st.markdown(f"💰 Cash: ${buyer['cash']:,.0f}")
                            
                            with col2:
                                st.markdown(f"**Suggested Offer**")
                                st.markdown(f"${buyer['suggested_offer']:,.0f}")
                            
                            with col3:
                                st.markdown(f"**Close Time**")
                                st.markdown(f"~{buyer['close_days']} days")
                            
                            with col4:
                                if st.button("📤 Send", key=f"send_{buyer['id']}"):
                                    st.success(f"Deal sent to {buyer['name']}!")
                else:
                    st.warning("⚠️ No matching buyers found. Consider adjusting price or expanding buyer network.")
                
                # Save deal
                if st.button("💾 Save to Pipeline", use_container_width=True):
                    deal_data = {
                        "address": property_data["address"],
                        "arv": property_data["arv"],
                        "rehab": property_data["rehab"],
                        "mao70": property_data["mao70"],
                        "mao75": property_data["mao75"],
                        "grade": property_data["grade"],
                        "profit_est": property_data["profit_est"],
                        "status": "Analyzing",
                        "created_at": datetime.now().isoformat()
                    }
                    st.session_state.deals.append(deal_data)
                    st.success("✅ Deal saved to pipeline!")

def show_lead_manager():
    """Display lead management page"""
    st.markdown("# 📇 Lead Manager")
    st.markdown("*Manage seller leads and track opportunities*")
    
    # Add new lead form
    with st.expander("➕ Add New Lead", expanded=True):
        with st.form("add_lead"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Seller Name*", placeholder="John Smith")
                phone = st.text_input("Phone Number", placeholder="(713) 555-0123")
                email = st.text_input("Email", placeholder="john@email.com")
                address = st.text_input("Property Address*", placeholder="123 Main St, Houston, TX")
            
            with col2:
                status = st.selectbox("Status", ["New", "Contacted", "Warm", "Hot", "Cold", "Closed"])
                source = st.selectbox("Lead Source", ["Direct Mail", "RVM", "Cold Calling", "PPC", "Referral", "Other"])
                motivation = st.selectbox("Seller Motivation", ["Low", "Medium", "High"])
                equity = st.selectbox("Estimated Equity", ["<10%", "10-30%", "30-50%", "50%+"])
                timeline = st.selectbox("Selling Timeline", ["ASAP", "30-60 days", "60+ days"])
            
            notes = st.text_area("Notes", placeholder="Additional information about the lead...")
            
            submitted = st.form_submit_button("💾 Add Lead", use_container_width=True)
            
            if submitted and name and address:
                # Calculate lead score
                score = calculate_lead_score(motivation, equity, timeline, source)
                
                lead_data = {
                    "name": name,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "status": status,
                    "source": source,
                    "motivation": motivation,
                    "equity": equity,
                    "timeline": timeline,
                    "score": score,
                    "notes": notes,
                    "created_at": datetime.now().isoformat()
                }
                
                st.session_state.leads.append(lead_data)
                st.success(f"✅ Lead added with score: {score}")
                st.rerun()
    
    # Display existing leads
    if st.session_state.leads:
        st.markdown("## 📋 Current Leads")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            status_filter = st.selectbox("Filter by Status", ["All"] + ["New", "Contacted", "Warm", "Hot", "Cold", "Closed"])
        with col2:
            source_filter = st.selectbox("Filter by Source", ["All"] + ["Direct Mail", "RVM", "Cold Calling", "PPC", "Referral", "Other"])
        with col3:
            min_score = st.slider("Minimum Score", 0, 100, 60)
        
        # Filter leads
        filtered_leads = st.session_state.leads.copy()
        
        if status_filter != "All":
            filtered_leads = [lead for lead in filtered_leads if lead["status"] == status_filter]
        
        if source_filter != "All":
            filtered_leads = [lead for lead in filtered_leads if lead["source"] == source_filter]
        
        filtered_leads = [lead for lead in filtered_leads if lead["score"] >= min_score]
        
        # Display leads
        if filtered_leads:
            for i, lead in enumerate(filtered_leads):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{lead['name']}**")
                        st.markdown(f"📍 {lead['address']}")
                        if lead['phone']:
                            st.markdown(f"📞 {lead['phone']}")
                    
                    with col2:
                        status_class = f"status-{lead['status'].lower()}"
                        st.markdown(f'<span class="status-badge {status_class}">{lead["status"]}</span>', unsafe_allow_html=True)
                        st.markdown(f"**Score:** {lead['score']}")
                    
                    with col3:
                        st.markdown(f"**Source**")
                        st.markdown(lead['source'])
                    
                    with col4:
                        if st.button("📞 Contact", key=f"contact_{i}"):
                            st.info(f"Opening contact form for {lead['name']}")
                        if st.button("📝 Edit", key=f"edit_{i}"):
                            st.info(f"Edit form for {lead['name']}")
                
                st.markdown("---")
        else:
            st.info("No leads match the current filters.")
    else:
        st.info("No leads yet. Add your first lead above!")

def show_buyer_network():
    """Display buyer network page"""
    st.markdown("# 🤝 Buyer Network")
    st.markdown("*Manage your verified cash buyer database*")
    
    # Buyer stats
    verified_buyers = [b for b in st.session_state.buyers if b["verified"]]
    total_cash = sum(b["cash"] for b in st.session_state.buyers)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Buyers", len(st.session_state.buyers))
    
    with col2:
        st.metric("Verified Buyers", len(verified_buyers))
    
    with col3:
        st.metric("Total Cash Available", f"${total_cash:,.0f}")
    
    with col4:
        avg_close = sum(b["close_days"] for b in st.session_state.buyers) / len(st.session_state.buyers)
        st.metric("Avg Close Time", f"{avg_close:.0f} days")
    
    st.markdown("---")
    
    # Add new buyer
    with st.expander("➕ Add New Buyer"):
        with st.form("add_buyer"):
            col1, col2 = st.columns(2)
            
            with col1:
                buyer_name = st.text_input("Buyer Name*", placeholder="ABC Capital Partners")
                buyer_email = st.text_input("Email*", placeholder="deals@abccapital.com")
                buyer_phone = st.text_input("Phone", placeholder="(713) 555-0100")
                cash_available = st.number_input("Cash Available", min_value=0.0, value=500000.0, step=50000.0)
            
            with col2:
                verified = st.checkbox("Verified Buyer", value=True)
                min_price = st.number_input("Minimum Price", min_value=0.0, value=75000.0, step=5000.0)
                max_price = st.number_input("Maximum Price", min_value=0.0, value=300000.0, step=5000.0)
                close_days = st.number_input("Typical Close Days", min_value=1, value=21, step=1)
            
            target_states = st.multiselect("Target States", ["TX", "FL", "GA", "NC", "SC", "TN", "AL", "MS", "OH", "MI", "IN", "IL"], default=["TX"])
            property_types = st.multiselect("Property Types", ["SFR", "Townhome", "Duplex", "Triplex", "4-plex", "Commercial"], default=["SFR"])
            
            submitted = st.form_submit_button("💾 Add Buyer", use_container_width=True)
            
            if submitted and buyer_name and buyer_email:
                new_buyer = {
                    "id": f"B{len(st.session_state.buyers)+1:03d}",
                    "name": buyer_name,
                    "email": buyer_email,
                    "phone": buyer_phone,
                    "cash": cash_available,
                    "verified": verified,
                    "min_price": min_price,
                    "max_price": max_price,
                    "states": target_states,
                    "types": property_types,
                    "close_days": close_days
                }
                st.session_state.buyers.append(new_buyer)
                st.success(f"✅ Added {buyer_name} to buyer network!")
                st.rerun()
    
    # Display buyers
    st.markdown("## 👥 Current Buyers")
    
    for buyer in st.session_state.buyers:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                verified_badge = "✅" if buyer["verified"] else "⏳"
                st.markdown(f"**{buyer['name']}** {verified_badge}")
                if buyer.get("email"):
                    st.markdown(f"📧 {buyer['email']}")
                if buyer.get("phone"):
                    st.markdown(f"📞 {buyer['phone']}")
            
            with col2:
                st.markdown(f"**Cash Available**")
                st.markdown(f"${buyer['cash']:,.0f}")
                st.markdown(f"**Close Time:** {buyer['close_days']} days")
            
            with col3:
                st.markdown(f"**Buy Box**")
                st.markdown(f"${buyer['min_price']:,.0f} - ${buyer['max_price']:,.0f}")
                st.markdown(f"**States:** {', '.join(buyer['states'])}")
            
            with col4:
                if st.button("📤 Send Deal", key=f"send_deal_{buyer['id']}"):
                    st.info(f"Opening deal sender for {buyer['name']}")
                if st.button("✏️ Edit", key=f"edit_buyer_{buyer['id']}"):
                    st.info(f"Edit form for {buyer['name']}")
        
        st.markdown("---")

def show_analytics():
    """Display analytics and reporting page"""
    st.markdown("# 📈 Analytics & Reports")
    st.markdown("*Track performance and identify trends*")
    
    # Sample data for charts
    deals_data = pd.DataFrame(st.session_state.deals) if st.session_state.deals else pd.DataFrame({
        "grade": ["A", "B", "C", "D", "A", "B"],
        "mao70": [150000, 120000, 100000, 80000, 180000, 140000],
        "status": ["Analyzing", "Negotiating", "Under Contract", "Closed", "Analyzing", "Negotiating"]
    })
    
    leads_data = pd.DataFrame(st.session_state.leads) if st.session_state.leads else pd.DataFrame({
        "score": [85, 72, 91, 68, 88, 95, 75],
        "source": ["Direct Mail", "RVM", "PPC", "Cold Calling", "Direct Mail", "Referral", "RVM"],
        "status": ["Hot", "Warm", "Hot", "Cold", "Hot", "Hot", "Warm"]
    })
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_deals = len(deals_data)
        st.metric("Total Deals", total_deals)
    
    with col2:
        grade_a_deals = len(deals_data[deals_data["grade"] == "A"]) if not deals_data.empty and "grade" in deals_data else 0
        st.metric("Grade A Deals", grade_a_deals)
    
    with col3:
        total_leads = len(leads_data)
        st.metric("Total Leads", total_leads)
    
    with col4:
        hot_leads = len(leads_data[leads_data["status"] == "Hot"]) if not leads_data.empty and "status" in leads_data else 0
        st.metric("Hot Leads", hot_leads)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Deals by Grade")
        if not deals_data.empty and "grade" in deals_data:
            grade_counts = deals_data["grade"].value_counts()
            fig = px.pie(values=grade_counts.values, names=grade_counts.index, title="Deal Distribution by Grade")
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No deal data available for chart")
    
    with col2:
        st.markdown("### 📈 Lead Score Distribution")
        if not leads_data.empty and "score" in leads_data:
            fig = px.histogram(leads_data, x="score", nbins=10, title="Lead Score Distribution")
            fig.update_layout(xaxis_title="Lead Score", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No lead data available for chart")
    
    # Tables
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💰 Top Deals by Value")
        if not deals_data.empty and "mao70" in deals_data:
            top_deals = deals_data.nlargest(5, "mao70")[["address", "grade", "mao70", "status"]] if "address" in deals_data else deals_data.head()
            st.dataframe(top_deals, use_container_width=True, hide_index=True)
        else:
            st.info("No deal data available")
    
    with col2:
        st.markdown("### 🔥 Highest Scoring Leads")
        if not leads_data.empty and "score" in leads_data:
            top_leads = leads_data.nlargest(5, "score")[["name", "score", "status", "source"]] if "name" in leads_data else leads_data.head()
            st.dataframe(top_leads, use_container_width=True, hide_index=True)
        else:
            st.info("No lead data available")

# -----------------------------
# Navigation & Main App
# -----------------------------
def show_sidebar():
    """Display sidebar navigation"""
    with st.sidebar:
        st.markdown("# 🏠 WTF Platform")
        st.markdown(f"**Version:** {APP_VERSION}")
        
        if st.session_state.authenticated:
            user = st.session_state.user
            st.markdown(f"**Welcome:** {user['name']}")
            st.markdown(f"**Role:** {user['role'].title()}")
            
            st.markdown("---")
            
            # Navigation
            pages = {
                "dashboard": "📊 Dashboard",
                "analyzer": "🧮 Deal Analyzer", 
                "leads": "📇 Lead Manager",
                "buyers": "🤝 Buyer Network",
                "analytics": "📈 Analytics"
            }
            
            for page_key, page_name in pages.items():
                if st.button(page_name, use_container_width=True, key=f"nav_{page_key}"):
                    st.session_state.page = page_key
                    st.rerun()
            
            st.markdown("---")
            
            if st.button("🚪 Sign Out", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.user = None
                st.session_state.page = "landing"
                st.rerun()
        else:
            st.markdown("*Please sign in to access the platform*")

def main():
    """Main application function"""
    # Load CSS
    load_css()
    
    # Initialize database and session state
    init_database()
    init_session_state()
    
    # Show sidebar
    show_sidebar()
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        if st.session_state.page == "landing":
            show_landing_page()
        login_form()
    else:
        page = st.session_state.page
        
        if page == "dashboard":
            show_dashboard()
        elif page == "analyzer":
            show_deal_analyzer()
        elif page == "leads":
            show_lead_manager()
        elif page == "buyers":
            show_buyer_network()
        elif page == "analytics":
            show_analytics()
        else:
            show_dashboard()

# -----------------------------
# App Entry Point
# -----------------------------
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error("🚨 Application Error")
        st.exception(e)
        st.markdown("### 🛠️ Troubleshooting")
        st.markdown("1. Refresh the page")
        st.markdown("2. Clear browser cache")
        st.markdown("3. Check browser console for errors")
        st.markdown("4. Ensure all dependencies are installed")