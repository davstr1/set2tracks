import { Request, Response, NextFunction } from 'express';
import { User } from '@prisma/client';
import config from '../config';

/**
 * Authentication middleware
 */

/**
 * Ensure user is authenticated
 */
export function requireAuth(req: Request, res: Response, next: NextFunction) {
  if (req.isAuthenticated()) {
    return next();
  }

  // API request - return 401
  if (req.path.startsWith('/api/')) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  // Web request - redirect to login
  res.redirect('/auth/login?redirect=' + encodeURIComponent(req.originalUrl));
}

/**
 * Ensure user is NOT authenticated (for login/register pages)
 */
export function requireGuest(req: Request, res: Response, next: NextFunction) {
  if (req.isAuthenticated()) {
    return res.redirect('/');
  }
  next();
}

/**
 * Ensure user is an admin
 */
export function requireAdmin(req: Request, res: Response, next: NextFunction) {
  if (!req.isAuthenticated()) {
    if (req.path.startsWith('/api/')) {
      return res.status(401).json({ error: 'Authentication required' });
    }
    return res.redirect('/auth/login');
  }

  const user = req.user as User;
  if (user.type !== 'Admin') {
    if (req.path.startsWith('/api/')) {
      return res.status(403).json({ error: 'Admin access required' });
    }
    return res.status(403).render('error.njk', {
      title: '403 - Forbidden',
      message: 'Admin access required',
    });
  }

  next();
}

/**
 * Optional auth - adds user to request if authenticated, but doesn't require it
 */
export function optionalAuth(req: Request, res: Response, next: NextFunction) {
  // User will be in req.user if authenticated via Passport
  next();
}

/**
 * Check if user can submit sets (rate limiting could be added here)
 */
export function canSubmitSet(req: Request, res: Response, next: NextFunction) {
  if (!req.isAuthenticated()) {
    const user = req.user as User;

    // Premium users have higher limits (could implement this)
    // For now, just check if authenticated
  }

  next();
}

/**
 * Attach user info to response locals for templates
 */
export function attachUser(req: Request, res: Response, next: NextFunction) {
  res.locals.user = req.user || null;
  res.locals.isAuthenticated = req.isAuthenticated();
  next();
}
