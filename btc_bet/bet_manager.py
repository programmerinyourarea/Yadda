from bson import ObjectId
from models import Bet
from db import db, redis_client
from decimal import Decimal


async def place_bet(user_id: str, guess: str, current_height: int):
    pending_key = f"user:{user_id}:pending_bets"
    count = int(await redis_client.get(pending_key) or 0)

    if count >= 5:
        print(f"[DENIED] User {user_id} has 5 unresolved bets.")
        return None

    bet = Bet(user_id=user_id, guess=guess, block_height=current_height + 1)
    bet_dict = bet.to_dict()
    bet_id = str(ObjectId())

    # WRITE-THROUGH: Redis + MongoDB
    await redis_client.hset(f"bet:{bet_id}", mapping=bet_dict)
    await db.bets.insert_one({**bet_dict, "_id": ObjectId(bet_id)})

    await redis_client.incr(pending_key)
    await redis_client.expire(pending_key, 600)

    await redis_client.rpush(f"bets:pending:{current_height + 1}", bet_id)

    ##print(f"[ACCEPTED] Bet {bet_id} placed for user {user_id} on '{guess}' at block {current_height + 1}")
    return bet_id
