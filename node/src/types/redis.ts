import { RedisClientType, createClient } from 'redis';

/**
 * Redis Client Types
 */

export type RedisClient = RedisClientType<any, any, any>;

export type RedisConnection = ReturnType<typeof createClient>;
