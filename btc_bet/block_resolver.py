import asyncio
import time
from db import db, redis_client
from utils import get_bet_by_id
from bson import ObjectId

async def resolve_bet_concurrent(bet_id: str, last_char: str, payout=100):
    bet = await get_bet_by_id(bet_id)
    if not bet:
        return

    outcome = "won" if bet["guess"].lower() == last_char else "lost"

    # Update MongoDB + Redis cache
    await db.bets.update_one(
        {"_id": ObjectId(bet_id)},
        {"$set": {"status": outcome}}
    )
    await redis_client.hset(f"bet:{bet_id}", mapping={"status": outcome})
    await redis_client.decr(f"user:{bet['user_id']}:pending_bets")

    if outcome == "won":
        await db.users.update_one(
            {"_id": bet["user_id"]},
            {"$inc": {"balance": payout}},
            upsert=True
        )

async def resolve_block_benchmark(height: int, block_hash: str, payout=100, concurrency=500):
    key = f"bets:pending:{height}"
    bet_ids = await redis_client.lrange(key, 0, -1)
    total_bets = len(bet_ids)
    if total_bets == 0:
        print("No pending bets to resolve.")
        return

    last_char = block_hash[-1].lower()
    semaphore = asyncio.Semaphore(concurrency)

    async def sem_task(bet_id):
        async with semaphore:
            await resolve_bet_concurrent(bet_id.decode() if isinstance(bet_id, bytes) else bet_id, last_char, payout)

    print(f"Starting to resolve {total_bets} bets at block {height} with concurrency={concurrency}")
    start = time.perf_counter()

    tasks = [asyncio.create_task(sem_task(bid)) for bid in bet_ids]
    await asyncio.gather(*tasks)

    total_time = time.perf_counter() - start
    tps = total_bets / total_time
    print(f"✅ Resolved {total_bets} bets in {total_time:.2f}s")
    print(f"Throughput: {tps:.0f} bets/sec")
