# Token Bucket Implementation Guide

## Overview

A clean, production-ready Token Bucket implementation in Python. The algorithm is simple: tokens accumulate at a constant rate, requests consume tokens, and burst traffic is naturally supported up to bucket capacity.

## Core Algorithm

```python
1. Calculate elapsed time since last request
2. Add (elapsed_time * refill_rate) tokens
3. Cap tokens at capacity
4. If tokens >= 1.0, allow request and deduct 1 token
5. Return (allowed, remaining_tokens)
```

## Key Design Decisions

### 1. **Floating-Point Tokens**

Tokens are stored as floats, not integers. This prevents loss of precision over time.

**Example:** With `refill_rate=10.5` tokens/sec:

- After 0.1s: `1.05` tokens added (not rounded to 1)
- After 1000 requests: precision maintained

```python
tokens_to_add = elapsed * self.refill_rate  # Float multiplication
self.tokens = min(self.tokens + tokens_to_add, self.capacity)
```

### 2. **Time is Updated on Each Call**

`last_refill` is updated every request, not just when refilling. This ensures precise tracking even with irregular request patterns.

```python
elapsed = current_time - self.last_refill
self.last_refill = current_time  # Update regardless of allowed/denied
```

### 3. **Capacity Capping**

Tokens never exceed capacity, preventing unbounded accumulation and enabling burst handling.

```python
self.tokens = min(self.tokens + tokens_to_add, self.capacity)
```

## Edge Cases & Handling

### **Burst Traffic**

**Scenario:** User makes 150 requests rapidly (capacity = 100, refill_rate = 10)

**Behavior:**

- Requests 1-100: Allowed ✓ (use all tokens in bucket)
- Request 101: Denied ✗ (no tokens available)
- After 0.1s: 1 new token → Request 101 allowed

**Why this works:** Burst capacity equals bucket size. Smooth decay after burst.

```
Tokens over time:
100 |████████████████████████
 50 |████████░░░░░░░░░░░░░░░░░░
  0 |░░░░░░░░░░░░░░░░░░░░░░░░░░
    0    1    2    3    4    5 (seconds)
    │    │    │    │    │    │
    └────┴────┴────┴────┴────┘
         Requests resumed
```

### **Time Precision**

**Scenario:** Requests arrive 0.001 seconds apart

**Precision loss at different levels:**

| Time Unit       | Precision Loss     | Impact            |
| --------------- | ------------------ | ----------------- |
| Seconds (float) | Negligible (~1e-9) | ✓ Production safe |
| Milliseconds    | ~0.1% error        | ⚠ Acceptable      |
| Microseconds    | ~0.001%            | ✓ Excellent       |

**Current implementation:** Uses `time.time()` (float seconds = ~microsecond precision)

**Example:**

```python
refill_rate = 10  # tokens/sec

# Precise calculation:
elapsed = 0.001  # 1 millisecond
tokens_to_add = 0.001 * 10 = 0.01  # 0.01 tokens added
```

### **Time Skew / Clock Drift**

**Scenario:** System clock jumps backward or forward

**Backward drift** (clock goes backward):

```python
elapsed = -0.5  # Negative time!
tokens_to_add = -0.5 * 10 = -5  # Loses 5 tokens!
```

**Solution:** Validate `current_time >= last_refill`

```python
if current_time < self.last_refill:
    current_time = self.last_refill  # Ignore backward time
```

**Forward drift** (clock jumps ahead):

```python
elapsed = 100  # System clock jumped 100 seconds!
tokens_to_add = 100 * 10 = 1000 tokens
self.tokens = min(1000 + 50, 100) = 100  # Capped safely
```

**Benefit:** Capacity capping protects against forward skew automatically.

### **Zero Refill Rate**

**Scenario:** `refill_rate=0` (tokens never refill)

**Behavior:**

```python
tokens_to_add = elapsed * 0 = 0
# Tokens only decrease, never increase
```

**Use case:** Fixed-window throttling

### **Very Small Refill Rate**

