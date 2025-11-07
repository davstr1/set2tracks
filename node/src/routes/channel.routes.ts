import { Router } from 'express';
import channelController from '../controllers/channel.controller';
import { validateRequest } from '../middleware/validation';
import {
  getChannelByIdValidator,
  browseChannelValidator,
} from '../validators/channel.validator';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Channels
 *   description: YouTube channel operations
 */

// HTML Pages (not documented in OpenAPI)
router.get('/', validateRequest(browseChannelValidator), channelController.getChannels.bind(channelController));
router.get('/:id', validateRequest(getChannelByIdValidator), channelController.getChannelById.bind(channelController));

/**
 * @swagger
 * /channel/api/channels:
 *   get:
 *     tags: [Channels]
 *     summary: Browse all channels with pagination
 *     description: Get a paginated list of all YouTube channels that have sets in the database
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Successfully retrieved channels
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 channels:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/ChannelDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/channels', validateRequest(browseChannelValidator), channelController.getChannelsApi.bind(channelController));

/**
 * @swagger
 * /channel/api/channels/popular:
 *   get:
 *     tags: [Channels]
 *     summary: Get popular channels
 *     description: Get channels ordered by number of sets (most popular first) with pagination
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Popular channels retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 channels:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/ChannelDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/channels/popular', validateRequest(browseChannelValidator), channelController.getPopularChannels.bind(channelController));

/**
 * @swagger
 * /channel/api/channels/search:
 *   get:
 *     tags: [Channels]
 *     summary: Search channels by name
 *     description: Full-text search across channel names with pagination
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
 *                 channels:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/ChannelDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/channels/search', validateRequest(browseChannelValidator), channelController.searchChannels.bind(channelController));

/**
 * @swagger
 * /channel/api/channels/{id}:
 *   get:
 *     tags: [Channels]
 *     summary: Get channel by database ID
 *     description: Retrieve detailed channel information including metadata and thumbnails
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         description: Channel database ID
 *         schema:
 *           type: integer
 *           example: 123
 *     responses:
 *       200:
 *         description: Channel details retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/ChannelDetailDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/channels/:id', validateRequest(getChannelByIdValidator), channelController.getChannelByIdApi.bind(channelController));

/**
 * @swagger
 * /channel/api/channels/{id}/sets:
 *   get:
 *     tags: [Channels]
 *     summary: Get all sets from a channel
 *     description: Get a paginated list of all sets from a specific YouTube channel
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         description: Channel database ID
 *         schema:
 *           type: integer
 *           example: 123
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Channel sets retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 channel:
 *                   $ref: '#/components/schemas/ChannelDto'
 *                 sets:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/SetListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/api/channels/:id/sets', validateRequest(getChannelByIdValidator), channelController.getChannelSets.bind(channelController));

export default router;
