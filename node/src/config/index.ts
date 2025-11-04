import dotenv from 'dotenv';
import path from 'path';

// Load environment variables
dotenv.config();

interface Config {
  // Environment
  env: string;
  nodeEnv: string;
  port: number;

  // Database
  database: {
    primary: {
      host: string;
      port: number;
      name: string;
      username: string;
      password: string;
      url: string;
    };
    secondary?: {
      host: string;
      port: number;
      name: string;
      username: string;
      password: string;
      url: string;
    };
    tables: {
      users: string;
      invites: string;
    };
  };

  // Security
  security: {
    secretKey: string;
    sessionSecret: string;
    passwordSaltLength: number;
    passwordHashMethod: string;
  };

  // Mail
  mail: {
    server: string;
    port: number;
    useTLS: boolean;
    username: string;
    password: string;
    defaultSender: string;
  };

  // OAuth
  oauth: {
    google: {
      clientId: string;
      clientSecret: string;
      callbackUrl: string;
    };
  };

  // External APIs
  apis: {
    spotify: {
      clientId: string;
      clientSecret: string;
      redirectUri: string;
    };
    apple: {
      keyId: string;
      teamId: string;
      privateKey: string;
      tokenExpiryLength: number;
    };
    recognition: {
      acrcloud?: {
        host: string;
        accessKey: string;
        accessSecret: string;
      };
      audd?: {
        apiToken: string;
      };
      maxRetries: number;
      retryDelay: number;
      maxConcurrent: number;
    };
    shazam: {
      proxyUrl?: string;
    };
  };

  // Proxy
  proxy: {
    socks5?: string;
    http?: string;
  };

  // Application
  app: {
    baseUrl: string;
    adminUid: string;
    audioSegmentsLength: number;
    languages: string[];
    preferredUrlScheme: string;
  };

  // Redis
  redis: {
    host: string;
    port: number;
    password?: string;
  };

  // File Upload
  upload: {
    directory: string;
    tempDirectory: string;
    maxFileSize: number;
  };

  // Logging
  logging: {
    level: string;
    configFile: string;
  };

  // Signup Options
  signup: {
    allowSite: boolean;
    allowGoogle: boolean;
    allowInvite: boolean;
  };
}

function getEnvVar(key: string, defaultValue?: string): string {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value || defaultValue || '';
}

function getEnvVarNumber(key: string, defaultValue?: number): number {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value ? parseInt(value, 10) : (defaultValue || 0);
}

function getEnvVarBoolean(key: string, defaultValue?: boolean): boolean {
  const value = process.env[key];
  if (value === undefined && defaultValue === undefined) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value ? value.toLowerCase() === 'true' : (defaultValue || false);
}

const env = getEnvVar('ENV', 'dev');
const preferredUrlScheme = env === 'dev' ? 'http' : 'https';

// Build database URLs
const primaryDbUrl = `postgresql://${getEnvVar('DB_USERNAME')}:${getEnvVar('DB_PASSWORD')}@${getEnvVar('DB_HOST')}:${getEnvVarNumber('DB_PORT', 5432)}/${getEnvVar('DB_NAME')}`;

let secondaryDbUrl: string | undefined;
if (process.env.DB_USERNAME2 && process.env.DB_PASSWORD2) {
  secondaryDbUrl = `postgresql://${getEnvVar('DB_USERNAME2')}:${getEnvVar('DB_PASSWORD2')}@${getEnvVar('DB_HOST2', 'localhost')}:${getEnvVarNumber('DB_PORT2', 5432)}/${getEnvVar('DB_NAME2', 'dummy_db')}`;
}

