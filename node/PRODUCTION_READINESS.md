# 🛡️ Production Readiness Checklist

**Current Status:** Code quality is excellent, but production infrastructure needs work.

---

## 🎯 Critical Priorities (Must Have for Production)

### 1. Testing ⚠️ **CRITICAL - 0% Coverage**
**Impact:** HIGH | **Effort:** HIGH (2-3 weeks) | **Status:** ❌ Not Started

**Why Critical:**
- No automated tests = high risk of regression bugs
- Cannot safely refactor or add features
- No confidence in deployments

**What to Implement:**

#### Unit Tests (Target: 70% coverage)
```bash
# Install testing dependencies
npm install --save-dev jest @types/jest ts-jest
npm install --save-dev supertest @types/supertest
npm install --save-dev @faker-js/faker
```

**Priority Test Suites:**
1. **Repositories** (Easiest - Pure logic)
   - `set.repository.test.ts`
   - `track.repository.test.ts`
   - `user.repository.test.ts`
   - Mock Prisma client for isolated tests

2. **Services** (Medium - Business logic)
   - `set.service.test.ts` - Queue logic, validation
   - `auth.service.test.ts` - Registration, password reset
   - `track.service.test.ts` - Search, filtering
   - Mock repositories

3. **Controllers** (Integration tests)
   - `set.controller.test.ts`
   - `auth.controller.test.ts`
   - Use supertest for HTTP testing

4. **Utilities** (Quick wins)
   - `request.test.ts` - parsePagination, etc.
   - `response.test.ts` - sendSuccess, etc.
   - `validation.test.ts` - isValidEmail, etc.
   - `password.test.ts` - hash, compare

5. **Middleware**
   - `validation.middleware.test.ts`
   - `requestId.middleware.test.ts`

**Example Test Structure:**
```typescript
// src/__tests__/services/auth.service.test.ts
import { AuthService } from '../../services/domain/auth.service';
import userRepository from '../../repositories/user.repository';

jest.mock('../../repositories/user.repository');

describe('AuthService', () => {
  describe('register', () => {
    it('should create a new user with hashed password', async () => {
      // Arrange
      const mockUser = { id: 1, email: 'test@example.com' };
      (userRepository.createUser as jest.Mock).mockResolvedValue(mockUser);

      // Act
      const result = await authService.register({
        email: 'test@example.com',
        password: 'SecurePass123!',
        fname: 'Test',
      });

      // Assert
      expect(result).toEqual(mockUser);
      expect(userRepository.createUser).toHaveBeenCalledWith(
        expect.objectContaining({
          email: 'test@example.com',
          password: expect.not.stringContaining('SecurePass123!'),
        })
      );
    });

    it('should throw ConflictError if email exists', async () => {
      // Arrange
      (userRepository.findByEmail as jest.Mock).mockResolvedValue({ id: 1 });

      // Act & Assert
      await expect(
        authService.register({
          email: 'existing@example.com',
          password: 'pass',
          fname: 'Test',
        })
      ).rejects.toThrow(ConflictError);
    });
  });
});
```

**Package.json Scripts:**
```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:ci": "jest --ci --coverage --maxWorkers=2"
  }
}
```

**Jest Configuration** (`jest.config.js`):
```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src'],
  testMatch: ['**/__tests__/**/*.test.ts'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/**/*.interface.ts',
    '!src/index.ts',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
};
```

---

### 2. Security Hardening ⚠️ **CRITICAL**
**Impact:** HIGH | **Effort:** LOW (2-3 hours) | **Status:** ❌ Partially Implemented

**Missing Security Layers:**

#### A. Helmet.js (Security Headers)
```bash
npm install helmet
npm install --save-dev @types/helmet
```

```typescript
// src/app.ts
import helmet from 'helmet';

private initializeMiddleware() {
  // Add before other middleware
  this.app.use(helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        scriptSrc: ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com"],
        imgSrc: ["'self'", "data:", "https:"],
      },
    },
    hsts: {
      maxAge: 31536000,
      includeSubDomains: true,
      preload: true,
    },
  }));

  // ... rest of middleware
}
```

**What Helmet Provides:**
- ✅ XSS Protection
- ✅ Clickjacking Protection (X-Frame-Options)
- ✅ MIME Sniffing Protection
- ✅ HSTS (Force HTTPS)
- ✅ Content Security Policy

#### B. Rate Limiting
```bash
npm install express-rate-limit
npm install --save-dev @types/express-rate-limit
```

