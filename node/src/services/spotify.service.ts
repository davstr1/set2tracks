import SpotifyWebApi from 'spotify-web-api-node';
import config from '../config';
import logger from '../utils/logger';

class SpotifyService {
  private spotifyApi: SpotifyWebApi;
  private tokenExpirationTime: number = 0;

  constructor() {
    this.spotifyApi = new SpotifyWebApi({
      clientId: config.apis.spotify.clientId,
      clientSecret: config.apis.spotify.clientSecret,
      redirectUri: config.apis.spotify.redirectUri,
    });
  }

  /**
   * Ensure we have a valid access token (client credentials flow)
   */
  private async ensureAccessToken(): Promise<void> {
    const currentTime = Date.now();

    if (currentTime >= this.tokenExpirationTime) {
      try {
        const data = await this.spotifyApi.clientCredentialsGrant();
        this.spotifyApi.setAccessToken(data.body.access_token);
        // Set expiration 1 minute before actual expiration
        this.tokenExpirationTime = currentTime + (data.body.expires_in - 60) * 1000;
        logger.info('Spotify access token refreshed');
      } catch (error) {
        logger.error('Error refreshing Spotify access token:', error);
        throw error;
      }
    }
  }

  /**
   * Search for a track on Spotify
   */
  async searchTrack(query: string, limit: number = 10): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.searchTracks(query, { limit });
      return data.body.tracks?.items || [];
    } catch (error) {
      logger.error(`Error searching Spotify for track: ${query}`, error);
      throw error;
    }
  }

  /**
   * Get track details by Spotify ID
   */
  async getTrack(trackId: string): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getTrack(trackId);
      return data.body;
    } catch (error) {
      logger.error(`Error getting Spotify track: ${trackId}`, error);
      throw error;
    }
  }

  /**
   * Get artist details by Spotify ID
   */
  async getArtist(artistId: string): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getArtist(artistId);
      return data.body;
    } catch (error) {
      logger.error(`Error getting Spotify artist: ${artistId}`, error);
      throw error;
    }
  }

  /**
   * Search for multiple tracks concurrently
   */
  async searchTracks(queries: string[], limit: number = 10): Promise<any[]> {
    await this.ensureAccessToken();

    const promises = queries.map(query => this.searchTrack(query, limit));
    return Promise.all(promises);
  }

  /**
   * Create a playlist (requires user auth)
   */
  async createPlaylist(
    userId: string,
    name: string,
    description: string,
    isPublic: boolean = true
  ): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.createPlaylist(name, {
        description,
        public: isPublic,
      });
      return data.body;
    } catch (error) {
      logger.error(`Error creating Spotify playlist: ${name}`, error);
      throw error;
    }
  }

  /**
   * Add tracks to a playlist
   */
  async addTracksToPlaylist(playlistId: string, trackUris: string[]): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.addTracksToPlaylist(playlistId, trackUris);
      return data.body;
    } catch (error) {
      logger.error(`Error adding tracks to Spotify playlist: ${playlistId}`, error);
      throw error;
    }
  }

  /**
   * Get user's playlists (requires user auth)
   */
  async getUserPlaylists(userId: string, limit: number = 50): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getUserPlaylists(userId, { limit });
      return data.body.items;
    } catch (error) {
      logger.error(`Error getting Spotify user playlists: ${userId}`, error);
      throw error;
    }
  }

  /**
   * Get track audio features
   */
  async getAudioFeatures(trackId: string): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getAudioFeaturesForTrack(trackId);
      return data.body;
    } catch (error) {
      logger.error(`Error getting Spotify audio features: ${trackId}`, error);
      throw error;
    }
  }

  /**
   * Get multiple tracks at once
   */
  async getTracks(trackIds: string[]): Promise<any[]> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getTracks(trackIds);
      return data.body.tracks;
    } catch (error) {
      logger.error('Error getting multiple Spotify tracks', error);
      throw error;
    }
  }

  /**
   * Get related artists
   */
  async getRelatedArtists(artistId: string): Promise<any[]> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getArtistRelatedArtists(artistId);
      return data.body.artists;
    } catch (error) {
      logger.error(`Error getting related artists for: ${artistId}`, error);
      throw error;
    }
  }

  /**
   * Get user's saved tracks (requires user auth)
   */
  async getSavedTracks(limit: number = 50, offset: number = 0): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getMySavedTracks({ limit, offset });
      return data.body.items;
    } catch (error) {
      logger.error('Error getting saved tracks', error);
      throw error;
    }
  }

  /**
   * Get recommendations based on seed tracks/artists/genres
   */
  async getRecommendations(options: {
    seedTracks?: string[];
    seedArtists?: string[];
    seedGenres?: string[];
    limit?: number;
  }): Promise<any> {
    await this.ensureAccessToken();

    try {
      const data = await this.spotifyApi.getRecommendations(options);
      return data.body.tracks;
    } catch (error) {
      logger.error('Error getting Spotify recommendations', error);
      throw error;
    }
  }

  /**
   * Create an OAuth instance for user authentication
   */
  createUserAuthApi(accessToken: string, refreshToken?: string): SpotifyWebApi {
    const api = new SpotifyWebApi({
      clientId: config.apis.spotify.clientId,
      clientSecret: config.apis.spotify.clientSecret,
      redirectUri: config.apis.spotify.redirectUri,
    });

    api.setAccessToken(accessToken);
    if (refreshToken) {
      api.setRefreshToken(refreshToken);
    }

    return api;
  }
}

export default new SpotifyService();
