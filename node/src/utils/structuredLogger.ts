/**
 * Structured Logger
 * Enhanced logging with context, request tracking, and structured metadata
 */

import { Request } from 'express';
import logger from './logger';
import { getRequestId, getRequestDuration } from '../middleware/requestId';
import { getErrorMessage } from '../types/errors';

/**
 * Log context interface
 */
export interface LogContext {
  requestId?: string;
  userId?: number;
  method?: string;
  path?: string;
  ip?: string;
  userAgent?: string;
  duration?: number;
  statusCode?: number;
  [key: string]: any;
}

/**
 * Create log context from request
 */
export function createLogContext(req: Request): LogContext {
  const context: LogContext = {
    requestId: getRequestId(req),
    method: req.method,
    path: req.path,
    ip: req.ip,
    userAgent: req.get('user-agent'),
  };

  // Add user info if authenticated
  if (req.user) {
    context.userId = (req.user as any).id;
  }

  // Add duration if available
  const duration = getRequestDuration(req);
  if (duration !== undefined) {
    context.duration = duration;
  }

  return context;
}

/**
 * Structured logger class
 */
export class StructuredLogger {
  /**
   * Log with context
   */
  private log(level: string, message: string, context?: LogContext, error?: Error): void {
    const meta: any = {
      ...(context || {}),
      timestamp: new Date().toISOString(),
    };

    if (error) {
      meta.error = {
        message: error.message,
        stack: error.stack,
        name: error.name,
      };
    }

    logger.log(level, message, meta);
  }

  /**
   * Info level log
   */
  info(message: string, context?: LogContext): void {
    this.log('info', message, context);
  }

  /**
   * Warn level log
   */
  warn(message: string, context?: LogContext): void {
    this.log('warn', message, context);
  }

  /**
   * Error level log
   */
  error(message: string, error?: Error | unknown, context?: LogContext): void {
    const err = error instanceof Error ? error : new Error(getErrorMessage(error));
    this.log('error', message, context, err);
  }

  /**
   * Debug level log
   */
  debug(message: string, context?: LogContext): void {
    this.log('debug', message, context);
  }

  /**
   * HTTP request log
   */
  httpRequest(req: Request, res: any): void {
    const context = createLogContext(req);
    context.statusCode = res.statusCode;

    const message = `${req.method} ${req.path} - ${res.statusCode}`;
    this.info(message, context);
  }

  /**
   * Database query log
   */
  dbQuery(query: string, duration: number, context?: LogContext): void {
    this.debug('Database query executed', {
      ...context,
      query,
      duration,
    });
  }

  /**
   * External API call log
   */
  apiCall(
    service: string,
    endpoint: string,
    method: string,
    statusCode: number,
    duration: number,
    context?: LogContext
  ): void {
    this.info('External API call', {
      ...context,
      service,
      endpoint,
      method,
      statusCode,
      duration,
    });
  }

  /**
   * Job/Task log
   */
  job(jobName: string, status: 'started' | 'completed' | 'failed', context?: LogContext): void {
    const level = status === 'failed' ? 'error' : 'info';
    this.log(level, `Job ${status}: ${jobName}`, context);
  }

  /**
   * Authentication log
   */
  auth(action: 'login' | 'logout' | 'register' | 'failed', userId?: number, context?: LogContext): void {
    this.info(`Authentication: ${action}`, {
      ...context,
      userId,
      action,
    });
  }

  /**
   * Security event log
   */
  security(event: string, severity: 'low' | 'medium' | 'high', context?: LogContext): void {
    const level = severity === 'high' ? 'error' : severity === 'medium' ? 'warn' : 'info';
    this.log(level, `Security event: ${event}`, {
      ...context,
      severity,
      event,
    });
  }

  /**
   * Performance log
   */
  performance(operation: string, duration: number, context?: LogContext): void {
    const level = duration > 5000 ? 'warn' : 'info';
    this.log(level, `Performance: ${operation}`, {
      ...context,
      operation,
      duration,
      slow: duration > 5000,
    });
  }

  /**
   * Business event log
   */
  businessEvent(event: string, data: any, context?: LogContext): void {
    this.info(`Business event: ${event}`, {
      ...context,
      event,
      data,
    });
  }
}

// Export singleton instance
export const structuredLogger = new StructuredLogger();

// Export convenience functions
export const logInfo = (message: string, context?: LogContext) =>
  structuredLogger.info(message, context);

export const logWarn = (message: string, context?: LogContext) =>
  structuredLogger.warn(message, context);

export const logError = (message: string, error?: Error | unknown, context?: LogContext) =>
  structuredLogger.error(message, error, context);

export const logDebug = (message: string, context?: LogContext) =>
  structuredLogger.debug(message, context);

export const logHttpRequest = (req: Request, res: any) =>
  structuredLogger.httpRequest(req, res);

export const logApiCall = (
  service: string,
  endpoint: string,
  method: string,
  statusCode: number,
  duration: number,
  context?: LogContext
) => structuredLogger.apiCall(service, endpoint, method, statusCode, duration, context);

export const logJob = (jobName: string, status: 'started' | 'completed' | 'failed', context?: LogContext) =>
  structuredLogger.job(jobName, status, context);

export const logAuth = (action: 'login' | 'logout' | 'register' | 'failed', userId?: number, context?: LogContext) =>
  structuredLogger.auth(action, userId, context);

export const logSecurity = (event: string, severity: 'low' | 'medium' | 'high', context?: LogContext) =>
  structuredLogger.security(event, severity, context);

export const logPerformance = (operation: string, duration: number, context?: LogContext) =>
  structuredLogger.performance(operation, duration, context);

export const logBusinessEvent = (event: string, data: any, context?: LogContext) =>
  structuredLogger.businessEvent(event, data, context);

export default structuredLogger;
