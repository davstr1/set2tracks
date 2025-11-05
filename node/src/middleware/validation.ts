import { Request, Response, NextFunction } from 'express';
import { validationResult, ValidationChain } from 'express-validator';
import logger from '../utils/logger';

/**
 * Validation Middleware
 *
 * Handles validation errors from express-validator and returns
 * user-friendly error messages
 */

/**
 * Middleware to check validation results
 */
export const validate = (req: Request, res: Response, next: NextFunction): void => {
  const errors = validationResult(req);

  if (!errors.isEmpty()) {
    const errorMessages = errors.array().map(err => ({
      field: err.type === 'field' ? (err as any).path : 'unknown',
      message: err.msg,
      value: err.type === 'field' ? (err as any).value : undefined,
    }));

    logger.warn('Validation failed', {
      path: req.path,
      method: req.method,
      errors: errorMessages,
    });

    res.status(400).json({
      status: 'error',
      message: 'Validation failed',
      errors: errorMessages,
    });
    return;
  }

  next();
};

/**
 * Helper to run validation chains and check results
 *
 * Usage in routes:
 * router.post('/endpoint',
 *   validateRequest([
 *     body('email').isEmail(),
 *     body('password').isLength({ min: 8 })
 *   ]),
 *   controller.method
 * );
 */
export const validateRequest = (validations: ValidationChain[]) => {
  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    // Run all validations
    await Promise.all(validations.map(validation => validation.run(req)));

    // Check results
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      const errorMessages = errors.array().map(err => ({
        field: err.type === 'field' ? (err as any).path : 'unknown',
        message: err.msg,
        value: err.type === 'field' ? (err as any).value : undefined,
      }));

      logger.warn('Validation failed', {
        path: req.path,
        method: req.method,
        errors: errorMessages,
      });

      res.status(400).json({
        status: 'error',
        message: 'Validation failed',
        errors: errorMessages,
      });
      return;
    }

    next();
  };
};

/**
 * Common validation chains for reuse
 */
export const commonValidations = {
  // Pagination
  page: () => ({
    in: ['query'],
    optional: true,
    isInt: {
      options: { min: 1 },
      errorMessage: 'Page must be a positive integer',
    },
    toInt: true,
  }),

  limit: () => ({
    in: ['query'],
    optional: true,
    isInt: {
      options: { min: 1, max: 100 },
      errorMessage: 'Limit must be between 1 and 100',
    },
    toInt: true,
  }),

  // ID parameters
  id: () => ({
    in: ['params'],
    isInt: {
      options: { min: 1 },
      errorMessage: 'ID must be a positive integer',
    },
    toInt: true,
  }),

  // YouTube video ID
  videoId: () => ({
    in: ['body'],
    isString: {
      errorMessage: 'Video ID must be a string',
    },
    trim: true,
    notEmpty: {
      errorMessage: 'Video ID is required',
    },
    isLength: {
      options: { min: 11, max: 11 },
      errorMessage: 'Video ID must be exactly 11 characters',
    },
    matches: {
      options: /^[a-zA-Z0-9_-]{11}$/,
      errorMessage: 'Video ID contains invalid characters',
    },
  }),

  // Email
  email: () => ({
    in: ['body'],
    isEmail: {
      errorMessage: 'Invalid email address',
    },
    normalizeEmail: true,
    trim: true,
  }),

  // Password
  password: () => ({
    in: ['body'],
    isString: {
      errorMessage: 'Password must be a string',
    },
    isLength: {
      options: { min: 8, max: 128 },
      errorMessage: 'Password must be between 8 and 128 characters',
    },
  }),

  // Search query
  searchQuery: () => ({
    in: ['query'],
    isString: {
      errorMessage: 'Search query must be a string',
    },
    trim: true,
    notEmpty: {
      errorMessage: 'Search query cannot be empty',
    },
    isLength: {
      options: { min: 1, max: 200 },
      errorMessage: 'Search query must be between 1 and 200 characters',
    },
  }),

  // Boolean flags
  boolean: () => ({
    optional: true,
    isBoolean: {
      errorMessage: 'Must be a boolean value',
    },
    toBoolean: true,
  }),
};

export default {
  validate,
  validateRequest,
  commonValidations,
};
