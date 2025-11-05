import { param, query } from 'express-validator';

/**
 * Channel Validators
 * Validation rules for channel-related endpoints
 */

/**
 * Validator: Get channel by database ID
 * GET /channel/:id
 */
export const getChannelByIdValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('Channel ID must be a positive integer')
    .toInt(),
];

/**
 * Validator: Browse/Search channels with pagination
 * GET /channel, /channel/search, /channel/popular
 */
export const browseChannelValidator = [
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

  query('q')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 200 })
    .withMessage('Search query too long (max 200 characters)'),

  query('sortBy')
    .optional()
    .isIn(['sets', 'subscribers', 'recent', 'name'])
    .withMessage('Invalid sort option'),

  query('order')
    .optional()
    .isIn(['asc', 'desc'])
    .withMessage('Order must be asc or desc'),

  query('minSets')
    .optional()
    .isInt({ min: 0 })
    .withMessage('Minimum sets must be a non-negative integer')
    .toInt(),

  query('followable')
    .optional()
    .isBoolean()
    .withMessage('Followable must be a boolean')
    .toBoolean(),
];
