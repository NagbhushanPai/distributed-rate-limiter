export interface RateLimiterConfig {
  capacity: number;
  refillRate: number;
  key?: string;
  requests?: number;
  window?: number;
}

export interface RateLimiterStatus {
  tokens: number;
  lastRefill: number;
  capacity: number;
  refillRate: number;
}

export interface BucketState {
  tokens: number;
  lastRefill: number;
}
