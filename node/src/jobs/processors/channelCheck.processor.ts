import { Job } from 'bull';
import { PrismaClient } from '@prisma/client';
import youtubeService from '../../services/youtube.service';
import { setProcessingQueue } from '../queue';
import logger from '../../utils/logger';
import { getErrorMessage } from '../../types/errors';

const prisma = new PrismaClient();

interface ChannelCheckJobData {
  channelId?: number;
  checkAll?: boolean;
}

/**
 * Channel Check Processor
 *
 * Monitors followed channels for new DJ set videos and automatically
 * queues them for processing. Runs periodically to keep content fresh.
 */
export async function processChannelCheck(job: Job<ChannelCheckJobData>): Promise<any> {
  const { channelId, checkAll = true } = job.data;

  logger.info('Starting channel check job', { channelId, checkAll });

  try {
    // Get channels to check
    const channels = channelId
      ? [await prisma.channel.findUnique({ where: { id: channelId } })]
      : await prisma.channel.findMany({
          where: {
            followable: true,
            hidden: false,
          },
          orderBy: {
            updatedAt: 'asc', // Check oldest first
          },
        });

    if (!channels || channels.length === 0) {
      logger.info('No channels to check');
      return { checked: 0, newSets: 0 };
    }

    logger.info(`Checking ${channels.length} channels for new videos`);

    let totalChecked = 0;
    let totalNewSets = 0;
    const results = [];

    for (const channel of channels) {
      if (!channel) continue;

      try {
        await job.progress((totalChecked / channels.length) * 100);

        logger.info(`Checking channel: ${channel.author} (${channel.channelId})`);

        // Get channel's recent uploads using YouTube API
        const recentVideos = await youtubeService.getChannelVideos(channel.channelId, {
          maxResults: 10, // Check last 10 videos
          order: 'date',
        });

        if (!recentVideos || recentVideos.length === 0) {
          logger.info(`No videos found for channel ${channel.channelId}`);
          totalChecked++;
          continue;
        }

        // Check which videos are already in our database
        const existingVideoIds = await prisma.set.findMany({
          where: {
            videoId: {
              in: recentVideos.map((v) => v.videoId),
            },
          },
          select: {
            videoId: true,
          },
        });

        const existingIds = new Set(existingVideoIds.map((s) => s.videoId));
        const newVideos = recentVideos.filter((v) => !existingIds.has(v.videoId));

        if (newVideos.length > 0) {
          logger.info(`Found ${newVideos.length} new videos for ${channel.author}`);

          // Queue each new video for processing
          for (const video of newVideos) {
            try {
              // Check if already in queue
              const inQueue = await prisma.setQueue.findUnique({
                where: { videoId: video.videoId },
              });

              if (inQueue) {
                logger.info(`Video ${video.videoId} already in queue, skipping`);
                continue;
              }

              // Get full video info
              const videoInfo = await youtubeService.getVideoInfo(video.videoId);

              // Create queue entry
              const queueItem = await prisma.setQueue.create({
                data: {
                  videoId: video.videoId,
                  userId: null, // System-initiated
                  userPremium: false,
                  status: 'pending',
                  duration: videoInfo.duration,
                  nbChapters: videoInfo.chapters?.length || 0,
                  videoInfoJson: videoInfo as any,
                  sendEmail: false, // Don't send email for auto-queued sets
                  playSound: false,
                },
              });

              // Add to Bull queue with lower priority (since it's automatic)
              await setProcessingQueue.add(
                {
                  videoId: video.videoId,
                  queueItemId: queueItem.id,
                },
                {
                  priority: 20, // Lower priority than user-submitted sets
                }
              );

              totalNewSets++;
              logger.info(`Queued new video: ${video.title} (${video.videoId})`);
            } catch (error: unknown) {
              logger.error(`Error queueing video ${video.videoId}:`, getErrorMessage(error));
            }
          }
        }

        // Update channel stats
        await prisma.channel.update({
          where: { id: channel.id },
          data: {
            updatedAt: new Date(),
          },
        });

        results.push({
          channelId: channel.id,
          channelName: channel.author,
          videosChecked: recentVideos.length,
          newVideos: newVideos.length,
        });

        totalChecked++;

        // Small delay between channels to avoid rate limiting
        await new Promise((resolve) => setTimeout(resolve, 1000));
      } catch (error: unknown) {
        logger.error(`Error checking channel ${channel.channelId}:`, getErrorMessage(error));
        results.push({
          channelId: channel.id,
          channelName: channel.author,
          error: getErrorMessage(error),
        });
      }
    }

    logger.info(`Channel check complete: ${totalChecked} channels checked, ${totalNewSets} new sets queued`);

    return {
      checked: totalChecked,
      newSets: totalNewSets,
      results,
    };
  } catch (error: unknown) {
    logger.error('Channel check job failed:', error);
    throw error;
  }
}

/**
 * Helper: Get Channel Videos
 * Extends YouTube service with channel-specific video fetching
 */
declare module '../../services/youtube.service' {
  interface YouTubeService {
    getChannelVideos(channelId: string, options?: { maxResults?: number; order?: string }): Promise<any[]>;
  }
}

// Extend YouTube service with channel video fetching if not already present
if (!youtubeService.getChannelVideos) {
  youtubeService.getChannelVideos = async function (
    channelId: string,
    options: { maxResults?: number; order?: string } = {}
  ): Promise<any[]> {
    try {
      const { maxResults = 10, order = 'date' } = options;

      // Use yt-dlp to get channel videos
      const result = await this.downloadAudio(
        `https://www.youtube.com/channel/${channelId}/videos`,
        {
          dumpSingleJson: true,
          flatPlaylist: true,
          playlistEnd: maxResults,
        } as any
      );

      // Parse result
      if (typeof result === 'string') {
        const data = JSON.parse(result);
        if (data.entries) {
          return data.entries.map((entry: { videoId: string; title: string }) => ({
            videoId: entry.id,
            title: entry.title,
            duration: entry.duration,
            publishDate: entry.upload_date ? new Date(entry.upload_date) : null,
            thumbnail: entry.thumbnail,
            viewCount: entry.view_count,
            likeCount: entry.like_count,
          }));
        }
      }

      return [];
    } catch (error: unknown) {
      logger.error(`Error fetching channel videos for ${channelId}:`, getErrorMessage(error));
      return [];
    }
  };
}

export default processChannelCheck;
