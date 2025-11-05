import { body, param, query } from 'express-validator';

/**
 * Set Validators
 * Validation rules for set-related endpoints
 */

/**
 * Validator: Queue a new set for processing
 * POST /set/queue
 */
export const queueSetValidator = [
  body('videoId')
    .isString()
    .withMessage('Video ID must be a string')
    .trim()
    .notEmpty()
    .withMessage('Video ID is required')
    .isLength({ min: 11, max: 11 })
    .withMessage('Video ID must be exactly 11 characters')
    .matches(/^[a-zA-Z0-9_-]{11}$/)
    .withMessage('Video ID contains invalid characters'),

  body('userEmail')
    .optional()
    .isEmail()
    .withMessage('Invalid email address')
    .normalizeEmail()
    .trim(),
];

/**
 * Validator: Get set by video ID
 * GET /set/video/:videoId
 */
export const getSetByVideoIdValidator = [
  param('videoId')
    .isString()
    .trim()
    .notEmpty()
    .isLength({ min: 11, max: 11 })
    .matches(/^[a-zA-Z0-9_-]{11}$/)
    .withMessage('Invalid video ID format'),
];

/**
 * Validator: Get set by database ID
 * GET /set/:id
 */
export const getSetByIdValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('Set ID must be a positive integer')
    .toInt(),
];

/**
 * Validator: Search/Browse sets with pagination
 * GET /set, /set/search, /set/popular, /set/recent
 */
export const browseSetValidator = [
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

  query('channelId')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Channel ID must be a positive integer')
    .toInt(),

  query('genre')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 50 })
    .withMessage('Genre too long (max 50 characters)'),

  query('sortBy')
    .optional()
    .isIn(['recent', 'popular', 'duration', 'tracks'])
    .withMessage('Invalid sort option'),

  query('order')
    .optional()
    .isIn(['asc', 'desc'])
    .withMessage('Order must be asc or desc'),
];
