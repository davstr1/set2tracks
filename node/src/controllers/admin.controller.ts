import { Request, Response, NextFunction } from 'express';
import adminService from '../services/domain/admin.service';
import setService from '../services/domain/set.service';
import authService from '../services/domain/auth.service';
import logger from '../utils/logger';
import { ValidationError } from '../types/errors';
import { parsePagination } from '../utils/request';
import { sendBadRequest } from '../utils/response';

/**
 * Admin Controller
 * Handles HTTP requests for administrative operations
 * Thin controller - delegates business logic to AdminService
 */
export class AdminController {
  /**
   * Admin Dashboard
   */
  async getDashboard(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const dashboardData = await adminService.getDashboardStats();

      res.render('admin/dashboard', {
        title: 'Admin Dashboard',
        ...dashboardData,
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
      const { page, limit } = parsePagination(req, { defaultLimit: 50 });

      const result = await adminService.getUsers(page, limit);

      res.render('admin/users', {
        title: 'Manage Users',
        ...result,
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
      const queueData = await adminService.getQueueStatus();

      res.render('admin/queue', {
        title: 'Queue Status',
        ...queueData,
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
      const config = await adminService.getConfig();

      res.render('admin/config', {
        title: 'Application Configuration',
        config,
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
        sendBadRequest(res, 'Key and value are required');
        return;
      }

      const result = await adminService.updateConfig(key, value);

      res.json(result);
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

      const result = await setService.toggleVisibility(parseInt(id), hidden === true || hidden === 'true');

      res.json(result);
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

      const result = await setService.deleteSet(parseInt(id));

      res.json(result);
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

      const result = await authService.updateUserType(parseInt(id), type);

      res.json(result);
    } catch (error) {
      if (error instanceof ValidationError) {
        sendBadRequest(res, error.message);
        return;
      }
      logger.error('Error updating user type:', error);
      next(error);
    }
  }

  /**
   * Get system stats (API)
   */
  async getSystemStats(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const stats = await adminService.getSystemStats();

      res.json(stats);
    } catch (error) {
      logger.error('Error fetching system stats:', error);
      next(error);
    }
  }
}

export default new AdminController();
