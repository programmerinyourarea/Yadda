from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
@dataclass
class User:
    user_id: str
    balance: Decimal = 1000.00
    active_bets: int = 0
    created_at: str = datetime.utcnow().isoformat()

    def to_dict(self):
        return asdict(self)
@dataclass
class Bet:
    user_id: str
    guess: str
    block_height: int
    status: str = "pending"
    created_at: str = datetime.utcnow().isoformat()

    def to_dict(self):
        return asdict(self)

