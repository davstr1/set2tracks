import { Set, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';

/**
 * Set Repository
 * Handles all database operations for DJ sets
 */
export class SetRepository extends BaseRepository<Set> {
  constructor() {
    super('set');
  }

  /**
   * Find published sets with pagination
   */
  async findPublishedSets(options: {
    skip: number;
    take: number;
    include?: Prisma.SetInclude;
  }): Promise<Set[]> {
    return this.prisma.set.findMany({
      where: {
        hidden: false,
        published: true,
      },
      include: options.include || {
        channel: true,
        trackSets: {
          include: {
            track: true,
          },
        },
      },
      orderBy: {
        publishDate: 'desc',
      },
      skip: options.skip,
      take: options.take,
    });
  }

  /**
   * Count published sets
   */
  async countPublishedSets(): Promise<number> {
    return this.prisma.set.count({
      where: {
        hidden: false,
        published: true,
      },
    });
  }

  /**
   * Find set by ID with full details
   */
  async findByIdWithDetails(id: number): Promise<Set | null> {
    return this.prisma.set.findUnique({
      where: { id },
      include: {
        channel: true,
        trackSets: {
          include: {
            track: {
              include: {
                genres: true,
              },
            },
          },
          orderBy: {
            pos: 'asc',
          },
        },
      },
    });
  }

  /**
   * Find set by video ID
   */
  async findByVideoId(videoId: string, includeDetails = true): Promise<Set | null> {
    if (includeDetails) {
      return this.prisma.set.findUnique({
        where: { videoId },
        include: {
          channel: true,
          trackSets: {
            include: {
              track: {
                include: {
                  genres: true,
                },
              },
            },
            orderBy: {
              pos: 'asc',
            },
          },
        },
      });
    }
    return this.prisma.set.findUnique({
      where: { videoId },
    });
  }

  /**
   * Search sets by title and author
   */
  async searchSets(query: string, limit = 50): Promise<Set[]> {
    return this.prisma.set.findMany({
      where: {
        AND: [
          { hidden: false },
          { published: true },
          {
            OR: [
              { title: { contains: query, mode: 'insensitive' } },
              { channel: { author: { contains: query, mode: 'insensitive' } } },
            ],
          },
        ],
      },
      include: {
        channel: true,
      },
      take: limit,
      orderBy: {
        publishDate: 'desc',
      },
    });
  }

  /**
   * Find popular sets
   */
  async findPopularSets(limit: number): Promise<Set[]> {
    return this.prisma.set.findMany({
      where: {
        hidden: false,
        published: true,
      },
      include: {
        channel: true,
      },
      orderBy: [
        { likeCount: 'desc' },
        { viewCount: 'desc' },
      ],
      take: limit,
    });
  }

  /**
   * Find recent sets
   */
  async findRecentSets(limit: number): Promise<Set[]> {
    return this.prisma.set.findMany({
      where: {
        hidden: false,
        published: true,
      },
      include: {
        channel: true,
      },
      orderBy: {
        publishDate: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find sets by channel ID
   */
  async findByChannelId(channelId: number, options: {
    skip?: number;
    take?: number;
    publishedOnly?: boolean;
  } = {}): Promise<Set[]> {
    const where: Prisma.SetWhereInput = {
      channelId,
      ...(options.publishedOnly && {
        hidden: false,
        published: true,
      }),
    };

    return this.prisma.set.findMany({
      where,
      orderBy: {
        publishDate: 'desc',
      },
      ...(options.skip !== undefined && { skip: options.skip }),
      ...(options.take !== undefined && { take: options.take }),
    });
  }

  /**
   * Count sets by channel ID
   */
  async countByChannelId(channelId: number, publishedOnly = true): Promise<number> {
    const where: Prisma.SetWhereInput = {
      channelId,
      ...(publishedOnly && {
        hidden: false,
        published: true,
      }),
    };

    return this.prisma.set.count({ where });
  }

  /**
   * Toggle set visibility (hide/unhide)
   */
  async toggleVisibility(id: number, hidden: boolean): Promise<Set> {
    return this.prisma.set.update({
      where: { id },
      data: { hidden },
    });
  }

  /**
   * Find recent sets for admin
   */
  async findRecentForAdmin(limit: number): Promise<Set[]> {
    return this.prisma.set.findMany({
      take: limit,
      orderBy: { updatedAt: 'desc' },
      include: { channel: true },
    });
  }
}

export default new SetRepository();
