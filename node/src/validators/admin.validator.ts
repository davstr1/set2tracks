import { body, param, query } from 'express-validator';

/**
 * Admin Validators
 * Validation rules for admin-related endpoints
 */

/**
 * Validator: Get user by ID
 * GET /admin/users/:id
 */
export const getUserByIdValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('User ID must be a positive integer')
    .toInt(),
];

/**
 * Validator: Update user
 * POST /admin/users/:id
 */
export const updateUserValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('User ID must be a positive integer')
    .toInt(),

  body('role')
    .optional()
    .isIn(['user', 'admin'])
    .withMessage('Role must be either user or admin'),

  body('premium')
    .optional()
    .isBoolean()
    .withMessage('Premium must be a boolean')
    .toBoolean(),

  body('active')
    .optional()
    .isBoolean()
    .withMessage('Active must be a boolean')
    .toBoolean(),
];

/**
 * Validator: Toggle set visibility
 * POST /admin/sets/:id/toggle-visibility
 */
export const toggleSetVisibilityValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('Set ID must be a positive integer')
    .toInt(),

  body('hidden')
    .isBoolean()
    .withMessage('Hidden must be a boolean')
    .toBoolean(),
];

/**
 * Validator: Update configuration
 * POST /admin/config
 */
export const updateConfigValidator = [
  body('maxSetsPerUser')
    .optional()
    .isInt({ min: 1, max: 1000 })
    .withMessage('Max sets per user must be between 1 and 1000')
    .toInt(),

  body('maxSetDuration')
    .optional()
    .isInt({ min: 60, max: 28800 })
    .withMessage('Max set duration must be between 60 and 28800 seconds (1 min - 8 hours)')
    .toInt(),

  body('requireInvite')
    .optional()
    .isBoolean()
    .withMessage('Require invite must be a boolean')
    .toBoolean(),

  body('maintenanceMode')
    .optional()
    .isBoolean()
    .withMessage('Maintenance mode must be a boolean')
    .toBoolean(),
];

/**
 * Validator: Browse users with pagination
 * GET /admin/users
 */
export const browseUsersValidator = [
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Page must be a positive integer')
    .toInt(),

  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100')
    .toInt(),

  query('search')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 200 })
    .withMessage('Search query too long (max 200 characters)'),

  query('role')
    .optional()
    .isIn(['user', 'admin', 'all'])
    .withMessage('Role must be user, admin, or all'),

  query('premium')
    .optional()
    .isBoolean()
    .withMessage('Premium must be a boolean')
    .toBoolean(),
];
