import { Request, Response, NextFunction } from 'express';
import trackService from '../services/domain/track.service';
import logger from '../utils/logger';
import { PAGINATION } from '../config/constants';
import { NotFoundError } from '../types/errors';

/**
 * Track Controller
 * Handles HTTP requests for tracks
 * Thin controller - delegates business logic to TrackService
 */
export class TrackController {
  /**
   * Get all tracks with pagination
   */
  async getTracks(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 50;

      const result = await trackService.getTracks(page, limit);

      res.json(result);
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

      const track = await trackService.getTrackById(parseInt(id));

      res.render('track/detail', {
        title: `${track.title} - ${track.artistName}`,
        track,
        user: req.user,
      });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).render('error', {
          title: 'Track Not Found',
          message: 'The track you are looking for could not be found.',
          error: { status: 404 },
        });
        return;
      }
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

      const track = await trackService.getTrackById(parseInt(id));

      res.json({ track });
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }
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

      const result = await trackService.searchTracks(q);

      res.json(result);
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
      const timeframe = req.query.timeframe as 'week' | 'month' | 'all' | undefined;

      const result = await trackService.getPopularTracks(limit, timeframe);

      res.json(result);
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

      const result = await trackService.getTracksByGenre(genre, limit);

      res.json(result);
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Genre not found' });
        return;
      }
      logger.error('Error fetching tracks by genre:', error);
      next(error);
    }
  }

  /**
   * Get all genres
   */
  async getGenres(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const result = await trackService.getGenres();

      res.json(result);
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

      const result = await trackService.getTrackBySpotifyId(spotifyId);

      res.json(result);
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }
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
      const limit = parseInt(req.query.limit as string) || PAGINATION.DEFAULT_PAGE_SIZE;

      const result = await trackService.getRelatedTracks(parseInt(id), limit);

      res.json(result);
    } catch (error) {
      if (error instanceof NotFoundError) {
        res.status(404).json({ error: 'Track not found' });
        return;
      }
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

      const result = await trackService.getNewTracks(limit);

      res.json(result);
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

      const result = await trackService.getTracksByArtist(artist, limit);

      res.json(result);
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

      const result = await trackService.getTracksByLabel(label, limit);

      res.json(result);
    } catch (error) {
      logger.error('Error fetching tracks by label:', error);
      next(error);
    }
  }
}

export default new TrackController();
