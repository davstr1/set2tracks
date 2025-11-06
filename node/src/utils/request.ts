/**
 * Request Utilities
 * Helper functions for parsing and handling HTTP requests
 */

import { Request } from 'express';
import { PAGINATION } from '../config/constants';

/**
 * Parse integer from query parameter
 * Returns the parsed integer or default value if invalid
 */
export function parseQueryInt(
  value: unknown,
  defaultValue: number = 0
): number {
  if (typeof value === 'number') {
    return value;
  }

  if (typeof value === 'string') {
    const parsed = parseInt(value, 10);
    return isNaN(parsed) ? defaultValue : parsed;
  }

  return defaultValue;
}

/**
 * Parse pagination parameters from request
 * Returns page and limit with sensible defaults
 */
export function parsePagination(
  req: Request,
  options?: {
    defaultLimit?: number;
    maxLimit?: number;
  }
): { page: number; limit: number; skip: number } {
  const defaultLimit = options?.defaultLimit || PAGINATION.DEFAULT_PAGE_SIZE;
  const maxLimit = options?.maxLimit || PAGINATION.MAX_PAGE_SIZE;

  const page = parseQueryInt(req.query.page, 1);
  let limit = parseQueryInt(req.query.limit, defaultLimit);

  // Enforce max limit
  if (limit > maxLimit) {
    limit = maxLimit;
  }

  // Enforce min limit
  if (limit < PAGINATION.MIN_PAGE_SIZE) {
    limit = PAGINATION.MIN_PAGE_SIZE;
  }

  const skip = (page - 1) * limit;

  return { page, limit, skip };
}

/**
 * Parse boolean from query parameter
 * Handles strings like 'true', 'false', '1', '0'
 */
export function parseQueryBoolean(
  value: unknown,
  defaultValue: boolean = false
): boolean {
  if (typeof value === 'boolean') {
    return value;
  }

  if (typeof value === 'string') {
    const lower = value.toLowerCase();
    if (lower === 'true' || lower === '1' || lower === 'yes') {
      return true;
    }
    if (lower === 'false' || lower === '0' || lower === 'no') {
      return false;
    }
  }

  return defaultValue;
}

/**
 * Parse string array from query parameter
 * Handles comma-separated values
 */
export function parseQueryArray(
  value: unknown,
  separator: string = ','
): string[] {
  if (Array.isArray(value)) {
    return value.map(String);
  }

  if (typeof value === 'string') {
    return value.split(separator).map(s => s.trim()).filter(Boolean);
  }

  return [];
}

/**
 * Get user ID from request (for authenticated routes)
 * Returns null if user is not authenticated
 */
export function getUserId(req: Request): number | null {
  if (!req.user) {
    return null;
  }
  return (req.user as any).id || null;
}

/**
 * Check if user is admin
 */
export function isAdmin(req: Request): boolean {
  if (!req.user) {
    return false;
  }
  return (req.user as any).type === 'Admin';
}

/**
 * Validate required query parameters
 * Throws error if any required param is missing
 */
export function requireQueryParams(
  req: Request,
  params: string[]
): void {
  const missing = params.filter(param => !req.query[param]);

  if (missing.length > 0) {
    throw new Error(`Missing required query parameters: ${missing.join(', ')}`);
  }
}

/**
 * Validate required body fields
 * Throws error if any required field is missing
 */
export function requireBodyFields(
  req: Request,
  fields: string[]
): void {
  const missing = fields.filter(field => !req.body[field]);

  if (missing.length > 0) {
    throw new Error(`Missing required fields: ${missing.join(', ')}`);
  }
}
