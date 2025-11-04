import youtubedl from 'youtube-dl-exec';
import ffmpeg from 'fluent-ffmpeg';
import fs from 'fs/promises';
import path from 'path';
import config from '../config';
import logger from '../utils/logger';

interface VideoInfo {
  id: string;
  title: string;
  description: string;
  duration: number;
  publishDate: string;
  channelId: string;
  channelName: string;
  thumbnail: string;
  viewCount: number;
  likeCount: number;
  playableInEmbed: boolean;
  chapters?: Chapter[];
}

interface Chapter {
  startTime: number;
  endTime: number;
  title: string;
}

class YouTubeService {
  private downloadDir: string;
  private tempDir: string;

  constructor() {
    this.downloadDir = config.upload.directory;
    this.tempDir = config.upload.tempDirectory;
    this.ensureDirectories();
  }

  private async ensureDirectories() {
    try {
      await fs.mkdir(this.downloadDir, { recursive: true });
      await fs.mkdir(this.tempDir, { recursive: true });
    } catch (error) {
      logger.error('Error creating directories:', error);
    }
  }

  /**
   * Get video information without downloading
   */
  async getVideoInfo(videoId: string): Promise<VideoInfo> {
    const url = `https://www.youtube.com/watch?v=${videoId}`;

    try {
      const info = await youtubedl(url, {
        dumpSingleJson: true,
        noWarnings: true,
        noCallHome: true,
        noCheckCertificate: true,
        preferFreeFormats: true,
        youtubeSkipDashManifest: true,
        ...(config.proxy.http && { proxy: config.proxy.http }),
      });

      // Extract chapters if available
      const chapters: Chapter[] = [];
      if (info.chapters && Array.isArray(info.chapters)) {
        info.chapters.forEach((chapter: any, index: number) => {
          chapters.push({
            startTime: Math.floor(chapter.start_time || 0),
            endTime: Math.floor(chapter.end_time || info.duration),
            title: chapter.title || `Chapter ${index + 1}`,
          });
        });
      }

      return {
        id: info.id,
        title: info.title,
        description: info.description || '',
        duration: Math.floor(info.duration),
        publishDate: info.upload_date,
        channelId: info.channel_id,
        channelName: info.channel || info.uploader,
        thumbnail: info.thumbnail,
        viewCount: parseInt(info.view_count || '0'),
        likeCount: parseInt(info.like_count || '0'),
        playableInEmbed: info.playable_in_embed !== false,
        chapters: chapters.length > 0 ? chapters : undefined,
      };
    } catch (error) {
      logger.error(`Error fetching video info for ${videoId}:`, error);
      throw new Error(`Failed to fetch video info: ${error}`);
    }
  }

  /**
   * Download video audio
   */
  async downloadAudio(videoId: string): Promise<string> {
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    const outputPath = path.join(this.tempDir, `${videoId}.%(ext)s`);

    try {
      logger.info(`Downloading audio for video: ${videoId}`);

      await youtubedl(url, {
        extractAudio: true,
        audioFormat: 'mp3',
        audioQuality: 0, // Best quality
        output: outputPath,
        noWarnings: true,
        noCallHome: true,
        noCheckCertificate: true,
        preferFreeFormats: true,
        ...(config.proxy.http && { proxy: config.proxy.http }),
      });

      const finalPath = path.join(this.tempDir, `${videoId}.mp3`);
      logger.info(`Audio downloaded successfully: ${finalPath}`);
      return finalPath;
    } catch (error) {
      logger.error(`Error downloading audio for ${videoId}:`, error);
      throw new Error(`Failed to download audio: ${error}`);
    }
  }

  /**
   * Extract audio segment from a file
   */
  async extractSegment(
    inputPath: string,
    outputPath: string,
    startTime: number,
    duration: number
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      ffmpeg(inputPath)
        .setStartTime(startTime)
        .setDuration(duration)
        .output(outputPath)
        .on('end', () => {
          logger.info(`Segment extracted: ${outputPath}`);
          resolve();
        })
        .on('error', (err) => {
          logger.error('Error extracting segment:', err);
          reject(err);
        })
        .run();
    });
  }

  /**
   * Split audio into segments for processing
   */
  async splitAudioIntoSegments(
    audioPath: string,
    segmentLength: number = config.app.audioSegmentsLength
  ): Promise<string[]> {
    const segments: string[] = [];
    const audioInfo = await this.getAudioDuration(audioPath);
    const duration = audioInfo.duration;
    const videoId = path.basename(audioPath, '.mp3');

    try {
      logger.info(`Splitting audio into ${segmentLength}s segments`);

      for (let startTime = 0; startTime < duration; startTime += segmentLength) {
        const segmentPath = path.join(
          this.tempDir,
          `${videoId}_segment_${startTime}.mp3`
        );

        await this.extractSegment(
          audioPath,
          segmentPath,
          startTime,
          Math.min(segmentLength, duration - startTime)
        );

        segments.push(segmentPath);
      }

      logger.info(`Created ${segments.length} audio segments`);
      return segments;
    } catch (error) {
      logger.error('Error splitting audio:', error);
      throw error;
    }
  }

  /**
   * Get audio duration
   */
  private async getAudioDuration(audioPath: string): Promise<{ duration: number }> {
    return new Promise((resolve, reject) => {
      ffmpeg.ffprobe(audioPath, (err, metadata) => {
        if (err) {
          reject(err);
        } else {
          resolve({
            duration: metadata.format.duration || 0,
          });
        }
      });
    });
  }

  /**
   * Delete temporary file
   */
  async deleteTempFile(filePath: string): Promise<void> {
    try {
      await fs.unlink(filePath);
      logger.info(`Deleted temp file: ${filePath}`);
    } catch (error) {
      logger.error(`Error deleting temp file ${filePath}:`, error);
    }
  }

  /**
   * Delete all temporary files for a video
   */
  async cleanupVideoFiles(videoId: string): Promise<void> {
    try {
      const files = await fs.readdir(this.tempDir);
      const videoFiles = files.filter(file => file.startsWith(videoId));

      for (const file of videoFiles) {
        await this.deleteTempFile(path.join(this.tempDir, file));
      }

      logger.info(`Cleaned up ${videoFiles.length} files for video ${videoId}`);
    } catch (error) {
      logger.error(`Error cleaning up files for ${videoId}:`, error);
    }
  }

  /**
   * Get channel information
   */
  async getChannelInfo(channelId: string): Promise<any> {
    const url = `https://www.youtube.com/channel/${channelId}`;

    try {
      const info = await youtubedl(url, {
        dumpSingleJson: true,
        playlistItems: '1',
        noWarnings: true,
        ...(config.proxy.http && { proxy: config.proxy.http }),
      });

      return {
        id: info.channel_id,
        name: info.channel || info.uploader,
        url: info.channel_url,
        subscriberCount: info.channel_follower_count,
      };
    } catch (error) {
      logger.error(`Error fetching channel info for ${channelId}:`, error);
      throw error;
    }
  }

  /**
   * Check if video is a live stream or premiere
   */
  async isLiveOrPremiere(videoId: string): Promise<{ isLive: boolean; premiereDate?: Date }> {
    try {
      const info = await this.getVideoInfo(videoId);
      // This is a simplified check - you may need to add more logic
      return {
        isLive: false,
        premiereDate: undefined,
      };
    } catch (error) {
      logger.error(`Error checking if video is live: ${videoId}`, error);
      return { isLive: false };
    }
  }
}

export default new YouTubeService();
