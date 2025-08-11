
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

DB_PATH = Path("data/w2f.db")

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        phone TEXT,
        role TEXT,
        password_hash TEXT,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        source TEXT,
        status TEXT,
        notes TEXT,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS deals(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        address TEXT,
        city TEXT,
        state TEXT,
        lat REAL,
        lon REAL,
        arv REAL,
        rehab REAL,
        mao70 REAL,
        mao75 REAL,
        grade TEXT,
        strategy TEXT,
        submitter_name TEXT,
        submitter_email TEXT,
        submitter_phone TEXT,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS buyers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        cash_available REAL,
        verified INTEGER,
        preferences TEXT,
        areas TEXT,
        created_at TEXT
    )''',
    '''CREATE TABLE IF NOT EXISTS documents(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deal_id INTEGER,
        doc_type TEXT,
        file_path TEXT,
        created_at TEXT
    )'''
]

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    for stmt in SCHEMA:
        cur.execute(stmt)
    conn.commit(); conn.close()

def insert_user(username, email, phone, role, password_hash):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users(username,email,phone,role,password_hash,created_at) VALUES(?,?,?,?,?,?)',
                (username, email, phone, role, password_hash, datetime.utcnow().isoformat()))
    conn.commit(); conn.close()

def add_lead(name, email, phone, source, status, notes):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT INTO leads(name,email,phone,source,status,notes,created_at) VALUES(?,?,?,?,?,?,?)',
                (name,email,phone,source,status,notes,datetime.utcnow().isoformat()))
    conn.commit(); conn.close()

def list_leads():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM leads ORDER BY created_at DESC', conn)
    conn.close(); return df

def add_deal(**kwargs):
    conn = get_conn(); cur = conn.cursor()
    fields = ",".join(kwargs.keys())
    q = ",".join(["?"]*len(kwargs))
    cur.execute(f'INSERT INTO deals({fields}) VALUES({q})', tuple(kwargs.values()))
    conn.commit(); conn.close()

def list_deals():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM deals ORDER BY created_at DESC', conn)
    conn.close(); return df

def add_buyer(**kwargs):
    conn = get_conn(); cur = conn.cursor()
    fields = ",".join(kwargs.keys())
    q = ",".join(["?"]*len(kwargs))
    cur.execute(f'INSERT INTO buyers({fields}) VALUES({q})', tuple(kwargs.values()))
    conn.commit(); conn.close()

def list_buyers():
    conn = get_conn()
    df = pd.read_sql_query('SELECT * FROM buyers ORDER BY created_at DESC', conn)
    conn.close(); return df

def save_document(deal_id, doc_type, file_path):
    conn = get_conn(); cur = conn.cursor()
    cur.execute('INSERT INTO documents(deal_id,doc_type,file_path,created_at) VALUES(?,?,?,?)',
                (deal_id, doc_type, file_path, datetime.utcnow().isoformat()))
    conn.commit(); conn.close()
