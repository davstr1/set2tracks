import channelRepository from '../../repositories/channel.repository';
import setRepository from '../../repositories/set.repository';
import { NotFoundError } from '../../types/errors';
import { PAGINATION } from '../../config/constants';
import { logInfo, logBusinessEvent, logPerformance } from '../../utils/structuredLogger';

/**
 * Channel Service
 * Business logic for YouTube channels
 */
export class ChannelService {
  /**
   * Get channels with pagination
   */
  async getChannels(page: number, limit: number, showAll = false) {
    const skip = (page - 1) * limit;

    const [channels, total] = await Promise.all([
      channelRepository.findChannelsWithPagination({ skip, take: limit, showAll }),
      channelRepository.countChannels(showAll),
    ]);

    return {
      channels,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get channel by ID with sets
   */
  async getChannelById(id: number, setLimit = 50) {
    const channel = await channelRepository.findByIdWithSets(id, setLimit);

    if (!channel) {
      throw new NotFoundError('Channel', id);
    }

    return channel;
  }

  /**
   * Get popular channels
   */
  async getPopularChannels(limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const channels = await channelRepository.findPopularChannels(limit);
    return { channels };
  }

  /**
   * Search channels
   */
  async searchChannels(query: string) {
    if (!query || query.trim().length === 0) {
      throw new Error('Search query is required');
    }

    const startTime = Date.now();
    logInfo('Channel search initiated', { query });

    const channels = await channelRepository.searchChannels(query);

    logBusinessEvent('channel_search', {
      query,
      resultCount: channels.length,
    });

    const duration = Date.now() - startTime;
    logPerformance('searchChannels', duration, { query, resultCount: channels.length });

    return {
      channels,
      query,
      count: channels.length,
    };
  }

  /**
   * Get channel sets with pagination
   */
  async getChannelSets(id: number, page: number, limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const channel = await channelRepository.findById(id);

    if (!channel) {
      throw new NotFoundError('Channel', id);
    }

    const skip = (page - 1) * limit;

    const [sets, total] = await Promise.all([
      setRepository.findByChannelId(channel.id, {
        skip,
        take: limit,
        publishedOnly: true,
      }),
      setRepository.countByChannelId(channel.id, true),
    ]);

    logBusinessEvent('channel_browsing', {
      channelId: id,
      channelName: channel.author,
      setCount: total,
      page,
    });

    return {
      channel,
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
   * Get followable channels (for background jobs)
   */
  async getFollowableChannels() {
    return channelRepository.findFollowableChannels();
  }

  /**
   * Update channel stats
   */
  async updateChannelStats(id: number, stats: {
    channelFollowerCount?: number;
    nbSets?: number;
  }) {
    logInfo('Channel stats updated', { channelId: id, stats });
    return channelRepository.updateStats(id, stats);
  }
}

export default new ChannelService();
