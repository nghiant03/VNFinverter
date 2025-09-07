import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal
from typing import Tuple
from zoneinfo import ZoneInfo

import pandas as pd
from ofxtools.header import make_header
from ofxtools.models import (
    BANKACCTFROM,
    BANKMSGSRSV1,
    BANKTRANLIST,
    LEDGERBAL,
    SIGNONMSGSRSV1,
    SONRS,
    STATUS,
    STMTRS,
    STMTTRN,
    STMTTRNRS,
)
from ofxtools.models.ofx import OFX

from vnfinverter.statement import Statement


def to_ofx(statement: Statement) -> bytes:
    ledger_bal = LEDGERBAL(balamt=statement.ledger_bal, dtasof=statement.to_date)
    account = BANKACCTFROM(bankid="1903", acctid=statement.account.account_no, accttype="CHECKING")
    transaction_list = []
    for _, row in statement.data.iterrows():
        transaction_type, amount = transaction_data(row)
        transaction = STMTTRN(
            trntype=transaction_type,
            dtposted=datetime.strptime(
                row["Ngày giao dịch (1)\nTransaction Date"], "%d/%m/%Y"
            ).astimezone(ZoneInfo("Asia/Ho_Chi_Minh")),
            trnamt=amount,
            fitid=row["Số bút toán\nTransaction No"],
            name=row["Đối tác\nRemitter"]
            if row["Đối tác\nRemitter"] != ""
            else row["NH Đối tác\nRemitter Bank"],
        )
        transaction_list.append(transaction)

    bank_transaction = BANKTRANLIST(
        dtstart=statement.from_date, dtend=statement.to_date, *transaction_list
    )
    statement_response = STMTRS(
        curdef=statement.account.currency,
        bankacctfrom=account,
        ledgerbal=ledger_bal,
        banktranlist=bank_transaction,
    )
    status = STATUS(code=0, severity="INFO")
    statement_wrapper = STMTTRNRS(status=status, trnuid="5678", stmtrs=statement_response)
    bank_message = BANKMSGSRSV1(statement_wrapper)
    response = SONRS(
        status=status,
        language="VIE",
        dtserver=datetime.now().astimezone(ZoneInfo("Asia/Ho_Chi_Minh")),
    )
    signon = SIGNONMSGSRSV1(sonrs=response)
    ofx = OFX(signonmsgsrsv1=signon, bankmsgsrsv1=bank_message)
    root = ofx.to_etree()
    message = ET.tostring(root).decode()
    header = str(make_header(version="220"))
    ofx_content = message + header
    ofx_content = ofx_content.encode("utf-8")
    return ofx_content


def transaction_data(transaction: pd.Series) -> Tuple[str, Decimal]:
    if pd.notna(transaction["Nợ TKTT\nDebit"]) and transaction["Nợ TKTT\nDebit"] != "":
        return "DEBIT", Decimal(transaction["Nợ TKTT\nDebit"].replace(",", ""))

    return "CREDIT", Decimal(transaction["Có TKTT\nCredit"].replace(",", ""))
