import fs from 'fs/promises';
import { Shazam } from 'node-shazam';
import config from '../config';
import logger from '../utils/logger';
import { ShazamTrack, ShazamResponse, ShazamMetadataItem, ShazamSection } from '../types/shazam';
import { getErrorMessage } from '../types/errors';
import { CONCURRENCY } from '../config/constants';

/**
 * Music Recognition Service using Shazam
 *
 * Clean implementation with proper error handling, retry logic,
 * and concurrency control - just like the original Python version!
 *
 * Uses: node-shazam-api (Node.js equivalent of shazamio)
 */

// Types
export interface RecognizedTrack {
  keyTrackShazam: number;
  title: string;
  artistName: string;
  album?: string;
  label?: string;
  releaseYear?: number;
  releaseDate?: string;
  durationMs?: number;
  isrc?: string;
  upc?: string;
  spotifyId?: string;
  appleMusicId?: string;
  appleMusicUrl?: string;
  coverArtUrl?: string;
  previewUrl?: string;
  genres?: string[];
  confidence?: number;  // 0-100
}

export interface RecognitionResult {
  success: boolean;
  track?: RecognizedTrack;
  error?: string;
  retries?: number;
}

export interface RecognitionOptions {
  maxRetries?: number;
  retryDelay?: number;
  timeout?: number;
}

/**
 * Music Recognition Service Class
 */
class MusicRecognitionService {
  private readonly maxRetries: number;
  private readonly retryDelay: number;
  private readonly maxConcurrent: number;
  private readonly proxyUrl?: string;

  constructor() {
    this.maxRetries = config.apis.recognition.maxRetries;
    this.retryDelay = config.apis.recognition.retryDelay;
    this.maxConcurrent = config.apis.recognition.maxConcurrent;
    this.proxyUrl = config.apis.shazam.proxyUrl;

    logger.info('✅ Shazam music recognition initialized');
    if (this.proxyUrl) {
      logger.info(`   Using proxy: ${this.proxyUrl}`);
    }
  }

