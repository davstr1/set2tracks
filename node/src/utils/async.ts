/**
 * Async Utilities
 * Helper functions for handling async operations
 */

import { Request, Response, NextFunction } from 'express';

/**
 * Async handler wrapper
 * Automatically catches errors from async route handlers and passes to error middleware
 */
export function asyncHandler(
  fn: (req: Request, res: Response, next: NextFunction) => Promise<void>
) {
  return (req: Request, res: Response, next: NextFunction): void => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
}

/**
 * Execute promises with a timeout
 * Rejects if promise doesn't resolve within timeoutMs
 */
export function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  errorMessage: string = 'Operation timed out'
): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(errorMessage)), timeoutMs)
    ),
  ]);
}

/**
 * Execute promises in batches with concurrency limit
 */
export async function batchExecute<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  concurrency: number = 5
): Promise<R[]> {
  const results: R[] = [];
  const executing: Promise<void>[] = [];

  for (const item of items) {
    const promise = fn(item).then(result => {
      results.push(result);
    });

    executing.push(promise);

    if (executing.length >= concurrency) {
      await Promise.race(executing);
      // Remove completed promises
      executing.splice(
        executing.findIndex(p => p === promise),
        1
      );
    }
  }

  await Promise.all(executing);
  return results;
}

/**
 * Retry a promise with exponential backoff
 */
export async function retry<T>(
  fn: () => Promise<T>,
  options: {
    maxAttempts?: number;
    delayMs?: number;
    backoffMultiplier?: number;
    onRetry?: (attempt: number, error: Error) => void;
  } = {}
): Promise<T> {
  const {
    maxAttempts = 3,
    delayMs = 1000,
    backoffMultiplier = 2,
    onRetry,
  } = options;

  let lastError: Error;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt < maxAttempts) {
        const delay = delayMs * Math.pow(backoffMultiplier, attempt - 1);

        if (onRetry) {
          onRetry(attempt, lastError);
        }

        await sleep(delay);
      }
    }
  }

  throw lastError!;
}

/**
 * Sleep for specified milliseconds
 */
export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Execute function with debounce
 * Returns a debounced version of the function
 */
export function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;

  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delayMs);
  };
}

/**
 * Execute function with throttle
 * Returns a throttled version of the function
 */
export function throttle<T extends (...args: any[]) => any>(
  fn: T,
  delayMs: number
): (...args: Parameters<T>) => void {
  let lastCall = 0;

  return (...args: Parameters<T>) => {
    const now = Date.now();

    if (now - lastCall >= delayMs) {
      lastCall = now;
      fn(...args);
    }
  };
}
