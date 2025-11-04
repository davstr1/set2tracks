import Bull from 'bull';
import config from '../config';
import logger from '../utils/logger';

/**
 * Bull Queue Configuration
 * Job queues for background processing
 */

// Queue options
const queueOptions: Bull.QueueOptions = {
  redis: {
    host: config.redis.host,
    port: config.redis.port,
    password: config.redis.password,
  },
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 2000,
    },
    removeOnComplete: 100, // Keep last 100 completed jobs
    removeOnFail: 500, // Keep last 500 failed jobs
  },
};

/**
 * Set Processing Queue
 * Handles DJ set processing (download → identify → enrich)
 */
export const setProcessingQueue = new Bull('set-processing', queueOptions);

/**
 * Channel Check Queue
 * Checks YouTube channels for new videos
 */
export const channelCheckQueue = new Bull('channel-check', queueOptions);

/**
 * Email Queue
 * Handles email sending
 */
export const emailQueue = new Bull('email', queueOptions);

/**
 * Cleanup Queue
 * Handles file cleanup and maintenance tasks
 */
export const cleanupQueue = new Bull('cleanup', queueOptions);

// Queue event listeners
function setupQueueListeners(queue: Bull.Queue, name: string) {
  queue.on('error', (error) => {
    logger.error(`[${name}] Queue error:`, error);
  });

  queue.on('waiting', (jobId) => {
    logger.info(`[${name}] Job ${jobId} is waiting`);
  });

  queue.on('active', (job) => {
    logger.info(`[${name}] Job ${job.id} started processing`);
  });

  queue.on('completed', (job, result) => {
    logger.info(`[${name}] Job ${job.id} completed`);
  });

  queue.on('failed', (job, err) => {
    logger.error(`[${name}] Job ${job?.id} failed:`, err);
  });

  queue.on('stalled', (job) => {
    logger.warn(`[${name}] Job ${job.id} stalled`);
  });
}

// Set up listeners for all queues
setupQueueListeners(setProcessingQueue, 'SetProcessing');
setupQueueListeners(channelCheckQueue, 'ChannelCheck');
setupQueueListeners(emailQueue, 'Email');
setupQueueListeners(cleanupQueue, 'Cleanup');

logger.info('Bull queues initialized');

export default {
  setProcessingQueue,
  channelCheckQueue,
  emailQueue,
  cleanupQueue,
};
