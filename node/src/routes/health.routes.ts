import { Router } from 'express';
import HealthController from '../controllers/health.controller';
import { RedisClient } from '../types/redis';

/**
 * Health Check Routes
 * Provides endpoints for monitoring and load balancer health checks
 */
export default function createHealthRoutes(redisClient: RedisClient): Router {
  const router = Router();
  const healthController = new HealthController(redisClient);

  /**
   * Kubernetes liveness probe
   * Simple check - is the server process running?
   */
  router.get('/healthz', healthController.liveness.bind(healthController));

  /**
   * Kubernetes readiness probe
   * Checks if server is ready to accept traffic (all dependencies available)
   */
  router.get('/readyz', healthController.readiness.bind(healthController));

  /**
   * Detailed health check
   * Provides comprehensive health information with metrics
   */
  router.get('/health', healthController.health.bind(healthController));

  /**
   * Metrics endpoint
   * For monitoring systems (Prometheus, Datadog, etc.)
   */
  router.get('/metrics', healthController.metrics.bind(healthController));

  return router;
}
