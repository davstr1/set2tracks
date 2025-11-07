import { Router } from 'express';
import trackController from '../controllers/track.controller';
import { optionalAuth } from '../middleware/auth';

const router = Router();

/**
 * @swagger
 * tags:
 *   name: Tracks
 *   description: Track operations - browse, search, get details
 */

/**
 * @swagger
 * /track:
 *   get:
 *     tags: [Tracks]
 *     summary: Browse all tracks with pagination
 *     description: Get a paginated list of all tracks in the database
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Successfully retrieved tracks
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/', optionalAuth, trackController.getTracks.bind(trackController));

/**
 * @swagger
 * /track/search:
 *   get:
 *     tags: [Tracks]
 *     summary: Search tracks by title or artist
 *     description: Full-text search across track titles and artist names
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
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       400:
 *         $ref: '#/components/responses/BadRequest'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/search', optionalAuth, trackController.searchTracks.bind(trackController));

/**
 * @swagger
 * /track/popular:
 *   get:
 *     tags: [Tracks]
 *     summary: Get popular tracks
 *     description: Get tracks ordered by number of sets they appear in (most popular first)
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Popular tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/popular', optionalAuth, trackController.getPopularTracks.bind(trackController));

/**
 * @swagger
 * /track/new:
 *   get:
 *     tags: [Tracks]
 *     summary: Get recently added tracks
 *     description: Get tracks ordered by when they were added to the database (newest first)
 *     parameters:
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Recent tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/new', optionalAuth, trackController.getNewTracks.bind(trackController));

/**
 * @swagger
 * /track/genres:
 *   get:
 *     tags: [Tracks]
 *     summary: Get all available genres
 *     description: Get a list of all unique genres found in the track database
 *     responses:
 *       200:
 *         description: Genres retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 genres:
 *                   type: array
 *                   items:
 *                     type: string
 *                   example: ["House", "Techno", "Trance", "Progressive House"]
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/genres', optionalAuth, trackController.getGenres.bind(trackController));

/**
 * @swagger
 * /track/genre/{genre}:
 *   get:
 *     tags: [Tracks]
 *     summary: Get tracks by genre
 *     description: Get all tracks in a specific genre with pagination
 *     parameters:
 *       - name: genre
 *         in: path
 *         required: true
 *         description: Genre name
 *         schema:
 *           type: string
 *           example: House
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 genre:
 *                   type: string
 *                   example: House
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/genre/:genre', optionalAuth, trackController.getTracksByGenre.bind(trackController));

/**
 * @swagger
 * /track/artist/{artist}:
 *   get:
 *     tags: [Tracks]
 *     summary: Get tracks by artist
 *     description: Get all tracks by a specific artist with pagination
 *     parameters:
 *       - name: artist
 *         in: path
 *         required: true
 *         description: Artist name
 *         schema:
 *           type: string
 *           example: Avicii
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 artist:
 *                   type: string
 *                   example: Avicii
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/artist/:artist', optionalAuth, trackController.getTracksByArtist.bind(trackController));

/**
 * @swagger
 * /track/label/{label}:
 *   get:
 *     tags: [Tracks]
 *     summary: Get tracks by label
 *     description: Get all tracks from a specific record label with pagination
 *     parameters:
 *       - name: label
 *         in: path
 *         required: true
 *         description: Record label name
 *         schema:
 *           type: string
 *           example: Spinnin' Records
 *       - $ref: '#/components/parameters/pageParam'
 *       - $ref: '#/components/parameters/limitParam'
 *     responses:
 *       200:
 *         description: Tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 label:
 *                   type: string
 *                   example: Spinnin' Records
 *                 tracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *                 pagination:
 *                   $ref: '#/components/schemas/PaginationMeta'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/label/:label', optionalAuth, trackController.getTracksByLabel.bind(trackController));

/**
 * @swagger
 * /track/spotify/{spotifyId}:
 *   get:
 *     tags: [Tracks]
 *     summary: Get track by Spotify ID
 *     description: Retrieve track details using its Spotify track ID
 *     parameters:
 *       - name: spotifyId
 *         in: path
 *         required: true
 *         description: Spotify track ID
 *         schema:
 *           type: string
 *           example: 3SdTKo2uVsxFblQjpScoHy
 *     responses:
 *       200:
 *         description: Track details retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/TrackDetailDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/spotify/:spotifyId', optionalAuth, trackController.getTrackBySpotifyId.bind(trackController));

/**
 * @swagger
 * /track/{id}:
 *   get:
 *     tags: [Tracks]
 *     summary: Get track by database ID
 *     description: Retrieve detailed track information including all sets where it appears
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         description: Track database ID
 *         schema:
 *           type: integer
 *           example: 123
 *     responses:
 *       200:
 *         description: Track details retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               $ref: '#/components/schemas/TrackDetailDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/:id', optionalAuth, trackController.getTrackById.bind(trackController));

/**
 * @swagger
 * /track/{id}/related:
 *   get:
 *     tags: [Tracks]
 *     summary: Get related tracks
 *     description: Get tracks that are similar or frequently appear in sets with this track
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         description: Track database ID
 *         schema:
 *           type: integer
 *           example: 123
 *       - name: limit
 *         in: query
 *         description: Number of related tracks to return
 *         required: false
 *         schema:
 *           type: integer
 *           minimum: 1
 *           maximum: 50
 *           default: 10
 *     responses:
 *       200:
 *         description: Related tracks retrieved successfully
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 track:
 *                   $ref: '#/components/schemas/TrackListDto'
 *                 relatedTracks:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/TrackListDto'
 *       404:
 *         $ref: '#/components/responses/NotFound'
 *       500:
 *         $ref: '#/components/responses/InternalServerError'
 */
router.get('/:id/related', optionalAuth, trackController.getRelatedTracks.bind(trackController));

export default router;
