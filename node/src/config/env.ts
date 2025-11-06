import { cleanEnv, str, port, url, email, bool } from 'envalid';

/**
 * Environment Variable Validation
 *
 * This file validates all required environment variables at startup.
 * If any required variable is missing or invalid, the application will
 * fail fast with a clear error message.
 *
 * Benefits:
 * - Catch configuration errors early (at startup, not at runtime)
 * - Clear error messages for missing/invalid variables
 * - Type-safe environment access
 * - Self-documenting configuration requirements
 */

export const env = cleanEnv(process.env, {
  // ========================================
  // Application
  // ========================================
  NODE_ENV: str({
    choices: ['development', 'production', 'test'],
    default: 'development',
    desc: 'Application environment',
  }),

  PORT: port({
    default: 3000,
    desc: 'Port to run the application on',
  }),

  BASE_URL: url({
    default: 'http://localhost:3000',
    desc: 'Base URL of the application',
  }),

  // ========================================
  // Database
  // ========================================
  DATABASE_URL: str({
    desc: 'PostgreSQL connection string (required)',
    example: 'postgresql://user:pass@localhost:5432/set2tracks',
  }),

  // ========================================
  // Redis
  // ========================================
  REDIS_HOST: str({
    default: 'localhost',
    desc: 'Redis host',
  }),

  REDIS_PORT: port({
    default: 6379,
    desc: 'Redis port',
  }),

  REDIS_PASSWORD: str({
    default: '',
    desc: 'Redis password (empty for no auth)',
  }),

  // ========================================
  // Security
  // ========================================
  SESSION_SECRET: str({
    minLength: 32,
    desc: 'Secret for signing session cookies (min 32 characters)',
    example: 'your-super-secret-session-key-min-32-chars',
  }),

  JWT_SECRET: str({
    minLength: 32,
    default: '',
    desc: 'Secret for JWT tokens (min 32 characters, optional)',
  }),

  // ========================================
  // External APIs
  // ========================================
  YOUTUBE_API_KEY: str({
    default: '',
    desc: 'YouTube Data API v3 key (optional)',
  }),

  SPOTIFY_CLIENT_ID: str({
    default: '',
    desc: 'Spotify API client ID (optional)',
  }),

  SPOTIFY_CLIENT_SECRET: str({
    default: '',
    desc: 'Spotify API client secret (optional)',
  }),

  GOOGLE_CLIENT_ID: str({
    default: '',
    desc: 'Google OAuth client ID (optional)',
  }),

  GOOGLE_CLIENT_SECRET: str({
    default: '',
    desc: 'Google OAuth client secret (optional)',
  }),

  GOOGLE_CALLBACK_URL: url({
    default: 'http://localhost:3000/auth/google/callback',
    desc: 'Google OAuth callback URL',
  }),

  // ========================================
  // Email
  // ========================================
  MAIL_SERVER: str({
    default: 'smtp.example.com',
    desc: 'SMTP server hostname',
  }),

  MAIL_PORT: port({
    default: 587,
    desc: 'SMTP server port',
  }),

  MAIL_USER: str({
    default: 'noreply@set2tracks.com',
    desc: 'SMTP username/email',
  }),

  MAIL_PASSWORD: str({
    default: '',
    desc: 'SMTP password',
  }),

  MAIL_FROM: str({
    default: 'Set2Tracks <noreply@set2tracks.com>',
    desc: 'Email "From" address',
  }),

  MAIL_TLS: bool({
    default: true,
    desc: 'Use TLS for SMTP',
  }),

  // ========================================
  // Application Settings
  // ========================================
  ALLOW_SITE_SIGNUP: bool({
    default: false,
    desc: 'Allow public registration (true/false)',
  }),

  ALLOW_GOOGLE_SIGNUP: bool({
    default: false,
    desc: 'Allow Google OAuth registration (true/false)',
  }),

  ALLOW_INVITE_SIGNUP: bool({
    default: true,
    desc: 'Allow invite-only registration (true/false)',
  }),

  LANGUAGES: str({
    default: 'en,fr,de,es',
    desc: 'Comma-separated list of supported languages',
  }),

  // ========================================
  // Logging
  // ========================================
  LOG_LEVEL: str({
    choices: ['error', 'warn', 'info', 'debug'],
    default: 'info',
    desc: 'Logging level',
  }),

  // ========================================
  // File Upload
  // ========================================
  UPLOAD_MAX_SIZE: str({
    default: '10mb',
    desc: 'Maximum file upload size',
  }),

  // ========================================
  // Worker/Queue
  // ========================================
  QUEUE_REDIS_HOST: str({
    default: 'localhost',
    desc: 'Redis host for Bull queue',
  }),

  QUEUE_REDIS_PORT: port({
    default: 6379,
    desc: 'Redis port for Bull queue',
  }),
});

/**
 * Type-safe access to environment variables
 * Use this instead of process.env
 */
export default env;
