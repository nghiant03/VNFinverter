from decimal import Decimal
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from vnfinverter.statement import Statement, Account

DATE_PATTERNS = {
    "from_date": r"Từ ngày/\s*From:\s*(\d{2}/\d{2}/\d{4})",
    "to_date": r"Đến ngày/\s*To:\s*(\d{2}/\d{2}/\d{4})",
}

ACCOUNT_PATTERNS = {
    "name": r"Tên khách hàng/\s*Customer name:\s*([^\n]+)\s*Loại tiền/\s*Currency:",
    "currency": r"Loại tiền/\s*Currency:\s*([A-Z]{2,4})\s*Số ID khách hàng/\s*Customer ID:",
    "id": r"Số ID khách hàng/\s*Customer ID:\s*([^\n]+)\s*Số tài khoản/\s*Account no\.:?",
    "account_no": r"Số tài khoản/\s*Account no\.:?\s*([0-9]+)\s",
    "account_type": r"Loại tài khoản/\s*Type of account:\s*([^\n]+)",
    "address_left": r"^(.*?)\s*(?:Loại tài khoản/|Loại tài khoản|Type of account)\b",
    "address_right": r"Địa chỉ/\s*Address:\s*([\s\S]*?)\nTên tài khoản/\s*Account name:",
    "account_name": r"Tên tài khoản/\s*Account name:\s*([^\n]+)",
}

def parse_pdf(path: Path) -> Statement:
    full_table = []
    columns = None
    account = None
    dates = None

    with pdfplumber.open(path) as pdf:
        page0 = pdf.pages[0]
        text = page0.extract_text()
        start = re.search(r"BANK STATEMENT/ DEBIT - CREDIT TRANSACTION", text, flags=re.I)
        text = text[start.end():] if start else text

        account = Account(**extract_account(text))
        dates = extract_dates(text)

        table = page0.extract_table()
        assert table is not None, "Table not found in first page!"
        columns = table.pop(0)
        
        result = validate_table(columns, table)
        assert result == -1, f"{table[result]} does not fit header of length {len(columns)}"
        
        full_table.extend(table)
        for i in range(1, len(pdf.pages) - 1):
            table = pdf.pages[i].extract_table()
            if table:
                assert result == -1, f"{table[result]} does not fit header of length {len(columns)}"
                full_table.extend(table)

        table = pdf.pages[-1].extract_table()
        assert table is not None, "Table not found in last page!"
        optional_bal = table.pop(-1)[-1]
        ledger_bal = float(optional_bal.replace(",", ".")) if optional_bal else 0
        ledger_bal = Decimal(ledger_bal)
    
    data = pd.DataFrame(full_table, columns=columns)

    return Statement(account=account, data=data, ledger_bal=ledger_bal, **dates)



def grab(pat, text, flags=None):
    m = re.search(pat, text, flags) if flags else re.search(pat, text)
    return m.group(1).strip(" .") if m else ""

def extract_account(text) -> Dict[str, Any]:
    out = {
        "name": grab(ACCOUNT_PATTERNS["name"], text),
        "currency": grab(ACCOUNT_PATTERNS["currency"], text),
        "id": grab(ACCOUNT_PATTERNS["id"], text),
        "account_no": grab(ACCOUNT_PATTERNS["account_no"], text),
        "account_type": grab(ACCOUNT_PATTERNS["account_type"], text),
        "account_name": grab(ACCOUNT_PATTERNS["account_name"], text),
    }
    left = grab(ACCOUNT_PATTERNS["address_left"], text, re.M)
    right = grab(ACCOUNT_PATTERNS["address_right"], text)
    address = ", ".join([s for s in (left, right) if s])
    out["address"] = address.strip(" ,.")
    return out

def extract_dates(text):
    return {
        "from_date": datetime.strptime(grab(DATE_PATTERNS["from_date"], text), "%d/%m/%Y"),
        "to_date": datetime.strptime(grab(DATE_PATTERNS["to_date"], text), "%d/%m/%Y"),
    }

def validate_table(columns: List[str | None], table: List[List[str | None]]) -> int:
    columns_length = len(columns)
    for i, row in enumerate(table):
        if len(row) > columns_length: 
            return i

    return -1
