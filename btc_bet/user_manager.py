from decimal import Decimal
from datetime import datetime
from bson import ObjectId
from models import User
from db import db, redis_client

async def create_user(user_id: str):
    """Write-through user creation matching bet pattern"""
    user = User(user_id=user_id)
    user_dict = user.to_dict()
    
    # Convert Decimal to string for Redis storage
    user_dict["balance"] = str(user_dict["balance"])
    
    # Write-through to both systems
    await redis_client.hset(f"user:{user_id}", mapping=user_dict)
    await db.users.insert_one({
        "_id": user_id,
        **user.to_dict()  # Store Decimal directly in MongoDB
    })
    return user_id

async def update_balance(user_id: str, amount: Decimal):
    """Atomic balance update with write-through"""
    # Redis operation with Decimal conversion
    await redis_client.hincrbyfloat(f"user:{user_id}", "balance", float(amount))
    
    # MongoDB operation
    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"balance": amount}}
    )

async def update_active_bets(user_id: str, delta: int):
    """Active bets counter with write-through"""
    # Redis operation
    await redis_client.hincrby(f"user:{user_id}", "active_bets", delta)
    
    # MongoDB operation
    await db.users.update_one(
        {"_id": user_id},
        {"$inc": {"active_bets": delta}}
    )

async def get_user(user_id: str):
    """Cache-aside pattern with type conversion"""
    user_key = f"user:{user_id}"
    cached = await redis_client.hgetall(user_key)
    
    if cached:
        return User(
            user_id=user_id,
            balance=Decimal(cached["balance"]),
            active_bets=int(cached["active_bets"]),
            created_at=cached["created_at"]
        )
    
    # Fallback to MongoDB
    db_user = await db.users.find_one({"_id": user_id})
    if db_user:
        # Update Redis cache
        redis_user = {**db_user, "balance": str(db_user["balance"])}
        await redis_client.hset(user_key, mapping=redis_user)
        return User(**db_user)
    return None