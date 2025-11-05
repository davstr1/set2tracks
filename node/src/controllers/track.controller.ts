import { PrismaClient } from '@prisma/client';
import prisma from '../utils/database';
import { Request, Response, NextFunction } from 'express';
import spotifyService from '../services/spotify.service';
import logger from '../utils/logger';


/**
 * Track Controller
 * Handles track browsing, searching, and discovery
 */
export class TrackController {
  /**
   * Get all tracks with pagination
   */
  async getTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 50;
      const skip = (page - 1) * limit;

      const [tracks, total] = await Promise.all([
        prisma.track.findMany({
          include: {
            genres: true,
          },
          orderBy: {
            nbSets: 'desc',
          },
          skip,
          take: limit,
        }),
        prisma.track.count(),
      ]);

      res.json({
        tracks,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      logger.error('Error fetching tracks:', error);
      next(error);
    }
  }

  /**
   * Get a single track by ID (HTML page)
   */
  async getTrackById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const track = await prisma.track.findUnique({
        where: { id: parseInt(id) },
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

      if (!track) {
        res.status(404).render('error', {
          title: 'Track Not Found',
          message: 'The track you are looking for could not be found.',
          error: { status: 404 },
        });
        return;
      }

      res.render('track/detail', {
        title: `${track.title} - ${track.artistName}`,
        track,
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching track:', error);
      next(error);
    }
  }

  /**
   * Get a single track by ID (API/JSON)
   */
  async getTrackByIdApi(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const track = await prisma.track.findUnique({
        where: { id: parseInt(id) },
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

      if (!track) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }

      res.json({ track });
    } catch (error) {
      logger.error('Error fetching track:', error);
      next(error);
    }
  }

  /**
   * Search tracks
   */
  async searchTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { q } = req.query;

      if (!q || typeof q !== 'string') {
        res.status(400).json({ error: 'Search query is required' });
        return;
      }

      // Basic search - can be enhanced with PostgreSQL full-text search
      const tracks = await prisma.track.findMany({
        where: {
          OR: [
            { title: { contains: q, mode: 'insensitive' } },
            { artistName: { contains: q, mode: 'insensitive' } },
            { album: { contains: q, mode: 'insensitive' } },
            { label: { contains: q, mode: 'insensitive' } },
          ],
        },
        include: {
          genres: true,
        },
        take: 50,
        orderBy: {
          nbSets: 'desc',
        },
      });

      res.json({ tracks, query: q, count: tracks.length });
    } catch (error) {
      logger.error('Error searching tracks:', error);
      next(error);
    }
  }

  /**
   * Get popular tracks
   */
  async getPopularTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 50;
      const timeframe = req.query.timeframe as string; // 'week', 'month', 'all'

      let dateFilter = {};
      if (timeframe === 'week') {
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
      } else if (timeframe === 'month') {
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

      const tracks = await prisma.track.findMany({
        where: dateFilter,
        include: {
          genres: true,
        },
        orderBy: {
          nbSets: 'desc',
        },
        take: limit,
      });

      res.json({ tracks });
    } catch (error) {
      logger.error('Error fetching popular tracks:', error);
      next(error);
    }
  }

  /**
   * Get tracks by genre
   */
  async getTracksByGenre(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { genre } = req.params;
      const limit = parseInt(req.query.limit as string) || 50;

      // Find genre
      const genreObj = await prisma.genre.findFirst({
        where: {
          name: { equals: genre, mode: 'insensitive' },
        },
      });

      if (!genreObj) {
        res.status(404).json({ error: 'Genre not found' });
        return;
      }

      const tracks = await prisma.track.findMany({
        where: {
          genres: {
            some: {
              id: genreObj.id,
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

      res.json({ genre: genreObj, tracks });
    } catch (error) {
      logger.error('Error fetching tracks by genre:', error);
      next(error);
    }
  }

  /**
   * Get all genres
   */
  async getGenres(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const genres = await prisma.genre.findMany({
        orderBy: {
          trackCount: 'desc',
        },
      });

      res.json({ genres });
    } catch (error) {
      logger.error('Error fetching genres:', error);
      next(error);
    }
  }

  /**
   * Get track by Spotify ID
   */
  async getTrackBySpotifyId(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { spotifyId } = req.params;

      const track = await prisma.track.findUnique({
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

      if (!track) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }

      res.json({ track });
    } catch (error) {
      logger.error('Error fetching track by Spotify ID:', error);
      next(error);
    }
  }

  /**
   * Get related tracks
   */
  async getRelatedTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const limit = parseInt(req.query.limit as string) || 20;

      const track = await prisma.track.findUnique({
        where: { id: parseInt(id) },
      });

      if (!track) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }

      // Get related tracks from database
      const relatedTracks = await prisma.$queryRaw`
        SELECT t.*, rt.insertion_order
        FROM tracks t
        INNER JOIN related_tracks rt ON t.id = rt.related_track_id
        WHERE rt.track_id = ${parseInt(id)}
        ORDER BY rt.insertion_order
        LIMIT ${limit}
      `;

      res.json({ track, relatedTracks });
    } catch (error) {
      logger.error('Error fetching related tracks:', error);
      next(error);
    }
  }

  /**
   * Get new/recent tracks
   */
  async getNewTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 50;

      const tracks = await prisma.track.findMany({
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

      res.json({ tracks });
    } catch (error) {
      logger.error('Error fetching new tracks:', error);
      next(error);
    }
  }

  /**
   * Get tracks by artist
   */
  async getTracksByArtist(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { artist } = req.params;
      const limit = parseInt(req.query.limit as string) || 50;

      const tracks = await prisma.track.findMany({
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

      res.json({ artist, tracks, count: tracks.length });
    } catch (error) {
      logger.error('Error fetching tracks by artist:', error);
      next(error);
    }
  }

  /**
   * Get tracks by label
   */
  async getTracksByLabel(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { label } = req.params;
      const limit = parseInt(req.query.limit as string) || 50;

      const tracks = await prisma.track.findMany({
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

      res.json({ label, tracks, count: tracks.length });
    } catch (error) {
      logger.error('Error fetching tracks by label:', error);
      next(error);
    }
  }
}

export default new TrackController();
