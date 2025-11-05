/**
 * Base DTO Types
 * Common response structures and wrappers
 */

/**
 * Standard API success response wrapper
 */
export interface ApiResponse<T> {
  status: 'success';
  data: T;
  message?: string;
}

/**
 * Standard API error response
 */
export interface ApiErrorResponse {
  status: 'error';
  code: string;
  message: string;
  details?: unknown;
  stack?: string;
}

/**
 * Pagination metadata
 */
export interface PaginationMeta {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

/**
 * Paginated response wrapper
 */
export interface PaginatedResponse<T> {
  items: T[];
  pagination: PaginationMeta;
}

/**
 * Simple list response
 */
export interface ListResponse<T> {
  items: T[];
  count: number;
}

/**
 * Search response with query metadata
 */
export interface SearchResponse<T> {
  items: T[];
  query: string;
  count: number;
}

/**
 * Success/failure operation result
 */
export interface OperationResult {
  success: boolean;
  message?: string;
}

/**
 * Timestamps for entities
 */
export interface Timestamps {
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Helper to create success response
 */
export function createSuccessResponse<T>(data: T, message?: string): ApiResponse<T> {
  return {
    status: 'success',
    data,
    ...(message && { message }),
  };
}

/**
 * Helper to create paginated response
 */
export function createPaginatedResponse<T>(
  items: T[],
  page: number,
  limit: number,
  total: number
): PaginatedResponse<T> {
  return {
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
}

/**
 * Helper to create search response
 */
export function createSearchResponse<T>(items: T[], query: string): SearchResponse<T> {
  return {
    items,
    query,
    count: items.length,
  };
}
