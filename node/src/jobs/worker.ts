import { setProcessingQueue, emailQueue, cleanupQueue, channelCheckQueue } from './queue';
import processSet from './processors/setProcessing.processor';
import processChannelCheck from './processors/channelCheck.processor';
import { initializeScheduler } from './scheduler';
import logger from '../utils/logger';

/**
 * Job Worker
 * Processes jobs from Bull queues
 */

logger.info('🚀 Starting job worker...');

// Initialize recurring jobs (channel checks every 10 minutes for near real-time updates)
initializeScheduler().catch((error) => {
  logger.error('Failed to initialize scheduler:', error);
});

/**
 * Set Processing Queue Processor
 */
setProcessingQueue.process(async (job) => {
  logger.info(`Processing set processing job ${job.id}`);
  await processSet(job);
});

/**
 * Email Queue Processor
 */
emailQueue.process(async (job) => {
  logger.info(`Processing email job ${job.id}`);
  const { type, data } = job.data;

  // TODO: Implement email processors
  // switch (type) {
  //   case 'password-reset':
  //     await emailService.sendPasswordReset(data.email, data.token);
  //     break;
  //   case 'set-processed':
  //     await emailService.sendSetProcessed(data.email, data.setTitle, data.setId);
  //     break;
  //   case 'welcome':
  //     await emailService.sendWelcome(data.email, data.name);
  //     break;
  //   default:
  //     logger.warn(`Unknown email type: ${type}`);
  // }
});

/**
 * Cleanup Queue Processor
 */
cleanupQueue.process(async (job) => {
  logger.info(`Processing cleanup job ${job.id}`);
  const { type, data } = job.data;

  // TODO: Implement cleanup processors
  // switch (type) {
  //   case 'temp-files':
  //     await cleanupTempFiles();
  //     break;
  //   case 'old-sessions':
  //     await cleanupOldSessions();
  //     break;
  //   default:
  //     logger.warn(`Unknown cleanup type: ${type}`);
  // }
});

/**
 * Channel Check Queue Processor
 */
channelCheckQueue.process(async (job) => {
  logger.info(`Processing channel check job ${job.id}`);
  await processChannelCheck(job);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM signal received: closing worker gracefully');

  await Promise.all([
    setProcessingQueue.close(),
    emailQueue.close(),
    cleanupQueue.close(),
    channelCheckQueue.close(),
  ]);

  logger.info('Worker closed');
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT signal received: closing worker gracefully');

  await Promise.all([
    setProcessingQueue.close(),
    emailQueue.close(),
    cleanupQueue.close(),
    channelCheckQueue.close(),
  ]);

  logger.info('Worker closed');
  process.exit(0);
});

logger.info('✅ Job worker is ready and processing jobs!');
logger.info('Listening on queues: set-processing, email, cleanup, channel-check');
