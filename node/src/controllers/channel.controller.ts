import { Request, Response, NextFunction } from 'express';
import channelService from '../services/domain/channel.service';
import logger from '../utils/logger';
import { PAGINATION } from '../config/constants';
import { NotFoundError } from '../types/errors';

/**
 * Channel Controller
 * Handles HTTP requests for YouTube channels
 * Thin controller - delegates business logic to ChannelService
 */
export class ChannelController {
  /**
   * Get all channels with pagination (HTML)
   */
  async getChannels(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 30;
      const showAll = req.query.showAll === 'true';

      const result = await channelService.getChannels(page, limit, showAll);

      res.render('channel/list', {
        title: 'DJ Channels',
        ...result,
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
      const showAll = req.query.showAll === 'true';

      const result = await channelService.getChannels(page, limit, showAll);

      res.json(result);
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

      const channel = await channelService.getChannelById(parseInt(id));

      res.render('channel/detail', {
        title: channel.author || 'Channel',
        channel,
        user: req.user,
      });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).render('error', {
          title: 'Channel Not Found',
          message: 'The channel you are looking for could not be found.',
          error: { status: 404 },
        });
        return;
      }
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

      const channel = await channelService.getChannelById(parseInt(id));

      res.json({ channel });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Channel not found' });
        return;
      }
      logger.error('Error fetching channel:', error);
      next(error);
    }
  }

  /**
   * Get popular channels
   */
  async getPopularChannels(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await channelService.getPopularChannels(limit);

      res.json(result);
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

      const result = await channelService.searchChannels(q);

      res.json(result);
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
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await channelService.getChannelSets(parseInt(id), page, limit);

      res.json(result);
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Channel not found' });
        return;
      }
      logger.error('Error fetching channel sets:', error);
      next(error);
    }
  }
}

export default new ChannelController();
