# Architecture & Implementation Details

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Clients (HTTP)                        │
└────────────┬────────────────────────────────┬────────────┘
             │                                │
        ┌────▼────┐                      ┌────▼────┐
        │   LB    │                      │   LB    │
        └────┬────┘                      └────┬────┘
             │                                │
    ┌────────┴────────┬───────────────────────┴────────┐
    │                 │                                 │
┌───▼──┐          ┌───▼──┐                         ┌───▼──┐
│Flask │          │Flask │                         │Flask │
│ App  │          │ App  │                         │ App  │
└───┬──┘          └───┬──┘                         └───┬──┘
    │                 │                                 │
    └─────────────────┼─────────────────────────────────┘
                      │
              ┌───────▼────────┐
              │   Redis Cluster │
              │  (Rate State)   │
              └────────────────┘
```

## Token Bucket Algorithm

### Algorithm Flow

```python
# Given: user_id, capacity, refill_rate, current_time, tokens_requested

1. Retrieve current state from Redis:
   - tokens: current token count
   - last_refill: timestamp of last refill

2. Calculate tokens to add since last refill:
   time_passed = (current_time - last_refill) / 1000  # seconds
   tokens_to_add = time_passed * refill_rate

3. Cap tokens at capacity:
   tokens = min(tokens + tokens_to_add, capacity)

4. Check if request is allowed:
   allowed = tokens >= tokens_requested

5. If allowed, consume tokens:
   tokens -= tokens_requested

6. Atomically update Redis:
   SET rate_limit:{user_id} "{tokens}:{current_time}"

7. Return result:
   {
     "allowed": allowed,
     "remaining_tokens": tokens,
     "retry_after": calculate_retry_time()
   }
```

### Example Timeline

```
Time: 0ms
  - User makes request (100 tokens available)
  - Request allowed ✓
  - Tokens remaining: 99

Time: 100ms
  - 10 tokens/sec * 0.1s = 1 new token
  - Total tokens: 100 (at capacity)

Time: 5000ms (5 seconds later)
  - 10 tokens/sec * 5s = 50 new tokens
  - Total tokens: 100 (capped at capacity)

Time: 5000ms - User makes 60 token request
  - Not enough tokens (100 < 60)?
  - Wait, error. Remaining: 100, need: 60 tokens
  - Actually: 100 > 60, so allowed ✓
  - Tokens remaining: 40
```

## Data Model

### Redis Key Format

```
rate_limit:{identifier}
```

### Redis Value Format

```
{tokens}:{last_refill_timestamp}

Example: "42.5:1704067200000"
- tokens: 42.5 (float, allows sub-token precision)
- last_refill: 1704067200000 (milliseconds since epoch)
```

## Lua Script (Atomic Operation)

```lua
-- Token Bucket Lua Script
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])
local tokens_requested = tonumber(ARGV[4])

-- Get current state
local state = redis.call('GET', key)
local tokens, last_refill

if state == false then
    tokens = capacity
    last_refill = current_time
else
    local parts = {}
    for part in string.gmatch(state, "[^:]+") do
        table.insert(parts, part)
    end
    tokens = tonumber(parts[1])
    last_refill = tonumber(parts[2])
end

-- Calculate tokens to add
local time_passed = (current_time - last_refill) / 1000
local tokens_to_add = time_passed * refill_rate
tokens = math.min(tokens + tokens_to_add, capacity)

-- Check if allowed
local allowed = tokens >= tokens_requested
local remaining = tokens

if allowed then
    tokens = tokens - tokens_requested
    remaining = tokens
end

-- Update state
redis.call('SET', key, tokens .. ':' .. current_time)

-- Return result
return {allowed and 1 or 0, remaining, last_refill}
```

### Why Lua Scripts?

- **Atomicity**: All operations execute atomically in Redis
- **Race Condition Prevention**: No concurrent modifications possible
- **Performance**: Single round-trip to Redis
- **Consistency**: State never becomes inconsistent

## Scaling Strategies

### Horizontal Scaling

```
Request → Load Balancer
           ├─ Flask Instance 1
           ├─ Flask Instance 2
           └─ Flask Instance 3
                  ↓
              Redis (Single)
