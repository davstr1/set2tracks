import { channelCheckQueue } from './queue';
import logger from '../utils/logger';
import { getErrorMessage } from '../types/errors';

/**
 * Job Scheduler
 * Sets up recurring background jobs
 */

/**
 * Schedule channel check job
 * Runs every 10 minutes to check followed channels for new videos (almost real-time!)
 */
export async function scheduleChannelCheck() {
  try {
    // Remove any existing recurring jobs
    const existingJobs = await channelCheckQueue.getRepeatableJobs();
    for (const job of existingJobs) {
      await channelCheckQueue.removeRepeatableByKey(job.key);
    }

    // Add repeating job: every 10 minutes (almost real-time)
    await channelCheckQueue.add(
      {
        checkAll: true,
      },
      {
        repeat: {
          every: 10 * 60 * 1000, // 10 minutes in milliseconds
        },
        jobId: 'channel-check-recurring',
      }
    );

    logger.info('✅ Scheduled channel check job (runs every 10 minutes for near real-time updates)');
  } catch (error: unknown) {
    logger.error('Error scheduling channel check job:', getErrorMessage(error));
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
