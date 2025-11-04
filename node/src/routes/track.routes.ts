import { Router } from 'express';
import trackController from '../controllers/track.controller';
import { optionalAuth } from '../middleware/auth';

const router = Router();

/**
 * Track Routes
 */

// Browse tracks
router.get('/', optionalAuth, trackController.getTracks.bind(trackController));

// Search tracks
router.get('/search', optionalAuth, trackController.searchTracks.bind(trackController));

// Popular tracks
router.get('/popular', optionalAuth, trackController.getPopularTracks.bind(trackController));

// New/recent tracks
router.get('/new', optionalAuth, trackController.getNewTracks.bind(trackController));

// All genres
router.get('/genres', optionalAuth, trackController.getGenres.bind(trackController));

// Tracks by genre
router.get('/genre/:genre', optionalAuth, trackController.getTracksByGenre.bind(trackController));

// Tracks by artist
router.get('/artist/:artist', optionalAuth, trackController.getTracksByArtist.bind(trackController));

// Tracks by label
router.get('/label/:label', optionalAuth, trackController.getTracksByLabel.bind(trackController));

// Track by Spotify ID
router.get('/spotify/:spotifyId', optionalAuth, trackController.getTrackBySpotifyId.bind(trackController));

// Track by ID (must be last to avoid conflicts)
router.get('/:id', optionalAuth, trackController.getTrackById.bind(trackController));

// Related tracks
router.get('/:id/related', optionalAuth, trackController.getRelatedTracks.bind(trackController));

export default router;
