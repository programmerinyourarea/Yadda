import asyncio
import random
import string
import uuid
from user_manager import create_user
from bet_manager import place_bet
from block_resolver import resolve_block
from incremental_sync import run_incremental_sync  # ✅ this is key!

NUM_USERS = 5000
BET_PER_PHASE = 3
BLOCK_HEIGHT = 100
CONCURRENCY_LIMIT = 100  # Tune based on your machine

def random_guess():
    return random.choice('0123456789abcdef')

def random_block_hash():
    return ''.join(random.choices(string.hexdigits.lower(), k=64))

async def limited(semaphore, coro):
    async with semaphore:
        return await coro

async def simulate():
    print("[SIM] Starting analytics simulation...")

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    user_ids = [str(uuid.uuid4()) for _ in range(NUM_USERS)]

    # Step 1: Create users
    print(f"[SIM] Creating {NUM_USERS} users...")
    await asyncio.gather(*[
        limited(semaphore, create_user(uid)) for uid in user_ids
    ])

    # Step 2: First round of 3 bets per user
    print("[SIM] Placing first round of bets...")
    await asyncio.gather(*[
        limited(semaphore, place_bet(uid, random_guess(), BLOCK_HEIGHT))
        for uid in user_ids for _ in range(BET_PER_PHASE)
    ])

    # Step 3: Resolve bets
    block_hash = random_block_hash()
    print(f"[SIM] Resolving block {BLOCK_HEIGHT} with hash {block_hash}...")
    await resolve_block(BLOCK_HEIGHT, block_hash)

    # Step 4: Second round of bets (unresolved)
    print("[SIM] Placing second round of bets...")
    await asyncio.gather(*[
        limited(semaphore, place_bet(uid, random_guess(), BLOCK_HEIGHT + 1))
        for uid in user_ids for _ in range(BET_PER_PHASE)
    ])

    # Step 5: Wait before export
    print("[SIM] Waiting 30 seconds before exporting to Snowflake...")
    await asyncio.sleep(30)

    # Step 6: Export only new data and upload to Snowflake
    print("[SIM] Exporting new data and uploading to Snowflake...")
    run_incremental_sync()

    print("[SIM] ✅ Analytics simulation complete.")

if __name__ == "__main__":
    asyncio.run(simulate())
