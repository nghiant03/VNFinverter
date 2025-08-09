import pandas as pd
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Account:
    name: str
    id: int
    address: str
    currency: str
    account_type: str
    account_no: int
    account_name: str

@dataclass
class Statement:
    account: Account
    data: pd.DataFrame
    from_date: datetime
    to_date: datetime