```typescript
// src/middleware/rateLimiter.ts
import rateLimit from 'express-rate-limit';

// General API rate limiter
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.',
  standardHeaders: true,
  legacyHeaders: false,
});

// Strict limiter for authentication endpoints
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts
  message: 'Too many login attempts, please try again later.',
  skipSuccessfulRequests: true, // Don't count successful logins
});

// Queue submission limiter (per user)
export const queueLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // 10 queue submissions per hour
  message: 'Queue limit reached. Please try again later.',
  keyGenerator: (req) => {
    // Use user ID instead of IP for authenticated requests
    return (req.user as any)?.id?.toString() || req.ip;
  },
});
```

```typescript
// src/routes/auth.routes.ts
import { authLimiter } from '../middleware/rateLimiter';

router.post('/login', authLimiter, authController.login);
router.post('/register', authLimiter, authController.register);

// src/routes/set.routes.ts
import { queueLimiter } from '../middleware/rateLimiter';

router.post('/queue', ensureAuthenticated, queueLimiter, setController.queueSet);
```

#### C. CORS Hardening
```typescript
// src/app.ts - Update CORS config
this.app.use(cors({
  origin: (origin, callback) => {
    const allowedOrigins = [
      config.app.baseUrl,
      'http://localhost:3000',
      'http://localhost:5173', // Vite dev server
    ];

    // Allow requests with no origin (mobile apps, Postman, etc.)
    if (!origin) return callback(null, true);

    if (allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Request-ID'],
  exposedHeaders: ['X-Request-ID'],
  maxAge: 86400, // 24 hours
}));
```

#### D. Input Sanitization
```bash
npm install express-mongo-sanitize
npm install xss-clean
```

```typescript
// src/app.ts
import mongoSanitize from 'express-mongo-sanitize';
import xss from 'xss-clean';

this.app.use(mongoSanitize()); // Prevent NoSQL injection
this.app.use(xss()); // Prevent XSS attacks in req.body
```

#### E. Session Security Enhancement
```typescript
// src/app.ts - Update session config
this.app.use(
  session({
    store: redisStore,
    secret: config.security.sessionSecret,
    resave: false,
    saveUninitialized: false,
    name: 'sessionId', // Don't use default 'connect.sid'
    cookie: {
      secure: config.env === 'production', // HTTPS only in production
      httpOnly: true, // Prevent XSS access to cookie
      maxAge: 24 * 60 * 60 * 1000, // 24 hours
      sameSite: 'strict', // CSRF protection
      domain: config.env === 'production' ? '.yourdomain.com' : undefined,
    },
  })
);
```

---

### 3. Health Checks & Monitoring ⚠️ **CRITICAL**
**Impact:** HIGH | **Effort:** LOW (1 hour) | **Status:** ❌ Not Implemented

**Why Critical:**
- Load balancers need health endpoints
- Kubernetes/Docker Swarm require health checks
- Early detection of issues

```typescript
// src/controllers/health.controller.ts
import { Request, Response } from 'express';
import prisma from '../utils/database';
import { RedisClient } from '../types/redis';

export class HealthController {
  private redisClient: RedisClient;

  constructor(redisClient: RedisClient) {
    this.redisClient = redisClient;
  }

  /**
   * Basic liveness probe - Is the server running?
   */
  async liveness(req: Request, res: Response): Promise<void> {
    res.status(200).json({
      status: 'ok',
      timestamp: new Date().toISOString(),
    });
  }

  /**
   * Readiness probe - Is the server ready to accept traffic?
   * Checks all critical dependencies
   */
  async readiness(req: Request, res: Response): Promise<void> {
    const checks = {
      database: false,
      redis: false,
    };

    let isReady = true;

    // Check database
    try {
      await prisma.$queryRaw`SELECT 1`;
      checks.database = true;
    } catch (error) {
      isReady = false;
    }

    // Check Redis
    try {
      await this.redisClient.ping();
      checks.redis = true;
    } catch (error) {
      isReady = false;
    }

    const statusCode = isReady ? 200 : 503;

    res.status(statusCode).json({
      status: isReady ? 'ready' : 'not_ready',
      timestamp: new Date().toISOString(),
      checks,
    });
  }

  /**
   * Detailed health check with metrics
   */
  async health(req: Request, res: Response): Promise<void> {
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      version: process.env.npm_package_version || '1.0.0',
      services: {
        database: { status: 'unknown', responseTime: 0 },
        redis: { status: 'unknown', responseTime: 0 },
      },
    };

    // Database health
    try {
      const dbStart = Date.now();
      await prisma.$queryRaw`SELECT 1`;
      health.services.database = {
        status: 'healthy',
        responseTime: Date.now() - dbStart,
      };
    } catch (error) {
      health.status = 'unhealthy';
      health.services.database = {
        status: 'unhealthy',
        responseTime: 0,
      };
    }

    // Redis health
    try {
      const redisStart = Date.now();
      await this.redisClient.ping();
      health.services.redis = {
        status: 'healthy',
        responseTime: Date.now() - redisStart,
      };
    } catch (error) {
      health.status = 'unhealthy';
      health.services.redis = {
        status: 'unhealthy',
        responseTime: 0,
      };
    }

    const statusCode = health.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(health);
  }
}

export default HealthController;
```