```

**Advantages:**

- Simple setup
- Good for moderate load
- Shared rate limit state

**Limitations:**

- Redis becomes bottleneck
- Limited to one Redis instance

### Redis Cluster (Advanced)

```
           ├─ Flask Instance 1 ─┐
Request → LB ├─ Flask Instance 2 ├─→ Redis Cluster
           └─ Flask Instance 3 ─┘
```

**Advantages:**

- Unlimited scalability
- High availability
- Distributed rate limit state

**Implementation:** Change Redis client to use Cluster support

## Error Handling & Resilience

### Fail-Open Strategy (Default)

```python
try:
    allowed = rate_limiter.is_allowed(user_id)
except RedisException:
    # If Redis is down, allow requests
    return {"allowed": True, ...}
```

**When to use:** External APIs, prevent cascading failures

### Fail-Closed Strategy

```python
try:
    allowed = rate_limiter.is_allowed(user_id)
except RedisException:
    # If Redis is down, block requests
    return {"allowed": False, ...}
```

**When to use:** Internal APIs, security-critical systems

## Performance Characteristics

### Time Complexity

- **Check Rate Limit**: O(1) - Single Redis lookup + Lua script
- **Get Status**: O(1) - Single Redis lookup
- **Reset**: O(1) - Single Redis delete

### Space Complexity

- **Per User**: O(1) - Fixed size Redis value (2 float/int values)
- **Per System**: O(n) where n = unique user IDs tracked

### Network Overhead

- **Per Request**: 1 Redis round-trip (~5ms on LAN)
- **Throughput**: Limited by Redis throughput (~100K ops/sec)

### Optimization Tips

1. **Connection Pooling**: Reuse Redis connections
2. **Pipelining**: Batch multiple requests
3. **Clustering**: Distribute load across Redis nodes
4. **Caching**: Cache frequently accessed limits locally
5. **Sharding**: Shard by user_id for better distribution

## Monitoring & Observability

### Key Metrics

```python
# Request metrics
rate_limit_requests_total{allowed=true/false}
rate_limit_request_latency_seconds{percentile=p50/p95/p99}

# System health
rate_limit_redis_connection_errors_total
rate_limit_redis_latency_seconds

# Business metrics
rate_limit_blocked_requests_total
rate_limit_tokens_consumed_total
```

### Example Prometheus Queries

```prometheus
# Total allowed vs blocked
rate(rate_limit_requests_total[5m])

# P99 latency
histogram_quantile(0.99, rate_limit_request_latency_seconds_bucket[5m])

# Blocked request rate
rate(rate_limit_requests_total{allowed="false"}[5m])
```

## Security Considerations

### User Identification

- **Never trust client-provided user_id**: Always validate from session/token
- Use authenticated identifiers (user_id, API key, JWT)
- Implement user hierarchy (different limits per tier)

### Rate Limit Bypass Prevention

- Validate rate limit headers in responses
- Monitor for suspicious patterns
- Implement IP-based fallback limiting

### Redis Security

- Enable Redis password authentication
- Use Redis ACLs (Redis 6+)
- Run Redis in isolated network
- Enable encryption in transit (Redis SSL/TLS)

## Alternative Algorithms

### Sliding Window

```
Time: |←── 1 minute window ──→|
      │ Old    │    Recent    │
      │requests│  requests    │
      └────────┴──────────────┘

Allowed = count(recent_requests) < limit
```

### Leaky Bucket

```
Token Generation → Bucket (Capacity)
                    ↓
                   Leak (constant rate)
                    ↓
                  Output
```

### Fixed Window

```
Minute 1: [0-60s] 100 requests allowed
Minute 2: [60-120s] 100 requests allowed
Minute 3: [120-180s] 100 requests allowed
```
