import { Job } from 'bull';
import prisma from '../../utils/database';
import { PrismaClient } from '@prisma/client';
import youtubeService from '../../services/youtube.service';
import recognitionService from '../../services/recognition.service';
import spotifyService from '../../services/spotify.service';
import logger from '../../utils/logger';
import config from '../../config';


interface SetProcessingJobData {
  videoId: string;
  queueItemId: number;
}

/**
 * Set Processing Job Processor
 *
 * This is the main pipeline for processing DJ sets:
 * 1. Download audio from YouTube
 * 2. Split audio into segments
 * 3. Identify tracks using Shazam
 * 4. Enrich tracks with Spotify data
 * 5. Create Set and Track records in database
 * 6. Send notification to user
 */
export async function processSet(job: Job<SetProcessingJobData>): Promise<void> {
  const { videoId, queueItemId } = job.data;

  logger.info(`Processing set: ${videoId}`);

  try {
    // Update queue status to processing
    await prisma.setQueue.update({
      where: { id: queueItemId },
      data: { status: 'processing' },
    });

    // Step 1: Get video info
    job.progress(10);
    logger.info(`[${videoId}] Fetching video info...`);
    const videoInfo = await youtubeService.getVideoInfo(videoId);

    // Check if channel exists, create if not
    let channel = await prisma.channel.findUnique({
      where: { channelId: videoInfo.channelId },
    });

    if (!channel) {
      channel = await prisma.channel.create({
        data: {
          channelId: videoInfo.channelId,
          author: videoInfo.channelName,
          channelUrl: `https://www.youtube.com/channel/${videoInfo.channelId}`,
        },
      });
    }

    // Step 2: Download audio
    job.progress(20);
    logger.info(`[${videoId}] Downloading audio...`);
    const audioPath = await youtubeService.downloadAudio(videoId);

    // Step 3: Split audio into segments
    job.progress(30);
    logger.info(`[${videoId}] Splitting audio into segments...`);
    const segmentLength = config.app.audioSegmentsLength;
    const segments = await youtubeService.splitAudioIntoSegments(audioPath, segmentLength);

    // Step 4: Identify tracks using Shazam
    job.progress(40);
    logger.info(`[${videoId}] Identifying tracks with Shazam (${segments.length} segments)...`);

    const recognitionResults = await recognitionService.recognizeTracks(segments);

    // Filter successful recognitions
    const identifiedTracks = recognitionResults
      .filter(r => r.success && r.track)
      .map(r => r.track!);

    // Step 5: Process identified tracks
    job.progress(60);
    logger.info(`[${videoId}] Processing identified tracks...`);

    const trackRecords = [];
    for (const identifiedTrack of identifiedTracks) {
      if (!identifiedTrack) continue;

      // Check if track exists
      let track = await prisma.track.findFirst({
        where: {
          OR: [
            { keyTrackShazam: identifiedTrack.keyTrackShazam },
            { keyTrackSpotify: identifiedTrack.spotifyId },
          ],
        },
      });

      if (!track) {
        // Create new track
        track = await prisma.track.create({
          data: {
            keyTrackShazam: identifiedTrack.keyTrackShazam,
            keyTrackSpotify: identifiedTrack.spotifyId || null,
            keyTrackApple: identifiedTrack.appleMusicId || null,
            title: identifiedTrack.title,
            artistName: identifiedTrack.artistName,
            album: identifiedTrack.album,
            label: identifiedTrack.label,
            releaseYear: identifiedTrack.releaseYear,
            releaseDate: identifiedTrack.releaseDate ? new Date(identifiedTrack.releaseDate) : null,
            coverArts: identifiedTrack.coverArtUrl ? { shazam: identifiedTrack.coverArtUrl } : null,
            previewUris: identifiedTrack.previewUrl ? { spotify: identifiedTrack.previewUrl } : null,
            uriApple: identifiedTrack.appleMusicUrl,
          },
        });
      } else {
        // Update track's set count
        await prisma.track.update({
          where: { id: track.id },
          data: { nbSets: { increment: 1 } },
        });
      }

      trackRecords.push(track);
    }

    // Step 6: Create Set record
    job.progress(80);
    logger.info(`[${videoId}] Creating set record...`);

    const set = await prisma.set.create({
      data: {
        videoId,
        channelId: channel.id,
        title: videoInfo.title,
        duration: videoInfo.duration,
        publishDate: new Date(videoInfo.publishDate),
        thumbnail: videoInfo.thumbnail,
        playableInEmbed: videoInfo.playableInEmbed,
        chapters: videoInfo.chapters as any,
        nbTracks: trackRecords.length,
        likeCount: videoInfo.likeCount,
        viewCount: videoInfo.viewCount,
        published: true,
      },
    });

    // Create TrackSet relationships
    for (let i = 0; i < trackRecords.length; i++) {
      await prisma.trackSet.create({
        data: {
          trackId: trackRecords[i].id,
          setId: set.id,
          pos: i,
          // startTime and endTime would come from segment timing
        },
      });
    }

    // Update channel's set count
    await prisma.channel.update({
      where: { id: channel.id },
      data: { nbSets: { increment: 1 } },
    });

    // Step 7: Cleanup temp files
    job.progress(90);
    logger.info(`[${videoId}] Cleaning up temporary files...`);
    await youtubeService.cleanupVideoFiles(videoId);

    // Step 8: Update queue status
    job.progress(100);
    await prisma.setQueue.update({
      where: { id: queueItemId },
      data: { status: 'done' },
    });

    // TODO: Send notification email if requested
    // if (sendEmail) {
    //   await emailService.sendSetProcessed(user.email, set.title, set.id);
    // }

    logger.info(`[${videoId}] ✅ Processing complete! Set ID: ${set.id}`);
  } catch (error) {
    logger.error(`[${videoId}] ❌ Processing failed:`, error);

    // Update queue status to failed
    await prisma.setQueue.update({
      where: { id: queueItemId },
      data: {
        status: 'failed',
        nAttempts: { increment: 1 },
      },
    });

    throw error;
  }
}

export default processSet;
