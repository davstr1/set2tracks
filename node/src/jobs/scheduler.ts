import { channelCheckQueue } from './queue';
import logger from '../utils/logger';

/**
 * Job Scheduler
 * Sets up recurring background jobs
 */

/**
 * Schedule channel check job
 * Runs every 6 hours to check followed channels for new videos
 */
export async function scheduleChannelCheck() {
  try {
    // Remove any existing recurring jobs
    const existingJobs = await channelCheckQueue.getRepeatableJobs();
    for (const job of existingJobs) {
      await channelCheckQueue.removeRepeatableByKey(job.key);
    }

    // Add repeating job: every 6 hours
    await channelCheckQueue.add(
      {
        checkAll: true,
      },
      {
        repeat: {
          every: 6 * 60 * 60 * 1000, // 6 hours in milliseconds
        },
        jobId: 'channel-check-recurring',
      }
    );

    logger.info('✅ Scheduled channel check job (runs every 6 hours)');
  } catch (error: any) {
    logger.error('Error scheduling channel check job:', error);
  }
}

/**
 * Schedule cleanup job
 * Runs daily to clean up old temp files and expired sessions
 */
export async function scheduleCleanup() {
  // TODO: Implement cleanup scheduling if needed
  logger.info('ℹ️  Cleanup scheduling not yet implemented');
}

/**
 * Initialize all scheduled jobs
 */
export async function initializeScheduler() {
  logger.info('📅 Initializing job scheduler...');

  await scheduleChannelCheck();
  // await scheduleCleanup();

  logger.info('✅ Job scheduler initialized');
}

export default {
  initializeScheduler,
  scheduleChannelCheck,
  scheduleCleanup,
};