  /**
   * Recognize track from audio file using Shazam
   */
  async recognizeTrack(
    audioFilePath: string,
    options?: RecognitionOptions
  ): Promise<RecognitionResult> {
    // Check if file exists
    try {
      await fs.access(audioFilePath);
    } catch (error) {
      logger.error(`Audio file not found: ${audioFilePath}`);
      return {
        success: false,
        error: `Audio file not found: ${audioFilePath}`,
      };
    }

    const maxRetries = options?.maxRetries ?? this.maxRetries;
    const retryDelay = options?.retryDelay ?? this.retryDelay;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        if (attempt > 0) {
          const delay = retryDelay * Math.pow(2, attempt - 1); // Exponential backoff
          logger.debug(`Retrying Shazam recognition (attempt ${attempt + 1}/${maxRetries + 1}) in ${delay}ms...`);
          await this.sleep(delay);
        }

        // Read audio file
        const audioBuffer = await fs.readFile(audioFilePath);

        // Initialize Shazam
        const shazam = new Shazam();

        // Recognize the track
        const result = await shazam.recognise(audioBuffer, 'en-US');

        if (result && result.track) {
          const shazamTrack = result.track;

          // Extract track information
          const track: RecognizedTrack = {
            keyTrackShazam: parseInt(shazamTrack.key || '0') || 0,
            title: shazamTrack.title || 'Unknown Title',
            artistName: shazamTrack.subtitle || 'Unknown Artist',
            album: shazamTrack.sections?.[0]?.metadata?.find((m: ShazamMetadataItem) => m.title === 'Album')?.text,
            label: shazamTrack.sections?.[0]?.metadata?.find((m: ShazamMetadataItem) => m.title === 'Label')?.text,
            releaseYear: this.extractReleaseYear(shazamTrack.sections),
            appleMusicUrl: shazamTrack.url,
            coverArtUrl: shazamTrack.images?.coverart || shazamTrack.share?.image,
            spotifyId: shazamTrack.hub?.providers?.find((p: { type: string }) => p.type === 'SPOTIFY')?.actions?.[0]?.uri?.split(':').pop(),
            genres: shazamTrack.genres?.primary ? [shazamTrack.genres.primary] : undefined,
            confidence: 90, // Shazam doesn't provide confidence score
          };

          logger.info(`✅ Shazam: Recognized "${track.title}" by ${track.artistName}`);

          return {
            success: true,
            track,
            retries: attempt,
          };
        } else {
          // No result found
          logger.info('ℹ️  Shazam: No match found for this audio');
          return {
            success: false,
            error: 'No match found',
            retries: attempt,
          };
        }
      } catch (error: unknown) {
        lastError = error;
        logger.error(`Shazam recognition attempt ${attempt + 1} failed:`, getErrorMessage(error));

        // Don't retry on certain errors
        const errorMessage = getErrorMessage(error);
        if (errorMessage.includes('rate limit')) {
          logger.warn('Rate limit hit, waiting longer before retry...');
          await this.sleep(5000); // Wait 5 seconds on rate limit
        }
      }
    }

    return {
      success: false,
      error: lastError?.message || 'Recognition failed after all retries',
      retries: maxRetries,
    };
  }

  /**
   * Recognize multiple tracks with concurrency control
   * This is the main method used for processing DJ sets
   */
  async recognizeTracks(
    audioFilePaths: string[],
    options?: RecognitionOptions
  ): Promise<RecognitionResult[]> {
    logger.info(`🎵 Recognizing ${audioFilePaths.length} audio segments with Shazam...`);

    const results: RecognitionResult[] = [];
    const batches: string[][] = [];

    // Split into batches based on maxConcurrent
    for (let i = 0; i < audioFilePaths.length; i += this.maxConcurrent) {
      batches.push(audioFilePaths.slice(i, i + this.maxConcurrent));
    }

    // Process batches sequentially, files within batch concurrently
    for (const [batchIndex, batch] of batches.entries()) {
      logger.info(`Processing batch ${batchIndex + 1}/${batches.length} (${batch.length} segments)...`);

      const batchPromises = batch.map((filePath, index) =>
        this.recognizeTrack(filePath, options)
          .then(result => {
            const globalIndex = batchIndex * this.maxConcurrent + index + 1;
            if (result.success) {
              logger.info(`  [${globalIndex}/${audioFilePaths.length}] ✅ ${result.track?.title} - ${result.track?.artistName}`);
            } else {
              logger.info(`  [${globalIndex}/${audioFilePaths.length}] ❌ ${result.error}`);
            }
            return result;
          })
      );

      const batchResults = await Promise.all(batchPromises);
      results.push(...batchResults);

      // Small delay between batches to avoid rate limiting
      if (batchIndex < batches.length - 1) {
        await this.sleep(1000);
      }
    }

    const successful = results.filter(r => r.success).length;
    logger.info(`✅ Shazam recognition complete: ${successful}/${results.length} tracks identified`);

    return results;
  }

  /**
   * Get track details by Shazam ID (for enrichment)
   */
  async getTrackDetails(shazamTrackId: number | string): Promise<ShazamTrack | null> {
    try {
      const shazam = new Shazam();
      const details = await shazam.getTrackDetails(shazamTrackId.toString());
      return details as ShazamTrack;
    } catch (error: unknown) {
      logger.error(`Error getting Shazam track details for ${shazamTrackId}:`, getErrorMessage(error));
      return null;
    }
  }

  /**
   * Get label for a track (separate API call in Shazam)
   */
  async getTrackLabel(shazamTrackId: number | string): Promise<string | null> {
    try {
      const details = await this.getTrackDetails(shazamTrackId);
      if (!details) return null;

      // Look for label in metadata sections
      const sections = details.sections || [];
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
    } catch (error: unknown) {
      logger.error(`Error getting label for track ${shazamTrackId}:`, getErrorMessage(error));
      return null;
    }
  }

  /**
   * Add labels to tracks concurrently (like the Python version)
   */
  async addLabelsToTracks(
    tracks: RecognizedTrack[],
    maxConcurrent: number = CONCURRENCY.MAX_LABEL_FETCHES
  ): Promise<RecognizedTrack[]> {
    logger.info(`Getting labels for ${tracks.length} tracks...`);

    // Filter tracks that don't have labels
    const tracksNeedingLabels = tracks.filter(t => !t.label);
    if (tracksNeedingLabels.length === 0) {
      logger.info('All tracks already have labels');
      return tracks;
    }

    // Process in batches
    const results: RecognizedTrack[] = [];
    const batches: RecognizedTrack[][] = [];

    for (let i = 0; i < tracksNeedingLabels.length; i += maxConcurrent) {
      batches.push(tracksNeedingLabels.slice(i, i + maxConcurrent));
    }

    for (const [index, batch] of batches.entries()) {
      logger.info(`Getting labels batch ${index + 1}/${batches.length}...`);

      const batchResults = await Promise.all(
        batch.map(async (track) => {
          const label = await this.getTrackLabel(track.keyTrackShazam);
          return { ...track, label: label || track.label };
        })
      );

      results.push(...batchResults);

      // Small delay between batches
      if (index < batches.length - 1) {
        await this.sleep(500);
      }
    }

    // Merge back with tracks that already had labels
    const tracksWithLabels = tracks.filter(t => t.label);
    const allTracks = [...tracksWithLabels, ...results];

    logger.info(`✅ Labels retrieved for ${results.length} tracks`);

    return allTracks;
  }

  /**
   * Get related tracks for a track ID
   */
  async getRelatedTracks(
    shazamTrackId: number | string,
    limit: number = 20
  ): Promise<RecognizedTrack[]> {
    try {
      logger.info(`Getting related tracks for ${shazamTrackId}...`);

      // Note: node-shazam-api might not have this feature
      // You may need to call the Shazam HTTP API directly
      // For now, return empty array
      logger.warn('Related tracks feature not yet implemented for Node.js Shazam');

      return [];
    } catch (error: unknown) {
      logger.error(`Error getting related tracks for ${shazamTrackId}:`, getErrorMessage(error));
      return [];
    }
  }

  /**
   * Test Shazam configuration
   */
  async testConfiguration(): Promise<void> {
    logger.info('🧪 Testing Shazam configuration...');
    logger.info('   Shazam API is publicly available (no API key needed)');
    logger.info('   Ready to recognize tracks!');

    if (this.proxyUrl) {
      logger.info(`   Proxy configured: ${this.proxyUrl}`);
    }
  }

  /**
   * Helper: Extract release year from Shazam sections
   */
  private extractReleaseYear(sections?: ShazamSection[]): number | undefined {
    if (!sections) return undefined;

    for (const section of sections) {
      if (section.metadata) {
        const releasedMetadata = section.metadata.find(
          (m: ShazamMetadataItem) => m.title === 'Released'
        );
        if (releasedMetadata?.text) {
          const year = parseInt(releasedMetadata.text);
          if (!isNaN(year)) {
            return year;
          }
        }
      }
    }

    return undefined;
  }

  /**
   * Helper: Sleep function
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export default new MusicRecognitionService();
