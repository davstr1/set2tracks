import { PrismaClient } from '@prisma/client';
import { Request, Response, NextFunction } from 'express';
import logger from '../utils/logger';

const prisma = new PrismaClient();

/**
 * Admin Controller
 * Handles administrative operations
 */
export class AdminController {
  /**
   * Admin Dashboard
   */
  async getDashboard(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      // Get statistics
      const [
        totalSets,
        totalTracks,
        totalChannels,
        totalUsers,
        recentSets,
        queuedSets,
        recentUsers,
      ] = await Promise.all([
        prisma.set.count(),
        prisma.track.count(),
        prisma.channel.count(),
        prisma.user.count(),
        prisma.set.findMany({
          take: 10,
          orderBy: { updatedAt: 'desc' },
          include: { channel: true },
        }),
        prisma.setQueue.findMany({
          take: 10,
          orderBy: { createdAt: 'desc' },
        }),
        prisma.user.findMany({
          take: 10,
          orderBy: { createdAt: 'desc' },
        }),
      ]);

      res.render('admin/dashboard', {
        title: 'Admin Dashboard',
        stats: {
          totalSets,
          totalTracks,
          totalChannels,
          totalUsers,
        },
        recentSets,
        queuedSets,
        recentUsers,
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching admin dashboard:', error);
      next(error);
    }
  }

  /**
   * Get all users
   */
  async getUsers(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = parseInt(req.query.limit as string) || 50;
      const skip = (page - 1) * limit;

      const [users, total] = await Promise.all([
        prisma.user.findMany({
          orderBy: { createdAt: 'desc' },
          skip,
          take: limit,
        }),
        prisma.user.count(),
      ]);

      res.render('admin/users', {
        title: 'Manage Users',
        users,
        pagination: {
          page,
          limit,
          total,
          totalPages: Math.ceil(total / limit),
        },
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching users:', error);
      next(error);
    }
  }

  /**
   * Get queue status
   */
  async getQueueStatus(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const [pendingQueue, processingQueue, failedQueue] = await Promise.all([
        prisma.setQueue.findMany({
          where: { status: 'pending' },
          orderBy: { createdAt: 'desc' },
          take: 50,
        }),
        prisma.setQueue.findMany({
          where: { status: 'processing' },
          orderBy: { createdAt: 'desc' },
          take: 50,
        }),
        prisma.setQueue.findMany({
          where: { status: 'failed' },
          orderBy: { updatedAt: 'desc' },
          take: 50,
        }),
      ]);

      res.render('admin/queue', {
        title: 'Queue Status',
        pendingQueue,
        processingQueue,
        failedQueue,
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching queue status:', error);
      next(error);
    }
  }

  /**
   * Get application logs
   */
  async getLogs(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      // In a real application, you would read from log files or a logging service
      // For now, just render the page with a message
      res.render('admin/logs', {
        title: 'Application Logs',
        message: 'Log viewing functionality to be implemented',
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching logs:', error);
      next(error);
    }
  }

  /**
   * Get application configuration
   */
  async getConfig(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const appConfig = await prisma.appConfig.findMany({
        orderBy: { key: 'asc' },
      });

      res.render('admin/config', {
        title: 'Application Configuration',
        config: appConfig,
        user: req.user,
      });
    } catch (error) {
      logger.error('Error fetching config:', error);
      next(error);
    }
  }

  /**
   * Update configuration value
   */
  async updateConfig(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { key, value } = req.body;

      if (!key || value === undefined) {
        res.status(400).json({ error: 'Key and value are required' });
        return;
      }

      const config = await prisma.appConfig.upsert({
        where: { key },
        update: { value },
        create: { key, value },
      });

      res.json({ success: true, config });
    } catch (error) {
      logger.error('Error updating config:', error);
      next(error);
    }
  }

  /**
   * Hide/unhide a set
   */
  async toggleSetVisibility(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { hidden } = req.body;

      const set = await prisma.set.update({
        where: { id: parseInt(id) },
        data: { hidden: hidden === true || hidden === 'true' },
      });

      res.json({ success: true, set });
    } catch (error) {
      logger.error('Error toggling set visibility:', error);
      next(error);
    }
  }

  /**
   * Delete a set
   */
  async deleteSet(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;

      await prisma.set.delete({
        where: { id: parseInt(id) },
      });

      res.json({ success: true, message: 'Set deleted successfully' });
    } catch (error) {
      logger.error('Error deleting set:', error);
      next(error);
    }
  }

  /**
   * Update user type (admin/user/guest)
   */
  async updateUserType(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { type } = req.body;

      if (!['Admin', 'User', 'Guest'].includes(type)) {
        res.status(400).json({ error: 'Invalid user type' });
        return;
      }

      const user = await prisma.user.update({
        where: { id: parseInt(id) },
        data: { type },
      });

      res.json({ success: true, user });
    } catch (error) {
      logger.error('Error updating user type:', error);
      next(error);
    }
  }

  /**
   * Get system stats (API)
   */
  async getSystemStats(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const [
        totalSets,
        publishedSets,
        totalTracks,
        totalChannels,
        totalUsers,
        queuePending,
        queueProcessing,
        queueFailed,
      ] = await Promise.all([
        prisma.set.count(),
        prisma.set.count({ where: { published: true, hidden: false } }),
        prisma.track.count(),
        prisma.channel.count(),
        prisma.user.count(),
        prisma.setQueue.count({ where: { status: 'pending' } }),
        prisma.setQueue.count({ where: { status: 'processing' } }),
        prisma.setQueue.count({ where: { status: 'failed' } }),
      ]);

      res.json({
        sets: {
          total: totalSets,
          published: publishedSets,
        },
        tracks: totalTracks,
        channels: totalChannels,
        users: totalUsers,
        queue: {
          pending: queuePending,
          processing: queueProcessing,
          failed: queueFailed,
        },
      });
    } catch (error) {
      logger.error('Error fetching system stats:', error);
      next(error);
    }
  }
}

export default new AdminController();
