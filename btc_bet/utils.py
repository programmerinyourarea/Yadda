from db import db, redis_client
from bson import ObjectId
from decimal import Decimal

async def get_bet_by_id(bet_id: str):
    cache_key = f"bet:{bet_id}"
    cached = await redis_client.hgetall(cache_key)
    if cached:
        return cached

    doc = await db.bets.find_one({"_id": ObjectId(bet_id)})
    if doc:
        doc["_id"] = str(doc["_id"])
        await redis_client.hset(cache_key, mapping=doc)
        return doc
    return None
