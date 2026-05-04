"""Seed test data in Redis"""

import redis
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to Redis
r = redis.from_url(
    f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0",
    decode_responses=True
)

print("🌱 Seeding test data...")

# Create test users with initial state
test_users = [
    ("user_1", 50, int(time.time() * 1000)),
    ("user_2", 100, int(time.time() * 1000)),
    ("user_3", 0, int(time.time() * 1000)),
]

for user_id, tokens, timestamp in test_users:
    key = f"rate_limit:{user_id}"
    value = f"{tokens}:{timestamp}"
    r.set(key, value)
    print(f"  ✓ {user_id}: {tokens} tokens")

print("Seeding complete")
