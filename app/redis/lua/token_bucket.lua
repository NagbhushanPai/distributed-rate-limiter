-- Token Bucket Rate Limiter - Lua Script
-- Atomically refills tokens, checks limit, and updates state

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