const config: Config = {
  env,
  nodeEnv: getEnvVar('NODE_ENV', 'development'),
  port: getEnvVarNumber('PORT', 8080),

  database: {
    primary: {
      host: getEnvVar('DB_HOST'),
      port: getEnvVarNumber('DB_PORT', 5432),
      name: getEnvVar('DB_NAME'),
      username: getEnvVar('DB_USERNAME'),
      password: getEnvVar('DB_PASSWORD'),
      url: primaryDbUrl,
    },
    secondary: secondaryDbUrl ? {
      host: getEnvVar('DB_HOST2', 'localhost'),
      port: getEnvVarNumber('DB_PORT2', 5432),
      name: getEnvVar('DB_NAME2', 'dummy_db'),
      username: getEnvVar('DB_USERNAME2', 'dummy_user'),
      password: getEnvVar('DB_PASSWORD2', 'dummy_pass'),
      url: secondaryDbUrl,
    } : undefined,
    tables: {
      users: getEnvVar('DB_TABLE_USERS'),
      invites: getEnvVar('DB_TABLE_INVITES'),
    },
  },

  security: {
    secretKey: getEnvVar('SECRET_KEY'),
    sessionSecret: getEnvVar('SESSION_SECRET', getEnvVar('SECRET_KEY')),
    passwordSaltLength: getEnvVarNumber('PWD_SALT_LENGTH', 29),
    passwordHashMethod: getEnvVar('PWD_HASH_METHOD', 'pbkdf2:sha256'),
  },

  mail: {
    server: getEnvVar('MAIL_SERVER'),
    port: getEnvVarNumber('MAIL_PORT', 587),
    useTLS: getEnvVarBoolean('MAIL_USE_TLS', true),
    username: getEnvVar('MAIL_USERNAME'),
    password: getEnvVar('MAIL_PASSWORD'),
    defaultSender: getEnvVar('MAIL_DEFAULT_SENDER'),
  },

  oauth: {
    google: {
      clientId: getEnvVar('GOOGLE_CLIENT_ID'),
      clientSecret: getEnvVar('GOOGLE_CLIENT_SECRET'),
      callbackUrl: getEnvVar('GOOGLE_CALLBACK_URL', `${preferredUrlScheme}://localhost:8080/auth/google/callback`),
    },
  },

  apis: {
    spotify: {
      clientId: getEnvVar('SPOTIFY_CLIENT_ID'),
      clientSecret: getEnvVar('SPOTIFY_CLIENT_SECRET'),
      redirectUri: getEnvVar('SPOTIPY_REDIRECT_URI', `${preferredUrlScheme}://localhost:8080/spotify/callback`),
    },
    apple: {
      keyId: getEnvVar('APPLE_KEY_ID', ''),
      teamId: getEnvVar('APPLE_TEAM_ID', ''),
      privateKey: getEnvVar('APPLE_PRIVATE_KEY', '').replace(/\\n/g, '\n'),
      tokenExpiryLength: getEnvVarNumber('APPLE_TOKEN_EXPIRY_LENGTH', 15552000),
    },
    recognition: {
      acrcloud: process.env.ACRCLOUD_ACCESS_KEY ? {
        host: getEnvVar('ACRCLOUD_HOST', 'identify-us-west-2.acrcloud.com'),
        accessKey: getEnvVar('ACRCLOUD_ACCESS_KEY'),
        accessSecret: getEnvVar('ACRCLOUD_ACCESS_SECRET'),
      } : undefined,
      audd: process.env.AUDD_API_TOKEN ? {
        apiToken: getEnvVar('AUDD_API_TOKEN'),
      } : undefined,
      maxRetries: getEnvVarNumber('RECOGNITION_MAX_RETRIES', 3),
      retryDelay: getEnvVarNumber('RECOGNITION_RETRY_DELAY', 1000),
      maxConcurrent: getEnvVarNumber('RECOGNITION_MAX_CONCURRENT', 10),
    },
    shazam: {
      proxyUrl: process.env.SHAZAM_PROXY_URL,
    },
  },

  proxy: {
    socks5: process.env.PROXY_URL_SOCKS5,
    http: process.env.PROXY_URL_HTTP,
  },

  app: {
    baseUrl: getEnvVar('BASE_URL', `${preferredUrlScheme}://localhost:8080`),
    adminUid: getEnvVar('ADMIN_UID', '1'),
    audioSegmentsLength: getEnvVarNumber('AUDIO_SEGMENTS_LENGTH', 10),
    languages: ['en', 'es', 'fr'],
    preferredUrlScheme,
  },

  redis: {
    host: getEnvVar('REDIS_HOST', 'localhost'),
    port: getEnvVarNumber('REDIS_PORT', 6379),
    password: process.env.REDIS_PASSWORD,
  },

  upload: {
    directory: getEnvVar('UPLOAD_DIR', path.join(__dirname, '../../uploads')),
    tempDirectory: getEnvVar('TEMP_DIR', path.join(__dirname, '../../temp')),
    maxFileSize: getEnvVarNumber('MAX_FILE_SIZE', 104857600), // 100MB
  },

  logging: {
    level: getEnvVar('LOG_LEVEL', 'info'),
    configFile: getEnvVar('LOGGING_CONFIG_FILE', './config/logging.json'),
  },

  signup: {
    allowSite: getEnvVarBoolean('SIGNUP_ALLOW_SITE', true),
    allowGoogle: getEnvVarBoolean('SIGNUP_ALLOW_GOOGLE', true),
    allowInvite: getEnvVarBoolean('SIGNUP_ALLOW_INVITE', true),
  },
};

export default config;
