import { RateLimiter } from '../src/rate-limiter';
import { TokenBucket } from '../src/algorithms/token-bucket';
import { Store } from '../src/stores/store.interface';
import { BucketState } from '../src/types';

// Mock Store
class MockStore implements Store {
  private data: Map<string, BucketState> = new Map();

  async get(key: string): Promise<BucketState | null> {
    return this.data.get(key) || null;
  }

  async set(key: string, state: BucketState): Promise<void> {
    this.data.set(key, state);
  }

  async delete(key: string): Promise<void> {
    this.data.delete(key);
  }

  async increment(key: string, amount: number): Promise<number> {
    const current = this.data.get(key)?.tokens || 0;
    const newValue = current + amount;
    this.data.set(key, { tokens: newValue, lastRefill: Date.now() });
    return newValue;
  }

  async decrement(key: string, amount: number): Promise<number> {
    return this.increment(key, -amount);
  }
}

describe('RateLimiter', () => {
  let store: MockStore;
  let rateLimiter: RateLimiter;

  beforeEach(() => {
    store = new MockStore();
    rateLimiter = new RateLimiter(store, {
      capacity: 10,
      refillRate: 5 // 5 tokens per second
    });
  });

  test('should allow requests within rate limit', async () => {
    const allowed = await rateLimiter.isAllowed('user-1');
    expect(allowed).toBe(true);
  });

  test('should track multiple users independently', async () => {
    const user1Allowed = await rateLimiter.isAllowed('user-1');
    const user2Allowed = await rateLimiter.isAllowed('user-2');
    expect(user1Allowed).toBe(true);
    expect(user2Allowed).toBe(true);
  });

  test('should return status information', async () => {
    await rateLimiter.isAllowed('user-3');
    const status = await rateLimiter.getStatus('user-3');
    expect(status.capacity).toBe(10);
    expect(status.refillRate).toBe(5);
  });

  test('should reset rate limiter for a key', async () => {
    await rateLimiter.isAllowed('user-4');
    await rateLimiter.reset('user-4');
    const status = await rateLimiter.getStatus('user-4');
    expect(status.tokens).toBe(10); // Reset to full capacity
  });
});
