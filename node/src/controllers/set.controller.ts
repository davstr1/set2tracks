import { Request, Response, NextFunction } from 'express';
import setService from '../services/domain/set.service';
import logger from '../utils/logger';
import { PAGINATION } from '../config/constants';
import { NotFoundError } from '../types/errors';

/**
 * Set Controller
 * Handles HTTP requests for DJ sets
 * Thin controller - delegates business logic to SetService
 */
export class SetController {
  /**
   * Get all sets with pagination
   */
  async getSets(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await setService.getPublishedSets(page, limit);

      res.json(result);
    } catch (error) {
      logger.error('Error fetching sets:', error);
      next(error);
    }
  }

  /**
   * Get a single set by ID (HTML page)
   */
  async getSetById(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const set = await setService.getSetById(parseInt(id));

      // Record browsing history if user is logged in
      if (req.user) {
        await setService.recordBrowsing((req.user as any).id, set.id);
      }

      res.render('set/detail', {
        title: set.title,
        set,
        user: req.user,
      });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).render('error', {
          title: 'Set Not Found',
          message: 'The set you are looking for could not be found.',
          error: { status: 404 },
        });
        return;
      }
      logger.error('Error fetching set:', error);
      next(error);
    }
  }

  /**
   * Get a single set by ID (API/JSON)
   */
  async getSetByIdApi(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      const set = await setService.getSetById(parseInt(id));

      res.json({ set });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Set not found' });
        return;
      }
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

      const set = await setService.getSetByVideoId(videoId);

      res.json({ set });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Set not found' });
        return;
      }
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

      const result = await setService.queueSet({
        videoId,
        userId: req.user ? (req.user as any).id : null,
        userType: req.user ? (req.user as any).type : null,
        sendEmail,
        playSound,
      });

      logger.info(`Set queued successfully: ${videoId}`);

      const statusCode = result.alreadyExists ? 200 : 201;
      res.status(statusCode).json(result);
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

      const result = await setService.searchSets(q);

      res.json({ sets: result.items, query: result.query, count: result.count });
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
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await setService.getUserHistory(userId, limit);

      res.json(result);
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
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await setService.getPopularSets(limit);

      res.json({ sets: result.items });
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
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await setService.getRecentSets(limit);

      res.json({ sets: result.items });
    } catch (error) {
      logger.error('Error fetching recent sets:', error);
      next(error);
    }
  }
}

export default new SetController();
