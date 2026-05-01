import { RedisClientType } from 'redis';
import { Store } from './store.interface';
import { BucketState } from '../types';

export class RedisStore implements Store {
  private prefix = 'rate-limit:';

  constructor(private client: RedisClientType) {}

  async get(key: string): Promise<BucketState | null> {
    const data = await this.client.get(this.prefix + key);
    if (!data) return null;
    return JSON.parse(data);
  }

  async set(key: string, state: BucketState): Promise<void> {
    await this.client.set(
      this.prefix + key,
      JSON.stringify(state)
    );
  }

  async delete(key: string): Promise<void> {
    await this.client.del(this.prefix + key);
  }

  async increment(key: string, amount: number): Promise<number> {
    return await this.client.incrByFloat(this.prefix + key, amount);
  }

  async decrement(key: string, amount: number): Promise<number> {
    return await this.client.incrByFloat(this.prefix + key, -amount);
  }
}
