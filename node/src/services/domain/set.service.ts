import setRepository from '../../repositories/set.repository';
import queueRepository from '../../repositories/queue.repository';
import userRepository from '../../repositories/user.repository';
import youtubeService from '../youtube.service';
import { setProcessingQueue } from '../../jobs/queue';
import { NotFoundError, ConflictError } from '../../types/errors';
import { PAGINATION, JOB_PRIORITY } from '../../config/constants';
import { mapToSetListDto, mapToSetDetailDto, mapToSetQueueDto } from '../../mappers';
import { PaginatedResponse, SetListDto, SetDetailDto, QueueSubmissionResult } from '../../types/dto';
import { logInfo, logBusinessEvent, logPerformance } from '../../utils/structuredLogger';

/**
 * Set Service
 * Business logic for DJ sets
 */
export class SetService {
  /**
   * Get published sets with pagination
   */
  async getPublishedSets(page: number, limit: number): Promise<PaginatedResponse<SetListDto>> {
    const skip = (page - 1) * limit;

    const [sets, total] = await Promise.all([
      setRepository.findPublishedSets({ skip, take: limit }),
      setRepository.countPublishedSets(),
    ]);

    return {
      items: sets.map(mapToSetListDto),
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
  async getSetById(id: number): Promise<SetDetailDto> {
    const set = await setRepository.findByIdWithDetails(id);

    if (!set) {
      throw new NotFoundError('Set', id);
    }

    return mapToSetDetailDto(set);
  }

  /**
   * Get set by video ID
   */
  async getSetByVideoId(videoId: string): Promise<SetDetailDto> {
    const set = await setRepository.findByVideoId(videoId);

    if (!set) {
      throw new NotFoundError('Set');
    }

    return mapToSetDetailDto(set);
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
  }): Promise<QueueSubmissionResult> {
    const startTime = Date.now();
    const { videoId, userId, userType, sendEmail, playSound } = params;

    logInfo('Set queue request received', { videoId, userId, userType });

    // Check if already exists in queue or as processed set
    const [existingQueue, existingSet] = await Promise.all([
      queueRepository.findByVideoId(videoId),
      setRepository.findByVideoId(videoId, false),
    ]);

    if (existingSet) {
      logInfo('Set already processed', { videoId, setId: existingSet.id });
      return {
        message: 'Set already processed',
        set: mapToSetListDto(existingSet),
        alreadyExists: true,
      };
    }

    if (existingQueue) {
      logInfo('Set already in queue', { videoId, queueId: existingQueue.id });
      return {
        message: 'Set already in queue',
        queueItem: mapToSetQueueDto(existingQueue),
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

    // Log business event
    logBusinessEvent('set_queued', {
      videoId,
      queueItemId: queueItem.id,
      userId,
      userPremium,
      priority: userPremium ? 'high' : 'normal',
    });

    // Log performance
    const duration = Date.now() - startTime;
    logPerformance('queueSet', duration, { videoId, userId });

    return {
      message: 'Set queued for processing',
      queueItem: mapToSetQueueDto(queueItem),
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
      items: sets.map(mapToSetListDto),
      query,
      count: sets.length,
    };
  }

  /**
   * Get user's browsing history
   */
  async getUserHistory(userId: number, limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const history = await userRepository.findBrowsingHistory(userId, limit);
    return {
      history: history.map((h) => ({
        setId: h.setId,
        datetime: h.datetime,
        set: mapToSetListDto(h.set),
      })),
    };
  }

  /**
   * Record set browsing
   */
  async recordBrowsing(userId: number, setId: number): Promise<void> {
    await userRepository.recordSetBrowsingHistory(userId, setId);
  }

  /**
   * Get popular sets
   */
  async getPopularSets(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const sets = await setRepository.findPopularSets(limit);
    return { items: sets.map(mapToSetListDto) };
  }

  /**
   * Get recent sets
   */
  async getRecentSets(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const sets = await setRepository.findRecentSets(limit);
    return { items: sets.map(mapToSetListDto) };
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
