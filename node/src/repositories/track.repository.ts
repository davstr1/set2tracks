import { Track, Prisma } from '@prisma/client';
import { BaseRepository } from './base.repository';

/**
 * Track Repository
 * Handles all database operations for tracks
 */
export class TrackRepository extends BaseRepository<Track> {
  constructor() {
    super('track');
  }

  /**
   * Find tracks with pagination
   */
  async findTracksWithPagination(options: {
    skip: number;
    take: number;
  }): Promise<Track[]> {
    return this.prisma.track.findMany({
      include: {
        genres: true,
      },
      orderBy: {
        nbSets: 'desc',
      },
      skip: options.skip,
      take: options.take,
    });
  }

  /**
   * Find track by ID with details
   */
  async findByIdWithDetails(id: number): Promise<Track | null> {
    return this.prisma.track.findUnique({
      where: { id },
      include: {
        genres: true,
        trackSets: {
          include: {
            set: {
              include: {
                channel: true,
              },
            },
          },
          orderBy: {
            set: {
              publishDate: 'desc',
            },
          },
        },
      },
    });
  }

  /**
   * Search tracks
   */
  async searchTracks(query: string, limit = 50): Promise<Track[]> {
    return this.prisma.track.findMany({
      where: {
        OR: [
          { title: { contains: query, mode: 'insensitive' } },
          { artistName: { contains: query, mode: 'insensitive' } },
          { album: { contains: query, mode: 'insensitive' } },
          { label: { contains: query, mode: 'insensitive' } },
        ],
      },
      include: {
        genres: true,
      },
      take: limit,
      orderBy: {
        nbSets: 'desc',
      },
    });
  }

  /**
   * Find popular tracks
   */
  async findPopularTracks(options: {
    limit: number;
    timeframe?: 'week' | 'month' | 'all';
  }): Promise<Track[]> {
    let dateFilter: Prisma.TrackWhereInput = {};

    if (options.timeframe === 'week') {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      dateFilter = {
        trackSets: {
          some: {
            set: {
              publishDate: {
                gte: weekAgo,
              },
            },
          },
        },
      };
    } else if (options.timeframe === 'month') {
      const monthAgo = new Date();
      monthAgo.setMonth(monthAgo.getMonth() - 1);
      dateFilter = {
        trackSets: {
          some: {
            set: {
              publishDate: {
                gte: monthAgo,
              },
            },
          },
        },
      };
    }

    return this.prisma.track.findMany({
      where: dateFilter,
      include: {
        genres: true,
      },
      orderBy: {
        nbSets: 'desc',
      },
      take: options.limit,
    });
  }

  /**
   * Find tracks by genre
   */
  async findByGenre(genreId: number, limit: number): Promise<Track[]> {
    return this.prisma.track.findMany({
      where: {
        genres: {
          some: {
            id: genreId,
          },
        },
      },
      include: {
        genres: true,
      },
      orderBy: {
        nbSets: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find track by Spotify ID
   */
  async findBySpotifyId(spotifyId: string): Promise<Track | null> {
    return this.prisma.track.findUnique({
      where: { keyTrackSpotify: spotifyId },
      include: {
        genres: true,
        trackSets: {
          include: {
            set: {
              include: {
                channel: true,
              },
            },
          },
        },
      },
    });
  }

  /**
   * Get related tracks using raw query
   */
  async findRelatedTracks(trackId: number, limit: number): Promise<any[]> {
    return this.prisma.$queryRaw`
      SELECT t.*, rt.insertion_order
      FROM tracks t
      INNER JOIN related_tracks rt ON t.id = rt.related_track_id
      WHERE rt.track_id = ${trackId}
      ORDER BY rt.insertion_order
      LIMIT ${limit}
    `;
  }

  /**
   * Find new/recent tracks
   */
  async findNewTracks(limit: number): Promise<Track[]> {
    return this.prisma.track.findMany({
      where: {
        releaseDate: {
          not: null,
        },
      },
      include: {
        genres: true,
      },
      orderBy: {
        releaseDate: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find tracks by artist
   */
  async findByArtist(artist: string, limit: number): Promise<Track[]> {
    return this.prisma.track.findMany({
      where: {
        artistName: {
          contains: artist,
          mode: 'insensitive',
        },
      },
      include: {
        genres: true,
      },
      orderBy: {
        nbSets: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find tracks by label
   */
  async findByLabel(label: string, limit: number): Promise<Track[]> {
    return this.prisma.track.findMany({
      where: {
        label: {
          contains: label,
          mode: 'insensitive',
        },
      },
      include: {
        genres: true,
      },
      orderBy: {
        nbSets: 'desc',
      },
      take: limit,
    });
  }

  /**
   * Find all genres
   */
  async findAllGenres(): Promise<any[]> {
    return this.prisma.genre.findMany({
      orderBy: {
        trackCount: 'desc',
      },
    });
  }

  /**
   * Find genre by name
   */
  async findGenreByName(name: string): Promise<any | null> {
    return this.prisma.genre.findFirst({
      where: {
        name: { equals: name, mode: 'insensitive' },
      },
    });
  }
}

export default new TrackRepository();
