/**
 * Validation Utilities
 * Helper functions for common validation tasks
 */

/**
 * Check if string is empty or only whitespace
 */
export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) {
    return true;
  }

  if (typeof value === 'string') {
    return value.trim().length === 0;
  }

  return false;
}

/**
 * Check if value is a valid email
 */
export function isValidEmail(email: unknown): boolean {
  if (typeof email !== 'string') {
    return false;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Check if value is a valid URL
 */
export function isValidUrl(url: unknown): boolean {
  if (typeof url !== 'string') {
    return false;
  }

  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

/**
 * Check if value is a valid YouTube video ID
 */
export function isValidYouTubeId(videoId: unknown): boolean {
  if (typeof videoId !== 'string') {
    return false;
  }

  // YouTube video IDs are 11 characters
  const youtubeIdRegex = /^[a-zA-Z0-9_-]{11}$/;
  return youtubeIdRegex.test(videoId);
}

/**
 * Check if value is within range
 */
export function isInRange(
  value: number,
  min: number,
  max: number
): boolean {
  return value >= min && value <= max;
}

/**
 * Check if string length is within range
 */
export function isLengthInRange(
  value: string,
  min: number,
  max: number
): boolean {
  const length = value.length;
  return length >= min && length <= max;
}

/**
 * Sanitize string by removing special characters
 */
export function sanitizeString(value: string): string {
  return value.replace(/[<>]/g, '');
}

/**
 * Normalize whitespace in string
 */
export function normalizeWhitespace(value: string): string {
  return value.replace(/\s+/g, ' ').trim();
}

/**
 * Check if array has items
 */
export function isNonEmptyArray(value: unknown): boolean {
  return Array.isArray(value) && value.length > 0;
}

/**
 * Check if object has properties
 */
export function isNonEmptyObject(value: unknown): boolean {
  return (
    typeof value === 'object' &&
    value !== null &&
    Object.keys(value).length > 0
  );
}

/**
 * Validate that value is one of allowed options
 */
export function isOneOf<T>(value: T, allowedValues: T[]): boolean {
  return allowedValues.includes(value);
}

/**
 * Check if date is in the past
 */
export function isInPast(date: Date): boolean {
  return date.getTime() < Date.now();
}

/**
 * Check if date is in the future
 */
export function isInFuture(date: Date): boolean {
  return date.getTime() > Date.now();
}

/**
 * Check if string contains only alphanumeric characters
 */
export function isAlphanumeric(value: string): boolean {
  return /^[a-zA-Z0-9]+$/.test(value);
}

/**
 * Check if string contains only alphabetic characters
 */
export function isAlpha(value: string): boolean {
  return /^[a-zA-Z]+$/.test(value);
}

/**
 * Check if string contains only numeric characters
 */
export function isNumeric(value: string): boolean {
  return /^[0-9]+$/.test(value);
}

/**
 * Check if value is a positive integer
 */
export function isPositiveInteger(value: unknown): boolean {
  if (typeof value !== 'number') {
    return false;
  }

  return Number.isInteger(value) && value > 0;
}

/**
 * Check if value is a non-negative integer
 */
export function isNonNegativeInteger(value: unknown): boolean {
  if (typeof value !== 'number') {
    return false;
  }

  return Number.isInteger(value) && value >= 0;
}
