import { param, query } from 'express-validator';

/**
 * Track Validators
 * Validation rules for track-related endpoints
 */

/**
 * Validator: Get track by database ID
 * GET /track/:id
 */
export const getTrackByIdValidator = [
  param('id')
    .isInt({ min: 1 })
    .withMessage('Track ID must be a positive integer')
    .toInt(),
];

/**
 * Validator: Get track by Spotify ID
 * GET /track/spotify/:spotifyId
 */
export const getTrackBySpotifyIdValidator = [
  param('spotifyId')
    .isString()
    .trim()
    .notEmpty()
    .withMessage('Spotify ID is required')
    .isLength({ min: 22, max: 22 })
    .withMessage('Spotify ID must be exactly 22 characters')
    .matches(/^[a-zA-Z0-9]{22}$/)
    .withMessage('Invalid Spotify ID format'),
];

/**
 * Validator: Get tracks by genre/artist/label
 * GET /track/genre/:genre, /track/artist/:artist, /track/label/:label
 */
export const getTracksByMetadataValidator = [
  param('genre')
    .optional()
    .isString()
    .trim()
    .notEmpty()
    .isLength({ max: 100 })
    .withMessage('Genre too long (max 100 characters)'),

  param('artist')
    .optional()
    .isString()
    .trim()
    .notEmpty()
    .isLength({ max: 200 })
    .withMessage('Artist name too long (max 200 characters)'),

  param('label')
    .optional()
    .isString()
    .trim()
    .notEmpty()
    .isLength({ max: 200 })
    .withMessage('Label name too long (max 200 characters)'),
];

/**
 * Validator: Browse/Search tracks with pagination
 * GET /track, /track/search, /track/popular, /track/new
 */
export const browseTrackValidator = [
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

  query('genre')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 100 })
    .withMessage('Genre too long (max 100 characters)'),

  query('artist')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 200 })
    .withMessage('Artist name too long (max 200 characters)'),

  query('label')
    .optional()
    .isString()
    .trim()
    .isLength({ max: 200 })
    .withMessage('Label name too long (max 200 characters)'),

  query('bpmMin')
    .optional()
    .isInt({ min: 0, max: 300 })
    .withMessage('BPM min must be between 0 and 300')
    .toInt(),

  query('bpmMax')
    .optional()
    .isInt({ min: 0, max: 300 })
    .withMessage('BPM max must be between 0 and 300')
    .toInt(),

  query('sortBy')
    .optional()
    .isIn(['recent', 'popular', 'bpm', 'title', 'artist'])
    .withMessage('Invalid sort option'),

  query('order')
    .optional()
    .isIn(['asc', 'desc'])
    .withMessage('Order must be asc or desc'),
];