```typescript
// src/routes/health.routes.ts
import { Router } from 'express';
import HealthController from '../controllers/health.controller';

const router = Router();

export default function createHealthRoutes(redisClient: any) {
  const healthController = new HealthController(redisClient);

  // Kubernetes liveness probe
  router.get('/healthz', healthController.liveness.bind(healthController));

  // Kubernetes readiness probe
  router.get('/readyz', healthController.readiness.bind(healthController));

  // Detailed health check
  router.get('/health', healthController.health.bind(healthController));

  return router;
}
```

```typescript
// src/app.ts - Add health routes
import createHealthRoutes from './routes/health.routes';

private initializeRoutes() {
  // Health checks (should be first, no auth required)
  this.app.use('/api', createHealthRoutes(this.redisClient));

  // ... other routes
}
```

---

### 4. Database Transactions ⚠️ **HIGH PRIORITY**
**Impact:** HIGH | **Effort:** MEDIUM (4-6 hours) | **Status:** ❌ Not Implemented

**Why Critical:**
- Data consistency in multi-step operations
- Prevent partial updates on failures
- ACID compliance

**Where Transactions Are Needed:**

#### A. Set Queue Processing
```typescript
// src/services/domain/set.service.ts
async queueSet(params: {...}): Promise<QueueSubmissionResult> {
  const { videoId, userId, userType } = params;

  // Use transaction for atomic operations
  return await prisma.$transaction(async (tx) => {
    // 1. Create queue item
    const queueItem = await tx.queue.create({
      data: {
        videoId,
        userId,
        status: 'pending',
        priority: userType === 'Premium' ? 1 : 0,
      },
    });

    // 2. Update user stats
    await tx.user.update({
      where: { id: userId },
      data: {
        queuedSets: { increment: 1 },
      },
    });

    // 3. Record browsing history
    await tx.userBrowsingHistory.create({
      data: {
        userId,
        setId: null, // Will be filled when processed
        videoId,
      },
    });

    return { queueItemId: queueItem.id, position: await this.getQueuePosition(queueItem.id) };
  });
}
```

#### B. User Registration with Invite
```typescript
// src/services/domain/auth.service.ts
async register(params: {...}) {
  return await prisma.$transaction(async (tx) => {
    // 1. Create user
    const user = await tx.user.create({ data: {...} });

    // 2. Delete invite
    if (inviteCode) {
      await tx.invite.delete({ where: { code: inviteCode } });
    }

    // 3. Create initial preferences
    await tx.userPreferences.create({
      data: {
        userId: user.id,
        theme: 'light',
        notifications: true,
      },
    });

    return user;
  });
}
```

#### C. Set Processing Completion
```typescript
// src/jobs/processors/setProcessing.processor.ts
async processSet(job: Job) {
  return await prisma.$transaction(async (tx) => {
    // 1. Update set status
    await tx.set.update({
      where: { id: setId },
      data: { published: true },
    });

    // 2. Update queue status
    await tx.queue.update({
      where: { id: job.data.queueItemId },
      data: { status: 'completed' },
    });

    // 3. Update channel stats
    await tx.channel.update({
      where: { id: channelId },
      data: { nbSets: { increment: 1 } },
    });
  });
}
```

---

### 5. Environment Validation ⚠️ **MEDIUM PRIORITY**
**Impact:** MEDIUM | **Effort:** LOW (1 hour) | **Status:** ❌ Not Implemented

**Why Important:**
- Catch configuration errors early
- Fail fast on startup if critical env vars missing
- Better developer experience

```bash
npm install envalid
```

