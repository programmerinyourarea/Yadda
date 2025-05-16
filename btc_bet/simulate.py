import asyncio
from bet_manager import place_bet
from block_resolver import resolve_block
from db import db
from decimal import Decimal

async def run():
    current_block = 900_000
    user_id = "user123"

    await db.users.update_one(
        {"_id": user_id},
        {"$set": {"balance": 1000}},
        upsert=True
    )

    print("Placing 5 valid bets…")
    for _ in range(5):
        await place_bet(user_id, "f", current_block)

    print("Attempting 6th bet (should fail)…")
    await place_bet(user_id, "a", current_block)

    print("Resolving block…")
    fake_hash = "0" * 63 + "f"
    await resolve_block(current_block + 1, fake_hash)

    user = await db.users.find_one({"_id": user_id})
    print(f"User balance after resolution: {user['balance']}")

if __name__ == "__main__":
    asyncio.run(run())
