import os
from datetime import datetime
import gspread

SHEET_NAME = os.environ.get("SHEET_NAME", "SPEND_BOT_TRACK")
CREDS_PATH = os.environ.get("GOOGLE_CREDS", "credentials.json")

_gc = None
_sh = None

def _ensure_client():
    global _gc, _sh
    if _gc is None:
        _gc = gspread.service_account(filename=CREDS_PATH)
    if _sh is None:
        _sh = _gc.open(SHEET_NAME)
    return _gc, _sh

def ensure_month_sheet(month_name: str):
    _, sh = _ensure_client()
    titles = [ws.title for ws in sh.worksheets()]
    if month_name not in titles:
        sh.add_worksheet(title=month_name, rows="500", cols="10")
    return sh.worksheet(month_name)

def append_transaction(row: list):
    """Append a row: [date, category, amount, notes, user]"""
    month = datetime.now().strftime("%B")
    ws = ensure_month_sheet(month)
    if not ws.acell("A1").value:
        ws.append_row(["Date", "Category", "Amount", "Notes", "User"])
    ws.append_row(row)

def get_records_for_month(month=None):
    _, sh = _ensure_client()
    if month is None:
        month = datetime.now().strftime("%B")
    try:
        ws = sh.worksheet(month)
    except Exception:
        return []
    return ws.get_all_records()

def aggregate_by_category(month=None):
    recs = get_records_for_month(month)
    agg = {}
    for r in recs:
        cat = (r.get("Category") or "uncategorized").strip().lower()
        try:
            amt = float(r.get("Amount") or 0)
        except (ValueError, TypeError):
            amt = 0
        agg[cat] = agg.get(cat, 0) + amt
    return dict(sorted(agg.items(), key=lambda x: x[1], reverse=True))

def category_report(month=None):
    agg = aggregate_by_category(month)
    total = sum(agg.values())
    lines = [f"{cat}: {amt:.2f}" for cat, amt in agg.items()]
    lines.append(f"Total: {total:.2f}")
    return "\n".join(lines)

if __name__ == "__main__":
    test_row = [datetime.now().strftime("%Y-%m-%d"), "Food", 150, "Lunch", "User1"]
    append_transaction(test_row)
    print(category_report())
