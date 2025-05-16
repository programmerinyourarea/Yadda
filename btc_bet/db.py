from pymongo import AsyncMongoClient
import redis.asyncio as redis
from decimal import Decimal

MONGO_URI = "mongodb://localhost:27017"
REDIS_URI = "redis://localhost:6379"

mongo_client = AsyncMongoClient(MONGO_URI)
db = mongo_client["btc_bet"]

redis_client = redis.from_url(REDIS_URI, decode_responses=True)
