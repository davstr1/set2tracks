import axios from 'axios';
import fs from 'fs/promises';
import config from '../config';
import logger from '../utils/logger';
import { ShazamTrack as ShazamTrackType, ShazamResponse, ShazamMetadataItem } from '../types/shazam';
import { CONCURRENCY } from '../config/constants';

/**
 * Shazam Service for track identification
 *
 * NOTE: This is a simplified implementation. The Python version uses the 'shazamio' library
 * which provides audio recognition. For Node.js, you have several options:
 *
 * 1. Use a Node.js Shazam library if available (e.g., node-shazam-api)
 * 2. Call Shazam's HTTP API directly (requires API key)
 * 3. Use AudD.io or AcrCloud as alternatives
 * 4. Execute the Python shazamio library as a subprocess
 *
 * This implementation shows the structure and interface that should be maintained.
 */

interface ShazamTrack {
  keyTrackShazam: number;
  title: string;
  artistName: string;
  album?: string;
  label?: string;
  coverArt?: string;
  previewUri?: string;
  releaseYear?: number;
  releaseDate?: string;
  appleMusicUrl?: string;
}

class ShazamService {
  private proxyUrl?: string;
  private maxConcurrentRequests: number = CONCURRENCY.MAX_SHAZAM_REQUESTS;

  constructor() {
    this.proxyUrl = config.apis.shazam.proxyUrl;
  }

  /**
   * Recognize track from audio file
   *
   * NOTE: This is a placeholder. You'll need to implement actual audio recognition.
   * Options include:
   * - Using AcrCloud API (https://www.acrcloud.com/)
   * - Using AudD.io API (https://audd.io/)
   * - Calling Python shazamio via child_process
   */
  async recognizeTrack(audioFilePath: string): Promise<ShazamTrack | null> {
    logger.warn('ShazamService.recognizeTrack is not fully implemented');
    logger.warn('Audio file path: ' + audioFilePath);

    try {
      // TODO: Implement actual audio recognition
      // For now, this is a placeholder that would need:
      // 1. Read audio file
      // 2. Send to recognition service
      // 3. Parse response

      // Example using AcrCloud or similar service:
      /*
      const audioBuffer = await fs.readFile(audioFilePath);
      const response = await axios.post('https://api.acrcloud.com/v1/identify', {
        audio: audioBuffer.toString('base64'),
        // ... other params
      });

      return this.parseShazamResponse(response.data);
      */

      return null;
    } catch (error) {
      logger.error('Error recognizing track:', error);
      return null;
    }
  }

  /**
   * Recognize multiple tracks from audio segments concurrently
   */
  async recognizeTracks(audioFilePaths: string[]): Promise<(ShazamTrack | null)[]> {
    logger.info(`Recognizing ${audioFilePaths.length} audio segments`);

    // Process in batches to avoid overwhelming the API
    const results: (ShazamTrack | null)[] = [];

    for (let i = 0; i < audioFilePaths.length; i += this.maxConcurrentRequests) {
      const batch = audioFilePaths.slice(i, i + this.maxConcurrentRequests);
      const batchResults = await Promise.all(
        batch.map(filePath => this.recognizeTrack(filePath))
      );
      results.push(...batchResults);
    }

    return results;
  }

  /**
   * Get track details by Shazam ID
   */
  async getTrackDetails(shazamTrackId: number): Promise<ShazamTrackType | null> {
    try {
      // Shazam API endpoint (unofficial)
      const url = `https://www.shazam.com/services/amapi/v1/catalog/US/songs/${shazamTrackId}`;

      const response = await axios.get(url, {
        ...(this.proxyUrl && { proxy: this.parseProxyUrl(this.proxyUrl) }),
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
      });

      return response.data as ShazamTrackType;
    } catch (error) {
      logger.error(`Error getting Shazam track details for ${shazamTrackId}:`, error);
      throw error;
    }
  }

  /**
   * Get label information for a track
   */
  async getTrackLabel(shazamTrackId: number): Promise<string | null> {
    try {
      const details = await this.getTrackDetails(shazamTrackId);

      // Extract label from metadata sections
      const sections = details?.sections || [];
      for (const section of sections) {
        if (section.metadata) {
          const labelMetadata = section.metadata.find(
            (m: ShazamMetadataItem) => m.title?.toLowerCase() === 'label'
          );
          if (labelMetadata?.text) {
            return labelMetadata.text;
          }
        }
      }

      return null;
    } catch (error) {
      logger.error(`Error getting label for track ${shazamTrackId}:`, error);
      return null;
    }
  }

  /**
   * Get labels for multiple tracks concurrently
   */
  async getTracksLabels(tracks: ShazamTrack[]): Promise<ShazamTrack[]> {
    logger.info(`Getting labels for ${tracks.length} tracks`);

    const results = await Promise.all(
      tracks.map(async (track) => {
        if (track.label) {
          return track;
        }

        const label = await this.getTrackLabel(track.keyTrackShazam);
        return { ...track, label: label || undefined };
      })
    );

    return results;
  }

  /**
   * Get related tracks
   */
  async getRelatedTracks(shazamTrackId: number, limit: number = 20): Promise<ShazamTrack[]> {
    try {
      logger.info(`Getting related tracks for ${shazamTrackId}`);

      // This would need actual implementation based on Shazam API
      // Placeholder for now
      return [];
    } catch (error) {
      logger.error(`Error getting related tracks for ${shazamTrackId}:`, error);
      return [];
    }
  }

  /**
   * Parse Shazam API response into our track format
   */
  private parseShazamResponse(response: ShazamResponse): ShazamTrack | null {
    if (!response.track) {
      return null;
    }

    const { track } = response;

    // Extract preview URI (prefer Apple Music .m4a)
    let previewUri: string | undefined;
    if (track.hub?.actions) {
      const previewAction = track.hub.actions.find(
        (action) => action.type === 'uri' && action.uri && action.uri.includes('.m4a')
      );
      previewUri = previewAction?.uri;
    }

    return {
      keyTrackShazam: track.key || 0,
      title: track.title || 'Unknown',
      artistName: track.subtitle || 'Unknown Artist',
      coverArt: track.images?.coverart || track.share?.image,
      previewUri,
      appleMusicUrl: track.share?.href,
    };
  }

  /**
   * Helper to parse proxy URL string
   */
  private parseProxyUrl(proxyUrl: string): { host: string; port: number } | undefined {
    try {
      const url = new URL(proxyUrl);
      return {
        host: url.hostname,
        port: parseInt(url.port) || 80,
      };
    } catch {
      return undefined;
    }
  }
}

export default new ShazamService();
