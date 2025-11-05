import { Channel, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';

/**
 * Channel Repository
 * Handles all database operations for YouTube channels
 */
export class ChannelRepository extends BaseRepository<Channel> {
  constructor() {
    super('channel');
  }

  /**
   * Find channels with pagination
   */
  async findChannelsWithPagination(options: {
    skip: number;
    take: number;
    showAll?: boolean;
  }): Promise<Channel[]> {
    const where: Prisma.ChannelWhereInput = options.showAll
      ? {}
      : { hidden: false, followable: true };

    return this.prisma.channel.findMany({
      where,
      orderBy: [
        { nbSets: 'desc' },
        { channelFollowerCount: 'desc' },
      ],
      skip: options.skip,
      take: options.take,
    });
  }

  /**
   * Count channels
   */
  async countChannels(showAll = false): Promise<number> {
    const where: Prisma.ChannelWhereInput = showAll
      ? {}
      : { hidden: false, followable: true };

    return this.prisma.channel.count({ where });
  }

  /**
   * Find channel by ID with sets
   */
  async findByIdWithSets(id: number, setLimit = 50): Promise<Channel | null> {
    return this.prisma.channel.findUnique({
      where: { id },
      include: {
        sets: {
          where: {
            hidden: false,
            published: true,
          },
          orderBy: {
            publishDate: 'desc',
          },
          take: setLimit,
        },
      },
    });
  }

  /**
   * Find channel by channel ID (YouTube ID)
   */
  async findByChannelId(channelId: string): Promise<Channel | null> {
    return this.prisma.channel.findUnique({
      where: { channelId },
    });
  }

  /**
   * Find popular channels
   */
  async findPopularChannels(limit: number): Promise<Channel[]> {
    return this.prisma.channel.findMany({
      where: {
        hidden: false,
        followable: true,
      },
      orderBy: [
        { nbSets: 'desc' },
        { channelFollowerCount: 'desc' },
      ],
      take: limit,
    });
  }

  /**
   * Search channels
   */
  async searchChannels(query: string, limit = 50): Promise<Channel[]> {
    return this.prisma.channel.findMany({
      where: {
        AND: [
          { hidden: false },
          {
            OR: [
              { author: { contains: query, mode: 'insensitive' } },
              { channelId: { contains: query, mode: 'insensitive' } },
            ],
          },
        ],
      },
      orderBy: {
        nbSets: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find followable channels (for channel check job)
   */
  async findFollowableChannels(): Promise<Channel[]> {
    return this.prisma.channel.findMany({
      where: {
        followable: true,
        hidden: false,
      },
    });
  }

  /**
   * Update channel stats
   */
  async updateStats(id: number, stats: {
    channelFollowerCount?: number;
    nbSets?: number;
  }): Promise<Channel> {
    return this.prisma.channel.update({
      where: { id },
      data: stats,
    });
  }
}

export default new ChannelRepository();
