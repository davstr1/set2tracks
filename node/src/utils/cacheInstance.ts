import { createClient } from 'redis';
import config from '../config';
import logger from './logger';
import CacheService from './cache';

/**
 * Singleton Redis client and CacheService instance
 * This allows services to use caching without dependency injection
 */

let redisClient: any = null;
let cacheService: CacheService | null = null;

/**
 * Initialize the Redis client and CacheService
 * Should be called once at application startup
 */
export async function initializeCacheService() {
  if (cacheService) {
    return cacheService;
  }

  // Create Redis client
  redisClient = createClient({
    socket: {
      host: config.redis.host,
      port: config.redis.port,
    },
    password: config.redis.password,
  });

  redisClient.on('error', (err: Error) => {
    logger.error('Cache Redis Client Error', err);
  });

  redisClient.on('connect', () => {
    logger.info('Cache Redis Client Connected');
  });

  await redisClient.connect();

  // Create CacheService instance
  cacheService = new CacheService(redisClient);
  logger.info('CacheService initialized');

  return cacheService;
}

/**
 * Get the CacheService instance
 * Throws error if not initialized
 */
export function getCacheService(): CacheService {
  if (!cacheService) {
    throw new Error('CacheService not initialized. Call initializeCacheService() first.');
  }
  return cacheService;
}

/**
 * Close the Redis client connection
 */
export async function closeCacheService() {
  if (redisClient) {
    await redisClient.quit();
    logger.info('Cache Redis Client disconnected');
    redisClient = null;
    cacheService = null;
  }
}
