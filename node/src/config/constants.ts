/**
 * Application Constants
 *
 * Centralized constants to replace magic numbers throughout the codebase.
 * Makes code more readable, maintainable, and self-documenting.
 */

/**
 * Pagination defaults
 */
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  DEFAULT_PAGE: 1,
  MAX_PAGE_SIZE: 100,
  MIN_PAGE_SIZE: 1,
} as const;

/**
 * Scheduler intervals (in milliseconds)
 */
export const SCHEDULER = {
  CHANNEL_CHECK_INTERVAL_MS: 10 * 60 * 1000, // 10 minutes - near real-time channel monitoring
  CLEANUP_INTERVAL_MS: 24 * 60 * 60 * 1000,  // 24 hours - daily cleanup
} as const;

/**
 * Job priorities (Bull queue)
 * Lower number = higher priority
 */
export const JOB_PRIORITY = {
  USER_SUBMITTED: 10,      // User-submitted sets (highest priority)
  AUTO_QUEUED: 20,         // Auto-queued from channel monitoring
  BACKGROUND: 30,          // Background processing
} as const;

/**
 * Concurrency limits
 */
export const CONCURRENCY = {
  MAX_SHAZAM_REQUESTS: 30,        // Max concurrent Shazam recognition requests
  MAX_YOUTUBE_DOWNLOADS: 5,        // Max concurrent YouTube downloads
  MAX_TRACK_RECOGNITIONS: 10,      // Max concurrent track recognitions
  MAX_LABEL_FETCHES: 30,           // Max concurrent label fetches
} as const;

/**
 * Retry configuration
 */
export const RETRY = {
  MAX_ATTEMPTS: 3,                 // Default max retry attempts
  BASE_DELAY_MS: 1000,             // Base delay between retries (1 second)
  EXPONENTIAL_BACKOFF_MS: [2000, 4000, 8000, 16000], // Exponential backoff delays
  SHAZAM_MAX_ATTEMPTS: 3,          // Max attempts for Shazam recognition
  SHAZAM_DELAY_MS: 2000,           // Delay between Shazam retries (2 seconds)
} as const;

/**
 * Timeouts (in milliseconds)
 */
export const TIMEOUT = {
  API_REQUEST_MS: 30000,           // 30 seconds - general API request timeout
  YOUTUBE_DOWNLOAD_MS: 300000,     // 5 minutes - YouTube download timeout
  SHAZAM_RECOGNITION_MS: 60000,    // 1 minute - Shazam recognition timeout
  DATABASE_QUERY_MS: 10000,        // 10 seconds - database query timeout
} as const;

/**
 * Rate limiting
 */
export const RATE_LIMIT = {
  WINDOW_MS: 15 * 60 * 1000,       // 15 minutes
  MAX_REQUESTS: 100,                // Max requests per window
  MAX_QUEUE_REQUESTS_PER_USER: 10, // Max sets a user can queue per window
} as const;

/**
 * Content limits
 */
export const LIMITS = {
  MAX_SET_DURATION_SECONDS: 28800,  // 8 hours max set duration
  MIN_SET_DURATION_SECONDS: 60,     // 1 minute min set duration
  MAX_TRACKS_PER_SET: 1000,         // Max tracks in a single set
  MAX_VIDEO_ID_LENGTH: 11,          // YouTube video ID length
  MAX_SEARCH_QUERY_LENGTH: 200,     // Max search query length
  MAX_CHANNEL_VIDEOS: 10,           // Max videos to check per channel
} as const;

/**
 * Session configuration
 */
export const SESSION = {
  MAX_AGE_MS: 7 * 24 * 60 * 60 * 1000, // 7 days
  COOKIE_NAME: 'sessionId',
} as const;

/**
 * HTTP status codes (for readability)
 */
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  NO_CONTENT: 204,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  CONFLICT: 409,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
} as const;

/**
 * File extensions
 */
export const FILE_EXTENSIONS = {
  AUDIO: '.mp3',
  VIDEO: '.mp4',
  METADATA: '.json',
} as const;

/**
 * Recognition configuration
 */
export const RECOGNITION = {
  CONFIDENCE_THRESHOLD: 80,         // Minimum confidence score (0-100)
  MIN_TRACK_DURATION_SECONDS: 30,   // Minimum track duration to recognize
} as const;

/**
 * Export all constants
 */
export default {
  PAGINATION,
  SCHEDULER,
  JOB_PRIORITY,
  CONCURRENCY,
  RETRY,
  TIMEOUT,
  RATE_LIMIT,
  LIMITS,
  SESSION,
  HTTP_STATUS,
  FILE_EXTENSIONS,
  RECOGNITION,
} as const;
