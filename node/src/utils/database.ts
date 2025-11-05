import { PrismaClient } from '@prisma/client';
import logger from './logger';

/**
 * PrismaClient Singleton
 *
 * Ensures only one instance of PrismaClient is created throughout the application
 * to prevent memory leaks and connection pool exhaustion.
 *
 * Best Practices:
 * - Use this singleton instead of creating new PrismaClient() instances
 * - Automatically handles connection lifecycle
 * - Includes query logging in development mode
 * - Proper error handling and graceful shutdown
 */

// Global type augmentation for hot reload in development
declare global {
  // eslint-disable-next-line no-var
  var prisma: PrismaClient | undefined;
}

// Create singleton instance
const prisma =
  global.prisma ||
  new PrismaClient({
    log: [
      { level: 'warn', emit: 'event' },
      { level: 'error', emit: 'event' },
    ],
  });

// Preserve instance across hot reloads in development
if (process.env.NODE_ENV !== 'production') {
  global.prisma = prisma;
}

// Log warnings and errors
prisma.$on('warn', (e) => {
  logger.warn('Prisma Warning:', e);
});

prisma.$on('error', (e) => {
  logger.error('Prisma Error:', e);
});

// Graceful shutdown handler
async function disconnectPrisma() {
  try {
    await prisma.$disconnect();
    logger.info('Prisma disconnected successfully');
  } catch (error) {
    logger.error('Error disconnecting Prisma:', error);
  }
}

// Register shutdown handlers
process.on('SIGINT', disconnectPrisma);
process.on('SIGTERM', disconnectPrisma);
process.on('beforeExit', disconnectPrisma);

export default prisma;
