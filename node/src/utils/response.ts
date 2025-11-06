/**
 * Response Utilities
 * Helper functions for formatting HTTP responses
 */

import { Response } from 'express';
import { PaginationMeta, ApiResponse } from '../types/dto';

/**
 * Send success response
 */
export function sendSuccess<T>(
  res: Response,
  data: T,
  message?: string,
  statusCode: number = 200
): void {
  const response: ApiResponse<T> = {
    status: 'success',
    data,
    ...(message && { message }),
  };

  res.status(statusCode).json(response);
}

/**
 * Send error response
 */
export function sendError(
  res: Response,
  message: string,
  statusCode: number = 400,
  code?: string,
  details?: unknown
): void {
  const response = {
    status: 'error',
    message,
    ...(code && { code }),
    ...(details && { details }),
  };

  res.status(statusCode).json(response);
}

/**
 * Send paginated response
 */
export function sendPaginated<T>(
  res: Response,
  items: T[],
  pagination: PaginationMeta
): void {
  res.json({
    items,
    pagination,
  });
}

/**
 * Send list response (without pagination)
 */
export function sendList<T>(
  res: Response,
  items: T[],
  key: string = 'items'
): void {
  res.json({
    [key]: items,
    count: items.length,
  });
}

/**
 * Send created response (201)
 */
export function sendCreated<T>(
  res: Response,
  data: T,
  message?: string
): void {
  sendSuccess(res, data, message, 201);
}

/**
 * Send no content response (204)
 */
export function sendNoContent(res: Response): void {
  res.status(204).send();
}

/**
 * Send not found response (404)
 */
export function sendNotFound(
  res: Response,
  resource: string = 'Resource',
  id?: string | number
): void {
  const message = id
    ? `${resource} with ID '${id}' not found`
    : `${resource} not found`;

  sendError(res, message, 404, 'NOT_FOUND', { resource, id });
}

/**
 * Send bad request response (400)
 */
export function sendBadRequest(
  res: Response,
  message: string = 'Bad request',
  details?: unknown
): void {
  sendError(res, message, 400, 'BAD_REQUEST', details);
}

/**
 * Send unauthorized response (401)
 */
export function sendUnauthorized(
  res: Response,
  message: string = 'Authentication required'
): void {
  sendError(res, message, 401, 'UNAUTHORIZED');
}

/**
 * Send forbidden response (403)
 */
export function sendForbidden(
  res: Response,
  message: string = 'Access forbidden'
): void {
  sendError(res, message, 403, 'FORBIDDEN');
}

/**
 * Send conflict response (409)
 */
export function sendConflict(
  res: Response,
  message: string,
  details?: unknown
): void {
  sendError(res, message, 409, 'CONFLICT', details);
}

/**
 * Send validation error response (422)
 */
export function sendValidationError(
  res: Response,
  errors: Array<{ field: string; message: string }>
): void {
  sendError(res, 'Validation failed', 422, 'VALIDATION_ERROR', { errors });
}
