
from datetime import datetime
from pathlib import Path

def _pdf_available():
    try:
        import reportlab
        return True
    except Exception:
        return False

def _make_pdf(text: str, out_path: Path):
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(out_path), pagesize=LETTER)
    width, height = LETTER
    x, y = 72, height - 72
    for line in text.splitlines():
        c.drawString(x, y, line[:95]); y -= 14
        if y < 72: c.showPage(); y = height - 72
    c.save()

LEGAL = ("This document is for negotiation purposes only and does not constitute legal advice. "
        "All parties should consult independent counsel.")

def loi_text(d: dict) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    return f"""LETTER OF INTENT
Date: {today}

Buyer: {d.get('buyer_name','')}
Seller: {d.get('seller_name','')}
Property: {d.get('address','')}

Purchase Price: ${d.get('price',0):,.0f}
Earnest Money: ${d.get('earnest',1000):,.0f}
Closing: {d.get('closing_days',21)} days or sooner

Terms:
- As-Is purchase; no seller repairs
- Inspection contingency {d.get('inspection_days',7)} business days
- Clear, marketable title
- No broker commissions unless agreed in writing
- Assignment permitted

This LOI is non-binding.

{LEGAL}
"""

def contract_text(d: dict) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    return f"""PURCHASE AND SALE AGREEMENT
Date: {today}

Buyer: {d.get('buyer_name','')}
Seller: {d.get('seller_name','')}
Property: {d.get('address','')}

Purchase Price: ${d.get('price',0):,.0f}
Earnest Money: ${d.get('earnest',1000):,.0f} within 48 hours
Closing Date: {d.get('closing_date','TBD')}

Key Terms:
1. Property sold AS-IS; access for inspection
2. Contingencies: {', '.join(d.get('contingencies', ['Inspection']))}
3. Title conveyed free of liens
4. Assignments permitted
5. Default per state law
6. Standard disclosures as applicable

{LEGAL}
"""

def write_doc(text: str, base_name: str, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    if _pdf_available():
        pdf = out_dir / f"{base_name}.pdf"
        _make_pdf(text, pdf); return pdf
    txt = out_dir / f"{base_name}.txt"
    txt.write_text(text, encoding="utf-8"); return txt
