import { RedisClient } from '../types/redis';
import { logInfo, logError } from './structuredLogger';

/**
 * Cache Service
 * Provides a simplified interface for caching operations using Redis
 */
export class CacheService {
  constructor(private redis: RedisClient) {}

  /**
   * Get a value from cache
   * @param key Cache key
   * @returns Parsed value or null if not found
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const cached = await this.redis.get(key);
      if (!cached) {
        return null;
      }
      return JSON.parse(cached) as T;
    } catch (error) {
      logError('Cache get error', error as Error, { key });
      return null;
    }
  }

  /**
   * Set a value in cache with TTL
   * @param key Cache key
   * @param value Value to cache (will be JSON stringified)
   * @param ttlSeconds Time to live in seconds (default: 1 hour)
   */
  async set(key: string, value: any, ttlSeconds: number = 3600): Promise<void> {
    try {
      await this.redis.setEx(key, ttlSeconds, JSON.stringify(value));
      logInfo('Cache set', { key, ttl: ttlSeconds });
    } catch (error) {
      logError('Cache set error', error as Error, { key });
    }
  }

  /**
   * Delete a specific key from cache
   * @param key Cache key
   */
  async del(key: string): Promise<void> {
    try {
      await this.redis.del(key);
      logInfo('Cache deleted', { key });
    } catch (error) {
      logError('Cache delete error', error as Error, { key });
    }
  }

  /**
   * Delete all keys matching a pattern
   * @param pattern Pattern to match (e.g., "sets:*")
   */
  async delPattern(pattern: string): Promise<void> {
    try {
      const keys = await this.redis.keys(pattern);
      if (keys.length > 0) {
        await this.redis.del(keys);
        logInfo('Cache pattern deleted', { pattern, count: keys.length });
      }
    } catch (error) {
      logError('Cache pattern delete error', error as Error, { pattern });
    }
  }

  /**
   * Check if a key exists in cache
   * @param key Cache key
   * @returns true if key exists
   */
  async exists(key: string): Promise<boolean> {
    try {
      const result = await this.redis.exists(key);
      return result === 1;
    } catch (error) {
      logError('Cache exists check error', error as Error, { key });
      return false;
    }
  }

  /**
   * Get or set a value in cache
   * If the key exists, return the cached value
   * Otherwise, execute the factory function, cache the result, and return it
   *
   * @param key Cache key
   * @param factory Function to execute if cache miss
   * @param ttlSeconds Time to live in seconds (default: 1 hour)
   * @returns The cached or newly generated value
   */
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttlSeconds: number = 3600
  ): Promise<T> {
    // Try to get from cache first
    const cached = await this.get<T>(key);
    if (cached !== null) {
      logInfo('Cache hit', { key });
      return cached;
    }

    // Cache miss - execute factory function
    logInfo('Cache miss', { key });
    const value = await factory();

    // Cache the result
    await this.set(key, value, ttlSeconds);

    return value;
  }

  /**
   * Increment a counter in cache
   * @param key Cache key
   * @param increment Amount to increment by (default: 1)
   * @returns New value after increment
   */
  async incr(key: string, increment: number = 1): Promise<number> {
    try {
      return await this.redis.incrBy(key, increment);
    } catch (error) {
      logError('Cache increment error', error as Error, { key, increment });
      throw error;
    }
  }

  /**
   * Set expiration time for a key
   * @param key Cache key
   * @param ttlSeconds Time to live in seconds
   */
  async expire(key: string, ttlSeconds: number): Promise<void> {
    try {
      await this.redis.expire(key, ttlSeconds);
    } catch (error) {
      logError('Cache expire error', error as Error, { key, ttlSeconds });
    }
  }

  /**
   * Get the time to live for a key
   * @param key Cache key
   * @returns TTL in seconds, or -1 if key has no expiration, -2 if key does not exist
   */
  async ttl(key: string): Promise<number> {
    try {
      return await this.redis.ttl(key);
    } catch (error) {
      logError('Cache TTL check error', error as Error, { key });
      return -2;
    }
  }
}

export default CacheService;
