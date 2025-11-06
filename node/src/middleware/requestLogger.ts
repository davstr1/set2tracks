/**
 * Request Logger Middleware
 * Logs all HTTP requests with structured context
 */

import { Request, Response, NextFunction } from 'express';
import { structuredLogger, createLogContext } from '../utils/structuredLogger';

/**
 * Middleware to log all HTTP requests
 */
export function requestLoggerMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const startTime = Date.now();

  // Log request start
  const context = createLogContext(req);
  structuredLogger.debug(`Request started: ${req.method} ${req.path}`, context);

  // Log when response finishes
  res.on('finish', () => {
    const duration = Date.now() - startTime;
    const logContext = {
      ...context,
      statusCode: res.statusCode,
      duration,
    };

    // Determine log level based on status code
    if (res.statusCode >= 500) {
      structuredLogger.error(`Request completed: ${req.method} ${req.path}`, undefined, logContext);
    } else if (res.statusCode >= 400) {
      structuredLogger.warn(`Request completed: ${req.method} ${req.path}`, logContext);
    } else {
      structuredLogger.info(`Request completed: ${req.method} ${req.path}`, logContext);
    }

    // Log slow requests
    if (duration > 3000) {
      structuredLogger.performance(`Slow request: ${req.method} ${req.path}`, duration, logContext);
    }
  });

  next();
}

/**
 * Skip logging for specific paths (like health checks)
 */
export function createRequestLoggerMiddleware(options?: {
  skip?: (req: Request) => boolean;
}): (req: Request, res: Response, next: NextFunction) => void {
  return (req: Request, res: Response, next: NextFunction) => {
    // Skip logging if specified
    if (options?.skip && options.skip(req)) {
      return next();
    }

    requestLoggerMiddleware(req, res, next);
  };
}

/**
 * Skip health check and monitoring endpoints
 */
export const requestLoggerWithSkip = createRequestLoggerMiddleware({
  skip: (req: Request) => {
    const skipPaths = ['/health', '/metrics', '/ping'];
    return skipPaths.includes(req.path);
  },
});
