import rateLimit from 'express-rate-limit';
import { Request } from 'express';

/**
 * General API rate limiter
 * Limits each IP to 100 requests per 15 minutes
 */
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true, // Return rate limit info in the `RateLimit-*` headers
  legacyHeaders: false, // Disable the `X-RateLimit-*` headers
  // Skip successful requests from being counted (optional)
  skipSuccessfulRequests: false,
});

/**
 * Strict limiter for authentication endpoints
 * Limits each IP to 5 attempts per 15 minutes
 */
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts from this IP, please try again after 15 minutes.',
  standardHeaders: true,
  legacyHeaders: false,
  skipSuccessfulRequests: true, // Don't count successful logins
  skipFailedRequests: false, // Count failed attempts
});

/**
 * Queue submission limiter (per user)
 * Limits to 10 queue submissions per hour per user
 */
export const queueLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // 10 queue submissions per hour
  message: 'Queue limit reached. You can submit up to 10 sets per hour. Please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req: Request) => {
    // Use user ID instead of IP for authenticated requests
    const user = req.user as any;
    return user?.id?.toString() || req.ip || 'unknown';
  },
  skip: (req: Request) => {
    // Skip rate limiting for admin users
    const user = req.user as any;
    return user?.type === 'Admin';
  },
});

/**
 * Registration limiter
 * Limits each IP to 3 registrations per hour
 */
export const registrationLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // 3 registrations per hour
  message: 'Too many accounts created from this IP, please try again after an hour.',
  standardHeaders: true,
  legacyHeaders: false,
});

/**
 * Password reset limiter
 * Limits each IP to 3 password reset requests per hour
 */
export const passwordResetLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 3, // 3 requests per hour
  message: 'Too many password reset attempts, please try again after an hour.',
  standardHeaders: true,
  legacyHeaders: false,
});
