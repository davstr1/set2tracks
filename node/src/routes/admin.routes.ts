import { Router } from 'express';
import adminController from '../controllers/admin.controller';
import { requireAdmin } from '../middleware/auth';
import { validateRequest } from '../middleware/validation';
import {
  getUserByIdValidator,
  updateUserValidator,
  toggleSetVisibilityValidator,
  updateConfigValidator,
  browseUsersValidator,
} from '../validators/admin.validator';
import { getSetByIdValidator } from '../validators/set.validator';

const router = Router();

// All admin routes require admin authentication
router.use(requireAdmin);

// HTML Pages
router.get('/', adminController.getDashboard.bind(adminController));
router.get('/users', validateRequest(browseUsersValidator), adminController.getUsers.bind(adminController));
router.get('/queue', adminController.getQueueStatus.bind(adminController));
router.get('/logs', adminController.getLogs.bind(adminController));
router.get('/config', adminController.getConfig.bind(adminController));

// API Endpoints
router.get('/api/stats', adminController.getSystemStats.bind(adminController));
router.post('/api/config', validateRequest(updateConfigValidator), adminController.updateConfig.bind(adminController));
router.post('/api/set/:id/visibility', validateRequest(toggleSetVisibilityValidator), adminController.toggleSetVisibility.bind(adminController));
router.delete('/api/set/:id', validateRequest(getSetByIdValidator), adminController.deleteSet.bind(adminController));
router.post('/api/user/:id/type', validateRequest(updateUserValidator), adminController.updateUserType.bind(adminController));

export default router;