```typescript
// src/config/env.ts
import { cleanEnv, str, port, url, email } from 'envalid';

export const env = cleanEnv(process.env, {
  NODE_ENV: str({ choices: ['development', 'production', 'test'] }),
  PORT: port({ default: 3000 }),

  // Database
  DATABASE_URL: str(),

  // Redis
  REDIS_HOST: str({ default: 'localhost' }),
  REDIS_PORT: port({ default: 6379 }),
  REDIS_PASSWORD: str({ default: '' }),

  // Security
  SESSION_SECRET: str({ minLength: 32 }),
  JWT_SECRET: str({ minLength: 32 }),

  // External APIs
  YOUTUBE_API_KEY: str(),
  SPOTIFY_CLIENT_ID: str(),
  SPOTIFY_CLIENT_SECRET: str(),

  // Email
  MAIL_SERVER: str(),
  MAIL_PORT: port(),
  MAIL_USER: email(),
  MAIL_PASSWORD: str(),
  MAIL_FROM: email(),

  // App
  BASE_URL: url(),

  // Optional with defaults
  LOG_LEVEL: str({ choices: ['error', 'warn', 'info', 'debug'], default: 'info' }),
  ALLOW_SITE_SIGNUP: str({ choices: ['true', 'false'], default: 'false' }),
});
```

```typescript
// src/config/index.ts
import { env } from './env';

const config = {
  env: env.NODE_ENV,
  port: env.PORT,
  // ... use env.* everywhere
};
```

---

## 🚀 High Priority (Should Have)

### 6. API Documentation (Swagger/OpenAPI)
**Impact:** MEDIUM | **Effort:** MEDIUM (1 day) | **Status:** ❌ Not Implemented

```bash
npm install swagger-jsdoc swagger-ui-express
npm install --save-dev @types/swagger-jsdoc @types/swagger-ui-express
```

```typescript
// src/config/swagger.ts
import swaggerJsdoc from 'swagger-jsdoc';

const options = {
  definition: {
    openapi: '3.0.0',
    info: {
      title: 'Set2Tracks API',
      version: '1.0.0',
      description: 'DJ Set Tracklist Generator API',
    },
    servers: [
      { url: 'http://localhost:3000', description: 'Development' },
      { url: 'https://api.set2tracks.com', description: 'Production' },
    ],
    components: {
      securitySchemes: {
        sessionAuth: {
          type: 'apiKey',
          in: 'cookie',
          name: 'sessionId',
        },
      },
    },
  },
  apis: ['./src/routes/*.ts', './src/controllers/*.ts'],
};

export const swaggerSpec = swaggerJsdoc(options);
```

```typescript
// src/app.ts
import swaggerUi from 'swagger-ui-express';
import { swaggerSpec } from './config/swagger';

private initializeRoutes() {
  // API documentation
  this.app.use('/api-docs', swaggerUi.serve, swaggerUi.setup(swaggerSpec));

  // ... other routes
}
```

**Example Controller Documentation:**
```typescript
/**
 * @swagger
 * /api/sets:
 *   get:
 *     summary: Get published sets
 *     tags: [Sets]
 *     parameters:
 *       - in: query
 *         name: page
 *         schema:
 *           type: integer
 *           default: 1
 *       - in: query
 *         name: limit
 *         schema:
 *           type: integer
 *           default: 20
 *     responses:
 *       200:
 *         description: List of published sets
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 items:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 */
async getSets(req: Request, res: Response) { ... }
```

---

### 7. Caching Layer
**Impact:** MEDIUM | **Effort:** MEDIUM (1-2 days) | **Status:** ❌ Not Implemented

**Why Important:**
- Reduce database load
- Faster response times
- Better scalability

```typescript
// src/utils/cache.ts
import { RedisClient } from '../types/redis';

export class CacheService {
  constructor(private redis: RedisClient) {}

  async get<T>(key: string): Promise<T | null> {
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async set(key: string, value: any, ttlSeconds: number = 3600): Promise<void> {
    await this.redis.setex(key, ttlSeconds, JSON.stringify(value));
  }

  async del(key: string): Promise<void> {
    await this.redis.del(key);
  }

  async delPattern(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }
}
```

```typescript
// src/services/domain/set.service.ts
import { CacheService } from '../../utils/cache';

export class SetService {
  constructor(private cache: CacheService) {}

  async getPublishedSets(page: number, limit: number) {
    const cacheKey = `sets:published:${page}:${limit}`;

    // Try cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      logInfo('Cache hit', { key: cacheKey });
      return cached;
    }

    // Cache miss - fetch from database
    const result = await this.fetchPublishedSets(page, limit);

    // Cache for 5 minutes
    await this.cache.set(cacheKey, result, 300);

    return result;
  }

  async queueSet(params: any) {
    const result = await this.createQueueItem(params);

    // Invalidate relevant caches
    await this.cache.delPattern('sets:published:*');
    await this.cache.delPattern('queue:*');

    return result;
  }
}
```