**Scenario:** `refill_rate=0.001` (1 token per 1000 seconds)

**Behavior:**

```python
after 100s: tokens_to_add = 100 * 0.001 = 0.1  # 0.1 tokens
after 1000s: tokens_to_add = 1000 * 0.001 = 1.0  # 1 token
```

**Note:** Float precision handles this correctly.

### **Very Large Request Gaps**

**Scenario:** Requests 1 hour apart, capacity=100

**Behavior:**

```python
elapsed = 3600  # 1 hour in seconds
tokens_to_add = 3600 * 10 = 36000  # 36000 tokens!
self.tokens = min(36000 + 0, 100) = 100  # Capped at capacity
```

**Result:** Bucket refills to full capacity, then stays there. ✓ Correct

## Performance Characteristics

| Operation         | Complexity | Time                 |
| ----------------- | ---------- | -------------------- |
| `allow_request()` | O(1)       | <1μs                 |
| Memory per bucket | O(1)       | ~48 bytes (2 floats) |
| Throughput        | -          | Unlimited (no I/O)   |

## Thread Safety (In-Memory)

**Not thread-safe by default.** For multi-threaded use:

```python
import threading

class ThreadSafeTokenBucket(TokenBucket):
    def __init__(self, capacity, refill_rate):
        super().__init__(capacity, refill_rate)
        self.lock = threading.Lock()

    def allow_request(self, current_time=None):
        with self.lock:
            return super().allow_request(current_time)
```

**For distributed systems:** Use Redis with Lua scripts (see `app.py`)

## Production Checklist

- [x] Handles burst traffic correctly
- [x] Floating-point arithmetic for precision
- [x] Capacity capping prevents unbounded growth
- [x] Time tracking is precise (~microsecond level)
- [x] Simple, understandable code
- [x] O(1) time and space complexity
- [ ] Thread-safe (if needed, add lock)
- [ ] Distributed (if needed, use Redis)

## When to Use Token Bucket

✓ **Good for:**

- API rate limiting
- Bandwidth throttling
- Burst-friendly limits
- Simple, per-user limits

✗ **Not ideal for:**

- Strict fairness (use Leaky Bucket)
- Distributed systems (use Redis)
- Complex policies (use custom logic)

## Common Mistakes

### ❌ Mistake 1: Allowing multiple tokens per request

```python
# WRONG
if self.tokens >= 5:
    self.tokens -= 5
    return {"allowed": True}
```

**Issue:** Inconsistent behavior with refill_rate

**Fix:** Always consume 1 token per request, or explicitly track multi-token consumption

### ❌ Mistake 2: Resetting time on each check

```python
# WRONG
def check(self):
    self.last_refill = time.time()  # Resets every time!
    # Refill tokens...
```

**Issue:** Tokens never accumulate

### ❌ Mistake 3: Using integer arithmetic

```python
# WRONG
tokens_to_add = int(elapsed * self.refill_rate)  # Loses precision
```

**Fix:** Use floats, only round when returning

## Testing Edge Cases

```python
# Test 1: Burst traffic
bucket = TokenBucket(100, 10)
for i in range(100):
    assert bucket.allow_request()["allowed"]
assert not bucket.allow_request()["allowed"]

# Test 2: Time precision
bucket = TokenBucket(100, 10)
bucket.allow_request(0)
bucket.allow_request(0.0001)  # 0.1ms later
result = bucket.allow_request(0.0001)
assert result["remaining_tokens"] >= 98

# Test 3: Capacity capping
bucket = TokenBucket(100, 10)
result = bucket.allow_request(1000)  # 1000 seconds later
assert result["remaining_tokens"] == 99  # Only 99 left (1 consumed)
```

## References

- Token Bucket Algorithm: https://en.wikipedia.org/wiki/Token_bucket
- RFC 6584 (Rate Limiting HTTP): https://tools.ietf.org/html/rfc6584
- Leaky Bucket vs Token Bucket: https://en.wikipedia.org/wiki/Leaky_bucket
