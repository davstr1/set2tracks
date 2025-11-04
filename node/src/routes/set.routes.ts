import { Router } from 'express';
import setController from '../controllers/set.controller';
import { optionalAuth, requireAuth } from '../middleware/auth';

const router = Router();

/**
 * Set Routes
 */

// Browse sets
router.get('/', optionalAuth, setController.getSets.bind(setController));

// Search sets
router.get('/search', optionalAuth, setController.searchSets.bind(setController));

// Popular sets
router.get('/popular', optionalAuth, setController.getPopularSets.bind(setController));

// Recent sets
router.get('/recent', optionalAuth, setController.getRecentSets.bind(setController));

// User's browsing history
router.get('/history', requireAuth, setController.getUserHistory.bind(setController));

// Queue a set for processing
router.post('/queue', optionalAuth, setController.queueSet.bind(setController));

// Get set by video ID
router.get('/video/:videoId', optionalAuth, setController.getSetByVideoId.bind(setController));

// Get set by ID
router.get('/:id', optionalAuth, setController.getSetById.bind(setController));

export default router;