**Cache Invalidation Strategy:**
- TTL-based: Set expiration times
- Event-based: Invalidate on writes
- Pattern-based: Clear related keys

---

### 8. Database Query Optimization
**Impact:** MEDIUM | **Effort:** MEDIUM (2-3 days) | **Status:** ⚠️ Needs Review

**Check for N+1 Queries:**
```typescript
// BAD - N+1 query problem
const sets = await prisma.set.findMany();
for (const set of sets) {
  const channel = await prisma.channel.findUnique({ where: { id: set.channelId } });
}

// GOOD - Single query with include
const sets = await prisma.set.findMany({
  include: { channel: true },
});
```

**Add Database Indexes:**
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_sets_published ON "Set"(published, hidden) WHERE published = true AND hidden = false;
CREATE INDEX idx_sets_video_id ON "Set"(video_id);
CREATE INDEX idx_tracks_artist ON "Track"(artist_name);
CREATE INDEX idx_queue_status ON "Queue"(status, created_at);
CREATE INDEX idx_user_email ON "User"(email);
```

**Pagination Optimization:**
```typescript
// Use cursor-based pagination for large datasets
async getSetsCursor(cursor?: number, limit: number = 20) {
  return await prisma.set.findMany({
    take: limit,
    skip: cursor ? 1 : 0,
    cursor: cursor ? { id: cursor } : undefined,
    orderBy: { id: 'desc' },
  });
}
```

---

## 🔧 Medium Priority (Nice to Have)

### 9. Containerization (Docker)
**Impact:** MEDIUM | **Effort:** LOW (2-3 hours) | **Status:** ❌ Not Implemented

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build TypeScript
RUN npm run build

# Production image
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install production dependencies only
RUN npm ci --only=production

# Copy built app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/public ./public
COPY --from=builder /app/views ./views

# Generate Prisma client
RUN npx prisma generate

# Create non-root user
RUN addgroup -g 1001 -S nodejs && adduser -S nodejs -u 1001
USER nodejs

EXPOSE 3000

CMD ["node", "dist/index.js"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - '3000:3000'
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/set2tracks
      REDIS_HOST: redis
      NODE_ENV: production
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: set2tracks
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  worker:
    build: .
    command: node dist/jobs/worker.js
    environment:
      DATABASE_URL: postgresql://user:pass@postgres:5432/set2tracks
      REDIS_HOST: redis
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

---

### 10. CI/CD Pipeline
**Impact:** MEDIUM | **Effort:** MEDIUM (1 day) | **Status:** ❌ Not Implemented

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: set2tracks_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npx tsc --noEmit

      - name: Run tests
        run: npm run test:ci
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/set2tracks_test
          REDIS_HOST: localhost

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  build:
    runs-on: ubuntu-latest
    needs: test

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Build
        run: |
          npm ci
          npm run build

      - name: Build Docker image
        run: docker build -t set2tracks:latest .

  deploy:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: echo "Deploy to production server"
```

---

### 11. Monitoring & Alerting
**Impact:** MEDIUM | **Effort:** MEDIUM | **Status:** ❌ Not Implemented

**Application Performance Monitoring (APM):**
```bash
# Choose one:
npm install @sentry/node @sentry/profiling-node  # Sentry
npm install newrelic  # New Relic
npm install dd-trace  # Datadog
```

```typescript
// src/utils/monitoring.ts
import * as Sentry from '@sentry/node';
import { ProfilingIntegration } from '@sentry/profiling-node';

export function initializeMonitoring(app: Application) {
  Sentry.init({
    dsn: process.env.SENTRY_DSN,
    environment: process.env.NODE_ENV,
    integrations: [
      new Sentry.Integrations.Http({ tracing: true }),
      new Sentry.Integrations.Express({ app }),
      new ProfilingIntegration(),
    ],
    tracesSampleRate: 1.0,
    profilesSampleRate: 1.0,
  });

  // Request handler must be first
  app.use(Sentry.Handlers.requestHandler());
  app.use(Sentry.Handlers.tracingHandler());
}

export function initializeErrorHandling(app: Application) {
  // Error handler must be last
  app.use(Sentry.Handlers.errorHandler());
}
```

