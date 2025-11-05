import express, { Application, Request, Response, NextFunction } from 'express';
import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';
import compression from 'compression';
import cors from 'cors';
import passport from 'passport';
import nunjucks from 'nunjucks';
import path from 'path';
import i18next from 'i18next';
import i18nextMiddleware from 'i18next-http-middleware';
import Backend from 'i18next-fs-backend';

import config from './config';
import logger from './utils/logger';
import { RedisClient } from './types/redis';
import { NunjucksFilterValue } from './types/nunjucks';

// Import passport config
import './middleware/passport';

// Import routes
import authRoutes from './routes/auth.routes';
import setRoutes from './routes/set.routes';
import trackRoutes from './routes/track.routes';
import channelRoutes from './routes/channel.routes';
import adminRoutes from './routes/admin.routes';
// import spotifyRoutes from './routes/spotify.routes';
// import playlistRoutes from './routes/playlist.routes';

// Import middleware
import { attachUser } from './middleware/auth';

class App {
  public app: Application;
  private redisClient: RedisClient;

  constructor() {
    this.app = express();
    this.initializeRedis();
    this.initializeMiddleware();
    this.initializeTemplateEngine();
    this.initializeI18n();
    this.initializePassport();
    this.initializeRoutes();
    this.initializeErrorHandling();
  }

  private async initializeRedis() {
    // Initialize Redis client for session storage
    this.redisClient = createClient({
      socket: {
        host: config.redis.host,
        port: config.redis.port,
      },
      password: config.redis.password,
    });

    this.redisClient.on('error', (err: Error) => {
      logger.error('Redis Client Error', err);
    });

    this.redisClient.on('connect', () => {
      logger.info('Redis Client Connected');
    });

    await this.redisClient.connect();
  }

  private initializeMiddleware() {
    // Body parsing middleware
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));

    // Compression middleware
    this.app.use(compression());

    // CORS middleware
    this.app.use(cors({
      origin: config.app.baseUrl,
      credentials: true,
    }));

    // Session middleware
    const redisStore = new RedisStore({
      client: this.redisClient,
      prefix: 'sess:',
    });

    this.app.use(
      session({
        store: redisStore,
        secret: config.security.sessionSecret,
        resave: false,
        saveUninitialized: false,
        cookie: {
          secure: config.env === 'production',
          httpOnly: true,
          maxAge: 1000 * 60 * 60 * 24 * 7, // 1 week
        },
      })
    );

    // Static files
    this.app.use(express.static(path.join(__dirname, '../public')));
    this.app.use('/uploads', express.static(path.join(__dirname, '../uploads')));

    // Request logging
    this.app.use((req: Request, res: Response, next: NextFunction) => {
      logger.info(`${req.method} ${req.path}`);
      next();
    });
  }

  private initializeTemplateEngine() {
    // Configure Nunjucks
    const viewsPath = path.join(__dirname, 'views');
    const env = nunjucks.configure(viewsPath, {
      autoescape: true,
      express: this.app,
      watch: config.nodeEnv === 'development',
      noCache: config.nodeEnv === 'development',
    });

    // Add custom filters (similar to Jinja2)
    env.addFilter('json', (value: NunjucksFilterValue) => JSON.stringify(value));
    env.addFilter('length', (value: NunjucksFilterValue) => (Array.isArray(value) ? value.length : 0));

    // Set view engine
    this.app.set('view engine', 'njk');
    this.app.set('views', viewsPath);
  }

  private async initializeI18n() {
    // Initialize i18next for internationalization
    await i18next
      .use(Backend)
      .use(i18nextMiddleware.LanguageDetector)
      .init({
        fallbackLng: 'en',
        supportedLngs: config.app.languages,
        preload: config.app.languages,
        backend: {
          loadPath: path.join(__dirname, '../locales/{{lng}}/{{ns}}.json'),
        },
        detection: {
          order: ['querystring', 'cookie', 'header'],
          caches: ['cookie'],
        },
      });

    this.app.use(i18nextMiddleware.handle(i18next));
  }

  private initializePassport() {
    // Initialize Passport for authentication
    this.app.use(passport.initialize());
    this.app.use(passport.session());

    // Attach user to locals for templates
    this.app.use(attachUser);
  }

  private initializeRoutes() {
    // Health check
    this.app.get('/health', (req: Request, res: Response) => {
      res.json({ status: 'ok', timestamp: new Date().toISOString() });
    });

    // Mount route modules
    this.app.use('/auth', authRoutes);
    this.app.use('/set', setRoutes);
    this.app.use('/track', trackRoutes);
    this.app.use('/channel', channelRoutes);
    this.app.use('/admin', adminRoutes);
    // this.app.use('/spotify', spotifyRoutes);
    // this.app.use('/playlist', playlistRoutes);

    // Home route (must be after other routes)
    this.app.get('/', (req: Request, res: Response) => {
      res.render('index.njk', {
        title: 'Set2Tracks - DJ Set Tracklist Generator',
        user: req.user,
      });
    });
  }

  private initializeErrorHandling() {
    // Import error handlers
    const { notFoundHandler, errorHandler } = require('./middleware/errorHandler');

    // 404 handler - catches undefined routes
    this.app.use(notFoundHandler);

    // Global error handler - catches all errors
    this.app.use(errorHandler);
  }

  public async close() {
    // Clean up resources
    if (this.redisClient) {
      await this.redisClient.quit();
    }
  }
}

export default App;
