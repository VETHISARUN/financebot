import os
from datetime import datetime
import gspread
import logging
from typing import List, Dict, Optional, Any

# ===========================
# CONFIGURATION
# ===========================
SHEET_NAME = os.environ.get("SHEET_NAME", "SPEND_BOT_TRACK")
CREDS_PATH = os.environ.get("GOOGLE_CREDS", "credentials.json")

# Global placeholders
_gc: Optional[gspread.Client] = None
_sh: Optional[gspread.Spreadsheet] = None

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# ===========================
# HELPER FUNCTIONS
# ===========================
def _ensure_client() -> (gspread.Client, gspread.Spreadsheet):
    global _gc, _sh
    if _gc is None:
        logging.info("Initializing Google Sheets client...")
        try:
            _gc = gspread.service_account(filename=CREDS_PATH)
        except Exception as e:
            logging.error(f"Failed to initialize client: {e}")
            raise
    if _sh is None:
        try:
            _sh = _gc.open(SHEET_NAME)
        except Exception as e:
            logging.error(f"Failed to open spreadsheet {SHEET_NAME}: {e}")
            raise
    return _gc, _sh

def ensure_month_sheet(month_name: str):
    """Ensure worksheet for the month exists; returns the worksheet object"""
    _, sh = _ensure_client()
    titles = [ws.title for ws in sh.worksheets()]
    if month_name not in titles:
        logging.info(f"Worksheet for {month_name} not found. Creating new sheet...")
        try:
            sh.add_worksheet(title=month_name, rows="500", cols="10")
        except Exception as e:
            logging.error(f"Failed to add worksheet: {e}")
            raise
    return sh.worksheet(month_name)

def _normalize_category(cat: Any) -> str:
    if not cat or not isinstance(cat, str):
        return "uncategorized"
    return cat.strip().lower()

def _parse_amount(value: Any) -> float:
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0.0

# ===========================
# TRANSACTION FUNCTIONS
# ===========================
def append_transaction(row: List[Any]):
    """Append a row: [date, category, amount, notes, user]"""
    month = datetime.now().strftime("%B")
    ws = ensure_month_sheet(month)

    # Ensure header exists
    try:
        if not ws.acell("A1").value:
            logging.info("Adding header row")
            ws.append_row(["Date", "Category", "Amount", "Notes", "User"])
    except Exception as e:
        logging.warning(f"Failed to check header: {e}")

    # Append row
    try:
        ws.append_row(row)
        logging.info(f"Row appended: {row}")
    except Exception as e:
        logging.error(f"Failed to append row: {e}")

def get_records_for_month(month: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return all records for a given month"""
    _, sh = _ensure_client()
    if month is None:
        month = datetime.now().strftime("%B")

    try:
        ws = sh.worksheet(month)
        records = ws.get_all_records()
        logging.info(f"Fetched {len(records)} records for {month}")
        return records
    except Exception as e:
        logging.warning(f"No worksheet found for {month} or failed to fetch: {e}")
        return []

def aggregate_by_category(month: Optional[str] = None) -> Dict[str, float]:
    """Aggregate total amount by category"""
    recs = get_records_for_month(month)
    agg: Dict[str, float] = {}

    for r in recs:
        cat = _normalize_category(r.get("Category"))
        amt = _parse_amount(r.get("Amount"))

        # Nested logging for debugging
        if cat not in agg:
            logging.debug(f"New category encountered: {cat}")
        agg[cat] = agg.get(cat, 0) + amt

    # Extra processing: sort by amount descending
    agg_sorted = dict(sorted(agg.items(), key=lambda x: x[1], reverse=True))
    logging.info(f"Aggregated categories: {agg_sorted}")
    return agg_sorted

# ===========================
# EXTRA FUNCTIONS TO ADD COMPLEXITY
# ===========================
def get_total_spent(month: Optional[str] = None) -> float:
    """Return total amount spent in the month"""
    recs = get_records_for_month(month)
    total = sum(_parse_amount(r.get("Amount")) for r in recs)
    logging.info(f"Total spent in {month or 'current month'}: {total}")
    return total

def category_report(month: Optional[str] = None) -> str:
    """Return a string report for category-wise spending"""
    agg = aggregate_by_category(month)
    report_lines = ["Category Report:"]
    for cat, amt in agg.items():
        report_lines.append(f"{cat}: {amt:.2f}")
    report_lines.append(f"Total: {get_total_spent(month):.2f}")
    report = "\n".join(report_lines)
    logging.info(f"Generated report:\n{report}")
    return report

def reset_sheet(month: Optional[str] = None):
    """Delete all records in a sheet except header"""
    _, sh = _ensure_client()
    if month is None:
        month = datetime.now().strftime("%B")
    try:
        ws = sh.worksheet(month)
        all_values = ws.get_all_values()
        if len(all_values) > 1:
            ws.delete_rows(2, len(all_values))
            logging.info(f"Cleared {len(all_values)-1} rows in {month}")
    except Exception as e:
        logging.warning(f"Failed to reset sheet {month}: {e}")

# ===========================
# MAIN EXECUTION (if run directly)
# ===========================
if __name__ == "__main__":
    logging.info("Running module directly for testing...")
    test_row = [datetime.now().strftime("%Y-%m-%d"), "Food", 150, "Lunch", "User1"]
    append_transaction(test_row)
    print(category_report())