---

### 12. Database Backups
**Impact:** HIGH | **Effort:** LOW | **Status:** ❌ Not Implemented

```bash
# Automated PostgreSQL backups
# Create backup script: scripts/backup-db.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgres"
FILENAME="set2tracks_${DATE}.sql.gz"

pg_dump -h $DB_HOST -U $DB_USER -d set2tracks | gzip > "${BACKUP_DIR}/${FILENAME}"

# Keep only last 7 days
find $BACKUP_DIR -name "set2tracks_*.sql.gz" -mtime +7 -delete

# Upload to S3
aws s3 cp "${BACKUP_DIR}/${FILENAME}" s3://your-backup-bucket/postgres/
```

```yaml
# Add to docker-compose.yml or cron
  backup:
    image: postgres:15-alpine
    volumes:
      - ./scripts:/scripts
      - backups:/backups
    environment:
      DB_HOST: postgres
      DB_USER: user
      DB_PASSWORD: pass
    command: /scripts/backup-db.sh
```

---

## 📊 Priority Matrix

| Priority | Task | Impact | Effort | Status |
|----------|------|--------|--------|--------|
| 🔴 P0 | Testing (Unit + Integration) | Critical | High | ❌ |
| 🔴 P0 | Security Hardening (Helmet, Rate Limiting) | Critical | Low | ❌ |
| 🔴 P0 | Health Checks | Critical | Low | ❌ |
| 🟠 P1 | Database Transactions | High | Medium | ❌ |
| 🟠 P1 | Environment Validation | High | Low | ❌ |
| 🟡 P2 | API Documentation (Swagger) | Medium | Medium | ❌ |
| 🟡 P2 | Caching Layer | Medium | Medium | ❌ |
| 🟡 P2 | Query Optimization | Medium | Medium | ⚠️ |
| 🟢 P3 | Docker/Containerization | Low | Low | ❌ |
| 🟢 P3 | CI/CD Pipeline | Low | Medium | ❌ |
| 🟢 P3 | Monitoring/APM | Low | Medium | ❌ |
| 🟢 P3 | Database Backups | High | Low | ❌ |

---

## 🎯 Recommended Implementation Order

### Week 1: Critical Security & Infrastructure
1. ✅ **Day 1-2:** Security hardening (Helmet, rate limiting, CORS)
2. ✅ **Day 3:** Health checks + environment validation
3. ✅ **Day 4-5:** Database transactions in critical paths

### Week 2: Testing Foundation
4. ✅ **Day 1-2:** Setup testing infrastructure (Jest, mocks)
5. ✅ **Day 3-4:** Unit tests for utilities and services
6. ✅ **Day 5:** Integration tests for critical endpoints

### Week 3: Performance & Documentation
7. ✅ **Day 1-2:** Caching layer implementation
8. ✅ **Day 3:** Query optimization and indexing
9. ✅ **Day 4-5:** API documentation (Swagger)

### Week 4: DevOps & Monitoring
10. ✅ **Day 1-2:** Containerization (Docker)
11. ✅ **Day 3-4:** CI/CD pipeline
12. ✅ **Day 5:** Monitoring and alerting

---

## ✅ Already Implemented (Great Job!)

- ✅ Graceful shutdown handling
- ✅ Unhandled rejection/exception handling
- ✅ Structured logging
- ✅ Request correlation (Request IDs)
- ✅ Error handling with custom error classes
- ✅ Input validation
- ✅ Type safety (TypeScript)
- ✅ Environment configuration
- ✅ CORS (basic setup)
- ✅ Session security (basic setup)
- ✅ Redis session storage

---

## 🚀 Quick Start - Top 3 Urgent Tasks

If you had to start today, do these first:

```bash
# 1. Security Hardening (30 minutes)
npm install helmet express-rate-limit express-mongo-sanitize xss-clean
# Implement helmet, rate limiting, input sanitization

# 2. Health Checks (30 minutes)
# Create health controller and routes
# Add /healthz, /readyz, /health endpoints

# 3. Testing Setup (1 hour)
npm install --save-dev jest ts-jest @types/jest supertest @types/supertest
# Create jest.config.js and first test file
```

**These 3 tasks (2 hours total) will give you:**
- ✅ Production-grade security
- ✅ Load balancer compatibility
- ✅ Foundation for quality assurance

Would you like me to implement any of these priorities? I recommend starting with the **Critical P0 items** (Security + Health Checks + Testing setup).
