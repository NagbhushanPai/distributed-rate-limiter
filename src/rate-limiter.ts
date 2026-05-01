import { Store } from './stores/store.interface';
import { TokenBucket } from './algorithms/token-bucket';
import { RateLimiterConfig, RateLimiterStatus } from './types';

export class RateLimiter {
  private buckets: Map<string, TokenBucket> = new Map();

  constructor(
    private store: Store,
    private defaultConfig: RateLimiterConfig
  ) {}

  async isAllowed(key: string): Promise<boolean> {
    const bucket = this.getBucket(key);
    return await bucket.isAllowed(1);
  }

  async consume(key: string, tokens: number = 1): Promise<number> {
    const bucket = this.getBucket(key);
    return await bucket.consume(tokens);
  }

  async reset(key: string): Promise<void> {
    const bucket = this.getBucket(key);
    await bucket.reset();
    this.buckets.delete(key);
  }

  async getStatus(key: string): Promise<RateLimiterStatus> {
    const bucket = this.getBucket(key);
    return await bucket.getStatus();
  }

  private getBucket(key: string): TokenBucket {
    if (!this.buckets.has(key)) {
      this.buckets.set(
        key,
        new TokenBucket(this.store, key, {
          ...this.defaultConfig,
          key
        })
      );
    }
    return this.buckets.get(key)!;
  }
}
