import { PrismaClient } from '@prisma/client';
import { Request, Response, NextFunction } from 'express';
import youtubeService from '../services/youtube.service';
import { setProcessingQueue } from '../jobs/queue';
import logger from '../utils/logger';

const prisma = new PrismaClient();

/**
 * Set Controller
 *
 * Handles operations related to DJ sets (video processing, browsing, searching)
 * This is an example controller showing the pattern for migrating Python controllers
 */

export class SetController {
  /**
   * Get all sets with pagination
   */
  async getSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const skip = (page - 1) * limit;

      const [sets, total] = await Promise.all([
        prisma.set.findMany({
          where: {
            hidden: false,
            published: true,
          },
          include: {
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
          skip,
          take: limit,
        }),
        prisma.set.count({
          where: {
            hidden: false,
            published: true,
          },
        }),
      ]);

      res.json({
        sets,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      logger.error('Error fetching sets:', error);
      next(error);
    }
  }

  /**
   * Get a single set by ID
   */
  async getSetById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const set = await prisma.set.findUnique({
        where: { id: parseInt(id) },
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

      if (!set) {
        res.status(404).json({ error: 'Set not found' });
        return;
      }

      // Record browsing history if user is logged in
      if (req.user) {
        await prisma.setBrowsingHistory.upsert({
          where: {
            setId_userId: {
              setId: set.id,
              userId: (req.user as any).id,
            },
          },
          update: {
            datetime: new Date(),
          },
          create: {
            setId: set.id,
            userId: (req.user as any).id,
            datetime: new Date(),
          },
        });
      }

      res.json({ set });
    } catch (error) {
      logger.error('Error fetching set:', error);
      next(error);
    }
  }

  /**
   * Get set by video ID
   */
  async getSetByVideoId(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { videoId } = req.params;

      const set = await prisma.set.findUnique({
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

      if (!set) {
        res.status(404).json({ error: 'Set not found' });
        return;
      }

      res.json({ set });
    } catch (error) {
      logger.error('Error fetching set by video ID:', error);
      next(error);
    }
  }

  /**
   * Queue a set for processing
   */
  async queueSet(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { videoId, sendEmail, playSound } = req.body;

      if (!videoId) {
        res.status(400).json({ error: 'Video ID is required' });
        return;
      }

      // Check if already exists in queue or as processed set
      const [existingQueue, existingSet] = await Promise.all([
        prisma.setQueue.findUnique({
          where: { videoId },
        }),
        prisma.set.findUnique({
          where: { videoId },
        }),
      ]);

      if (existingSet) {
        res.json({
          message: 'Set already processed',
          set: existingSet,
        });
        return;
      }

      if (existingQueue) {
        res.json({
          message: 'Set already in queue',
          queueItem: existingQueue,
        });
        return;
      }

      // Get video info from YouTube
      logger.info(`Fetching info for video: ${videoId}`);
      const videoInfo = await youtubeService.getVideoInfo(videoId);

      // Create queue item
      const queueItem = await prisma.setQueue.create({
        data: {
          videoId,
          userId: req.user ? (req.user as any).id : null,
          userPremium: req.user ? (req.user as any).type === 'Admin' : false,
          status: 'pending',
          duration: videoInfo.duration,
          nbChapters: videoInfo.chapters?.length || 0,
          videoInfoJson: videoInfo as any,
          sendEmail: sendEmail || false,
          playSound: playSound || false,
        },
      });

      // Add job to Bull queue for processing
      await setProcessingQueue.add({
        videoId,
        queueItemId: queueItem.id,
      }, {
        priority: queueItem.userPremium ? 1 : 10, // Premium users get higher priority
      });

      logger.info(`Set queued successfully: ${videoId}`);

      res.status(201).json({
        message: 'Set queued for processing',
        queueItem,
      });
    } catch (error) {
      logger.error('Error queueing set:', error);
      next(error);
    }
  }

  /**
   * Search sets by title and author
   */
  async searchSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { q } = req.query;

      if (!q || typeof q !== 'string') {
        res.status(400).json({ error: 'Search query is required' });
        return;
      }

      // Basic search - can be enhanced with PostgreSQL full-text search
      const sets = await prisma.set.findMany({
        where: {
          AND: [
            { hidden: false },
            { published: true },
            {
              OR: [
                { title: { contains: q, mode: 'insensitive' } },
                { channel: { author: { contains: q, mode: 'insensitive' } } },
              ],
            },
          ],
        },
        include: {
          channel: true,
        },
        take: 50,
        orderBy: {
          publishDate: 'desc',
        },
      });

      // Record search query
      await prisma.setSearch.upsert({
        where: { query: q },
        update: {
          nbResults: sets.length,
          updatedAt: new Date(),
        },
        create: {
          query: q,
          nbResults: sets.length,
        },
      });

      res.json({ sets, query: q, count: sets.length });
    } catch (error) {
      logger.error('Error searching sets:', error);
      next(error);
    }
  }

  /**
   * Get user's browsing history
   */
  async getUserHistory(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      if (!req.user) {
        res.status(401).json({ error: 'Authentication required' });
        return;
      }

      const userId = (req.user as any).id;
      const limit = parseInt(req.query.limit as string) || 20;

      const history = await prisma.setBrowsingHistory.findMany({
        where: { userId },
        include: {
          set: {
            include: {
              channel: true,
            },
          },
        },
        orderBy: {
          datetime: 'desc',
        },
        take: limit,
      });

      res.json({ history });
    } catch (error) {
      logger.error('Error fetching user history:', error);
      next(error);
    }
  }

  /**
   * Get popular sets
   */
  async getPopularSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 20;

      const sets = await prisma.set.findMany({
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

      res.json({ sets });
    } catch (error) {
      logger.error('Error fetching popular sets:', error);
      next(error);
    }
  }

  /**
   * Get recent sets
   */
  async getRecentSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 20;

      const sets = await prisma.set.findMany({
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

      res.json({ sets });
    } catch (error) {
      logger.error('Error fetching recent sets:', error);
      next(error);
    }
  }
}

export default new SetController();
