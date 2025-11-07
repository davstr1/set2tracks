import { Router } from 'express';
import setController from '../controllers/set.controller';
import { optionalAuth, requireAuth } from '../middleware/auth';
import { queueLimiter } from '../middleware/rateLimiter';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Sets
 *   description: DJ set operations - browse, search, queue for processing
 */

/**
 * @swagger
 * /set:
 *   get:
 *     tags: [Sets]
 *     summary: Browse all sets with pagination
 *     description: Get a paginated list of all DJ sets in the database. Results are ordered by publish date (newest first).
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Successfully retrieved sets
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 sets:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/', optionalAuth, setController.getSets.bind(setController));

/**
 * @swagger
 * /set/search:
 *   get:
 *     tags: [Sets]
 *     summary: Search sets by title or channel
 *     description: Full-text search across set titles and channel names with pagination
 *     parameters:
 *       - $ref: '#/components/parameters/searchQueryParam'
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Search results
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 sets:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/search', optionalAuth, setController.searchSets.bind(setController));

/**
 * @swagger
 * /set/popular:
 *   get:
 *     tags: [Sets]
 *     summary: Get popular sets
 *     description: Get sets ordered by view count (most popular first) with pagination
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Popular sets retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 sets:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/popular', optionalAuth, setController.getPopularSets.bind(setController));

/**
 * @swagger
 * /set/recent:
 *   get:
 *     tags: [Sets]
 *     summary: Get recently added sets
 *     description: Get sets ordered by when they were added to the database (newest first) with pagination
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Recent sets retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 sets:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/recent', optionalAuth, setController.getRecentSets.bind(setController));

/**
 * @swagger
 * /set/history:
 *   get:
 *     tags: [Sets]
 *     summary: Get user's browsing history
 *     description: Get the authenticated user's set browsing history with pagination. Requires authentication.
 *     security:
 *       - sessionAuth: []
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Browsing history retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 history:
 *                   type: array
 *                   items:
 *                     type: object
 *                     properties:
 *                       set:
 *                         $ref: '#/components/schemas/SetListDto'
 *                       viewedAt:
 *                         type: string
 *                         format: date-time
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       401:
 *         $ref: '#/components/responses/Unauthorized'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/history', requireAuth, setController.getUserHistory.bind(setController));

/**
 * @swagger
 * /set/queue:
 *   post:
 *     tags: [Sets]
 *     summary: Queue a YouTube video for processing
 *     description: |
 *       Submit a YouTube video URL or video ID to be processed and added to the database.
 *       The video will be queued for automatic track identification using Shazam.
 *
 *       **Rate Limited:** 10 submissions per hour per user (admins exempt)
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             type: object
 *             required:
 *               - videoId
 *             properties:
 *               videoId:
 *                 type: string
 *                 description: YouTube video ID or full URL
 *                 example: dQw4w9WgXcQ
 *               url:
 *                 type: string
 *                 description: Alternative - full YouTube URL
 *                 example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
 *     responses:
 *       200:
 *         description: Set queued or already exists
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/QueueSubmissionResult'
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       429:
 *         $ref: '#/components/responses/TooManyRequests'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.post('/queue', optionalAuth, queueLimiter, setController.queueSet.bind(setController));

/**
 * @swagger
 * /set/video/{videoId}:
 *   get:
 *     tags: [Sets]
 *     summary: Get set by YouTube video ID
 *     description: Retrieve detailed information about a set using its YouTube video ID, including full tracklist
 *     parameters:
 *       - name: videoId
 *         in: path
 *         required: true
 *         description: YouTube video ID
 *         schema:
 *           type: string
 *           example: dQw4w9WgXcQ
 *     responses:
 *       200:
 *         description: Set details retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SetDetailDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/video/:videoId', optionalAuth, setController.getSetByVideoId.bind(setController));

/**
 * @swagger
 * /set/{id}:
 *   get:
 *     tags: [Sets]
 *     summary: Get set by database ID
 *     description: Retrieve detailed information about a set using its database ID, including full tracklist
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         description: Set database ID
 *         schema:
 *           type: integer
 *           example: 123
 *     responses:
 *       200:
 *         description: Set details retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/SetDetailDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/:id', optionalAuth, setController.getSetById.bind(setController));

export default router;
