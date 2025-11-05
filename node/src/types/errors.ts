/**
 * Custom Error Types
 * Type-safe error handling with custom error class hierarchy
 */

export interface ErrorWithMessage {
  message: string;
}

export interface ErrorWithCode extends ErrorWithMessage {
  code?: string;
  statusCode?: number;
}

export function isErrorWithMessage(error: unknown): error is ErrorWithMessage {
  return (
    typeof error === 'object' &&
    error !== null &&
    'message' in error &&
    typeof (error as Record<string, unknown>).message === 'string'
  );
}

export function toErrorWithMessage(maybeError: unknown): ErrorWithMessage {
  if (isErrorWithMessage(maybeError)) return maybeError;

  try {
    return new Error(JSON.stringify(maybeError));
  } catch {
    // fallback in case there's an error stringifying
    return new Error(String(maybeError));
  }
}

export function getErrorMessage(error: unknown): string {
  return toErrorWithMessage(error).message;
}

export function getErrorCode(error: unknown): string | undefined {
  if (
    typeof error === 'object' &&
    error !== null &&
    'code' in error &&
    typeof (error as Record<string, unknown>).code === 'string'
  ) {
    return (error as ErrorWithCode).code;
  }
  return undefined;
}

/**
 * Custom Error Class Hierarchy
 */

/**
 * Base Application Error
 * All custom errors extend from this class
 */
export class AppError extends Error {
  public readonly statusCode: number;
  public readonly isOperational: boolean;
  public readonly code?: string;
  public readonly details?: unknown;

  constructor(
    message: string,
    statusCode: number = 500,
    isOperational: boolean = true,
    code?: string,
    details?: unknown
  ) {
    super(message);
    Object.setPrototypeOf(this, new.target.prototype);

    this.statusCode = statusCode;
    this.isOperational = isOperational;
    this.code = code;
    this.details = details;

    this.name = this.constructor.name;
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * 400 Bad Request - Invalid input or request
 */
export class BadRequestError extends AppError {
  constructor(message: string = 'Bad Request', details?: unknown) {
    super(message, 400, true, 'BAD_REQUEST', details);
  }
}

/**
 * 401 Unauthorized - Authentication required
 */
export class UnauthorizedError extends AppError {
  constructor(message: string = 'Unauthorized', details?: unknown) {
    super(message, 401, true, 'UNAUTHORIZED', details);
  }
}

/**
 * 403 Forbidden - Insufficient permissions
 */
export class ForbiddenError extends AppError {
  constructor(message: string = 'Forbidden', details?: unknown) {
    super(message, 403, true, 'FORBIDDEN', details);
  }
}

/**
 * 404 Not Found - Resource doesn't exist
 */
export class NotFoundError extends AppError {
  constructor(resource: string = 'Resource', id?: string | number) {
    const message = id
      ? `${resource} with ID '${id}' not found`
      : `${resource} not found`;
    super(message, 404, true, 'NOT_FOUND', { resource, id });
  }
}

/**
 * 409 Conflict - Resource already exists
 */
export class ConflictError extends AppError {
  constructor(message: string = 'Resource already exists', details?: unknown) {
    super(message, 409, true, 'CONFLICT', details);
  }
}

/**
 * 422 Unprocessable Entity - Validation failed
 */
export class ValidationError extends AppError {
  constructor(message: string = 'Validation failed', details?: unknown) {
    super(message, 422, true, 'VALIDATION_ERROR', details);
  }
}

/**
 * 429 Too Many Requests - Rate limit exceeded
 */
export class RateLimitError extends AppError {
  constructor(message: string = 'Too many requests', retryAfter?: number) {
    super(message, 429, true, 'RATE_LIMIT', { retryAfter });
  }
}

/**
 * 500 Internal Server Error - Unexpected server error
 */
export class InternalError extends AppError {
  constructor(message: string = 'Internal server error', details?: unknown) {
    super(message, 500, false, 'INTERNAL_ERROR', details);
  }
}

/**
 * 503 Service Unavailable - External service error
 */
export class ServiceUnavailableError extends AppError {
  constructor(service: string, message?: string) {
    const errorMessage = message || `${service} is currently unavailable`;
    super(errorMessage, 503, true, 'SERVICE_UNAVAILABLE', { service });
  }
}

/**
 * Authentication Error - General auth issues
 */
export class AuthError extends AppError {
  constructor(message: string = 'Authentication failed', details?: unknown) {
    super(message, 401, true, 'AUTH_ERROR', details);
  }
}

/**
 * Database Error - Database operation failures
 */
export class DatabaseError extends AppError {
  constructor(message: string = 'Database error', details?: unknown) {
    super(message, 500, false, 'DATABASE_ERROR', details);
  }
}

/**
 * External API Error - Third-party API failures
 */
export class ExternalAPIError extends AppError {
  constructor(apiName: string, message?: string, details?: unknown) {
    const errorMessage = message || `${apiName} API error`;
    super(errorMessage, 502, true, 'EXTERNAL_API_ERROR', { apiName, ...details });
  }
}

/**
 * Type guard to check if error is AppError
 */
export function isAppError(error: unknown): error is AppError {
  return error instanceof AppError;
}
