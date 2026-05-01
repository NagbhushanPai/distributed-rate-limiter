import { Store } from '../stores/store.interface';
import { BucketState, RateLimiterConfig } from '../types';

export class TokenBucket {
  private capacity: number;
  private refillRate: number;

  constructor(
    private store: Store,
    private key: string,
    config: RateLimiterConfig
  ) {
    this.capacity = config.capacity;
    this.refillRate = config.refillRate;
  }

  async isAllowed(tokens: number = 1): Promise<boolean> {
    const state = await this.getOrCreateState();
    const now = Date.now();
    
    // Calculate tokens added since last refill
    const timePassed = (now - state.lastRefill) / 1000; // Convert to seconds
    const tokensToAdd = timePassed * this.refillRate;
    
    let currentTokens = Math.min(
      state.tokens + tokensToAdd,
      this.capacity
    );

    if (currentTokens >= tokens) {
      currentTokens -= tokens;
      await this.store.set(this.key, {
        tokens: currentTokens,
        lastRefill: now
      });
      return true;
    }

    return false;
  }

  async consume(tokens: number = 1): Promise<number> {
    const state = await this.getOrCreateState();
    const now = Date.now();

    const timePassed = (now - state.lastRefill) / 1000;
    const tokensToAdd = timePassed * this.refillRate;

    let currentTokens = Math.min(
      state.tokens + tokensToAdd,
      this.capacity
    );

    currentTokens = Math.max(0, currentTokens - tokens);

    await this.store.set(this.key, {
      tokens: currentTokens,
      lastRefill: now
    });

    return currentTokens;
  }

  async getStatus() {
    const state = await this.getOrCreateState();
    const now = Date.now();

    const timePassed = (now - state.lastRefill) / 1000;
    const tokensToAdd = timePassed * this.refillRate;

    const currentTokens = Math.min(
      state.tokens + tokensToAdd,
      this.capacity
    );

    return {
      tokens: currentTokens,
      lastRefill: state.lastRefill,
      capacity: this.capacity,
      refillRate: this.refillRate
    };
  }

  async reset(): Promise<void> {
    await this.store.delete(this.key);
  }

  private async getOrCreateState(): Promise<BucketState> {
    let state = await this.store.get(this.key);
    if (!state) {
      state = {
        tokens: this.capacity,
        lastRefill: Date.now()
      };
      await this.store.set(this.key, state);
    }
    return state;
  }
}
