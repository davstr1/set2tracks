import trackRepository from '../../repositories/track.repository';
import { NotFoundError } from '../../types/errors';
import { PAGINATION } from '../../config/constants';

/**
 * Track Service
 * Business logic for tracks
 */
export class TrackService {
  /**
   * Get tracks with pagination
   */
  async getTracks(page: number, limit: number) {
    const skip = (page - 1) * limit;

    const [tracks, total] = await Promise.all([
      trackRepository.findTracksWithPagination({ skip, take: limit }),
      trackRepository.count(),
    ]);

    return {
      tracks,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * Get track by ID with details
   */
  async getTrackById(id: number) {
    const track = await trackRepository.findByIdWithDetails(id);

    if (!track) {
      throw new NotFoundError('Track', id);
    }

    return track;
  }

  /**
   * Search tracks
   */
  async searchTracks(query: string) {
    if (!query || query.trim().length === 0) {
      throw new Error('Search query is required');
    }

    const tracks = await trackRepository.searchTracks(query);

    return {
      tracks,
      query,
      count: tracks.length,
    };
  }

  /**
   * Get popular tracks
   */
  async getPopularTracks(limit: number, timeframe?: 'week' | 'month' | 'all') {
    const tracks = await trackRepository.findPopularTracks({
      limit,
      timeframe,
    });

    return { tracks };
  }

  /**
   * Get tracks by genre
   */
  async getTracksByGenre(genreName: string, limit: number) {
    // Find genre
    const genre = await trackRepository.findGenreByName(genreName);

    if (!genre) {
      throw new NotFoundError('Genre');
    }

    const tracks = await trackRepository.findByGenre(genre.id, limit);

    return { genre, tracks };
  }

  /**
   * Get all genres
   */
  async getGenres() {
    const genres = await trackRepository.findAllGenres();
    return { genres };
  }

  /**
   * Get track by Spotify ID
   */
  async getTrackBySpotifyId(spotifyId: string) {
    const track = await trackRepository.findBySpotifyId(spotifyId);

    if (!track) {
      throw new NotFoundError('Track');
    }

    return { track };
  }

  /**
   * Get related tracks
   */
  async getRelatedTracks(id: number, limit: number = PAGINATION.DEFAULT_PAGE_SIZE) {
    const track = await trackRepository.findById(id);

    if (!track) {
      throw new NotFoundError('Track', id);
    }

    const relatedTracks = await trackRepository.findRelatedTracks(id, limit);

    return { track, relatedTracks };
  }

  /**
   * Get new/recent tracks
   */
  async getNewTracks(limit: number) {
    const tracks = await trackRepository.findNewTracks(limit);
    return { tracks };
  }

  /**
   * Get tracks by artist
   */
  async getTracksByArtist(artist: string, limit: number) {
    const tracks = await trackRepository.findByArtist(artist, limit);

    return {
      artist,
      tracks,
      count: tracks.length,
    };
  }

  /**
   * Get tracks by label
   */
  async getTracksByLabel(label: string, limit: number) {
    const tracks = await trackRepository.findByLabel(label, limit);

    return {
      label,
      tracks,
      count: tracks.length,
    };
  }
}

export default new TrackService();
