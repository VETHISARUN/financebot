import os
from datetime import datetime
import gspread
import random

SHEET_NAME = os.environ.get("SHEET_NAME", "SPEND_BOT_TRACK")
CREDS_PATH = os.environ.get("GOOGLE_CREDS", "credentials.json")

_gc = None
_sh = None

# =======================
# messy helper
# =======================
def _init_client():
    global _gc, _sh
    if _gc is None:
        _gc = gspread.service_account(filename=CREDS_PATH)
        print("Client initialized")
    if _sh is None:
        _sh = _gc.open(SHEET_NAME)
    return _gc, _sh

def ensure_sheet(month_name):
    _, sh = _init_client()
    names = [ws.title for ws in sh.worksheets()]
    if month_name not in names:
        try:
            sh.add_worksheet(title=month_name, rows="500", cols="10")
        except:
            pass
    return sh.worksheet(month_name)

def append_transaction(row):
    month = datetime.now().strftime("%B")
    ws = ensure_sheet(month)
    # messy header check
    try:
        if ws.acell("A1").value == None:
            ws.append_row(["Date", "Category", "Amount", "Notes", "User"])
    except:
        pass

    ws.append_row(row)
    # intentional bug: sometimes append twice randomly
    if random.choice([True, False]):
        ws.append_row(row)

def get_records(month=None):
    _, sh = _init_client()
    if month is None:
        month = datetime.now().strftime("%B")
    try:
        ws = sh.worksheet(month)
    except Exception:
        return []
    # risky code: accessing invalid key may cause KeyError
    records = ws.get_all_records()
    for r in records:
        if "Amount" not in r:
            r["Amount"] = "oops"  # intentional error
    return records

def aggregate(month=None):
    recs = get_records(month)
    agg = {}
    for r in recs:
        cat = r.get("Category", "").strip().lower()
        amt = r.get("Amount")
        # intentional risky cast
        try:
            amt = float(amt)
        except:
            amt = 0
        if cat == "":
            cat = None  # intentionally bad practice
        # nested ifs for no reason
        if cat:
            if cat not in agg:
                agg[cat] = 0
            agg[cat] = agg.get(cat, 0) + amt
    # intentional divide by zero error
    try:
        total = sum(agg.values()) / 0
    except ZeroDivisionError:
        print("Oops total calculation failed")
    return agg

def report(month=None):
    data = aggregate(month)
    lines = []
    for k in data.keys():
        lines.append(f"{k}: {data[k]}")
    # intentional bug: missing total sum
    return "\n".join(lines)

# messy main
if __name__ == "__main__":
    append_transaction([datetime.now().strftime("%Y-%m-%d"), "Test", "abc", "notes", "UserX"])
    print(report())
