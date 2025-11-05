import setRepository from '../../repositories/set.repository';
import queueRepository from '../../repositories/queue.repository';
import userRepository from '../../repositories/user.repository';
import youtubeService from '../youtube.service';
import { setProcessingQueue } from '../../jobs/queue';
import { NotFoundError, ConflictError } from '../../types/errors';
import { PAGINATION, JOB_PRIORITY } from '../../config/constants';

/**
 * Set Service
 * Business logic for DJ sets
 */
export class SetService {
  /**
   * Get published sets with pagination
   */
  async getPublishedSets(page: number, limit: number) {
    const skip = (page - 1) * limit;

    const [sets, total] = await Promise.all([
      setRepository.findPublishedSets({ skip, take: limit }),
      setRepository.countPublishedSets(),
    ]);

    return {
      sets,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get a single set by ID with full details
   */
  async getSetById(id: number) {
    const set = await setRepository.findByIdWithDetails(id);

    if (!set) {
      throw new NotFoundError('Set', id);
    }

    return set;
  }

  /**
   * Get set by video ID
   */
  async getSetByVideoId(videoId: string) {
    const set = await setRepository.findByVideoId(videoId);

    if (!set) {
      throw new NotFoundError('Set');
    }

    return set;
  }

  /**
   * Queue a set for processing
   */
  async queueSet(params: {
    videoId: string;
    userId: number | null;
    userType: string | null;
    sendEmail?: boolean;
    playSound?: boolean;
  }) {
    const { videoId, userId, userType, sendEmail, playSound } = params;

    // Check if already exists in queue or as processed set
    const [existingQueue, existingSet] = await Promise.all([
      queueRepository.findByVideoId(videoId),
      setRepository.findByVideoId(videoId, false),
    ]);

    if (existingSet) {
      return {
        message: 'Set already processed',
        set: existingSet,
        alreadyExists: true,
      };
    }

    if (existingQueue) {
      return {
        message: 'Set already in queue',
        queueItem: existingQueue,
        alreadyExists: true,
      };
    }

    // Get video info from YouTube
    const videoInfo = await youtubeService.getVideoInfo(videoId);

    // Determine if user is premium
    const userPremium = userType === 'Admin';

    // Create queue item
    const queueItem = await queueRepository.createQueueItem({
      videoId,
      userId,
      userPremium,
      status: 'pending',
      duration: videoInfo.duration,
      nbChapters: videoInfo.chapters?.length || 0,
      videoInfoJson: videoInfo as any,
      sendEmail: sendEmail || false,
      playSound: playSound || false,
    });

    // Add job to Bull queue for processing
    await setProcessingQueue.add(
      {
        videoId,
        queueItemId: queueItem.id,
      },
      {
        priority: queueItem.userPremium ? JOB_PRIORITY.USER_SUBMITTED : JOB_PRIORITY.AUTO_QUEUED,
      }
    );

    return {
      message: 'Set queued for processing',
      queueItem,
      alreadyExists: false,
    };
  }

  /**
   * Search sets
   */
  async searchSets(query: string) {
    if (!query || query.trim().length === 0) {
      throw new Error('Search query is required');
    }

    const sets = await setRepository.searchSets(query);

    // Record search query
    await userRepository.recordSearchQuery(query, sets.length);

    return {
      sets,
      query,
      count: sets.length,
    };
  }

  /**
   * Get user's browsing history
   */
  async getUserHistory(userId: number, limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const history = await userRepository.findBrowsingHistory(userId, limit);
    return { history };
  }

  /**
   * Record set browsing
   */
  async recordBrowsing(userId: number, setId: number) {
    await userRepository.recordSetBrowsingHistory(userId, setId);
  }

  /**
   * Get popular sets
   */
  async getPopularSets(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const sets = await setRepository.findPopularSets(limit);
    return { sets };
  }

  /**
   * Get recent sets
   */
  async getRecentSets(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const sets = await setRepository.findRecentSets(limit);
    return { sets };
  }

  /**
   * Toggle set visibility (admin)
   */
  async toggleVisibility(id: number, hidden: boolean) {
    const set = await setRepository.toggleVisibility(id, hidden);
    return { success: true, set };
  }

  /**
   * Delete a set (admin)
   */
  async deleteSet(id: number) {
    await setRepository.delete(id);
    return { success: true, message: 'Set deleted successfully' };
  }
}

export default new SetService();
