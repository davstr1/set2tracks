/**
 * Request ID Middleware
 * Adds unique request ID to each request for tracking and correlation
 */

import { Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';

declare global {
  namespace Express {
    interface Request {
      id?: string;
      startTime?: number;
    }
  }
}

/**
 * Middleware to add unique request ID to each request
 * Also tracks request start time for duration calculation
 */
export function requestIdMiddleware(
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Generate unique request ID
  req.id = uuidv4();
  req.startTime = Date.now();

  // Add request ID to response headers
  res.setHeader('X-Request-ID', req.id);

  // Log when response is finished
  res.on('finish', () => {
    if (req.startTime) {
      const duration = Date.now() - req.startTime;

      // Store duration for logging
      (req as any).duration = duration;
    }
  });

  next();
}

/**
 * Get request ID from request
 */
export function getRequestId(req: Request): string | undefined {
  return req.id;
}

/**
 * Get request duration in milliseconds
 */
export function getRequestDuration(req: Request): number | undefined {
  if (!req.startTime) {
    return undefined;
  }
  return Date.now() - req.startTime;
}
