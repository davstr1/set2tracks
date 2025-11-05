import App from './app';
import config from './config';
import logger from './utils/logger';

const app = new App();

const server = app.app.listen(config.port, () => {
  logger.info(`🚀 Set2Tracks Node.js server is running!`);
  logger.info(`📍 Environment: ${config.env}`);
  logger.info(`🌐 Server: ${config.app.baseUrl}`);
  logger.info(`💾 Database: ${config.database.primary.host}:${config.database.primary.port}/${config.database.primary.name}`);
  logger.info(`🔴 Redis: ${config.redis.host}:${config.redis.port}`);
  logger.info(`📧 Mail: ${config.mail.server}`);
  logger.info(`\n✨ Ready to process DJ sets!\n`);
});

// Graceful shutdown
const gracefulShutdown = async () => {
  logger.info('Received shutdown signal, closing server gracefully...');

  server.close(async () => {
    logger.info('HTTP server closed');

    // Close app resources (Redis, etc.)
    await app.close();

    logger.info('All resources cleaned up. Exiting...');
    process.exit(0);
  });

  // Force close after 10 seconds
  setTimeout(() => {
    logger.error('Could not close connections in time, forcefully shutting down');
    process.exit(1);
  }, 10000);
};

process.on('SIGTERM', gracefulShutdown);
process.on('SIGINT', gracefulShutdown);

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason: unknown, promise: Promise<unknown>) => {
  logger.error('Unhandled Rejection at:', promise, 'reason:', reason);
});

// Handle uncaught exceptions
process.on('uncaughtException', (error: Error) => {
  logger.error('Uncaught Exception:', error);
  gracefulShutdown();
});

export default app;
