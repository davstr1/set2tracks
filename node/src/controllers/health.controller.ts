import { Request, Response } from 'express';
import prisma from '../utils/database';
import { RedisClient } from '../types/redis';

/**
 * Health Controller
 * Provides health check endpoints for monitoring and load balancers
 */
export class HealthController {
  private redisClient: RedisClient;

  constructor(redisClient: RedisClient) {
    this.redisClient = redisClient;
  }

  /**
   * Basic liveness probe - Is the server running?
   * Path: GET /healthz
   * Used by Kubernetes liveness probes
   */
  async liveness(req: Request, res: Response): Promise<void> {
    res.status(200).json({
      status: 'ok',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Readiness probe - Is the server ready to accept traffic?
   * Path: GET /readyz
   * Checks all critical dependencies
   * Used by Kubernetes readiness probes
   */
  async readiness(req: Request, res: Response): Promise<void> {
    const checks = {
      database: false,
      redis: false,
    };

    let isReady = true;

    // Check database connection
    try {
      await prisma.$queryRaw`SELECT 1`;
      checks.database = true;
    } catch (error) {
      isReady = false;
    }

    // Check Redis connection
    try {
      await this.redisClient.ping();
      checks.redis = true;
    } catch (error) {
      isReady = false;
    }

    const statusCode = isReady ? 200 : 503;

    res.status(statusCode).json({
      status: isReady ? 'ready' : 'not_ready',
      timestamp: new Date().toISOString(),
      checks,
    });
  }

  /**
   * Detailed health check with metrics
   * Path: GET /health
   * Provides comprehensive health information including response times
   */
  async health(req: Request, res: Response): Promise<void> {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: {
        rss: `${Math.round(process.memoryUsage().rss / 1024 / 1024)}MB`,
        heapTotal: `${Math.round(process.memoryUsage().heapTotal / 1024 / 1024)}MB`,
        heapUsed: `${Math.round(process.memoryUsage().heapUsed / 1024 / 1024)}MB`,
        external: `${Math.round(process.memoryUsage().external / 1024 / 1024)}MB`,
      },
      version: process.env.npm_package_version || '1.0.0',
      nodeVersion: process.version,
      environment: process.env.NODE_ENV || 'development',
      services: {
        database: { status: 'unknown', responseTime: 0 },
        redis: { status: 'unknown', responseTime: 0 },
      },
    };

    // Check database health with response time
    try {
      const dbStart = Date.now();
      await prisma.$queryRaw`SELECT 1`;
      const dbResponseTime = Date.now() - dbStart;

      health.services.database = {
        status: 'healthy',
        responseTime: dbResponseTime,
      };
    } catch (error) {
      health.status = 'unhealthy';
      health.services.database = {
        status: 'unhealthy',
        responseTime: 0,
      };
    }

    // Check Redis health with response time
    try {
      const redisStart = Date.now();
      await this.redisClient.ping();
      const redisResponseTime = Date.now() - redisStart;

      health.services.redis = {
        status: 'healthy',
        responseTime: redisResponseTime,
      };
    } catch (error) {
      health.status = 'unhealthy';
      health.services.redis = {
        status: 'unhealthy',
        responseTime: 0,
      };
    }

    const statusCode = health.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(health);
  }

  /**
   * Metrics endpoint for monitoring systems
   * Path: GET /metrics
   * Returns Prometheus-style metrics (optional, for future implementation)
   */
  async metrics(req: Request, res: Response): Promise<void> {
    const metrics = {
      process_uptime_seconds: process.uptime(),
      process_memory_rss_bytes: process.memoryUsage().rss,
      process_memory_heap_total_bytes: process.memoryUsage().heapTotal,
      process_memory_heap_used_bytes: process.memoryUsage().heapUsed,
      process_memory_external_bytes: process.memoryUsage().external,
      nodejs_version: process.version,
    };

    res.json(metrics);
  }
}

export default HealthController;
