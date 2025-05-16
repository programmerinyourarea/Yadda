# btc_bet/performance_test.py

import asyncio
import time
import uuid
from db import db, redis_client
from user_manager import create_user
from bet_manager import place_bet
from block_resolver import resolve_block_benchmark
NUM_USERS = 1_000_0
BETS_PER_USER = 5
CONCURRENCY = 32

user_ids = []  # UUIDs of created users


async def reset_databases():
    print("Flushing Redis…")
    await redis_client.flushdb()
    print("Clearing MongoDB collections…")
    await db.bets.delete_many({})
    await db.users.delete_many({})


async def create_users():
    print(f"Creating {NUM_USERS} users…")
    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def sem_task():
        async with semaphore:
            user_id = str(uuid.uuid4())
            await create_user(user_id)
            user_ids.append(user_id)

    await asyncio.gather(*(sem_task() for _ in range(NUM_USERS)))


async def place_bets():
    print(f"Placing {NUM_USERS * BETS_PER_USER} bets…")
    semaphore = asyncio.Semaphore(CONCURRENCY)
    current_height = 1_000_000

    async def sem_task(user_id):
        async with semaphore:
            for _ in range(BETS_PER_USER):
                await place_bet(user_id, guess="f", current_height=current_height)

    await asyncio.gather(*(sem_task(uid) for uid in user_ids))


async def run():
    await reset_databases()
"""""
    start = time.perf_counter()
    await create_users()
    print(f"✅ Created {NUM_USERS} in {(time.perf_counter() - start):.2f}s")
    print(f"Throughput: {int(NUM_USERS / time.perf_counter() - start)} users/sec")
    await place_bets()
    total_time = time.perf_counter() - start

    total_bets = NUM_USERS * BETS_PER_USER
    print(f"✅ Completed {total_bets} bets in {total_time:.2f}s")
    print(f"Throughput: {int(total_bets / total_time)} bets/sec")
    await resolve_block_benchmark(height=1000000+1, block_hash="abcd1234ef56", payout=100, concurrency=32)
"""

if __name__ == "__main__":
    asyncio.run(run())
