import { PrismaClient } from '@prisma/client';
import { Request, Response, NextFunction } from 'express';
import logger from '../utils/logger';

const prisma = new PrismaClient();

/**
 * Channel Controller
 * Handles operations related to YouTube channels
 */
export class ChannelController {
  /**
   * Get all channels with pagination
   */
  async getChannels(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 30;
      const skip = (page - 1) * limit;
      const showAll = req.query.showAll === 'true';

      const where = showAll ? {} : { hidden: false, followable: true };

      const [channels, total] = await Promise.all([
        prisma.channel.findMany({
          where,
          orderBy: [
            { nbSets: 'desc' },
            { channelFollowerCount: 'desc' },
          ],
          skip,
          take: limit,
        }),
        prisma.channel.count({ where }),
      ]);

      res.render('channel/list', {
        title: 'DJ Channels',
        channels,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching channels:', error);
      next(error);
    }
  }

  /**
   * Get channels (API/JSON)
   */
  async getChannelsApi(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 30;
      const skip = (page - 1) * limit;
      const showAll = req.query.showAll === 'true';

      const where = showAll ? {} : { hidden: false, followable: true };

      const [channels, total] = await Promise.all([
        prisma.channel.findMany({
          where,
          orderBy: [
            { nbSets: 'desc' },
            { channelFollowerCount: 'desc' },
          ],
          skip,
          take: limit,
        }),
        prisma.channel.count({ where }),
      ]);

      res.json({
        channels,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      logger.error('Error fetching channels:', error);
      next(error);
    }
  }

  /**
   * Get a single channel by ID (HTML page)
   */
  async getChannelById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const channel = await prisma.channel.findUnique({
        where: { id: parseInt(id) },
        include: {
          sets: {
            where: {
              hidden: false,
              published: true,
            },
            orderBy: {
              publishDate: 'desc',
            },
            take: 50,
          },
        },
      });

      if (!channel) {
        res.status(404).render('error', {
          title: 'Channel Not Found',
          message: 'The channel you are looking for could not be found.',
          error: { status: 404 },
        });
        return;
      }

      res.render('channel/detail', {
        title: channel.author || 'Channel',
        channel,
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching channel:', error);
      next(error);
    }
  }

  /**
   * Get a single channel by ID (API/JSON)
   */
  async getChannelByIdApi(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const channel = await prisma.channel.findUnique({
        where: { id: parseInt(id) },
        include: {
          sets: {
            where: {
              hidden: false,
              published: true,
            },
            orderBy: {
              publishDate: 'desc',
            },
            take: 50,
          },
        },
      });

      if (!channel) {
        res.status(404).json({ error: 'Channel not found' });
        return;
      }

      res.json({ channel });
    } catch (error) {
      logger.error('Error fetching channel:', error);
      next(error);
    }
  }

  /**
   * Get popular channels
   */
  async getPopularChannels(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || 20;

      const channels = await prisma.channel.findMany({
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

      res.json({ channels });
    } catch (error) {
      logger.error('Error fetching popular channels:', error);
      next(error);
    }
  }

  /**
   * Search channels
   */
  async searchChannels(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { q } = req.query;

      if (!q || typeof q !== 'string') {
        res.status(400).json({ error: 'Search query is required' });
        return;
      }

      const channels = await prisma.channel.findMany({
        where: {
          AND: [
            { hidden: false },
            {
              OR: [
                { author: { contains: q, mode: 'insensitive' } },
                { channelId: { contains: q, mode: 'insensitive' } },
              ],
            },
          ],
        },
        orderBy: {
          nbSets: 'desc',
        },
        take: 50,
      });

      res.json({ channels, query: q, count: channels.length });
    } catch (error) {
      logger.error('Error searching channels:', error);
      next(error);
    }
  }

  /**
   * Get channel sets (paginated)
   */
  async getChannelSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 20;
      const skip = (page - 1) * limit;

      const channel = await prisma.channel.findUnique({
        where: { id: parseInt(id) },
      });

      if (!channel) {
        res.status(404).json({ error: 'Channel not found' });
        return;
      }

      const [sets, total] = await Promise.all([
        prisma.set.findMany({
          where: {
            channelId: channel.id,
            hidden: false,
            published: true,
          },
          orderBy: {
            publishDate: 'desc',
          },
          skip,
          take: limit,
        }),
        prisma.set.count({
          where: {
            channelId: channel.id,
            hidden: false,
            published: true,
          },
        }),
      ]);

      res.json({
        channel,
        sets,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      logger.error('Error fetching channel sets:', error);
      next(error);
    }
  }
}

export default new ChannelController();
