import { BucketState } from '../types';

export interface Store {
  get(key: string): Promise<BucketState | null>;
  set(key: string, state: BucketState): Promise<void>;
  delete(key: string): Promise<void>;
  increment(key: string, amount: number): Promise<number>;
  decrement(key: string, amount: number): Promise<number>;
}
