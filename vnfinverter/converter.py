import pandas as pd
from decimal import Decimal
from datetime import datetime
from ofxtools.header import make_header
from ofxtools.models import BANKTRANLIST, LEDGERBAL, STMTRS, BANKMSGSRSV1, SONRS, STMTTRNRS, BANKACCTFROM, STMTTRN
from vnfinverter.statement import Statement
from typing import Tuple

def to_ofx(statement: Statement) -> str:
    ledger_bal = LEDGERBAL(balamt=statement.ledger_bal, dtaof=statement.to_date)
    account = BANKACCTFROM(bankid="1903", acctid=statement.account.account_no, accttype="CHECKING")
    transaction_list = []
    for _, row in statement.data.iterrows():
        transaction_type, amount = transaction_data(row)
        transaction = STMTTRN(trntype=transaction_type, dtposted=row["Ngày giao dịch (1)\nTransaction Date"], trnamt=amount, fitid=row["Số bút toán\nTransaction No"], name=row["Diễn giải\nDetails"])
        transaction_list.append(transaction)

    bank_transaction =  BANKTRANLIST(dtstart=statement.from_date, dtend=statement.to_date, stmtrn=transaction_list)
    statement_response = STMTRS(curtime=datetime.now(), bankacctfrom=account, ledgerbal=ledger_bal, banktranlist=bank_transaction)
    bank_message = BANKMSGSRSV1(stmtrs=statement_response)
    response = SONRS(status=STMTTRNRS(trnuid="1001", status=bank_message))
    header = str(make_header(version="220"))
    return header + response.to_xml()


def transaction_data(transaction: pd.Series) -> Tuple[str, Decimal]:
    if transaction["Nợ TKTT\nDebit"].notna(): 
        return "DEBIT", Decimal(transaction["Nợ TKTT\nDebit"].replace(",", "."))
    
    return "CREDIT", Decimal(transaction["Có TKTT\nCredit"].replace(",", "."))
