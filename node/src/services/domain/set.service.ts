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
import { getCacheService } from '../../utils/cacheInstance';

/**
 * Cache TTL constants (in seconds)
 */
const CACHE_TTL = {
  PUBLISHED_SETS: 300, // 5 minutes
  SET_DETAIL: 600, // 10 minutes
  POPULAR_SETS: 300, // 5 minutes
  RECENT_SETS: 180, // 3 minutes
  SEARCH_RESULTS: 300, // 5 minutes
};

/**
 * Set Service
 * Business logic for DJ sets
 */
export class SetService {
  /**
   * Get published sets with pagination
   */
  async getPublishedSets(page: number, limit: number): Promise<PaginatedResponse<SetListDto>> {
    const cacheKey = `sets:published:${page}:${limit}`;
    const cache = getCacheService();

    // Try to get from cache
    return await cache.getOrSet(
      cacheKey,
      async () => {
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
      },
      CACHE_TTL.PUBLISHED_SETS
    );
  }

  /**
   * Get a single set by ID with full details
   */
  async getSetById(id: number): Promise<SetDetailDto> {
    const cacheKey = `set:detail:${id}`;
    const cache = getCacheService();

    return await cache.getOrSet(
      cacheKey,
      async () => {
        const set = await setRepository.findByIdWithDetails(id);

        if (!set) {
          throw new NotFoundError('Set', id);
        }

        return mapToSetDetailDto(set);
      },
      CACHE_TTL.SET_DETAIL
    );
  }

  /**
   * Get set by video ID
   */
  async getSetByVideoId(videoId: string): Promise<SetDetailDto> {
    const cacheKey = `set:video:${videoId}`;
    const cache = getCacheService();

    return await cache.getOrSet(
      cacheKey,
      async () => {
        const set = await setRepository.findByVideoId(videoId);

        if (!set) {
          throw new NotFoundError('Set');
        }

        return mapToSetDetailDto(set);
      },
      CACHE_TTL.SET_DETAIL
    );
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

    // Invalidate relevant caches (new set will appear in lists after processing)
    const cache = getCacheService();
    await cache.delPattern('sets:published:*');
    await cache.delPattern('sets:popular:*');
    await cache.delPattern('sets:recent:*');

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

    const cacheKey = `sets:search:${query.toLowerCase().trim()}`;
    const cache = getCacheService();

    return await cache.getOrSet(
      cacheKey,
      async () => {
        const sets = await setRepository.searchSets(query);

        // Record search query (don't await, run async)
        userRepository.recordSearchQuery(query, sets.length).catch((err) => {
          logInfo('Failed to record search query', { error: err.message });
        });

        return {
          items: sets.map(mapToSetListDto),
          query,
          count: sets.length,
        };
      },
      CACHE_TTL.SEARCH_RESULTS
    );
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
    const cacheKey = `sets:popular:${limit}`;
    const cache = getCacheService();

    return await cache.getOrSet(
      cacheKey,
      async () => {
        const sets = await setRepository.findPopularSets(limit);
        return { items: sets.map(mapToSetListDto) };
      },
      CACHE_TTL.POPULAR_SETS
    );
  }

  /**
   * Get recent sets
   */
  async getRecentSets(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const cacheKey = `sets:recent:${limit}`;
    const cache = getCacheService();

    return await cache.getOrSet(
      cacheKey,
      async () => {
        const sets = await setRepository.findRecentSets(limit);
        return { items: sets.map(mapToSetListDto) };
      },
      CACHE_TTL.RECENT_SETS
    );
  }

  /**
   * Toggle set visibility (admin)
   */
  async toggleVisibility(id: number, hidden: boolean) {
    const set = await setRepository.toggleVisibility(id, hidden);

    // Invalidate caches
    const cache = getCacheService();
    await cache.delPattern('sets:*');
    await cache.del(`set:detail:${id}`);

    return { success: true, set };
  }

  /**
   * Delete a set (admin)
   */
  async deleteSet(id: number) {
    await setRepository.delete(id);

    // Invalidate caches
    const cache = getCacheService();
    await cache.delPattern('sets:*');
    await cache.del(`set:detail:${id}`);

    return { success: true, message: 'Set deleted successfully' };
  }
}

export default new SetService();
