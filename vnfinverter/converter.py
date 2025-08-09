from decimal import Decimal
from ofxtools.models import BANKTRANLIST, AVAILBAL, STMTRS, BANKMSGSRSV1, SONRS, STMTTRNRS, BANKACCTFROM
from vnfinverter.statement import Statement

def to_ofx(statement: Statement):
    available_bal = AVAILBAL(balamt=Decimal(statement.))
