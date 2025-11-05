import { Request, Response, NextFunction } from 'express';
import { AppError, isAppError } from '../types/errors';
import logger from '../utils/logger';

/**
 * Global Error Handler Middleware
 *
 * Catches all errors thrown in the application and returns
 * appropriate HTTP responses with consistent error format.
 */

export function errorHandler(
  err: Error | AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  // Log error for monitoring
  if (isAppError(err)) {
    if (!err.isOperational) {
      // Log non-operational errors (programming errors) as errors
      logger.error('Non-operational error:', {
        name: err.name,
        message: err.message,
        code: err.code,
        statusCode: err.statusCode,
        stack: err.stack,
        details: err.details,
        path: req.path,
        method: req.method,
      });
    } else {
      // Log operational errors as warnings
      logger.warn('Operational error:', {
        name: err.name,
        message: err.message,
        code: err.code,
        statusCode: err.statusCode,
        path: req.path,
        method: req.method,
      });
    }
  } else {
    // Unknown error type - log as error
    logger.error('Unexpected error:', {
      name: err.name,
      message: err.message,
      stack: err.stack,
      path: req.path,
      method: req.method,
    });
  }

  // Determine response details
  const statusCode = isAppError(err) ? err.statusCode : 500;
  const code = isAppError(err) ? err.code : 'INTERNAL_ERROR';
  const message = err.message || 'An unexpected error occurred';

  // Don't expose internal error details in production
  const isDevelopment = process.env.NODE_ENV === 'development';
  const details = isAppError(err) && isDevelopment ? err.details : undefined;
  const stack = isDevelopment ? err.stack : undefined;

  // Send error response
  res.status(statusCode).json({
    status: 'error',
    code,
    message,
    ...(details && { details }),
    ...(stack && { stack }),
  });
}

/**
 * 404 Not Found Handler
 * Catches requests to undefined routes
 */
export function notFoundHandler(req: Request, res: Response, next: NextFunction): void {
  const error = new AppError(
    `Route not found: ${req.method} ${req.path}`,
    404,
    true,
    'ROUTE_NOT_FOUND',
    { path: req.path, method: req.method }
  );
  next(error);
}

/**
 * Async Error Wrapper
 * Wraps async route handlers to catch errors automatically
 */
export function asyncHandler<T>(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<T>
) {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}
